import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TargetClass(Base):
    __tablename__ = "target_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color_hex: Mapped[str] = mapped_column(String(7), server_default="#06b6d4", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), server_default="medium", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class DatasetVersion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "dataset_versions"
    __table_args__ = (
        CheckConstraint("total_samples >= 0", name="ck_dataset_versions_samples_positive"),
    )

    version_tag: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_samples: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    split_ratios: Mapped[Dict[str, float]] = mapped_column(
        JSONB,
        server_default='{"train": 0.7, "val": 0.15, "test": 0.15}',
        nullable=False,
    )
    storage_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_frozen: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class AiModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_models"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_ai_models_name_version"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    storage_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    status: Mapped[str] = mapped_column(String(50), server_default="registered", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    evaluations: Mapped[List["ModelEvaluation"]] = relationship("ModelEvaluation", back_populates="model", cascade="all, delete-orphan")


class ModelEvaluation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "model_evaluations"
    __table_args__ = (
        CheckConstraint("precision_score IS NULL OR (precision_score >= 0 AND precision_score <= 1)", name="ck_eval_precision_range"),
        CheckConstraint("recall_score IS NULL OR (recall_score >= 0 AND recall_score <= 1)", name="ck_eval_recall_range"),
        CheckConstraint("map50_score IS NULL OR (map50_score >= 0 AND map50_score <= 1)", name="ck_eval_map50_range"),
        CheckConstraint("map50_95_score IS NULL OR (map50_95_score >= 0 AND map50_95_score <= 1)", name="ck_eval_map50_95_range"),
        CheckConstraint("iou_score IS NULL OR (iou_score >= 0 AND iou_score <= 1)", name="ck_eval_iou_range"),
        CheckConstraint("f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1)", name="ck_eval_f1_range"),
    )

    ai_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    precision_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    recall_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    map50_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    map50_95_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    iou_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    f1_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    evaluation_metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    model: Mapped["AiModel"] = relationship("AiModel", back_populates="evaluations")
    dataset_version: Mapped["DatasetVersion"] = relationship("DatasetVersion")
