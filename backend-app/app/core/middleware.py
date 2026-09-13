import logging
import uuid
from typing import Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.db.session import AsyncSessionLocal
from app.models.auth import AuditLog

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures every mutating HTTP request (POST, PUT, DELETE, PATCH),
    propagates or creates an X-Correlation-ID, and records security audit logs in PostgreSQL.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Retrieve or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Process the request
        response = await call_next(request)

        # Inject correlation ID into response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Only record mutating actions into the audit log
        if request.method in {"POST", "PUT", "DELETE", "PATCH"} and not request.url.path.startswith("/api/v1/health"):
            # Execute audit log persistence in non-blocking background task
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("User-Agent")
            path = request.url.path
            method = request.method
            status_code = response.status_code

            # Extract user_id if authenticated
            user_id: Optional[UUID] = getattr(request.state, "user_id", None)

            try:
                await self._persist_audit_log(
                    user_id=user_id,
                    correlation_id=correlation_id,
                    action=f"HTTP_{method}",
                    resource_type="API_ENDPOINT",
                    resource_id=path,
                    details={
                        "path": path,
                        "method": method,
                        "status_code": status_code,
                    },
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
            except Exception as e:
                logger.error("Failed to write audit log for correlation %s: %s", correlation_id, e)

        return response

    async def _persist_audit_log(
        self,
        user_id: Optional[UUID],
        correlation_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> None:
        async with AsyncSessionLocal() as session:
            try:
                audit_record = AuditLog(
                    user_id=user_id,
                    correlation_id=correlation_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                session.add(audit_record)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def _get_client_ip(self, request: Request) -> str:
        xf = request.headers.get("X-Forwarded-For")
        if xf:
            return xf.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
