import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import numpy as np

from app.pipeline.adapters.base import BaseDeviceAdapter
from app.pipeline.contracts import NavigationSample, NormalizedSonarFrame


class GenericDeviceAdapter(BaseDeviceAdapter):
    """
    Fallback adapter for HSX, SDF, or raw raster binaries.
    Interprets binary payloads as raw 8-bit or 16-bit acoustic raster lines with default telemetry.
    """

    def parse(
        self,
        source: Union[str, Path, bytes],
        survey_id: UUID,
        sss_file_id: Optional[UUID] = None,
        frame_height: int = 1024,
        line_width: int = 1024,
        **kwargs,
    ) -> List[NormalizedSonarFrame]:
        if isinstance(source, bytes):
            data = source
        else:
            with open(str(source), "rb") as f:
                data = f.read()

        # Try interpreting as uint8
        total_samples = len(data)
        if total_samples < line_width:
            arr = np.zeros((frame_height, line_width), dtype=np.float32)
        else:
            pings = total_samples // line_width
            truncated_len = pings * line_width
            arr = np.frombuffer(data[:truncated_len], dtype=np.uint8).astype(np.float32) / 255.0
            arr = arr.reshape((pings, line_width))

        frames: List[NormalizedSonarFrame] = []
        frame_idx = 0
        pings_total = arr.shape[0]

        step = max(frame_height, 128)
        for i in range(0, pings_total, step):
            slice_data = arr[i : i + step, :]
            if slice_data.shape[0] < step:
                pad = step - slice_data.shape[0]
                slice_data = np.pad(slice_data, ((0, pad), (0, 0)), mode="edge")

            nav = NavigationSample(
                latitude=13.0827,
                longitude=80.2707,
                altitude_m=15.0,
                heading_deg=90.0,
                speed_knots=4.5,
                timestamp=datetime.now(timezone.utc),
            )

            half = line_width // 2
            frame = NormalizedSonarFrame(
                survey_id=survey_id,
                sss_file_id=sss_file_id,
                frame_number=frame_idx,
                intensity=slice_data,
                port_channels=slice_data[:, :half],
                starboard_channels=slice_data[:, half:],
                navigation=nav,
                metadata={"source_format": "generic_binary", "start_ping": i},
            )
            frames.append(frame)
            frame_idx += 1

        return frames
