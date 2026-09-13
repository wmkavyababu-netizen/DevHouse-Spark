from typing import Dict, Tuple
import numpy as np

from app.pipeline.contracts import NormalizedSonarFrame


class SlantRangeCorrector:
    """
    Corrects geometric slant-range distortion to horizontal ground-range across-track.
    For seafloor pixels (Rs >= h): Rg = sqrt(Rs^2 - h^2).
    Preserves nadir water-column geometry without clipping.
    """

    def process(
        self,
        frame: NormalizedSonarFrame,
        nadir_mask: np.ndarray,
        **kwargs,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        img = frame.intensity
        h, w = img.shape
        center_x = w // 2

        alt_m = frame.navigation.altitude_m if frame.navigation.altitude_m is not None else 15.0
        range_max_m = frame.slant_range_max_m if frame.slant_range_max_m > 0 else 75.0

        # Safety clamp altitude to not exceed 85% of slant range
        effective_alt = min(max(alt_m, 1.0), range_max_m * 0.85)

        channel_width = center_x
        # Equidistant ground-range grid for each channel
        max_ground_range_m = np.sqrt(range_max_m**2 - effective_alt**2)

        # Mapping: for each ground-range sample x_g in [0, channel_width - 1],
        # find corresponding slant-range coordinate in [0, channel_width - 1]
        r_g = np.linspace(0, max_ground_range_m, channel_width)
        r_s = np.sqrt(r_g**2 + effective_alt**2)
        # Convert Rs meters back to slant-range sample indices [0, channel_width - 1]
        slant_indices = (r_s / range_max_m) * (channel_width - 1)
        slant_indices = np.clip(slant_indices, 0, channel_width - 1)

        corrected = np.empty_like(img)
        sample_grid = np.arange(channel_width)

        # Perform correction on port (left of center, flipped) and starboard (right of center)
        for row in range(h):
            # Port channel (columns 0 to center_x, where 0 is far port and center_x is nadir)
            port_slant = img[row, :center_x][::-1]  # from nadir to far port
            port_corrected = np.interp(slant_indices, sample_grid, port_slant)
            corrected[row, :center_x] = port_corrected[::-1]

            # Starboard channel (columns center_x to w, where center_x is nadir, w is far starboard)
            stbd_slant = img[row, center_x:]  # from nadir to far starboard
            stbd_corrected = np.interp(slant_indices, sample_grid, stbd_slant)
            corrected[row, center_x:] = stbd_corrected

        metrics = {
            "effective_altitude_m": float(effective_alt),
            "max_slant_range_m": float(range_max_m),
            "max_ground_range_m": float(max_ground_range_m),
            "ground_range_compression_ratio": float(max_ground_range_m / range_max_m),
        }

        return corrected, metrics
