import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from geoalchemy2.functions import ST_MakePoint, ST_SetSRID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection import Detection, Geotag
from app.models.target import DetectionTargetMapping, Target, TargetHistory


class TargetClusterer:
    """
    Spatial & Class Target Deduplication and Fusion engine.
    Associates multi-pass / multi-frame acoustic observations of the same physical seabed object,
    fuses spatial positions and confidences, and maintains audit trails in target_history.
    """

    EARTH_RADIUS_M = 6371000.0

    @staticmethod
    def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates surface distance in meters between two WGS-84 coordinates."""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)

        a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return TargetClusterer.EARTH_RADIUS_M * c

    async def associate_or_create_target(
        self,
        db: AsyncSession,
        detection_id: UUID,
        survey_frame_id: UUID,
        target_class_id: int,
        lat: float,
        lon: float,
        confidence: float,
        class_name: str,
        max_cluster_distance_m: float = 10.0,
    ) -> Tuple[Target, bool]:
        """
        Associates detection with an existing target if within cluster distance,
        otherwise creates a new target record.
        Returns: (target, is_new_target)
        """
        # Search existing targets with the same debris class
        res = await db.execute(
            select(Target).where(Target.target_class_id == target_class_id)
        )
        candidates = res.scalars().all()

        best_match: Optional[Target] = None
        min_dist = float("inf")

        for cand in candidates:
            # Extract target coordinates from metadata or compute distance
            cand_meta = cand.metadata_json or {}
            cand_lat = cand_meta.get("lat")
            cand_lon = cand_meta.get("lon")

            if cand_lat is not None and cand_lon is not None:
                dist = self.haversine_distance_m(lat, lon, float(cand_lat), float(cand_lon))
                if dist <= max_cluster_distance_m and dist < min_dist:
                    min_dist = dist
                    best_match = cand

        now = datetime.now(timezone.utc)
        dec_conf = Decimal(f"{confidence:.4f}")

        if best_match is not None:
            # ------------------------------------------------------------------
            # FUSE INTO EXISTING TARGET
            # ------------------------------------------------------------------
            prev_conf = best_match.fused_confidence
            prev_status = best_match.status
            old_count = best_match.observation_count
            new_count = old_count + 1

            # Recalculate centroid coordinates
            cand_meta = best_match.metadata_json or {}
            old_lat = float(cand_meta.get("lat", lat))
            old_lon = float(cand_meta.get("lon", lon))

            fused_lat = round((old_lat * old_count + lat) / new_count, 7)
            fused_lon = round((old_lon * old_count + lon) / new_count, 7)

            # Confidence fusion across observations (boost with repeated observations)
            fused_conf_val = min(float(max(prev_conf, dec_conf)) * 1.02, 0.9990)
            new_fused_conf = Decimal(f"{fused_conf_val:.4f}")

            # Update target record
            best_match.location = ST_SetSRID(ST_MakePoint(fused_lon, fused_lat), 4326)
            best_match.fused_confidence = new_fused_conf
            best_match.observation_count = new_count
            cand_meta.update({"lat": fused_lat, "lon": fused_lon, "last_seen_frame_id": str(survey_frame_id)})
            best_match.metadata_json = cand_meta

            # Record history audit
            hist = TargetHistory(
                target_id=best_match.id,
                previous_status=prev_status,
                new_status=best_match.status,
                previous_confidence=prev_conf,
                new_confidence=new_fused_conf,
                change_reason=f"Fused detection {detection_id} (observation #{new_count}, distance: {min_dist:.1f}m)",
                metadata_json={"detection_id": str(detection_id), "distance_m": min_dist},
            )
            db.add(hist)

            # Record many-to-many mapping
            assoc_score = Decimal(f"{max(0.0, 1.0 - (min_dist / max_cluster_distance_m)):.4f}")
            mapping = DetectionTargetMapping(
                detection_id=detection_id,
                target_id=best_match.id,
                association_score=assoc_score,
            )
            db.add(mapping)

            await db.flush()
            return best_match, False

        else:
            # ------------------------------------------------------------------
            # CREATE NEW TARGET
            # ------------------------------------------------------------------
            geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
            is_unknown = (target_class_id == 5) or (class_name == "unknown")
            desc = (
                f"Confirmed {class_name.replace('_', ' ')} debris candidate"
                if not is_unknown
                else "Unclassified acoustic anomaly / unknown debris candidate"
            )
            initial_status = "detected" if not is_unknown else "unclassified"

            target = Target(
                target_class_id=target_class_id,
                location=geom,
                best_survey_frame_id=survey_frame_id,
                status=initial_status,
                fused_confidence=dec_conf,
                observation_count=1,
                description=desc,
                metadata_json={
                    "lat": lat,
                    "lon": lon,
                    "initial_frame_id": str(survey_frame_id),
                    "is_ood": is_unknown,
                    "class_name": class_name,
                },
            )
            db.add(target)
            await db.flush()

            # Record initial history
            hist = TargetHistory(
                target_id=target.id,
                previous_status=None,
                new_status=initial_status,
                previous_confidence=None,
                new_confidence=dec_conf,
                change_reason=f"Initial registration from detection {detection_id}" + (" (unclassified OOD anomaly)" if is_unknown else ""),
                metadata_json={"detection_id": str(detection_id), "is_ood": is_unknown},
            )
            db.add(hist)

            # Record initial mapping
            mapping = DetectionTargetMapping(
                detection_id=detection_id,
                target_id=target.id,
                association_score=Decimal("1.0000"),
            )
            db.add(mapping)

            await db.flush()
            return target, True


target_clusterer = TargetClusterer()
