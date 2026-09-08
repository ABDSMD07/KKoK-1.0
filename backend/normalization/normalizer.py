"""
===========================================================
PS 26018 - Land Record Intelligence System
Normalization V1.0

Purpose:
    Standardize values produced by Extraction V1.1 while
    preserving the original extracted value and evidence.

Pipeline:

    Extraction V1.1
          ↓
    Normalization V1.0
          ↓
       Validation

Normalization DOES:
    - Unicode normalization
    - whitespace normalization
    - Devanagari digit conversion
    - date standardization
    - identifier standardization
    - ownership-share standardization
    - area/unit standardization
    - textual value normalization
    - missing/null normalization

Normalization DOES NOT:
    - validate whether a value is factually correct
    - calculate confidence
    - modify extraction evidence
    - guess missing values
    - silently correct uncertain OCR
===========================================================
"""

import copy
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


NORMALIZATION_VERSION = "1.0"


# ============================================================
# FIELD GROUPS
# ============================================================

NAME_FIELDS = {
    "owner_name",
    "father_name",
    "ownership_owner_name",
}


LOCATION_FIELDS = {
    "village",
    "tehsil",
    "district",
}


DATE_FIELDS = {
    "mutation_date",
    "registration_date",
}


IDENTIFIER_FIELDS = {
    "survey_number",
    "khasra_number",
    "khata_number",
    "serial_number",
    "mutation_entry_number",
    "registered_document_number",
}


TEXT_FIELDS = {
    "address",
    "land_classification",
    "nature_of_rights",
    "mutation_type",
    "sub_registrar_office",
}


# ============================================================
# DEVANAGARI DIGITS
# ============================================================

DEVANAGARI_DIGITS = str.maketrans({
    "०": "0",
    "१": "1",
    "२": "2",
    "३": "3",
    "४": "4",
    "५": "5",
    "६": "6",
    "७": "7",
    "८": "8",
    "९": "9",
})


def normalize_digits(value: str) -> str:
    """
    Convert Devanagari digits to ASCII digits.

    Example:
        ५४/२ -> 54/2
        १२/०३/२०१८ -> 12/03/2018
    """

    return value.translate(
        DEVANAGARI_DIGITS
    )


# ============================================================
# GENERIC UNICODE NORMALIZATION
# ============================================================

def normalize_unicode(
    value: Any,
) -> str:

    if value is None:
        return ""

    text = str(value)

    # NFC preserves composed Indic text better than using NFKC
    # indiscriminately for source-language values.
    text = unicodedata.normalize(
        "NFC",
        text,
    )

    replacements = {
        "\u00a0": " ",
        "\u200b": "",
        "\ufeff": "",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    return text


# ============================================================
# WHITESPACE
# ============================================================

def normalize_whitespace(
    value: Any,
) -> str:

    text = normalize_unicode(
        value
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# NULL NORMALIZATION
# ============================================================

NULL_VALUES = {
    "",
    "none",
    "null",
    "nil",
    "n/a",
    "na",
    "not available",
    "not applicable",
    "-",
    "--",
}


def normalize_null(
    value: Any,
) -> Optional[str]:

    if value is None:
        return None

    text = normalize_whitespace(
        value
    )

    if text.lower() in NULL_VALUES:
        return None

    return text


# ============================================================
# GENERAL TEXT
# ============================================================

def normalize_text_value(
    value: Any,
) -> Optional[str]:

    text = normalize_null(
        value
    )

    if text is None:
        return None

    text = normalize_digits(
        text
    )

    # Normalize spaces around separators without removing
    # potentially meaningful punctuation.
    text = re.sub(
        r"\s*,\s*",
        ", ",
        text,
    )

    text = re.sub(
        r"\s*;\s*",
        "; ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# NAMES
# ============================================================

def normalize_name(
    value: Any,
) -> Optional[str]:

    """
    Conservative name normalization.

    We deliberately do NOT:
        - title-case names
        - remove initials
        - expand abbreviations
        - transliterate Indic names
        - guess OCR corrections

    Those operations can change identity.
    """

    text = normalize_text_value(
        value
    )

    if text is None:
        return None

    # Remove accidental repeated spaces around periods used
    # in initials:
    #
    # Robert L. Sterling
    #
    text = re.sub(
        r"\s*\.\s*",
        ". ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# LOCATION
# ============================================================

def normalize_location(
    value: Any,
) -> Optional[str]:

    """
    Structural normalization only.

    Example:
        '  Green   Valley  '
        ->
        'Green Valley'

    Whether the location actually exists belongs to Validation.
    """

    return normalize_text_value(
        value
    )


# ============================================================
# IDENTIFIERS
# ============================================================

def normalize_identifier(
    value: Any,
) -> Optional[str]:

    text = normalize_null(
        value
    )

    if text is None:
        return None

    text = normalize_digits(
        text
    )

    # Normalize slash spacing:
    #
    # 54 / 2 -> 54/2
    #
    text = re.sub(
        r"\s*/\s*",
        "/",
        text,
    )

    # Normalize hyphen spacing:
    #
    # 54 - A -> 54-A
    #
    text = re.sub(
        r"\s*-\s*",
        "-",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# DATE NORMALIZATION
# ============================================================

DATE_PATTERN = re.compile(
    r"^(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{4})$"
)


def normalize_date(
    value: Any,
) -> Optional[str]:

    """
    Standard output:
        YYYY-MM-DD

    Examples:
        12/03/2018 -> 2018-03-12
        12-03-2018 -> 2018-03-12
        १२/०३/२०१८ -> 2018-03-12

    Impossible dates are preserved rather than discarded,
    because semantic validity belongs to Validation.
    """

    text = normalize_null(
        value
    )

    if text is None:
        return None

    text = normalize_digits(
        text
    )

    match = DATE_PATTERN.fullmatch(
        text
    )

    if not match:
        return text

    day = int(
        match.group(1)
    )

    month = int(
        match.group(2)
    )

    year = int(
        match.group(3)
    )

    try:

        parsed = datetime(
            year,
            month,
            day,
        )

    except ValueError:

        # Do not destroy the extracted value.
        # Validation will mark the date invalid later.
        return text

    return parsed.strftime(
        "%Y-%m-%d"
    )


# ============================================================
# OWNERSHIP SHARE
# ============================================================

def normalize_share(
    value: Any,
) -> Optional[str]:

    """
    Examples:

        1 / 1 (Full)
            ->
        1/1 (Full)

        १ / २
            ->
        1/2
    """

    text = normalize_text_value(
        value
    )

    if text is None:
        return None

    text = normalize_digits(
        text
    )

    text = re.sub(
        r"\s*/\s*",
        "/",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# AREA NORMALIZATION
# ============================================================

AREA_PATTERN = re.compile(
    r"^\s*"
    r"(?P<number>\d+(?:\.\d+)?)"
    r"\s*"
    r"(?P<unit>"
    r"acres?|"
    r"hectares?|"
    r"ha|"
    r"sq\.?\s*m|"
    r"sqm"
    r")?"
    r"\s*$",
    re.IGNORECASE,
)


AREA_UNIT_MAP = {
    "acre": "acre",
    "acres": "acre",

    "hectare": "hectare",
    "hectares": "hectare",
    "ha": "hectare",

    "sqm": "square_meter",
    "sq m": "square_meter",
    "sq. m": "square_meter",
}


def _canonical_decimal(
    number: str,
) -> str:

    """
    Keep a stable decimal representation without unnecessarily
    converting the value to float.

        10.500 -> 10.5
        10.0   -> 10
        10     -> 10
    """

    if "." not in number:
        return number

    number = number.rstrip("0")
    number = number.rstrip(".")

    return number


def normalize_area(
    value: Any,
) -> Tuple[
    Optional[str],
    Optional[Dict[str, Any]],
]:

    """
    Returns:
        normalized display value
        structured area metadata

    Example:

        "10.5 ACRES"

    becomes:

        "10.5 acre"

        {
            "value": "10.5",
            "unit": "acre"
        }

    Unit conversion is intentionally NOT performed here.
    """

    text = normalize_null(
        value
    )

    if text is None:
        return None, None

    text = normalize_digits(
        text
    )

    text = normalize_whitespace(
        text
    )

    match = AREA_PATTERN.fullmatch(
        text
    )

    if not match:

        # Preserve unrecognized representation.
        return text, None

    number = _canonical_decimal(
        match.group("number")
    )

    raw_unit = match.group(
        "unit"
    )

    if raw_unit is None:

        return (
            number,
            {
                "value": number,
                "unit": None,
            },
        )

    normalized_unit_key = (
        normalize_whitespace(
            raw_unit
        )
        .lower()
    )

    canonical_unit = AREA_UNIT_MAP.get(
        normalized_unit_key,
        normalized_unit_key,
    )

    display_value = (
        f"{number} {canonical_unit}"
    )

    return (
        display_value,
        {
            "value": number,
            "unit": canonical_unit,
        },
    )


# ============================================================
# FIELD DISPATCH
# ============================================================

def normalize_field_value(
    field_name: str,
    raw_value: Any,
) -> Tuple[
    Optional[str],
    Optional[Dict[str, Any]],
]:

    """
    Returns:

        normalized_value
        structured_value

    structured_value is optional field-specific metadata.
    """

    if raw_value is None:
        return None, None

    if field_name in DATE_FIELDS:

        return (
            normalize_date(
                raw_value
            ),
            None,
        )

    if field_name in NAME_FIELDS:

        return (
            normalize_name(
                raw_value
            ),
            None,
        )

    if field_name in LOCATION_FIELDS:

        return (
            normalize_location(
                raw_value
            ),
            None,
        )

    if field_name in IDENTIFIER_FIELDS:

        return (
            normalize_identifier(
                raw_value
            ),
            None,
        )

    if field_name == "plot_area":

        return normalize_area(
            raw_value
        )

    if field_name == "ownership_share":

        return (
            normalize_share(
                raw_value
            ),
            None,
        )

    return (
        normalize_text_value(
            raw_value
        ),
        None,
    )


# ============================================================
# NORMALIZE FIELD OBJECT
# ============================================================

def normalize_field(
    field_name: str,
    field_result: Dict[str, Any],
) -> Dict[str, Any]:

    """
    Preserve Extraction evidence while adding normalized output.
    """

    result = copy.deepcopy(
        field_result
    )

    raw_value = field_result.get(
        "value"
    )

    normalized_value, structured_value = (
        normalize_field_value(
            field_name,
            raw_value,
        )
    )

    # Preserve exactly what Extraction produced.
    result["raw_value"] = raw_value

    # Do NOT replace Extraction's value.
    result["normalized_value"] = (
        normalized_value
    )

    if structured_value is not None:

        result["structured_value"] = (
            structured_value
        )

    else:

        result["structured_value"] = None

    result["normalization_status"] = (
        "normalized"
        if normalized_value is not None
        else "missing"
    )

    return result


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def normalize_extraction(
    extraction_result: Dict[str, Any],
) -> Dict[str, Any]:

    """
    Normalize an Extraction V1.1 result.

    Extraction evidence is preserved.
    """

    if not isinstance(
        extraction_result,
        dict,
    ):
        raise TypeError(
            "extraction_result must be a dictionary"
        )

    fields = extraction_result.get(
        "fields"
    )

    if not isinstance(fields, dict):

        raise ValueError(
            "extraction_result['fields'] must be a dictionary"
        )

    normalized_fields = {}

    for field_name, field_result in fields.items():

        if not isinstance(
            field_result,
            dict,
        ):
            continue

        normalized_fields[field_name] = (
            normalize_field(
                field_name,
                field_result,
            )
        )

    total_fields = len(
        normalized_fields
    )

    normalized_count = sum(
        1
        for field in normalized_fields.values()
        if field.get(
            "normalized_value"
        ) is not None
    )

    missing_count = (
        total_fields
        - normalized_count
    )

    changed_count = sum(
        1
        for field in normalized_fields.values()
        if (
            field.get("raw_value")
            is not None
            and field.get("normalized_value")
            != field.get("raw_value")
        )
    )

    return {
        "normalization_version": (
            NORMALIZATION_VERSION
        ),

        "source_extraction_version": (
            extraction_result.get(
                "extraction_version"
            )
        ),

        "document_id": (
            extraction_result.get(
                "document_id"
            )
        ),

        "summary": {
            "total_fields": (
                total_fields
            ),

            "normalized_fields": (
                normalized_count
            ),

            "missing_fields": (
                missing_count
            ),

            "changed_fields": (
                changed_count
            ),
        },

        "fields": normalized_fields,
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "Normalization V1.0 module loaded successfully."
    )