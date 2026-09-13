import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    TIMESTAMP,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Detection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "detections"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_detections_confidence_range"),
    )

    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    survey_frame_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("survey_frames.id", ondelete="CASCADE"),
        nullable=False,
    )
    processing_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_stages.id", ondelete="SET NULL"),
        nullable=True,
    )
    ai_model_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("target_classes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bounding_box: Mapped[List[float]] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    segmentation_mask_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(50), server_default="unreviewed", nullable=False)
    raw_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)

    xai_evidence: Mapped[Optional["XaiEvidence"]] = relationship("XaiEvidence", back_populates="detection", uselist=False, cascade="all, delete-orphan")
    physics_validation: Mapped[Optional["PhysicsValidation"]] = relationship("PhysicsValidation", back_populates="detection", uselist=False, cascade="all, delete-orphan")
    geotags: Mapped[List["Geotag"]] = relationship("Geotag", back_populates="detection", cascade="all, delete-orphan")


class XaiEvidence(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "xai_evidence"
    __table_args__ = (
        UniqueConstraint("detection_id", name="uq_xai_evidence_detection_id"),
        CheckConstraint("saliency_score IS NULL OR (saliency_score >= 0 AND saliency_score <= 1)", name="ck_xai_saliency_range"),
    )

    detection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(String(50), server_default="grad_cam", nullable=False)
    heatmap_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    saliency_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    explanation_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    detection: Mapped["Detection"] = relationship("Detection", back_populates="xai_evidence")


class PhysicsValidation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "physics_validation"
    __table_args__ = (
        UniqueConstraint("detection_id", name="uq_physics_validation_detection_id"),
        CheckConstraint("shadow_consistency_score IS NULL OR (shadow_consistency_score >= 0 AND shadow_consistency_score <= 1)", name="ck_physics_shadow_consistency_range"),
    )

    detection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
    )
    slant_range_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    acoustic_shadow_length_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    expected_size_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    shadow_consistency_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    is_plausible: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    validation_details: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    validated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    detection: Mapped["Detection"] = relationship("Detection", back_populates="physics_validation")


class Geotag(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "geotags"
    __table_args__ = (
        CheckConstraint("uncertainty_radius_meters IS NULL OR uncertainty_radius_meters >= 0", name="ck_geotags_uncertainty_positive"),
    )

    detection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
    )
    survey_frame_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("survey_frames.id", ondelete="CASCADE"),
        nullable=False,
    )
    location: Mapped[Any] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    uncertainty_radius_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    depth_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    is_authoritative: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(100), server_default="slant_range_nav", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    detection: Mapped["Detection"] = relationship("Detection", back_populates="geotags")
    survey_frame: Mapped["SurveyFrame"] = relationship("SurveyFrame")
