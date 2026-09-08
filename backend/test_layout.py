import json

from layout.layout import build_layout


OCR_FILE = r"C:\Users\DELL G15 5530\Documents\PS26018\backend\digitalized_documents\DOC-6548A9AB\ocr_result.json"

DOCUMENT_ID = "DOC-6548A9AB"

OUTPUT_FILE = "layout_result.json"


# Load OCR result
with open(OCR_FILE, "r", encoding="utf-8") as file:
    ocr_result = json.load(file)


# Run Layout V1.2
layout_result = build_layout(
    ocr_result,
    DOCUMENT_ID,
)


# Save layout result
with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        layout_result,
        file,
        indent=2,
        ensure_ascii=False,
    )


# Print summary
print("====================================")
print("LAYOUT ANALYSIS COMPLETE")
print("====================================")

print(
    "Document ID:",
    DOCUMENT_ID,
)

print(
    "Pages:",
    layout_result["summary"]["page_count"],
)

print(
    "Lines:",
    layout_result["summary"]["line_count"],
)

print(
    "Blocks:",
    layout_result["summary"]["block_count"],
)

print(
    "Sections:",
    layout_result["summary"]["section_count"],
)

print(
    "Key-Value relationships:",
    layout_result["summary"]["relationship_count"],
)

print(
    "Output:",
    OUTPUT_FILE,
)