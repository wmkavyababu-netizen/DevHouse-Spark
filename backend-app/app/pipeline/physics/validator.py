from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Typical height expectations (meters) for marine debris classes
CLASS_TYPICAL_HEIGHTS_M = {
    0: 0.6,   # crab_pot (0.4m - 0.8m)
    1: 0.8,   # submarine_pipeline (0.5m - 1.5m)
    2: 4.5,   # shipwreck (2.0m - 10.0m)
    3: 0.3,   # ghost_net (draped flush or low relief)
    4: 1.0,   # mine_cylinder (0.6m - 1.5m)
}


class AcousticPhysicsValidator:
    """
    Validates side-scan sonar detections against underwater acoustic principles:
    1. Slant-range plausibility: Target must reside outside the water column (Rs >= h).
    2. Acoustic shadow consistency: Shadow must radiate strictly away from the nadir centerline,
       and its length must correlate with towfish altitude via H = (h * Ls) / (Rs + Ls).
    3. Expected size-at-range: Checks cross-track beam spreading and dimensions.
    """

    def validate_detection(
        self,
        bbox: List[float],  # [x1, y1, x2, y2] relative to full frame
        target_class_id: int,
        frame_width: int,
        frame_height: int,
        altitude_m: float = 15.0,
        slant_range_max_m: float = 75.0,
        beam_width_deg: float = 1.0,
        shadow_map: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive acoustic physics validation.
        Returns:
          slant_range_meters: float
          acoustic_shadow_length_meters: float
          expected_size_meters: float
          shadow_consistency_score: float in [0.0, 1.0]
          is_plausible: bool
          validation_details: dict
        """
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0
        nadir_x = frame_width / 2.0

        pixel_size_m = slant_range_max_m / (nadir_x)

        # 1. Slant Range Calculation
        # Across-track pixel offset from nadir centerline
        dx_px = abs(center_x - nadir_x)
        is_port = center_x < nadir_x
        slant_range_m = float(max(dx_px * pixel_size_m, 1.0))

        # Check water column plausibility: target cannot be in water column (Rs < h)
        water_column_limit_m = altitude_m * 0.95
        in_water_column = slant_range_m < water_column_limit_m

        # 2. Target Dimension Calculation
        bbox_w_px = max(x2 - x1, 1.0)
        bbox_h_px = max(y2 - y1, 1.0)
        detected_w_m = float(bbox_w_px * pixel_size_m)
        detected_h_m = float(bbox_h_px * pixel_size_m)
        target_span_m = float(max(detected_w_m, detected_h_m))

        # Beam spreading expansion at range: Delta = R * tan(theta)
        beam_expansion_m = slant_range_m * np.tan(np.radians(beam_width_deg))

        # 3. Acoustic Shadow Analysis
        # Expected shadow length from acoustics: Ls = (H * Rs) / (h - H)
        expected_obj_h = CLASS_TYPICAL_HEIGHTS_M.get(target_class_id, 0.8)
        denom = max(altitude_m - expected_obj_h, 1.0)
        theoretical_shadow_len_m = float((expected_obj_h * slant_range_m) / denom)

        # Inspect real shadow in shadow_map if provided
        measured_shadow_len_m = 0.0
        directional_valid = True

        if shadow_map is not None:
            # Check shadow pixels directly adjacent to target extending away from nadir
            y_start = max(0, int(y1))
            y_end = min(frame_height, int(y2))
            
            if is_port:
                # Shadow must extend to the LEFT (decreasing x)
                shadow_search_start = max(0, int(x1) - int(theoretical_shadow_len_m / pixel_size_m * 1.5))
                shadow_region = shadow_map[y_start:y_end, shadow_search_start:int(x1)]
                # Check for erroneous shadow toward nadir (to the right)
                nadir_side_region = shadow_map[y_start:y_end, int(x2):min(frame_width, int(x2) + 20)]
            else:
                # Shadow must extend to the RIGHT (increasing x)
                shadow_search_end = min(frame_width, int(x2) + int(theoretical_shadow_len_m / pixel_size_m * 1.5))
                shadow_region = shadow_map[y_start:y_end, int(x2):shadow_search_end]
                # Check for erroneous shadow toward nadir (to the left)
                nadir_side_region = shadow_map[y_start:y_end, max(0, int(x1) - 20):int(x1)]

            if shadow_region.size > 0:
                shadow_pixels = np.sum(shadow_region == 255)
                measured_shadow_len_m = float((shadow_pixels / max(y_end - y_start, 1)) * pixel_size_m)

            # Inverted shadow check: if there is stronger shadow toward nadir than away, unphysical!
            if nadir_side_region.size > 0 and shadow_region.size > 0:
                nadir_shadow_density = np.mean(nadir_side_region == 255)
                outward_shadow_density = np.mean(shadow_region == 255)
                if nadir_shadow_density > 0.4 and nadir_shadow_density > outward_shadow_density * 2.0:
                    directional_valid = False

        else:
            # Fallback estimation based on theoretical acoustics
            measured_shadow_len_m = theoretical_shadow_len_m

        # 4. Compute Shadow Consistency Score in [0.0, 1.0]
        if in_water_column:
            shadow_consistency = 0.15  # Severe penalty: inside water column
            is_plausible = False
        elif not directional_valid:
            shadow_consistency = 0.10  # Severe penalty: shadow points wrong way
            is_plausible = False
        else:
            # Ratio between measured and theoretical shadow length
            len_ratio = measured_shadow_len_m / max(theoretical_shadow_len_m, 0.5)
            # Bell curve matching around 1.0
            shadow_match = float(np.exp(-0.5 * ((len_ratio - 1.0) / 0.8) ** 2))
            
            # Size plausibility (debris shouldn't be 100 meters wide)
            size_plausible = 0.2 <= target_span_m <= 45.0
            size_penalty = 1.0 if size_plausible else 0.4

            shadow_consistency = float(np.clip(shadow_match * size_penalty * 0.95 + 0.05, 0.0, 1.0))
            is_plausible = shadow_consistency >= 0.35

        return {
            "slant_range_meters": round(slant_range_m, 2),
            "acoustic_shadow_length_meters": round(measured_shadow_len_m, 2),
            "expected_size_meters": round(target_span_m, 2),
            "shadow_consistency_score": round(shadow_consistency, 4),
            "is_plausible": is_plausible,
            "validation_details": {
                "theoretical_shadow_length_m": round(theoretical_shadow_len_m, 2),
                "in_water_column": in_water_column,
                "directional_valid": directional_valid,
                "beam_expansion_m": round(beam_expansion_m, 2),
                "is_port": is_port,
                "altitude_m": altitude_m,
            },
        }


physics_validator = AcousticPhysicsValidator()
