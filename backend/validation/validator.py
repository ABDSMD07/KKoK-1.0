"""
===========================================================
PS 26018 - Land Record Intelligence System
Validation V1.0

Purpose:
    Validate normalized land-record fields structurally,
    syntactically, and through conservative cross-field rules.

Pipeline:

    Extraction V1.1
          ↓
    Normalization V1.0
          ↓
    Validation V1.0
          ↓
       Confidence
          ↓
    Human Verification

Validation DOES:
    - structural validation
    - field-format validation
    - missing-value detection
    - suspicious-value detection
    - conservative cross-field checks
    - issue reporting
    - preserve normalization/extraction evidence

Validation DOES NOT:
    - OCR / HTR
    - extraction
    - normalization
    - OCR correction
    - guess missing values
    - calculate confidence
    - perform duplicate detection
    - access databases
===========================================================
"""

import copy
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


VALIDATION_VERSION = "1.0"


# ============================================================
# VALIDATION STATUSES
# ============================================================

STATUS_VALID = "valid"
STATUS_WARNING = "warning"
STATUS_INVALID = "invalid"
STATUS_MISSING = "missing"
STATUS_NOT_CHECKED = "not_checked"

VALID_STATUSES = {
    STATUS_VALID,
    STATUS_WARNING,
    STATUS_INVALID,
    STATUS_MISSING,
    STATUS_NOT_CHECKED,
}


# ============================================================
# ISSUE SEVERITIES
# ============================================================

SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"


# ============================================================
# EXPECTED FIELDS
# ============================================================

EXPECTED_FIELDS = (
    "owner_name",
    "father_name",
    "address",
    "village",
    "tehsil",
    "district",
    "survey_number",
    "khasra_number",
    "khata_number",
    "plot_area",
    "land_classification",
    "serial_number",
    "ownership_owner_name",
    "ownership_share",
    "nature_of_rights",
    "mutation_entry_number",
    "mutation_date",
    "mutation_type",
    "registered_document_number",
    "sub_registrar_office",
    "registration_date",
)


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


LAND_IDENTIFIER_FIELDS = {
    "survey_number",
    "khasra_number",
    "khata_number",
}


GENERAL_IDENTIFIER_FIELDS = {
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
# EXPECTED NORMALIZED FIELD METADATA
# ============================================================

EXPECTED_FIELD_KEYS = (
    "field",
    "value",
    "status",
    "confidence",
    "section",
    "source_text",
    "source_line_ids",
    "source_page",
    "evidence_type",
    "matched_label",
    "raw_value",
    "normalized_value",
    "structured_value",
    "normalization_status",
)


# ============================================================
# PATTERNS
# ============================================================

ISO_DATE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}$"
)

LAND_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9]+"
    r"(?:[/-][A-Za-z0-9]+)*$"
)

GENERAL_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9]+"
    r"(?:[./_-][A-Za-z0-9]+)*$"
)

SHARE_PATTERN = re.compile(
    r"^(?P<numerator>\d+)"
    r"/"
    r"(?P<denominator>\d+)"
    r"(?:\s*\([^()]+\))?$"
)

NUMBER_PATTERN = re.compile(
    r"^\d+(?:\.\d+)?$"
)


# ============================================================
# RECOGNIZED AREA UNITS
# ============================================================

RECOGNIZED_AREA_UNITS = {
    "acre",
    "hectare",
    "square_meter",
}


# ============================================================
# ISSUE CREATION
# ============================================================

def make_issue(
    code: str,
    severity: str,
    message: str,
    field: Optional[str] = None,
    scope: str = "field",
) -> Dict[str, Any]:

    return {
        "code": code,
        "severity": severity,
        "message": message,
        "field": field,
        "scope": scope,
    }


# ============================================================
# STATUS FROM ISSUES
# ============================================================

def status_from_issues(
    issues: List[Dict[str, Any]],
    missing: bool = False,
) -> str:

    if missing:
        return STATUS_MISSING

    if any(
        issue.get("severity") == SEVERITY_ERROR
        for issue in issues
    ):
        return STATUS_INVALID

    if any(
        issue.get("severity") == SEVERITY_WARNING
        for issue in issues
    ):
        return STATUS_WARNING

    return STATUS_VALID


# ============================================================
# VALUE HELPERS
# ============================================================

def _value_is_missing(
    value: Any,
) -> bool:

    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def _contains_letter(
    value: str,
) -> bool:
    """
    Unicode-friendly approximation.

    str.isalpha() works for Latin and Indic letters.
    """

    return any(
        character.isalpha()
        for character in value
    )


def _alphanumeric_count(
    value: str,
) -> int:

    return sum(
        character.isalnum()
        for character in value
    )


# ============================================================
# NAME VALIDATION
# ============================================================

def validate_name(
    field_name: str,
    value: str,
) -> List[Dict[str, Any]]:

    issues = []

    if not _contains_letter(value):

        issues.append(
            make_issue(
                code="NAME_NO_LETTERS",
                severity=SEVERITY_ERROR,
                message=(
                    "Name does not contain alphabetic characters."
                ),
                field=field_name,
            )
        )

        return issues

    if _alphanumeric_count(value) < 2:

        issues.append(
            make_issue(
                code="NAME_TOO_SHORT",
                severity=SEVERITY_WARNING,
                message=(
                    "Name is unusually short."
                ),
                field=field_name,
            )
        )

    if re.search(
        r"[<>{}\[\]|]",
        value,
    ):

        issues.append(
            make_issue(
                code="NAME_SUSPICIOUS_CHARACTERS",
                severity=SEVERITY_WARNING,
                message=(
                    "Name contains unusual characters."
                ),
                field=field_name,
            )
        )

    return issues


# ============================================================
# LOCATION VALIDATION
# ============================================================

def validate_location(
    field_name: str,
    value: str,
) -> List[Dict[str, Any]]:

    issues = []

    if not _contains_letter(value):

        issues.append(
            make_issue(
                code="LOCATION_NO_LETTERS",
                severity=SEVERITY_ERROR,
                message=(
                    "Location does not contain alphabetic characters."
                ),
                field=field_name,
            )
        )

        return issues

    letters = [
        character.lower()
        for character in value
        if character.isalpha()
    ]

    # Conservative OCR-suspicion heuristic.
    #
    # Example:
    #     eee
    #
    # This is only a warning. It does NOT attempt to determine
    # the correct district.
    if (
        len(letters) >= 3
        and len(set(letters)) == 1
    ):

        issues.append(
            make_issue(
                code="LOCATION_REPEATED_CHARACTER",
                severity=SEVERITY_WARNING,
                message=(
                    "Location contains an unusually repeated "
                    "single character and may be OCR noise."
                ),
                field=field_name,
            )
        )

    if len(letters) == 1:

        issues.append(
            make_issue(
                code="LOCATION_TOO_SHORT",
                severity=SEVERITY_WARNING,
                message=(
                    "Location is unusually short."
                ),
                field=field_name,
            )
        )

    return issues


# ============================================================
# TEXT VALIDATION
# ============================================================

def validate_text(
    field_name: str,
    value: str,
) -> List[Dict[str, Any]]:

    issues = []

    if _alphanumeric_count(value) == 0:

        issues.append(
            make_issue(
                code="TEXT_NO_CONTENT",
                severity=SEVERITY_ERROR,
                message=(
                    "Text contains no alphanumeric content."
                ),
                field=field_name,
            )
        )

    return issues


# ============================================================
# DATE VALIDATION
# ============================================================

def validate_date(
    field_name: str,
    value: str,
) -> List[Dict[str, Any]]:

    issues = []

    if not ISO_DATE_PATTERN.fullmatch(
        value
    ):

        issues.append(
            make_issue(
                code="DATE_INVALID_FORMAT",
                severity=SEVERITY_ERROR,
                message=(
                    "Date must use normalized YYYY-MM-DD format."
                ),
                field=field_name,
            )
        )

        return issues

    try:

        datetime.strptime(
            value,
            "%Y-%m-%d",
        )

    except ValueError:

        issues.append(
            make_issue(
                code="DATE_INVALID_CALENDAR_DATE",
                severity=SEVERITY_ERROR,
                message=(
                    "Date is not a valid calendar date."
                ),
                field=field_name,
            )
        )

    return issues


# ============================================================
# LAND IDENTIFIER VALIDATION
# ============================================================

def validate_land_identifier(
    field_name: str,
    value: str,
) -> List[Dict[str, Any]]:

    issues = []

    if not LAND_IDENTIFIER_PATTERN.fullmatch(
        value
    ):

        issues.append(
            make_issue(
                code="LAND_IDENTIFIER_INVALID_FORMAT",
                severity=SEVERITY_ERROR,
                message=(
                    "Land identifier contains an invalid structure."
                ),
                field=field_name,
            )
        )

    return issues


# ============================================================
# GENERAL IDENTIFIER VALIDATION
# ============================================================

def validate_general_identifier(
    field_name: str,
    value: str,
) -> List[Dict[str, Any]]:

    issues = []

    if not GENERAL_IDENTIFIER_PATTERN.fullmatch(
        value
    ):

        issues.append(
            make_issue(
                code="IDENTIFIER_INVALID_FORMAT",
                severity=SEVERITY_ERROR,
                message=(
                    "Identifier contains an invalid structure."
                ),
                field=field_name,
            )
        )

    return issues


# ============================================================
# AREA VALIDATION
# ============================================================

def validate_area(
    field_name: str,
    normalized_value: str,
    structured_value: Any,
) -> List[Dict[str, Any]]:

    issues = []

    if not isinstance(
        structured_value,
        dict,
    ):

        issues.append(
            make_issue(
                code="AREA_STRUCTURE_MISSING",
                severity=SEVERITY_ERROR,
                message=(
                    "Area does not contain normalized numeric/unit "
                    "structure."
                ),
                field=field_name,
            )
        )

        return issues

    number = structured_value.get(
        "value"
    )

    unit = structured_value.get(
        "unit"
    )

    if (
        not isinstance(number, str)
        or not NUMBER_PATTERN.fullmatch(number)
    ):

        issues.append(
            make_issue(
                code="AREA_INVALID_NUMBER",
                severity=SEVERITY_ERROR,
                message=(
                    "Area does not contain a valid numeric value."
                ),
                field=field_name,
            )
        )

    else:

        try:

            numeric_value = float(
                number
            )

            if numeric_value <= 0:

                issues.append(
                    make_issue(
                        code="AREA_NON_POSITIVE",
                        severity=SEVERITY_ERROR,
                        message=(
                            "Area must be greater than zero."
                        ),
                        field=field_name,
                    )
                )

        except ValueError:

            issues.append(
                make_issue(
                    code="AREA_INVALID_NUMBER",
                    severity=SEVERITY_ERROR,
                    message=(
                        "Area numeric value cannot be parsed."
                    ),
                    field=field_name,
                )
            )

    if unit is None:

        issues.append(
            make_issue(
                code="AREA_UNIT_MISSING",
                severity=SEVERITY_WARNING,
                message=(
                    "Area value does not include a unit."
                ),
                field=field_name,
            )
        )

    elif unit not in RECOGNIZED_AREA_UNITS:

        issues.append(
            make_issue(
                code="AREA_UNIT_UNKNOWN",
                severity=SEVERITY_ERROR,
                message=(
                    f"Unrecognized area unit: {unit!r}."
                ),
                field=field_name,
            )
        )

    return issues


# ============================================================
# OWNERSHIP SHARE VALIDATION
# ============================================================

def validate_share(
    field_name: str,
    value: str,
) -> List[Dict[str, Any]]:

    issues = []

    match = SHARE_PATTERN.fullmatch(
        value
    )

    if not match:

        issues.append(
            make_issue(
                code="SHARE_INVALID_FORMAT",
                severity=SEVERITY_ERROR,
                message=(
                    "Ownership share must use a fraction such as "
                    "'1/1' or '1/2', optionally followed by text "
                    "in parentheses."
                ),
                field=field_name,
            )
        )

        return issues

    numerator = int(
        match.group("numerator")
    )

    denominator = int(
        match.group("denominator")
    )

    if denominator == 0:

        issues.append(
            make_issue(
                code="SHARE_ZERO_DENOMINATOR",
                severity=SEVERITY_ERROR,
                message=(
                    "Ownership share denominator cannot be zero."
                ),
                field=field_name,
            )
        )

        return issues

    if numerator == 0:

        issues.append(
            make_issue(
                code="SHARE_ZERO_NUMERATOR",
                severity=SEVERITY_WARNING,
                message=(
                    "Ownership share numerator is zero."
                ),
                field=field_name,
            )
        )

    if numerator > denominator:

        issues.append(
            make_issue(
                code="SHARE_EXCEEDS_WHOLE",
                severity=SEVERITY_WARNING,
                message=(
                    "Ownership share numerator exceeds denominator."
                ),
                field=field_name,
            )
        )

    return issues


# ============================================================
# FIELD DISPATCH
# ============================================================

def validate_field_value(
    field_name: str,
    field_result: Dict[str, Any],
) -> Tuple[
    str,
    List[Dict[str, Any]],
]:

    value = field_result.get(
        "normalized_value"
    )

    # Missing is a first-class status, not invalid.
    if _value_is_missing(value):

        issue = make_issue(
            code="FIELD_MISSING",
            severity=SEVERITY_WARNING,
            message=(
                "Field has no normalized value."
            ),
            field=field_name,
        )

        return (
            STATUS_MISSING,
            [issue],
        )

    value = str(value)

    issues: List[
        Dict[str, Any]
    ] = []

    if field_name in NAME_FIELDS:

        issues.extend(
            validate_name(
                field_name,
                value,
            )
        )

    elif field_name in LOCATION_FIELDS:

        issues.extend(
            validate_location(
                field_name,
                value,
            )
        )

    elif field_name in DATE_FIELDS:

        issues.extend(
            validate_date(
                field_name,
                value,
            )
        )

    elif field_name in LAND_IDENTIFIER_FIELDS:

        issues.extend(
            validate_land_identifier(
                field_name,
                value,
            )
        )

    elif field_name in GENERAL_IDENTIFIER_FIELDS:

        issues.extend(
            validate_general_identifier(
                field_name,
                value,
            )
        )

    elif field_name == "plot_area":

        issues.extend(
            validate_area(
                field_name,
                value,
                field_result.get(
                    "structured_value"
                ),
            )
        )

    elif field_name == "ownership_share":

        issues.extend(
            validate_share(
                field_name,
                value,
            )
        )

    elif field_name in TEXT_FIELDS:

        issues.extend(
            validate_text(
                field_name,
                value,
            )
        )

    else:

        return (
            STATUS_NOT_CHECKED,
            [],
        )

    return (
        status_from_issues(
            issues
        ),
        issues,
    )


# ============================================================
# STRUCTURAL VALIDATION
# ============================================================

def validate_structure(
    normalization_result: Dict[str, Any],
) -> List[Dict[str, Any]]:

    issues = []

    expected_top_level = (
        "normalization_version",
        "source_extraction_version",
        "document_id",
        "summary",
        "fields",
    )

    for key in expected_top_level:

        if key not in normalization_result:

            issues.append(
                make_issue(
                    code="STRUCTURE_MISSING_TOP_LEVEL_KEY",
                    severity=SEVERITY_ERROR,
                    message=(
                        f"Normalization result is missing "
                        f"top-level key {key!r}."
                    ),
                    field=None,
                    scope="structure",
                )
            )

    fields = normalization_result.get(
        "fields"
    )

    if not isinstance(fields, dict):

        issues.append(
            make_issue(
                code="STRUCTURE_INVALID_FIELDS",
                severity=SEVERITY_ERROR,
                message=(
                    "'fields' must be a dictionary."
                ),
                field=None,
                scope="structure",
            )
        )

        return issues

    for expected_field in EXPECTED_FIELDS:

        if expected_field not in fields:

            issues.append(
                make_issue(
                    code="STRUCTURE_FIELD_ABSENT",
                    severity=SEVERITY_ERROR,
                    message=(
                        f"Expected field {expected_field!r} "
                        f"is absent from normalization output."
                    ),
                    field=expected_field,
                    scope="structure",
                )
            )

    for field_name, field_result in fields.items():

        if not isinstance(
            field_result,
            dict,
        ):

            issues.append(
                make_issue(
                    code="STRUCTURE_INVALID_FIELD_OBJECT",
                    severity=SEVERITY_ERROR,
                    message=(
                        f"Field {field_name!r} must be a dictionary."
                    ),
                    field=field_name,
                    scope="structure",
                )
            )

            continue

        for key in EXPECTED_FIELD_KEYS:

            if key not in field_result:

                issues.append(
                    make_issue(
                        code="STRUCTURE_MISSING_FIELD_METADATA",
                        severity=SEVERITY_ERROR,
                        message=(
                            f"Field {field_name!r} is missing "
                            f"metadata key {key!r}."
                        ),
                        field=field_name,
                        scope="structure",
                    )
                )

        declared_name = field_result.get(
            "field"
        )

        if (
            declared_name is not None
            and declared_name != field_name
        ):

            issues.append(
                make_issue(
                    code="STRUCTURE_FIELD_NAME_MISMATCH",
                    severity=SEVERITY_ERROR,
                    message=(
                        f"Dictionary key {field_name!r} does not "
                        f"match field metadata {declared_name!r}."
                    ),
                    field=field_name,
                    scope="structure",
                )
            )

        line_ids = field_result.get(
            "source_line_ids"
        )

        if (
            line_ids is not None
            and not isinstance(
                line_ids,
                list,
            )
        ):

            issues.append(
                make_issue(
                    code="STRUCTURE_INVALID_SOURCE_LINE_IDS",
                    severity=SEVERITY_ERROR,
                    message=(
                        "'source_line_ids' must be a list."
                    ),
                    field=field_name,
                    scope="structure",
                )
            )

    return issues


# ============================================================
# CROSS-FIELD HELPERS
# ============================================================

def _get_valid_date(
    fields: Dict[str, Dict[str, Any]],
    field_name: str,
) -> Optional[datetime]:

    field = fields.get(
        field_name
    )

    if not isinstance(field, dict):
        return None

    value = field.get(
        "normalized_value"
    )

    if not isinstance(value, str):
        return None

    if not ISO_DATE_PATTERN.fullmatch(
        value
    ):
        return None

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%d",
        )

    except ValueError:

        return None


# ============================================================
# CROSS-FIELD VALIDATION
# ============================================================

def validate_cross_fields(
    fields: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:

    issues = []

    mutation_date = _get_valid_date(
        fields,
        "mutation_date",
    )

    registration_date = _get_valid_date(
        fields,
        "registration_date",
    )

    # This is intentionally only a warning.
    #
    # Different land-record workflows can legitimately produce
    # different event ordering. We flag the relationship for
    # review rather than declaring either field invalid.
    if (
        mutation_date is not None
        and registration_date is not None
        and registration_date < mutation_date
    ):

        issues.append(
            make_issue(
                code="DATE_ORDER_REVIEW",
                severity=SEVERITY_WARNING,
                message=(
                    "Registration date is earlier than mutation "
                    "date. Review the document chronology."
                ),
                field=None,
                scope="cross_field",
            )
        )

    return issues


# ============================================================
# ATTACH CROSS-FIELD WARNINGS
# ============================================================

def apply_cross_field_status(
    fields: Dict[str, Dict[str, Any]],
    cross_issues: List[Dict[str, Any]],
) -> None:

    """
    Cross-field issues without a single responsible field remain
    document-level issues and do not arbitrarily invalidate a field.

    If a later rule names a specific field, its warning can be
    attached here.
    """

    for issue in cross_issues:

        field_name = issue.get(
            "field"
        )

        if not field_name:
            continue

        field = fields.get(
            field_name
        )

        if not isinstance(field, dict):
            continue

        validation_issues = field.setdefault(
            "validation_issues",
            [],
        )

        validation_issues.append(
            copy.deepcopy(issue)
        )

        current_status = field.get(
            "validation_status"
        )

        if (
            issue.get("severity")
            == SEVERITY_ERROR
        ):

            field[
                "validation_status"
            ] = STATUS_INVALID

        elif (
            current_status == STATUS_VALID
            and issue.get("severity")
            == SEVERITY_WARNING
        ):

            field[
                "validation_status"
            ] = STATUS_WARNING


# ============================================================
# MAIN VALIDATOR
# ============================================================

def validate_normalization(
    normalization_result: Dict[str, Any],
) -> Dict[str, Any]:

    if not isinstance(
        normalization_result,
        dict,
    ):

        raise TypeError(
            "normalization_result must be a dictionary"
        )

    # --------------------------------------------------------
    # STRUCTURAL VALIDATION
    # --------------------------------------------------------

    structural_issues = (
        validate_structure(
            normalization_result
        )
    )

    source_fields = (
        normalization_result.get(
            "fields"
        )
    )

    if not isinstance(
        source_fields,
        dict,
    ):
        source_fields = {}

    # Deep-copy so Validation never mutates Normalization output.
    validated_fields = copy.deepcopy(
        source_fields
    )

    all_issues = list(
        structural_issues
    )

    # --------------------------------------------------------
    # FIELD VALIDATION
    # --------------------------------------------------------

    for field_name in EXPECTED_FIELDS:

        field_result = (
            validated_fields.get(
                field_name
            )
        )

        if not isinstance(
            field_result,
            dict,
        ):
            continue

        validation_status, issues = (
            validate_field_value(
                field_name,
                field_result,
            )
        )

        field_result[
            "validation_status"
        ] = validation_status

        field_result[
            "validation_issues"
        ] = copy.deepcopy(
            issues
        )

        all_issues.extend(
            copy.deepcopy(
                issues
            )
        )

    # Unknown fields are preserved but not silently validated.
    for field_name, field_result in (
        validated_fields.items()
    ):

        if field_name in EXPECTED_FIELDS:
            continue

        if not isinstance(
            field_result,
            dict,
        ):
            continue

        field_result[
            "validation_status"
        ] = STATUS_NOT_CHECKED

        field_result[
            "validation_issues"
        ] = []

    # --------------------------------------------------------
    # CROSS-FIELD VALIDATION
    # --------------------------------------------------------

    cross_field_issues = (
        validate_cross_fields(
            validated_fields
        )
    )

    apply_cross_field_status(
        validated_fields,
        cross_field_issues,
    )

    all_issues.extend(
        copy.deepcopy(
            cross_field_issues
        )
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    status_counts = {
        STATUS_VALID: 0,
        STATUS_WARNING: 0,
        STATUS_INVALID: 0,
        STATUS_MISSING: 0,
        STATUS_NOT_CHECKED: 0,
    }

    for field_result in (
        validated_fields.values()
    ):

        if not isinstance(
            field_result,
            dict,
        ):
            continue

        status = field_result.get(
            "validation_status",
            STATUS_NOT_CHECKED,
        )

        if status not in status_counts:
            status = STATUS_NOT_CHECKED

        status_counts[status] += 1

    error_count = sum(
        1
        for issue in all_issues
        if issue.get("severity")
        == SEVERITY_ERROR
    )

    warning_count = sum(
        1
        for issue in all_issues
        if issue.get("severity")
        == SEVERITY_WARNING
    )

    structural_error_count = sum(
        1
        for issue in structural_issues
        if issue.get("severity")
        == SEVERITY_ERROR
    )

    return {
        "validation_version": (
            VALIDATION_VERSION
        ),

        "source_normalization_version": (
            normalization_result.get(
                "normalization_version"
            )
        ),

        "source_extraction_version": (
            normalization_result.get(
                "source_extraction_version"
            )
        ),

        "document_id": (
            normalization_result.get(
                "document_id"
            )
        ),

        "structurally_valid": (
            structural_error_count == 0
        ),

        "summary": {
            "total_fields": len(
                validated_fields
            ),

            "valid_fields": status_counts[
                STATUS_VALID
            ],

            "warning_fields": status_counts[
                STATUS_WARNING
            ],

            "invalid_fields": status_counts[
                STATUS_INVALID
            ],

            "missing_fields": status_counts[
                STATUS_MISSING
            ],

            "not_checked_fields": status_counts[
                STATUS_NOT_CHECKED
            ],

            "issue_count": len(
                all_issues
            ),

            "error_count": error_count,

            "warning_count": warning_count,
        },

        "fields": validated_fields,

        "issues": all_issues,

        "structural_issues": (
            structural_issues
        ),

        "cross_field_issues": (
            cross_field_issues
        ),
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "Validation V1.0 module loaded successfully."
    )