import copy

from duplicate_detection.duplicate_detector import (
    detect_duplicates,
)


IDENTIFIERS = (
    "registered_document_number",
    "mutation_entry_number",
    "survey_number",
    "khasra_number",
    "khata_number",
)


def make_record(
    document_id,
    registered_document_number=None,
    mutation_entry_number=None,
    survey_number=None,
    khasra_number=None,
    khata_number=None,
):

    values = {
        "registered_document_number": (
            registered_document_number
        ),
        "mutation_entry_number": (
            mutation_entry_number
        ),
        "survey_number": survey_number,
        "khasra_number": khasra_number,
        "khata_number": khata_number,
    }

    fields = {}

    for field_name in IDENTIFIERS:

        value = values[field_name]

        fields[field_name] = {
            "field": field_name,
            "value": value,
            "raw_value": value,
            "normalized_value": value,
            "validation_status": (
                "valid"
                if value is not None
                else "missing"
            ),
        }

    return {
        "validation_version": "1.0",
        "document_id": document_id,
        "fields": fields,
    }


def run_test(
    test_name,
    candidate,
    existing,
    expected_status,
):

    result = detect_duplicates(
        candidate,
        existing,
    )

    actual = result["status"]

    success = (
        actual == expected_status
    )

    print(
        f"{test_name:45} "
        f"{'PASS' if success else 'FAIL'} "
        f"({actual})"
    )

    if not success:

        raise AssertionError(
            f"{test_name}: expected "
            f"{expected_status}, got {actual}"
        )


# ============================================================
# TEST 1
# DOCUMENT NUMBER MATCH
# ============================================================

candidate = make_record(
    "DOC-CANDIDATE",
    registered_document_number="789/2018",
    survey_number="54/2",
)

existing = make_record(
    "DOC-001",
    registered_document_number="789/2018",
    survey_number="99/1",
)

run_test(
    "Test 1 - Registration number match",
    candidate,
    [existing],
    "strong_duplicate",
)


# ============================================================
# TEST 2
# MUTATION NUMBER MATCH
# ============================================================

candidate = make_record(
    "DOC-CANDIDATE",
    mutation_entry_number="456",
)

existing = make_record(
    "DOC-002",
    mutation_entry_number="456",
)

run_test(
    "Test 2 - Mutation number match",
    candidate,
    [existing],
    "strong_duplicate",
)


# ============================================================
# TEST 3
# SURVEY + KHASRA + KHATA
# ============================================================

candidate = make_record(
    "DOC-CANDIDATE",
    survey_number="54/2",
    khasra_number="100",
    khata_number="88",
)

existing = make_record(
    "DOC-003",
    survey_number="54/2",
    khasra_number="100",
    khata_number="88",
)

run_test(
    "Test 3 - All three land identifiers",
    candidate,
    [existing],
    "possible_duplicate",
)


# ============================================================
# TEST 4
# ONLY SURVEY
# ============================================================

candidate = make_record(
    "DOC-CANDIDATE",
    survey_number="54/2",
)

existing = make_record(
    "DOC-004",
    survey_number="54/2",
)

run_test(
    "Test 4 - Survey only",
    candidate,
    [existing],
    "insufficient_evidence",
)


# ============================================================
# TEST 5
# DIFFERENT IDENTIFIERS
# ============================================================

candidate = make_record(
    "DOC-CANDIDATE",
    registered_document_number="789/2018",
    mutation_entry_number="456",
    survey_number="54/2",
)

existing = make_record(
    "DOC-005",
    registered_document_number="999/2020",
    mutation_entry_number="999",
    survey_number="20/1",
)

run_test(
    "Test 5 - Different identifiers",
    candidate,
    [existing],
    "not_duplicate",
)


# ============================================================
# TEST 6
# MISSING IDENTIFIERS
# ============================================================

candidate = make_record(
    "DOC-CANDIDATE"
)

existing = make_record(
    "DOC-006",
    survey_number="54/2",
)

run_test(
    "Test 6 - Missing identifiers",
    candidate,
    [existing],
    "insufficient_evidence",
)


# ============================================================
# TEST 7
# MULTIPLE EXISTING RECORDS
# ============================================================

candidate = make_record(
    "DOC-CANDIDATE",
    registered_document_number="789/2018",
    survey_number="54/2",
)

existing_1 = make_record(
    "DOC-007-A",
    registered_document_number="123/2011",
    survey_number="54/2",
)

existing_2 = make_record(
    "DOC-007-B",
    registered_document_number="789/2018",
    survey_number="99/1",
)

existing_3 = make_record(
    "DOC-007-C",
    registered_document_number="777/2015",
    survey_number="100/1",
)

result = detect_duplicates(
    candidate,
    [
        existing_1,
        existing_2,
        existing_3,
    ],
)

assert (
    result["status"]
    == "strong_duplicate"
)

assert (
    result["best_match"]["document_id"]
    == "DOC-007-B"
)

print(
    f"{'Test 7 - Multiple existing records':45} "
    f"PASS ({result['status']})"
)


print()
print("====================================")
print("ALL DUPLICATE DETECTION TESTS PASSED")
print("====================================")