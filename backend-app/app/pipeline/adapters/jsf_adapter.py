import io
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import numpy as np

from app.pipeline.adapters.base import BaseDeviceAdapter
from app.pipeline.contracts import NavigationSample, NormalizedSonarFrame


class JsfDeviceAdapter(BaseDeviceAdapter):
    """
    Binary parser for EdgeTech JSF format side-scan sonar files.
    Parses 16-byte message headers (marker 0x1601) and Type 80 sonar trace packets.
    """

    JSF_SYNC_MARKER = 0x1601
    MSG_TYPE_SONAR_DATA = 80

    def parse(
        self,
        source: Union[str, Path, bytes],
        survey_id: UUID,
        sss_file_id: Optional[UUID] = None,
        frame_height: int = 1024,
        **kwargs,
    ) -> List[NormalizedSonarFrame]:
        if isinstance(source, bytes):
            stream = io.BytesIO(source)
        else:
            stream = open(str(source), "rb")

        pings_port: List[Dict[str, Any]] = []
        pings_stbd: List[Dict[str, Any]] = []

        try:
            while True:
                msg_hdr = stream.read(16)
                if len(msg_hdr) < 16:
                    break

                marker, version, session, msg_type, cmd, subsystem, channel, seq, res, payload_len = struct.unpack(
                    "<HBBHBBBBHI", msg_hdr
                )

                if marker != self.JSF_SYNC_MARKER:
                    # Sync marker search
                    continue

                if payload_len == 0 or payload_len > 10_000_000:
                    continue

                payload = stream.read(payload_len)
                if len(payload) < payload_len:
                    break

                # Process Type 80 Sonar Data
                if msg_type == self.MSG_TYPE_SONAR_DATA and len(payload) >= 240:
                    # Parse Type 80 Header (240 bytes)
                    # Timestamp
                    time_s = struct.unpack("<I", payload[0:4])[0]
                    millis = struct.unpack("<I", payload[4:8])[0]
                    try:
                        ping_time = datetime.fromtimestamp(time_s, tz=timezone.utc)
                    except Exception:
                        ping_time = datetime.now(timezone.utc)

                    # Navigation & Telemetry
                    raw_x = struct.unpack("<i", payload[80:84])[0] if len(payload) >= 84 else 0
                    raw_y = struct.unpack("<i", payload[84:88])[0] if len(payload) >= 88 else 0
                    coord_units = struct.unpack("<h", payload[88:90])[0] if len(payload) >= 90 else 1

                    # Scaling coordinate
                    scale = 10000.0 if coord_units == 2 else (1.0 if coord_units == 1 else 3600.0)
                    lon = (raw_x / scale) if raw_x != 0 else 80.2707
                    lat = (raw_y / scale) if raw_y != 0 else 13.0827

                    altitude = struct.unpack("<f", payload[120:124])[0] if len(payload) >= 124 else 15.0
                    depth = struct.unpack("<f", payload[124:128])[0] if len(payload) >= 128 else 25.0
                    heading = (struct.unpack("<h", payload[156:158])[0] / 100.0) if len(payload) >= 158 else 90.0
                    pitch = (struct.unpack("<h", payload[158:160])[0] / 100.0) if len(payload) >= 160 else 0.0
                    roll = (struct.unpack("<h", payload[160:162])[0] / 100.0) if len(payload) >= 162 else 0.0

                    num_samples = struct.unpack("<H", payload[114:116])[0] if len(payload) >= 116 else 512
                    sample_data = payload[240:]

                    # Unpack 16-bit integer samples
                    if len(sample_data) >= num_samples * 2:
                        samples = np.frombuffer(sample_data[: num_samples * 2], dtype=np.int16).astype(np.float32)
                        # Normalize envelope to [0.0, 1.0]
                        max_val = np.max(samples) if len(samples) > 0 else 1.0
                        samples = samples / max(max_val, 1.0)
                    else:
                        samples = np.zeros(num_samples, dtype=np.float32)

                    record = {
                        "samples": samples,
                        "lat": float(lat),
                        "lon": float(lon),
                        "alt": float(altitude if altitude > 0 else 15.0),
                        "depth": float(depth),
                        "heading": float(heading),
                        "pitch": float(pitch),
                        "roll": float(roll),
                        "time": ping_time,
                    }

                    if channel == 0:  # Port
                        pings_port.append(record)
                    else:  # Starboard
                        pings_stbd.append(record)

        finally:
            if hasattr(stream, "close") and not isinstance(source, bytes):
                stream.close()

        # Balance channel lengths
        total_pings = min(len(pings_port), len(pings_stbd))
        if total_pings == 0:
            # Fallback frame
            blank = np.zeros((frame_height, 1024), dtype=np.float32)
            return [
                NormalizedSonarFrame(
                    survey_id=survey_id,
                    sss_file_id=sss_file_id,
                    frame_number=0,
                    intensity=blank,
                    navigation=NavigationSample(latitude=13.0827, longitude=80.2707, altitude_m=15.0),
                    metadata={"source_format": "jsf", "fallback": True},
                )
            ]

        frames: List[NormalizedSonarFrame] = []
        frame_idx = 0

        for i in range(0, total_pings, frame_height):
            chunk_p = pings_port[i : i + frame_height]
            chunk_s = pings_stbd[i : i + frame_height]
            
            p_lines = [p["samples"] for p in chunk_p]
            s_lines = [s["samples"] for s in chunk_s]

            # Uniform width
            w_p = max(len(l) for l in p_lines)
            w_s = max(len(l) for l in s_lines)
            target_w = max(w_p, w_s, 512)

            norm_p = np.array([np.resize(l, target_w) for l in p_lines], dtype=np.float32)
            norm_s = np.array([np.resize(l, target_w) for l in s_lines], dtype=np.float32)

            # Waterfall: flip port horizontally, concatenate starboard
            waterfall = np.hstack([np.fliplr(norm_p), norm_s])

            if waterfall.shape[0] < frame_height:
                pad = frame_height - waterfall.shape[0]
                waterfall = np.pad(waterfall, ((0, pad), (0, 0)), mode="edge")
                norm_p = np.pad(norm_p, ((0, pad), (0, 0)), mode="edge")
                norm_s = np.pad(norm_s, ((0, pad), (0, 0)), mode="edge")

            mid_p = chunk_p[len(chunk_p) // 2]
            nav = NavigationSample(
                latitude=mid_p["lat"],
                longitude=mid_p["lon"],
                altitude_m=mid_p["alt"],
                depth_m=mid_p["depth"],
                heading_deg=mid_p["heading"],
                pitch_deg=mid_p["pitch"],
                roll_deg=mid_p["roll"],
                timestamp=mid_p["time"],
            )

            frame = NormalizedSonarFrame(
                survey_id=survey_id,
                sss_file_id=sss_file_id,
                frame_number=frame_idx,
                intensity=waterfall,
                port_channels=norm_p,
                starboard_channels=norm_s,
                navigation=nav,
                metadata={"source_format": "jsf", "chunk_start": i, "pings": len(chunk_p)},
            )
            frames.append(frame)
            frame_idx += 1

        return frames
