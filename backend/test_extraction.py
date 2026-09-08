import json

from layout.layout import build_layout
from composer.composer import compose_document_text
from extraction.extractor import extract_fields


# ============================================================
# FILE CONFIGURATION
# ============================================================

OCR_FILE = (
    r"C:\Users\DELL G15 5530\Documents\PS26018"
    r"\backend\digitalized_documents\DOC-6548A9AB"
    r"\ocr_result.json"
)

DOCUMENT_ID = "DOC-6548A9AB"

OUTPUT_FILE = "extraction_result.json"


# ============================================================
# 1. LOAD OCR RESULT
# ============================================================

print("Loading OCR result...")

with open(
    OCR_FILE,
    "r",
    encoding="utf-8",
) as file:

    ocr_result = json.load(file)


# ============================================================
# 2. BUILD LAYOUT
# ============================================================

print("Running Layout V1.2...")

layout_result = build_layout(
    ocr_result,
    DOCUMENT_ID,
)

print("Layout completed.")


# ============================================================
# 3. BUILD STRUCTURED TEXT
# ============================================================

print("Running Structured Text Composer V1.2...")

composer_result = compose_document_text(
    layout_result
)

print("Composer completed.")


# ============================================================
# 4. MERGE COMPOSER OUTPUT
# ============================================================

layout_result["document_text"] = (
    composer_result["document_text"]
)

layout_result["text_blocks"] = (
    composer_result["text_blocks"]
)


# ============================================================
# 5. RUN EXTRACTION
# ============================================================

print("Running Extraction V1...")

extraction_result = extract_fields(
    ocr_result,
    layout_result,
)

print("Extraction completed.")


# ============================================================
# 6. SAVE RESULT
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        extraction_result,
        file,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# 7. SUMMARY
# ============================================================

print()
print("====================================")
print("EXTRACTION V1 COMPLETE")
print("====================================")

print(
    "Document ID:",
    extraction_result["document_id"],
)

print(
    "Total Fields:",
    extraction_result["summary"]["total_fields"],
)

print(
    "Extracted Fields:",
    extraction_result["summary"]["extracted_fields"],
)

print(
    "Missing Fields:",
    extraction_result["summary"]["missing_fields"],
)

print(
    "Output:",
    OUTPUT_FILE,
)


# ============================================================
# 8. PRINT EXTRACTED VALUES
# ============================================================

print()
print("====================================")
print("EXTRACTED FIELDS")
print("====================================")

for field_name, field in (
    extraction_result["fields"].items()
):

    print(
        f"{field_name:35} : "
        f"{field['value']}"
    )


# ============================================================
# 9. PRINT PROVENANCE
# ============================================================

print()
print("====================================")
print("EXTRACTION EVIDENCE")
print("====================================")

for field_name, field in (
    extraction_result["fields"].items()
):

    if field["value"] is not None:

        print()
        print("FIELD:", field_name)
        print("VALUE:", field["value"])
        print("SOURCE:", field["source_text"])
        print(
            "LINE:",
            field["source_line_ids"]
        )