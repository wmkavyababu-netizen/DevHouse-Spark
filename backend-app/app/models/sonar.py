import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    BigInteger,
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
from geoalchemy2 import Geography

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SonarDevice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sonar_devices"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supported_formats: Mapped[List[str]] = mapped_column(JSONB, server_default='["xtf", "jsf"]', nullable=False)
    operating_frequencies_khz: Mapped[List[int]] = mapped_column(JSONB, server_default="[]", nullable=False)
    default_range_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    calibration_profile: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    beam_width_degrees: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)


class StorageArtifact(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "storage_artifacts"
    __table_args__ = (
        CheckConstraint("file_size_bytes >= 0", name="ck_storage_artifacts_size_positive"),
    )

    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class Survey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "surveys"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    operator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sonar_device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sonar_devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    mission_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), server_default="uploaded", nullable=False)
    start_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    survey_area: Mapped[Optional[Any]] = mapped_column(Geography(geometry_type="POLYGON", srid=4326), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)

    sss_files: Mapped[List["SssFile"]] = relationship("SssFile", back_populates="survey", cascade="all, delete-orphan")
    frames: Mapped[List["SurveyFrame"]] = relationship("SurveyFrame", back_populates="survey", cascade="all, delete-orphan")


class SssFile(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "sss_files"
    __table_args__ = (
        CheckConstraint("file_size_bytes >= 0", name="ck_sss_files_size_positive"),
        CheckConstraint("ping_count IS NULL OR ping_count >= 0", name="ck_sss_files_ping_count_positive"),
    )

    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    storage_artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_count: Mapped[int] = mapped_column(Integer, server_default="2", nullable=False)
    sample_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    ping_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    survey: Mapped["Survey"] = relationship("Survey", back_populates="sss_files")
    storage_artifact: Mapped["StorageArtifact"] = relationship("StorageArtifact")


class SurveyFrame(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "survey_frames"
    __table_args__ = (
        UniqueConstraint("survey_id", "frame_number", name="uq_survey_frame_number"),
        CheckConstraint("frame_number >= 0", name="ck_survey_frames_frame_number_positive"),
        CheckConstraint("heading_degrees IS NULL OR (heading_degrees >= 0 AND heading_degrees <= 360)", name="ck_survey_frames_heading_range"),
        CheckConstraint("speed_knots IS NULL OR speed_knots >= 0", name="ck_survey_frames_speed_positive"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)", name="ck_survey_frames_quality_score_range"),
    )

    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    sss_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sss_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    location: Mapped[Optional[Any]] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    altitude_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    heading_degrees: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    speed_knots: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    raw_image_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    enhanced_image_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    shadow_map_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("storage_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    dropout_flags: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    survey: Mapped["Survey"] = relationship("Survey", back_populates="frames")
    sss_file: Mapped[Optional["SssFile"]] = relationship("SssFile")
    raw_image: Mapped[Optional["StorageArtifact"]] = relationship("StorageArtifact", foreign_keys=[raw_image_artifact_id])
    enhanced_image: Mapped[Optional["StorageArtifact"]] = relationship("StorageArtifact", foreign_keys=[enhanced_image_artifact_id])
    shadow_map: Mapped[Optional["StorageArtifact"]] = relationship("StorageArtifact", foreign_keys=[shadow_map_artifact_id])
