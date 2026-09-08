import json
from pathlib import Path

from duplicate_detector import detect_duplicates


# ============================================================
# PATHS
# ============================================================

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent

VALIDATION_RESULT_PATH = BACKEND_DIR / "validation_result.json"
OUTPUT_PATH = BACKEND_DIR / "duplicate_detection_result.json"


# ============================================================
# LOAD VALIDATION RESULT
# ============================================================

if not VALIDATION_RESULT_PATH.exists():
    raise FileNotFoundError(
        f"Validation result not found:\n{VALIDATION_RESULT_PATH}"
    )

with open(VALIDATION_RESULT_PATH, "r", encoding="utf-8") as f:
    validation_result = json.load(f)


# ============================================================
# DEMO EXISTING RECORDS
# ============================================================
#
# These are validated-record-shaped examples used only to
# exercise the duplicate detector.
#
# IMPORTANT:
# In the real system, these will later come from PostgreSQL.
#

existing_records = [
    {
        "document_id": "EXISTING-DOC-001",
        "validation_version": "1.0",
        "fields": {
            "registered_document_number": {
                "normalized_value": "999/2020",
                "validation_status": "valid",
            },
            "mutation_entry_number": {
                "normalized_value": "MUT-999",
                "validation_status": "valid",
            },
            "survey_number": {
                "normalized_value": "999",
                "validation_status": "valid",
            },
            "khasra_number": {
                "normalized_value": "999",
                "validation_status": "valid",
            },
            "khata_number": {
                "normalized_value": "999",
                "validation_status": "valid",
            },
        },
    }
]


# ============================================================
# RUN DUPLICATE DETECTION
# ============================================================

duplicate_result = detect_duplicates(
    validation_result=validation_result,
    existing_records=existing_records,
)


# ============================================================
# SAVE RESULT
# ============================================================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(
        duplicate_result,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# CONSOLE OUTPUT
# ============================================================

print("=" * 60)
print("DUPLICATE DETECTION V1.0 COMPLETE")
print("=" * 60)

print(f"Document ID: {duplicate_result.get('document_id')}")
print(f"Status: {duplicate_result.get('status')}")

summary = duplicate_result.get("summary", {})

print(
    f"Existing Records Received: "
    f"{summary.get('existing_records_received', 0)}"
)

print(
    f"Records Compared: "
    f"{summary.get('records_compared', 0)}"
)

print(
    f"Strong Duplicate Matches: "
    f"{summary.get('strong_duplicate_matches', 0)}"
)

print(
    f"Possible Duplicate Matches: "
    f"{summary.get('possible_duplicate_matches', 0)}"
)

print()
print(f"Output saved to:")
print(OUTPUT_PATH)