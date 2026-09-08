import json

from validation.validator import validate_normalization


INPUT_FILE = "normalization_result.json"
OUTPUT_FILE = "validation_result.json"


print("Loading Normalization result...")

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8",
) as file:
    normalization_result = json.load(file)


print("Running Validation V1.0...")

validation_result = validate_normalization(
    normalization_result
)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        validation_result,
        file,
        indent=2,
        ensure_ascii=False,
    )


print("Validation completed.")

print()
print("====================================")
print("VALIDATION V1.0 COMPLETE")
print("====================================")

print(
    "Document ID:",
    validation_result["document_id"],
)

print(
    "Structurally Valid:",
    validation_result["structurally_valid"],
)

summary = validation_result["summary"]

print("Total Fields:", summary["total_fields"])
print("Valid:", summary["valid_fields"])
print("Warnings:", summary["warning_fields"])
print("Invalid:", summary["invalid_fields"])
print("Missing:", summary["missing_fields"])
print("Not Checked:", summary["not_checked_fields"])
print("Issues:", summary["issue_count"])

print()
print("====================================")
print("FIELD VALIDATION")
print("====================================")

for field_name, field in validation_result["fields"].items():

    print(
        f"{field_name:35}: "
        f"{field.get('normalized_value')} "
        f"[{field.get('validation_status')}]"
    )

    for issue in field.get(
        "validation_issues",
        []
    ):
        print(
            f"    - {issue['code']}: "
            f"{issue['message']}"
        )


print()
print("====================================")
print("CROSS-FIELD ISSUES")
print("====================================")

if not validation_result["cross_field_issues"]:
    print("None")

else:
    for issue in validation_result["cross_field_issues"]:
        print(
            f"- {issue['code']}: "
            f"{issue['message']}"
        )


print()
print(
    "Output:",
    OUTPUT_FILE,
)