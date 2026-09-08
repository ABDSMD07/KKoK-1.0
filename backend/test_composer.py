import json

from layout.layout import build_layout
from composer.composer import compose_document_text


OCR_FILE = r"C:\Users\DELL G15 5530\Documents\PS26018\backend\digitalized_documents\DOC-6548A9AB\ocr_result.json"

DOCUMENT_ID = "DOC-6548A9AB"

OUTPUT_FILE = "composer_result.json"


# ============================================================
# 1. LOAD OCR RESULT
# ============================================================

with open(OCR_FILE, "r", encoding="utf-8") as file:
    ocr_result = json.load(file)


# ============================================================
# 2. RUN LAYOUT V1.2
# ============================================================

print("Running Layout V1.2...")

layout_result = build_layout(
    ocr_result,
    DOCUMENT_ID,
)

print("Layout completed.")


# ============================================================
# 3. RUN STRUCTURED TEXT COMPOSER V1.2
# ============================================================

print("Running Structured Text Composer V1.2...")

composer_result = compose_document_text(
    layout_result
)

print("Composer completed.")


# ============================================================
# 4. MERGE COMPOSER OUTPUT
# ============================================================

layout_result["document_text"] = composer_result["document_text"]

layout_result["text_blocks"] = composer_result["text_blocks"]


# ============================================================
# 5. SAVE RESULT
# ============================================================

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


# ============================================================
# 6. PRINT SUMMARY
# ============================================================

print()
print("====================================")
print("COMPOSER ANALYSIS COMPLETE")
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
    "Sections:",
    layout_result["summary"]["section_count"],
)

print(
    "Relationships:",
    layout_result["summary"]["relationship_count"],
)

print(
    "Text Blocks:",
    len(composer_result["text_blocks"]),
)

print(
    "Document Text Length:",
    len(composer_result["document_text"]),
)

print(
    "Output:",
    OUTPUT_FILE,
)


# ============================================================
# 7. PREVIEW STRUCTURED TEXT
# ============================================================

print()
print("====================================")
print("DOCUMENT TEXT PREVIEW")
print("====================================")

print(composer_result["document_text"])