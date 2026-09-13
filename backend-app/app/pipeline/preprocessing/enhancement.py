from typing import Dict, Tuple
import cv2
import numpy as np


class DynamicRangeEnhancer:
    """
    Controlled Dynamic-Range Enhancement.
    Applies quantile boundary normalization and Contrast-Limited Adaptive Histogram Equalization (CLAHE)
    to reveal subtle debris targets in both low-backscatter seabed and high-reflectivity zones
    without saturating the dynamic range.
    """

    def process(
        self,
        intensity: np.ndarray,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8),
        p_low: float = 1.0,
        p_high: float = 99.5,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
        """
        Returns:
          enhanced_f32: float32 in [0.0, 1.0]
          enhanced_uint8: uint8 in [0, 255]
          metrics: dictionary of contrast metrics
        """
        # 1. Percentile-based robust dynamic range normalization
        v_min, v_max = np.percentile(intensity, (p_low, p_high))
        if v_max - v_min < 1e-4:
            v_max = v_min + 1.0

        clipped = np.clip(intensity, v_min, v_max)
        normalized = (clipped - v_min) / (v_max - v_min)

        # 2. Convert to uint8 for CLAHE
        u8_in = (normalized * 255.0).astype(np.uint8)

        # 3. Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        enhanced_uint8 = clahe.apply(u8_in)

        # 4. Normalized float32 representation
        enhanced_f32 = enhanced_uint8.astype(np.float32) / 255.0

        # Contrast improvement metric (standard deviation ratio)
        orig_std = float(np.std(intensity))
        enh_std = float(np.std(enhanced_f32))

        metrics = {
            "percentile_low": float(v_min),
            "percentile_high": float(v_max),
            "original_contrast_std": orig_std,
            "enhanced_contrast_std": enh_std,
            "contrast_expansion_ratio": float(enh_std / max(orig_std, 1e-6)),
            "clahe_clip_limit": float(clip_limit),
        }

        return enhanced_f32, enhanced_uint8, metrics
