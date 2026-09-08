import torch

from ocr.paddle_vl_engine import PaddleOCRVLEngine


IMAGE_PATH = "test_data/test.jpeg"


def main():
    print("Loading PaddleOCR-VL 1.5...")

    engine = PaddleOCRVLEngine()

    print("Running inference...")

    results = engine.predict(IMAGE_PATH)

    print(f"\nNumber of results: {len(results)}")

    for i, result in enumerate(results):
        print(f"\n========== RESULT {i} ==========")

        result.print()

        result.save_to_json(
            save_path="./paddle_output"
        )

        result.save_to_markdown(
            save_path="./paddle_output"
        )


if __name__ == "__main__":
    main()