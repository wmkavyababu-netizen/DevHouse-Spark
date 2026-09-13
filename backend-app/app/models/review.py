import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin


class ReviewAssignment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "review_assignments"

    detection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), server_default="claimed", nullable=False)
    claimed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class Review(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "reviews"

    detection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("targets.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    corrected_target_class_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("target_classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    corrected_bbox: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    corrected_mask_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class DatasetSample(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "dataset_samples"
    __table_args__ = (
        CheckConstraint("split_type IN ('train', 'val', 'test')", name="ck_dataset_samples_split_type"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)", name="ck_dataset_samples_quality_range"),
    )

    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    detection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="SET NULL"),
        nullable=True,
    )
    survey_frame_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("survey_frames.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("target_classes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    split_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    annotation_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
