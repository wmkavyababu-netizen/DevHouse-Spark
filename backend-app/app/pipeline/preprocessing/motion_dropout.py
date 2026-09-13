from typing import Any, Dict, Tuple
import numpy as np

from app.pipeline.contracts import NormalizedSonarFrame


class MotionDropoutHandler:
    """
    Handles acoustic data dropouts, missing ping packets, and vehicle motion effects.
    CRITICAL RULE: If IMU metadata is missing, flag it and gracefully skip or downgrade
    motion-dependent corrections — DO NOT fail the survey.
    """

    def process(
        self,
        intensity: np.ndarray,
        frame: NormalizedSonarFrame,
        max_interpolatable_gap: int = 4,
        **kwargs,
    ) -> Tuple[np.ndarray, Dict[str, Any], Dict[str, float]]:
        h, w = intensity.shape
        cleaned = intensity.copy()
        nav = frame.navigation

        # 1. Detect dropout lines (pings with 0.0 or NaN across > 95% of samples)
        nan_mask = np.isnan(cleaned)
        cleaned[nan_mask] = 0.0

        zero_fraction_per_line = np.mean(cleaned < 1e-4, axis=1)
        dropout_line_indices = np.where(zero_fraction_per_line > 0.95)[0].tolist()

        # Interpolate small dropout gaps
        interpolated_lines = 0
        if dropout_line_indices:
            for row in dropout_line_indices:
                # Look for preceding and succeeding valid lines
                prev_row = row - 1
                while prev_row in dropout_line_indices and prev_row >= 0:
                    prev_row -= 1
                next_row = row + 1
                while next_row in dropout_line_indices and next_row < h:
                    next_row += 1

                gap_size = (next_row - prev_row) - 1
                if 0 <= prev_row < h and 0 <= next_row < h and gap_size <= max_interpolatable_gap:
                    # Linear interpolation between valid pings
                    alpha = (row - prev_row) / float(gap_size + 1)
                    cleaned[row] = (1.0 - alpha) * cleaned[prev_row] + alpha * cleaned[next_row]
                    interpolated_lines += 1

        # 2. Check IMU metadata presence
        has_roll = nav.roll_deg is not None and abs(nav.roll_deg) > 1e-3
        has_pitch = nav.pitch_deg is not None and abs(nav.pitch_deg) > 1e-3
        has_yaw = nav.yaw_deg is not None and abs(nav.yaw_deg) > 1e-3
        imu_available = (nav.roll_deg is not None and nav.pitch_deg is not None)

        dropout_flags: Dict[str, Any] = {
            "total_lines": h,
            "dropout_line_count": len(dropout_line_indices),
            "interpolated_lines": interpolated_lines,
            "unrecovered_dropouts": len(dropout_line_indices) - interpolated_lines,
            "imu_missing": not imu_available,
            "motion_correction_applied": False,
        }

        # 3. Motion handling with graceful downgrade
        if not imu_available:
            # Graceful downgrade: Keep frame, log flags, skip motion-dependent warping
            dropout_flags["status"] = "imu_missing_downgraded_gracefully"
            dropout_flags["warning"] = "IMU telemetry missing. Motion correction skipped; survey preserved."
        else:
            # Apply roll compensation if roll angle is present
            roll_deg = float(nav.roll_deg or 0.0)
            if abs(roll_deg) > 0.2:
                # Small across-track shift: shift_pixels = (roll_rad) * (w / 2)
                shift_px = int(np.tan(np.radians(roll_deg)) * (w / 4.0))
                if abs(shift_px) > 0 and abs(shift_px) < w // 8:
                    cleaned = np.roll(cleaned, shift_px, axis=1)
                    dropout_flags["motion_correction_applied"] = True
                    dropout_flags["roll_compensated_deg"] = roll_deg
                    dropout_flags["roll_shift_pixels"] = shift_px
            dropout_flags["status"] = "imu_valid"

        metrics = {
            "dropout_rate_pct": float((len(dropout_line_indices) / float(h)) * 100.0),
            "recovery_rate_pct": float((interpolated_lines / max(len(dropout_line_indices), 1)) * 100.0),
            "imu_present": 1.0 if imu_available else 0.0,
            "roll_deg": float(nav.roll_deg or 0.0),
            "pitch_deg": float(nav.pitch_deg or 0.0),
        }

        return cleaned, dropout_flags, metrics
