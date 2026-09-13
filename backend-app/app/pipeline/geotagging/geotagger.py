import math
from typing import Any, Dict, List, Tuple


class GeodesicGeotagger:
    """
    Computes precise geospatial WGS-84 coordinates for side-scan sonar detections.
    Combines vessel/towfish GPS, gyro heading, and horizontal ground-range geometry.
    Computes uncertainty radius based on acoustic beam spread and GPS dilution of precision.
    """

    EARTH_RADIUS_M = 6371000.0  # Mean spherical Earth radius

    def calculate_geotag(
        self,
        towfish_lat: float,
        towfish_lon: float,
        heading_deg: float,
        bbox: List[float],
        frame_width: int,
        frame_height: int,
        altitude_m: float = 15.0,
        slant_range_max_m: float = 75.0,
        gps_uncertainty_m: float = 1.5,
    ) -> Tuple[float, float, float, Dict[str, Any]]:
        """
        Returns:
          target_lat: float
          target_lon: float
          uncertainty_radius_meters: float
          details: dict
        """
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0
        nadir_x = frame_width / 2.0

        pixel_size_m = slant_range_max_m / nadir_x

        # 1. Across-track distance and direction
        dx_px = center_x - nadir_x
        slant_range_m = (abs(dx_px) / nadir_x) * slant_range_max_m
        
        # Ground range: Rg = sqrt(Rs^2 - h^2)
        if slant_range_m >= altitude_m:
            ground_range_m = math.sqrt(slant_range_m**2 - altitude_m**2)
        else:
            # Nadir fallback
            ground_range_m = slant_range_m * 0.5

        # Port is -90 deg from heading, Starboard is +90 deg
        if dx_px < 0:
            across_track_bearing = (heading_deg - 90.0) % 360.0
        else:
            across_track_bearing = (heading_deg + 90.0) % 360.0

        # Along-track offset relative to frame center
        dy_px = center_y - (frame_height / 2.0)
        along_track_m = dy_px * pixel_size_m

        # Combined horizontal displacement vector from towfish
        total_dist_m = math.sqrt(ground_range_m**2 + along_track_m**2)
        
        # Angle offset from heading
        if total_dist_m > 0:
            rel_bearing_rad = math.atan2(
                ground_range_m if dx_px >= 0 else -ground_range_m,
                along_track_m,
            )
            target_bearing_deg = (heading_deg + math.degrees(rel_bearing_rad)) % 360.0
        else:
            target_bearing_deg = heading_deg

        # 2. Geodesic Forward Projection (WGS-84 spherical)
        lat_rad = math.radians(towfish_lat)
        lon_rad = math.radians(towfish_lon)
        bearing_rad = math.radians(target_bearing_deg)
        dist_rad = total_dist_m / self.EARTH_RADIUS_M

        target_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(dist_rad)
            + math.cos(lat_rad) * math.sin(dist_rad) * math.cos(bearing_rad)
        )
        target_lon_rad = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(dist_rad) * math.cos(lat_rad),
            math.cos(dist_rad) - math.sin(lat_rad) * math.sin(target_lat_rad),
        )

        target_lat = math.degrees(target_lat_rad)
        target_lon = math.degrees(target_lon_rad)

        # 3. Uncertainty Radius: GPS baseline + acoustic beam expansion
        acoustic_uncertainty_m = slant_range_m * 0.035
        uncertainty_radius_m = round(gps_uncertainty_m + acoustic_uncertainty_m, 2)

        details = {
            "towfish_lat": towfish_lat,
            "towfish_lon": towfish_lon,
            "towfish_heading": heading_deg,
            "ground_range_m": round(ground_range_m, 2),
            "slant_range_m": round(slant_range_m, 2),
            "along_track_m": round(along_track_m, 2),
            "total_displacement_m": round(total_dist_m, 2),
            "target_bearing_deg": round(target_bearing_deg, 2),
            "uncertainty_radius_m": uncertainty_radius_m,
        }

        return round(target_lat, 7), round(target_lon, 7), uncertainty_radius_m, details


geodesic_geotagger = GeodesicGeotagger()
