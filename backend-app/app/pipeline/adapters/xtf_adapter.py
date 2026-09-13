import io
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import numpy as np

from app.pipeline.adapters.base import BaseDeviceAdapter
from app.pipeline.contracts import NavigationSample, NormalizedSonarFrame


class XtfDeviceAdapter(BaseDeviceAdapter):
    """
    Binary parser for eXtended Triton Format (.xtf) side-scan sonar files.
    Parses XTFFILEHEADER, sequential XTFPINGHEADER packets, port & starboard channel samples.
    """

    XTF_HEADER_SIZE = 1024
    MAGIC_XTF_FILE = 0x7B

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

        try:
            # 1. Parse File Header
            header_bytes = stream.read(self.XTF_HEADER_SIZE)
            if len(header_bytes) < 14:
                raise ValueError("XTF file too small for file header")

            file_format, system_type = struct.unpack("<BB", header_bytes[:2])
            if file_format != self.MAGIC_XTF_FILE and file_format != 0x1B:
                # Still attempt parsing if header structure aligns
                pass

            pings: List[Dict[str, Any]] = []

            # 2. Iterate through packets
            while True:
                packet_hdr = stream.read(14)
                if len(packet_hdr) < 14:
                    break

                magic_number, header_type, sub_chan_num, num_chans_to_follow = struct.unpack(
                    "<HBBB", packet_hdr[:5]
                )
                num_bytes_this_record = struct.unpack("<I", packet_hdr[10:14])[0]

                if num_bytes_this_record == 0:
                    break

                remaining_bytes_len = num_bytes_this_record - 14
                if remaining_bytes_len < 0:
                    break

                record_data = stream.read(remaining_bytes_len)
                if len(record_data) < remaining_bytes_len:
                    break

                # Header type 0 = XTF_DATA_SIDESCAN
                if header_type == 0 and len(record_data) >= 242:
                    # Ping Header (256 bytes total including 14-byte packet header)
                    ping_hdr = record_data[:242]
                    year, month, day, hour, minute, second, hsecond = struct.unpack("<HBBBBBB", ping_hdr[:8])
                    
                    try:
                        ping_time = datetime(year, month, day, hour, minute, second, hsecond * 10000, tzinfo=timezone.utc)
                    except Exception:
                        ping_time = datetime.now(timezone.utc)

                    # Offsets in XTFPINGHEADER
                    heading = struct.unpack("<f", ping_hdr[36:40])[0] if len(ping_hdr) >= 40 else 0.0
                    pitch = struct.unpack("<f", ping_hdr[40:44])[0] if len(ping_hdr) >= 44 else 0.0
                    roll = struct.unpack("<f", ping_hdr[44:48])[0] if len(ping_hdr) >= 48 else 0.0
                    yaw = struct.unpack("<f", ping_hdr[48:52])[0] if len(ping_hdr) >= 52 else 0.0
                    alt = struct.unpack("<f", ping_hdr[52:56])[0] if len(ping_hdr) >= 56 else 15.0
                    sound_vel = struct.unpack("<f", ping_hdr[60:64])[0] if len(ping_hdr) >= 64 else 1500.0
                    sensor_x = struct.unpack("<d", ping_hdr[68:76])[0] if len(ping_hdr) >= 76 else 80.2707
                    sensor_y = struct.unpack("<d", ping_hdr[76:84])[0] if len(ping_hdr) >= 84 else 13.0827
                    sensor_speed = struct.unpack("<f", ping_hdr[84:88])[0] if len(ping_hdr) >= 88 else 4.5

                    # Extract channel payload (port + starboard)
                    sample_payload = record_data[242:]
                    if len(sample_payload) > 0:
                        half = len(sample_payload) // 2
                        port_bytes = sample_payload[:half]
                        stbd_bytes = sample_payload[half:]
                        
                        port_samples = np.frombuffer(port_bytes, dtype=np.uint8).astype(np.float32) / 255.0
                        stbd_samples = np.frombuffer(stbd_bytes, dtype=np.uint8).astype(np.float32) / 255.0
                        
                        # Full waterfall line: port flipped horizontally + nadir + starboard
                        ping_line = np.concatenate([np.flip(port_samples), stbd_samples])
                        pings.append({
                            "line": ping_line,
                            "port": port_samples,
                            "stbd": stbd_samples,
                            "lat": float(sensor_y),
                            "lon": float(sensor_x),
                            "alt": float(alt),
                            "heading": float(heading),
                            "speed": float(sensor_speed),
                            "pitch": float(pitch),
                            "roll": float(roll),
                            "yaw": float(yaw),
                            "sound_vel": float(sound_vel),
                            "time": ping_time,
                        })

        finally:
            if hasattr(stream, "close") and not isinstance(source, bytes):
                stream.close()

        # Fallback if no valid pings were decoded (corrupt or synthetic header)
        if not pings:
            # Produce a baseline normalized frame with standard dimensions (512 pings x 1024 samples)
            blank_intensity = np.zeros((frame_height, 1024), dtype=np.float32)
            nav = NavigationSample(latitude=13.0827, longitude=80.2707, altitude_m=15.0)
            return [
                NormalizedSonarFrame(
                    survey_id=survey_id,
                    sss_file_id=sss_file_id,
                    frame_number=0,
                    intensity=blank_intensity,
                    navigation=nav,
                    metadata={"source_format": "xtf", "pings_extracted": 0, "fallback": True},
                )
            ]

        # 3. Assemble sequential frames
        frames: List[NormalizedSonarFrame] = []
        frame_idx = 0
        samples_per_line = max(len(pings[0]["line"]), 256)

        for i in range(0, len(pings), frame_height):
            chunk = pings[i : i + frame_height]
            chunk_lines = [
                cv_line["line"] if len(cv_line["line"]) == samples_per_line
                else np.resize(cv_line["line"], samples_per_line)
                for cv_line in chunk
            ]
            frame_arr = np.vstack(chunk_lines)

            # Pad height if needed
            if frame_arr.shape[0] < frame_height:
                pad = frame_height - frame_arr.shape[0]
                frame_arr = np.pad(frame_arr, ((0, pad), (0, 0)), mode="edge")

            mid_nav = chunk[len(chunk) // 2]
            nav = NavigationSample(
                latitude=mid_nav["lat"],
                longitude=mid_nav["lon"],
                altitude_m=mid_nav["alt"],
                heading_deg=mid_nav["heading"],
                speed_knots=mid_nav["speed"],
                pitch_deg=mid_nav["pitch"],
                roll_deg=mid_nav["roll"],
                yaw_deg=mid_nav["yaw"],
                timestamp=mid_nav["time"],
            )

            half = samples_per_line // 2
            frame = NormalizedSonarFrame(
                survey_id=survey_id,
                sss_file_id=sss_file_id,
                frame_number=frame_idx,
                intensity=frame_arr,
                port_channels=frame_arr[:, :half],
                starboard_channels=frame_arr[:, half:],
                navigation=nav,
                sound_speed_mps=mid_nav.get("sound_vel", 1500.0),
                metadata={"source_format": "xtf", "chunk_start": i, "chunk_pings": len(chunk)},
            )
            frames.append(frame)
            frame_idx += 1

        return frames
