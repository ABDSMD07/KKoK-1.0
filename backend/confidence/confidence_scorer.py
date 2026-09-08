"""
===========================================================
PS 26018 - Land Record Intelligence System
Confidence Scoring V1.0

Purpose:
    Calculate transparent field-level and record-level
    confidence from evidence produced by upstream modules.

Confidence is NOT probability.

Confidence DOES:
    - calculate field confidence
    - calculate record confidence
    - evaluate extraction evidence
    - consider validation status
    - consider normalization status
    - evaluate provenance completeness
    - identify fields requiring review
    - propagate duplicate risk

Confidence DOES NOT:
    - perform OCR / HTR
    - extract fields
    - normalize values
    - validate values
    - correct values
    - invent values
    - perform duplicate matching
    - access databases

Important:
    Duplicate risk is separate from data confidence.

    Duplicate status can require human review but NEVER
    mathematically reduces record confidence.
===========================================================
"""

import copy
from typing import Any, Dict, List, Optional, Tuple


CONFIDENCE_VERSION = "1.0"


# ============================================================
# VALIDATION STATUSES
# ============================================================

STATUS_VALID = "valid"
STATUS_WARNING = "warning"
STATUS_INVALID = "invalid"
STATUS_MISSING = "missing"
STATUS_NOT_CHECKED = "not_checked"


# ============================================================
# CONFIDENCE LEVELS
# ============================================================

LEVEL_HIGH = "high"
LEVEL_MEDIUM = "medium"
LEVEL_LOW = "low"
LEVEL_CRITICAL = "critical"


# ============================================================
# REVIEW STATUSES
# ============================================================

REVIEW_REQUIRED = "required"
REVIEW_NOT_REQUIRED = "not_required"


# ============================================================
# EXTRACTION EVIDENCE
# ============================================================

EVIDENCE_SCORES = {

    # Strongest structured evidence
    "layout_relationship": 100.0,

    # Structured Layout line
    "layout_same_line": 90.0,

    # Nearby Layout evidence
    "layout_below_label": 82.0,

    # Structured table evidence
    "layout_table": 90.0,

    # Fallback sources
    "composer_fallback": 72.0,
    "ocr_fallback": 62.0,
}


UNKNOWN_EVIDENCE_SCORE = 40.0


# ============================================================
# FALLBACK EVIDENCE TYPES
# ============================================================

# These evidence types require human review even when other
# confidence components produce a relatively high score.

FALLBACK_EVIDENCE_TYPES = {
    "composer_fallback",
    "ocr_fallback",
}


# ============================================================
# VALIDATION SCORES
# ============================================================

VALIDATION_SCORES = {
    STATUS_VALID: 100.0,
    STATUS_WARNING: 55.0,
    STATUS_INVALID: 15.0,
    STATUS_MISSING: 0.0,
    STATUS_NOT_CHECKED: 40.0,
}


# ============================================================
# NORMALIZATION SCORES
# ============================================================

NORMALIZATION_SCORES = {
    "normalized": 100.0,
    "missing": 0.0,
}


UNKNOWN_NORMALIZATION_SCORE = 50.0


# ============================================================
# FIELD COMPONENT WEIGHTS
# ============================================================

WEIGHT_EVIDENCE = 0.30
WEIGHT_VALIDATION = 0.40
WEIGHT_NORMALIZATION = 0.15
WEIGHT_SOURCE_COMPLETENESS = 0.15


# ============================================================
# RECORD WEIGHTS
# ============================================================

WEIGHT_RECORD_FIELDS = 0.75
WEIGHT_RECORD_COMPLETENESS = 0.25


# ============================================================
# THRESHOLDS
# ============================================================

HIGH_THRESHOLD = 85.0
MEDIUM_THRESHOLD = 65.0
LOW_THRESHOLD = 40.0


# ============================================================
# EVIDENCE SCORE
# ============================================================

def evidence_score(
    field: Dict[str, Any],
) -> float:

    evidence_type = field.get(
        "evidence_type"
    )

    if not evidence_type:
        return 0.0

    return EVIDENCE_SCORES.get(
        evidence_type,
        UNKNOWN_EVIDENCE_SCORE,
    )


# ============================================================
# VALIDATION SCORE
# ============================================================

def validation_score(
    field: Dict[str, Any],
) -> float:

    status = field.get(
        "validation_status",
        STATUS_NOT_CHECKED,
    )

    return VALIDATION_SCORES.get(
        status,
        VALIDATION_SCORES[
            STATUS_NOT_CHECKED
        ],
    )


# ============================================================
# NORMALIZATION SCORE
# ============================================================

def normalization_score(
    field: Dict[str, Any],
) -> float:

    status = field.get(
        "normalization_status"
    )

    return NORMALIZATION_SCORES.get(
        status,
        UNKNOWN_NORMALIZATION_SCORE,
    )


# ============================================================
# SOURCE COMPLETENESS
# ============================================================

def source_completeness_score(
    field: Dict[str, Any],
) -> float:
    """
    Evaluate provenance completeness.

    Checks:
        source_text
        source_line_ids
        source_page
        matched_label
    """

    available = 0
    total = 4

    # --------------------------------------------------------
    # SOURCE TEXT
    # --------------------------------------------------------

    source_text = field.get(
        "source_text"
    )

    if (
        isinstance(source_text, str)
        and source_text.strip()
    ):
        available += 1

    # --------------------------------------------------------
    # LINE IDS
    # --------------------------------------------------------

    source_line_ids = field.get(
        "source_line_ids"
    )

    if (
        isinstance(source_line_ids, list)
        and len(source_line_ids) > 0
    ):
        available += 1

    # --------------------------------------------------------
    # PAGE
    # --------------------------------------------------------

    if field.get(
        "source_page"
    ) is not None:
        available += 1

    # --------------------------------------------------------
    # MATCHED LABEL
    # --------------------------------------------------------

    matched_label = field.get(
        "matched_label"
    )

    if (
        isinstance(matched_label, str)
        and matched_label.strip()
    ):
        available += 1

    return round(
        (
            available
            / total
        ) * 100.0,
        2,
    )


# ============================================================
# CONFIDENCE LEVEL
# ============================================================

def confidence_level(
    score: float,
) -> str:

    if score >= HIGH_THRESHOLD:
        return LEVEL_HIGH

    if score >= MEDIUM_THRESHOLD:
        return LEVEL_MEDIUM

    if score >= LOW_THRESHOLD:
        return LEVEL_LOW

    return LEVEL_CRITICAL


# ============================================================
# FIELD REVIEW DECISION
# ============================================================

def determine_field_review(
    field: Dict[str, Any],
    score: float,
) -> Tuple[str, List[str]]:
    """
    Decide whether a field requires human review.

    IMPORTANT:

    Review decision != numerical confidence.

    A field can have a relatively high confidence score but
    still require review because it came from fallback OCR or
    Composer evidence.
    """

    reasons: List[str] = []

    validation_status = field.get(
        "validation_status",
        STATUS_NOT_CHECKED,
    )

    evidence_type = field.get(
        "evidence_type"
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    if validation_status == STATUS_INVALID:

        reasons.append(
            "Validation marked the field invalid."
        )

    elif validation_status == STATUS_WARNING:

        reasons.append(
            "Validation produced warning(s)."
        )

    elif validation_status == STATUS_NOT_CHECKED:

        reasons.append(
            "Field was not fully validated."
        )

    elif validation_status == STATUS_MISSING:

        reasons.append(
            "Field is missing."
        )

    # ========================================================
    # FALLBACK EXTRACTION
    # ========================================================

    if evidence_type == "composer_fallback":

        reasons.append(
            "Field was extracted from Composer fallback evidence."
        )

    elif evidence_type == "ocr_fallback":

        reasons.append(
            "Field was extracted directly from OCR fallback evidence."
        )

    # ========================================================
    # UNKNOWN EVIDENCE
    # ========================================================

    if not evidence_type:

        reasons.append(
            "Extraction evidence type is unavailable."
        )

    elif evidence_type not in EVIDENCE_SCORES:

        reasons.append(
            "Extraction evidence type is unknown."
        )

    # ========================================================
    # SCORE THRESHOLD
    # ========================================================

    if score < HIGH_THRESHOLD:

        reasons.append(
            "Confidence is below the automatic acceptance threshold."
        )

    # ========================================================
    # SOURCE TEXT
    # ========================================================

    source_text = field.get(
        "source_text"
    )

    if (
        not isinstance(source_text, str)
        or not source_text.strip()
    ):

        reasons.append(
            "Source evidence text is unavailable."
        )

    # ========================================================
    # RESULT
    # ========================================================

    if reasons:

        return (
            REVIEW_REQUIRED,
            reasons,
        )

    return (
        REVIEW_NOT_REQUIRED,
        [
            "Field has sufficient supporting evidence."
        ],
    )


# ============================================================
# FIELD CONFIDENCE
# ============================================================

def calculate_field_confidence(
    field_name: str,
    field: Dict[str, Any],
) -> Dict[str, Any]:

    result = copy.deepcopy(
        field
    )

    normalized_value = field.get(
        "normalized_value"
    )

    validation_status = field.get(
        "validation_status",
        STATUS_NOT_CHECKED,
    )

    # ========================================================
    # MISSING FIELD
    # ========================================================

    if (
        normalized_value is None
        or validation_status == STATUS_MISSING
    ):

        result[
            "confidence_score"
        ] = 0.0

        result[
            "confidence_level"
        ] = LEVEL_CRITICAL

        result[
            "confidence_review"
        ] = REVIEW_REQUIRED

        result[
            "confidence_components"
        ] = {
            "evidence_score": 0.0,
            "validation_score": 0.0,
            "normalization_score": 0.0,
            "source_completeness_score": 0.0,
        }

        result[
            "confidence_reason"
        ] = (
            "Field has no normalized value."
        )

        return result

    # ========================================================
    # COMPONENT SCORES
    # ========================================================

    evidence = evidence_score(
        field
    )

    validation = validation_score(
        field
    )

    normalization = normalization_score(
        field
    )

    source = source_completeness_score(
        field
    )

    # ========================================================
    # RAW WEIGHTED SCORE
    # ========================================================

    score = (
        evidence
        * WEIGHT_EVIDENCE

        + validation
        * WEIGHT_VALIDATION

        + normalization
        * WEIGHT_NORMALIZATION

        + source
        * WEIGHT_SOURCE_COMPLETENESS
    )

    # ========================================================
    # VALIDATION CAPS
    # ========================================================

    # Invalid fields can never appear medium/high confidence.

    if validation_status == STATUS_INVALID:

        score = min(
            score,
            39.0,
        )

    # Warning fields cannot automatically become high-confidence.

    elif validation_status == STATUS_WARNING:

        score = min(
            score,
            64.0,
        )

    # ========================================================
    # CLAMP
    # ========================================================

    score = round(
        max(
            0.0,
            min(
                100.0,
                score,
            ),
        ),
        2,
    )

    # ========================================================
    # LEVEL
    # ========================================================

    level = confidence_level(
        score
    )

    # ========================================================
    # REVIEW
    # ========================================================

    review_status, reasons = (
        determine_field_review(
            field,
            score,
        )
    )

    # ========================================================
    # RESULT
    # ========================================================

    result[
        "confidence_score"
    ] = score

    result[
        "confidence_level"
    ] = level

    result[
        "confidence_review"
    ] = review_status

    result[
        "confidence_components"
    ] = {

        "evidence_score": round(
            evidence,
            2,
        ),

        "validation_score": round(
            validation,
            2,
        ),

        "normalization_score": round(
            normalization,
            2,
        ),

        "source_completeness_score": round(
            source,
            2,
        ),
    }

    result[
        "confidence_reason"
    ] = "; ".join(
        reasons
    )

    return result


# ============================================================
# DUPLICATE CLASSIFICATION
# ============================================================

def extract_duplicate_classification(
    duplicate_result: Optional[
        Dict[str, Any]
    ],
) -> Optional[str]:

    if not isinstance(
        duplicate_result,
        dict,
    ):
        return None

    classification = (
        duplicate_result.get(
            "status"
        )
    )

    if isinstance(
        classification,
        str,
    ):
        return classification

    return None


# ============================================================
# DUPLICATE RISK
# ============================================================

def duplicate_risk_score(
    duplicate_classification: Optional[str],
) -> float:
    """
    Duplicate workflow risk.

    This NEVER reduces data confidence.
    """

    risk_scores = {

        "strong_duplicate": 100.0,

        "possible_duplicate": 70.0,

        "insufficient_evidence": 30.0,

        "not_duplicate": 0.0,
    }

    if duplicate_classification is None:

        return 0.0

    return risk_scores.get(
        duplicate_classification,
        0.0,
    )


# ============================================================
# RECORD CONFIDENCE
# ============================================================

def calculate_record_confidence(
    field_results: Dict[
        str,
        Dict[str, Any]
    ],
    duplicate_result: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    scores: List[float] = []

    present_fields = 0
    missing_fields = 0

    review_fields: List[str] = []

    # ========================================================
    # FIELD AGGREGATION
    # ========================================================

    for field_name, field in (
        field_results.items()
    ):

        score = field.get(
            "confidence_score"
        )

        if score is not None:

            scores.append(
                float(score)
            )

        normalized_value = field.get(
            "normalized_value"
        )

        if normalized_value is None:

            missing_fields += 1

        else:

            present_fields += 1

        if (
            field.get(
                "confidence_review"
            )
            == REVIEW_REQUIRED
        ):

            review_fields.append(
                field_name
            )

    total_fields = len(
        field_results
    )

    # ========================================================
    # MEAN FIELD CONFIDENCE
    # ========================================================

    if scores:

        mean_confidence = (
            sum(scores)
            / len(scores)
        )

    else:

        mean_confidence = 0.0

    # ========================================================
    # COMPLETENESS
    # ========================================================

    if total_fields > 0:

        completeness = (
            present_fields
            / total_fields
        ) * 100.0

    else:

        completeness = 0.0

    # ========================================================
    # DATA CONFIDENCE
    # ========================================================

    # IMPORTANT:
    #
    # Duplicate risk is NOT included in this calculation.

    record_score = (
        mean_confidence
        * WEIGHT_RECORD_FIELDS

        + completeness
        * WEIGHT_RECORD_COMPLETENESS
    )

    record_score = round(
        max(
            0.0,
            min(
                100.0,
                record_score,
            ),
        ),
        2,
    )

    # ========================================================
    # DUPLICATE INFORMATION
    # ========================================================

    duplicate_classification = (
        extract_duplicate_classification(
            duplicate_result
        )
    )

    duplicate_risk = (
        duplicate_risk_score(
            duplicate_classification
        )
    )

    # ========================================================
    # RECORD REVIEW
    # ========================================================

    review_reasons: List[str] = []

    if review_fields:

        review_reasons.append(
            (
                f"{len(review_fields)} field(s) "
                "require review."
            )
        )

    if (
        duplicate_classification
        == "strong_duplicate"
    ):

        review_reasons.append(
            "Duplicate Detection reported a strong duplicate."
        )

    elif (
        duplicate_classification
        == "possible_duplicate"
    ):

        review_reasons.append(
            "Duplicate Detection reported a possible duplicate."
        )

    if record_score < HIGH_THRESHOLD:

        review_reasons.append(
            "Record confidence is below the automatic acceptance threshold."
        )

    review_required = bool(
        review_reasons
    )

    # ========================================================
    # RESULT
    # ========================================================

    return {

        "record_confidence_score": (
            record_score
        ),

        "record_confidence_level": (
            confidence_level(
                record_score
            )
        ),

        "field_count": (
            total_fields
        ),

        "present_field_count": (
            present_fields
        ),

        "missing_field_count": (
            missing_fields
        ),

        "completeness_score": round(
            completeness,
            2,
        ),

        "mean_field_confidence": round(
            mean_confidence,
            2,
        ),

        "duplicate_classification": (
            duplicate_classification
        ),

        "duplicate_risk_score": (
            duplicate_risk
        ),

        # Compatibility only.
        # It is NEVER subtracted.
        "duplicate_penalty": 0.0,

        "review_required": (
            REVIEW_REQUIRED
            if review_required
            else REVIEW_NOT_REQUIRED
        ),

        "review_reasons": (
            review_reasons
        ),

        "fields_requiring_review": (
            review_fields
        ),
    }


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def calculate_confidence(
    validation_result: Dict[str, Any],
    duplicate_result: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if not isinstance(
        validation_result,
        dict,
    ):

        raise TypeError(
            "validation_result must be a dictionary"
        )

    source_fields = (
        validation_result.get(
            "fields"
        )
    )

    if not isinstance(
        source_fields,
        dict,
    ):

        raise ValueError(
            "validation_result['fields'] must be a dictionary"
        )

    # ========================================================
    # FIELD CONFIDENCE
    # ========================================================

    confidence_fields = {}

    for field_name, field in (
        source_fields.items()
    ):

        if not isinstance(
            field,
            dict,
        ):
            continue

        confidence_fields[
            field_name
        ] = (
            calculate_field_confidence(
                field_name,
                field,
            )
        )

    # ========================================================
    # RECORD CONFIDENCE
    # ========================================================

    record_confidence = (
        calculate_record_confidence(
            confidence_fields,
            duplicate_result,
        )
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    return {

        "confidence_version": (
            CONFIDENCE_VERSION
        ),

        "source_validation_version": (
            validation_result.get(
                "validation_version"
            )
        ),

        "source_normalization_version": (
            validation_result.get(
                "source_normalization_version"
            )
        ),

        "source_extraction_version": (
            validation_result.get(
                "source_extraction_version"
            )
        ),

        "document_id": (
            validation_result.get(
                "document_id"
            )
        ),

        "summary": (
            record_confidence
        ),

        "fields": (
            confidence_fields
        ),

        "duplicate_information": {

            "classification": (
                record_confidence[
                    "duplicate_classification"
                ]
            ),

            "risk_score": (
                record_confidence[
                    "duplicate_risk_score"
                ]
            ),

            "penalty": 0.0,
        },
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "Confidence V1.0 module loaded successfully."
    )