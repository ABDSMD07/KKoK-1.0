"""
PS 26018 - Layout Analysis Module (V1.2 - locked scope)

Pipeline:
    OCR words
        -> Line reconstruction
        -> Block reconstruction
        -> Section detection
        -> Spatial relationships (label <-> value)
        -> Table detection (heuristic)
        -> Reading order
        -> Provenance (preserved throughout)

Layout does NOT decide field meaning (e.g. "54/2 is Survey
Number"), validity, or duplicates. That is Extraction's job
and beyond.

CHANGE LOG (relative to prior versions, all verified against
the real PS26018 test document OCR output):

  FIX 1 - Section detection used exact string equality; failed
          on every real header due to OCR noise sharing the
          same line. Changed to substring containment.

  FIX 2 - Label regex was anchored at line start; failed when
          garbage tokens preceded the label. Changed to
          search-anywhere matching.

  FIX 3 - "Value on next line" fallback had no spatial
          validation, risking a wrong value attached with
          false confidence. Added a vertical-distance check;
          rejects the guess (value stays None) if too far.

  FIX 4 - Code referenced page.get("width")/("height"), keys
          that do not exist in the real OCR contract. Aligned
          to the actual contract (image_width/image_height,
          optional).

  FIX 5 - y_tolerance/block_gap were fixed pixel constants.
          Changed to derive from the document's own median
          word/line height, so it adapts across resolutions.

  FIX 6 - Inline value capture was greedy to end-of-line,
          which on the real document bleeds one label's value
          into the next label's text on the same merged line
          (e.g. "Village" would have captured "GREEN VALLEY
          Survey Number / Khssra Number 54/2..."). Inline
          capture now stops at the next detected label
          occurring later in the same line, if any.

NEW IN V1.2 (per locked scope):

  - Explicit "relationships" replacing the old flat
    key_value_relationships list, with a spatial_relation
    field (same_line / below / right).
  - Heuristic table detection (column-alignment based),
    explicitly labeled as a heuristic, not a validated
    feature.
  - Reading order per page, with a column-clustering fallback
    for potential multi-column pages (untested - we have no
    real multi-column sample yet).
  - Page "dimensions" field.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from statistics import mean, median
import json
import re
import traceback


# ============================================================
# CONFIGURATION
# ============================================================

FALLBACK_Y_TOLERANCE = 15.0
FALLBACK_BLOCK_GAP = 80.0

# How close (in x) two word start-positions must be to be
# considered "the same table column" during heuristic table
# detection.
TABLE_COLUMN_X_TOLERANCE = 40.0

# Minimum number of lines in a block before we even attempt
# table detection on it.
TABLE_MIN_LINES = 2

# Minimum number of consistent columns required to call
# something a table candidate.
TABLE_MIN_COLUMNS = 2


# ============================================================
# BASIC HELPERS
# ============================================================

def _word_bbox(word: Dict[str, Any]) -> Dict[str, float]:
    bbox = word.get("bbox", {})
    return {
        "x": float(bbox.get("x", 0)),
        "y": float(bbox.get("y", 0)),
        "width": float(bbox.get("width", 0)),
        "height": float(bbox.get("height", 0)),
    }


def _word_center_y(word: Dict[str, Any]) -> float:
    bbox = _word_bbox(word)
    return bbox["y"] + bbox["height"] / 2


def _word_right(word: Dict[str, Any]) -> float:
    bbox = _word_bbox(word)
    return bbox["x"] + bbox["width"]


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def _estimate_adaptive_tolerance(words: List[Dict[str, Any]]) -> float:
    """
    FIX 5: derive line-grouping tolerance from the document's
    own text size instead of a hardcoded pixel constant.
    """

    heights = [
        _word_bbox(w)["height"] for w in words if _word_bbox(w)["height"] > 0
    ]

    if not heights:
        return FALLBACK_Y_TOLERANCE

    return max(FALLBACK_Y_TOLERANCE, median(heights) * 0.6)


def _y_ranges_overlap(
    a_top: float, a_bottom: float, b_top: float, b_bottom: float
) -> float:
    """
    Returns the fraction of the smaller range that overlaps
    with the other range. 0.0 if no overlap.
    """

    overlap = min(a_bottom, b_bottom) - max(a_top, b_top)

    if overlap <= 0:
        return 0.0

    smaller = min(a_bottom - a_top, b_bottom - b_top)

    if smaller <= 0:
        return 0.0

    return overlap / smaller


# ============================================================
# LINE RECONSTRUCTION
# ============================================================

def group_words_into_lines(
    words: List[Dict[str, Any]],
    y_tolerance: Optional[float] = None,
) -> List[Dict[str, Any]]:

    valid_words = []

    for word in words:
        text = _clean_text(word.get("text", ""))

        if not text:
            continue

        copied = dict(word)
        copied["text"] = text
        copied["_center_y"] = _word_center_y(copied)

        valid_words.append(copied)

    if not valid_words:
        return []

    if y_tolerance is None:
        y_tolerance = _estimate_adaptive_tolerance(valid_words)

    valid_words.sort(key=lambda w: (w["_center_y"], _word_bbox(w)["x"]))

    lines: List[List[Dict[str, Any]]] = []

    for word in valid_words:

        if not lines:
            lines.append([word])
            continue

        current_line = lines[-1]
        average_y = mean(item["_center_y"] for item in current_line)

        if abs(word["_center_y"] - average_y) <= y_tolerance:
            current_line.append(word)
        else:
            lines.append([word])

    result = []

    for line_index, line_words in enumerate(lines):

        line_words.sort(key=lambda w: _word_bbox(w)["x"])

        text = " ".join(word["text"] for word in line_words)

        xs = [_word_bbox(w)["x"] for w in line_words]
        ys = [_word_bbox(w)["y"] for w in line_words]
        rights = [_word_right(w) for w in line_words]
        bottoms = [
            _word_bbox(w)["y"] + _word_bbox(w)["height"] for w in line_words
        ]

        bbox = {
            "x": min(xs),
            "y": min(ys),
            "width": max(rights) - min(xs),
            "height": max(bottoms) - min(ys),
        }

        confidences = [float(w.get("confidence", 0)) for w in line_words]

        result.append(
            {
                "line_id": f"line_{line_index + 1}",
                "text": text,
                "bbox": bbox,
                "confidence": round(mean(confidences), 2),
                "word_count": len(line_words),
                "words": [
                    {
                        "text": w["text"],
                        "confidence": w.get("confidence"),
                        "bbox": _word_bbox(w),
                    }
                    for w in line_words
                ],
            }
        )

    return result


# ============================================================
# BLOCK RECONSTRUCTION
# ============================================================

def group_lines_into_blocks(
    lines: List[Dict[str, Any]],
    block_gap: Optional[float] = None,
) -> List[Dict[str, Any]]:

    if not lines:
        return []

    if block_gap is None:
        line_heights = [
            line["bbox"]["height"] for line in lines if line["bbox"]["height"] > 0
        ]

        block_gap = (
            max(FALLBACK_BLOCK_GAP, median(line_heights) * 3.0)
            if line_heights
            else FALLBACK_BLOCK_GAP
        )

    sorted_lines = sorted(lines, key=lambda line: line["bbox"]["y"])

    blocks: List[List[Dict[str, Any]]] = []

    for line in sorted_lines:

        if not blocks:
            blocks.append([line])
            continue

        previous = blocks[-1][-1]
        previous_bottom = previous["bbox"]["y"] + previous["bbox"]["height"]
        current_top = line["bbox"]["y"]
        gap = current_top - previous_bottom

        if gap <= block_gap:
            blocks[-1].append(line)
        else:
            blocks.append([line])

    result = []

    for block_index, block_lines in enumerate(blocks):

        block_text = "\n".join(line["text"] for line in block_lines)

        x_values = [line["bbox"]["x"] for line in block_lines]
        y_values = [line["bbox"]["y"] for line in block_lines]
        right_values = [
            line["bbox"]["x"] + line["bbox"]["width"] for line in block_lines
        ]
        bottom_values = [
            line["bbox"]["y"] + line["bbox"]["height"] for line in block_lines
        ]
        confidences = [line["confidence"] for line in block_lines]

        bbox = {
            "x": min(x_values),
            "y": min(y_values),
            "width": max(right_values) - min(x_values),
            "height": max(bottom_values) - min(y_values),
        }

        result.append(
            {
                "block_id": f"block_{block_index + 1}",
                "text": block_text,
                "bbox": bbox,
                "confidence": round(mean(confidences), 2),
                "line_count": len(block_lines),
                "line_ids": [line["line_id"] for line in block_lines],
            }
        )

    return result


# ============================================================
# SECTION DETECTION
# ============================================================

SECTION_NAMES = [
    "LANDOWNER DETAILS",
    "LAND IDENTIFICATION",
    "LAND CHARACTERISTICS",
    "OWNERSHIP DETAILS",
    "MUTATION RECORDS",
    "REGISTRATION INFORMATION",
]


def _normalize_for_matching(text: str) -> str:
    text = text.upper()
    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_sections(lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    FIX 1: substring containment instead of exact equality -
    verified necessary against the real test document, where
    every section header line also contains OCR noise tokens.
    """

    detected = []

    for index, line in enumerate(lines):

        normalized = _normalize_for_matching(line["text"])

        for section_name in SECTION_NAMES:

            if section_name in normalized:

                detected.append(
                    {
                        "section_id": f"section_{len(detected) + 1}",
                        "name": section_name,
                        "line_id": line["line_id"],
                        "bbox": line["bbox"],
                        "confidence": line["confidence"],
                        "line_index": index,
                    }
                )

                break

    return detected


# ============================================================
# SPATIAL RELATIONSHIPS (label <-> value)
# ============================================================

LABEL_DEFINITIONS = [
    ("Name", r"Name"),
    ("Father's Name", r"Father.?s Name"),
    ("Address", r"Address"),
    ("Village", r"Village"),
    ("Tehsil", r"Tehsil"),
    ("District", r"District"),
    ("Survey Number", r"Survey Number|Survey No\.?"),
    ("Khasra Number", r"Khasra Number|Khasra No\.?|Khssra Number"),
    ("Khata Number", r"Khata Number|Account No\.?"),
    ("Plot Area", r"Plot Area"),
    ("Land Classification", r"Land Classification"),
]

# Compiled once: (canonical_label_name, compiled_pattern)
_COMPILED_LABELS: List[Tuple[str, "re.Pattern"]] = [
    (name, re.compile(pattern, flags=re.IGNORECASE))
    for name, pattern in LABEL_DEFINITIONS
]


def _find_all_label_matches(text: str) -> List[Tuple[str, int, int]]:
    """
    Find every label occurrence in a line of text.

    Returns a list of (canonical_label_name, start_index, end_index),
    sorted by start_index. Used both to locate the label we're
    currently processing and (FIX 6) to know where the NEXT
    label starts, so inline value capture can stop there instead
    of running greedily to end-of-line.
    """

    matches = []

    for name, pattern in _COMPILED_LABELS:

        for match in pattern.finditer(text):
            matches.append((name, match.start(), match.end()))

    matches.sort(key=lambda m: m[1])

    return matches


def _vertical_gap(line_a: Dict[str, Any], line_b: Dict[str, Any]) -> float:
    bottom_a = line_a["bbox"]["y"] + line_a["bbox"]["height"]
    top_b = line_b["bbox"]["y"]
    return top_b - bottom_a


def detect_relationships(lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect label -> value relationships using three spatial
    strategies, in priority order:

      1. same_line  - value follows the label on the same
                       reconstructed line (bounded by the next
                       label on that line, FIX 6).
      2. below      - value is the next line down, within a
                       validated vertical distance (FIX 3).
      3. right      - value is a separate line at roughly the
                       same vertical band, positioned to the
                       right (handles side-by-side label/value
                       columns that did not merge into one
                       reconstructed line).
    """

    relationships = []

    if lines:
        line_heights = [
            line["bbox"]["height"] for line in lines if line["bbox"]["height"] > 0
        ]
        median_line_height = median(line_heights) if line_heights else 20.0
    else:
        median_line_height = 20.0

    max_below_gap = median_line_height * 2.0
    max_right_gap = median_line_height * 15.0  # generous horizontal allowance

    for index, line in enumerate(lines):

        text = _clean_text(line["text"])
        label_matches = _find_all_label_matches(text)

        if not label_matches:
            continue

        # Process the FIRST label found on this line as the
        # "current" label. (A line with multiple labels, e.g.
        # "Village ... Survey Number ...", will be revisited
        # naturally because each label's own line index is the
        # same line - but to avoid duplicate/overlapping value
        # capture, we process one label match per outer loop
        # pass using its own start/end and the boundary of the
        # NEXT match after it.)

        for match_index, (label_name, start, end) in enumerate(label_matches):

            after_label_start = end
            after_label_end = (
                label_matches[match_index + 1][1]
                if match_index + 1 < len(label_matches)
                else len(text)
            )

            inline_value = _clean_text(
                text[after_label_start:after_label_end]
            )

            # Strip a leading ":" or "-" left over from the pattern.
            inline_value = re.sub(r"^[:\-]\s*", "", inline_value)

            value = inline_value or None
            value_line_id = None
            spatial_relation = "same_line" if value else None

            if not value and index + 1 < len(lines):

                next_line = lines[index + 1]
                gap = _vertical_gap(line, next_line)

                if 0 <= gap <= max_below_gap:
                    value = _clean_text(next_line["text"])
                    value_line_id = next_line["line_id"]
                    spatial_relation = "below"

            if not value:

                # Try "right": another line at roughly the same
                # y-band, positioned to the right of this label.
                label_bottom = line["bbox"]["y"] + line["bbox"]["height"]
                label_top = line["bbox"]["y"]
                label_right = line["bbox"]["x"] + line["bbox"]["width"]

                best_candidate = None
                best_distance = None

                for other_index, other_line in enumerate(lines):

                    if other_index == index:
                        continue

                    other_top = other_line["bbox"]["y"]
                    other_bottom = other_line["bbox"]["y"] + other_line["bbox"]["height"]
                    other_left = other_line["bbox"]["x"]

                    overlap = _y_ranges_overlap(
                        label_top, label_bottom, other_top, other_bottom
                    )

                    if overlap < 0.5:
                        continue

                    horizontal_gap = other_left - label_right

                    if horizontal_gap < 0 or horizontal_gap > max_right_gap:
                        continue

                    if best_distance is None or horizontal_gap < best_distance:
                        best_distance = horizontal_gap
                        best_candidate = other_line

                if best_candidate is not None:
                    value = _clean_text(best_candidate["text"])
                    value_line_id = best_candidate["line_id"]
                    spatial_relation = "right"

            relationships.append(
                {
                    "relationship_id": f"rel_{len(relationships) + 1}",
                    "relation": "label_value",
                    "spatial_relation": spatial_relation,
                    "label": label_name,
                    "label_text_raw": _clean_text(text[start:end]),
                    "value": value,
                    "source_line_id": line["line_id"],
                    "target_line_id": value_line_id,
                    "confidence": line["confidence"],
                }
            )

    return relationships


# ============================================================
# TABLE DETECTION (HEURISTIC - NOT VALIDATED)
# ============================================================

def _cluster_x_positions(
    positions: List[float], tolerance: float
) -> List[float]:
    """
    Cluster a list of x-positions into column anchors.
    Simple gap-based clustering: sort, start a new cluster
    whenever the gap to the previous position exceeds tolerance.
    """

    if not positions:
        return []

    sorted_positions = sorted(positions)
    clusters: List[List[float]] = [[sorted_positions[0]]]

    for pos in sorted_positions[1:]:

        if pos - clusters[-1][-1] <= tolerance:
            clusters[-1].append(pos)
        else:
            clusters.append([pos])

    return [mean(cluster) for cluster in clusters]


def _assign_to_nearest_cluster(value: float, clusters: List[float]) -> int:

    best_index = 0
    best_distance = abs(value - clusters[0])

    for i, c in enumerate(clusters[1:], start=1):

        distance = abs(value - c)

        if distance < best_distance:
            best_distance = distance
            best_index = i

    return best_index


def detect_tables(
    blocks: List[Dict[str, Any]],
    lines_by_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    HEURISTIC table detection based on column alignment of word
    x-start positions across consecutive lines within a block.

    IMPORTANT: this is an unvalidated heuristic (see module
    docstring). It may produce false positives on any block
    with coincidentally aligned text, and false negatives on
    tables with irregular spacing. Treat "tables" output as a
    draft signal, not a certified structure, until measured
    against ground truth (project roadmap Phase 3/9).
    """

    tables = []

    for block in blocks:

        block_lines = [
            lines_by_id[line_id]
            for line_id in block["line_ids"]
            if line_id in lines_by_id
        ]

        if len(block_lines) < TABLE_MIN_LINES:
            continue

        # Collect word x-start positions across all lines in
        # this block.
        all_x_starts = [
            word["bbox"]["x"]
            for line in block_lines
            for word in line["words"]
        ]

        clusters = _cluster_x_positions(all_x_starts, TABLE_COLUMN_X_TOLERANCE)

        if len(clusters) < TABLE_MIN_COLUMNS:
            continue

        # Require that at least half the lines actually populate
        # 2+ distinct columns - otherwise this is likely just a
        # paragraph of normal text, not a table.
        lines_with_multiple_columns = 0

        rows = []

        for line in block_lines:

            column_hits = {}

            for word in line["words"]:
                cluster_index = _assign_to_nearest_cluster(
                    word["bbox"]["x"], clusters
                )
                column_hits.setdefault(cluster_index, []).append(word)

            if len(column_hits) >= TABLE_MIN_COLUMNS:
                lines_with_multiple_columns += 1

            cells = []

            for cluster_index in sorted(column_hits.keys()):

                words_in_cell = sorted(
                    column_hits[cluster_index],
                    key=lambda w: w["bbox"]["x"],
                )

                cell_text = " ".join(w["text"] for w in words_in_cell)

                cells.append(
                    {
                        "column_index": cluster_index,
                        "text": cell_text,
                    }
                )

            rows.append(
                {
                    "row_id": f"{block['block_id']}_{line['line_id']}",
                    "line_id": line["line_id"],
                    "cells": cells,
                }
            )

        if lines_with_multiple_columns < max(1, len(block_lines) // 2):
            continue

        tables.append(
            {
                "table_id": f"table_{len(tables) + 1}",
                "bbox": block["bbox"],
                "block_id": block["block_id"],
                "column_count": len(clusters),
                "rows": rows,
                "detection_method": "column_alignment_heuristic",
                "validated": False,
            }
        )

    return tables


# ============================================================
# READING ORDER
# ============================================================

def compute_reading_order(
    lines: List[Dict[str, Any]],
    blocks: List[Dict[str, Any]],
) -> List[str]:
    """
    Determine the order in which lines should be read.

    Default: top-to-bottom (already the natural order lines are
    produced in, since group_words_into_lines sorts by y).

    Multi-column fallback: if blocks appear to occupy distinct,
    non-overlapping horizontal ranges (a rough signal of
    columns), order column-major (leftmost column fully, then
    next column). NOTE: untested - the current test document is
    single-column, so this fallback has not been validated
    against a real multi-column document yet.
    """

    if not blocks:
        return [line["line_id"] for line in lines]

    block_ranges = [
        (b["bbox"]["x"], b["bbox"]["x"] + b["bbox"]["width"], b)
        for b in blocks
    ]

    # Simple column signal: do block x-ranges cluster into 2+
    # groups with little overlap?
    lefts = sorted(r[0] for r in block_ranges)

    # Conservative: only attempt column ordering if there's a
    # clear, large gap in the sorted left-edges (page split).
    column_break_detected = False

    for i in range(1, len(lefts)):
        if lefts[i] - lefts[i - 1] > 300:  # heuristic gap in px
            column_break_detected = True
            break

    if not column_break_detected:
        # Default: natural top-to-bottom order.
        return [line["line_id"] for line in lines]

    # Column-major fallback (untested on real data).
    sorted_blocks = sorted(block_ranges, key=lambda r: (r[0], r[2]["bbox"]["y"]))

    ordered_line_ids = []

    for _, _, block in sorted_blocks:
        ordered_line_ids.extend(block["line_ids"])

    return ordered_line_ids


# ============================================================
# COMPLETE LAYOUT ANALYSIS
# ============================================================

def analyze_layout(ocr_result: Dict[str, Any]) -> Dict[str, Any]:

    pages = ocr_result.get("pages", [])

    layout_pages = []

    for page_index, page in enumerate(pages):

        words = page.get("words", [])

        lines = group_words_into_lines(words)
        lines_by_id = {line["line_id"]: line for line in lines}

        blocks = group_lines_into_blocks(lines)
        sections = detect_sections(lines)
        relationships = detect_relationships(lines)
        tables = detect_tables(blocks, lines_by_id)
        reading_order = compute_reading_order(lines, blocks)

        layout_pages.append(
            {
                "page_number": page.get("page_number", page_index + 1),
                "image": page.get("image"),
                "dimensions": {
                    "width": page.get("image_width"),
                    "height": page.get("image_height"),
                },
                "lines": lines,
                "blocks": blocks,
                "sections": sections,
                "relationships": relationships,
                "tables": tables,
                "reading_order": reading_order,
            }
        )

    total_lines = sum(len(p["lines"]) for p in layout_pages)
    total_blocks = sum(len(p["blocks"]) for p in layout_pages)
    total_sections = sum(len(p["sections"]) for p in layout_pages)
    total_relationships = sum(len(p["relationships"]) for p in layout_pages)
    total_tables = sum(len(p["tables"]) for p in layout_pages)

    return {
        "layout_version": "1.2",
        "pages": layout_pages,
        "summary": {
            "page_count": len(layout_pages),
            "line_count": total_lines,
            "block_count": total_blocks,
            "section_count": total_sections,
            "relationship_count": total_relationships,
            "table_count": total_tables,
        },
    }


# ============================================================
# PIPELINE INTEGRATION HELPERS
# ============================================================

def build_layout(ocr_result: Dict[str, Any], document_id: str) -> Dict[str, Any]:
    layout = analyze_layout(ocr_result)
    layout["document_id"] = document_id
    return layout


def save_layout_result(result: Dict[str, Any], output_path: Path) -> str:

    output_path = Path(output_path)

    print("[LAYOUT] Attempting to save JSON:")
    print("[LAYOUT]", output_path)

    try:

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(result, json_file, ensure_ascii=False, indent=4)

        if not output_path.exists():
            raise RuntimeError("JSON write completed but file does not exist.")

        file_size = output_path.stat().st_size

        print("[LAYOUT] JSON CREATED SUCCESSFULLY")
        print("[LAYOUT] JSON size:", file_size, "bytes")
        print("[LAYOUT] JSON path:", output_path.resolve())

        return str(output_path)

    except Exception as error:

        print("[LAYOUT JSON ERROR]", error)
        traceback.print_exc()
        raise