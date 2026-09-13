from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import numpy as np


@dataclass
class NavigationSample:
    """Towfish and vessel geospatial/telemetry navigation record."""
    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    depth_m: Optional[float] = None
    heading_deg: Optional[float] = None
    speed_knots: Optional[float] = None
    pitch_deg: Optional[float] = None
    roll_deg: Optional[float] = None
    yaw_deg: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class NormalizedSonarFrame:
    """
    Standardized in-memory sonar frame contract produced by the Device Adapter layer.
    Intensity array represents the stitched port-starboard waterfall image [H, W],
    where H is number of pings (along-track) and W is number of range samples (across-track).
    Center column represents the nadir (towfish flight path).
    """
    survey_id: UUID
    frame_number: int
    intensity: np.ndarray  # 2D float32 array normalized to [0.0, 1.0] or raw [H, W]
    navigation: NavigationSample
    slant_range_max_m: float = 75.0
    sound_speed_mps: float = 1500.0
    frequency_khz: Optional[float] = None
    sample_rate_hz: Optional[float] = None
    port_channels: Optional[np.ndarray] = None
    starboard_channels: Optional[np.ndarray] = None
    sss_file_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def height(self) -> int:
        return int(self.intensity.shape[0])

    @property
    def width(self) -> int:
        return int(self.intensity.shape[1])


@dataclass
class TileSample:
    """Overlapping frame sub-tile ready for AI model inference (Prompt G)."""
    tile_id: str
    frame_number: int
    tile_index: int
    bbox_px: List[int]  # [x1, y1, x2, y2] relative to parent frame
    image_data: np.ndarray  # [H, W] or [H, W, 3] uint8/float32
    pixel_size_m: float = 0.05


@dataclass
class PreprocessingOutput:
    """Final output bundle from the preprocessing pipeline."""
    enhanced_frame: np.ndarray  # [H, W] uint8 [0, 255]
    shadow_map: np.ndarray  # [H, W] uint8 binary mask [0, 255]
    nadir_mask: np.ndarray  # [H, W] uint8 binary mask [0, 255]
    quality_score: float  # 0.0 to 100.0
    dropout_flags: Dict[str, Any]
    metrics: Dict[str, float]
    processing_parameters: Dict[str, Any]
    tiles: List[TileSample] = field(default_factory=list)


@dataclass
class StageResult:
    """Execution status and metric payload from an individual preprocessing stage."""
    stage_name: str
    stage_order: int
    status: str  # "completed", "failed", "skipped"
    progress_percentage: float  # 0.0 to 100.0
    execution_time_ms: float
    parameters_used: Dict[str, Any] = field(default_factory=dict)
    log_message: str = ""
    error_message: Optional[str] = None
