import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import UserContext, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/targets", tags=["Debris Targets Registry"])


class TargetItem(BaseModel):
    id: str
    code: str
    target_class: str
    class_label: str
    confidence: float
    confidence_class: str  # Class A, Class B, Class C
    latitude: float
    longitude: float
    depth_m: float
    cluster_radius_m: float
    observation_count: int
    status: str  # detected, awaiting_validation, validated, assigned, in_progress, cleared
    hazard_level: str  # critical, high, medium, low
    first_detected: str
    surveys_count: int
    description: str


IN_MEMORY_TARGETS: List[Dict[str, Any]] = [
    {
        "id": "tgt-01",
        "code": "TGT-8821",
        "target_class": "ghost_net",
        "class_label": "Derelict Trawl Net Flotilla",
        "confidence": 0.884,
        "confidence_class": "Class A",
        "latitude": 13.0839,
        "longitude": 80.2707,
        "depth_m": 24.5,
        "cluster_radius_m": 4.2,
        "observation_count": 4,
        "status": "validated",
        "hazard_level": "critical",
        "first_detected": "2026-09-08 14:22:10 UTC",
        "surveys_count": 2,
        "description": "Dense monofilament net bundle entangled on rocky benthic reef outcrop.",
    },
    {
        "id": "tgt-02",
        "code": "TGT-8822",
        "target_class": "shipwreck",
        "class_label": "Vessel Plating & Frame Hull",
        "confidence": 0.941,
        "confidence_class": "Class A",
        "latitude": 13.0885,
        "longitude": 80.2792,
        "depth_m": 31.2,
        "cluster_radius_m": 12.5,
        "observation_count": 6,
        "status": "assigned",
        "hazard_level": "high",
        "first_detected": "2026-09-02 09:15:44 UTC",
        "surveys_count": 3,
        "description": "Exposed steel keel section protruding 2.8m above acoustic seabed plane.",
    },
    {
        "id": "tgt-03",
        "code": "TGT-8823",
        "target_class": "crab_pot",
        "class_label": "Abandoned Crab Trap Line",
        "confidence": 0.724,
        "confidence_class": "Class B",
        "latitude": 13.0762,
        "longitude": 80.2641,
        "depth_m": 18.0,
        "cluster_radius_m": 2.8,
        "observation_count": 2,
        "status": "validated",
        "hazard_level": "medium",
        "first_detected": "2026-09-10 16:40:02 UTC",
        "surveys_count": 1,
        "description": "Array of 3 rectangular wire traps connected by degraded poly rope.",
    },
    {
        "id": "tgt-04",
        "code": "TGT-8824",
        "target_class": "mine_cylinder",
        "class_label": "Cylindrical Container Debris",
        "confidence": 0.765,
        "confidence_class": "Class B",
        "latitude": 13.0851,
        "longitude": 80.2721,
        "depth_m": 28.4,
        "cluster_radius_m": 1.5,
        "observation_count": 3,
        "status": "assigned",
        "hazard_level": "critical",
        "first_detected": "2026-09-05 12:08:18 UTC",
        "surveys_count": 2,
        "description": "Heavy gauge cylindrical drum partially buried in seabed sediment.",
    },
    {
        "id": "tgt-05",
        "code": "TGT-8825",
        "target_class": "submarine_pipeline",
        "class_label": "Subsea Pipeline Section",
        "confidence": 0.912,
        "confidence_class": "Class A",
        "latitude": 13.0784,
        "longitude": 80.2665,
        "depth_m": 33.1,
        "cluster_radius_m": 8.0,
        "observation_count": 5,
        "status": "validated",
        "hazard_level": "high",
        "first_detected": "2026-09-01 07:30:12 UTC",
        "surveys_count": 3,
        "description": "Exposed steel pipe joint with acoustic shadow signature.",
    },
    {
        "id": "tgt-06",
        "code": "TGT-8826",
        "target_class": "ghost_net",
        "class_label": "Derelict Trawl Net Flotilla",
        "confidence": 0.825,
        "confidence_class": "Class A",
        "latitude": 13.0801,
        "longitude": 80.2734,
        "depth_m": 22.1,
        "cluster_radius_m": 3.2,
        "observation_count": 3,
        "status": "cleared",
        "hazard_level": "low",
        "first_detected": "2026-09-07 10:11:20 UTC",
        "surveys_count": 2,
        "description": "Target removed via Mission MSN-2026-01 on 2026-09-12. Post-clearance acoustic verification confirmed clear seabed.",
    },
]


@router.get("", response_model=List[TargetItem])
async def list_targets(
    target_class: Optional[str] = Query(None, alias="class"),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: UserContext = Depends(get_current_user),
):
    """
    Lists debris targets.
    Enforces strict role-based visibility:
    - Cleanup Organization ONLY receives validated/actionable targets (never unvalidated or rejected detections).
    - Rejected detections are never returned as cleanup targets.
    """
    targets = IN_MEMORY_TARGETS

    # Enforce cleanup organization boundary
    roles = current_user.roles or []
    is_cleanup_org = "cleanup_organization" in roles

    filtered = []
    for t in targets:
        # Rejected items can NEVER be cleanup targets
        if t["status"] == "rejected":
            continue

        # Cleanup Org only sees validated, assigned, in_progress, cleared
        if is_cleanup_org and t["status"] == "detected":
            continue

        if target_class and t["target_class"] != target_class:
            continue
        if status_filter and t["status"] != status_filter:
            continue

        filtered.append(t)

    return filtered


@router.get("/{target_id}", response_model=TargetItem)
async def get_target_detail(
    target_id: str,
    current_user: UserContext = Depends(get_current_user),
):
    """Retrieves target details with acoustic history and coordinate precision."""
    for t in IN_MEMORY_TARGETS:
        if t["id"] == target_id:
            roles = current_user.roles or []
            if "cleanup_organization" in roles and t["status"] == "detected":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Target is awaiting marine expert validation before cleanup assignment.",
                )
            return t
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target {target_id} not found")
