"""
===========================================================
PS 26018 - Land Record Intelligence System
Duplicate Detection V1.0

Purpose:
    Compare identifier evidence from a validated candidate
    document against existing validated records.

Pipeline:

    Validation
        ↓
    Duplicate Detection V1.0
        ↓
    Confidence
        ↓
    Human Verification

Duplicate Detection uses ONLY:

    - registered_document_number
    - mutation_entry_number
    - survey_number
    - khasra_number
    - khata_number

It DOES NOT:
    - perform OCR / extraction / normalization
    - correct identifiers
    - calculate confidence
    - query databases
    - use owner/location fields
    - modify Validation output
===========================================================
"""

from typing import Any, Dict, List, Optional, Tuple


DUPLICATE_DETECTION_VERSION = "1.0"


IDENTIFIER_FIELDS = (
    "registered_document_number",
    "mutation_entry_number",
    "survey_number",
    "khasra_number",
    "khata_number",
)


STRONG_IDENTIFIERS = (
    "registered_document_number",
    "mutation_entry_number",
)


LAND_IDENTIFIERS = (
    "survey_number",
    "khasra_number",
    "khata_number",
)


# ============================================================
# STATUS VALUES
# ============================================================

STATUS_STRONG_DUPLICATE = "strong_duplicate"
STATUS_POSSIBLE_DUPLICATE = "possible_duplicate"
STATUS_INSUFFICIENT_EVIDENCE = "insufficient_evidence"
STATUS_NOT_DUPLICATE = "not_duplicate"


# ============================================================
# IDENTIFIER LABELS
# ============================================================

IDENTIFIER_LABELS = {
    "registered_document_number": "Registered document number",
    "mutation_entry_number": "Mutation entry number",
    "survey_number": "Survey number",
    "khasra_number": "Khasra number",
    "khata_number": "Khata number",
}


# ============================================================
# ACCEPTABLE VALIDATION STATUSES
# ============================================================

# Invalid identifiers must not participate in matching.
#
# Warning values may participate because "warning" does not
# necessarily mean the identifier itself is syntactically bad.
MATCHABLE_VALIDATION_STATUSES = {
    "valid",
    "warning",
}


# ============================================================
# SAFE VALUE EXTRACTION
# ============================================================

def _get_identifier(
    validation_result: Dict[str, Any],
    field_name: str,
) -> Optional[str]:
    """
    Return a normalized identifier only when the field is
    suitable for duplicate comparison.
    """

    fields = validation_result.get(
        "fields",
        {},
    )

    if not isinstance(fields, dict):
        return None

    field = fields.get(field_name)

    if not isinstance(field, dict):
        return None

    status = field.get(
        "validation_status"
    )

    if status not in MATCHABLE_VALIDATION_STATUSES:
        return None

    value = field.get(
        "normalized_value"
    )

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def _extract_identifiers(
    validation_result: Dict[str, Any],
) -> Dict[str, Optional[str]]:

    return {
        field_name: _get_identifier(
            validation_result,
            field_name,
        )
        for field_name in IDENTIFIER_FIELDS
    }


# ============================================================
# INPUT VALIDATION
# ============================================================

def _validate_input(
    validation_result: Dict[str, Any],
    parameter_name: str,
) -> None:

    if not isinstance(
        validation_result,
        dict,
    ):
        raise TypeError(
            f"{parameter_name} must be a dictionary"
        )

    fields = validation_result.get(
        "fields"
    )

    if not isinstance(fields, dict):
        raise ValueError(
            f"{parameter_name}['fields'] must be a dictionary"
        )


# ============================================================
# VALUE COMPARISON
# ============================================================

def _compare_identifiers(
    candidate: Dict[str, Optional[str]],
    existing: Dict[str, Optional[str]],
) -> Tuple[
    List[str],
    List[str],
    List[str],
]:
    """
    Returns:

        matched
        conflicting
        missing

    A conflict exists only when BOTH records contain a usable
    identifier and the values differ.

    Missing means comparison was impossible because either side
    did not contain a usable value.
    """

    matched = []
    conflicting = []
    missing = []

    for field_name in IDENTIFIER_FIELDS:

        candidate_value = candidate.get(
            field_name
        )

        existing_value = existing.get(
            field_name
        )

        if (
            candidate_value is None
            or existing_value is None
        ):
            missing.append(
                field_name
            )

            continue

        if candidate_value == existing_value:

            matched.append(
                field_name
            )

        else:

            conflicting.append(
                field_name
            )

    return (
        matched,
        conflicting,
        missing,
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def _classify_match(
    matched: List[str],
    conflicting: List[str],
) -> Tuple[str, List[str]]:
    """
    Policy V1.0:

        Registered document match
            -> strong duplicate

        Mutation entry match
            -> strong duplicate

        Survey + Khasra + Khata
            -> possible duplicate

        One/two land identifiers
            -> insufficient evidence

        No match + comparable conflicts
            -> not duplicate

        No usable comparison
            -> insufficient evidence
    """

    reasons = []

    if (
        "registered_document_number"
        in matched
    ):

        reasons.append(
            "Registered document number matched "
            "an existing record."
        )

        return (
            STATUS_STRONG_DUPLICATE,
            reasons,
        )

    if (
        "mutation_entry_number"
        in matched
    ):

        reasons.append(
            "Mutation entry number matched "
            "an existing record."
        )

        return (
            STATUS_STRONG_DUPLICATE,
            reasons,
        )

    land_matches = [
        field_name
        for field_name in LAND_IDENTIFIERS
        if field_name in matched
    ]

    if len(land_matches) == 3:

        reasons.append(
            "Survey number, Khasra number, and "
            "Khata number all matched an existing record."
        )

        return (
            STATUS_POSSIBLE_DUPLICATE,
            reasons,
        )

    if land_matches:

        readable = [
            IDENTIFIER_LABELS[
                field_name
            ]
            for field_name in land_matches
        ]

        reasons.append(
            f"{', '.join(readable)} matched, "
            "but land identifiers alone do not provide "
            "sufficient evidence for duplicate classification."
        )

        return (
            STATUS_INSUFFICIENT_EVIDENCE,
            reasons,
        )

    if conflicting:

        reasons.append(
            "Comparable identifiers were present but "
            "none matched."
        )

        return (
            STATUS_NOT_DUPLICATE,
            reasons,
        )

    reasons.append(
        "There were not enough comparable identifiers "
        "to determine whether the record is a duplicate."
    )

    return (
        STATUS_INSUFFICIENT_EVIDENCE,
        reasons,
    )


# ============================================================
# SINGLE RECORD COMPARISON
# ============================================================

def _compare_record(
    candidate_result: Dict[str, Any],
    existing_result: Dict[str, Any],
) -> Dict[str, Any]:

    candidate_identifiers = (
        _extract_identifiers(
            candidate_result
        )
    )

    existing_identifiers = (
        _extract_identifiers(
            existing_result
        )
    )

    (
        matched,
        conflicting,
        missing,
    ) = _compare_identifiers(
        candidate_identifiers,
        existing_identifiers,
    )

    status, reasons = _classify_match(
        matched,
        conflicting,
    )

    return {
        "document_id": (
            existing_result.get(
                "document_id"
            )
        ),

        "status": status,

        "matched_identifiers": (
            matched
        ),

        "conflicting_identifiers": (
            conflicting
        ),

        "missing_identifiers": (
            missing
        ),

        "match_reasons": (
            reasons
        ),

        # Useful for audit/debugging.
        "identifier_comparison": {
            field_name: {
                "candidate": (
                    candidate_identifiers[
                        field_name
                    ]
                ),
                "existing": (
                    existing_identifiers[
                        field_name
                    ]
                ),
            }
            for field_name in IDENTIFIER_FIELDS
        },
    }


# ============================================================
# MATCH RANKING
# ============================================================

STATUS_RANK = {
    STATUS_STRONG_DUPLICATE: 4,
    STATUS_POSSIBLE_DUPLICATE: 3,
    STATUS_INSUFFICIENT_EVIDENCE: 2,
    STATUS_NOT_DUPLICATE: 1,
}


def _match_sort_key(
    comparison: Dict[str, Any],
) -> Tuple[int, int, int]:

    status = comparison.get(
        "status"
    )

    status_rank = STATUS_RANK.get(
        status,
        0,
    )

    matched_count = len(
        comparison.get(
            "matched_identifiers",
            [],
        )
    )

    conflict_count = len(
        comparison.get(
            "conflicting_identifiers",
            [],
        )
    )

    return (
        status_rank,
        matched_count,
        -conflict_count,
    )


# ============================================================
# TOP-LEVEL STATUS
# ============================================================

def _overall_status(
    comparisons: List[Dict[str, Any]],
) -> str:

    if not comparisons:
        return STATUS_INSUFFICIENT_EVIDENCE

    statuses = {
        comparison.get("status")
        for comparison in comparisons
    }

    if STATUS_STRONG_DUPLICATE in statuses:
        return STATUS_STRONG_DUPLICATE

    if STATUS_POSSIBLE_DUPLICATE in statuses:
        return STATUS_POSSIBLE_DUPLICATE

    if STATUS_INSUFFICIENT_EVIDENCE in statuses:
        return STATUS_INSUFFICIENT_EVIDENCE

    return STATUS_NOT_DUPLICATE


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def detect_duplicates(
    validation_result: Dict[str, Any],
    existing_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare one candidate Validation V1.0 result against existing
    validated records.

    No input object is modified.
    """

    _validate_input(
        validation_result,
        "validation_result",
    )

    if not isinstance(
        existing_records,
        list,
    ):
        raise TypeError(
            "existing_records must be a list"
        )

    candidate_identifiers = (
        _extract_identifiers(
            validation_result
        )
    )

    candidate_missing = [
        field_name
        for field_name, value
        in candidate_identifiers.items()
        if value is None
    ]

    comparisons = []

    for index, existing_record in enumerate(
        existing_records
    ):

        if not isinstance(
            existing_record,
            dict,
        ):
            continue

        try:

            _validate_input(
                existing_record,
                (
                    f"existing_records[{index}]"
                ),
            )

        except (
            TypeError,
            ValueError,
        ):
            # Malformed comparison records are skipped.
            # They are reported separately below.
            continue

        # Do not compare a document against itself when IDs exist.
        candidate_document_id = (
            validation_result.get(
                "document_id"
            )
        )

        existing_document_id = (
            existing_record.get(
                "document_id"
            )
        )

        if (
            candidate_document_id is not None
            and existing_document_id is not None
            and candidate_document_id
            == existing_document_id
        ):
            continue

        comparisons.append(
            _compare_record(
                validation_result,
                existing_record,
            )
        )

    comparisons.sort(
        key=_match_sort_key,
        reverse=True,
    )

    best_comparison = (
        comparisons[0]
        if comparisons
        else None
    )

    status = _overall_status(
        comparisons
    )

    invalid_existing_records = sum(
        1
        for record in existing_records
        if (
            not isinstance(record, dict)
            or not isinstance(
                record.get("fields"),
                dict,
            )
        )
    )

    if best_comparison:

        best_match = {
            "document_id": (
                best_comparison[
                    "document_id"
                ]
            )
        }

        matched_identifiers = (
            best_comparison[
                "matched_identifiers"
            ]
        )

        conflicting_identifiers = (
            best_comparison[
                "conflicting_identifiers"
            ]
        )

        missing_identifiers = (
            best_comparison[
                "missing_identifiers"
            ]
        )

        match_reasons = (
            best_comparison[
                "match_reasons"
            ]
        )

    else:

        best_match = None
        matched_identifiers = []
        conflicting_identifiers = []
        missing_identifiers = (
            candidate_missing
        )

        match_reasons = [
            "No existing comparable records were available."
        ]

    return {
        "duplicate_detection_version": (
            DUPLICATE_DETECTION_VERSION
        ),

        "source_validation_version": (
            validation_result.get(
                "validation_version"
            )
        ),

        "document_id": (
            validation_result.get(
                "document_id"
            )
        ),

        "status": status,

        "best_match": best_match,

        "matched_identifiers": (
            matched_identifiers
        ),

        "conflicting_identifiers": (
            conflicting_identifiers
        ),

        "missing_identifiers": (
            missing_identifiers
        ),

        "match_reasons": (
            match_reasons
        ),

        "candidate_identifiers": (
            candidate_identifiers
        ),

        "summary": {
            "existing_records_received": (
                len(existing_records)
            ),

            "records_compared": (
                len(comparisons)
            ),

            "invalid_existing_records": (
                invalid_existing_records
            ),

            "strong_duplicate_matches": sum(
                1
                for comparison in comparisons
                if comparison["status"]
                == STATUS_STRONG_DUPLICATE
            ),

            "possible_duplicate_matches": sum(
                1
                for comparison in comparisons
                if comparison["status"]
                == STATUS_POSSIBLE_DUPLICATE
            ),
        },

        # Keep all candidate comparisons so a later human-review
        # stage is not limited to only the best result.
        "candidate_matches": (
            comparisons
        ),
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "Duplicate Detection V1.0 module loaded successfully."
    )