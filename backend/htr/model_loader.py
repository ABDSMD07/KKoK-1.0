from transformers import VisionEncoderDecoderModel, AutoProcessor, AutoTokenizer
from huggingface_hub import snapshot_download


MODEL_ID = "QuickHawk/trocr-indic"


def download_model():
    print("Downloading HTR model...")

    model_path = snapshot_download(
        repo_id=MODEL_ID
    )

    print(f"Model downloaded to:\n{model_path}")

    return model_path


if __name__ == "__main__":
    download_model()
    