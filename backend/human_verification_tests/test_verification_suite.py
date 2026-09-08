"""
===========================================================
Human Verification V1.0 Controlled Test Suite
===========================================================
"""

from human_verification.verification_engine import (
    create_verification,
    apply_field_decision,
    apply_duplicate_decision,
    finalize_verification,
    get_verified_values,
    can_finalize,
)


# ============================================================
# TEST DATA
# ============================================================

def make_field(
    value,
    confidence_score,
    confidence_review,
    validation_status,
):

    return {
        "field": "test",

        "value": value,
        "raw_value": value,
        "normalized_value": value,

        "validation_status": (
            validation_status
        ),

        "validation_issues": [],

        "normalization_status": (
            "normalized"
            if value is not None
            else "missing"
        ),

        "confidence_score": (
            confidence_score
        ),

        "confidence_level": (
            "high"
            if confidence_score >= 85
            else "critical"
        ),

        "confidence_review": (
            confidence_review
        ),

        "confidence_reason": (
            "Controlled test"
        ),

        "source_text": (
            f"Source: {value}"
            if value is not None
            else None
        ),

        "source_line_ids": (
            [1]
            if value is not None
            else []
        ),

        "source_page": (
            1
            if value is not None
            else None
        ),

        "evidence_type": (
            "layout_relationship"
            if value is not None
            else None
        ),

        "matched_label": (
            "test"
            if value is not None
            else None
        ),
    }


confidence_result = {
    "confidence_version": "1.0",
    "source_validation_version": "1.0",
    "source_normalization_version": "1.0",
    "source_extraction_version": "1.1",
    "document_id": "TEST-DOC",

    "fields": {
        "survey_number": make_field(
            "54/2",
            100.0,
            "not_required",
            "valid",
        ),

        "district": make_field(
            "eee",
            64.0,
            "required",
            "warning",
        ),

        "owner_name": make_field(
            None,
            0.0,
            "required",
            "missing",
        ),
    },

    "duplicate_information": {
        "classification": (
            "possible_duplicate"
        ),
        "risk_score": 70.0,
    },
}


duplicate_result = {
    "duplicate_detection_version": "1.0",
    "document_id": "TEST-DOC",
    "status": "possible_duplicate",

    "best_match": {
        "document_id": "EXISTING-DOC"
    },

    "matched_identifiers": [
        "survey_number"
    ],

    "conflicting_identifiers": [],

    "match_reasons": [
        "Controlled duplicate test"
    ],
}


# ============================================================
# TEST 1 - CREATE QUEUE
# ============================================================

verification = create_verification(
    confidence_result,
    duplicate_result=duplicate_result,
)

assert (
    "district"
    in verification["review_queue"]
)

assert (
    "owner_name"
    in verification["review_queue"]
)

assert (
    "survey_number"
    not in verification["review_queue"]
)

assert (
    verification[
        "fields"
    ][
        "survey_number"
    ][
        "decision"
    ]
    == "auto_accepted"
)

print(
    "Test 1 - Review queue                  PASS"
)


# ============================================================
# TEST 2 - MACHINE VALUE PRESERVED
# ============================================================

assert (
    verification[
        "fields"
    ][
        "district"
    ][
        "machine_value"
    ]
    == "eee"
)

print(
    "Test 2 - Machine value preservation    PASS"
)


# ============================================================
# TEST 3 - HUMAN EDIT
# ============================================================

verification = apply_field_decision(
    verification,
    field_name="district",
    decision="edited",
    reviewer="REVIEWER-001",
    edited_value="Pune",
    reason=(
        "Verified against original document."
    ),
)

district = (
    verification[
        "fields"
    ][
        "district"
    ]
)

assert (
    district["machine_value"]
    == "eee"
)

assert (
    district["verified_value"]
    == "Pune"
)

assert (
    district["decision"]
    == "edited"
)

print(
    "Test 3 - Human edit                    PASS"
)


# ============================================================
# TEST 4 - MISSING FIELD ACCEPTED AS MISSING
# ============================================================

verification = apply_field_decision(
    verification,
    field_name="owner_name",
    decision="accepted",
    reviewer="REVIEWER-001",
    reason=(
        "Field is not present in source document."
    ),
)

assert (
    verification[
        "fields"
    ][
        "owner_name"
    ][
        "verified_value"
    ]
    is None
)

assert (
    verification[
        "fields"
    ][
        "owner_name"
    ][
        "decision"
    ]
    == "accepted"
)

print(
    "Test 4 - Accept missing field          PASS"
)


# ============================================================
# TEST 5 - DUPLICATE STILL PENDING
# ============================================================

assert (
    can_finalize(
        verification
    )
    is False
)

print(
    "Test 5 - Duplicate blocks finalize     PASS"
)


# ============================================================
# TEST 6 - HUMAN DUPLICATE DECISION
# ============================================================

verification = apply_duplicate_decision(
    verification,
    decision="not_duplicate",
    reviewer="REVIEWER-001",
    reason=(
        "Compared source records manually."
    ),
)

assert (
    verification[
        "duplicate_decision"
    ][
        "machine_classification"
    ]
    == "possible_duplicate"
)

assert (
    verification[
        "duplicate_decision"
    ][
        "human_decision"
    ]
    == "not_duplicate"
)

print(
    "Test 6 - Duplicate decision            PASS"
)


# ============================================================
# TEST 7 - FINALIZE
# ============================================================

assert (
    can_finalize(
        verification
    )
    is True
)

verification = finalize_verification(
    verification,
    reviewer="REVIEWER-001",
)

assert (
    verification["status"]
    == "verified"
)

assert (
    verification[
        "summary"
    ][
        "fields_pending"
    ]
    == 0
)

print(
    "Test 7 - Finalization                  PASS"
)


# ============================================================
# TEST 8 - VERIFIED VALUES
# ============================================================

values = get_verified_values(
    verification
)

assert (
    values["district"]
    == "Pune"
)

assert (
    values["survey_number"]
    == "54/2"
)

assert (
    values["owner_name"]
    is None
)

print(
    "Test 8 - Verified values               PASS"
)


# ============================================================
# TEST 9 - AUDIT TRAIL
# ============================================================

assert (
    len(
        verification[
            "audit_trail"
        ]
    )
    >= 4
)

events = [
    event["event"]
    for event in verification[
        "audit_trail"
    ]
]

assert (
    "field_decision"
    in events
)

assert (
    "duplicate_decision"
    in events
)

assert (
    "verification_finalized"
    in events
)

print(
    "Test 9 - Audit trail                   PASS"
)


print()
print("=" * 60)
print(
    "ALL HUMAN VERIFICATION V1.0 TESTS PASSED"
)
print("=" * 60)