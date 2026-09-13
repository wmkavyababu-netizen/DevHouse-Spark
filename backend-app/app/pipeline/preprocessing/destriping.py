from typing import Dict, Tuple
import numpy as np
from scipy.ndimage import median_filter, uniform_filter1d

from app.pipeline.contracts import NormalizedSonarFrame


class Destriper:
    """
    Destriping filter for side-scan sonar waterfall imagery.
    Removes ping-to-ping horizontal banding artifacts caused by vehicle pitch/yaw oscillations
    or transient transmit power fluctuations using along-track median baseline equalization.
    """

    def process(
        self,
        intensity: np.ndarray,
        nadir_mask: np.ndarray,
        filter_window: int = 31,
        **kwargs,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        h, w = intensity.shape
        destriped = intensity.copy()

        # Compute line-by-line median intensity over valid seafloor pixels (where nadir_mask == 1)
        valid_pixels = (nadir_mask == 1)
        line_medians = np.zeros(h, dtype=np.float32)

        for row in range(h):
            row_valid = intensity[row, valid_pixels[row]]
            if len(row_valid) > 0:
                line_medians[row] = np.median(row_valid)
            else:
                line_medians[row] = np.median(intensity[row])

        # Avoid zero division
        global_median = float(np.median(line_medians))
        if global_median <= 1e-6:
            global_median = 0.5
        line_medians = np.maximum(line_medians, 1e-4)

        # Compute smoothed along-track trend using a moving window
        window_size = min(max(filter_window, 5), h)
        if window_size % 2 == 0:
            window_size += 1
        smoothed_trend = uniform_filter1d(line_medians, size=window_size, mode="nearest")

        # Multiplicative correction factor per ping
        correction_factors = smoothed_trend / line_medians
        # Clamp correction factors to avoid extreme scaling on anomaly lines
        correction_factors = np.clip(correction_factors, 0.6, 1.6)

        # Apply correction along track
        destriped = intensity * correction_factors[:, np.newaxis]
        destriped = np.clip(destriped, 0.0, 1.0)

        # Compute striping reduction metric
        initial_variance = float(np.var(line_medians))
        corrected_medians = line_medians * correction_factors
        final_variance = float(np.var(corrected_medians))
        striping_reduction_pct = float(max(0.0, (1.0 - (final_variance / max(initial_variance, 1e-6))) * 100.0))

        metrics = {
            "initial_ping_variance": initial_variance,
            "final_ping_variance": final_variance,
            "striping_reduction_percent": striping_reduction_pct,
            "window_size": float(window_size),
        }

        return destriped, metrics
