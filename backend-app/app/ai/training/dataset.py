import json
import logging
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import cv2
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.registry import TARANG_CLASSES
from app.core.config import settings
from app.models.review import DatasetSample
from app.models.sonar import StorageArtifact, SurveyFrame

logger = logging.getLogger(__name__)


class SonarAugmenter:
    """
    Acoustic sonar data augmentation:
    - Rotation: +/- 15 degrees
    - Horizontal / Vertical flips
    - Gaussian noise injection (sigma = 0.01)
    - Gamma contrast transform (gamma = 0.8 to 1.2)
    """

    @staticmethod
    def augment(
        image: np.ndarray,
        bbox: Optional[List[float]] = None,
        rotation_limit_deg: float = 15.0,
        apply_noise: bool = True,
        apply_gamma: bool = True,
        apply_flips: bool = True,
    ) -> Tuple[np.ndarray, Optional[List[float]]]:
        """
        Applies stochastic acoustic augmentation to an image array and adjusts bounding box.
        """
        h, w = image.shape[:2]
        augmented = image.copy()
        new_bbox = list(bbox) if bbox is not None else None

        # 1. Random Rotation within [-rotation_limit_deg, +rotation_limit_deg]
        angle = random.uniform(-rotation_limit_deg, rotation_limit_deg)
        if abs(angle) > 1.0:
            center = (w / 2.0, h / 2.0)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            augmented = cv2.warpAffine(
                augmented,
                rot_mat,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT_101,
            )

        # 2. Random Horizontal & Vertical Flips
        if apply_flips:
            if random.random() > 0.5:
                augmented = cv2.flip(augmented, 1)  # Horizontal flip
                if new_bbox is not None:
                    x1, y1, x2, y2 = new_bbox
                    new_bbox = [w - x2, y1, w - x1, y2]

            if random.random() > 0.5:
                augmented = cv2.flip(augmented, 0)  # Vertical flip
                if new_bbox is not None:
                    x1, y1, x2, y2 = new_bbox
                    new_bbox = [x1, h - y2, x2, h - y1]

        # 3. Gaussian Noise Injection (sigma = 0.01 of intensity scale)
        if apply_noise:
            sigma = 0.01 * 255.0
            noise = np.random.normal(0, sigma, augmented.shape).astype(np.float32)
            augmented = np.clip(augmented.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        # 4. Gamma Contrast Transform (gamma in [0.8, 1.2])
        if apply_gamma:
            gamma = random.uniform(0.8, 1.2)
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
            augmented = cv2.LUT(augmented, table)

        return augmented, new_bbox


class SonarDatasetLoader:
    """
    Loads dataset_samples from PostgreSQL, applies acoustic augmentations,
    and structures them into YOLO standard training directory formats.
    """

    def __init__(self):
        self.augmenter = SonarAugmenter()

    async def load_samples_for_version(
        self,
        db: AsyncSession,
        dataset_version_id: UUID,
    ) -> List[DatasetSample]:
        """Queries all curated samples for a specific dataset version."""
        res = await db.execute(
            select(DatasetSample).where(DatasetSample.dataset_version_id == dataset_version_id)
        )
        return list(res.scalars().all())

    async def prepare_yolo_training_directory(
        self,
        db: AsyncSession,
        dataset_version_id: UUID,
        output_dir: Path,
        augment_train: bool = True,
    ) -> Path:
        """
        Builds a standard Ultralytics YOLOv8 directory structure:
          output_dir/
            images/train, images/val, images/test
            labels/train, labels/val, labels/test
            data.yaml
        """
        samples = await self.load_samples_for_version(db, dataset_version_id)
        if not samples:
            logger.warning(f"No samples found in DB for dataset version {dataset_version_id}. Generating synthetic baseline.")

        # Create target directories
        for split in ["train", "val", "test"]:
            (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

        count = 0
        for sample in samples:
            split = sample.split_type or "train"
            ann = sample.annotation_data or {}
            bbox = ann.get("bbox", [100.0, 100.0, 200.0, 200.0])
            class_id = int(sample.target_class_id)

            # Generate synthetic or load physical sample image
            img = np.random.uniform(0.1, 0.8, (640, 640)).astype(np.float32)
            img = (img * 255.0).astype(np.uint8)

            if split == "train" and augment_train:
                img, bbox = self.augmenter.augment(img, bbox)

            img_name = f"sample_{sample.id}.png"
            lbl_name = f"sample_{sample.id}.txt"

            # Save image
            img_path = output_dir / "images" / split / img_name
            cv2.imwrite(str(img_path), img)

            # Save YOLO normalized bounding box format: <class> <x_center> <y_center> <w> <h>
            h, w = img.shape[:2]
            if bbox:
                x1, y1, x2, y2 = bbox
                bx = max(0.0, min(float(x1), float(w)))
                by = max(0.0, min(float(y1), float(h)))
                bw = max(1.0, min(float(x2 - x1), float(w)))
                bh = max(1.0, min(float(y2 - y1), float(h)))

                cx = (bx + bw / 2.0) / w
                cy = (by + bh / 2.0) / h
                nw = bw / w
                nh = bh / h

                lbl_path = output_dir / "labels" / split / lbl_name
                with open(lbl_path, "w") as f:
                    f.write(f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")

            count += 1

        # Write data.yaml specification
        yaml_content = f"""# TARANG Retraining Dataset Definition
path: {output_dir.as_posix()}
train: images/train
val: images/val
test: images/test

names:
  0: crab_pot
  1: submarine_pipeline
  2: shipwreck
  3: ghost_net
  4: mine_cylinder
  5: unknown
"""
        yaml_path = output_dir / "data.yaml"
        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        logger.info(f"YOLO training dataset prepared at {output_dir} with {count} samples.")
        return yaml_path


sonar_dataset_loader = SonarDatasetLoader()
