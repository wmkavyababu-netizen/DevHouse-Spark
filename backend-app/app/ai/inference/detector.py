import logging
from typing import Any, Dict, List, Optional, Union
import numpy as np
from PIL import Image
from ultralytics import YOLO

from app.ai.models.registry import TARANG_CLASSES

logger = logging.getLogger(__name__)


class YOLODetector:
    """
    In-process, local YOLOv8 inference engine for marine debris detection.
    Runs entirely on local CPU/GPU with ZERO external network or API calls.
    Applies strict confidence (0.5) and NMS IoU (0.45) thresholds.
    """

    def __init__(
        self,
        model: YOLO,
        default_conf: float = 0.5,
        default_iou: float = 0.45,
    ):
        self.model = model
        self.default_conf = default_conf
        self.default_iou = default_iou

    @staticmethod
    def _prepare_image(image: Union[np.ndarray, Image.Image, str]) -> np.ndarray:
        """Converts arbitrary input format into an RGB uint8 image array."""
        if isinstance(image, str):
            img = Image.open(image).convert("RGB")
            return np.array(img)
        elif isinstance(image, Image.Image):
            return np.array(image.convert("RGB"))
        elif isinstance(image, np.ndarray):
            # Normalize float to uint8 if needed
            if image.dtype in (np.float32, np.float64):
                if image.max() <= 1.0:
                    image = (image * 255.0).astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
            # Handle grayscale 2D to 3D RGB
            if len(image.shape) == 2:
                image = np.stack([image, image, image], axis=-1)
            elif len(image.shape) == 3 and image.shape[2] == 1:
                image = np.concatenate([image, image, image], axis=-1)
            return image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

    def detect(
        self,
        image: Union[np.ndarray, Image.Image, str],
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs local inference on a single image.
        Returns list of {class_id, class_name, confidence, bbox: [x1, y1, x2, y2]}.
        """
        conf = conf_threshold if conf_threshold is not None else self.default_conf
        iou = iou_threshold if iou_threshold is not None else self.default_iou

        rgb_img = self._prepare_image(image)

        # Run local YOLOv8 predict (in-process, device='cpu', no network calls)
        results = self.model.predict(
            source=rgb_img,
            conf=conf,
            iou=iou,
            device="cpu",
            verbose=False,
        )

        detections: List[Dict[str, Any]] = []
        if not results or len(results) == 0:
            return detections

        first_res = results[0]
        if first_res.boxes is None:
            return detections

        boxes_data = first_res.boxes
        xyxy = getattr(boxes_data, "xyxy", None)
        if xyxy is None:
            return detections
        if hasattr(xyxy, "cpu"):
            xyxy = xyxy.cpu()
        if hasattr(xyxy, "numpy"):
            xyxy = xyxy.numpy()
        if len(xyxy) == 0:
            return detections

        confs = boxes_data.conf
        if hasattr(confs, "cpu"):
            confs = confs.cpu()
        if hasattr(confs, "numpy"):
            confs = confs.numpy()

        classes = boxes_data.cls
        if hasattr(classes, "cpu"):
            classes = classes.cpu()
        if hasattr(classes, "numpy"):
            classes = classes.numpy().astype(int)

        for i in range(len(xyxy)):
            box = [float(c) for c in xyxy[i]]
            score = float(confs[i])
            raw_cls = int(classes[i])

            # Check if class is within known marine debris classes (0 to 4)
            if raw_cls in (0, 1, 2, 3, 4):
                target_class_id = raw_cls
                target_class_name = TARANG_CLASSES[target_class_id]
                is_ood = False
            else:
                # Honest OOD / unknown representation: do NOT force into known classes
                target_class_id = 5
                target_class_name = "unknown"
                is_ood = True

            detections.append({
                "class_id": target_class_id,
                "class_name": target_class_name,
                "confidence": round(score, 4),
                "bbox": [round(c, 2) for c in box],  # [x1, y1, x2, y2]
                "raw_class_id": raw_cls,
                "is_ood": is_ood,
            })

        return detections

    def detect_batch(
        self,
        images: List[Union[np.ndarray, Image.Image]],
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> List[List[Dict[str, Any]]]:
        """
        Runs batch inference across multiple sub-tiles or frames.
        """
        if not images:
            return []

        prepared_batch = [self._prepare_image(img) for img in images]
        conf = conf_threshold if conf_threshold is not None else self.default_conf
        iou = iou_threshold if iou_threshold is not None else self.default_iou

        batch_results = self.model.predict(
            source=prepared_batch,
            conf=conf,
            iou=iou,
            device="cpu",
            verbose=False,
        )

        all_detections: List[List[Dict[str, Any]]] = []
        for res in batch_results:
            sample_dets: List[Dict[str, Any]] = []
            if res.boxes is not None and len(res.boxes) > 0:
                xyxy = res.boxes.xyxy.cpu().numpy()
                confs = res.boxes.conf.cpu().numpy()
                classes = res.boxes.cls.cpu().numpy().astype(int)

                for i in range(len(xyxy)):
                    raw_cls = int(classes[i])
                    if raw_cls in (0, 1, 2, 3, 4):
                        target_class_id = raw_cls
                        target_class_name = TARANG_CLASSES[target_class_id]
                        is_ood = False
                    else:
                        target_class_id = 5
                        target_class_name = "unknown"
                        is_ood = True

                    sample_dets.append({
                        "class_id": target_class_id,
                        "class_name": target_class_name,
                        "confidence": round(float(confs[i]), 4),
                        "bbox": [round(float(c), 2) for c in xyxy[i]],
                        "is_ood": is_ood,
                    })
            all_detections.append(sample_dets)

        return all_detections
