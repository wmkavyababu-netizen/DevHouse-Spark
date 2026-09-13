from typing import Any, Dict, Tuple
import numpy as np


class ConfidenceFuser:
    """
    Multi-modal evidence confidence fusion engine.
    Fuses raw AI object detection confidence, acoustic physics shadow score,
    and frame image quality score per the TARANG v6.2 specification.
    """

    def __init__(
        self,
        weight_ai: float = 0.55,
        weight_physics: float = 0.30,
        weight_quality: float = 0.15,
    ):
        self.w_ai = weight_ai
        self.w_phys = weight_physics
        self.w_qual = weight_quality

    def fuse(
        self,
        ai_confidence: float,
        physics_score: float,
        frame_quality_score: float,
        is_physically_plausible: bool = True,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates the fused confidence score C_final in [0.0, 1.0].
        """
        c_ai = float(np.clip(ai_confidence, 0.0, 1.0))
        s_phys = float(np.clip(physics_score, 0.0, 1.0))
        q_norm = float(np.clip(frame_quality_score / 100.0, 0.0, 1.0))

        # Weighted linear combination
        raw_fused = (self.w_ai * c_ai) + (self.w_phys * s_phys) + (self.w_qual * q_norm)

        # Apply damping penalty if physics validation failed (e.g. shadow direction wrong or inside water column)
        if not is_physically_plausible or s_phys < 0.35:
            damped_fused = raw_fused * 0.72
            applied_penalty = True
        else:
            damped_fused = raw_fused
            applied_penalty = False

        # Bound strictly for DECIMAL(5,4) compatibility (max 0.9999)
        final_confidence = float(np.clip(damped_fused, 0.05, 0.9990))

        details = {
            "ai_confidence": round(c_ai, 4),
            "physics_score": round(s_phys, 4),
            "quality_normalized": round(q_norm, 4),
            "raw_fused": round(raw_fused, 4),
            "applied_penalty": applied_penalty,
            "final_confidence": round(final_confidence, 4),
            "weights": {
                "ai": self.w_ai,
                "physics": self.w_phys,
                "quality": self.w_qual,
            },
        }

        return round(final_confidence, 4), details


confidence_fuser = ConfidenceFuser()
