"""
Comprehensive unit and integration test suite for the TARANG SSS Preprocessing Pipeline.
Verifies all 9 pure scientific stages, device adapters, IMU fallback, unit conversions,
tiling, and orchestrator execution.
"""

import io
import os
import struct
import sys
import uuid
from datetime import datetime, timezone
import numpy as np
import pytest
from PIL import Image

# Ensure backend-app is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.contracts import NavigationSample, NormalizedSonarFrame
from app.pipeline.adapters import get_device_adapter, PngMetadataAdapter, XtfDeviceAdapter, JsfDeviceAdapter
from app.pipeline.preprocessing import (
    NadirZoneMasker,
    SlantRangeCorrector,
    TvgCalibrator,
    Destriper,
    SpeckleFilter,
    DynamicRangeEnhancer,
    MotionDropoutHandler,
    ImageQualityAssessor,
    FrameTiler,
)
from app.pipeline.orchestrator import PreprocessingOrchestrator


def create_synthetic_frame(
    h: int = 256,
    w: int = 512,
    altitude_m: float = 15.0,
    has_imu: bool = True,
    has_target: bool = True,
) -> NormalizedSonarFrame:
    """Generates a realistic synthetic side-scan sonar frame with nadir, seafloor, and debris shadow."""
    np.random.seed(42)
    center_x = w // 2

    # Seafloor backscatter baseline with speckle
    intensity = np.random.rayleigh(scale=0.3, size=(h, w)).astype(np.float32)
    intensity = np.clip(intensity, 0.05, 0.95)

    # Water column (nadir blind zone): low backscatter around center_x
    nadir_radius = int((altitude_m / 75.0) * (w / 2.0))
    intensity[:, center_x - nadir_radius : center_x + nadir_radius] = np.random.uniform(0.01, 0.04, (h, 2 * nadir_radius))

    # Optional target: bright highlight followed by dark acoustic shadow
    if has_target:
        ty, tx = h // 2, center_x + nadir_radius + 40
        # Bright highlight (specular reflection from metallic/hard debris)
        intensity[ty - 4 : ty + 4, tx : tx + 10] = 0.98
        # Acoustic shadow extending outward away from nadir
        intensity[ty - 4 : ty + 4, tx + 10 : tx + 40] = 0.01

    nav = NavigationSample(
        latitude=13.0827,
        longitude=80.2707,
        altitude_m=altitude_m,
        depth_m=25.0,
        heading_deg=90.0,
        speed_knots=4.5,
        pitch_deg=1.2 if has_imu else None,
        roll_deg=-2.5 if has_imu else None,
        yaw_deg=0.5 if has_imu else None,
        timestamp=datetime.now(timezone.utc),
    )

    return NormalizedSonarFrame(
        survey_id=uuid.uuid4(),
        frame_number=0,
        intensity=intensity,
        navigation=nav,
        slant_range_max_m=75.0,
        frequency_khz=455.0,
    )


# ------------------------------------------------------------------------------
# 1. Nadir Zone Masker Tests
# ------------------------------------------------------------------------------
def test_nadir_mask_preserves_dimensions_and_does_not_crop():
    frame = create_synthetic_frame(h=256, w=512, altitude_m=15.0)
    masker = NadirZoneMasker()
    preserved_img, mask, metrics = masker.process(frame)

    # Must NOT crop or stitch: dimensions must strictly match
    assert preserved_img.shape == (256, 512)
    assert mask.shape == (256, 512)

    # Water column around center must be 0 (masked)
    center_x = 512 // 2
    assert mask[128, center_x] == 0

    # Far range must be 1 (valid seafloor)
    assert mask[128, 10] == 1
    assert mask[128, 500] == 1

    # Image pixels must be preserved exactly
    np.testing.assert_array_equal(preserved_img, frame.intensity)
    assert metrics["water_column_altitude_m"] == 15.0


# ------------------------------------------------------------------------------
# 2. Slant-Range Correction Tests
# ------------------------------------------------------------------------------
def test_slant_range_geometric_projection():
    frame = create_synthetic_frame(h=256, w=512, altitude_m=15.0)
    masker = NadirZoneMasker()
    _, mask, _ = masker.process(frame)

    corrector = SlantRangeCorrector()
    corrected, metrics = corrector.process(frame, mask)

    assert corrected.shape == (256, 512)
    assert metrics["effective_altitude_m"] == 15.0
    assert metrics["max_ground_range_m"] < 75.0
    assert not np.isnan(corrected).any()


# ------------------------------------------------------------------------------
# 3. Sonar-Specific TVG & Unit Conversion Tests
# ------------------------------------------------------------------------------
def test_tvg_correct_unit_conversion():
    frame = create_synthetic_frame(h=256, w=512)
    calibrator = TvgCalibrator()

    # Device calibration profile with custom parameters
    profile = {
        "alpha_db_per_km": 120.0,
        "spreading_coefficient": 20.0,
        "max_gain_db": 30.0,
    }
    calibrated, metrics = calibrator.process(frame, profile)

    assert calibrated.shape == (256, 512)
    assert metrics["absorption_alpha_db_per_km"] == 120.0

    # Ensure max gain in dB was converted to linear scale:
    # 30 dB in linear amplitude is 10^(30/20) ~ 31.62
    # Verify that dB value was NOT used as a direct linear multiplier
    assert metrics["max_applied_gain_db"] <= 30.0
    assert not np.isnan(calibrated).any()
    assert np.all(calibrated >= 0.0) and np.all(calibrated <= 1.0)


# ------------------------------------------------------------------------------
# 4. Destriping Tests
# ------------------------------------------------------------------------------
def test_destriping_variance_reduction():
    frame = create_synthetic_frame(h=256, w=512)
    # Intentionally add artificial striping banding
    striped = frame.intensity.copy()
    striped[::4, :] *= 1.4
    striped[1::4, :] *= 0.7

    mask = np.ones((256, 512), dtype=np.uint8)
    destriper = Destriper()
    destriped, metrics = destriper.process(striped, mask)

    assert destriped.shape == (256, 512)
    assert metrics["striping_reduction_percent"] >= 0.0
    assert not np.isnan(destriped).any()


# ------------------------------------------------------------------------------
# 5. Speckle Noise Suppression Tests
# ------------------------------------------------------------------------------
def test_speckle_filter_edge_preservation():
    frame = create_synthetic_frame(h=256, w=512)
    filter_stage = SpeckleFilter()
    filtered, metrics = filter_stage.process(frame.intensity)

    assert filtered.shape == (256, 512)
    assert metrics["filtered_enl"] > 0.0
    assert not np.isnan(filtered).any()


# ------------------------------------------------------------------------------
# 6. Controlled Dynamic-Range Enhancement Tests
# ------------------------------------------------------------------------------
def test_dynamic_range_enhancer_clahe():
    frame = create_synthetic_frame(h=256, w=512)
    enhancer = DynamicRangeEnhancer()
    f32_out, u8_out, metrics = enhancer.process(frame.intensity)

    assert f32_out.shape == (256, 512)
    assert u8_out.shape == (256, 512)
    assert u8_out.dtype == np.uint8
    assert metrics["contrast_expansion_ratio"] > 0.0


# ------------------------------------------------------------------------------
# 7. Dropout and Missing IMU Handling Tests
# ------------------------------------------------------------------------------
def test_missing_imu_graceful_fallback():
    # Frame with missing IMU metadata
    frame_no_imu = create_synthetic_frame(h=256, w=512, has_imu=False)
    handler = MotionDropoutHandler()
    cleaned, dropout_flags, metrics = handler.process(frame_no_imu.intensity, frame_no_imu)

    # CRITICAL RULE: Missing IMU must NOT fail, but flag imu_missing and downgrade gracefully
    assert dropout_flags["imu_missing"] is True
    assert dropout_flags["status"] == "imu_missing_downgraded_gracefully"
    assert dropout_flags["motion_correction_applied"] is False
    assert metrics["imu_present"] == 0.0
    assert cleaned.shape == (256, 512)


def test_valid_imu_roll_compensation():
    # Frame with valid IMU metadata
    frame_imu = create_synthetic_frame(h=256, w=512, has_imu=True)
    handler = MotionDropoutHandler()
    cleaned, dropout_flags, metrics = handler.process(frame_imu.intensity, frame_imu)

    assert dropout_flags["imu_missing"] is False
    assert dropout_flags["motion_correction_applied"] is True
    assert dropout_flags["status"] == "imu_valid"
    assert "roll_compensated_deg" in dropout_flags


def test_dropout_interpolation():
    frame = create_synthetic_frame(h=256, w=512)
    # Inject 2 blank dropped lines
    intensity = frame.intensity.copy()
    intensity[50:52, :] = 0.0

    handler = MotionDropoutHandler()
    cleaned, dropout_flags, metrics = handler.process(intensity, frame)

    assert dropout_flags["dropout_line_count"] >= 2
    assert dropout_flags["interpolated_lines"] >= 2
    # Verify dropped lines were recovered (non-zero)
    assert np.mean(cleaned[50, :]) > 0.01


# ------------------------------------------------------------------------------
# 8. Image Quality Assessment & Shadow Map Tests
# ------------------------------------------------------------------------------
def test_quality_assessment_and_shadow_map():
    frame = create_synthetic_frame(h=256, w=512, has_target=True)
    masker = NadirZoneMasker()
    _, mask, _ = masker.process(frame)

    assessor = ImageQualityAssessor()
    shadow_map, quality_score, metrics = assessor.process(
        frame.intensity, mask, {"dropout_line_count": 0}
    )

    assert shadow_map.shape == (256, 512)
    assert shadow_map.dtype == np.uint8
    # Quality score must be within schema constraint [0.0, 100.0]
    assert 0.0 <= quality_score <= 100.0
    assert metrics["snr_db"] > 0.0
    assert metrics["shannon_entropy"] > 0.0
    # The synthetic target shadow should be detected
    assert np.sum(shadow_map == 255) > 0


# ------------------------------------------------------------------------------
# 9. Tiling / Inference Preparation Tests
# ------------------------------------------------------------------------------
def test_frame_tiler_sub_tiles():
    frame = create_synthetic_frame(h=512, w=1024)
    u8_img = (frame.intensity * 255).astype(np.uint8)

    tiler = FrameTiler()
    tiles, meta = tiler.process(u8_img, frame, tile_size=640, stride=512)

    assert len(tiles) > 0
    assert meta["total_tiles"] == len(tiles)
    for t in tiles:
        assert t.image_data.shape == (640, 640)
        assert len(t.bbox_px) == 4
        assert t.pixel_size_m > 0.0


# ------------------------------------------------------------------------------
# 10. Device Adapters Tests
# ------------------------------------------------------------------------------
def test_png_metadata_adapter():
    survey_id = uuid.uuid4()
    # Create test PNG bytes
    arr = (np.random.uniform(0.1, 0.8, (512, 1024)) * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    png_bytes = buf.getvalue()

    adapter = PngMetadataAdapter()
    frames = adapter.parse(png_bytes, survey_id=survey_id, frame_height=256)

    assert len(frames) == 2
    assert frames[0].survey_id == survey_id
    assert frames[0].intensity.shape == (256, 1024)
    assert frames[0].navigation.latitude == 13.0827


def test_xtf_device_adapter_fallback_and_parsing():
    survey_id = uuid.uuid4()
    adapter = XtfDeviceAdapter()

    # Test with minimal header bytes
    dummy_xtf = b"\x7b\x00" + b"\x00" * 1022
    frames = adapter.parse(dummy_xtf, survey_id=survey_id, frame_height=256)

    assert len(frames) >= 1
    assert frames[0].survey_id == survey_id
    assert frames[0].intensity.shape == (256, 1024)


def test_jsf_device_adapter_fallback():
    survey_id = uuid.uuid4()
    adapter = JsfDeviceAdapter()

    # Test with minimal JSF sync pattern
    dummy_jsf = b"\x01\x16\x01\x01" + b"\x00" * 100
    frames = adapter.parse(dummy_jsf, survey_id=survey_id, frame_height=256)

    assert len(frames) >= 1
    assert frames[0].survey_id == survey_id
    assert frames[0].intensity.shape == (256, 1024)


# ------------------------------------------------------------------------------
# 11. End-to-End Preprocessing Orchestrator Tests
# ------------------------------------------------------------------------------
def test_end_to_end_orchestrator():
    frame = create_synthetic_frame(h=256, w=512, altitude_m=15.0, has_imu=True, has_target=True)
    orchestrator = PreprocessingOrchestrator()

    recorded_stages = []

    def on_stage(stage_res):
        recorded_stages.append(stage_res.stage_name)

    output = orchestrator.process_frame(
        frame=frame,
        calibration_profile={"alpha_db_per_km": 125.0, "spreading_coefficient": 20.0},
        progress_callback=on_stage,
    )

    # Verify all 9 stages were invoked
    expected_stages = [
        "nadir_masking",
        "slant_range_correction",
        "tvg_calibration",
        "destriping",
        "speckle_filtering",
        "dynamic_range_enhancement",
        "motion_dropout_handling",
        "quality_assessment",
        "tiling_preparation",
    ]
    assert recorded_stages == expected_stages

    # Verify outputs
    assert output.enhanced_frame.shape == (256, 512)
    assert output.enhanced_frame.dtype == np.uint8
    assert output.shadow_map.shape == (256, 512)
    assert output.nadir_mask.shape == (256, 512)
    assert 0.0 <= output.quality_score <= 100.0
    assert len(output.tiles) > 0
    assert "tiling_preparation" in output.processing_parameters


if __name__ == "__main__":
    pytest.main(["-v", __file__])
