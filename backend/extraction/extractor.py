"""
===========================================================
PS 26018 - Land Record Intelligence System
Extraction V1.1

Evidence priority:

    1. Layout relationships
    2. Layout lines / spatial structure
    3. Layout tables
    4. Composer text fallback
    5. OCR fallback

Extraction DOES NOT:
    - perform OCR
    - correct OCR text
    - validate semantic correctness
    - calculate confidence
    - invent missing values
===========================================================
"""

import re
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# SECTIONS
# ============================================================

SECTION_NAMES = (
    "LANDOWNER DETAILS",
    "LAND IDENTIFICATION",
    "LAND CHARACTERISTICS",
    "OWNERSHIP DETAILS",
    "MUTATION RECORDS",
    "REGISTRATION INFORMATION",
)


# ============================================================
# FIELD DEFINITIONS
# ============================================================

FIELD_DEFINITIONS = {

    # LANDOWNER DETAILS
    "owner_name": {
        "section": "LANDOWNER DETAILS",
        "labels": (
            "owner name",
            "name",
        ),
    },

    "father_name": {
        "section": "LANDOWNER DETAILS",
        "labels": (
            "father's name",
            "father name",
        ),
    },

    "address": {
        "section": "LANDOWNER DETAILS",
        "labels": (
            "address",
        ),
    },

    # LAND IDENTIFICATION
    "village": {
        "section": "LAND IDENTIFICATION",
        "labels": (
            "village",
        ),
    },

    "tehsil": {
        "section": "LAND IDENTIFICATION",
        "labels": (
            "tehsil",
            "tahsil",
        ),
    },

    "district": {
        "section": "LAND IDENTIFICATION",
        "labels": (
            "district",
        ),
    },

    "survey_number": {
        "section": "LAND IDENTIFICATION",
        "labels": (
            "survey number",
            "survey no",
        ),
    },

    "khasra_number": {
        "section": "LAND IDENTIFICATION",
        "labels": (
            "khasra number",
            "khasra no",
            "khssra number",
        ),
    },

    "khata_number": {
        "section": "LAND IDENTIFICATION",
        "labels": (
            "khata number",
            "khata no",
            "account number",
            "account no",
        ),
    },

    # LAND CHARACTERISTICS
    "plot_area": {
        "section": "LAND CHARACTERISTICS",
        "labels": (
            "plot area",
        ),
    },

    "land_classification": {
        "section": "LAND CHARACTERISTICS",
        "labels": (
            "land classification",
            "classification",
        ),
    },

    # OWNERSHIP DETAILS
    "serial_number": {
        "section": "OWNERSHIP DETAILS",
        "labels": (
            "serial number",
            "serial no",
            "sr no",
            "s no",
        ),
    },

    "ownership_owner_name": {
        "section": "OWNERSHIP DETAILS",
        "labels": (
            "owner name",
        ),
    },

    "ownership_share": {
        "section": "OWNERSHIP DETAILS",
        "labels": (
            "ownership share",
            "share",
        ),
    },

    "nature_of_rights": {
        "section": "OWNERSHIP DETAILS",
        "labels": (
            "nature of rights",
            "nature of right",
        ),
    },

    # MUTATION RECORDS
    "mutation_entry_number": {
        "section": "MUTATION RECORDS",
        "labels": (
            "latest mutation entry number",
            "latest mutation entry no",
            "mutation entry number",
            "mutation entry no",
        ),
    },

    "mutation_date": {
        "section": "MUTATION RECORDS",
        "labels": (
            "mutation date",
            "date",
        ),
    },

    "mutation_type": {
        "section": "MUTATION RECORDS",
        "labels": (
            "mutation type",
            "type",
        ),
    },

    # REGISTRATION INFORMATION
    "registered_document_number": {
        "section": "REGISTRATION INFORMATION",
        "labels": (
            "registered document number",
            "registered document no",
            "document number",
            "document no",
        ),
    },

    "sub_registrar_office": {
        "section": "REGISTRATION INFORMATION",
        "labels": (
            "sub registrar office",
            "sub-registrar office",
            "sub registrar",
        ),
    },

    "registration_date": {
        "section": "REGISTRATION INFORMATION",
        "labels": (
            "registration date",
            "date",
        ),
    },
}


# ============================================================
# LAYOUT V1.2 ADAPTER
# ============================================================

def get_layout_lines(
    layout_result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Layout V1.2 adapter.

    Change only this function if the actual Layout schema
    stores lines somewhere else.
    """

    lines = layout_result.get("lines", [])

    if not isinstance(lines, list):
        return []

    return [
        line
        for line in lines
        if isinstance(line, dict)
    ]


def get_layout_relationships(
    layout_result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Layout V1.2 relationship adapter.
    """

    relationships = layout_result.get(
        "relationships",
        [],
    )

    if not isinstance(relationships, list):
        return []

    return [
        relationship
        for relationship in relationships
        if isinstance(relationship, dict)
    ]


def get_layout_tables(
    layout_result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Layout V1.2 table adapter.
    """

    tables = layout_result.get("tables", [])

    if not isinstance(tables, list):
        return []

    return [
        table
        for table in tables
        if isinstance(table, dict)
    ]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(value: Any) -> str:

    if value is None:
        return ""

    text = str(value)

    text = text.replace("’", "'")
    text = text.replace("‘", "'")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def clean_value(value: Any) -> str:

    if value is None:
        return ""

    value = str(value)

    value = re.sub(
        r"^[\s:;|,=/\\\-]+",
        "",
        value,
    )

    value = re.sub(
        r"[\s;|]+$",
        "",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ============================================================
# LABEL REGEX
# ============================================================

def make_label_pattern(
    label: str,
) -> re.Pattern:

    """
    Allows OCR / Composer separators between label words.

    Example:

        Registered Document | No.
        Registered Document No
        Registered-Document-No

    can all match "registered document no".
    """

    parts = re.findall(
        r"[A-Za-z0-9]+",
        label,
    )

    if not parts:
        return re.compile(r"(?!x)x")

    separator = r"[\s._:/|,\-]*"

    regex = r"\b"

    regex += separator.join(
        re.escape(part)
        for part in parts
    )

    regex += r"\.?\b"

    return re.compile(
        regex,
        re.IGNORECASE,
    )


ALL_LABELS = sorted(
    {
        label
        for definition in FIELD_DEFINITIONS.values()
        for label in definition["labels"]
    },
    key=len,
    reverse=True,
)


LABEL_PATTERNS = {
    label: make_label_pattern(label)
    for label in ALL_LABELS
}


# ============================================================
# SECTION DETECTION
# ============================================================

def detect_section(
    text: Any,
) -> Optional[str]:

    normalized = normalize_text(text)

    if not normalized:
        return None

    for section in SECTION_NAMES:

        section_normalized = normalize_text(
            section
        )

        if section_normalized in normalized:
            return section

    return None


# ============================================================
# LABEL MATCHING
# ============================================================

def find_label(
    text: str,
    labels: Tuple[str, ...],
) -> Optional[Tuple[str, re.Match]]:

    matches = []

    for label in labels:

        pattern = LABEL_PATTERNS[label]

        match = pattern.search(text)

        if match:

            matches.append(
                (
                    match.start(),
                    -len(label),
                    label,
                    match,
                )
            )

    if not matches:
        return None

    matches.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    _, _, label, match = matches[0]

    return label, match


def find_next_label_position(
    text: str,
    start: int,
) -> Optional[int]:

    positions = []

    for pattern in LABEL_PATTERNS.values():

        match = pattern.search(
            text,
            start,
        )

        if match:
            positions.append(
                match.start()
            )

    if not positions:
        return None

    return min(positions)


# ============================================================
# VALUE BOUNDARY EXTRACTION
# ============================================================

def value_after_label(
    text: str,
    labels: Tuple[str, ...],
) -> Optional[Tuple[str, str]]:

    result = find_label(
        text,
        labels,
    )

    if result is None:
        return None

    label, match = result

    value_start = match.end()

    next_label = find_next_label_position(
        text,
        value_start,
    )

    if next_label is None:

        value = text[value_start:]

    else:

        value = text[
            value_start:next_label
        ]

    value = clean_value(value)

    if not value:
        return None

    return label, value


# ============================================================
# FIELD PARSERS
# ============================================================

DATE_PATTERN = re.compile(
    r"\b\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{4}\b"
)

LAND_NUMBER_PATTERN = re.compile(
    r"\b\d+(?:[\/\-][A-Za-z0-9]+)*\b"
)

DOCUMENT_NUMBER_PATTERN = re.compile(
    r"\b[A-Za-z0-9\-]+\/\d{4}\b"
)

AREA_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?"
    r"(?:\s*(?:"
    r"acres?|"
    r"hectares?|"
    r"ha|"
    r"sq\.?\s*m|"
    r"sqm"
    r"))?",
    re.IGNORECASE,
)


def parse_field_value(
    field_name: str,
    raw_value: Any,
) -> Optional[str]:

    value = clean_value(raw_value)

    if not value:
        return None

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if field_name in {
        "mutation_date",
        "registration_date",
    }:

        match = DATE_PATTERN.search(
            value
        )

        return (
            match.group(0)
            if match
            else None
        )

    # --------------------------------------------------------
    # LAND NUMBERS
    # --------------------------------------------------------

    if field_name in {
        "survey_number",
        "khasra_number",
        "khata_number",
    }:

        match = LAND_NUMBER_PATTERN.search(
            value
        )

        return (
            match.group(0)
            if match
            else None
        )

    # --------------------------------------------------------
    # MUTATION NUMBER
    # --------------------------------------------------------

    if field_name == "mutation_entry_number":

        match = re.search(
            r"\b\d+[A-Za-z0-9\/\-]*\b",
            value,
        )

        return (
            match.group(0)
            if match
            else None
        )

    # --------------------------------------------------------
    # REGISTERED DOCUMENT NUMBER
    # --------------------------------------------------------

    if field_name == "registered_document_number":

        match = DOCUMENT_NUMBER_PATTERN.search(
            value
        )

        if match:
            return match.group(0)

        match = re.search(
            r"\b\d{2,}\b",
            value,
        )

        return (
            match.group(0)
            if match
            else None
        )

    # --------------------------------------------------------
    # PLOT AREA
    # --------------------------------------------------------

    if field_name == "plot_area":

        match = AREA_PATTERN.search(
            value
        )

        return (
            clean_value(match.group(0))
            if match
            else None
        )

    return value


# ============================================================
# FIELD RESULT
# ============================================================

def make_field_result(
    field_name: str,
    value: Optional[str],
    section: str,
    source_text: Optional[str] = None,
    source_line_ids: Optional[List[Any]] = None,
    source_page: Optional[int] = None,
    evidence_type: Optional[str] = None,
    matched_label: Optional[str] = None,
) -> Dict[str, Any]:

    return {
        "field": field_name,

        "value": value,

        "status": (
            "extracted"
            if value
            else "missing"
        ),

        # Calculated later.
        "confidence": None,

        "section": section,

        "source_text": source_text,

        "source_line_ids": (
            source_line_ids or []
        ),

        "source_page": source_page,

        "evidence_type": evidence_type,

        "matched_label": matched_label,
    }


# ============================================================
# SAFE DICT TEXT
# ============================================================

def object_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):

        for key in (
            "text",
            "value",
            "content",
        ):

            candidate = value.get(key)

            if candidate is not None:
                return str(candidate).strip()

    return str(value).strip()


# ============================================================
# RELATIONSHIP EXTRACTION
# ============================================================

def extract_from_relationships(
    layout_result: Dict[str, Any],
    results: Dict[str, Dict[str, Any]],
) -> None:

    relationships = get_layout_relationships(
        layout_result
    )

    for relationship in relationships:

        key_text = object_text(
            relationship.get("key")
        )

        value_text = object_text(
            relationship.get("value")
        )

        # Alternative common Layout names.
        if not key_text:
            key_text = object_text(
                relationship.get("label")
            )

        if not value_text:
            value_text = object_text(
                relationship.get("value_text")
            )

        if not key_text or not value_text:
            continue

        relationship_section = detect_section(
            relationship.get("section")
        )

        for field_name, definition in FIELD_DEFINITIONS.items():

            if field_name in results:
                continue

            expected_section = definition[
                "section"
            ]

            if (
                relationship_section
                and relationship_section
                != expected_section
            ):
                continue

            match = find_label(
                key_text,
                definition["labels"],
            )

            if match is None:
                continue

            matched_label, _ = match

            parsed_value = parse_field_value(
                field_name,
                value_text,
            )

            if not parsed_value:
                continue

            line_ids = relationship.get(
                "source_line_ids",
                [],
            )

            if not isinstance(
                line_ids,
                list,
            ):
                line_ids = [line_ids]

            results[field_name] = (
                make_field_result(
                    field_name=field_name,
                    value=parsed_value,
                    section=expected_section,
                    source_text=(
                        f"{key_text} | {value_text}"
                    ),
                    source_line_ids=line_ids,
                    source_page=relationship.get(
                        "page_number"
                    ),
                    evidence_type=(
                        "layout_relationship"
                    ),
                    matched_label=matched_label,
                )
            )


# ============================================================
# CONVERT LAYOUT LINES
# ============================================================

def prepare_layout_lines(
    layout_result: Dict[str, Any],
) -> List[Dict[str, Any]]:

    prepared = []

    current_section = None

    lines = get_layout_lines(
        layout_result
    )

    for index, line in enumerate(lines):

        text = object_text(
            line.get("text")
        )

        if not text:
            continue

        explicit_section = detect_section(
            line.get("section")
        )

        heading_section = detect_section(
            text
        )

        if explicit_section:
            current_section = explicit_section

        elif heading_section:
            current_section = heading_section

        prepared.append({
            "line_id": line.get(
                "line_id",
                index,
            ),

            "text": text,

            "page_number": line.get(
                "page_number"
            ),

            "bbox": line.get(
                "bbox"
            ),

            "section": current_section,

            "is_section_heading": (
                heading_section is not None
            ),
        })

    return prepared


# ============================================================
# SAME-LINE EXTRACTION
# ============================================================

def extract_from_lines(
    lines: List[Dict[str, Any]],
    results: Dict[str, Dict[str, Any]],
    evidence_type: str,
) -> None:

    for index, line in enumerate(lines):

        text = line["text"]

        if line.get(
            "is_section_heading"
        ):
            continue

        section = line.get(
            "section"
        )

        for field_name, definition in FIELD_DEFINITIONS.items():

            if field_name in results:
                continue

            expected_section = definition[
                "section"
            ]

            if (
                section
                and section != expected_section
            ):
                continue

            candidate = value_after_label(
                text,
                definition["labels"],
            )

            if candidate is None:
                continue

            matched_label, raw_value = (
                candidate
            )

            parsed_value = parse_field_value(
                field_name,
                raw_value,
            )

            if not parsed_value:
                continue

            results[field_name] = (
                make_field_result(
                    field_name=field_name,
                    value=parsed_value,
                    section=expected_section,
                    source_text=text,
                    source_line_ids=[
                        line.get(
                            "line_id",
                            index,
                        )
                    ],
                    source_page=line.get(
                        "page_number"
                    ),
                    evidence_type=evidence_type,
                    matched_label=matched_label,
                )
            )


# ============================================================
# BELOW-LABEL EXTRACTION
# ============================================================

def extract_below_labels(
    lines: List[Dict[str, Any]],
    results: Dict[str, Dict[str, Any]],
) -> None:

    for index in range(
        len(lines) - 1
    ):

        line = lines[index]
        next_line = lines[index + 1]

        text = line["text"]

        for field_name, definition in FIELD_DEFINITIONS.items():

            if field_name in results:
                continue

            expected_section = definition[
                "section"
            ]

            section = line.get(
                "section"
            )

            if (
                section
                and section != expected_section
            ):
                continue

            label_match = find_label(
                text,
                definition["labels"],
            )

            if label_match is None:
                continue

            matched_label, match = (
                label_match
            )

            remainder = clean_value(
                text[
                    match.end():
                ]
            )

            # Label already has value.
            if remainder:
                continue

            # Do not cross pages.
            page1 = line.get(
                "page_number"
            )

            page2 = next_line.get(
                "page_number"
            )

            if (
                page1 is not None
                and page2 is not None
                and page1 != page2
            ):
                continue

            next_section = (
                next_line.get("section")
            )

            if (
                next_section
                and next_section
                != expected_section
            ):
                continue

            next_text = next_line[
                "text"
            ]

            # Never consume a section heading.
            if detect_section(next_text):
                continue

            # Never consume another label as a value.
            contains_label = False

            for label in ALL_LABELS:

                if LABEL_PATTERNS[
                    label
                ].search(next_text):

                    contains_label = True
                    break

            if contains_label:
                continue

            parsed_value = parse_field_value(
                field_name,
                next_text,
            )

            if not parsed_value:
                continue

            results[field_name] = (
                make_field_result(
                    field_name=field_name,
                    value=parsed_value,
                    section=expected_section,
                    source_text=(
                        f"{text} | {next_text}"
                    ),
                    source_line_ids=[
                        line.get(
                            "line_id",
                            index,
                        ),
                        next_line.get(
                            "line_id",
                            index + 1,
                        ),
                    ],
                    source_page=page1,
                    evidence_type=(
                        "layout_below_label"
                    ),
                    matched_label=matched_label,
                )
            )


# ============================================================
# TABLE EXTRACTION
# ============================================================

def _table_rows(
    table: Dict[str, Any],
) -> List[Any]:

    rows = table.get(
        "rows",
        []
    )

    if isinstance(rows, list):
        return rows

    return []


def _row_cells(
    row: Any,
) -> List[str]:

    if isinstance(row, list):

        return [
            object_text(cell)
            for cell in row
        ]

    if isinstance(row, dict):

        cells = row.get(
            "cells",
            []
        )

        if isinstance(cells, list):

            return [
                object_text(cell)
                for cell in cells
            ]

    return []


def extract_from_tables(
    layout_result: Dict[str, Any],
    results: Dict[str, Dict[str, Any]],
) -> None:

    """
    Conservative ownership-table extraction.

    Expected logical columns:

        Serial No
        Owner Name
        Share
        Nature of Rights

    The table must have >= 3 meaningful cells.
    """

    tables = get_layout_tables(
        layout_result
    )

    for table in tables:

        section = detect_section(
            table.get("section")
        )

        if (
            section
            and section
            != "OWNERSHIP DETAILS"
        ):
            continue

        for row_index, row in enumerate(
            _table_rows(table)
        ):

            cells = [
                clean_value(cell)
                for cell in _row_cells(row)
            ]

            cells = [
                cell
                for cell in cells
                if cell
            ]

            if len(cells) < 3:
                continue

            # Ignore obvious header rows.
            normalized_row = normalize_text(
                " ".join(cells)
            )

            header_terms = (
                "owner name",
                "nature of rights",
                "serial no",
            )

            if sum(
                term in normalized_row
                for term in header_terms
            ) >= 2:
                continue

            # -----------------------------------------------
            # SERIAL NUMBER
            # -----------------------------------------------

            if (
                "serial_number"
                not in results
            ):

                serial_match = re.fullmatch(
                    r"\d+",
                    cells[0],
                )

                if serial_match:

                    results[
                        "serial_number"
                    ] = make_field_result(
                        field_name=(
                            "serial_number"
                        ),
                        value=cells[0],
                        section=(
                            "OWNERSHIP DETAILS"
                        ),
                        source_text=(
                            " | ".join(cells)
                        ),
                        source_line_ids=[],
                        source_page=table.get(
                            "page_number"
                        ),
                        evidence_type=(
                            "layout_table"
                        ),
                        matched_label=(
                            "serial number"
                        ),
                    )

            # -----------------------------------------------
            # OWNER
            # -----------------------------------------------

            if (
                "ownership_owner_name"
                not in results
                and len(cells) >= 2
            ):

                results[
                    "ownership_owner_name"
                ] = make_field_result(
                    field_name=(
                        "ownership_owner_name"
                    ),
                    value=cells[1],
                    section=(
                        "OWNERSHIP DETAILS"
                    ),
                    source_text=(
                        " | ".join(cells)
                    ),
                    source_line_ids=[],
                    source_page=table.get(
                        "page_number"
                    ),
                    evidence_type=(
                        "layout_table"
                    ),
                    matched_label=(
                        "owner name"
                    ),
                )

            # -----------------------------------------------
            # SHARE
            # -----------------------------------------------

            if (
                "ownership_share"
                not in results
                and len(cells) >= 3
            ):

                share = cells[2]

                if re.search(
                    r"\d+\s*/\s*\d+",
                    share,
                ):

                    results[
                        "ownership_share"
                    ] = make_field_result(
                        field_name=(
                            "ownership_share"
                        ),
                        value=share,
                        section=(
                            "OWNERSHIP DETAILS"
                        ),
                        source_text=(
                            " | ".join(cells)
                        ),
                        source_line_ids=[],
                        source_page=table.get(
                            "page_number"
                        ),
                        evidence_type=(
                            "layout_table"
                        ),
                        matched_label="share",
                    )

            # -----------------------------------------------
            # NATURE OF RIGHTS
            # -----------------------------------------------

            if (
                "nature_of_rights"
                not in results
                and len(cells) >= 4
            ):

                rights = " | ".join(
                    cells[3:]
                )

                results[
                    "nature_of_rights"
                ] = make_field_result(
                    field_name=(
                        "nature_of_rights"
                    ),
                    value=rights,
                    section=(
                        "OWNERSHIP DETAILS"
                    ),
                    source_text=(
                        " | ".join(cells)
                    ),
                    source_line_ids=[],
                    source_page=table.get(
                        "page_number"
                    ),
                    evidence_type=(
                        "layout_table"
                    ),
                    matched_label=(
                        "nature of rights"
                    ),
                )


# ============================================================
# COMPOSER TEXT
# ============================================================

def prepare_text_lines(
    document_text: str,
) -> List[Dict[str, Any]]:

    result = []

    current_section = None

    line_id = 0

    for raw_line in document_text.splitlines():

        text = raw_line.strip()

        if not text:
            continue

        detected = detect_section(
            text
        )

        if detected:
            current_section = detected

        result.append({
            "line_id": line_id,

            "text": text,

            "page_number": None,

            "bbox": None,

            "section": current_section,

            "is_section_heading": (
                detected is not None
            ),
        })

        line_id += 1

    return result


# ============================================================
# OCR FALLBACK
# ============================================================

def prepare_ocr_lines(
    ocr_result: Dict[str, Any],
) -> List[Dict[str, Any]]:

    """
    Minimal OCR fallback.

    If OCR already provides line objects, use them.
    """

    result = []

    current_section = None

    line_id = 0

    for page in ocr_result.get(
        "pages",
        []
    ):

        page_number = page.get(
            "page_number"
        )

        lines = page.get(
            "lines",
            []
        )

        if not isinstance(lines, list):
            continue

        for line in lines:

            if isinstance(line, str):
                text = line

            elif isinstance(line, dict):
                text = object_text(
                    line.get("text")
                )

            else:
                continue

            text = text.strip()

            if not text:
                continue

            detected = detect_section(
                text
            )

            if detected:
                current_section = (
                    detected
                )

            result.append({
                "line_id": line_id,

                "text": text,

                "page_number": (
                    page_number
                ),

                "bbox": (
                    line.get("bbox")
                    if isinstance(
                        line,
                        dict,
                    )
                    else None
                ),

                "section": (
                    current_section
                ),

                "is_section_heading": (
                    detected is not None
                ),
            })

            line_id += 1

    return result


# ============================================================
# DOCUMENT ID
# ============================================================

def get_document_id(
    ocr_result: Dict[str, Any],
    layout_result: Dict[str, Any],
) -> Optional[str]:

    document_id = layout_result.get(
        "document_id"
    )

    if document_id:
        return str(document_id)

    document_id = ocr_result.get(
        "document_id"
    )

    if document_id:
        return str(document_id)

    return None


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def extract_fields(
    ocr_result: Dict[str, Any],
    layout_result: Optional[
        Dict[str, Any]
    ] = None,
    composer_result: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    layout_result = (
        layout_result or {}
    )

    composer_result = (
        composer_result or {}
    )

    document_id = get_document_id(
        ocr_result,
        layout_result,
    )

    results: Dict[
        str,
        Dict[str, Any]
    ] = {}

    # ========================================================
    # 1. LAYOUT RELATIONSHIPS
    # ========================================================

    extract_from_relationships(
        layout_result,
        results,
    )

    # ========================================================
    # 2. LAYOUT LINES / STRUCTURE
    # ========================================================

    layout_lines = prepare_layout_lines(
        layout_result
    )

    if layout_lines:

        extract_from_lines(
            layout_lines,
            results,
            evidence_type=(
                "layout_same_line"
            ),
        )

        extract_below_labels(
            layout_lines,
            results,
        )

    # ========================================================
    # 3. LAYOUT TABLES
    # ========================================================

    extract_from_tables(
        layout_result,
        results,
    )

    # ========================================================
    # 4. COMPOSER FALLBACK
    # ========================================================

    document_text = (
        composer_result.get(
            "document_text"
        )
        or layout_result.get(
            "document_text"
        )
        or ""
    )

    if document_text:

        composer_lines = (
            prepare_text_lines(
                document_text
            )
        )

        extract_from_lines(
            composer_lines,
            results,
            evidence_type=(
                "composer_fallback"
            ),
        )

    # ========================================================
    # 5. OCR FALLBACK
    # ========================================================

    if len(results) < len(
        FIELD_DEFINITIONS
    ):

        ocr_lines = prepare_ocr_lines(
            ocr_result
        )

        if ocr_lines:

            extract_from_lines(
                ocr_lines,
                results,
                evidence_type=(
                    "ocr_fallback"
                ),
            )

    # ========================================================
    # COMPLETE FIELD SET
    # ========================================================

    fields = {}

    for field_name, definition in (
        FIELD_DEFINITIONS.items()
    ):

        if field_name in results:

            fields[field_name] = (
                results[field_name]
            )

        else:

            fields[field_name] = (
                make_field_result(
                    field_name=field_name,
                    value=None,
                    section=definition[
                        "section"
                    ],
                )
            )

    extracted_count = sum(
        1
        for result in fields.values()
        if result["value"] is not None
    )

    total_fields = len(fields)

    return {
        "extraction_version": "1.1",

        "document_id": document_id,

        "summary": {
            "total_fields": (
                total_fields
            ),

            "extracted_fields": (
                extracted_count
            ),

            "missing_fields": (
                total_fields
                - extracted_count
            ),
        },

        "fields": fields,

        "document_text": (
            document_text
        ),
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "Extraction V1.1 module loaded successfully."
    )