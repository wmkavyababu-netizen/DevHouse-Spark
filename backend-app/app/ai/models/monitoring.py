import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ModelMonitor:
    """
    Real-time inference telemetry and statistical distribution drift monitoring engine.
    Logs per-prediction metrics and alerts when inference confidence distributions
    shift by >10% relative to training baseline distributions.
    """

    def __init__(self, max_buffer_size: int = 5000):
        self._max_buffer = max_buffer_size
        self._telemetry_log: deque = deque(maxlen=max_buffer_size)
        # Default baseline training distribution (calibrated acoustic sonar debris expectations)
        np.random.seed(42)
        self._default_baseline = list(np.random.beta(a=8, b=2, size=500))  # mean ~ 0.80

    def track_inference(
        self,
        model_version: str,
        confidence: float,
        class_id: int,
        bbox: Optional[List[float]] = None,
        inference_time_ms: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Logs individual prediction telemetry in rolling in-memory buffer.
        """
        record = {
            "timestamp": datetime.now(timezone.utc),
            "model_version": model_version,
            "confidence": float(np.clip(confidence, 0.0, 1.0)),
            "class_id": class_id,
            "bbox": bbox,
            "inference_time_ms": inference_time_ms,
        }
        self._telemetry_log.append(record)
        return record

    def get_recent_confidences(self, model_version: Optional[str] = None, limit: int = 200) -> List[float]:
        """Extracts recent prediction confidences for a specific model version."""
        if model_version:
            filtered = [r["confidence"] for r in self._telemetry_log if r["model_version"] == model_version]
        else:
            filtered = [r["confidence"] for r in self._telemetry_log]
        return filtered[-limit:]

    @staticmethod
    def _ks_statistic(sample1: List[float], sample2: List[float]) -> float:
        """
        Computes the Kolmogorov-Smirnov 2-sample statistic D in [0.0, 1.0]:
        D = max |F_1(x) - F_2(x)|
        Measures the maximum vertical distance between two empirical cumulative distributions.
        """
        if not sample1 or not sample2:
            return 0.0

        data1 = np.sort(np.array(sample1, dtype=np.float32))
        data2 = np.sort(np.array(sample2, dtype=np.float32))
        n1 = len(data1)
        n2 = len(data2)

        data_all = np.concatenate([data1, data2])
        cdf1 = np.searchsorted(data1, data_all, side="right") / n1
        cdf2 = np.searchsorted(data2, data_all, side="right") / n2

        d_stat = float(np.max(np.abs(cdf1 - cdf2)))
        return round(d_stat, 4)

    def calculate_drift(
        self,
        model_version: str,
        reference_distribution: Optional[List[float]] = None,
        sample_size: int = 100,
        drift_threshold: float = 0.10,
    ) -> Dict[str, Any]:
        """
        Evaluates distribution drift by comparing recent predictions against baseline.
        Alerts if the KS distance D exceeds 10% (0.10).
        """
        recent = self.get_recent_confidences(model_version=model_version, limit=sample_size)
        ref = reference_distribution if reference_distribution is not None else self._default_baseline

        if len(recent) < 10:
            return {
                "model_version": model_version,
                "status": "insufficient_data",
                "sample_count": len(recent),
                "drift_score": 0.0,
                "drift_detected": False,
                "threshold": drift_threshold,
                "alert": False,
                "message": f"Insufficient prediction samples ({len(recent)} < 10) for drift calculation.",
            }

        d_stat = self._ks_statistic(recent, ref)
        drift_detected = d_stat > drift_threshold

        recent_mean = float(np.mean(recent))
        ref_mean = float(np.mean(ref))
        mean_shift = round(recent_mean - ref_mean, 4)

        if drift_detected:
            severity = "critical" if d_stat > 0.25 else "warning"
            message = (
                f"ALERT: Distribution drift of {d_stat * 100:.1f}% detected on model '{model_version}' "
                f"(exceeds {drift_threshold * 100:.1f}% threshold). Mean confidence shifted by {mean_shift:+.3f}."
            )
            logger.warning(message)
        else:
            severity = "normal"
            message = f"Model '{model_version}' confidence distribution is stable (drift: {d_stat * 100:.1f}%)."

        return {
            "model_version": model_version,
            "status": "active",
            "sample_count": len(recent),
            "drift_score": d_stat,
            "drift_detected": drift_detected,
            "threshold": drift_threshold,
            "alert": drift_detected,
            "severity": severity,
            "recent_mean_confidence": round(recent_mean, 4),
            "baseline_mean_confidence": round(ref_mean, 4),
            "mean_shift": mean_shift,
            "message": message,
        }

    def clear_buffer(self) -> None:
        """Resets telemetry log buffer (useful for test isolation)."""
        self._telemetry_log.clear()


model_monitor = ModelMonitor()
