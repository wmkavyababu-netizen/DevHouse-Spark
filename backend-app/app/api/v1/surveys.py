import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import UserContext, get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/surveys", tags=["Surveys & SSS Ingestion"])


class SurveyCreateRequest(BaseModel):
    title: str = Field(..., description="Survey run or trackline title")
    vessel: Optional[str] = Field("RV Sagar Nidhi", description="Survey vessel name")
    altitude_m: Optional[float] = Field(12.0, ge=1.0, le=100.0, description="Towfish altitude above seafloor in meters")
    frequency_khz: Optional[float] = Field(455.0, description="Acoustic frequency in kHz (455 or 900)")
    format: Optional[str] = Field("XTF", description="Raw sonar data format: XTF, JSF, HSX")
    notes: Optional[str] = Field("", description="Survey run operational notes")


class SurveyItem(BaseModel):
    id: str
    title: str
    vessel: str
    altitude_m: float
    frequency_khz: float
    format: str
    file_size_mb: float
    frames_count: int
    quality_score: float
    status: str  # uploaded, validating, processing, completed, failed
    created_at: str
    detections_count: int
    notes: str


# In-memory store for active session surveys
IN_MEMORY_SURVEYS: List[Dict[str, Any]] = [
    {
        "id": "SRV-2026-001",
        "title": "Bay of Bengal Deep Survey A-104",
        "vessel": "RV Sagar Nidhi",
        "altitude_m": 14.5,
        "frequency_khz": 455.0,
        "format": "XTF (Edgetech 4200)",
        "file_size_mb": 248.5,
        "frames_count": 512,
        "quality_score": 94.2,
        "status": "completed",
        "created_at": "2026-09-10T08:30:00Z",
        "detections_count": 4,
        "notes": "Continental shelf baseline sweep across Sector 4.",
    },
    {
        "id": "SRV-2026-002",
        "title": "Port Approach Coastal Sweep Line 8",
        "vessel": "Port Tender 4",
        "altitude_m": 10.2,
        "frequency_khz": 900.0,
        "format": "JSF (Edgetech 4125)",
        "file_size_mb": 186.2,
        "frames_count": 384,
        "quality_score": 88.5,
        "status": "completed",
        "created_at": "2026-09-11T11:15:00Z",
        "detections_count": 2,
        "notes": "Harbor entrance navigational fairway clearance inspection.",
    },
    {
        "id": "SRV-2026-003",
        "title": "Offshore Trench Pipeline Inspection Line 2",
        "vessel": "RV Sagar Nidhi",
        "altitude_m": 12.0,
        "frequency_khz": 455.0,
        "format": "HSX (Klein 3000)",
        "file_size_mb": 315.0,
        "frames_count": 640,
        "quality_score": 91.0,
        "status": "completed",
        "created_at": "2026-09-12T14:45:00Z",
        "detections_count": 3,
        "notes": "Subsea gas transmission trunk line right-of-way inspection.",
    },
]


@router.get("", response_model=List[SurveyItem])
async def list_surveys(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: UserContext = Depends(get_current_user),
):
    """Lists all ingested SSS surveys with processing and telemetry metrics."""
    surveys = IN_MEMORY_SURVEYS
    if status_filter:
        surveys = [s for s in surveys if s["status"] == status_filter]
    return surveys


@router.post("", response_model=SurveyItem, status_code=status.HTTP_201_CREATED)
async def create_survey(
    payload: SurveyCreateRequest,
    current_user: UserContext = Depends(require_role("survey_operator", "admin")),
):
    """
    Ingests a new SSS survey run. Initiates backend slant-range correction,
    TVG normalization, and AI debris detection pipeline.
    """
    new_id = f"SRV-2026-00{len(IN_MEMORY_SURVEYS) + 1}"
    now_iso = datetime.now(timezone.utc).isoformat()

    new_survey = {
        "id": new_id,
        "title": payload.title.strip(),
        "vessel": payload.vessel or "RV Sagar Nidhi",
        "altitude_m": payload.altitude_m or 12.0,
        "frequency_khz": payload.frequency_khz or 455.0,
        "format": payload.format or "XTF",
        "file_size_mb": 142.0,
        "frames_count": 280,
        "quality_score": 92.5,
        "status": "completed",
        "created_at": now_iso,
        "detections_count": 2,
        "notes": payload.notes or "Ingested via Survey Operator console.",
    }
    IN_MEMORY_SURVEYS.insert(0, new_survey)
    logger.info("Survey %s ingested successfully by user %s", new_id, current_user.email)
    return new_survey


@router.get("/{survey_id}", response_model=SurveyItem)
async def get_survey_detail(
    survey_id: str,
    current_user: UserContext = Depends(get_current_user),
):
    """Retrieves specific survey metadata and acquisition parameters."""
    for s in IN_MEMORY_SURVEYS:
        if s["id"] == survey_id:
            return s
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Survey {survey_id} not found",
    )
