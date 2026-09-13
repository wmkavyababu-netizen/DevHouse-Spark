from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ReviewClaimResponse(BaseModel):
    assignment_id: UUID
    detection_id: UUID
    assigned_to: UUID
    status: str
    claimed_at: datetime
    expires_at: Optional[datetime] = None


class ReviewReleaseResponse(BaseModel):
    detection_id: UUID
    status: str
    message: str


class ReviewDecisionRequest(BaseModel):
    decision: Literal["accepted", "rejected", "corrected", "unknown"] = Field(
        ..., description="Expert decision on the AI detection"
    )
    corrected_target_class_id: Optional[int] = Field(
        None, description="Corrected class ID (0: crab_pot, 1: pipeline, 2: shipwreck, 3: ghost_net, 4: mine_cylinder, 5: unknown)"
    )
    corrected_bbox: Optional[List[float]] = Field(
        None, description="Corrected bounding box [x1, y1, x2, y2] relative to frame"
    )
    corrected_mask_artifact_id: Optional[UUID] = Field(
        None, description="Optional storage artifact UUID of corrected pixel mask"
    )
    comments: Optional[str] = Field(None, description="Free-text domain expert rationale")


class ReviewDecisionResponse(BaseModel):
    review_id: UUID
    detection_id: UUID
    decision: str
    reviewer_id: UUID
    feedback_type: str
    target_updated: bool
    reviewed_at: datetime
    message: str


class ReviewQueueItem(BaseModel):
    detection_id: UUID
    survey_id: UUID
    survey_frame_id: UUID
    survey_title: Optional[str] = None
    frame_number: Optional[int] = None
    target_class_id: int
    class_name: str
    confidence: float
    bounding_box: List[float]
    status: str
    risk_level: str
    claimed_by: Optional[UUID] = None
    claimed_at: Optional[datetime] = None
    is_claimed_by_me: bool = False
    created_at: datetime


class ReviewQueueResponse(BaseModel):
    items: List[ReviewQueueItem]
    total: int
    page: int
    page_size: int


class ReviewDetailResponse(BaseModel):
    review_id: UUID
    detection_id: UUID
    target_id: Optional[UUID] = None
    reviewer_id: UUID
    decision: str
    corrected_target_class_id: Optional[int] = None
    corrected_bbox: Optional[List[float]] = None
    comments: Optional[str] = None
    reviewed_at: datetime
