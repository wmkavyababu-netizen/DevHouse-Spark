"""
Comprehensive test suite for Prompts G and H:
1. Model Registry and checksum integrity verification
2. Local in-process YOLOv8 inference (offline, zero network calls)
3. Explainable AI (XAI) Grad-CAM saliency heatmaps
4. Acoustic physics validation (shadow consistency and geometry)
5. Geodesic geotagging (WGS-84 coordinate projection)
6. Multi-modal confidence fusion
7. Spatial target deduplication, mapping, and history audit
8. REST API /api/v1/detections/infer endpoint
"""

import base64
import io
import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
import numpy as np
import pytest
from PIL import Image
import httpx

# Ensure backend-app is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.security import register_cached_public_key
from app.ai.models.registry import model_registry, TARANG_CLASSES
from app.ai.inference.detector import YOLODetector
from app.ai.xai.gradcam import xai_generator
from app.pipeline.physics.validator import physics_validator
from app.pipeline.geotagging.geotagger import geodesic_geotagger
from app.pipeline.confidence.fusion import confidence_fuser
from app.pipeline.deduplication.cluster import target_clusterer


# ------------------------------------------------------------------------------
# 1. Model Registry & Checksum Integrity Tests
# ------------------------------------------------------------------------------
def test_model_registry_baseline_and_checksum():
    model_path, checksum = model_registry.ensure_baseline_model_exists("v1.0")
    assert model_path.exists()
    assert len(checksum) == 64  # Valid SHA-256 string

    # Re-compute checksum and verify exact match
    computed = model_registry.compute_sha256(model_path)
    assert computed == checksum

    # In-memory caching: second load returns identical cached instance
    m1 = model_registry.load_model("v1.0", checksum)
    m2 = model_registry.load_model("v1.0", checksum)
    assert m1 is m2

    # Checksum mismatch detection
    with pytest.raises(ValueError) as exc_info:
        model_registry.load_model("v1.0", expected_checksum="0" * 64)
    assert "integrity verification failed" in str(exc_info.value)


# ------------------------------------------------------------------------------
# 2. Local In-Process YOLO Inference Tests (Zero Network Calls)
# ------------------------------------------------------------------------------
def test_yolo_detector_local_inference():
    yolo_model = model_registry.load_model("v1.0")
    detector = YOLODetector(yolo_model, default_conf=0.1, default_iou=0.45)

    # Synthetic 640x640 test tile
    test_img = np.random.uniform(0.1, 0.8, (640, 640)).astype(np.float32)
    # Inject a distinct synthetic target box
    test_img[200:260, 300:360] = 0.99

    results = detector.detect(test_img, conf_threshold=0.05)
    assert isinstance(results, list)

    # Batch detection test
    batch_res = detector.detect_batch([test_img, test_img], conf_threshold=0.05)
    assert len(batch_res) == 2


# ------------------------------------------------------------------------------
# 3. Explainable AI (XAI) Saliency Tests
# ------------------------------------------------------------------------------
def test_xai_saliency_heatmap_generation():
    img = np.zeros((256, 256), dtype=np.uint8)
    img[100:150, 100:150] = 240  # Highlight box

    bbox = [100.0, 100.0, 150.0, 150.0]
    heatmap_bytes, saliency_score, explanation = xai_generator.generate_saliency_map(
        image=img,
        bbox=bbox,
        class_id=0,
        class_name="crab_pot",
        confidence=0.85,
    )

    assert isinstance(heatmap_bytes, bytes)
    assert len(heatmap_bytes) > 0
    # Must be valid PNG
    assert heatmap_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    # Saliency score bounded strictly in [0.0, 1.0]
    assert 0.0 <= saliency_score <= 1.0
    assert explanation["method"] == "grad_cam_sonar"
    assert explanation["class_name"] == "crab_pot"


# ------------------------------------------------------------------------------
# 4. Acoustic Physics Validation Tests
# ------------------------------------------------------------------------------
def test_physics_validation_plausible_target():
    # Target on starboard at x=350 (nadir is at 256 in 512-wide frame)
    # Theoretical shadow should extend to the right (increasing x)
    frame_w, frame_h = 512, 256
    shadow_map = np.zeros((frame_h, frame_w), dtype=np.uint8)
    # Add acoustic shadow directly adjacent to target extending right
    shadow_map[100:120, 360:410] = 255

    bbox = [330.0, 100.0, 360.0, 120.0]
    res = physics_validator.validate_detection(
        bbox=bbox,
        target_class_id=0,  # crab_pot
        frame_width=frame_w,
        frame_height=frame_h,
        altitude_m=15.0,
        slant_range_max_m=75.0,
        shadow_map=shadow_map,
    )

    assert res["is_plausible"] is True
    assert res["shadow_consistency_score"] >= 0.35
    assert res["slant_range_meters"] > 15.0
    assert res["validation_details"]["is_port"] is False


def test_physics_validation_inverted_shadow_failure():
    # Target on starboard (x=350), but shadow points toward nadir (to the left)
    frame_w, frame_h = 512, 256
    shadow_map = np.zeros((frame_h, frame_w), dtype=np.uint8)
    # Inverted shadow pointing toward nadir
    shadow_map[100:120, 280:330] = 255

    bbox = [330.0, 100.0, 360.0, 120.0]
    res = physics_validator.validate_detection(
        bbox=bbox,
        target_class_id=0,
        frame_width=frame_w,
        frame_height=frame_h,
        altitude_m=15.0,
        slant_range_max_m=75.0,
        shadow_map=shadow_map,
    )

    # Unphysical shadow direction must be penalized
    assert res["is_plausible"] is False
    assert res["shadow_consistency_score"] <= 0.20
    assert res["validation_details"]["directional_valid"] is False


def test_physics_validation_in_water_column():
    # Target positioned inside nadir water column zone (x=258, nadir is 256)
    frame_w, frame_h = 512, 256
    bbox = [256.0, 100.0, 260.0, 120.0]
    res = physics_validator.validate_detection(
        bbox=bbox,
        target_class_id=0,
        frame_width=frame_w,
        frame_height=frame_h,
        altitude_m=15.0,
        slant_range_max_m=75.0,
    )

    # In-water-column target fails seafloor plausibility
    assert res["is_plausible"] is False
    assert res["validation_details"]["in_water_column"] is True


# ------------------------------------------------------------------------------
# 5. Geodesic Geotagging Tests
# ------------------------------------------------------------------------------
def test_geodesic_geotag_calculation():
    towfish_lat = 13.0827
    towfish_lon = 80.2707
    heading_deg = 90.0  # Heading due East

    # Target on starboard side (x=384 in 512-wide frame, nadir at 256)
    # If heading East (90 deg), starboard is South (180 deg)
    # Therefore, target latitude should decrease (move South)
    target_lat, target_lon, uncertainty_m, details = geodesic_geotagger.calculate_geotag(
        towfish_lat=towfish_lat,
        towfish_lon=towfish_lon,
        heading_deg=heading_deg,
        bbox=[360.0, 120.0, 400.0, 136.0],
        frame_width=512,
        frame_height=256,
        altitude_m=15.0,
        slant_range_max_m=75.0,
    )

    assert target_lat < towfish_lat  # Shifted South
    assert uncertainty_m > 0.0
    assert details["ground_range_m"] > 0.0


# ------------------------------------------------------------------------------
# 6. Confidence Fusion Tests
# ------------------------------------------------------------------------------
def test_confidence_fusion():
    # Plausible target
    fused, details = confidence_fuser.fuse(
        ai_confidence=0.85,
        physics_score=0.90,
        frame_quality_score=80.0,
        is_physically_plausible=True,
    )

    # Expected: 0.55 * 0.85 + 0.30 * 0.90 + 0.15 * 0.80 = 0.4675 + 0.270 + 0.120 = 0.8575
    assert 0.84 <= fused <= 0.88
    assert details["applied_penalty"] is False

    # Implausible target (penalty applied)
    fused_bad, details_bad = confidence_fuser.fuse(
        ai_confidence=0.85,
        physics_score=0.10,
        frame_quality_score=80.0,
        is_physically_plausible=False,
    )
    assert details_bad["applied_penalty"] is True
    assert fused_bad < fused


# ------------------------------------------------------------------------------
# 7. Spatial Target Deduplication Distance Tests
# ------------------------------------------------------------------------------
def test_haversine_distance_calculation():
    lat1, lon1 = 13.0827, 80.2707
    # 0.0001 deg latitude is roughly 11.1 meters
    lat2, lon2 = 13.0828, 80.2707
    dist_m = target_clusterer.haversine_distance_m(lat1, lon1, lat2, lon2)
    assert 10.0 <= dist_m <= 12.5


# ------------------------------------------------------------------------------
# 8. REST API /api/v1/detections/infer Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_detections_classes():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/detections/classes")
        assert response.status_code == 200
        classes = response.json()
        assert classes["0"] == "crab_pot"
        assert classes["1"] == "submarine_pipeline"
        assert classes["2"] == "shipwreck"
        assert classes["3"] == "ghost_net"
        assert classes["4"] == "mine_cylinder"
        assert classes["5"] == "unknown"


@pytest.mark.asyncio
async def test_api_detections_infer_endpoint():
    # Register test public key for auth
    try:
        from tests.test_core_security import public_key_pem, TEST_KID, create_test_jwt
    except ImportError:
        from test_core_security import public_key_pem, TEST_KID, create_test_jwt
    register_cached_public_key(TEST_KID, public_key_pem)
    token = create_test_jwt(roles=["ROLE_OPERATOR", "ROLE_ANALYST"])

    # Create synthetic test image and base64 encode
    arr = (np.random.uniform(0.1, 0.8, (256, 256)) * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    from app.db.session import get_db

    async def override_get_db():
        yield None

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/detections/infer",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "image_base64": b64_img,
                    "confidence_threshold": 0.05,
                    "iou_threshold": 0.45,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "model_version" in data
            assert "model_checksum" in data
            assert "detections" in data
            assert isinstance(data["detections"], list)
    finally:
        app.dependency_overrides.pop(get_db, None)


# ------------------------------------------------------------------------------
# 9. Synthetic Known-Geometry Unit Tests
# ------------------------------------------------------------------------------
def test_physics_validation_synthetic_known_geometry():
    """
    Unit test for known acoustic shadow geometry:
    Target height H = 1.0m (mine_cylinder), Altitude h = 15.0m, Slant Range Rs = 45.0m.
    Acoustic equation: Ls = (H * Rs) / (h - H) = (1.0 * 45.0) / (15.0 - 1.0) = 45 / 14 = 3.214m.
    Verifies recovery of H via: H = (h * Ls) / (Rs + Ls) = (15 * 3.214) / (45 + 3.214) = 1.00m.
    """
    frame_w, frame_h = 512, 256
    slant_max_m = 75.0
    pixel_size_m = slant_max_m / (frame_w / 2.0)

    # Target centered at slant range ~45m on starboard:
    bbox = [400.0, 100.0, 419.0, 119.0]

    # Shadow length in pixels: 3.214m / pixel_size_m = 10.97 px (~11 px)
    shadow_map = np.zeros((frame_h, frame_w), dtype=np.uint8)
    shadow_map[100:120, 420:431] = 255  # 11 px wide shadow extending away from nadir

    res = physics_validator.validate_detection(
        bbox=bbox,
        target_class_id=4,  # mine_cylinder (expected H = 1.0m)
        frame_width=frame_w,
        frame_height=frame_h,
        altitude_m=15.0,
        slant_range_max_m=slant_max_m,
        beam_width_deg=1.0,
        shadow_map=shadow_map,
    )

    assert res["is_plausible"] is True
    assert 40.0 <= res["slant_range_meters"] <= 50.0
    assert 2.5 <= res["acoustic_shadow_length_meters"] <= 4.0
    assert 0.6 <= res["validation_details"]["beam_expansion_m"] <= 1.0
    assert res["shadow_consistency_score"] >= 0.70


# ------------------------------------------------------------------------------
# 10. Honest OOD / Unknown Detection Representation Tests
# ------------------------------------------------------------------------------
def test_ood_unclassified_detection_honesty():
    """
    Verifies that unclassified / out-of-distribution detections are surfaced
    honestly as class 5 ('unknown') with is_ood=True, and NOT forced into known classes 0-4.
    """
    import torch

    mock_model = MagicMock()
    mock_box = MagicMock()
    mock_box.xyxy = torch.tensor([[100.0, 100.0, 150.0, 150.0]])
    mock_box.conf = torch.tensor([0.75])
    mock_box.cls = torch.tensor([99])  # Unfamiliar / out-of-distribution class

    mock_res = MagicMock()
    mock_res.boxes = mock_box
    mock_model.predict.return_value = [mock_res]

    detector = YOLODetector(model=mock_model)
    synthetic_img = np.zeros((256, 256, 3), dtype=np.uint8)
    detections = detector.detect(synthetic_img)

    assert len(detections) == 1
    det = detections[0]
    assert det["class_id"] == 5
    assert det["class_name"] == "unknown"
    assert det["is_ood"] is True
    assert det["class_id"] not in (0, 1, 2, 3, 4)


# ------------------------------------------------------------------------------
# 11. Full Run: Survey Frame -> Detections -> Evidence Fusion -> Targets
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_full_run_survey_evidence_fusion():
    """
    Confirms a full run on a survey frame produces:
    detections -> xai_evidence -> physics_validation -> geotags (one authoritative each)
    -> targets with correct detection_target_mapping and target_history.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.pipeline.fusion_stage import EvidenceFusionPipeline
    from app.pipeline.contracts import NormalizedSonarFrame, NavigationSample, PreprocessingOutput
    from app.models.detection import Detection, XaiEvidence, PhysicsValidation, Geotag
    from app.models.target import Target, DetectionTargetMapping, TargetHistory
    from app.models.sonar import StorageArtifact

    added_objects = []

    mock_db = MagicMock(spec=AsyncSession)
    def fake_add(obj):
        added_objects.append(obj)
    mock_db.add.side_effect = fake_add
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()

    # Mock DB query for existing targets (returns empty list so targets are newly created)
    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value.all.return_value = []
    mock_exec_res.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_exec_res)

    survey_id = uuid.uuid4()
    frame_id = uuid.uuid4()
    job_id = uuid.uuid4()

    nav = NavigationSample(
        latitude=13.0827,
        longitude=80.2707,
        altitude_m=15.0,
        depth_m=20.0,
        heading_deg=90.0,
        speed_knots=3.5,
    )
    frame = NormalizedSonarFrame(
        survey_id=survey_id,
        frame_number=1,
        intensity=np.ones((256, 512), dtype=np.float32) * 0.5,
        port_channels=np.ones((256, 256), dtype=np.float32) * 0.5,
        starboard_channels=np.ones((256, 256), dtype=np.float32) * 0.5,
        navigation=nav,
        slant_range_max_m=75.0,
    )

    shadow_map = np.zeros((256, 512), dtype=np.uint8)
    shadow_map[100:120, 360:390] = 255

    prep_out = PreprocessingOutput(
        enhanced_frame=np.ones((256, 512), dtype=np.uint8) * 128,
        shadow_map=shadow_map,
        nadir_mask=np.zeros((256, 512), dtype=np.uint8),
        quality_score=85.0,
        dropout_flags={"dropout_count": 0},
        metrics={"snr_db": 18.5},
        tiles=[],
        processing_parameters={"destriping": True},
    )

    pipeline = EvidenceFusionPipeline()

    mock_detector = MagicMock()
    mock_detector.detect.return_value = [
        {
            "class_id": 0,
            "class_name": "crab_pot",
            "confidence": 0.88,
            "bbox": [340.0, 100.0, 360.0, 120.0],
            "raw_class_id": 0,
            "is_ood": False,
        },
        {
            "class_id": 5,
            "class_name": "unknown",
            "confidence": 0.65,
            "bbox": [150.0, 80.0, 180.0, 110.0],
            "raw_class_id": 99,
            "is_ood": True,
        }
    ]

    mock_artifact = StorageArtifact(
        id=uuid.uuid4(),
        artifact_type="xai_saliency_heatmap",
        storage_uri="storage://surveys/test/xai.png",
        filename="xai.png",
        mime_type="image/png",
        file_size_bytes=1024,
        checksum_sha256="a" * 64,
    )

    with patch("app.pipeline.fusion_stage.storage_service.save_artifact", AsyncMock(return_value=mock_artifact)):
        with patch("app.pipeline.fusion_stage.YOLODetector", return_value=mock_detector):
            detections = await pipeline.execute_for_frame(
                db=mock_db,
                survey_id=survey_id,
                survey_frame_id=frame_id,
                processing_job_id=job_id,
                processing_stage_id=None,
                frame=frame,
                preprocessing_output=prep_out,
            )

    assert len(detections) == 2

    # 1. Verify Detections
    created_dets = [o for o in added_objects if isinstance(o, Detection)]
    assert len(created_dets) == 2

    # 2. Verify XaiEvidence (one-to-one per detection)
    xai_recs = [o for o in added_objects if isinstance(o, XaiEvidence)]
    assert len(xai_recs) == 2
    det_ids_xai = {x.detection_id for x in xai_recs}
    assert det_ids_xai == {d.id for d in created_dets}
    for x in xai_recs:
        assert 0.0 <= float(x.saliency_score) <= 1.0
        assert x.heatmap_artifact_id == mock_artifact.id

    # 3. Verify PhysicsValidation (one-to-one per detection)
    phys_recs = [o for o in added_objects if isinstance(o, PhysicsValidation)]
    assert len(phys_recs) == 2
    det_ids_phys = {p.detection_id for p in phys_recs}
    assert det_ids_phys == {d.id for d in created_dets}

    # 4. Verify Geotags (one authoritative per detection)
    geotag_recs = [o for o in added_objects if isinstance(o, Geotag)]
    assert len(geotag_recs) == 2
    for g in geotag_recs:
        assert g.is_authoritative is True
        assert g.uncertainty_radius_meters > 0

    # 5. Verify Targets, DetectionTargetMapping, and TargetHistory
    target_recs = [o for o in added_objects if isinstance(o, Target)]
    mapping_recs = [o for o in added_objects if isinstance(o, DetectionTargetMapping)]
    history_recs = [o for o in added_objects if isinstance(o, TargetHistory)]

    assert len(target_recs) == 2
    assert len(mapping_recs) == 2
    assert len(history_recs) == 2

    mapped_det_ids = {m.detection_id for m in mapping_recs}
    assert mapped_det_ids == {d.id for d in created_dets}

    ood_det = next(d for d in created_dets if d.target_class_id == 5)
    assert ood_det.metadata_json["is_ood"] is True
    assert ood_det.metadata_json["class_name"] == "unknown"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
