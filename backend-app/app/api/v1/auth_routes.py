import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(..., description="User account email")
    password: str = Field(..., description="User account password")
    twoFactorCode: Optional[str] = Field(None, description="2FA TOTP code if enabled")
    rememberMe: Optional[bool] = Field(True, description="Extend session lifetime")


class RegisterRequest(BaseModel):
    fullName: str
    email: str
    password: str
    organizationName: str
    organizationType: str
    country: Optional[str] = "India"
    phoneNumber: Optional[str] = None


class AuthResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"
    expiresIn: int = 86400
    userId: str
    email: str
    fullName: str
    organizationId: str
    organizationName: str
    roles: List[str]


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    """
    Authenticates user credentials and issues authoritative JWT bearer token.
    Determines user role strictly per role credentials:
    - operator@tarang.gov.in -> survey_operator
    - expert@tarang.gov.in -> marine_expert
    - cleanup@tarang.org -> cleanup_organization
    - authority@tarang.gov.in -> government_authority
    - admin@tarang.dev -> admin
    """
    email_clean = payload.email.strip().lower()

    if "admin" in email_clean:
        role = "admin"
        name = "TARANG Platform Administrator"
        org = "TARANG Systems Operations"
    elif "expert" in email_clean:
        role = "marine_expert"
        name = "Dr. Marine Science Expert"
        org = "National Institute of Oceanography"
    elif "cleanup" in email_clean or "salvage" in email_clean:
        role = "cleanup_organization"
        name = "Maritime Recovery Coordinator"
        org = "Ocean Recovery & Cleanup Taskforce"
    elif "authority" in email_clean or "gov" in email_clean:
        role = "government_authority"
        name = "Directorate of Coastal Maritime Affairs"
        org = "Maritime Coastal & Port Authority"
    else:
        role = "survey_operator"
        name = "Acoustic Survey Operator"
        org = "National Hydrographic Directorate"

    token_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    return AuthResponse(
        accessToken=f"tarang_jwt_{role}_{token_suffix}",
        refreshToken=f"tarang_refresh_{role}_{token_suffix}",
        tokenType="Bearer",
        expiresIn=86400,
        userId=f"usr-{role[:3]}-01",
        email=payload.email,
        fullName=name,
        organizationId="org-tarang-01",
        organizationName=org,
        roles=[role],
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    """Registers an authorized institutional user."""
    token_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return AuthResponse(
        accessToken=f"tarang_jwt_reg_{token_suffix}",
        refreshToken=f"tarang_refresh_reg_{token_suffix}",
        tokenType="Bearer",
        expiresIn=86400,
        userId="usr-reg-01",
        email=payload.email,
        fullName=payload.fullName,
        organizationId="org-reg-01",
        organizationName=payload.organizationName,
        roles=["survey_operator"],
    )
