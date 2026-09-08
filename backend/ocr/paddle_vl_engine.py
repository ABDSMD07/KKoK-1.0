from pathlib import Path

import torch
from paddleocr import PaddleOCRVL


class PaddleOCRVLEngine:
    def __init__(self):
        self.pipeline = PaddleOCRVL(
            pipeline_version="v1.5"
        )

    def predict(self, image_path: str):
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        return list(
            self.pipeline.predict(str(image_path))
        )