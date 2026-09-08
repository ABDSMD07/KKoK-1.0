from pathlib import Path

import cv2
import numpy as np


# ==========================================================
# CONFIGURATION
# ==========================================================

# Target approximate character/glyph height for OCR.
# This is NOT a fixed image resolution.
TARGET_GLYPH_HEIGHT = 24.0

# Never artificially enlarge more than this.
MAX_UPSCALE = 4.0

# Quality thresholds.
LOW_CONTRAST_THRESHOLD = 35.0
HIGH_NOISE_THRESHOLD = 12.0

# Deskew threshold.
SKEW_THRESHOLD = 1.0

# Illumination threshold.
# This measures variation between document regions,
# NOT global brightness.
ILLUMINATION_TILE_STD_THRESHOLD = 12.0

# Text/background separation.
BIMODALITY_THRESHOLD = 0.35

# Diagnostic blur thresholds.
SEVERE_BLUR_THRESHOLD = 40.0
BLUR_THRESHOLD = 80.0


# ==========================================================
# BASIC HELPERS
# ==========================================================

def to_gray(image):
    """
    Convert image to grayscale.

    This function does NOT modify the original image.
    """

    if image is None:
        raise ValueError(
            "Cannot analyze an empty image."
        )

    if len(image.shape) == 3:
        return cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

    return image.copy()


# ==========================================================
# BLUR ANALYSIS
# ==========================================================

def calculate_blur(gray):
    """
    Variance of Laplacian.

    Higher value generally means stronger high-frequency
    edges. This is used only as a diagnostic signal.
    """

    return float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )


# ==========================================================
# NOISE ANALYSIS
# ==========================================================

def calculate_noise(gray):
    """
    Estimate noise using the difference between the image
    and a small median-filtered version.
    """

    median = cv2.medianBlur(
        gray,
        3
    )

    residual = cv2.absdiff(
        gray,
        median
    )

    return float(
        np.mean(residual)
    )


# ==========================================================
# TEXT / BACKGROUND SEPARATION
# ==========================================================

def calculate_bimodality(gray):
    """
    Estimate how strongly the image separates into
    foreground/background intensity groups.

    This is an analysis signal only.

    It does NOT mean:
        high score -> automatically threshold.

    It is used to decide whether binarization might be
    worth testing later.
    """

    if gray.size == 0:
        return 0.0

    histogram = cv2.calcHist(
        [gray],
        [0],
        None,
        [256],
        [0, 256]
    ).ravel()

    total = float(
        histogram.sum()
    )

    if total <= 0:
        return 0.0

    probabilities = (
        histogram / total
    )

    levels = np.arange(
        256,
        dtype=np.float64
    )

    global_mean = float(
        np.sum(
            levels * probabilities
        )
    )

    total_variance = float(
        np.sum(
            ((levels - global_mean) ** 2)
            * probabilities
        )
    )

    if total_variance <= 1e-9:
        return 0.0

    threshold, _ = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    threshold = int(threshold)

    weight_background = float(
        np.sum(
            probabilities[
                :threshold + 1
            ]
        )
    )

    weight_foreground = (
        1.0 -
        weight_background
    )

    if (
        weight_background <= 1e-9
        or
        weight_foreground <= 1e-9
    ):
        return 0.0

    mean_background = float(
        np.sum(
            levels[:threshold + 1]
            *
            probabilities[:threshold + 1]
        )
        /
        weight_background
    )

    mean_foreground = float(
        np.sum(
            levels[threshold + 1:]
            *
            probabilities[threshold + 1:]
        )
        /
        weight_foreground
    )

    between_class_variance = (
        weight_background
        *
        weight_foreground
        *
        (
            mean_background
            -
            mean_foreground
        ) ** 2
    )

    score = (
        between_class_variance
        /
        total_variance
    )

    return float(
        np.clip(
            score,
            0.0,
            1.0
        )
    )


# ==========================================================
# TEXT HEIGHT ESTIMATION
# ==========================================================

def estimate_glyph_height(gray):
    """
    Estimate median text component height.

    This is a heuristic.

    It is NOT trying to understand the text.

    Its purpose is simply to answer:

        "How many pixels tall is the text?"

    so that resolution scaling can be based on text size
    rather than arbitrary page dimensions.
    """

    height, width = gray.shape[:2]

    # ------------------------------------------------------
    # Analysis-only threshold
    # ------------------------------------------------------

    _, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV
        +
        cv2.THRESH_OTSU
    )

    # ------------------------------------------------------
    # Remove large horizontal table lines
    # ------------------------------------------------------

    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            max(
                15,
                width // 20
            ),
            1
        )
    )

    horizontal_lines = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        horizontal_kernel
    )

    # ------------------------------------------------------
    # Remove large vertical table lines
    # ------------------------------------------------------

    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            1,
            max(
                15,
                height // 20
            )
        )
    )

    vertical_lines = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        vertical_kernel
    )

    # ------------------------------------------------------
    # Remove detected ruling lines
    # ------------------------------------------------------

    line_mask = cv2.bitwise_or(
        horizontal_lines,
        vertical_lines
    )

    text_mask = cv2.subtract(
        binary,
        line_mask
    )

    # ------------------------------------------------------
    # Connected components
    # ------------------------------------------------------

    number_of_labels, _, stats, _ = (
        cv2.connectedComponentsWithStats(
            text_mask,
            connectivity=8
        )
    )

    heights = []

    min_height = max(
        2,
        int(
            round(
                height * 0.003
            )
        )
    )

    max_height = max(
        min_height + 1,
        int(
            round(
                height * 0.08
            )
        )
    )

    min_area = 3

    max_area = max(
        30,
        int(
            height
            *
            width
            *
            0.002
        )
    )

    for index in range(
        1,
        number_of_labels
    ):

        x, y, component_width, component_height, area = (
            stats[index]
        )

        # Ignore extremely small noise.
        if component_height < min_height:
            continue

        # Ignore huge page/table components.
        if component_height > max_height:
            continue

        if area < min_area:
            continue

        if area > max_area:
            continue

        # Ignore extremely wide components.
        if component_width > max(
            3,
            int(width * 0.08)
        ):
            continue

        aspect_ratio = (
            component_width
            /
            max(
                component_height,
                1
            )
        )

        if aspect_ratio > 8.0:
            continue

        fill_ratio = (
            area
            /
            float(
                max(
                    component_width
                    *
                    component_height,
                    1
                )
            )
        )

        if fill_ratio < 0.05:
            continue

        heights.append(
            component_height
        )

    if not heights:
        return None

    return float(
        np.median(
            heights
        )
    )


# ==========================================================
# TEXT-BASED SCALE
# ==========================================================

def estimate_scale(glyph_height):
    """
    Estimate enlargement factor from observed text size.
    """

    if (
        glyph_height is None
        or
        glyph_height <= 0
    ):
        return 1.0

    required_scale = (
        TARGET_GLYPH_HEIGHT
        /
        glyph_height
    )

    return float(
        np.clip(
            required_scale,
            1.0,
            MAX_UPSCALE
        )
    )


# ==========================================================
# ILLUMINATION ANALYSIS
# ==========================================================

def analyze_illumination(
    gray,
    grid=4
):
    """
    Analyze illumination using tiled brightness.

    We intentionally use the 90th percentile of each tile
    rather than the tile mean.

    Why?

    Because a tile containing lots of black text/table
    lines should not automatically look like a dark-light
    illumination problem.
    """

    values = []

    for row in np.array_split(
        gray,
        grid,
        axis=0
    ):

        for tile in np.array_split(
            row,
            grid,
            axis=1
        ):

            if tile.size == 0:
                continue

            values.append(
                float(
                    np.percentile(
                        tile,
                        90
                    )
                )
            )

    if not values:
        return {
            "tile_brightness": [],
            "tile_brightness_std": 0.0
        }

    return {
        "tile_brightness": values,
        "tile_brightness_std": float(
            np.std(values)
        )
    }


# ==========================================================
# SKEW DETECTION
# ==========================================================

def detect_skew(gray):
    """
    Detect approximate document skew.

    Long straight edges such as tables can influence this
    estimate, so this remains a conservative signal.
    """

    edges = cv2.Canny(
        gray,
        50,
        150,
        apertureSize=3
    )

    height, width = gray.shape[:2]

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=max(
            30,
            min(
                width,
                height
            ) // 8
        ),
        minLineLength=max(
            40,
            width // 12
        ),
        maxLineGap=20
    )

    if lines is None:
        return 0.0

    angles = []

    for line in lines:

        values = np.asarray(
            line
        ).reshape(-1)

        if len(values) != 4:
            continue

        x1, y1, x2, y2 = values

        angle = float(
            np.degrees(
                np.arctan2(
                    y2 - y1,
                    x2 - x1
                )
            )
        )

        # Only consider near-horizontal lines.
        if (
            -20.0
            <= angle
            <= 20.0
        ):
            angles.append(
                angle
            )

    if not angles:
        return 0.0

    return float(
        np.median(
            angles
        )
    )


# ==========================================================
# DIAGNOSTIC QUALITY SCORE
# ==========================================================

def calculate_quality_score(
    metrics
):
    """
    Diagnostic 0-100 score.

    IMPORTANT:

    This score is NOT used as the main processing decision.

    Individual evidence signals control preprocessing.
    """

    score = 100.0

    glyph_height = (
        metrics[
            "glyph_height_est"
        ]
    )

    if glyph_height is not None:

        if glyph_height < 8:
            score -= 30

        elif glyph_height < 16:
            score -= 15

    blur = metrics[
        "blur_raw"
    ]

    if blur < SEVERE_BLUR_THRESHOLD:
        score -= 25

    elif blur < BLUR_THRESHOLD:
        score -= 10

    contrast = metrics[
        "contrast"
    ]

    if contrast < LOW_CONTRAST_THRESHOLD:
        score -= 20

    noise = metrics[
        "noise"
    ]

    if noise > HIGH_NOISE_THRESHOLD:
        score -= 15

    skew = abs(
        metrics[
            "skew_angle"
        ]
    )

    if skew > 5:
        score -= 10

    elif skew > SKEW_THRESHOLD:
        score -= 5

    illumination = metrics[
        "illumination"
    ][
        "tile_brightness_std"
    ]

    if illumination > (
        ILLUMINATION_TILE_STD_THRESHOLD
    ):
        score -= 10

    return float(
        np.clip(
            score,
            0.0,
            100.0
        )
    )


# ==========================================================
# QUALITY CLASSIFICATION
# ==========================================================

def classify_quality(
    score,
    glyph_height
):
    """
    Diagnostic quality classification.
    """

    if (
        glyph_height is not None
        and
        glyph_height < 5
    ):
        return "IRRECOVERABLE_RISK"

    if score >= 85:
        return "GOOD"

    if score >= 65:
        return "FAIR"

    if score >= 40:
        return "POOR"

    return "CRITICAL"


# ==========================================================
# COMPLETE QUALITY ANALYSIS
# ==========================================================

def analyze_image(
    image
):
    """
    Analyze a document image before preprocessing.

    Returns structured diagnostic information.
    """

    gray = to_gray(
        image
    )

    height, width = (
        gray.shape[:2]
    )

    illumination = (
        analyze_illumination(
            gray
        )
    )

    glyph_height = (
        estimate_glyph_height(
            gray
        )
    )

    suggested_scale = (
        estimate_scale(
            glyph_height
        )
    )

    metrics = {

        "resolution": {
            "width": int(width),
            "height": int(height)
        },

        "glyph_height_est":
            glyph_height,

        "suggested_scale":
            suggested_scale,

        "blur_raw":
            calculate_blur(gray),

        "brightness":
            float(
                np.mean(gray)
            ),

        "contrast":
            float(
                np.std(gray)
            ),

        "noise":
            calculate_noise(gray),

        "skew_angle":
            detect_skew(gray),

        "bimodality":
            calculate_bimodality(gray),

        "illumination":
            illumination
    }

    problems = []

    # ------------------------------------------------------
    # Text scale
    # ------------------------------------------------------

    if (
        glyph_height is not None
        and
        glyph_height
        <
        TARGET_GLYPH_HEIGHT
    ):
        problems.append(
            "LOW_TEXT_SCALE"
        )

    # ------------------------------------------------------
    # Contrast
    # ------------------------------------------------------

    if (
        metrics["contrast"]
        <
        LOW_CONTRAST_THRESHOLD
    ):
        problems.append(
            "LOW_CONTRAST"
        )

    # ------------------------------------------------------
    # Noise
    # ------------------------------------------------------

    if (
        metrics["noise"]
        >
        HIGH_NOISE_THRESHOLD
    ):
        problems.append(
            "HIGH_NOISE"
        )

    # ------------------------------------------------------
    # Illumination
    # ------------------------------------------------------

    if (
        metrics["illumination"]
        ["tile_brightness_std"]
        >
        ILLUMINATION_TILE_STD_THRESHOLD
    ):
        problems.append(
            "UNEVEN_ILLUMINATION"
        )

    # ------------------------------------------------------
    # Skew
    # ------------------------------------------------------

    if (
        abs(
            metrics["skew_angle"]
        )
        >
        SKEW_THRESHOLD
    ):
        problems.append(
            "SKEW"
        )

    # ------------------------------------------------------
    # Text/background separation
    # ------------------------------------------------------

    if (
        metrics["bimodality"]
        <
        BIMODALITY_THRESHOLD
    ):
        problems.append(
            "LOW_TEXT_BACKGROUND_SEPARATION"
        )

    # ------------------------------------------------------
    # Final diagnostic score
    # ------------------------------------------------------

    quality_score = (
        calculate_quality_score(
            metrics
        )
    )

    quality_level = (
        classify_quality(
            quality_score,
            glyph_height
        )
    )

    return {

        "quality_score":
            quality_score,

        "quality_level":
            quality_level,

        "problems":
            problems,

        "metrics":
            metrics
    }