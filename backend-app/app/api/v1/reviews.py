import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import UserContext, get_current_user, require_role
from app.db.session import get_db
from app.models.review import Review
from app.schemas.review import (
    ReviewClaimResponse,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ReviewDetailResponse,
    ReviewQueueResponse,
    ReviewReleaseResponse,
)
from app.services.review_service import review_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["Expert Review Workflow"])


@router.get("/queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    class_id: Optional[int] = Query(None, description="Filter by target class ID"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum AI confidence"),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum AI confidence"),
    survey_id: Optional[UUID] = Query(None, description="Filter by survey UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    Returns prioritized pending detections for marine expert review.
    Enforces RBAC: viewable by marine experts, analysts, operators, and admins.
    """
    return await review_service.get_review_queue(
        db=db,
        current_user_id=current_user.user_id,
        page=page,
        page_size=page_size,
        class_id=class_id,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        survey_id=survey_id,
    )


@router.post("/claim/{detection_id}", response_model=ReviewClaimResponse)
async def claim_detection(
    detection_id: UUID,
    timeout_minutes: int = Query(30, ge=5, le=120, description="Claim hold duration in minutes"),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    Claims a detection for review.
    Enforced by partial unique index 'uq_review_assignment_claimed'.
    Returns 409 Conflict if already claimed by another active expert.
    """
    return await review_service.claim_detection(
        db=db,
        detection_id=detection_id,
        user_id=current_user.user_id,
        timeout_minutes=timeout_minutes,
    )


@router.post("/release/{detection_id}", response_model=ReviewReleaseResponse)
async def release_claim(
    detection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """Releases an active claim on a detection."""
    return await review_service.release_claim(
        db=db,
        detection_id=detection_id,
        user_id=current_user.user_id,
    )


@router.post("/decision", response_model=ReviewDecisionResponse)
async def submit_decision(
    detection_id: UUID = Query(..., description="Target detection UUID"),
    payload: ReviewDecisionRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """
    Submits an expert review decision ('accepted', 'rejected', 'corrected', 'unknown').
    Completes claim, updates detection and target status, and codifies feedback for retraining.
    """
    return await review_service.submit_review_decision(
        db=db,
        detection_id=detection_id,
        reviewer_id=current_user.user_id,
        request=payload,
    )


@router.get("/{detection_id}", response_model=ReviewDetailResponse)
async def get_review_detail(
    detection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """Retrieves existing expert review record for a detection."""
    res = await db.execute(select(Review).where(Review.detection_id == detection_id))
    review = res.scalar_one_or_none()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No review record found for detection {detection_id}",
        )

    return ReviewDetailResponse(
        review_id=review.id,
        detection_id=review.detection_id,
        target_id=review.target_id,
        reviewer_id=review.reviewer_id,
        decision=review.decision,
        corrected_target_class_id=review.corrected_target_class_id,
        corrected_bbox=review.corrected_bbox,
        comments=review.comments,
        reviewed_at=review.reviewed_at,
    )
