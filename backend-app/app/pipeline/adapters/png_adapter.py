import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import numpy as np
from PIL import Image

from app.pipeline.adapters.base import BaseDeviceAdapter
from app.pipeline.contracts import NavigationSample, NormalizedSonarFrame


class PngMetadataAdapter(BaseDeviceAdapter):
    """
    Adapter for PNG waterfall imagery with optional companion JSON metadata.
    Splits long continuous waterfall recordings into standard survey frames.
    """

    def parse(
        self,
        source: Union[str, Path, bytes],
        survey_id: UUID,
        sss_file_id: Optional[UUID] = None,
        frame_height: int = 1024,
        metadata_json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[NormalizedSonarFrame]:
        # 1. Load image
        if isinstance(source, bytes):
            img = Image.open(io.BytesIO(source))
        else:
            img = Image.open(str(source))

        # Convert to grayscale 8-bit/16-bit
        img_gray = img.convert("L")
        raw_arr = np.array(img_gray, dtype=np.float32) / 255.0  # Normalize to [0.0, 1.0]

        # 2. Extract or infer companion metadata
        meta = metadata_json or {}
        if not meta and isinstance(source, (str, Path)):
            json_path = Path(source).with_suffix(".json")
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

        lat = float(meta.get("latitude", 13.0827))  # Default coastal Chennai / Bay of Bengal coordinate
        lon = float(meta.get("longitude", 80.2707))
        alt = float(meta.get("altitude_m", 15.0))
        depth = float(meta.get("depth_m", 25.0))
        heading = float(meta.get("heading_deg", 90.0))
        speed = float(meta.get("speed_knots", 4.5))
        pitch = float(meta.get("pitch_deg", 0.0))
        roll = float(meta.get("roll_deg", 0.0))
        yaw = float(meta.get("yaw_deg", 0.0))
        slant_range = float(meta.get("slant_range_max_m", 75.0))
        sound_speed = float(meta.get("sound_speed_mps", 1500.0))
        freq = float(meta.get("frequency_khz", 455.0))

        total_pings, samples_per_ping = raw_arr.shape
        frames: List[NormalizedSonarFrame] = []

        # 3. Slice waterfall into sequential frames
        frame_idx = 0
        step = max(frame_height, 128)
        for start_y in range(0, total_pings, step):
            end_y = min(start_y + step, total_pings)
            slice_data = raw_arr[start_y:end_y, :]

            # Pad final frame if shorter than standard height
            if slice_data.shape[0] < step and total_pings > step:
                pad_height = step - slice_data.shape[0]
                slice_data = np.pad(slice_data, ((0, pad_height), (0, 0)), mode="edge")

            # Interpolate navigation along track
            ping_fraction = start_y / max(total_pings, 1)
            d_lat = float(meta.get("delta_lat", 0.001)) * ping_fraction
            d_lon = float(meta.get("delta_lon", 0.001)) * ping_fraction

            nav = NavigationSample(
                latitude=lat + d_lat,
                longitude=lon + d_lon,
                altitude_m=alt,
                depth_m=depth,
                heading_deg=heading,
                speed_knots=speed,
                pitch_deg=pitch,
                roll_deg=roll,
                yaw_deg=yaw,
                timestamp=datetime.now(timezone.utc),
            )

            # Separate port and starboard channels (half across track)
            mid_x = samples_per_ping // 2
            port_ch = slice_data[:, :mid_x]
            starboard_ch = slice_data[:, mid_x:]

            frame = NormalizedSonarFrame(
                survey_id=survey_id,
                sss_file_id=sss_file_id,
                frame_number=frame_idx,
                intensity=slice_data,
                port_channels=port_ch,
                starboard_channels=starboard_ch,
                navigation=nav,
                slant_range_max_m=slant_range,
                sound_speed_mps=sound_speed,
                frequency_khz=freq,
                metadata={
                    "source_format": "png+json",
                    "start_ping": start_y,
                    "end_ping": end_y,
                    "original_shape": [total_pings, samples_per_ping],
                },
            )
            frames.append(frame)
            frame_idx += 1

        return frames
