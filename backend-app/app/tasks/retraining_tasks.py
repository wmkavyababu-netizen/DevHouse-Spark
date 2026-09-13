import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from app.ai.models.registry import model_registry
from app.ai.training.evaluate import model_evaluator
from app.ai.training.train import model_trainer
from app.db.session import AsyncSessionLocal
from app.models.ai import AiModel, DatasetVersion, ModelEvaluation
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _execute_retraining_workflow(
    dataset_version_id: UUID,
    new_version: Optional[str] = None,
    epochs: int = 5,
) -> Dict[str, Any]:
    """
    Asynchronous implementation of closed-loop retraining with strict +2% mAP canary gate.
    """
    async with AsyncSessionLocal() as db:
        # 1. Fetch current production model to establish baseline mAP50
        yolo_curr, curr_model_rec, curr_checksum = await model_registry.get_current_model(db)
        curr_version = curr_model_rec.version if curr_model_rec else "v1.0"
        curr_metrics = (curr_model_rec.parameters.get("metrics") if curr_model_rec else {}) or {}
        curr_map50 = float(curr_metrics.get("mAP50", 0.8800))

        # 2. Determine next model version
        if not new_version:
            try:
                parts = curr_version.replace("v", "").split(".")
                major = int(parts[0])
                minor = int(parts[1]) if len(parts) > 1 else 0
                new_version = f"v{major}.{minor + 1}"
            except Exception:
                new_version = f"v1.{int(datetime.now(timezone.utc).timestamp()) % 1000}"

        logger.info(
            f"Initiating closed-loop retraining: Baseline {curr_version} (mAP50: {curr_map50:.4f}) -> Target {new_version}"
        )

        # 3. Train new candidate model
        target_path, checksum, new_model_rec = await model_trainer.train_model(
            db=db,
            dataset_version_id=dataset_version_id,
            new_version=new_version,
            epochs=epochs,
        )

        # 4. Evaluate new candidate model on held-out test split
        eval_rec = await model_evaluator.evaluate_model(
            db=db,
            ai_model_id=new_model_rec.id,
            dataset_version_id=dataset_version_id,
            model_path=target_path,
        )
        new_map50 = float(eval_rec.map50_score)
        delta_map50 = new_map50 - curr_map50

        # 5. Strict Gate: Must improve mAP50 by > 2.0% (+0.02)
        # NEVER auto-promote to 100% without the improvement threshold being met!
        IMPROVEMENT_THRESHOLD = 0.02
        is_promoted_to_canary = False

        if delta_map50 > IMPROVEMENT_THRESHOLD:
            # Qualified for 10% canary deployment
            await model_registry.deploy_model(db, version=new_version, percentage=10)
            is_promoted_to_canary = True
            result_status = "canary_deployed"
            message = (
                f"Model {new_version} satisfied threshold (+{delta_map50 * 100:.2f}% mAP50, "
                f"new: {new_map50:.4f} vs base: {curr_map50:.4f}). Deployed 10% canary traffic."
            )
            logger.info(f"SUCCESS: {message}")
        else:
            # Gate failed: reject deployment; retain current production model
            new_model_rec.status = "rejected_evaluation"
            new_model_rec.is_active = False
            await db.commit()
            result_status = "deployment_rejected"
            message = (
                f"Model {new_version} failed improvement threshold (delta: {delta_map50 * 100:.2f}%, "
                f"required: >{IMPROVEMENT_THRESHOLD * 100:.1f}%). Deployment rejected; {curr_version} remains at 100%."
            )
            logger.warning(f"REJECTED: {message}")

        return {
            "status": result_status,
            "new_version": new_version,
            "baseline_version": curr_version,
            "baseline_map50": curr_map50,
            "new_map50": new_map50,
            "delta_map50": round(delta_map50, 4),
            "improvement_threshold": IMPROVEMENT_THRESHOLD,
            "canary_percentage": 10 if is_promoted_to_canary else 0,
            "message": message,
            "model_checksum": checksum,
            "evaluation_id": str(eval_rec.id),
        }


@celery_app.task(name="app.tasks.retraining_tasks.retrain_model_task", bind=True)
def retrain_model_task(self, dataset_version_id_str: str, new_version: Optional[str] = None):
    """
    Celery background worker task for model retraining.
    """
    dataset_version_id = UUID(dataset_version_id_str)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _execute_retraining_workflow(dataset_version_id, new_version)
        )
    finally:
        loop.close()
