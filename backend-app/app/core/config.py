import os
from typing import List, Set
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "TARANG Application & Pipeline Backend"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://tarang_user:tarang_insecure_dev_password@localhost:5432/tarang_db",
    )
    DATABASE_SYNC_URL: str = os.getenv(
        "DATABASE_SYNC_URL",
        "postgresql://tarang_user:tarang_insecure_dev_password@localhost:5432/tarang_db",
    )

    # Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # Spring Boot Auth Service & JWT
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8080")
    AUTH_PUBLIC_KEY_ENDPOINT: str = "/api/auth/public-key"
    AUTH_JWKS_ENDPOINT: str = "/api/auth/.well-known/jwks.json"
    JWT_ALGORITHM: str = "RS256"
    JWT_KEY_ID: str = os.getenv("JWT_KEY_ID", "tarang-dev-key-v1")

    # Storage Service Configuration
    STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "storage")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "1024"))
    DOWNLOAD_TOKEN_SECRET: str = os.getenv("DOWNLOAD_TOKEN_SECRET", "tarang-storage-download-secret-dev-only")
    DOWNLOAD_TOKEN_EXPIRE_SECONDS: int = 3600

    # Whitelisted SSS and Image Extensions
    ALLOWED_EXTENSIONS: Set[str] = {".xtf", ".jsf", ".hsx", ".sdf", ".png", ".json"}

    # CORS Configuration (Restricted to Nginx Gateway and Dev)
    CORS_ALLOWED_ORIGINS: str = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost,http://localhost:3000,http://localhost:80,https://localhost",
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
