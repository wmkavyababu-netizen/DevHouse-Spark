from contextlib import asynccontextmanager
import logging
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.middleware import AuditLoggingMiddleware
from app.core.security import UserContext, get_current_user, require_role
from app.db.session import get_db
from app.models.sonar import StorageArtifact
from app.storage.service import storage_service

from app.ai.models.registry import model_registry
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.surveys import router as surveys_router
from app.api.v1.detections import router as detections_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.targets import router as targets_router
from app.api.v1.missions import router as missions_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.public import router as public_router
from app.api.v1.admin.retraining import router as retraining_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("tarang.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s in %s mode", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT)
    logger.info("Storage root configured at: %s", settings.STORAGE_ROOT)
    logger.info("Auth service gateway: %s", settings.AUTH_SERVICE_URL)
    # Ensure baseline model exists for local offline inference
    try:
        model_registry.ensure_baseline_model_exists("v1.0")
    except Exception as e:
        logger.warning("Model initialization notice: %s", e)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title="TARANG Application & Pipeline API",
    description="Marine Debris Side-Scan Sonar detection, processing, and GIS platform",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# Middlewares
# ------------------------------------------------------------------------------
# Audit logging middleware records mutating requests with correlation IDs
app.add_middleware(AuditLoggingMiddleware)

# CORS restricted to Nginx reverse proxy gateway origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)


# ------------------------------------------------------------------------------
# Core Infrastructure Endpoints
# ------------------------------------------------------------------------------
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """System health check probe."""
    return {
        "status": "healthy",
        "service": "tarang-backend-app",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/v1/auth/context", tags=["Security"], response_model=UserContext)
async def get_authenticated_context(
    current_user: UserContext = Depends(get_current_user),
):
    """
    Validates the incoming RS256 JWT issued by Spring Boot backend-auth,
    and returns the verified request-scoped user context.
    """
    return current_user


@app.get("/api/v1/admin/ping", tags=["Security"])
async def admin_only_ping(
    current_user: UserContext = Depends(require_role("admin", "super_admin", "org_admin")),
):
    """Admin RBAC test endpoint."""
    return {
        "status": "ok",
        "message": "Admin authorization confirmed",
        "user_id": str(current_user.user_id),
        "roles": current_user.roles,
    }


@app.get("/api/v1/storage/download/{token}", tags=["Storage"])
async def download_artifact_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Resolves an authorized, signed download token and streams the artifact.
    Never exposes raw server filesystem paths to the client.
    """
    artifact_id, user_id = storage_service.verify_download_token(token)

    result = await db.execute(select(StorageArtifact).where(StorageArtifact.id == artifact_id))
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage artifact not found in database registry",
        )

    try:
        physical_path = storage_service.resolve_physical_path(artifact.storage_uri)
    except (FileNotFoundError, PermissionError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact content unavailable: {str(e)}",
        )

    return FileResponse(
        path=str(physical_path),
        media_type=artifact.mime_type,
        filename=artifact.filename,
    )


# ------------------------------------------------------------------------------
# Feature Routers
# ------------------------------------------------------------------------------
app.include_router(auth_router, prefix="/api/v1")
app.include_router(surveys_router, prefix="/api/v1")
app.include_router(detections_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(targets_router, prefix="/api/v1")
app.include_router(missions_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(public_router, prefix="/api/v1")
app.include_router(retraining_router, prefix="/api/v1")
