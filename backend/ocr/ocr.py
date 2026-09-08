from pathlib import Path
import json
import shutil
import traceback

from PIL import Image
import pytesseract
from pytesseract import Output


# ==========================================================
# TESSERACT
# ==========================================================

WINDOWS_TESSERACT = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def configure_tesseract():

    print("[OCR] Searching for Tesseract...")


    # Check system PATH first

    system_tesseract = shutil.which(
        "tesseract"
    )


    if system_tesseract:

        pytesseract.pytesseract.tesseract_cmd = (
            system_tesseract
        )

        print(
            "[OCR] Tesseract found in PATH:",
            system_tesseract
        )

        return system_tesseract


    # Check normal Windows location

    if WINDOWS_TESSERACT.exists():

        pytesseract.pytesseract.tesseract_cmd = str(
            WINDOWS_TESSERACT
        )

        print(
            "[OCR] Tesseract found:",
            WINDOWS_TESSERACT
        )

        return str(
            WINDOWS_TESSERACT
        )


    raise RuntimeError(
        "Tesseract executable not found. "
        "Expected at "
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )


# ==========================================================
# VERIFY ENGINE
# ==========================================================

def verify_tesseract():

    configure_tesseract()


    try:

        version = (
            pytesseract.get_tesseract_version()
        )


        print(
            "[OCR] Tesseract version:",
            version
        )


        return str(version)


    except Exception as error:

        raise RuntimeError(
            f"Tesseract could not start: {error}"
        ) from error


# ==========================================================
# OCR SINGLE IMAGE
# ==========================================================

def process_image(
    image_path: Path,
    lang: str = "eng",
    psm: int = 4,
):
    """
    lang: Tesseract language code(s), e.g. "eng", "hin+eng".
    psm: Page Segmentation Mode. Land records are forms
        (labels/values/tables), NOT a uniform paragraph, so the
        previous hardcoded default (6 = "single uniform block")
        was a poor fit. Default changed to 4 ("assume a single
        column of text of variable sizes"), which is closer to
        a form layout. Also try 11 ("sparse text, no particular
        order") if 4 still performs badly on your documents —
        which one wins is an empirical question, test both on
        your real sample images.
    """

    image_path = Path(
        image_path
    )


    print(
        "[OCR] Reading page:",
        image_path
    )


    if not image_path.exists():

        raise FileNotFoundError(
            f"Image does not exist: {image_path}"
        )


    try:

        image = Image.open(
            image_path
        )


        image = image.convert(
            "L"
        )


        print(
            "[OCR] Image size:",
            image.size
        )


        data = (
            pytesseract.image_to_data(

                image,

                output_type=Output.DICT,

                lang=lang,

                config=f"--oem 3 --psm {psm}",
            )
        )


        image.close()


    except Exception as error:

        print(
            "[OCR IMAGE ERROR]",
            image_path.name,
            error
        )


        traceback.print_exc()


        raise


    words = []

    total_confidence = 0.0

    valid_words = 0


    for index in range(
        len(data["text"])
    ):

        text = str(
            data["text"][index]
        ).strip()


        if not text:
            continue


        try:

            confidence = float(
                data["conf"][index]
            )


        except (
            TypeError,
            ValueError
        ):

            confidence = -1


        if confidence < 0:
            continue


        word = {

            "text":
                text,

            "confidence":
                round(
                    confidence,
                    2
                ),

            "bbox": {

                "x":
                    int(
                        data["left"][index]
                    ),

                "y":
                    int(
                        data["top"][index]
                    ),

                "width":
                    int(
                        data["width"][index]
                    ),

                "height":
                    int(
                        data["height"][index]
                    ),
            },
        }


        words.append(
            word
        )


        total_confidence += (
            confidence
        )


        valid_words += 1


    full_text = " ".join(

        word["text"]

        for word in words
    )


    average_confidence = (

        round(
            total_confidence
            / valid_words,
            2
        )

        if valid_words > 0

        else 0.0
    )


    print(
        f"[OCR] {image_path.name}: "
        f"{len(words)} words, "
        f"{average_confidence}% confidence"
    )


    return {

        "image":
            image_path.name,

        "text":
            full_text,

        "confidence":
            average_confidence,

        "word_count":
            len(words),

        "words":
            words,
    }


# ==========================================================
# COMPLETE DOCUMENT OCR
# ==========================================================

def process_document(
    processed_dir: Path,
    lang: str = "eng",
    psm: int = 4,
):

    processed_dir = Path(
        processed_dir
    )


    print("")
    print(
        "======================================"
    )
    print(
        "[OCR] STARTING DOCUMENT OCR"
    )
    print(
        "[OCR] Directory:",
        processed_dir
    )
    print(
        "======================================"
    )


    if not processed_dir.exists():

        raise RuntimeError(
            f"Processed directory does not exist: "
            f"{processed_dir}"
        )


    # ======================================================
    # VERIFY TESSERACT
    # ======================================================

    tesseract_version = (
        verify_tesseract()
    )


    # ======================================================
    # DEBUG DIRECTORY CONTENTS
    # ======================================================

    directory_files = list(
        processed_dir.iterdir()
    )


    print(
        "[OCR] Files currently in directory:"
    )


    for file in directory_files:

        print(
            "   ",
            file.name
        )


    # ======================================================
    # FIND PAGE IMAGES
    # ======================================================

    image_files = sorted(

        [

            file

            for file
            in directory_files

            if (
                file.is_file()

                and file.suffix.lower()
                in {
                    ".png",
                    ".jpg",
                    ".jpeg",
                }
            )

        ],

        key=lambda path:
            path.name.lower()
    )


    print(
        "[OCR] Images found:",
        len(image_files)
    )


    if not image_files:

        raise RuntimeError(
            "No PNG/JPG/JPEG pages found in "
            f"{processed_dir}"
        )


    # ======================================================
    # PROCESS PAGES
    # ======================================================

    page_results = []


    for page_number, image_path in enumerate(
        image_files,
        start=1
    ):

        print(
            f"[OCR] Processing page "
            f"{page_number}/{len(image_files)}"
        )


        result = process_image(
            image_path,
            lang=lang,
            psm=psm,
        )


        result[
            "page_number"
        ] = page_number


        page_results.append(
            result
        )


    # ======================================================
    # COMBINE TEXT
    # ======================================================

    complete_text = "\n\n".join(

        page["text"]

        for page in page_results

        if page["text"]
    )


    # ======================================================
    # DOCUMENT CONFIDENCE
    # ======================================================

    total_words = sum(

        page["word_count"]

        for page in page_results
    )


    if total_words > 0:

        weighted_total = sum(

            (
                page["confidence"]
                * page["word_count"]
            )

            for page
            in page_results
        )


        document_confidence = round(

            weighted_total
            / total_words,

            2
        )


    else:

        document_confidence = 0.0


    # ======================================================
    # FINAL RESULT
    # ======================================================

    result = {

        "engine":
            "Tesseract",

        "tesseract_version":
            tesseract_version,

        "document_confidence":
            document_confidence,

        "page_count":
            len(page_results),

        "word_count":
            total_words,

        "text":
            complete_text,

        "pages":
            page_results,
    }


    print(
        "[OCR] Document OCR completed."
    )


    print(
        "[OCR] Confidence:",
        document_confidence
    )


    return result


# ==========================================================
# SAVE JSON
# ==========================================================

def save_ocr_result(
    result,
    output_path: Path
):

    output_path = Path(
        output_path
    )


    print(
        "[OCR] Attempting to save JSON:"
    )

    print(
        "[OCR]",
        output_path
    )


    try:

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        # Save directly while debugging.
        # This makes the resulting location obvious.

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as json_file:

            json.dump(
                result,
                json_file,
                ensure_ascii=False,
                indent=4
            )


        # Verify immediately.

        if not output_path.exists():

            raise RuntimeError(
                "JSON write completed but file "
                "does not exist."
            )


        file_size = (
            output_path
            .stat()
            .st_size
        )


        print(
            "[OCR] JSON CREATED SUCCESSFULLY"
        )


        print(
            "[OCR] JSON size:",
            file_size,
            "bytes"
        )


        print(
            "[OCR] JSON path:",
            output_path.resolve()
        )


        return str(
            output_path
        )


    except Exception as error:

        print(
            "[OCR JSON ERROR]",
            error
        )


        traceback.print_exc()


        raise