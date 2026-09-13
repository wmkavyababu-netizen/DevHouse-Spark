import uuid
from decimal import Decimal
from sqlalchemy import Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MvSurveyStats(Base):
    """SQLAlchemy model for materialized view mv_survey_stats."""
    __tablename__ = "mv_survey_stats"

    operator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    total_surveys: Mapped[int] = mapped_column(Integer, nullable=False)
    total_frames_processed: Mapped[int] = mapped_column(Integer, nullable=False)
    total_detections: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
