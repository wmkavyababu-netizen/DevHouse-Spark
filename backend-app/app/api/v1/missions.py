import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import UserContext, get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/missions", tags=["Ocean Cleanup Missions"])


class MissionCreateRequest(BaseModel):
    name: str = Field(..., description="Mission operational title")
    target_cluster: str = Field(..., description="Target cluster code or label")
    assigned_vessel: Optional[str] = Field("Ocean Guardian (ROV Unit)", description="Assigned vessel or dive unit")
    estimated_recovery_kg: Optional[float] = Field(1200.0, description="Estimated debris weight in kg")
    notes: Optional[str] = Field("", description="Operational sortie notes")


class MissionStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Updated status: planned, active, completed, cancelled")
    recovered_kg: Optional[float] = Field(None, description="Actual recovered debris weight in kg upon completion")
    notes: Optional[str] = Field(None, description="Completion or progress remarks")


class MissionItem(BaseModel):
    id: str
    name: str
    target_cluster: str
    target_count: int
    assigned_vessel: str
    lead_agency: str
    status: str  # planned, active, completed, cancelled
    estimated_recovery_kg: float
    recovered_kg: float
    date: str
    notes: str


IN_MEMORY_MISSIONS: List[Dict[str, Any]] = [
    {
        "id": "MSN-2026-01",
        "name": "Bay of Bengal Ghost Gear Extraction Sortie 1",
        "target_cluster": "Cluster #104: 3x Derelict Gillnets",
        "target_count": 3,
        "assigned_vessel": "Ocean Guardian (Support Tug + Crane)",
        "lead_agency": "Ocean Cleanup Taskforce",
        "status": "active",
        "estimated_recovery_kg": 1850.0,
        "recovered_kg": 620.0,
        "date": "2026-09-12",
        "notes": "Operations active in Sector 4 benthic trench.",
    },
    {
        "id": "MSN-2026-02",
        "name": "Harbor Channel Navigational Hazard Clearance",
        "target_cluster": "Cluster #089: 2x Metal Drums + Hull Debris",
        "target_count": 2,
        "assigned_vessel": "Port Tender 4 (Commercial Diver Unit)",
        "lead_agency": "Coastal Cleanup Unit",
        "status": "completed",
        "estimated_recovery_kg": 920.0,
        "recovered_kg": 920.0,
        "date": "2026-09-08",
        "notes": "Target cleared and verified via post-cleanup acoustic survey.",
    },
]


@router.get("", response_model=List[MissionItem])
async def list_missions(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: UserContext = Depends(get_current_user),
):
    """Lists cleanup missions and recovery progress."""
    missions = IN_MEMORY_MISSIONS
    if status_filter:
        missions = [m for m in missions if m["status"] == status_filter]
    return missions


@router.post("", response_model=MissionItem, status_code=status.HTTP_201_CREATED)
async def create_mission(
    payload: MissionCreateRequest,
    current_user: UserContext = Depends(require_role("cleanup_organization", "admin")),
):
    """Plans and schedules a new debris extraction mission."""
    new_id = f"MSN-2026-0{len(IN_MEMORY_MISSIONS) + 1}"
    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    new_msn = {
        "id": new_id,
        "name": payload.name.strip(),
        "target_cluster": payload.target_cluster.strip(),
        "target_count": 2,
        "assigned_vessel": payload.assigned_vessel or "Ocean Guardian (ROV Unit)",
        "lead_agency": current_user.organization_name or "Ocean Cleanup Taskforce",
        "status": "planned",
        "estimated_recovery_kg": payload.estimated_recovery_kg or 1000.0,
        "recovered_kg": 0.0,
        "date": today_iso,
        "notes": payload.notes or "Mission scheduled for deployment.",
    }
    IN_MEMORY_MISSIONS.insert(0, new_msn)
    logger.info("Mission %s created by user %s", new_id, current_user.email)
    return new_msn


@router.patch("/{mission_id}/status", response_model=MissionItem)
async def update_mission_status(
    mission_id: str,
    payload: MissionStatusUpdateRequest,
    current_user: UserContext = Depends(require_role("cleanup_organization", "admin")),
):
    """Updates mission status (planned -> active -> completed) and logs recovered tonnage."""
    for m in IN_MEMORY_MISSIONS:
        if m["id"] == mission_id:
            m["status"] = payload.status
            if payload.recovered_kg is not None:
                m["recovered_kg"] = payload.recovered_kg
            if payload.notes:
                m["notes"] = payload.notes
            return m
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mission {mission_id} not found")
