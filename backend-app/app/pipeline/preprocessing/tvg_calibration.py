from typing import Any, Dict, Optional, Tuple
import numpy as np

from app.pipeline.contracts import NormalizedSonarFrame


class TvgCalibrator:
    """
    Sonar-Specific Time-Varied Gain (TVG) and Acoustic Calibration.
    CRITICAL RULE: Unit conversion: A dB loss term must NEVER be treated as a
    linear multiplicative gain. The transmission loss (spreading + absorption) in dB
    must be converted to a linear amplitude scale: Gain_linear = 10^(Gain_dB / 20).
    """

    DEFAULT_ABSORPTION_DB_PER_KM = {
        100.0: 35.0,
        455.0: 125.0,
        900.0: 320.0,
    }

    def _get_absorption_coefficient(self, freq_khz: Optional[float]) -> float:
        """Determines acoustic absorption alpha in dB/km."""
        if freq_khz is None or freq_khz <= 0:
            return 125.0  # Default for 455 kHz SSS

        # Find closest standard frequency or interpolate
        known_freqs = sorted(self.DEFAULT_ABSORPTION_DB_PER_KM.keys())
        if freq_khz <= known_freqs[0]:
            return self.DEFAULT_ABSORPTION_DB_PER_KM[known_freqs[0]]
        if freq_khz >= known_freqs[-1]:
            return self.DEFAULT_ABSORPTION_DB_PER_KM[known_freqs[-1]]

        return float(np.interp(freq_khz, known_freqs, [self.DEFAULT_ABSORPTION_DB_PER_KM[f] for f in known_freqs]))

    def process(
        self,
        frame: NormalizedSonarFrame,
        calibration_profile: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        img = frame.intensity
        h, w = img.shape
        center_x = w // 2
        channel_samples = center_x

        profile = calibration_profile or {}
        max_range_m = frame.slant_range_max_m if frame.slant_range_max_m > 0 else 75.0
        freq_khz = frame.frequency_khz

        # 1. Acoustic parameters
        alpha_db_km = float(profile.get("alpha_db_per_km") or self._get_absorption_coefficient(freq_khz))
        spreading_coeff = float(profile.get("spreading_coefficient", 20.0))  # 20 log10(R)
        max_gain_db = float(profile.get("max_gain_db", 32.0))  # Max clamp to prevent noise explosion
        min_range_m = float(profile.get("min_range_m", 1.5))

        # 2. Range grid for half-channel [0, max_range_m]
        ranges = np.linspace(min_range_m, max_range_m, channel_samples)

        # 3. Transmission loss in dB: TL = spreading * log10(R) + 2 * alpha * (R / 1000)
        spreading_loss_db = spreading_coeff * np.log10(ranges / min_range_m)
        absorption_loss_db = 2.0 * alpha_db_km * (ranges / 1000.0)
        total_loss_db = spreading_loss_db + absorption_loss_db

        # Gain in dB bounded by max_gain_db
        gain_db = np.clip(total_loss_db, 0.0, max_gain_db)

        # 4. CRITICAL: Convert dB to LINEAR amplitude gain factor
        # Linear amplitude gain: G_linear = 10 ^ (G_dB / 20)
        linear_gain_curve = 10.0 ** (gain_db / 20.0)

        # Normalize gain curve relative to midpoint so we don't blow out dynamic range
        norm_gain_curve = linear_gain_curve / np.median(linear_gain_curve)

        # 5. Symmetric gain mask across track (port mirrored + starboard)
        full_gain_row = np.concatenate([norm_gain_curve[::-1], norm_gain_curve])
        gain_matrix = np.tile(full_gain_row, (h, 1))

        # Apply TVG
        calibrated = img * gain_matrix
        # Soft-clip to [0.0, 1.0]
        calibrated = np.clip(calibrated, 0.0, 1.0)

        metrics = {
            "absorption_alpha_db_per_km": float(alpha_db_km),
            "spreading_coefficient": float(spreading_coeff),
            "max_applied_gain_db": float(np.max(gain_db)),
            "min_applied_gain_db": float(np.min(gain_db)),
            "max_linear_multiplier": float(np.max(norm_gain_curve)),
        }

        return calibrated, metrics
