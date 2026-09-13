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


class ProcessingJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "processing_jobs"
    __table_args__ = (
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="ck_processing_jobs_progress_range"),
    )

    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), server_default="queued", nullable=False)
    progress_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default="0.0", nullable=False)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    stages: Mapped[List["ProcessingStage"]] = relationship("ProcessingStage", back_populates="job", cascade="all, delete-orphan")


class ProcessingStage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "processing_stages"
    __table_args__ = (
        UniqueConstraint("processing_job_id", "stage_name", name="uq_processing_job_stage"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="ck_processing_stages_progress_range"),
        CheckConstraint("attempt_count >= 0", name="ck_processing_stages_attempt_count_positive"),
        CheckConstraint("retry_count >= 0", name="ck_processing_stages_retry_count_positive"),
        CheckConstraint("stage_order >= 0", name="ck_processing_stages_order_positive"),
    )

    processing_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), server_default="pending", nullable=False)
    progress_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default="0.0", nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    execution_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters_used: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    job: Mapped["ProcessingJob"] = relationship("ProcessingJob", back_populates="stages")


class PreprocessingRun(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "preprocessing_runs"
    __table_args__ = (
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)", name="ck_preprocessing_runs_quality_range"),
    )

    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    frame_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("survey_frames.id", ondelete="CASCADE"),
        nullable=True,
    )
    sonar_device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sonar_devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    tvg_applied: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    destriping_applied: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    denoising_applied: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    run_parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
