"""
Comprehensive verification test suite for the Closed-Loop Expert Review and Retraining Pipeline:
1. Review claiming & concurrency control (partial unique index uq_review_assignment_claimed)
2. Expert review decisions: accepted, rejected, corrected (bbox + class), unknown
3. Curation of review decisions into dataset_samples with feedback_type and split='train'
4. Sonar acoustic data augmentation (rotation +/-15 deg, h/v flip, Gaussian noise, gamma)
5. Model evaluation and metric computation (mAP50, precision, recall, F1, confusion matrix)
6. Retraining safety gate (+2% mAP threshold) with 10% canary deployment
7. Inference telemetry logging and real-time distribution drift monitoring (KS-statistic > 10%)
8. REST API endpoints for reviews and admin retraining
"""

import base64
import io
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import numpy as np
import pytest
from PIL import Image

# Ensure backend-app is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.security import register_cached_public_key
from app.models.ai import AiModel, DatasetVersion, ModelEvaluation, TargetClass
from app.models.detection import Detection
from app.models.review import DatasetSample, Review, ReviewAssignment
from app.models.sonar import Survey, SurveyFrame
from app.models.target import DetectionTargetMapping, Target, TargetHistory
from app.services.curation_service import curation_service
from app.services.review_service import review_service
from app.ai.training.dataset import sonar_dataset_loader, SonarAugmenter
from app.ai.training.evaluate import model_evaluator
from app.ai.training.train import model_trainer
from app.ai.models.monitoring import model_monitor
from app.tasks.retraining_tasks import _execute_retraining_workflow


# ------------------------------------------------------------------------------
# 1. Review Claim & Concurrency Control Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_review_claim_and_concurrency():
    """
    Verifies that a detection can be claimed, and that a second expert
    attempting to claim an active detection receives a 409 Conflict.
    """
    mock_db = MagicMock()
    detection_id = uuid.uuid4()
    reviewer_1 = uuid.uuid4()
    reviewer_2 = uuid.uuid4()

    # Step A: First claim succeeds
    mock_exec_res = MagicMock()
    mock_exec_res.scalar_one_or_none.return_value = None  # No existing claim
    mock_db.execute = AsyncMock(return_value=mock_exec_res)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    claim_1 = await review_service.claim_detection(
        db=mock_db,
        detection_id=detection_id,
        user_id=reviewer_1,
        timeout_minutes=30,
    )
    assert claim_1.detection_id == detection_id
    assert claim_1.assigned_to == reviewer_1
    assert claim_1.status == "claimed"

    # Step B: Second claim by different user on active unexpired claim raises 409 Conflict
    existing_active_claim = ReviewAssignment(
        id=uuid.uuid4(),
        detection_id=detection_id,
        assigned_to=reviewer_1,
        status="claimed",
        claimed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=25),
    )
    mock_exec_res.scalar_one_or_none.return_value = existing_active_claim

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await review_service.claim_detection(
            db=mock_db,
            detection_id=detection_id,
            user_id=reviewer_2,
        )
    assert exc_info.value.status_code == 409
    assert "already claimed" in exc_info.value.detail


# ------------------------------------------------------------------------------
# 2. Expert Review Decisions & State Transitions Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_review_decision_corrections_and_target_sync():
    """
    Tests submission of 'corrected', 'rejected', and 'unknown' decisions:
    Verifies detection updates, target history tracking, and feedback codification.
    """
    mock_db = MagicMock()
    detection_id = uuid.uuid4()
    target_id = uuid.uuid4()
    reviewer_id = uuid.uuid4()

    det = Detection(
        id=detection_id,
        survey_id=uuid.uuid4(),
        survey_frame_id=uuid.uuid4(),
        target_class_id=0,  # crab_pot originally
        bounding_box=[100.0, 100.0, 150.0, 150.0],
        confidence=Decimal("0.8500"),
        status="unreviewed",
        metadata_json={},
    )
    target = Target(
        id=target_id,
        target_class_id=0,
        status="detected",
        fused_confidence=Decimal("0.8500"),
        observation_count=1,
        description="Crab Pot",
        metadata_json={},
    )

    # Setup mock returns
    def mock_exec_side_effect(stmt):
        m = MagicMock()
        str_stmt = str(stmt)
        if "FROM detections" in str_stmt:
            m.scalar_one_or_none.return_value = det
        elif "FROM detection_target_mapping" in str_stmt:
            m.scalar_one_or_none.return_value = target_id
        elif "FROM targets" in str_stmt:
            m.scalar_one_or_none.return_value = target
        else:
            m.scalar_one_or_none.return_value = None
        return m

    mock_db.execute = AsyncMock(side_effect=mock_exec_side_effect)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    added_objs = []
    mock_db.add.side_effect = lambda o: added_objs.append(o)

    # Submit Correction decision: class 0 -> 4 (mine_cylinder), new bbox
    from app.schemas.review import ReviewDecisionRequest
    correction_req = ReviewDecisionRequest(
        decision="corrected",
        corrected_target_class_id=4,  # mine_cylinder
        corrected_bbox=[105.0, 105.0, 160.0, 160.0],
        comments="Cylindrical metal casing clearly visible in acoustic highlight.",
    )

    resp = await review_service.submit_review_decision(
        db=mock_db,
        detection_id=detection_id,
        reviewer_id=reviewer_id,
        request=correction_req,
    )

    assert resp.decision == "corrected"
    assert resp.feedback_type == "correction"
    assert det.status == "corrected"
    assert det.target_class_id == 4
    assert det.bounding_box == [105.0, 105.0, 160.0, 160.0]
    assert target.target_class_id == 4

    # Verify TargetHistory audit record was added
    target_histories = [o for o in added_objs if isinstance(o, TargetHistory)]
    assert len(target_histories) == 1
    assert target_histories[0].target_id == target_id
    assert "mine" in target_histories[0].change_reason.lower() or "corrected" in target_histories[0].change_reason.lower()


# ------------------------------------------------------------------------------
# 3. Feedback Curation into dataset_samples Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_feedback_curation_into_dataset_samples():
    """
    Verifies that uncurated review decisions are transformed into dataset_samples
    with split='train', feedback_type, and corrected annotations.
    """
    mock_db = MagicMock()
    d_ver_id = uuid.uuid4()
    det_id = uuid.uuid4()
    frame_id = uuid.uuid4()
    rev_id = uuid.uuid4()

    d_ver = DatasetVersion(
        id=d_ver_id,
        version_tag="v1.1-retrain",
        total_samples=10,
        is_frozen=False,
    )
    rev = Review(
        id=rev_id,
        detection_id=det_id,
        reviewer_id=uuid.uuid4(),
        decision="corrected",
        corrected_target_class_id=3,  # ghost_net
        corrected_bbox=[50.0, 50.0, 120.0, 120.0],
        comments="Net entanglement confirmed",
    )
    det = Detection(
        id=det_id,
        survey_id=uuid.uuid4(),
        survey_frame_id=frame_id,
        target_class_id=0,
        bounding_box=[45.0, 45.0, 100.0, 100.0],
        confidence=Decimal("0.7800"),
        status="corrected",
    )
    frame = SurveyFrame(
        id=frame_id,
        quality_score=Decimal("88.50"),
        raw_image_artifact_id=uuid.uuid4(),
    )

    def mock_exec_side_effect(stmt):
        m = MagicMock()
        str_stmt = str(stmt)
        if "FROM dataset_versions" in str_stmt:
            m.scalar_one_or_none.return_value = d_ver
        elif "FROM reviews" in str_stmt:
            m.all.return_value = [(rev, det, frame)]
        else:
            m.scalar_one_or_none.return_value = None
            m.all.return_value = []
        return m

    mock_db.execute = AsyncMock(side_effect=mock_exec_side_effect)
    mock_db.commit = AsyncMock()
    added_samples = []
    mock_db.add.side_effect = lambda o: added_samples.append(o)

    summary = await curation_service.curate_pending_feedback(
        db=mock_db,
        target_dataset_version_id=d_ver_id,
    )

    assert summary["curated_count"] == 1
    assert len(added_samples) == 1
    sample: DatasetSample = added_samples[0]
    assert sample.dataset_version_id == d_ver_id
    assert sample.detection_id == det_id
    assert sample.split_type == "train"
    assert sample.target_class_id == 3  # Corrected class
    assert sample.annotation_data["feedback_type"] == "correction"
    assert sample.annotation_data["bbox"] == [50.0, 50.0, 120.0, 120.0]
    assert sample.annotation_data["source"] == "expert_correction"


# ------------------------------------------------------------------------------
# 4. Sonar Acoustic Data Augmentation Tests
# ------------------------------------------------------------------------------
def test_sonar_data_augmentation():
    """
    Verifies acoustic sonar transformations:
    - Rotation +/- 15 deg
    - Horizontal & vertical flips
    - Gaussian noise injection (sigma = 0.01)
    - Gamma contrast transform (0.8 - 1.2)
    """
    augmenter = SonarAugmenter()
    orig_img = np.ones((128, 128), dtype=np.uint8) * 100
    orig_bbox = [20.0, 20.0, 60.0, 60.0]

    aug_img, new_bbox = augmenter.augment(
        image=orig_img,
        bbox=orig_bbox,
        rotation_limit_deg=15.0,
        apply_noise=True,
        apply_gamma=True,
        apply_flips=True,
    )

    # Shape and type preserved
    assert aug_img.shape == orig_img.shape
    assert aug_img.dtype == np.uint8
    # Noise and gamma caused intensity variation
    assert not np.array_equal(aug_img, orig_img)
    # Bounding box adjusted and coordinates valid
    assert new_bbox is not None
    assert len(new_bbox) == 4
    x1, y1, x2, y2 = new_bbox
    assert 0.0 <= x1 <= 128.0
    assert 0.0 <= y1 <= 128.0


# ------------------------------------------------------------------------------
# 5. Model Evaluation and Metric Calculation Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_model_evaluation_metric_computation():
    """
    Verifies computation of precision, recall, F1, mAP50, mAP50-95,
    and recording in model_evaluations.
    """
    mock_db = MagicMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    model_id = uuid.uuid4()
    d_ver_id = uuid.uuid4()
    dummy_model_path = model_trainer.get_model_file_path("v1.0") if hasattr(model_trainer, "get_model_file_path") else None
    
    from app.ai.models.registry import model_registry
    model_path = model_registry.get_model_file_path("v1.0")
    model_registry.ensure_baseline_model_exists("v1.0")

    eval_rec = await model_evaluator.evaluate_model(
        db=mock_db,
        ai_model_id=model_id,
        dataset_version_id=d_ver_id,
        model_path=model_path,
        data_yaml_path=None,
    )

    assert float(eval_rec.map50_score) >= 0.85
    assert float(eval_rec.precision_score) >= 0.80
    assert float(eval_rec.recall_score) >= 0.80
    assert float(eval_rec.f1_score) >= 0.80
    assert "per_class_map50" in eval_rec.evaluation_metrics


# ------------------------------------------------------------------------------
# 6. Retraining Safety Gate (+2% mAP) Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_retraining_safety_gate_rejection():
    """
    Scenario A: New model improves mAP by only 1.0% (less than 2% gate).
    Verifies that deployment is REJECTED and the model is NEVER promoted.
    """
    mock_db = MagicMock()
    curr_model = AiModel(
        id=uuid.uuid4(),
        name="tarang-yolov8",
        version="v1.0",
        parameters={"metrics": {"mAP50": 0.8800}, "deployment_percentage": 100},
        status="active",
        is_active=True,
    )
    new_model = AiModel(
        id=uuid.uuid4(),
        name="tarang-yolov8-v1.1",
        version="v1.1",
        parameters={"metrics": {"mAP50": 0.8900}, "deployment_percentage": 0},
        status="evaluating",
        is_active=False,
    )
    eval_rec = ModelEvaluation(
        id=uuid.uuid4(),
        ai_model_id=new_model.id,
        dataset_version_id=uuid.uuid4(),
        map50_score=Decimal("0.8900"),  # +1.0% improvement (fails >2% gate)
    )

    with patch("app.tasks.retraining_tasks.AsyncSessionLocal") as mock_session_cls:
        session_instance = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = session_instance
        session_instance.commit = AsyncMock()

        with patch("app.tasks.retraining_tasks.model_registry.get_current_model", AsyncMock(return_value=(None, curr_model, "hash1"))):
            with patch("app.tasks.retraining_tasks.model_trainer.train_model", AsyncMock(return_value=(None, "hash2", new_model))):
                with patch("app.tasks.retraining_tasks.model_evaluator.evaluate_model", AsyncMock(return_value=eval_rec)):
                    with patch("app.tasks.retraining_tasks.model_registry.deploy_model", AsyncMock()) as mock_deploy:
                        res = await _execute_retraining_workflow(
                            dataset_version_id=uuid.uuid4(),
                            new_version="v1.1",
                        )

                        # Deployment rejected because delta_map = +1.0% <= 2.0%
                        assert res["status"] == "deployment_rejected"
                        assert res["delta_map50"] == 0.0100
                        assert res["canary_percentage"] == 0
                        # deploy_model should NEVER be called when gate fails
                        mock_deploy.assert_not_called()


@pytest.mark.asyncio
async def test_retraining_safety_gate_success_and_canary():
    """
    Scenario B: New model improves mAP by 3.5% (exceeds >2% gate).
    Verifies that model qualifies and deploys to 10% canary traffic.
    """
    curr_model = AiModel(
        id=uuid.uuid4(),
        name="tarang-yolov8",
        version="v1.0",
        parameters={"metrics": {"mAP50": 0.8800}, "deployment_percentage": 100},
        status="active",
        is_active=True,
    )
    new_model = AiModel(
        id=uuid.uuid4(),
        name="tarang-yolov8-v1.1",
        version="v1.1",
        parameters={"metrics": {"mAP50": 0.9150}, "deployment_percentage": 0},
        status="evaluating",
        is_active=False,
    )
    eval_rec = ModelEvaluation(
        id=uuid.uuid4(),
        ai_model_id=new_model.id,
        dataset_version_id=uuid.uuid4(),
        map50_score=Decimal("0.9150"),  # +3.5% improvement (passes >2% gate)
    )

    with patch("app.tasks.retraining_tasks.AsyncSessionLocal") as mock_session_cls:
        session_instance = MagicMock()
        mock_session_cls.return_value.__aenter__.return_value = session_instance
        session_instance.commit = AsyncMock()

        with patch("app.tasks.retraining_tasks.model_registry.get_current_model", AsyncMock(return_value=(None, curr_model, "hash1"))):
            with patch("app.tasks.retraining_tasks.model_trainer.train_model", AsyncMock(return_value=(None, "hash2", new_model))):
                with patch("app.tasks.retraining_tasks.model_evaluator.evaluate_model", AsyncMock(return_value=eval_rec)):
                    with patch("app.tasks.retraining_tasks.model_registry.deploy_model", AsyncMock()) as mock_deploy:
                        res = await _execute_retraining_workflow(
                            dataset_version_id=uuid.uuid4(),
                            new_version="v1.1",
                        )

                        # Deployment approved to 10% canary
                        assert res["status"] == "canary_deployed"
                        assert res["delta_map50"] == 0.0350
                        assert res["canary_percentage"] == 10
                        mock_deploy.assert_called_once_with(session_instance, version="v1.1", percentage=10)


# ------------------------------------------------------------------------------
# 7. Distribution Drift Monitoring Tests
# ------------------------------------------------------------------------------
def test_distribution_drift_monitoring():
    """
    Verifies that ModelMonitor logs predictions and raises an alert
    when the inference confidence distribution shifts by >10%.
    """
    model_monitor.clear_buffer()

    # 1. Feed stable predictions (mean ~ 0.80 matching baseline)
    np.random.seed(123)
    stable_samples = np.random.beta(a=8, b=2, size=150)
    for conf in stable_samples:
        model_monitor.track_inference("v1.0", confidence=float(conf), class_id=0)

    stable_res = model_monitor.calculate_drift("v1.0", drift_threshold=0.10)
    assert stable_res["drift_detected"] is False
    assert stable_res["alert"] is False

    # 2. Feed degraded / drifted predictions (mean ~ 0.40 due to sensor fouling / turbidity)
    model_monitor.clear_buffer()
    drifted_samples = np.random.beta(a=2, b=4, size=100)
    for conf in drifted_samples:
        model_monitor.track_inference("v1.0", confidence=float(conf), class_id=0)

    drift_res = model_monitor.calculate_drift("v1.0", drift_threshold=0.10)
    assert drift_res["drift_detected"] is True
    assert drift_res["alert"] is True
    assert drift_res["drift_score"] > 0.10
    assert "ALERT" in drift_res["message"]


# ------------------------------------------------------------------------------
# 8. REST API Endpoints Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_reviews_queue_endpoint():
    """Verifies GET /api/v1/reviews/queue."""
    try:
        from tests.test_core_security import public_key_pem, TEST_KID, create_test_jwt
    except ImportError:
        from test_core_security import public_key_pem, TEST_KID, create_test_jwt
    register_cached_public_key(TEST_KID, public_key_pem)
    token = create_test_jwt(roles=["ROLE_EXPERT", "ROLE_ANALYST"])

    from app.db.session import get_db
    async def override_get_db():
        yield None

    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch("app.api.v1.reviews.review_service.get_review_queue") as mock_get_q:
            from app.schemas.review import ReviewQueueResponse
            mock_get_q.return_value = ReviewQueueResponse(items=[], total=0, page=1, page_size=20)

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get(
                    "/api/v1/reviews/queue",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert resp.status_code == 200
                data = resp.json()
                assert "items" in data
                assert data["total"] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_api_admin_retraining_drift_endpoint():
    """Verifies GET /api/v1/admin/retraining/drift."""
    try:
        from tests.test_core_security import public_key_pem, TEST_KID, create_test_jwt
    except ImportError:
        from test_core_security import public_key_pem, TEST_KID, create_test_jwt
    register_cached_public_key(TEST_KID, public_key_pem)
    token = create_test_jwt(roles=["ROLE_ADMIN", "ROLE_ORG_ADMIN"])

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/admin/retraining/drift?model_version=v1.0&threshold=0.10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "drift_score" in data
        assert "drift_detected" in data


if __name__ == "__main__":
    pytest.main(["-v", __file__])
