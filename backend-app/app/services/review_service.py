import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.registry import TARANG_CLASSES
from app.models.ai import TargetClass
from app.models.detection import Detection
from app.models.review import Review, ReviewAssignment
from app.models.sonar import Survey, SurveyFrame
from app.models.target import DetectionTargetMapping, Target, TargetHistory
from app.schemas.review import (
    ReviewClaimResponse,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ReviewQueueItem,
    ReviewQueueResponse,
    ReviewReleaseResponse,
)

logger = logging.getLogger(__name__)


class ReviewService:
    """
    Manages marine expert review claiming, concurrency control, decision submission,
    target state synchronization, and active learning feedback record creation.
    """

    async def get_review_queue(
        self,
        db: AsyncSession,
        current_user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        class_id: Optional[int] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        survey_id: Optional[UUID] = None,
    ) -> ReviewQueueResponse:
        """
        Retrieves pending detections for domain expert review.
        Orders by risk level, confidence, and timestamp.
        """
        offset = (page - 1) * page_size

        # Base query: unreviewed or unclassified detections
        query = (
            select(
                Detection,
                Survey.title.label("survey_title"),
                SurveyFrame.frame_number.label("frame_number"),
                ReviewAssignment.assigned_to.label("claimed_by"),
                ReviewAssignment.claimed_at.label("claimed_at"),
            )
            .join(SurveyFrame, Detection.survey_frame_id == SurveyFrame.id)
            .join(Survey, Detection.survey_id == Survey.id)
            .outerjoin(
                ReviewAssignment,
                (ReviewAssignment.detection_id == Detection.id)
                & (ReviewAssignment.status == "claimed"),
            )
            .where(Detection.status.in_(["unreviewed", "unclassified"]))
        )

        if class_id is not None:
            query = query.where(Detection.target_class_id == class_id)
        if min_confidence is not None:
            query = query.where(Detection.confidence >= min_confidence)
        if max_confidence is not None:
            query = query.where(Detection.confidence <= max_confidence)
        if survey_id is not None:
            query = query.where(Detection.survey_id == survey_id)

        # Count total
        count_q = select(func.count()).select_from(query.subquery())
        total_res = await db.execute(count_q)
        total = total_res.scalar() or 0

        # Execute paginated query
        query = query.order_by(desc(Detection.confidence), desc(Detection.created_at)).offset(offset).limit(page_size)
        res = await db.execute(query)
        rows = res.all()

        items: List[ReviewQueueItem] = []
        for det, s_title, f_num, claimed_by, claimed_at in rows:
            cls_name = TARANG_CLASSES.get(det.target_class_id, "unknown")
            # Determine risk level based on class
            risk_map = {
                0: "medium",    # crab_pot
                1: "high",      # submarine_pipeline
                2: "critical",  # shipwreck
                3: "critical",  # ghost_net
                4: "critical",  # mine_cylinder
                5: "low",       # unknown
            }
            items.append(
                ReviewQueueItem(
                    detection_id=det.id,
                    survey_id=det.survey_id,
                    survey_frame_id=det.survey_frame_id,
                    survey_title=s_title,
                    frame_number=f_num,
                    target_class_id=det.target_class_id,
                    class_name=cls_name,
                    confidence=float(det.confidence),
                    bounding_box=det.bounding_box,
                    status=det.status,
                    risk_level=risk_map.get(det.target_class_id, "medium"),
                    claimed_by=claimed_by,
                    claimed_at=claimed_at,
                    is_claimed_by_me=(claimed_by == current_user_id) if claimed_by else False,
                    created_at=det.created_at,
                )
            )

        return ReviewQueueResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def claim_detection(
        self,
        db: AsyncSession,
        detection_id: UUID,
        user_id: UUID,
        timeout_minutes: int = 30,
    ) -> ReviewClaimResponse:
        """
        Claims a detection for review.
        Enforces partial unique constraint 'one active claimed assignment per detection'.
        Raises 409 Conflict if claimed by another active reviewer.
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=timeout_minutes)

        # Check existing active claim
        stmt = select(ReviewAssignment).where(
            ReviewAssignment.detection_id == detection_id,
            ReviewAssignment.status == "claimed",
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            # Check if expired
            if existing.expires_at and existing.expires_at < now:
                existing.status = "expired"
                await db.flush()
            elif existing.assigned_to == user_id:
                # Idempotent re-claim by same user; extend expiration
                existing.expires_at = expires
                await db.commit()
                return ReviewClaimResponse(
                    assignment_id=existing.id,
                    detection_id=existing.detection_id,
                    assigned_to=existing.assigned_to,
                    status=existing.status,
                    claimed_at=existing.claimed_at,
                    expires_at=existing.expires_at,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Detection {detection_id} is already claimed by reviewer {existing.assigned_to}",
                )

        assignment = ReviewAssignment(
            id=uuid4(),
            detection_id=detection_id,
            assigned_to=user_id,
            status="claimed",
            claimed_at=now,
            expires_at=expires,
        )
        db.add(assignment)

        try:
            await db.commit()
            await db.refresh(assignment)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Concurrent claim conflict for detection {detection_id}",
            )

        return ReviewClaimResponse(
            assignment_id=assignment.id,
            detection_id=assignment.detection_id,
            assigned_to=assignment.assigned_to,
            status=assignment.status,
            claimed_at=assignment.claimed_at,
            expires_at=assignment.expires_at,
        )

    async def release_claim(
        self,
        db: AsyncSession,
        detection_id: UUID,
        user_id: UUID,
    ) -> ReviewReleaseResponse:
        """Releases an active claim held by the current user."""
        stmt = (
            update(ReviewAssignment)
            .where(
                ReviewAssignment.detection_id == detection_id,
                ReviewAssignment.assigned_to == user_id,
                ReviewAssignment.status == "claimed",
            )
            .values(status="released")
        )
        res = await db.execute(stmt)
        await db.commit()

        if res.rowcount == 0:
            return ReviewReleaseResponse(
                detection_id=detection_id,
                status="not_found",
                message="No active claim found for this user and detection",
            )

        return ReviewReleaseResponse(
            detection_id=detection_id,
            status="released",
            message="Claim released successfully",
        )

    async def submit_review_decision(
        self,
        db: AsyncSession,
        detection_id: UUID,
        reviewer_id: UUID,
        request: ReviewDecisionRequest,
    ) -> ReviewDecisionResponse:
        """
        Records expert validation/correction decision, updates detection & target states,
        and codifies the feedback for the retraining loop.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch detection
        d_res = await db.execute(select(Detection).where(Detection.id == detection_id))
        detection = d_res.scalar_one_or_none()
        if not detection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Detection {detection_id} not found",
            )

        # 2. Complete any active review assignment
        await db.execute(
            update(ReviewAssignment)
            .where(
                ReviewAssignment.detection_id == detection_id,
                ReviewAssignment.status == "claimed",
            )
            .values(
                status="completed",
                completed_at=now,
            )
        )

        # 3. Determine feedback type
        feedback_type_map = {
            "accepted": "acceptance",
            "rejected": "rejection",
            "corrected": "correction",
            "unknown": "unknown",
        }
        feedback_type = feedback_type_map.get(request.decision, "acceptance")

        # 4. Find associated Target
        map_res = await db.execute(
            select(DetectionTargetMapping.target_id).where(
                DetectionTargetMapping.detection_id == detection_id
            )
        )
        target_id = map_res.scalar_one_or_none()

        # 5. Create Review record
        review = Review(
            id=uuid4(),
            detection_id=detection_id,
            target_id=target_id,
            reviewer_id=reviewer_id,
            decision=request.decision,
            corrected_target_class_id=request.corrected_target_class_id,
            corrected_bbox=request.corrected_bbox,
            corrected_mask_artifact_id=request.corrected_mask_artifact_id,
            comments=request.comments,
            reviewed_at=now,
        )
        db.add(review)

        # 6. Update Detection state
        target_updated = False
        old_status = detection.status
        det_meta = dict(detection.metadata_json or {})

        if request.decision == "accepted":
            detection.status = "validated"
        elif request.decision == "rejected":
            detection.status = "rejected"
        elif request.decision == "corrected":
            detection.status = "corrected"
            if request.corrected_target_class_id is not None:
                det_meta["original_class_id"] = detection.target_class_id
                detection.target_class_id = request.corrected_target_class_id
            if request.corrected_bbox is not None:
                det_meta["original_bbox"] = detection.bounding_box
                detection.bounding_box = request.corrected_bbox
        elif request.decision == "unknown":
            detection.status = "unclassified"
            detection.target_class_id = 5  # unknown
            det_meta["is_ood"] = True

        det_meta["reviewed_by"] = str(reviewer_id)
        det_meta["review_decision"] = request.decision
        det_meta["feedback_type"] = feedback_type
        detection.metadata_json = det_meta

        # 7. Update Target & TargetHistory if associated
        if target_id is not None:
            t_res = await db.execute(select(Target).where(Target.id == target_id))
            target = t_res.scalar_one_or_none()
            if target:
                target_updated = True
                prev_status = target.status
                prev_conf = target.fused_confidence

                if request.decision == "accepted":
                    target.status = "validated"
                elif request.decision == "rejected":
                    # If multiple observations, keep detected; if sole observation, reject
                    if target.observation_count <= 1:
                        target.status = "rejected"
                elif request.decision == "corrected":
                    target.status = "corrected"
                    if request.corrected_target_class_id is not None:
                        target.target_class_id = request.corrected_target_class_id
                elif request.decision == "unknown":
                    target.status = "unclassified"
                    target.target_class_id = 5

                # Append to target history
                hist = TargetHistory(
                    id=uuid4(),
                    target_id=target.id,
                    updated_by=reviewer_id,
                    previous_status=prev_status,
                    new_status=target.status,
                    previous_confidence=prev_conf,
                    new_confidence=target.fused_confidence,
                    change_reason=f"Expert review ({request.decision}) by reviewer {reviewer_id}: {request.comments or 'No comment'}",
                    metadata_json={
                        "decision": request.decision,
                        "feedback_type": feedback_type,
                        "detection_id": str(detection_id),
                    },
                )
                db.add(hist)

        await db.commit()
        await db.refresh(review)

        logger.info(
            f"Review recorded for detection {detection_id} (decision: {request.decision}, feedback: {feedback_type})"
        )

        return ReviewDecisionResponse(
            review_id=review.id,
            detection_id=detection_id,
            decision=review.decision,
            reviewer_id=reviewer_id,
            feedback_type=feedback_type,
            target_updated=target_updated,
            reviewed_at=review.reviewed_at,
            message=f"Review decision '{request.decision}' recorded successfully",
        )


review_service = ReviewService()
