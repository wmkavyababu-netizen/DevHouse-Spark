import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public Portal"])


class PublicZone(BaseModel):
    id: str
    name: str
    region: str
    latitude: float
    longitude: float
    status: str
    description: str


class AccessRequestPayload(BaseModel):
    fullName: str = Field(..., description="Applicant's full name")
    officialEmail: str = Field(..., description="Official institutional email")
    organization: str = Field(..., description="Organization or agency name")
    stakeholderRole: str = Field(..., description="Requested role: survey_operator, marine_expert, etc.")
    phoneNumber: Optional[str] = Field(None, description="Contact phone number")
    purposeOfAccess: str = Field(..., description="Statement of intended purpose")


class AccessRequestResponse(BaseModel):
    requestId: str
    status: str
    message: str


PUBLIC_ZONES: List[Dict[str, Any]] = [
    {
        "id": "PUB-CHN-01",
        "name": "Chennai Coastal Shelf Zone A",
        "region": "East Coast • Tamil Nadu",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "status": "Active Survey Track",
        "description": "Permitted SSS survey corridor for benthic debris categorization.",
    },
    {
        "id": "PUB-ENR-02",
        "name": "Ennore Marine Approach Fairway",
        "region": "Coromandel Coast • Tamil Nadu",
        "latitude": 13.235,
        "longitude": 80.325,
        "status": "Active Survey Track",
        "description": "Acoustic survey trackline monitoring maritime navigation lanes.",
    },
    {
        "id": "PUB-MNR-03",
        "name": "Gulf of Mannar Ecological Buffer",
        "region": "Southeast Coast • Tamil Nadu",
        "latitude": 9.288,
        "longitude": 79.135,
        "status": "Conservation Priority Zone",
        "description": "Marine biodiversity buffer with acoustic verification of ghost gear clearance.",
    },
    {
        "id": "PUB-KCH-04",
        "name": "Cochin Port Approach Fairway",
        "region": "Southwest Coast • Kerala",
        "latitude": 9.965,
        "longitude": 76.242,
        "status": "Hazard Cleared",
        "description": "Post-cleanup acoustic verification confirming clearance of shipping lane obstacles.",
    },
]


@router.get("/zones", response_model=List[PublicZone])
async def get_public_zones():
    """
    Returns generalized, public-safe survey zones.
    Exact private bathymetric coordinates, pending detections, and internal expert notes
    are strictly excluded.
    """
    return PUBLIC_ZONES


@router.post("/access-request", response_model=AccessRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_access_request(payload: AccessRequestPayload):
    """Processes an institutional access request from a marine stakeholder."""
    req_id = f"TARANG-REQ-{datetime.now(timezone.utc).year}-{datetime.now(timezone.utc).strftime('%m%d%H%M')}"
    logger.info("Access request %s submitted by %s (%s)", req_id, payload.fullName, payload.officialEmail)

    return AccessRequestResponse(
        requestId=req_id,
        status="received",
        message="Your institutional access application has been received and logged for administrative verification.",
    )
