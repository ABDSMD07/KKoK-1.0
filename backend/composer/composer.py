"""
PS 26018 - Structured Text Composer (V1.2)

Consumes an already-built Layout V1.2 result (unmodified, locked)
and produces the Extraction-facing plain structured text.

WHAT THIS MODULE IS:
    A rendering / composition layer. It walks reading_order and
    decides, using rules only (no scoring, no NLP, no ML), how to
    present what Layout V1.2 already detected.

WHAT THIS MODULE IS NOT:
    - Not a field-meaning classifier.
    - Not a semantic validator. It never inspects VALUE CONTENT to
      decide if a value is "correct".
    - Not a new provenance store. Every emitted block carries ID
      references back into the EXISTING V1.2 pages[] structure.

CHANGE LOG (V1.1 -> V1.2):

  CHANGE 1 - LOW_CONFIDENCE_VALUE_THRESHOLD lowered from 40.0 to
             0.0 (effectively disabled). 40.0 was an uncalibrated
             guess. document_text is Extraction's primary input --
             Composer should not be hiding values from it based on
             an arbitrary number before ground-truth calibration
             exists. Suppression machinery is kept intact (not
             deleted) so it can be re-enabled with a calibrated
             threshold later without rewriting logic. With
             threshold=0.0, no value should ever be suppressed
             (confidence is never < 0.0), but raw_value/suppressed
             fields will still populate correctly if the constant
             is raised again in future.

  CHANGE 2 - Field blocks now carry section_id and section_name,
             identifying which Layout-detected section the field
             falls under. Composer does NOT infer this itself --
             it simply tracks the most recently encountered section
             header while walking reading_order (the same order
             Layout already established) and stamps that context
             onto every field/table/raw_line block that follows,
             until the next section header appears. If no section
             header has been seen yet, section_id/section_name are
             null.

OUTPUT CONTRACT (unchanged):
    {
        "document_text": "<single human-readable string>",
        "text_blocks": [ {...}, ... ]
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Set


# ============================================================
# CONFIGURATION
# ============================================================

# CHANGE 1: disabled pending ground-truth calibration.
# Kept as a named constant (not deleted) so suppression logic
# can be re-enabled later without a rewrite.
LOW_CONFIDENCE_VALUE_THRESHOLD = 0.0

DEFAULT_CONFIDENCE_WHEN_MISSING = 100.0


# ============================================================
# TABLE RENDERING
# ============================================================

def render_table_as_text(table: Dict[str, Any]) -> str:
    """
    Render a heuristically-detected table as plain text.

    NOTE: Layout V1.2's table detector does not distinguish a
    header row from data rows. Row 1 is rendered exactly like every
    other row. Header/data distinction is Extraction's job.
    """

    lines_out = ["[TABLE - structure detected heuristically, unvalidated]"]

    for row in table.get("rows", []):
        cell_texts = [cell.get("text", "") for cell in row.get("cells", [])]
        lines_out.append(" | ".join(cell_texts))

    return "\n".join(lines_out)


# ============================================================
# INDEX BUILDERS (pure lookups, no interpretation)
# ============================================================

def _index_relationships(
    relationships: List[Dict[str, Any]]
) -> Tuple[Dict[str, List[Dict[str, Any]]], Set[str]]:

    by_source: Dict[str, List[Dict[str, Any]]] = {}
    consumed_targets: Set[str] = set()

    for rel in relationships:

        source_id = rel.get("source_line_id")

        if source_id:
            by_source.setdefault(source_id, []).append(rel)

        target_id = rel.get("target_line_id")

        if target_id:
            consumed_targets.add(target_id)

    return by_source, consumed_targets


def _index_tables_by_row_line(
    tables: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:

    table_by_line_id: Dict[str, Dict[str, Any]] = {}

    for table in tables:
        for row in table.get("rows", []):

            line_id = row.get("line_id")

            if line_id:
                table_by_line_id[line_id] = table

    return table_by_line_id


def _index_sections_by_line(
    sections: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:

    return {
        section["line_id"]: section
        for section in sections
        if section.get("line_id")
    }


# ============================================================
# FIELD RENDERING
# ============================================================

def _build_field_block(
    rel: Dict[str, Any],
    lines_by_id: Dict[str, Dict[str, Any]],
    current_section_id: str | None,
    current_section_name: str | None,
) -> Dict[str, Any]:
    """
    Build a single field text_block from a Layout relationship.

    Structural-only rules applied:
      - value is None                -> render empty, value_present=False
      - value present but confidence
        below threshold              -> SUPPRESS from display text,
                                         value_present=False, but keep
                                         raw_value + reason for audit.
                                         (Threshold currently 0.0 ->
                                         effectively never fires. See
                                         CHANGE 1.)
      - value present and confident  -> render normally.

    section_id/section_name are carried forward from the caller's
    reading-order walk (CHANGE 2) -- this function does not decide
    section membership itself.
    """

    raw_value = rel.get("value")
    confidence = rel.get("confidence")

    if confidence is None:
        confidence = DEFAULT_CONFIDENCE_WHEN_MISSING

    value_present = False
    display_value = ""
    suppressed = False
    suppression_reason = None

    if raw_value is not None:

        if confidence < LOW_CONFIDENCE_VALUE_THRESHOLD:
            suppressed = True
            suppression_reason = "low_confidence"
        else:
            value_present = True
            display_value = raw_value

    source_line_id = rel.get("source_line_id")
    target_line_id = rel.get("target_line_id")

    source_text = (
        lines_by_id.get(source_line_id, {}).get("text", "")
        if source_line_id
        else ""
    )

    value_source_text = None

    if target_line_id:
        value_source_text = lines_by_id.get(target_line_id, {}).get("text")

    source_ids = {source_line_id} if source_line_id else set()

    if target_line_id:
        source_ids.add(target_line_id)

    block = {
        "type": "field",
        "text": f"{rel['label']}: {display_value}".rstrip(),
        "relationship_id": rel["relationship_id"],
        "label": rel["label"],
        "value_present": value_present,
        "value_confidence": confidence,
        "section_id": current_section_id,
        "section_name": current_section_name,
        "source_line_ids": sorted(source_ids),
        "source_text": source_text,
        "leading_blank": False,
    }

    if value_source_text is not None:
        block["value_source_text"] = value_source_text

    if suppressed:
        block["value_suppressed"] = True
        block["value_suppressed_reason"] = suppression_reason
        block["raw_value"] = raw_value

    return block


# ============================================================
# PAGE-LEVEL COMPOSITION
# ============================================================

def compose_page_text_blocks(page: Dict[str, Any]) -> List[Dict[str, Any]]:

    lines = page.get("lines", [])
    sections = page.get("sections", [])
    relationships = page.get("relationships", [])
    tables = page.get("tables", [])

    reading_order = page.get("reading_order") or [
        line["line_id"] for line in lines
    ]

    lines_by_id = {line["line_id"]: line for line in lines}

    section_by_line_id = _index_sections_by_line(sections)
    relationships_by_source, consumed_target_line_ids = _index_relationships(
        relationships
    )
    table_by_line_id = _index_tables_by_row_line(tables)

    rendered_table_ids: Set[str] = set()
    blocks: List[Dict[str, Any]] = []
    is_first_block = True

    # CHANGE 2: tracked, not inferred -- updated only when we
    # actually pass a section_header line in reading_order, which
    # is the exact order Layout already established.
    current_section_id: str | None = None
    current_section_name: str | None = None

    for line_id in reading_order:

        if line_id not in lines_by_id:
            continue

        # ---- RULE 1: table membership -------------------------
        if line_id in table_by_line_id:

            table = table_by_line_id[line_id]

            if table["table_id"] in rendered_table_ids:
                continue

            rendered_table_ids.add(table["table_id"])

            blocks.append(
                {
                    "type": "table",
                    "text": render_table_as_text(table),
                    "table_id": table["table_id"],
                    "section_id": current_section_id,
                    "section_name": current_section_name,
                    "source_line_ids": [
                        row["line_id"]
                        for row in table.get("rows", [])
                        if row.get("line_id")
                    ],
                    "leading_blank": not is_first_block,
                }
            )

            is_first_block = False
            continue

        # ---- RULE 2: section header -----------------------------
        if line_id in section_by_line_id:

            section = section_by_line_id[line_id]

            current_section_id = section["section_id"]
            current_section_name = section["name"]

            blocks.append(
                {
                    "type": "section_header",
                    "text": f"[{section['name']}]",
                    "section_id": current_section_id,
                    "section_name": current_section_name,
                    "source_line_ids": [line_id],
                    "leading_blank": not is_first_block,
                }
            )

            is_first_block = False
            continue

        # ---- RULE 3: label -> value relationship(s) from here ---
        if line_id in relationships_by_source:

            for rel in relationships_by_source[line_id]:

                block = _build_field_block(
                    rel,
                    lines_by_id,
                    current_section_id,
                    current_section_name,
                )
                blocks.append(block)

            is_first_block = False
            continue

        # ---- RULE 4: consumed purely as someone else's value ----
        if line_id in consumed_target_line_ids:
            continue

        # ---- RULE 5: unclassified free text (fallback) -----------
        line = lines_by_id[line_id]

        blocks.append(
            {
                "type": "raw_line",
                "text": line["text"],
                "line_id": line_id,
                "section_id": current_section_id,
                "section_name": current_section_name,
                "source_line_ids": [line_id],
                "leading_blank": False,
            }
        )

        is_first_block = False

    return blocks


def compose_page_text(page: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:

    blocks = compose_page_text_blocks(page)

    rendered_pieces: List[str] = []

    for block in blocks:

        if block.get("leading_blank"):
            rendered_pieces.append("")

        rendered_pieces.append(block["text"])

    page_text = "\n".join(rendered_pieces)

    return page_text, blocks


# ============================================================
# DOCUMENT-LEVEL COMPOSITION
# ============================================================

def compose_document_text(layout_result: Dict[str, Any]) -> Dict[str, Any]:

    pages = layout_result.get("pages", [])

    page_texts: List[str] = []
    all_blocks: List[Dict[str, Any]] = []

    for page in pages:

        page_text, blocks = compose_page_text(page)

        for block in blocks:
            block["page_number"] = page.get("page_number")

        page_texts.append(page_text)
        all_blocks.extend(blocks)

    if len(page_texts) > 1:
        separator = "\n\n" + ("=" * 20) + " PAGE BREAK " + ("=" * 20) + "\n\n"
        document_text = separator.join(page_texts)
    else:
        document_text = page_texts[0] if page_texts else ""

    return {
        "document_text": document_text,
        "text_blocks": all_blocks,
    }


# ============================================================
# INTEGRATION HELPER
# ============================================================

def build_layout_with_text(
    ocr_result: Dict[str, Any], document_id: str
) -> Dict[str, Any]:

    from .layout import build_layout  # locked V1.2 module

    layout = build_layout(ocr_result, document_id)
    text_result = compose_document_text(layout)

    layout["document_text"] = text_result["document_text"]
    layout["text_blocks"] = text_result["text_blocks"]

    return layout