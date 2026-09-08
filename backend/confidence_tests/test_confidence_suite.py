"""
===========================================================
PS 26018 - Confidence V1.0 Controlled Test Suite

Tests Confidence policy independently of the real OCR pipeline.
===========================================================
"""

from confidence.confidence_scorer import (
    calculate_confidence,
    calculate_field_confidence,
)


# ============================================================
# HELPERS
# ============================================================

def make_field(
    value="54/2",
    evidence_type="layout_relationship",
    validation_status="valid",
    normalization_status="normalized",
    source_text="Survey Number | 54/2",
    source_line_ids=None,
    source_page=1,
    matched_label="survey number",
):

    if source_line_ids is None:
        source_line_ids = [11]

    return {
        "field": "survey_number",
        "value": value,
        "raw_value": value,
        "normalized_value": value,

        "status": (
            "extracted"
            if value is not None
            else "missing"
        ),

        "confidence": None,

        "section": "LAND IDENTIFICATION",

        "source_text": source_text,
        "source_line_ids": source_line_ids,
        "source_page": source_page,

        "evidence_type": evidence_type,
        "matched_label": matched_label,

        "structured_value": None,

        "normalization_status": (
            normalization_status
        ),

        "validation_status": (
            validation_status
        ),

        "validation_issues": [],
    }


def make_validation_result(
    field,
):

    return {
        "validation_version": "1.0",
        "source_normalization_version": "1.0",
        "source_extraction_version": "1.1",
        "document_id": "TEST-DOCUMENT",

        "fields": {
            "survey_number": field,
        },
    }


def assert_range(
    value,
    minimum,
    maximum,
    message,
):

    assert minimum <= value <= maximum, (
        f"{message}: "
        f"expected {minimum}-{maximum}, "
        f"got {value}"
    )


def print_result(
    test_name,
    passed,
    details="",
):

    print(
        f"{test_name:45} "
        f"{'PASS' if passed else 'FAIL'}"
        f"{' - ' + details if details else ''}"
    )


# ============================================================
# TEST 1
# STRONG EVIDENCE + VALID
# ============================================================

field = make_field()

result = calculate_field_confidence(
    "survey_number",
    field,
)

assert result[
    "confidence_level"
] == "high"

assert result[
    "confidence_review"
] == "not_required"

assert_range(
    result["confidence_score"],
    85.0,
    100.0,
    "Strong evidence score",
)

print_result(
    "Test 1 - Strong evidence + valid",
    True,
    f"score={result['confidence_score']}",
)


# ============================================================
# TEST 2
# WEAKER EVIDENCE
# ============================================================

field = make_field(
    evidence_type="ocr_fallback",
)

result = calculate_field_confidence(
    "survey_number",
    field,
)

strong_result = (
    calculate_field_confidence(
        "survey_number",
        make_field(),
    )
)

assert (
    result["confidence_score"]
    < strong_result["confidence_score"]
)

assert (
    result["confidence_review"]
    == "required"
)

print_result(
    "Test 2 - Weak evidence",
    True,
    f"score={result['confidence_score']}",
)


# ============================================================
# TEST 3
# VALIDATION WARNING
# ============================================================

field = make_field(
    validation_status="warning",
)

result = calculate_field_confidence(
    "survey_number",
    field,
)

assert (
    result["confidence_review"]
    == "required"
)

assert (
    result["confidence_score"]
    <= 64.0
)

print_result(
    "Test 3 - Validation warning",
    True,
    f"score={result['confidence_score']}",
)


# ============================================================
# TEST 4
# INVALID FIELD
# ============================================================

field = make_field(
    validation_status="invalid",
)

result = calculate_field_confidence(
    "survey_number",
    field,
)

assert (
    result["confidence_review"]
    == "required"
)

assert (
    result["confidence_score"]
    <= 39.0
)

assert (
    result["confidence_level"]
    == "critical"
)

print_result(
    "Test 4 - Invalid field",
    True,
    f"score={result['confidence_score']}",
)


# ============================================================
# TEST 5
# MISSING FIELD
# ============================================================

field = make_field(
    value=None,
    validation_status="missing",
    normalization_status="missing",
    source_text=None,
    source_line_ids=[],
    source_page=None,
    matched_label=None,
)

result = calculate_field_confidence(
    "survey_number",
    field,
)

assert (
    result["confidence_score"]
    == 0.0
)

assert (
    result["confidence_level"]
    == "critical"
)

assert (
    result["confidence_review"]
    == "required"
)

print_result(
    "Test 5 - Missing field",
    True,
    "score=0",
)


# ============================================================
# BASELINE RECORD
# ============================================================

baseline_validation = (
    make_validation_result(
        make_field()
    )
)

baseline_duplicate = {
    "duplicate_detection_version": "1.0",
    "document_id": "TEST-DOCUMENT",
    "status": "not_duplicate",
}

baseline = calculate_confidence(
    baseline_validation,
    baseline_duplicate,
)

baseline_score = baseline[
    "summary"
][
    "record_confidence_score"
]


# ============================================================
# TEST 6
# STRONG DUPLICATE
# ============================================================

strong_duplicate = {
    "duplicate_detection_version": "1.0",
    "document_id": "TEST-DOCUMENT",
    "status": "strong_duplicate",
}

result = calculate_confidence(
    baseline_validation,
    strong_duplicate,
)

summary = result["summary"]

# Critical policy:
# duplicate status does NOT reduce extraction/data confidence.
assert (
    summary["record_confidence_score"]
    == baseline_score
)

assert (
    summary["duplicate_classification"]
    == "strong_duplicate"
)

assert (
    summary["duplicate_risk_score"]
    == 100.0
)

assert (
    summary["review_required"]
    == "required"
)

print_result(
    "Test 6 - Strong duplicate",
    True,
    (
        f"confidence={summary['record_confidence_score']}, "
        f"risk={summary['duplicate_risk_score']}"
    ),
)


# ============================================================
# TEST 7
# POSSIBLE DUPLICATE
# ============================================================

possible_duplicate = {
    "duplicate_detection_version": "1.0",
    "document_id": "TEST-DOCUMENT",
    "status": "possible_duplicate",
}

result = calculate_confidence(
    baseline_validation,
    possible_duplicate,
)

summary = result["summary"]

assert (
    summary["record_confidence_score"]
    == baseline_score
)

assert (
    summary["duplicate_classification"]
    == "possible_duplicate"
)

assert (
    summary["duplicate_risk_score"]
    == 70.0
)

assert (
    summary["review_required"]
    == "required"
)

print_result(
    "Test 7 - Possible duplicate",
    True,
    (
        f"confidence={summary['record_confidence_score']}, "
        f"risk={summary['duplicate_risk_score']}"
    ),
)


# ============================================================
# TEST 8
# NOT DUPLICATE
# ============================================================

not_duplicate = {
    "duplicate_detection_version": "1.0",
    "document_id": "TEST-DOCUMENT",
    "status": "not_duplicate",
}

result = calculate_confidence(
    baseline_validation,
    not_duplicate,
)

summary = result["summary"]

assert (
    summary["duplicate_classification"]
    == "not_duplicate"
)

assert (
    summary["duplicate_risk_score"]
    == 0.0
)

assert (
    summary["record_confidence_score"]
    == baseline_score
)

print_result(
    "Test 8 - Not duplicate",
    True,
    (
        f"confidence={summary['record_confidence_score']}, "
        "risk=0"
    ),
)


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 60)
print("ALL CONFIDENCE V1.0 CONTROLLED TESTS PASSED")
print("=" * 60)