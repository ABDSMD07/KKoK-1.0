import json

from normalization.normalizer import normalize_extraction


INPUT_FILE = "extraction_result.json"
OUTPUT_FILE = "normalization_result.json"


print("Loading Extraction result...")

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8",
) as file:

    extraction_result = json.load(
        file
    )


print("Running Normalization V1.0...")

normalization_result = normalize_extraction(
    extraction_result
)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        normalization_result,
        file,
        indent=2,
        ensure_ascii=False,
    )


print("Normalization completed.")

print()
print("====================================")
print("NORMALIZATION V1.0 COMPLETE")
print("====================================")

print(
    "Document ID:",
    normalization_result["document_id"],
)

print(
    "Total Fields:",
    normalization_result[
        "summary"
    ]["total_fields"],
)

print(
    "Normalized Fields:",
    normalization_result[
        "summary"
    ]["normalized_fields"],
)

print(
    "Missing Fields:",
    normalization_result[
        "summary"
    ]["missing_fields"],
)

print(
    "Changed Fields:",
    normalization_result[
        "summary"
    ]["changed_fields"],
)

print(
    "Output:",
    OUTPUT_FILE,
)


print()
print("====================================")
print("NORMALIZED VALUES")
print("====================================")

for field_name, field in (
    normalization_result[
        "fields"
    ].items()
):

    print(
        f"{field_name:35}: "
        f"{field['raw_value']} "
        f"-> "
        f"{field['normalized_value']}"
    )