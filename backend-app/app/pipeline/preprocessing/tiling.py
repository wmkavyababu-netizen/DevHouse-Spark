from typing import Any, Dict, List, Tuple
from uuid import uuid4
import numpy as np

from app.pipeline.contracts import NormalizedSonarFrame, TileSample


class FrameTiler:
    """
    Tiling / Inference Preparation stage.
    Slices large side-scan sonar frames into standardized overlapping tiles (e.g. 640x640)
    preserving spatial resolution for YOLO object detection and U-Net segmentation (Prompt G).
    """

    def process(
        self,
        enhanced_image: np.ndarray,
        frame: NormalizedSonarFrame,
        tile_size: int = 640,
        stride: int = 512,
        **kwargs,
    ) -> Tuple[List[TileSample], Dict[str, Any]]:
        h, w = enhanced_image.shape[:2]

        # Calculate spatial resolution (meters per pixel across track)
        channel_width_px = w / 2.0
        range_max_m = frame.slant_range_max_m if frame.slant_range_max_m > 0 else 75.0
        pixel_size_m = float(range_max_m / max(channel_width_px, 1.0))

        tiles: List[TileSample] = []
        tile_idx = 0

        # Adjust tile size if image is smaller than standard tile size
        eff_tile_h = min(tile_size, h)
        eff_tile_w = min(tile_size, w)
        eff_stride_y = min(stride, eff_tile_h)
        eff_stride_x = min(stride, eff_tile_w)

        y_coords = list(range(0, max(h - eff_tile_h + 1, 1), eff_stride_y))
        if y_coords and y_coords[-1] + eff_tile_h < h:
            y_coords.append(h - eff_tile_h)

        x_coords = list(range(0, max(w - eff_tile_w + 1, 1), eff_stride_x))
        if x_coords and x_coords[-1] + eff_tile_w < w:
            x_coords.append(w - eff_tile_w)

        for y in y_coords:
            for x in x_coords:
                x2 = min(x + eff_tile_w, w)
                y2 = min(y + eff_tile_h, h)
                tile_crop = enhanced_image[y:y2, x:x2]

                # Ensure exact tile_size dimensions with edge padding if necessary
                if tile_crop.shape[0] < tile_size or tile_crop.shape[1] < tile_size:
                    pad_y = max(0, tile_size - tile_crop.shape[0])
                    pad_x = max(0, tile_size - tile_crop.shape[1])
                    tile_crop = np.pad(tile_crop, ((0, pad_y), (0, pad_x)), mode="constant", constant_values=0)

                tile_sample = TileSample(
                    tile_id=f"{frame.survey_id}_{frame.frame_number}_{tile_idx}_{uuid4().hex[:6]}",
                    frame_number=frame.frame_number,
                    tile_index=tile_idx,
                    bbox_px=[x, y, x2, y2],
                    image_data=tile_crop,
                    pixel_size_m=pixel_size_m,
                )
                tiles.append(tile_sample)
                tile_idx += 1

        metadata = {
            "total_tiles": len(tiles),
            "tile_size": tile_size,
            "stride": stride,
            "pixel_size_meters": pixel_size_m,
            "parent_frame_shape": [h, w],
        }

        return tiles, metadata
