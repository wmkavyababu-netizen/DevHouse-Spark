import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
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
from geoalchemy2 import Geography

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Target(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "targets"
    __table_args__ = (
        CheckConstraint("fused_confidence >= 0 AND fused_confidence <= 1", name="ck_targets_confidence_range"),
        CheckConstraint("observation_count >= 1", name="ck_targets_observation_count_positive"),
    )

    target_class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("target_classes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    location: Mapped[Any] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    best_survey_frame_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("survey_frames.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(50), server_default="detected", nullable=False)
    fused_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)

    history: Mapped[List["TargetHistory"]] = relationship("TargetHistory", back_populates="target", cascade="all, delete-orphan")


class TargetHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "target_history"
    __table_args__ = (
        CheckConstraint("previous_confidence IS NULL OR (previous_confidence >= 0 AND previous_confidence <= 1)", name="ck_target_hist_prev_conf_range"),
        CheckConstraint("new_confidence IS NULL OR (new_confidence >= 0 AND new_confidence <= 1)", name="ck_target_hist_new_conf_range"),
    )

    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    new_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    target: Mapped["Target"] = relationship("Target", back_populates="history")


class DetectionTargetMapping(Base):
    __tablename__ = "detection_target_mapping"
    __table_args__ = (
        CheckConstraint("association_score IS NULL OR (association_score >= 0 AND association_score <= 1)", name="ck_mapping_association_score_range"),
    )

    detection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("targets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    association_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    associated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
