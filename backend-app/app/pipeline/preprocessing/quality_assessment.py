from typing import Any, Dict, Tuple
import cv2
import numpy as np


class ImageQualityAssessor:
    """
    Image Quality Assessment (IQA) and Acoustic Shadow Map extraction.
    Computes SNR, ENL, Tenengrad sharpness, Shannon entropy, and an aggregate 0-100 quality score.
    Extracts acoustic shadow zones cast by underwater objects.
    """

    def process(
        self,
        enhanced_f32: np.ndarray,
        nadir_mask: np.ndarray,
        dropout_flags: Dict[str, Any],
        **kwargs,
    ) -> Tuple[np.ndarray, float, Dict[str, float]]:
        """
        Returns:
          shadow_map: uint8 array [0, 255], where 255 = acoustic shadow
          quality_score: float in [0.0, 100.0]
          metrics: detailed metric dictionary
        """
        h, w = enhanced_f32.shape
        seafloor_pixels = enhanced_f32[nadir_mask == 1]

        if len(seafloor_pixels) == 0:
            seafloor_pixels = enhanced_f32.flatten()

        mean_val = float(np.mean(seafloor_pixels))
        std_val = float(np.std(seafloor_pixels))
        var_val = max(std_val**2, 1e-6)

        # 1. Equivalent Number of Looks (ENL)
        enl = float((mean_val**2) / var_val)

        # 2. Signal-to-Noise Ratio (SNR) in dB
        noise_floor = float(np.percentile(seafloor_pixels, 5.0))
        snr_db = float(20.0 * np.log10(max(mean_val, 1e-4) / max(noise_floor, 1e-4)))

        # 3. Tenengrad / Sobel Gradient Sharpness
        u8_img = (enhanced_f32 * 255.0).astype(np.uint8)
        sobel_x = cv2.Sobel(u8_img, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(u8_img, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag_sq = sobel_x**2 + sobel_y**2
        sharpness = float(np.mean(gradient_mag_sq))

        # 4. Shannon Entropy (information density)
        hist, _ = np.histogram(u8_img, bins=256, range=(0, 256), density=True)
        hist_nonzero = hist[hist > 0]
        entropy = float(-np.sum(hist_nonzero * np.log2(hist_nonzero)))

        # 5. Composite Quality Score (0 - 100)
        # Normalized metrics:
        norm_sharpness = min(sharpness / 1200.0, 1.0) * 30.0   # Up to 30 pts
        norm_entropy = min(entropy / 8.0, 1.0) * 25.0          # Up to 25 pts
        norm_enl = min(enl / 10.0, 1.0) * 25.0                 # Up to 25 pts
        contrast_score = min(std_val / 0.25, 1.0) * 20.0       # Up to 20 pts

        raw_score = norm_sharpness + norm_entropy + norm_enl + contrast_score

        # Apply penalty for data dropouts
        dropout_penalty = min(float(dropout_flags.get("dropout_line_count", 0)) * 2.0, 25.0)
        quality_score = float(np.clip(raw_score - dropout_penalty, 5.0, 100.0))

        # 6. Extract Acoustic Shadow Map
        # Shadows are characterized by extremely low backscatter on the valid seafloor
        shadow_threshold = max(mean_val - 1.1 * std_val, 0.08)
        shadow_mask = np.zeros((h, w), dtype=np.uint8)

        # Seafloor pixels strictly below shadow threshold
        is_shadow = (enhanced_f32 < shadow_threshold) & (nadir_mask == 1)
        shadow_mask[is_shadow] = 255

        # Morphological clean up to remove single-pixel speckle noise in shadows
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        shadow_cleaned = cv2.morphologyEx(shadow_mask, cv2.MORPH_OPEN, kernel)
        shadow_cleaned = cv2.morphologyEx(shadow_cleaned, cv2.MORPH_CLOSE, kernel)

        metrics = {
            "snr_db": snr_db,
            "enl": enl,
            "sharpness_tenengrad": sharpness,
            "shannon_entropy": entropy,
            "quality_score": quality_score,
            "shadow_area_ratio": float(np.mean(shadow_cleaned == 255)),
            "shadow_threshold": float(shadow_threshold),
        }

        return shadow_cleaned, quality_score, metrics
