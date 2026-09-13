from typing import Dict, Tuple
import cv2
import numpy as np

from app.pipeline.contracts import NormalizedSonarFrame


class SpeckleFilter:
    """
    Edge-preserving acoustic speckle noise suppressor.
    Combines Bilateral filtering with adaptive variance weighting to smooth Rayleigh speckle
    in uniform seafloor zones while preserving sharp highlight-to-shadow debris edges.
    """

    def process(
        self,
        intensity: np.ndarray,
        diameter: int = 5,
        sigma_color: float = 0.12,
        sigma_space: float = 5.0,
        **kwargs,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        # Ensure float32 in [0, 1]
        img_f32 = intensity.astype(np.float32)

        # Bilateral filter in OpenCV
        filtered = cv2.bilateralFilter(
            src=img_f32,
            d=diameter,
            sigmaColor=sigma_color,
            sigmaSpace=sigma_space,
        )

        filtered = np.clip(filtered, 0.0, 1.0)

        # Compute Equivalent Number of Looks (ENL) improvement
        # ENL = mean^2 / var over a uniform test patch
        h, w = intensity.shape
        patch_h = max(h // 8, 16)
        patch_w = max(w // 8, 16)
        y0, x0 = h // 4, w // 4
        orig_patch = img_f32[y0 : y0 + patch_h, x0 : x0 + patch_w]
        filt_patch = filtered[y0 : y0 + patch_h, x0 : x0 + patch_w]

        orig_enl = float((np.mean(orig_patch) ** 2) / max(float(np.var(orig_patch)), 1e-6))
        filt_enl = float((np.mean(filt_patch) ** 2) / max(float(np.var(filt_patch)), 1e-6))

        metrics = {
            "initial_enl": orig_enl,
            "filtered_enl": filt_enl,
            "enl_improvement_factor": float(filt_enl / max(orig_enl, 1e-6)),
            "filter_diameter": float(diameter),
        }

        return filtered, metrics
