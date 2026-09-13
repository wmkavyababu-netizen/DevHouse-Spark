import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.registry import TARANG_CLASSES
from app.models.ai import DatasetVersion
from app.models.detection import Detection
from app.models.review import DatasetSample, Review
from app.models.sonar import SurveyFrame

logger = logging.getLogger(__name__)


class CurationService:
    """
    Translates human-in-the-loop expert review feedback into curated training samples (dataset_samples)
    and manages versioned training sets (dataset_versions) for closed-loop retraining.
    """

    async def get_or_create_active_dataset_version(
        self,
        db: AsyncSession,
        version_tag: str = "v1.0-baseline",
    ) -> DatasetVersion:
        """Ensures an active dataset version exists in the registry."""
        res = await db.execute(
            select(DatasetVersion).where(DatasetVersion.version_tag == version_tag)
        )
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        new_ver = DatasetVersion(
            id=uuid4(),
            version_tag=version_tag,
            description="Baseline dataset version populated from expert reviews and survey ingest.",
            total_samples=0,
            split_ratios={"train": 0.8, "val": 0.1, "test": 0.1},
            is_frozen=False,
        )
        db.add(new_ver)
        await db.commit()
        await db.refresh(new_ver)
        return new_ver

    async def create_new_dataset_version(
        self,
        db: AsyncSession,
        version_tag: str,
        description: str,
        created_by: Optional[UUID] = None,
        split_ratios: Optional[Dict[str, float]] = None,
    ) -> DatasetVersion:
        """Freezes previous versions and registers a new dataset version tag."""
        res = await db.execute(
            select(DatasetVersion).where(DatasetVersion.version_tag == version_tag)
        )
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        new_ver = DatasetVersion(
            id=uuid4(),
            version_tag=version_tag,
            description=description,
            total_samples=0,
            split_ratios=split_ratios or {"train": 0.8, "val": 0.1, "test": 0.1},
            created_by=created_by,
            is_frozen=False,
        )
        db.add(new_ver)
        await db.commit()
        await db.refresh(new_ver)
        return new_ver

    async def curate_pending_feedback(
        self,
        db: AsyncSession,
        target_dataset_version_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Scans all expert review decisions that have not yet been curated into dataset_samples.
        Codifies corrections, rejections, acceptances, and unknown anomalies into training samples.
        """
        # 1. Resolve dataset version
        if not target_dataset_version_id:
            d_ver = await self.get_or_create_active_dataset_version(db)
            version_id = d_ver.id
        else:
            res = await db.execute(
                select(DatasetVersion).where(DatasetVersion.id == target_dataset_version_id)
            )
            d_ver = res.scalar_one_or_none()
            if not d_ver:
                raise ValueError(f"Dataset version {target_dataset_version_id} not found")
            version_id = d_ver.id

        # 2. Find reviews not yet curated into dataset_samples for this version
        subq = (
            select(DatasetSample.detection_id)
            .where(
                DatasetSample.dataset_version_id == version_id,
                DatasetSample.detection_id.isnot(None),
            )
            .scalar_subquery()
        )

        stmt = (
            select(Review, Detection, SurveyFrame)
            .join(Detection, Review.detection_id == Detection.id)
            .join(SurveyFrame, Detection.survey_frame_id == SurveyFrame.id)
            .where(~Review.detection_id.in_(subq))
        )

        res = await db.execute(stmt)
        unincluded = res.all()

        curated_samples: List[DatasetSample] = []
        feedback_breakdown = {"acceptance": 0, "correction": 0, "rejection": 0, "unknown": 0}

        for review, detection, frame in unincluded:
            # Determine feedback type and annotations
            decision = review.decision
            if decision == "corrected":
                feedback_type = "correction"
                final_class_id = review.corrected_target_class_id or detection.target_class_id
                final_bbox = review.corrected_bbox or detection.bounding_box
            elif decision == "rejected":
                feedback_type = "rejection"
                final_class_id = detection.target_class_id
                final_bbox = detection.bounding_box
            elif decision == "unknown":
                feedback_type = "unknown"
                final_class_id = 5  # canonical unknown class
                final_bbox = detection.bounding_box
            else:  # accepted
                feedback_type = "acceptance"
                final_class_id = detection.target_class_id
                final_bbox = detection.bounding_box

            feedback_breakdown[feedback_type] = feedback_breakdown.get(feedback_type, 0) + 1

            annotation_data = {
                "bbox": final_bbox,
                "class_id": final_class_id,
                "class_name": TARANG_CLASSES.get(final_class_id, "unknown"),
                "source": "expert_correction",
                "feedback_type": feedback_type,
                "decision": decision,
                "reviewer_id": str(review.reviewer_id),
                "comments": review.comments,
                "raw_image_artifact_id": str(frame.raw_image_artifact_id) if frame.raw_image_artifact_id else None,
                "enhanced_image_artifact_id": str(frame.enhanced_image_artifact_id) if frame.enhanced_image_artifact_id else None,
                "original_ai_class_id": detection.target_class_id,
                "original_ai_confidence": float(detection.confidence),
            }

            sample = DatasetSample(
                id=uuid4(),
                dataset_version_id=version_id,
                detection_id=detection.id,
                survey_frame_id=frame.id,
                target_class_id=final_class_id,
                split_type="train",  # Newly harvested active learning feedback routes to train split
                quality_score=frame.quality_score,
                annotation_data=annotation_data,
            )
            db.add(sample)
            curated_samples.append(sample)

        # 3. Update sample count on dataset version
        if curated_samples:
            d_ver.total_samples += len(curated_samples)
            await db.commit()

        logger.info(
            f"Curated {len(curated_samples)} new dataset_samples for dataset version {d_ver.version_tag} "
            f"(breakdown: {feedback_breakdown})"
        )

        return {
            "dataset_version_id": str(version_id),
            "version_tag": d_ver.version_tag,
            "curated_count": len(curated_samples),
            "total_samples": d_ver.total_samples,
            "breakdown": feedback_breakdown,
        }


curation_service = CurationService()
