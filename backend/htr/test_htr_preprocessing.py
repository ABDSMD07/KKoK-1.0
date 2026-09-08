from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from htr_engine import HTREngine


TEST_IMAGES = [
    "test_image.png",
    "test_image_2.png",
    "test_image_3.png",
]


def preprocess_variants(image_path):
    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Variant 1: grayscale
    gray_path = image_path.with_name(
        image_path.stem + "_gray.png"
    )
    cv2.imwrite(str(gray_path), gray)

    # Variant 2: contrast enhancement
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    enhanced_path = image_path.with_name(
        image_path.stem + "_enhanced.png"
    )
    cv2.imwrite(str(enhanced_path), enhanced)

    # Variant 3: adaptive threshold
    threshold = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    threshold_path = image_path.with_name(
        image_path.stem + "_threshold.png"
    )
    cv2.imwrite(str(threshold_path), threshold)

    return [
        image_path,
        gray_path,
        enhanced_path,
        threshold_path,
    ]


if __name__ == "__main__":

    print("=" * 60)
    print("HTR PREPROCESSING BASELINE TEST")
    print("=" * 60)

    engine = HTREngine()

    for image_name in TEST_IMAGES:

        image_path = Path(image_name)

        if not image_path.exists():
            print(f"\nSKIPPING: {image_name}")
            print("Image not found.")
            continue

        print("\n" + "=" * 60)
        print(f"IMAGE: {image_name}")
        print("=" * 60)

        variants = preprocess_variants(image_path)

        for variant in variants:

            print("\n----------------------------------------")
            print(f"Variant: {variant.name}")
            print("----------------------------------------")

            try:
                result = engine.predict(variant)
                print("Prediction:")
                print(result)

            except Exception as e:
                print("ERROR:")
                print(e)