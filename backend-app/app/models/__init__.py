"""TARANG SQLAlchemy ORM models package.

All models exactly mirror the 30 tables/views defined in Alembic migration 001_initial_schema.py.
"""

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .auth import (
    Organization,
    Role,
    User,
    UserRole,
    RefreshToken,
    Notification,
    AuditLog,
)
from .sonar import (
    SonarDevice,
    StorageArtifact,
    Survey,
    SssFile,
    SurveyFrame,
)
from .pipeline import (
    ProcessingJob,
    ProcessingStage,
    PreprocessingRun,
)
from .ai import (
    TargetClass,
    DatasetVersion,
    AiModel,
    ModelEvaluation,
)
from .detection import (
    Detection,
    XaiEvidence,
    PhysicsValidation,
    Geotag,
)
from .target import (
    Target,
    TargetHistory,
    DetectionTargetMapping,
)
from .review import (
    ReviewAssignment,
    Review,
    DatasetSample,
)
from .views import (
    MvSurveyStats,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # Auth
    "Organization",
    "Role",
    "User",
    "UserRole",
    "RefreshToken",
    "Notification",
    "AuditLog",
    # Sonar
    "SonarDevice",
    "StorageArtifact",
    "Survey",
    "SssFile",
    "SurveyFrame",
    # Pipeline
    "ProcessingJob",
    "ProcessingStage",
    "PreprocessingRun",
    # AI
    "TargetClass",
    "DatasetVersion",
    "AiModel",
    "ModelEvaluation",
    # Detection
    "Detection",
    "XaiEvidence",
    "PhysicsValidation",
    "Geotag",
    # Target
    "Target",
    "TargetHistory",
    "DetectionTargetMapping",
    # Review
    "ReviewAssignment",
    "Review",
    "DatasetSample",
    # Views
    "MvSurveyStats",
]
