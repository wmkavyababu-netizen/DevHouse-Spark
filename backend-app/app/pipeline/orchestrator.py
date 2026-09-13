import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from app.pipeline.contracts import (
    NormalizedSonarFrame,
    PreprocessingOutput,
    StageResult,
    TileSample,
)
from app.pipeline.preprocessing.destriping import Destriper
from app.pipeline.preprocessing.enhancement import DynamicRangeEnhancer
from app.pipeline.preprocessing.motion_dropout import MotionDropoutHandler
from app.pipeline.preprocessing.nadir_mask import NadirZoneMasker
from app.pipeline.preprocessing.quality_assessment import ImageQualityAssessor
from app.pipeline.preprocessing.slant_range import SlantRangeCorrector
from app.pipeline.preprocessing.speckle_filter import SpeckleFilter
from app.pipeline.preprocessing.tiling import FrameTiler
from app.pipeline.preprocessing.tvg_calibration import TvgCalibrator


# Standard pipeline stage definitions in order
STAGE_DEFINITIONS = [
    ("nadir_masking", 1, "Nadir-Zone Masking (Preserving Water Column)"),
    ("slant_range_correction", 2, "Slant-Range / Ground-Range Geometry Correction"),
    ("tvg_calibration", 3, "Sonar-Specific TVG & Absorption Calibration"),
    ("destriping", 4, "Along-Track Destriping & Baseline Equalization"),
    ("speckle_filtering", 5, "Edge-Preserving Acoustic Speckle Suppression"),
    ("dynamic_range_enhancement", 6, "Controlled Dynamic-Range CLAHE Enhancement"),
    ("motion_dropout_handling", 7, "Motion Telemetry & Dropout Handling"),
    ("quality_assessment", 8, "Image Quality Assessment & Shadow Map Extraction"),
    ("tiling_preparation", 9, "Overlapping Tiling & AI Inference Preparation"),
]


class PreprocessingOrchestrator:
    """
    Executes the side-scan sonar preprocessing pipeline as an ordered sequence
    of pure, independently callable stages according to the TARANG v6.2 specification.
    """

    def __init__(self):
        self.nadir_masker = NadirZoneMasker()
        self.slant_range_corrector = SlantRangeCorrector()
        self.tvg_calibrator = TvgCalibrator()
        self.destriper = Destriper()
        self.speckle_filter = SpeckleFilter()
        self.dynamic_enhancer = DynamicRangeEnhancer()
        self.motion_handler = MotionDropoutHandler()
        self.quality_assessor = ImageQualityAssessor()
        self.tiler = FrameTiler()

    def process_frame(
        self,
        frame: NormalizedSonarFrame,
        calibration_profile: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[StageResult], None]] = None,
    ) -> PreprocessingOutput:
        """
        Executes all preprocessing stages on a single NormalizedSonarFrame.
        Invokes progress_callback after each stage to report progress and parameters.
        """
        all_stage_parameters: Dict[str, Any] = {}
        all_metrics: Dict[str, float] = {}

        # ----------------------------------------------------------------------
        # Stage 1: Nadir-Zone Masking (Mask, do NOT crop/stitch)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        intensity, nadir_mask, nadir_metrics = self.nadir_masker.process(frame)
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_metrics.update(nadir_metrics)
        all_stage_parameters["nadir_masking"] = nadir_metrics

        if progress_callback:
            progress_callback(StageResult(
                stage_name="nadir_masking",
                stage_order=1,
                status="completed",
                progress_percentage=11.1,
                execution_time_ms=t_stage,
                parameters_used=nadir_metrics,
                log_message=f"Nadir masked (half-width: {nadir_metrics['nadir_half_width_samples']} samples)",
            ))

        # ----------------------------------------------------------------------
        # Stage 2: Slant-Range / Geometry Correction
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        corrected_geom, slant_metrics = self.slant_range_corrector.process(frame, nadir_mask)
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_metrics.update(slant_metrics)
        all_stage_parameters["slant_range_correction"] = slant_metrics

        if progress_callback:
            progress_callback(StageResult(
                stage_name="slant_range_correction",
                stage_order=2,
                status="completed",
                progress_percentage=22.2,
                execution_time_ms=t_stage,
                parameters_used=slant_metrics,
                log_message=f"Slant-range projected (effective altitude: {slant_metrics['effective_altitude_m']}m)",
            ))

        # ----------------------------------------------------------------------
        # Stage 3: Sonar-Specific TVG / Calibration (correct units, dB to linear)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        tvg_frame = NormalizedSonarFrame(
            survey_id=frame.survey_id,
            frame_number=frame.frame_number,
            intensity=corrected_geom,
            navigation=frame.navigation,
            slant_range_max_m=frame.slant_range_max_m,
            frequency_khz=frame.frequency_khz,
        )
        tvg_calibrated, tvg_metrics = self.tvg_calibrator.process(tvg_frame, calibration_profile)
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_metrics.update(tvg_metrics)
        all_stage_parameters["tvg_calibration"] = tvg_metrics

        if progress_callback:
            progress_callback(StageResult(
                stage_name="tvg_calibration",
                stage_order=3,
                status="completed",
                progress_percentage=33.3,
                execution_time_ms=t_stage,
                parameters_used=tvg_metrics,
                log_message=f"TVG calibrated (alpha: {tvg_metrics['absorption_alpha_db_per_km']} dB/km, max gain: {tvg_metrics['max_applied_gain_db']:.1f} dB)",
            ))

        # ----------------------------------------------------------------------
        # Stage 4: Destriping
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        destriped, destripe_metrics = self.destriper.process(tvg_calibrated, nadir_mask)
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_metrics.update(destripe_metrics)
        all_stage_parameters["destriping"] = destripe_metrics

        if progress_callback:
            progress_callback(StageResult(
                stage_name="destriping",
                stage_order=4,
                status="completed",
                progress_percentage=44.4,
                execution_time_ms=t_stage,
                parameters_used=destripe_metrics,
                log_message=f"Destriped along-track (variance reduction: {destripe_metrics['striping_reduction_percent']:.1f}%)",
            ))

        # ----------------------------------------------------------------------
        # Stage 5: Speckle / Noise Suppression
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        despeckled, speckle_metrics = self.speckle_filter.process(destriped)
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_metrics.update(speckle_metrics)
        all_stage_parameters["speckle_filtering"] = speckle_metrics

        if progress_callback:
            progress_callback(StageResult(
                stage_name="speckle_filtering",
                stage_order=5,
                status="completed",
                progress_percentage=55.5,
                execution_time_ms=t_stage,
                parameters_used=speckle_metrics,
                log_message=f"Speckle suppressed (ENL factor: {speckle_metrics['enl_improvement_factor']:.2f}x)",
            ))

        # ----------------------------------------------------------------------
        # Stage 6: Controlled Dynamic-Range Enhancement
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        enhanced_f32, enhanced_uint8, enh_metrics = self.dynamic_enhancer.process(despeckled)
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_metrics.update(enh_metrics)
        all_stage_parameters["dynamic_range_enhancement"] = enh_metrics

        if progress_callback:
            progress_callback(StageResult(
                stage_name="dynamic_range_enhancement",
                stage_order=6,
                status="completed",
                progress_percentage=66.6,
                execution_time_ms=t_stage,
                parameters_used=enh_metrics,
                log_message=f"CLAHE dynamic range expanded (contrast ratio: {enh_metrics['contrast_expansion_ratio']:.2f}x)",
            ))

        # ----------------------------------------------------------------------
        # Stage 7: Dropout / Motion / Quality Handling (graceful IMU fallback)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        motion_cleaned, dropout_flags, motion_metrics = self.motion_handler.process(enhanced_f32, frame)
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_metrics.update(motion_metrics)
        all_stage_parameters["motion_dropout_handling"] = {**dropout_flags, **motion_metrics}

        if progress_callback:
            progress_callback(StageResult(
                stage_name="motion_dropout_handling",
                stage_order=7,
                status="completed",
                progress_percentage=77.7,
                execution_time_ms=t_stage,
                parameters_used=all_stage_parameters["motion_dropout_handling"],
                log_message=f"Motion telemetry handled (status: {dropout_flags['status']})",
            ))

        # ----------------------------------------------------------------------
        # Stage 8: Image Quality Assessment & Shadow Map Extraction
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        shadow_map, quality_score, iqa_metrics = self.quality_assessor.process(
            motion_cleaned, nadir_mask, dropout_flags
        )
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_metrics.update(iqa_metrics)
        all_stage_parameters["quality_assessment"] = iqa_metrics

        if progress_callback:
            progress_callback(StageResult(
                stage_name="quality_assessment",
                stage_order=8,
                status="completed",
                progress_percentage=88.8,
                execution_time_ms=t_stage,
                parameters_used=iqa_metrics,
                log_message=f"IQA computed (quality score: {quality_score:.1f}/100, SNR: {iqa_metrics['snr_db']:.1f} dB)",
            ))

        # Final enhanced uint8 frame
        final_enhanced_u8 = (motion_cleaned * 255.0).astype(np.uint8)

        # ----------------------------------------------------------------------
        # Stage 9: Tiling / Inference Preparation (Leaves clear call-site for Prompt G)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        tiles, tiling_metadata = self.tiler.process(final_enhanced_u8, frame)
        t_stage = (time.perf_counter() - t0) * 1000.0
        all_stage_parameters["tiling_preparation"] = tiling_metadata

        if progress_callback:
            progress_callback(StageResult(
                stage_name="tiling_preparation",
                stage_order=9,
                status="completed",
                progress_percentage=100.0,
                execution_time_ms=t_stage,
                parameters_used=tiling_metadata,
                log_message=f"Tiled frame into {len(tiles)} patches ready for AI inference",
            ))

        return PreprocessingOutput(
            enhanced_frame=final_enhanced_u8,
            shadow_map=shadow_map,
            nadir_mask=(nadir_mask * 255).astype(np.uint8),
            quality_score=quality_score,
            dropout_flags=dropout_flags,
            metrics=all_metrics,
            processing_parameters=all_stage_parameters,
            tiles=tiles,
        )
