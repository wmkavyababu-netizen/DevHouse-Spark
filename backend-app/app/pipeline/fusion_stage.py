import hashlib
import json
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import numpy as np
from geoalchemy2.functions import ST_MakePoint, ST_SetSRID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.inference.detector import YOLODetector
from app.ai.models.registry import TARANG_CLASSES, model_registry
from app.ai.xai.gradcam import xai_generator
from app.models.ai import AiModel
from app.models.detection import Detection, Geotag, PhysicsValidation, XaiEvidence
from app.models.sonar import SurveyFrame
from app.models.target import Target
from app.pipeline.confidence.fusion import confidence_fuser
from app.pipeline.contracts import NormalizedSonarFrame, PreprocessingOutput
from app.pipeline.deduplication.cluster import target_clusterer
from app.pipeline.geotagging.geotagger import geodesic_geotagger
from app.pipeline.physics.validator import physics_validator
from app.storage.service import storage_service

logger = logging.getLogger(__name__)


class EvidenceFusionPipeline:
    """
    Orchestrates the complete evidence-fusion lifecycle following frame preprocessing:
    Inference (YOLO) -> XAI (Grad-CAM) -> Physics Validation (Shadows) ->
    Authoritative Geotagging -> Confidence Fusion -> Target Deduplication & Audit History.
    """

    async def execute_for_frame(
        self,
        db: AsyncSession,
        survey_id: UUID,
        survey_frame_id: UUID,
        processing_job_id: UUID,
        processing_stage_id: Optional[UUID],
        frame: NormalizedSonarFrame,
        preprocessing_output: PreprocessingOutput,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
    ) -> List[Detection]:
        """
        Executes local AI detection and complete multi-modal evidence fusion for a single frame.
        """
        # 1. Load current production AI model
        yolo_model, ai_model_rec, model_checksum = await model_registry.get_current_model(db)
        detector = YOLODetector(yolo_model, default_conf=conf_threshold, default_iou=iou_threshold)

        # 2. Run local in-process YOLO detection on the enhanced frame
        enhanced_img = preprocessing_output.enhanced_frame
        raw_detections = detector.detect(enhanced_img, conf_threshold=conf_threshold, iou_threshold=iou_threshold)

        if not raw_detections:
            logger.info(f"Zero candidate detections on frame {frame.frame_number}")
            return []

        logger.info(f"Processing {len(raw_detections)} candidate detections on frame {frame.frame_number}")
        created_detections: List[Detection] = []
        nav = frame.navigation
        h, w = enhanced_img.shape[:2]

        for det in raw_detections:
            bbox = det["bbox"]  # [x1, y1, x2, y2]
            class_id = det["class_id"]
            class_name = det["class_name"]
            ai_conf = det["confidence"]

            # Traceability & Idempotency key: SHA256(frame_id + stage_id + model_checksum)
            stage_str = str(processing_stage_id) if processing_stage_id else "direct_inference"
            inference_key = hashlib.sha256(
                f"{survey_frame_id}:{stage_str}:{model_checksum}:{bbox}".encode("utf-8")
            ).hexdigest()

            # ------------------------------------------------------------------
            # Stage A: Explainable AI (XAI) Saliency Map Generation
            # ------------------------------------------------------------------
            heatmap_bytes, saliency_score, xai_meta = xai_generator.generate_saliency_map(
                image=enhanced_img,
                bbox=bbox,
                class_id=class_id,
                class_name=class_name,
                confidence=ai_conf,
            )

            # Persist heatmap artifact
            det_uuid = uuid4()
            heatmap_path = storage_service.get_survey_processed_path(
                survey_id, processing_job_id, f"xai_{det_uuid}.png"
            )
            heatmap_artifact = await storage_service.save_artifact(
                db=db,
                dest_path=heatmap_path,
                content=heatmap_bytes,
                artifact_type="xai_saliency_heatmap",
                filename=heatmap_path.name,
                mime_type="image/png",
                metadata={"detection_id": str(det_uuid), "method": "grad_cam"},
            )

            # ------------------------------------------------------------------
            # Stage B: Acoustic Physics Validation
            # ------------------------------------------------------------------
            physics_res = physics_validator.validate_detection(
                bbox=bbox,
                target_class_id=class_id,
                frame_width=w,
                frame_height=h,
                altitude_m=float(nav.altitude_m or 15.0),
                slant_range_max_m=float(frame.slant_range_max_m),
                shadow_map=preprocessing_output.shadow_map,
            )

            # ------------------------------------------------------------------
            # Stage C: Geodesic Geotagging (WGS-84 Point)
            # ------------------------------------------------------------------
            target_lat, target_lon, uncertainty_m, geo_details = geodesic_geotagger.calculate_geotag(
                towfish_lat=float(nav.latitude),
                towfish_lon=float(nav.longitude),
                heading_deg=float(nav.heading_deg or 90.0),
                bbox=bbox,
                frame_width=w,
                frame_height=h,
                altitude_m=float(nav.altitude_m or 15.0),
                slant_range_max_m=float(frame.slant_range_max_m),
            )

            # ------------------------------------------------------------------
            # Stage D: Multi-Modal Confidence Fusion
            # ------------------------------------------------------------------
            fused_conf, fusion_details = confidence_fuser.fuse(
                ai_confidence=ai_conf,
                physics_score=physics_res["shadow_consistency_score"],
                frame_quality_score=preprocessing_output.quality_score,
                is_physically_plausible=physics_res["is_plausible"],
            )

            # Honest OOD / unknown detection handling
            is_ood = det.get("is_ood", False) or (class_id == 5) or (class_name == "unknown")
            model_ver = ai_model_rec.version if ai_model_rec else "v1.0"
            model_id = ai_model_rec.id if ai_model_rec else None

            # ------------------------------------------------------------------
            # Stage E: Create Detection Database Record
            # ------------------------------------------------------------------
            detection = Detection(
                id=det_uuid,
                survey_id=survey_id,
                survey_frame_id=survey_frame_id,
                processing_stage_id=processing_stage_id,
                ai_model_id=model_id,
                target_class_id=class_id,
                bounding_box=bbox,
                confidence=Decimal(f"{fused_conf:.4f}"),
                status="unreviewed" if not is_ood else "unclassified",
                raw_lat=target_lat,
                raw_lon=target_lon,
                metadata_json={
                    "inference_key": inference_key,
                    "model_version": model_ver,
                    "model_checksum": model_checksum,
                    "class_name": class_name,
                    "fusion_details": fusion_details,
                    "raw_ai_confidence": ai_conf,
                    "is_ood": is_ood,
                    "anomaly_type": "unknown" if is_ood else None,
                },
            )
            db.add(detection)
            await db.flush()

            # ------------------------------------------------------------------
            # Stage F: Create XAI Evidence Record (1-to-1)
            # ------------------------------------------------------------------
            xai_rec = XaiEvidence(
                detection_id=detection.id,
                method="grad_cam",
                heatmap_artifact_id=heatmap_artifact.id,
                saliency_score=Decimal(f"{saliency_score:.4f}"),
                explanation_json=xai_meta,
            )
            db.add(xai_rec)

            # ------------------------------------------------------------------
            # Stage G: Create Physics Validation Record (1-to-1)
            # ------------------------------------------------------------------
            physics_rec = PhysicsValidation(
                detection_id=detection.id,
                slant_range_meters=Decimal(f"{physics_res['slant_range_meters']:.2f}"),
                acoustic_shadow_length_meters=Decimal(f"{physics_res['acoustic_shadow_length_meters']:.2f}"),
                expected_size_meters=Decimal(f"{physics_res['expected_size_meters']:.2f}"),
                shadow_consistency_score=Decimal(f"{physics_res['shadow_consistency_score']:.4f}"),
                is_plausible=physics_res["is_plausible"],
                validation_details=physics_res["validation_details"],
            )
            db.add(physics_rec)

            # ------------------------------------------------------------------
            # Stage H: Create Authoritative Geotag Record
            # ------------------------------------------------------------------
            geotag_pt = ST_SetSRID(ST_MakePoint(target_lon, target_lat), 4326)
            geotag_rec = Geotag(
                detection_id=detection.id,
                survey_frame_id=survey_frame_id,
                location=geotag_pt,
                uncertainty_radius_meters=Decimal(f"{uncertainty_m:.2f}"),
                depth_meters=Decimal(f"{float(nav.depth_m or 25.0):.2f}"),
                is_authoritative=True,  # Authoritative tag (enforced by partial unique index)
                calculation_method="slant_range_geodesic",
            )
            db.add(geotag_rec)

            # ------------------------------------------------------------------
            # Stage I: Target Deduplication & Association
            # ------------------------------------------------------------------
            target, is_new = await target_clusterer.associate_or_create_target(
                db=db,
                detection_id=detection.id,
                survey_frame_id=survey_frame_id,
                target_class_id=class_id,
                lat=target_lat,
                lon=target_lon,
                confidence=fused_conf,
                class_name=class_name,
            )

            created_detections.append(detection)

        await db.commit()
        return created_detections


evidence_fusion_pipeline = EvidenceFusionPipeline()
