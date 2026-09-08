from pathlib import Path

import torch
from PIL import Image
from transformers import VisionEncoderDecoderModel, AutoProcessor, AutoTokenizer


MODEL_ID = "QuickHawk/trocr-indic"
ENCODER_MODEL = "facebook/deit-base-distilled-patch16-224"
DECODER_MODEL = "ai4bharat/IndicBART"

# IndicBART language tags. Add more here if you need other
# Indian languages later (e.g. "bn": "<2bn>" for Bengali,
# "ta": "<2ta>" for Tamil) — check ai4bharat/IndicBART's own
# tokenizer vocab for the exact supported tag list before relying
# on a new one.
LANGUAGE_TOKENS = {
    "hi": "<2hi>",   # Hindi
    "mr": "<2mr>",   # Marathi
    "en": "<2en>",   # English
}

DEFAULT_LANGUAGE = "hi"


class HTREngine:

    def __init__(self):
        print("Loading HTR model...")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Device: {self.device}")

        self.processor = AutoProcessor.from_pretrained(
            ENCODER_MODEL,
            use_fast=True
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            DECODER_MODEL,
            use_fast=True
        )

        self.model = VisionEncoderDecoderModel.from_pretrained(
            MODEL_ID
        )

        self.model.to(self.device)
        self.model.eval()

        self.bos_id = self.tokenizer._convert_token_to_id_with_added_voc("<s>")
        self.eos_id = self.tokenizer._convert_token_to_id_with_added_voc("</s>")
        self.pad_id = self.tokenizer._convert_token_to_id_with_added_voc("<pad>")

        # BUG FIX (previous version): decoder_start_id was hardcoded to
        # "<2en>" at init time, meaning the model was always told to
        # decode into English regardless of the document's actual
        # language. This silently breaks Hindi/Marathi output.
        #
        # Fix: resolve one decoder-start id PER SUPPORTED LANGUAGE up
        # front, and let predict() choose the right one per call.
        self.decoder_start_ids = {}

        for lang_code, token in LANGUAGE_TOKENS.items():
            token_id = self.tokenizer._convert_token_to_id_with_added_voc(token)

            # Sanity check: if the tokenizer doesn't actually know this
            # token, _convert_token_to_id_with_added_voc will usually
            # fall back to the unk token id. Catch that now, at load
            # time, instead of silently mis-decoding later.
            unk_id = getattr(self.tokenizer, "unk_token_id", None)
            if unk_id is not None and token_id == unk_id:
                print(
                    f"[HTR] WARNING: language tag '{token}' for "
                    f"'{lang_code}' resolved to the tokenizer's UNK "
                    f"token. This language tag may not exist in "
                    f"{DECODER_MODEL}'s vocabulary — verify before "
                    f"trusting output in this language."
                )

            self.decoder_start_ids[lang_code] = token_id

        print("HTR model loaded successfully.")
        print(f"Supported languages: {list(LANGUAGE_TOKENS.keys())}")

    def predict(self, image_path, language: str = DEFAULT_LANGUAGE):
        """
        Run handwriting recognition on one image.

        language: one of the keys in LANGUAGE_TOKENS ("hi", "mr", "en").
        Defaults to Hindi. Pass the language you expect THIS document
        (or document region) to be written in — this is not
        auto-detected.
        """

        if language not in self.decoder_start_ids:
            raise ValueError(
                f"Unsupported language '{language}'. "
                f"Supported: {list(LANGUAGE_TOKENS.keys())}. "
                f"Add it to LANGUAGE_TOKENS in htr_engine.py if the "
                f"tokenizer supports it."
            )

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        image = Image.open(image_path).convert("RGB")

        print(f"Image: {image_path}")
        print(f"Image size: {image.size}")
        print(f"Decoding language: {language}")

        pixel_values = self.processor(
            images=image,
            return_tensors="pt"
        ).pixel_values.to(self.device)

        decoder_start_id = self.decoder_start_ids[language]

        with torch.no_grad():

            outputs_ids = self.model.generate(
                pixel_values,
                use_cache=True,
                num_beams=4,
                max_length=128,
                min_length=1,
                early_stopping=True,
                pad_token_id=self.pad_id,
                bos_token_id=self.bos_id,
                eos_token_id=self.eos_id,
                decoder_start_token_id=decoder_start_id
            )

        text = self.tokenizer.decode(
            outputs_ids[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )

        return text.strip()
