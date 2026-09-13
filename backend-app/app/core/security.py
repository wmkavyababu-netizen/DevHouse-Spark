import json
import logging
from typing import Callable, Dict, List, Optional
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)

# Reusable Bearer security scheme
bearer_scheme = HTTPBearer(auto_error=True)

# In-memory public key cache: kid -> PEM string
_public_key_cache: Dict[str, str] = {}


class UserContext(BaseModel):
    """Authenticated user context extracted from Spring Boot's asymmetric RS256 JWT."""
    user_id: UUID = Field(..., description="User primary key UUID")
    email: str = Field(..., description="User email address")
    roles: List[str] = Field(default_factory=list, description="Assigned RBAC role names")
    organization_id: Optional[UUID] = Field(None, description="User organization UUID")
    full_name: Optional[str] = Field(None, description="User full display name")

    @property
    def is_admin(self) -> bool:
        return any("admin" in r.lower() for r in self.roles)

    def has_role(self, role: str) -> bool:
        norm = role.lower().replace("role_", "")
        user_roles = [r.lower().replace("role_", "") for r in self.roles]
        return self.is_admin or norm in user_roles


async def fetch_public_key_by_kid(kid: str) -> str:
    """
    Fetch and cache Spring Boot's RS256 public key for a given key ID (kid).
    FastAPI never stores or issues tokens; it only verifies signatures.
    """
    global _public_key_cache

    if kid in _public_key_cache:
        return _public_key_cache[kid]

    # Try fetching public key PEM directly from Spring Boot
    public_key_url = f"{settings.AUTH_SERVICE_URL}{settings.AUTH_PUBLIC_KEY_ENDPOINT}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(public_key_url)
            if resp.status_code == 200 and resp.text.strip():
                pem = resp.text.strip()
                _public_key_cache[kid] = pem
                logger.info("Successfully fetched and cached public key for kid: %s", kid)
                return pem
    except Exception as e:
        logger.warning("Failed to fetch public key from %s: %s", public_key_url, e)

    # Try fetching JWKS endpoint as fallback
    jwks_url = f"{settings.AUTH_SERVICE_URL}{settings.AUTH_JWKS_ENDPOINT}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(jwks_url)
            if resp.status_code == 200:
                jwks_data = resp.json()
                for key in jwks_data.get("keys", []):
                    if key.get("kid") == kid:
                        # Convert JWK to PEM or return dict for jose
                        _public_key_cache[kid] = json.dumps(key)
                        return _public_key_cache[kid]
    except Exception as e:
        logger.warning("Failed to fetch JWKS from %s: %s", jwks_url, e)

    # Check if a cached key exists
    if kid in _public_key_cache:
        return _public_key_cache[kid]

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Unable to retrieve public key for token verification (kid: {kid}). Identity service may be starting.",
    )


def register_cached_public_key(kid: str, pem_or_jwk: str) -> None:
    """Manual hook for injecting / testing public keys directly."""
    global _public_key_cache
    _public_key_cache[kid] = pem_or_jwk


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserContext:
    """
    FastAPI dependency validating incoming RS256 JWT tokens.
    Extracts user_id, email, roles, organization_id into a request-scoped UserContext.
    """
    token = credentials.credentials

    try:
        # Extract unverified header to retrieve Key ID (kid)
        unverified_headers = jwt.get_unverified_header(token)
    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token header structure: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    kid = unverified_headers.get("kid", settings.JWT_KEY_ID)
    public_key = await fetch_public_key_by_kid(kid)

    try:
        # Verify asymmetric RS256 signature using the public key
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier (sub)",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = UUID(user_id_str)
        email = payload.get("email", "")
        roles = payload.get("roles", [])
        org_id_str = payload.get("organization_id") or payload.get("org_id")
        organization_id = UUID(org_id_str) if org_id_str else None
        full_name = payload.get("full_name")

        return UserContext(
            user_id=user_id,
            email=email,
            roles=roles,
            organization_id=organization_id,
            full_name=full_name,
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (PyJWTError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token signature or payload: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*allowed_roles: str) -> Callable[[UserContext], UserContext]:
    """
    RBAC dependency factory.
    Enforces that the authenticated user possesses at least one of the specified roles (or is admin).
    """
    def role_checker(current_user: UserContext = Depends(get_current_user)) -> UserContext:
        if current_user.is_admin:
            return current_user

        user_roles_normalized = {r.lower().replace("role_", "") for r in current_user.roles}
        required_roles_normalized = {r.lower().replace("role_", "") for r in allowed_roles}

        if not user_roles_normalized.intersection(required_roles_normalized):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Requires one of roles: {list(allowed_roles)}",
            )
        return current_user

    return role_checker


def require_org_match(org_id_param_name: str = "organization_id") -> Callable[[Request, UserContext], UserContext]:
    """
    RBAC dependency factory for multi-tenant isolation.
    Verifies that the target resource's organization matches the user's organization (or user is admin).
    """
    def org_checker(request: Request, current_user: UserContext = Depends(get_current_user)) -> UserContext:
        if current_user.is_admin:
            return current_user

        # Inspect path parameters or query parameters for organization_id
        target_org_str = request.path_params.get(org_id_param_name) or request.query_params.get(org_id_param_name)
        if target_org_str:
            try:
                target_org_uuid = UUID(target_org_str)
                if current_user.organization_id != target_org_uuid:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Resource belongs to a different organization",
                    )
            except ValueError:
                pass

        return current_user

    return org_checker
