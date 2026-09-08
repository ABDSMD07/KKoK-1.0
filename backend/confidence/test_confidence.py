import json

from confidence_scorer import calculate_confidence


VALIDATION_FILE = "../validation_result.json"
DUPLICATE_FILE = "../duplicate_detection_result.json"
OUTPUT_FILE = "../confidence_result.json"


def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


print("=" * 60)
print("CONFIDENCE V1.0 TEST")
print("=" * 60)

print()
print("Loading Validation result...")

validation_result = load_json(
    VALIDATION_FILE
)

print("Validation loaded.")

print()
print("Loading Duplicate Detection result...")

try:

    duplicate_result = load_json(
        DUPLICATE_FILE
    )

    print("Duplicate Detection loaded.")

except FileNotFoundError:

    duplicate_result = None

    print(
        "Duplicate Detection result not found."
    )

print()
print("Calculating Confidence...")

confidence_result = calculate_confidence(
    validation_result,
    duplicate_result,
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        confidence_result,
        file,
        indent=2,
        ensure_ascii=False,
    )


print()
print("=" * 60)
print("CONFIDENCE V1.0 COMPLETE")
print("=" * 60)

print(
    "Document ID:",
    confidence_result["document_id"],
)

summary = confidence_result[
    "summary"
]

print(
    "Record Confidence:",
    summary[
        "record_confidence_score"
    ],
)

print(
    "Confidence Level:",
    summary[
        "record_confidence_level"
    ],
)

print(
    "Completeness:",
    summary[
        "completeness_score"
    ],
)

print(
    "Fields Requiring Review:",
    len(
        summary[
            "fields_requiring_review"
        ]
    ),
)

print()
print("=" * 60)
print("FIELD CONFIDENCE")
print("=" * 60)

for field_name, field in (
    confidence_result[
        "fields"
    ].items()
):

    print(
        f"{field_name:35}"
        f" Score={field['confidence_score']:6.2f}"
        f" Level={field['confidence_level']:10}"
        f" Review={field['confidence_review']}"
    )

print()
print(
    "Output:",
    OUTPUT_FILE,
)