"""
============================================================
PS 26018 - PostgreSQL Persistence Layer V1.0
============================================================

Consumes:
    human_verification_result.json

Persists into:
    documents
    land_record_fields
    evidence
    verification_audit

The Human Verification artifact remains the source of truth.
This module does not perform extraction, normalization,
validation, confidence calculation, duplicate detection,
or human verification.
============================================================
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .db_manager import DatabaseManager


class DatabasePersistence:
    """Persist a Human Verification artifact into PostgreSQL."""

    def __init__(self):
        self.db = DatabaseManager()

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _parse_timestamp(value: Optional[str]):
        """Convert ISO timestamp string to Python datetime."""
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        value = value.strip()

        # Handle ISO timestamps ending with Z.
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        return datetime.fromisoformat(value)

    @staticmethod
    def _json_value(value: Any):
        """Convert Python values into JSON-compatible values."""
        if value is None:
            return None

        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _text_value(value: Any):
        """Safely convert a value into database text."""
        if value is None:
            return None

        if isinstance(value, str):
            return value

        return json.dumps(value, ensure_ascii=False)

    # ========================================================
    # DOCUMENT
    # ========================================================

    def _insert_document(self, result: Dict[str, Any]):
        """Insert or update the main document record."""

        document_id = result["document_id"]
        summary = result.get("summary", {})
        source_versions = result.get("source_versions", {})
        duplicate = result.get("duplicate_decision", {})

        query = """
            INSERT INTO documents (
                document_id,
                status,
                created_at,
                completed_at,

                human_verification_version,
                confidence_version,
                validation_version,
                normalization_version,
                extraction_version,

                duplicate_classification,
                duplicate_review_required,

                total_fields,
                fields_requiring_review,
                fields_reviewed,
                fields_accepted,
                fields_auto_accepted,
                fields_edited,
                fields_rejected,
                fields_pending
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (document_id)
            DO UPDATE SET
                status = EXCLUDED.status,
                created_at = EXCLUDED.created_at,
                completed_at = EXCLUDED.completed_at,

                human_verification_version =
                    EXCLUDED.human_verification_version,

                confidence_version =
                    EXCLUDED.confidence_version,

                validation_version =
                    EXCLUDED.validation_version,

                normalization_version =
                    EXCLUDED.normalization_version,

                extraction_version =
                    EXCLUDED.extraction_version,

                duplicate_classification =
                    EXCLUDED.duplicate_classification,

                duplicate_review_required =
                    EXCLUDED.duplicate_review_required,

                total_fields =
                    EXCLUDED.total_fields,

                fields_requiring_review =
                    EXCLUDED.fields_requiring_review,

                fields_reviewed =
                    EXCLUDED.fields_reviewed,

                fields_accepted =
                    EXCLUDED.fields_accepted,

                fields_auto_accepted =
                    EXCLUDED.fields_auto_accepted,

                fields_edited =
                    EXCLUDED.fields_edited,

                fields_rejected =
                    EXCLUDED.fields_rejected,

                fields_pending =
                    EXCLUDED.fields_pending
        """

        params = (
            document_id,
            result.get("status"),
            self._parse_timestamp(result.get("created_at")),
            self._parse_timestamp(result.get("completed_at")),

            result.get("human_verification_version"),
            source_versions.get("confidence"),
            source_versions.get("validation"),
            source_versions.get("normalization"),
            source_versions.get("extraction"),

            duplicate.get("machine_classification"),
            bool(duplicate.get("review_required", False)),

            summary.get("total_fields", 0),
            summary.get("fields_requiring_review", 0),
            summary.get("fields_reviewed", 0),
            summary.get("fields_accepted", 0),
            summary.get("fields_auto_accepted", 0),
            summary.get("fields_edited", 0),
            summary.get("fields_rejected", 0),
            summary.get("fields_pending", 0),
        )

        self.db.execute(query, params)

    # ========================================================
    # LAND RECORD FIELDS
    # ========================================================

    def _insert_fields(self, result: Dict[str, Any]):
        """Insert or update all extracted/verified fields."""

        document_id = result["document_id"]
        fields = result.get("fields", {})

        query = """
            INSERT INTO land_record_fields (
                document_id,
                field_name,

                machine_value,
                raw_value,
                normalized_value,
                verified_value,

                decision,
                review_required,

                validation_status,

                confidence_score,
                confidence_level,
                confidence_reason,

                human_reason
            )
            VALUES (
                %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s,
                %s, %s, %s,
                %s
            )
            ON CONFLICT (document_id, field_name)
            DO UPDATE SET
                machine_value = EXCLUDED.machine_value,
                raw_value = EXCLUDED.raw_value,
                normalized_value = EXCLUDED.normalized_value,
                verified_value = EXCLUDED.verified_value,

                decision = EXCLUDED.decision,
                review_required = EXCLUDED.review_required,

                validation_status = EXCLUDED.validation_status,

                confidence_score = EXCLUDED.confidence_score,
                confidence_level = EXCLUDED.confidence_level,
                confidence_reason = EXCLUDED.confidence_reason,

                human_reason = EXCLUDED.human_reason
        """

        for field_name, field in fields.items():

            if not isinstance(field, dict):
                continue

            params = (
                document_id,
                field_name,

                self._text_value(
                    field.get("machine_value")
                ),

                self._text_value(
                    field.get("raw_value")
                ),

                self._text_value(
                    field.get("normalized_value")
                ),

                self._text_value(
                    field.get("verified_value")
                ),

                field.get("decision"),

                bool(
                    field.get(
                        "review_required",
                        False
                    )
                ),

                field.get("validation_status"),

                field.get("confidence_score"),

                field.get("confidence_level"),

                self._text_value(
                    field.get("confidence_reason")
                ),

                self._text_value(
                    field.get("human_reason")
                ),
            )

            self.db.execute(query, params)

    # ========================================================
    # EVIDENCE
    # ========================================================

    def _insert_evidence(self, result: Dict[str, Any]):
        """Persist source/evidence information for every field."""

        document_id = result["document_id"]
        fields = result.get("fields", {})

        query = """
            INSERT INTO evidence (
                document_id,
                field_name,
                source_text,
                source_line_ids,
                source_page,
                source_bbox,
                evidence_type,
                matched_label
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        for field_name, field in fields.items():

            if not isinstance(field, dict):
                continue

            source_text = field.get("source_text")
            source_line_ids = field.get(
                "source_line_ids",
                []
            )
            source_page = field.get("source_page")
            source_bbox = field.get("source_bbox")
            evidence_type = field.get("evidence_type")
            matched_label = field.get("matched_label")

            # Only create an evidence row when evidence
            # information actually exists.
            if (
                source_text is None
                and not source_line_ids
                and source_page is None
                and source_bbox is None
                and evidence_type is None
                and matched_label is None
            ):
                continue

            params = (
                document_id,
                field_name,
                source_text,
                self._json_value(source_line_ids),
                source_page,
                self._json_value(source_bbox),
                evidence_type,
                matched_label,
            )

            self.db.execute(query, params)

    # ========================================================
    # AUDIT TRAIL
    # ========================================================

    def _insert_audit_trail(self, result: Dict[str, Any]):
        """Persist Human Verification audit events."""

        document_id = result["document_id"]
        audit_trail = result.get(
            "audit_trail",
            []
        )

        query = """
            INSERT INTO verification_audit (
                document_id,
                field_name,
                event_type,
                decision,
                reviewer,
                human_reason,
                event_timestamp,
                event_details
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        for event in audit_trail:

            if not isinstance(event, dict):
                continue

            event_timestamp = (
                event.get("timestamp")
                or event.get("event_timestamp")
            )

            params = (
                document_id,

                event.get("field"),

                event.get("event"),

                event.get("decision"),

                event.get("reviewer"),

                event.get("reason"),

                self._parse_timestamp(
                    event_timestamp
                ),

                self._json_value(event),
            )

            self.db.execute(query, params)

    # ========================================================
    # MAIN PERSISTENCE
    # ========================================================

    def persist(self, result: Dict[str, Any]):
        """
        Persist the complete Human Verification artifact.

        All database operations happen inside one transaction.
        """

        if not isinstance(result, dict):
            raise ValueError(
                "Human Verification result must be a dictionary."
            )

        if not result.get("document_id"):
            raise ValueError(
                "Human Verification result is missing document_id."
            )

        connection = self.db.connect()

        try:

            # ------------------------------------------------
            # Main document
            # ------------------------------------------------

            self._insert_document(result)

            # ------------------------------------------------
            # Fields
            # ------------------------------------------------

            self._insert_fields(result)

            # ------------------------------------------------
            # Evidence
            # ------------------------------------------------

            self._insert_evidence(result)

            # ------------------------------------------------
            # Audit trail
            # ------------------------------------------------

            self._insert_audit_trail(result)

            # ------------------------------------------------
            # Commit EVERYTHING
            # ------------------------------------------------

            connection.commit()

        except Exception:

            # If anything fails, don't leave half the
            # document stored in PostgreSQL.
            connection.rollback()

            raise

        finally:
            self.db.close()


# ============================================================
# JSON LOADER
# ============================================================

def load_human_verification_result(
    path: str
) -> Dict[str, Any]:
    """Load Human Verification JSON from disk."""

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Human Verification result not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:

        result = json.load(file)

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PS 26018 - DATABASE PERSISTENCE V1.0")
    print("=" * 60)

    result_path = (
        Path(__file__).resolve().parent.parent
        / "human_verification_result.json"
    )

    print(
        f"Loading: {result_path}"
    )

    result = load_human_verification_result(
        str(result_path)
    )

    print(
        f"Document ID: {result.get('document_id')}"
    )

    print(
        f"Status: {result.get('status')}"
    )

    print(
        f"Fields: {len(result.get('fields', {}))}"
    )

    print()
    print("Persisting to PostgreSQL...")

    persistence = DatabasePersistence()

    persistence.persist(result)

    print()
    print("DATABASE PERSISTENCE COMPLETE")
    print("-" * 60)
    print(
        "Document inserted/updated"
    )
    print(
        "Fields inserted/updated"
    )
    print(
        "Evidence inserted"
    )
    print(
        "Audit trail inserted"
    )
    print("-" * 60)
    print(
        "Database: P_S26018"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()