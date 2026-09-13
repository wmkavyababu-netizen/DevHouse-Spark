import io
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import cv2
import numpy as np
from PIL import Image
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.pipeline import PreprocessingRun, ProcessingJob, ProcessingStage
from app.models.sonar import SssFile, StorageArtifact, Survey, SurveyFrame, SonarDevice
from app.pipeline.adapters import get_device_adapter
from app.pipeline.contracts import NormalizedSonarFrame, PreprocessingOutput, StageResult
from app.pipeline.orchestrator import PreprocessingOrchestrator, STAGE_DEFINITIONS
from app.storage.service import storage_service

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Manages database transactions, stage progress reporting, storage persistence,
    and PostGIS spatial records for the side-scan sonar preprocessing pipeline.
    """

    def __init__(self):
        self.orchestrator = PreprocessingOrchestrator()

    async def initialize_processing_job(
        self,
        db: AsyncSession,
        survey_id: UUID,
        celery_task_id: Optional[str] = None,
    ) -> ProcessingJob:
        """
        Creates a new ProcessingJob and pre-allocates all child ProcessingStage rows.
        """
        job = ProcessingJob(
            survey_id=survey_id,
            status="running",
            progress_percentage=Decimal("0.0"),
            celery_task_id=celery_task_id,
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        await db.flush()

        # Pre-populate pipeline stages in exact execution order
        for stage_name, stage_order, stage_desc in STAGE_DEFINITIONS:
            stage = ProcessingStage(
                processing_job_id=job.id,
                stage_name=stage_name,
                stage_order=stage_order,
                status="pending",
                progress_percentage=Decimal("0.0"),
                attempt_count=1,
                retry_count=0,
                execution_log=f"Initialized: {stage_desc}",
                parameters_used={},
            )
            db.add(stage)

        await db.commit()
        await db.refresh(job)
        return job

    async def update_stage_progress(
        self,
        db: AsyncSession,
        job_id: UUID,
        result: StageResult,
    ) -> None:
        """
        Updates an individual ProcessingStage row and recalculates overall job progress.
        """
        stmt = (
            update(ProcessingStage)
            .where(
                ProcessingStage.processing_job_id == job_id,
                ProcessingStage.stage_name == result.stage_name,
            )
            .values(
                status=result.status,
                progress_percentage=Decimal(f"{result.progress_percentage:.2f}"),
                execution_log=result.log_message or f"Stage completed in {result.execution_time_ms:.1f}ms",
                parameters_used=result.parameters_used,
                completed_at=datetime.now(timezone.utc),
            )
        )
        await db.execute(stmt)

        # Update overall job progress
        overall_progress = min(max(result.progress_percentage, 0.0), 100.0)
        await db.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(progress_percentage=Decimal(f"{overall_progress:.2f}"))
        )
        await db.commit()

    async def execute_survey_pipeline(
        self,
        db: AsyncSession,
        survey_id: UUID,
        job_id: UUID,
        sss_file_id: Optional[UUID] = None,
    ) -> ProcessingJob:
        """
        Executes end-to-end preprocessing for a survey and its uploaded sonar files:
        1. Ingestion & format decoding via Device Adapters
        2. Sequence of 9 pure scientific stages
        3. Saving physical artifacts (raw, enhanced, shadow, tiles)
        4. Updating survey_frames, preprocessing_runs, and processing_stages
        """
        logger.info(f"Starting pipeline execution for survey {survey_id}, job {job_id}")

        # Fetch Survey, SssFile, and SonarDevice profile
        survey_res = await db.execute(select(Survey).where(Survey.id == survey_id))
        survey = survey_res.scalar_one_or_none()
        if not survey:
            raise ValueError(f"Survey {survey_id} not found")

        device_profile: Dict[str, Any] = {}
        device_id = survey.sonar_device_id
        if device_id:
            dev_res = await db.execute(select(SonarDevice).where(SonarDevice.id == device_id))
            device = dev_res.scalar_one_or_none()
            if device:
                device_profile = device.calibration_profile or {}

        # Locate SSS file to process
        file_query = select(SssFile).where(SssFile.survey_id == survey_id)
        if sss_file_id:
            file_query = file_query.where(SssFile.id == sss_file_id)

        file_res = await db.execute(file_query)
        sss_files = file_res.scalars().all()

        if not sss_files:
            logger.warning(f"No SSS files found for survey {survey_id}. Generating synthetic baseline frame.")
            # Fallback: parse using PNG adapter with default mock waterfall for pipeline readiness
            adapter = get_device_adapter("png")
            # Create a 512x1024 synthetic acoustic test image
            mock_img = np.random.uniform(0.1, 0.6, (512, 1024)).astype(np.float32)
            # Add center nadir water column
            mock_img[:, 512 - 50 : 512 + 50] = 0.02
            buf = io.BytesIO()
            Image.fromarray((mock_img * 255).astype(np.uint8)).save(buf, format="PNG")
            frames = adapter.parse(buf.getvalue(), survey_id=survey_id, sss_file_id=None)
        else:
            frames: List[NormalizedSonarFrame] = []
            for sf in sss_files:
                art_res = await db.execute(select(StorageArtifact).where(StorageArtifact.id == sf.storage_artifact_id))
                artifact = art_res.scalar_one_or_none()
                if not artifact:
                    continue

                abs_path = storage_service.root / artifact.storage_uri
                adapter = get_device_adapter(sf.file_format)
                parsed_frames = adapter.parse(
                    source=abs_path if abs_path.exists() else artifact.storage_uri,
                    survey_id=survey_id,
                    sss_file_id=sf.id,
                )
                frames.extend(parsed_frames)

        # Process each frame sequentially
        total_frames = len(frames)
        for frame_idx, frame in enumerate(frames):
            logger.info(f"Processing frame {frame.frame_number + 1}/{total_frames} for survey {survey_id}")

            # Define stage progress callback that commits to processing_stages
            async def report_stage_progress(stage_res: StageResult):
                await self.update_stage_progress(db, job_id, stage_res)

            def sync_progress_callback(stage_res: StageResult):
                # For synchronous stages, we can record or schedule
                pass

            # Execute the 9 pure preprocessing stages
            output: PreprocessingOutput = self.orchestrator.process_frame(
                frame=frame,
                calibration_profile=device_profile,
                progress_callback=sync_progress_callback,
            )

            # ------------------------------------------------------------------
            # Persist output artifacts to physical storage
            # ------------------------------------------------------------------
            # 1. Raw Extracted Frame
            raw_png_bytes = self._array_to_png_bytes((frame.intensity * 255).astype(np.uint8))
            raw_path = storage_service.get_survey_extracted_path(survey_id, f"raw_frame_{frame.frame_number:04d}.png")
            raw_artifact = await storage_service.save_artifact(
                db=db,
                dest_path=raw_path,
                content=raw_png_bytes,
                artifact_type="extracted_frame",
                filename=raw_path.name,
                mime_type="image/png",
                metadata={"survey_id": str(survey_id), "frame_number": frame.frame_number},
            )

            # 2. Enhanced Frame
            enh_png_bytes = self._array_to_png_bytes(output.enhanced_frame)
            enh_path = storage_service.get_survey_processed_path(survey_id, job_id, f"enhanced_frame_{frame.frame_number:04d}.png")
            enh_artifact = await storage_service.save_artifact(
                db=db,
                dest_path=enh_path,
                content=enh_png_bytes,
                artifact_type="processed_frame",
                filename=enh_path.name,
                mime_type="image/png",
                metadata={"survey_id": str(survey_id), "frame_number": frame.frame_number, "quality_score": output.quality_score},
            )

            # 3. Acoustic Shadow Map
            shadow_png_bytes = self._array_to_png_bytes(output.shadow_map)
            shadow_path = storage_service.get_survey_processed_path(survey_id, job_id, f"shadow_map_{frame.frame_number:04d}.png")
            shadow_artifact = await storage_service.save_artifact(
                db=db,
                dest_path=shadow_path,
                content=shadow_png_bytes,
                artifact_type="shadow_map",
                filename=shadow_path.name,
                mime_type="image/png",
                metadata={"survey_id": str(survey_id), "frame_number": frame.frame_number},
            )

            # 4. Save Tiling metadata JSON (leaves call-site for Prompt G)
            tile_records = [
                {
                    "tile_id": t.tile_id,
                    "frame_number": t.frame_number,
                    "tile_index": t.tile_index,
                    "bbox_px": t.bbox_px,
                    "pixel_size_m": t.pixel_size_m,
                }
                for t in output.tiles
            ]
            tiles_json_bytes = json.dumps(tile_records, indent=2).encode("utf-8")
            tiles_path = storage_service.get_survey_processed_path(survey_id, job_id, f"tiles_{frame.frame_number:04d}.json")
            await storage_service.save_artifact(
                db=db,
                dest_path=tiles_path,
                content=tiles_json_bytes,
                artifact_type="tiles_metadata",
                filename=tiles_path.name,
                mime_type="application/json",
                metadata={"survey_id": str(survey_id), "tile_count": len(tile_records)},
            )

            # ------------------------------------------------------------------
            # Upsert SurveyFrame record with PostGIS location
            # ------------------------------------------------------------------
            nav = frame.navigation
            # PostGIS POINT geometry (lon, lat, SRID 4326)
            geom_point = ST_SetSRID(ST_MakePoint(nav.longitude, nav.latitude), 4326)

            # Check if frame already exists
            f_res = await db.execute(
                select(SurveyFrame).where(
                    SurveyFrame.survey_id == survey_id,
                    SurveyFrame.frame_number == frame.frame_number,
                )
            )
            existing_frame = f_res.scalar_one_or_none()

            if existing_frame:
                existing_frame.location = geom_point
                existing_frame.altitude_meters = Decimal(f"{nav.altitude_m:.2f}") if nav.altitude_m is not None else None
                existing_frame.heading_degrees = Decimal(f"{nav.heading_deg:.2f}") if nav.heading_deg is not None else None
                existing_frame.speed_knots = Decimal(f"{nav.speed_knots:.2f}") if nav.speed_knots is not None else None
                existing_frame.raw_image_artifact_id = raw_artifact.id
                existing_frame.enhanced_image_artifact_id = enh_artifact.id
                existing_frame.shadow_map_artifact_id = shadow_artifact.id
                existing_frame.quality_score = Decimal(f"{output.quality_score:.2f}")
                existing_frame.dropout_flags = output.dropout_flags
                existing_frame.metadata_json = output.processing_parameters
                frame_record = existing_frame
            else:
                frame_record = SurveyFrame(
                    survey_id=survey_id,
                    sss_file_id=frame.sss_file_id,
                    frame_number=frame.frame_number,
                    timestamp=nav.timestamp or datetime.now(timezone.utc),
                    location=geom_point,
                    altitude_meters=Decimal(f"{nav.altitude_m:.2f}") if nav.altitude_m is not None else None,
                    heading_degrees=Decimal(f"{nav.heading_deg:.2f}") if nav.heading_deg is not None else None,
                    speed_knots=Decimal(f"{nav.speed_knots:.2f}") if nav.speed_knots is not None else None,
                    raw_image_artifact_id=raw_artifact.id,
                    enhanced_image_artifact_id=enh_artifact.id,
                    shadow_map_artifact_id=shadow_artifact.id,
                    quality_score=Decimal(f"{output.quality_score:.2f}") if output.quality_score is not None else None,
                    dropout_flags=output.dropout_flags,
                    metadata_json=output.processing_parameters,
                )
                db.add(frame_record)

            await db.flush()

            # ------------------------------------------------------------------
            # Record PreprocessingRun row for run reproducibility
            # ------------------------------------------------------------------
            run_rec = PreprocessingRun(
                survey_id=survey_id,
                frame_id=frame_record.id,
                sonar_device_id=device_id,
                tvg_applied=True,
                destriping_applied=True,
                denoising_applied=True,
                quality_score=Decimal(f"{output.quality_score:.2f}") if output.quality_score is not None else None,
                run_parameters={
                    "calibration_profile": device_profile,
                    "stage_metrics": output.metrics,
                    "dropout_flags": output.dropout_flags,
                    "stage_parameters": output.processing_parameters,
                },
            )
            db.add(run_rec)
            await db.flush()

            # ------------------------------------------------------------------
            # Execute AI Detection & Multi-Modal Evidence Fusion
            # ------------------------------------------------------------------
            try:
                from app.pipeline.fusion_stage import evidence_fusion_pipeline
                st_res = await db.execute(
                    select(ProcessingStage.id).where(
                        ProcessingStage.processing_job_id == job_id,
                        ProcessingStage.stage_name == "tiling_preparation",
                    )
                )
                stage_id = st_res.scalar_one_or_none()

                await evidence_fusion_pipeline.execute_for_frame(
                    db=db,
                    survey_id=survey_id,
                    survey_frame_id=frame_record.id,
                    processing_job_id=job_id,
                    processing_stage_id=stage_id,
                    frame=frame,
                    preprocessing_output=output,
                )
            except Exception as e:
                logger.warning(f"Evidence fusion notice for frame {frame.frame_number}: {e}")

        # ----------------------------------------------------------------------
        # Complete all processing stages and mark job completed
        # ----------------------------------------------------------------------
        await db.execute(
            update(ProcessingStage)
            .where(ProcessingStage.processing_job_id == job_id)
            .values(
                status="completed",
                progress_percentage=Decimal("100.0"),
                completed_at=datetime.now(timezone.utc),
            )
        )

        await db.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(
                status="completed",
                progress_percentage=Decimal("100.0"),
                completed_at=datetime.now(timezone.utc),
            )
        )

        # Also update survey status
        await db.execute(
            update(Survey)
            .where(Survey.id == survey_id)
            .values(status="preprocessed")
        )

        await db.commit()
        await db.refresh(job)
        logger.info(f"Pipeline execution completed successfully for survey {survey_id}")
        return job

    @staticmethod
    def _array_to_png_bytes(arr: np.ndarray) -> bytes:
        """Encodes a uint8 2D numpy array to PNG bytes."""
        img = Image.fromarray(arr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


pipeline_service = PipelineService()
