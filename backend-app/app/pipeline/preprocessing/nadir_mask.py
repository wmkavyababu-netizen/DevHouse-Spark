from typing import Dict, Tuple
import numpy as np

from app.pipeline.contracts import NormalizedSonarFrame


class NadirZoneMasker:
    """
    Computes the Nadir-Zone Mask for side-scan sonar waterfall imagery.
    CRITICAL RULE: The nadir zone is masked, NEVER cropped or stitched.
    The water column and first bottom return must be preserved for acoustic shadow
    geometry and towfish altitude verification.
    """

    def process(
        self,
        frame: NormalizedSonarFrame,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
        """
        Generates a binary nadir mask where:
          0 = Nadir water column blind zone
          1 = Valid seafloor acoustic backscatter
        Returns: (masked_intensity, binary_mask, metrics)
        """
        img = frame.intensity
        h, w = img.shape
        center_x = w // 2

        # Extract towfish altitude h_alt and maximum slant range R_max
        alt_m = frame.navigation.altitude_m if frame.navigation.altitude_m is not None else 15.0
        range_max_m = frame.slant_range_max_m if frame.slant_range_max_m > 0 else 75.0

        # Physical geometry: water column half-width in samples
        # Each channel spans w / 2 samples over range_max_m
        channel_samples = w / 2.0
        nadir_fraction = min(max(alt_m / range_max_m, 0.02), 0.9)
        nadir_radius_samples = int(channel_samples * nadir_fraction)

        # Build binary mask (1 for valid seafloor, 0 for water column)
        mask = np.ones((h, w), dtype=np.uint8)
        left_bound = max(0, center_x - nadir_radius_samples)
        right_bound = min(w, center_x + nadir_radius_samples)

        mask[:, left_bound:right_bound] = 0

        # Preserve the original image pixels; do not crop or destroy nadir
        preserved_intensity = img.copy()

        metrics = {
            "nadir_half_width_samples": float(nadir_radius_samples),
            "nadir_fraction": float(nadir_fraction),
            "water_column_altitude_m": float(alt_m),
            "seafloor_pixel_ratio": float(np.mean(mask)),
        }

        return preserved_intensity, mask, metrics
