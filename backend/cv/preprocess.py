from pathlib import Path

import cv2
import numpy as np

from .quality import (
    analyze_image,
    MAX_UPSCALE,
    TARGET_GLYPH_HEIGHT,
    HIGH_NOISE_THRESHOLD,
    LOW_CONTRAST_THRESHOLD,
    ILLUMINATION_TILE_STD_THRESHOLD,
    SKEW_THRESHOLD,
    BIMODALITY_THRESHOLD,
)


# ==========================================================
# PDF SUPPORT
# ==========================================================

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf


# ==========================================================
# IMAGE HELPERS
# ==========================================================

def to_gray(image):

    if image is None:
        raise ValueError(
            "Could not read image."
        )

    if len(image.shape) == 3:

        return cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

    return image.copy()


# ==========================================================
# RESOLUTION NORMALIZATION
# ==========================================================

def resize_for_text(
    gray,
    scale
):

    if scale <= 1.0:
        return gray

    height, width = (
        gray.shape[:2]
    )

    new_width = max(
        1,
        int(
            round(
                width * scale
            )
        )
    )

    new_height = max(
        1,
        int(
            round(
                height * scale
            )
        )
    )

    # Lanczos for smaller enlargement.
    if scale <= 2.0:

        interpolation = (
            cv2.INTER_LANCZOS4
        )

    else:

        interpolation = (
            cv2.INTER_CUBIC
        )

    return cv2.resize(
        gray,
        (
            new_width,
            new_height
        ),
        interpolation=interpolation
    )


# ==========================================================
# DENOISING
# ==========================================================

def apply_denoising(
    gray
):

    return cv2.fastNlMeansDenoising(
        gray,
        None,
        h=7,
        templateWindowSize=7,
        searchWindowSize=21
    )


# ==========================================================
# ILLUMINATION CORRECTION
# ==========================================================

def correct_illumination(
    gray
):

    background = cv2.GaussianBlur(
        gray,
        (0, 0),
        21
    )

    background = np.maximum(
        background,
        1
    )

    normalized = cv2.divide(
        gray.astype(
            np.float32
        ),
        background.astype(
            np.float32
        )
    )

    normalized *= 255.0

    normalized = np.clip(
        normalized,
        0,
        255
    )

    return normalized.astype(
        np.uint8
    )


# ==========================================================
# CONTRAST ENHANCEMENT
# ==========================================================

def apply_clahe(
    gray
):

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    return clahe.apply(
        gray
    )


# ==========================================================
# LIGHT SHARPENING
# ==========================================================

def apply_light_sharpen(
    gray
):

    blurred = cv2.GaussianBlur(
        gray,
        (0, 0),
        1.0
    )

    sharpened = cv2.addWeighted(
        gray,
        1.15,
        blurred,
        -0.15,
        0
    )

    return np.clip(
        sharpened,
        0,
        255
    ).astype(
        np.uint8
    )


# ==========================================================
# DESKEW
# ==========================================================

def rotate_image(
    gray,
    angle
):

    if abs(angle) <= (
        SKEW_THRESHOLD
    ):
        return gray

    height, width = (
        gray.shape[:2]
    )

    center = (
        width / 2.0,
        height / 2.0
    )

    matrix = cv2.getRotationMatrix2D(
        center,
        angle,
        1.0
    )

    return cv2.warpAffine(
        gray,
        matrix,
        (
            width,
            height
        ),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )


# ==========================================================
# DECISION ENGINE
# ==========================================================

def choose_plan(
    quality_report
):

    metrics = (
        quality_report[
            "metrics"
        ]
    )

    problems = (
        quality_report[
            "problems"
        ]
    )

    glyph_height = (
        metrics[
            "glyph_height_est"
        ]
    )

    # ------------------------------------------------------
    # RESOLUTION
    # ------------------------------------------------------

    if glyph_height is None:

        scale = 1.0

        resolution_reason = (
            "Text size could not be estimated; "
            "blind enlargement avoided."
        )

    else:

        scale = float(
            np.clip(
                metrics[
                    "suggested_scale"
                ],
                1.0,
                MAX_UPSCALE
            )
        )

        if scale > 1.0:

            resolution_reason = (
                f"Estimated text height "
                f"{glyph_height:.1f}px; "
                f"upscaling by "
                f"{scale:.2f}x toward "
                f"{TARGET_GLYPH_HEIGHT:.0f}px."
            )

        else:

            resolution_reason = (
                f"Estimated text height "
                f"{glyph_height:.1f}px; "
                "resolution adequate."
            )

    # ------------------------------------------------------
    # OPERATION PLAN
    # ------------------------------------------------------

    plan = {

        "scale":
            scale,

        "denoise":
            "HIGH_NOISE"
            in problems,

        "illumination":
            metrics[
                "illumination"
            ][
                "tile_brightness_std"
            ]
            >
            ILLUMINATION_TILE_STD_THRESHOLD,

        "clahe":
            "LOW_CONTRAST"
            in problems,

        # IMPORTANT:
        # We deliberately do not sharpen merely because
        # the diagnostic score says POOR.
        "sharpen":
            False,

        "deskew":
            abs(
                metrics[
                    "skew_angle"
                ]
            )
            >
            SKEW_THRESHOLD,

        # Binarization is now only a candidate.
        "binarize_candidate":
            metrics[
                "bimodality"
            ]
            <
            BIMODALITY_THRESHOLD,

        "reasons": []
    }

    # ------------------------------------------------------
    # EXPLAINABILITY
    # ------------------------------------------------------

    plan[
        "reasons"
    ].append(
        resolution_reason
    )

    if plan["denoise"]:

        plan[
            "reasons"
        ].append(
            "High noise detected; "
            "conservative denoising enabled."
        )

    else:

        plan[
            "reasons"
        ].append(
            "Noise acceptable; "
            "denoising skipped."
        )

    if plan["illumination"]:

        plan[
            "reasons"
        ].append(
            "Uneven illumination detected; "
            "illumination correction enabled."
        )

    else:

        plan[
            "reasons"
        ].append(
            "Illumination sufficiently uniform; "
            "correction skipped."
        )

    if plan["clahe"]:

        plan[
            "reasons"
        ].append(
            "Low contrast detected; "
            "mild CLAHE enabled."
        )

    else:

        plan[
            "reasons"
        ].append(
            "Contrast acceptable; "
            "CLAHE skipped."
        )

    if plan["deskew"]:

        plan[
            "reasons"
        ].append(
            f"Skew of "
            f"{metrics['skew_angle']:.2f}° detected; "
            "deskew enabled."
        )

    else:

        plan[
            "reasons"
        ].append(
            "Skew acceptable; "
            "deskew skipped."
        )

    if plan[
        "binarize_candidate"
    ]:

        plan[
            "reasons"
        ].append(
            "Text/background separation is weak; "
            "binarization may be tested later."
        )

    else:

        plan[
            "reasons"
        ].append(
            "Text/background separation is adequate; "
            "grayscale preserved."
        )

    return plan


# ==========================================================
# MAIN IMAGE PREPROCESSOR
# ==========================================================

def preprocess_image(
    image,
    return_quality=False
):

    if image is None:
        raise ValueError(
            "Could not read image."
        )

    # ------------------------------------------------------
    # STEP 1 — QUALITY ANALYSIS
    # ------------------------------------------------------

    quality_report = (
        analyze_image(
            image
        )
    )

    metrics = (
        quality_report[
            "metrics"
        ]
    )

    print()
    print("=" * 64)
    print(
        "[CV] QUALITY ANALYSIS V1.5"
    )
    print("=" * 64)

    print(
        f"[CV] Quality Score    : "
        f"{quality_report['quality_score']:.2f}"
    )

    print(
        f"[CV] Quality Level    : "
        f"{quality_report['quality_level']}"
    )

    print(
        f"[CV] Problems         : "
        f"{quality_report['problems'] or 'NONE'}"
    )

    print(
        f"[CV] Resolution       : "
        f"{metrics['resolution']['width']} "
        f"x "
        f"{metrics['resolution']['height']}"
    )

    print(
        f"[CV] Text height      : "
        f"{metrics['glyph_height_est']}"
    )

    print(
        f"[CV] Suggested scale  : "
        f"{metrics['suggested_scale']:.2f}x"
    )

    print(
        f"[CV] Blur             : "
        f"{metrics['blur_raw']:.2f}"
    )

    print(
        f"[CV] Brightness       : "
        f"{metrics['brightness']:.2f}"
    )

    print(
        f"[CV] Contrast         : "
        f"{metrics['contrast']:.2f}"
    )

    print(
        f"[CV] Noise            : "
        f"{metrics['noise']:.2f}"
    )

    print(
        f"[CV] Skew             : "
        f"{metrics['skew_angle']:.2f}°"
    )

    print(
        f"[CV] Bimodality       : "
        f"{metrics['bimodality']:.3f}"
    )

    print(
        f"[CV] Illumination std : "
        f"{metrics['illumination']['tile_brightness_std']:.2f}"
    )

    print("=" * 64)

    # ------------------------------------------------------
    # STEP 2 — DECISION ENGINE
    # ------------------------------------------------------

    plan = choose_plan(
        quality_report
    )

    print(
        "[CV] OPERATION PLAN"
    )

    for reason in plan[
        "reasons"
    ]:

        print(
            f"[CV] - {reason}"
        )

    # ------------------------------------------------------
    # STEP 3 — GRAYSCALE
    # ------------------------------------------------------

    gray = to_gray(
        image
    )

    # ------------------------------------------------------
    # STEP 4 — RESOLUTION
    # ------------------------------------------------------

    if plan[
        "scale"
    ] > 1.0:

        old_height, old_width = (
            gray.shape[:2]
        )

        gray = resize_for_text(
            gray,
            plan[
                "scale"
            ]
        )

        print(
            f"[CV] Resize: "
            f"{old_width}x{old_height}"
            f" -> "
            f"{gray.shape[1]}x{gray.shape[0]}"
        )

    else:

        print(
            "[CV] Resize: skipped."
        )

    # ------------------------------------------------------
    # STEP 5 — DENOISING
    # ------------------------------------------------------

    if plan[
        "denoise"
    ]:

        print(
            "[CV] Denoising: enabled."
        )

        gray = apply_denoising(
            gray
        )

    else:

        print(
            "[CV] Denoising: skipped."
        )

    # ------------------------------------------------------
    # STEP 6 — ILLUMINATION
    # ------------------------------------------------------

    if plan[
        "illumination"
    ]:

        print(
            "[CV] Illumination correction: enabled."
        )

        gray = correct_illumination(
            gray
        )

    else:

        print(
            "[CV] Illumination correction: skipped."
        )

    # ------------------------------------------------------
    # STEP 7 — CONTRAST
    # ------------------------------------------------------

    if plan[
        "clahe"
    ]:

        print(
            "[CV] CLAHE: enabled."
        )

        gray = apply_clahe(
            gray
        )

    else:

        print(
            "[CV] CLAHE: skipped."
        )

    # ------------------------------------------------------
    # STEP 8 — RECHECK BLUR AFTER SCALING
    # ------------------------------------------------------

    normalized_blur = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    quality_report[
        "metrics"
    ][
        "blur_normalized"
    ] = normalized_blur

    # Conservative sharpening only when the normalized
    # image is genuinely very soft.
    if normalized_blur < 40.0:

        print(
            f"[CV] Post-scale blur = "
            f"{normalized_blur:.2f}; "
            "light sharpening enabled."
        )

        gray = apply_light_sharpen(
            gray
        )

        plan[
            "sharpen"
        ] = True

    else:

        print(
            f"[CV] Post-scale blur = "
            f"{normalized_blur:.2f}; "
            "sharpening skipped."
        )

    # ------------------------------------------------------
    # STEP 9 — DESKEW
    # ------------------------------------------------------

    if plan[
        "deskew"
    ]:

        angle = metrics[
            "skew_angle"
        ]

        print(
            f"[CV] Deskew: "
            f"{angle:.2f}°"
        )

        gray = rotate_image(
            gray,
            angle
        )

    else:

        print(
            "[CV] Deskew: skipped."
        )

    # ------------------------------------------------------
    # STEP 10 — PRESERVE GRAYSCALE
    # ------------------------------------------------------

    preserved_grayscale = (
        gray.copy()
    )

    # ------------------------------------------------------
    # STEP 11 — NO FORCED BINARIZATION
    # ------------------------------------------------------

    if plan[
        "binarize_candidate"
    ]:

        print(
            "[CV] Binarization: "
            "candidate only."
        )

        print(
            "[CV] Primary output remains grayscale."
        )

    else:

        print(
            "[CV] Binarization: skipped."
        )

    # ------------------------------------------------------
    # STEP 12 — FINAL REPORT
    # ------------------------------------------------------

    processed = gray

    quality_report[
        "processing_plan"
    ] = plan

    quality_report[
        "processing_result"
    ] = {

        "final_width":
            int(
                processed.shape[1]
            ),

        "final_height":
            int(
                processed.shape[0]
            ),

        "grayscale_preserved":
            True
    }

    print(
        f"[CV] Final image size: "
        f"{processed.shape[1]}x"
        f"{processed.shape[0]}"
    )

    print(
        "[CV] Intelligent preprocessing completed."
    )

    print("=" * 64)
    print()

    if return_quality:

        return (
            processed,
            preserved_grayscale,
            quality_report
        )

    return processed


# ==========================================================
# PDF PREPROCESSING
# ==========================================================

def preprocess_pdf(
    pdf_path,
    output_dir
):

    pdf_path = Path(
        pdf_path
    )

    output_dir = Path(
        output_dir
    )

    if not pdf_path.exists():

        raise FileNotFoundError(
            f"PDF does not exist: "
            f"{pdf_path}"
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    document = pymupdf.open(
        str(pdf_path)
    )

    output_files = []

    try:

        if len(document) == 0:

            raise ValueError(
                "PDF contains no pages."
            )

        for (
            page_number,
            page
        ) in enumerate(
            document
        ):

            print(
                f"\n[CV] Processing PDF page "
                f"{page_number + 1}/"
                f"{len(document)}"
            )

            # --------------------------------------------------
            # Render PDF at approximately 300 DPI.
            # --------------------------------------------------

            zoom = (
                300 / 72
            )

            matrix = pymupdf.Matrix(
                zoom,
                zoom
            )

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False
            )

            # --------------------------------------------------
            # Convert to NumPy.
            # --------------------------------------------------

            image = np.frombuffer(
                pixmap.samples,
                dtype=np.uint8
            )

            image = image.reshape(
                pixmap.height,
                pixmap.width,
                pixmap.n
            )

            # --------------------------------------------------
            # RGB/RGBA -> BGR.
            # --------------------------------------------------

            if pixmap.n == 4:

                image = cv2.cvtColor(
                    image,
                    cv2.COLOR_RGBA2BGR
                )

            elif pixmap.n == 3:

                image = cv2.cvtColor(
                    image,
                    cv2.COLOR_RGB2BGR
                )

            else:

                image = cv2.cvtColor(
                    image,
                    cv2.COLOR_GRAY2BGR
                )

            # --------------------------------------------------
            # CV preprocessing.
            # --------------------------------------------------

            processed = preprocess_image(
                image
            )

            # --------------------------------------------------
            # Save processed page.
            # --------------------------------------------------

            output_file = (
                output_dir
                /
                f"page_{page_number + 1:04d}.png"
            )

            success = cv2.imwrite(
                str(output_file),
                processed
            )

            if not success:

                raise RuntimeError(
                    f"Could not save processed page "
                    f"{page_number + 1}."
                )

            output_files.append(
                str(output_file)
            )

            print(
                f"[CV] Saved: "
                f"{output_file}"
            )

    finally:

        document.close()

    return output_files


# ==========================================================
# JPG / JPEG / PNG PREPROCESSING
# ==========================================================

def preprocess_image_file(
    image_path,
    output_dir
):

    image_path = Path(
        image_path
    )

    output_dir = Path(
        output_dir
    )

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image does not exist: "
            f"{image_path}"
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ------------------------------------------------------
    # Windows-safe image loading.
    # ------------------------------------------------------

    raw_data = np.fromfile(
        str(image_path),
        dtype=np.uint8
    )

    image = cv2.imdecode(
        raw_data,
        cv2.IMREAD_COLOR
    )

    if image is None:

        raise ValueError(
            "The uploaded image could not be decoded."
        )

    print(
        f"\n[CV] Processing image: "
        f"{image_path.name}"
    )

    # ------------------------------------------------------
    # Run CV pipeline.
    # ------------------------------------------------------

    processed = preprocess_image(
        image
    )

    # ------------------------------------------------------
    # Save processed image.
    # ------------------------------------------------------

    output_file = (
        output_dir
        /
        "page_0001.png"
    )

    success = cv2.imwrite(
        str(output_file),
        processed
    )

    if not success:

        raise RuntimeError(
            "Could not save processed image."
        )

    print(
        f"[CV] Saved: "
        f"{output_file}"
    )

    return [
        str(output_file)
    ]