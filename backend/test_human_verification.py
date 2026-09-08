"""
===========================================================
PS 26018 - Human Verification V1.0
Production Artifact Runner
===========================================================

Purpose:
    Connect the actual pipeline outputs to Human Verification
    and save the resulting verification artifact.

Pipeline:
    Validation
        +
    Duplicate Detection
        +
    Confidence
        ↓
    Human Verification
        ↓
    human_verification_result.json

IMPORTANT:
    This runner does NOT automatically make human decisions.
    It only creates the review artifact.

    Required reviews remain pending until a human reviewer
    explicitly accepts, edits, rejects, or resolves them.
===========================================================
"""

import json

from human_verification.verification_engine import (
    create_verification,
)


# ============================================================
# FILE PATHS
# ============================================================

VALIDATION_FILE = "validation_result.json"

DUPLICATE_FILE = "duplicate_detection_result.json"

CONFIDENCE_FILE = "confidence_result.json"

OUTPUT_FILE = "human_verification_result.json"


# ============================================================
# JSON LOADER
# ============================================================

def load_json(filename):
    """
    Load a JSON artifact from the backend directory.
    """

    print(f"Loading: {filename}")

    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("HUMAN VERIFICATION V1.0")
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Load upstream artifacts
    # --------------------------------------------------------

    validation_result = load_json(
        VALIDATION_FILE
    )

    duplicate_result = load_json(
        DUPLICATE_FILE
    )

    confidence_result = load_json(
        CONFIDENCE_FILE
    )

    print()
    print("Creating Human Verification artifact...")
    print()

    # --------------------------------------------------------
    # Create verification artifact
    # --------------------------------------------------------
    #
    # The engine receives the machine-produced results.
    # It creates the review state without changing the
    # original machine artifacts.
    #
    # --------------------------------------------------------

    verification_result = create_verification(
        validation_result=validation_result,
        duplicate_result=duplicate_result,
        confidence_result=confidence_result,
    )

    # --------------------------------------------------------
    # Save artifact
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            verification_result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = verification_result.get(
        "summary",
        {},
    )

    print("=" * 60)
    print("HUMAN VERIFICATION V1.0 COMPLETE")
    print("=" * 60)

    print(
        "Document ID:",
        verification_result.get(
            "document_id"
        ),
    )

    print(
        "Status:",
        verification_result.get(
            "status"
        ),
    )

    print(
        "Total Fields:",
        summary.get(
            "total_fields"
        ),
    )

    print(
        "Fields Requiring Review:",
        summary.get(
            "fields_requiring_review"
        ),
    )

    print(
        "Fields Pending:",
        summary.get(
            "fields_pending"
        ),
    )

    print(
        "Duplicate Review Required:",
        verification_result.get(
            "duplicate_decision",
            {}
        ).get(
            "review_required"
        ),
    )

    print()
    print("Output saved to:")
    print(OUTPUT_FILE)
    print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()