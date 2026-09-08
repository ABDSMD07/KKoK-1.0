"""
===========================================================
PS 26018 - Land Record Intelligence System
Human Verification V1.0

Purpose:
    Manage explicit human review decisions over machine-produced
    land-record results while preserving all original evidence.

Human Verification DOES:
    - build the review queue
    - expose machine values and evidence
    - accept human decisions
    - preserve machine output
    - record audit events
    - handle duplicate-review decisions
    - produce a final verified artifact

Human Verification DOES NOT:
    - perform OCR / HTR
    - extract values
    - normalize values
    - validate values
    - calculate confidence
    - perform duplicate detection
    - guess missing values
    - silently modify machine output
    - access databases
===========================================================
"""

import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


HUMAN_VERIFICATION_VERSION = "1.0"


# ============================================================
# FIELD DECISIONS
# ============================================================

DECISION_ACCEPTED = "accepted"
DECISION_EDITED = "edited"
DECISION_REJECTED = "rejected"
DECISION_PENDING = "pending"
DECISION_AUTO_ACCEPTED = "auto_accepted"


# ============================================================
# RECORD STATUSES
# ============================================================

STATUS_PENDING = "pending_review"
STATUS_VERIFIED = "verified"


# ============================================================
# DUPLICATE HUMAN DECISIONS
# ============================================================

DUPLICATE_CONFIRMED = "confirmed_duplicate"
DUPLICATE_NOT_DUPLICATE = "not_duplicate"
DUPLICATE_NEEDS_REVIEW = "needs_more_review"
DUPLICATE_PENDING = "pending"


# ============================================================
# MACHINE DUPLICATE STATUSES REQUIRING REVIEW
# ============================================================

DUPLICATE_REVIEW_REQUIRED = {
    "strong_duplicate",
    "possible_duplicate",
}


# ============================================================
# HELPERS
# ============================================================

def _utc_now() -> str:
    """
    Produce ISO-8601 UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


def _require_dict(
    value: Any,
    name: str,
) -> None:

    if not isinstance(value, dict):

        raise TypeError(
            f"{name} must be a dictionary"
        )


def _machine_value(
    field: Dict[str, Any],
) -> Any:
    """
    Prefer normalized value because this stage follows
    Normalization/Validation/Confidence.

    raw/extracted values remain preserved elsewhere.
    """

    return field.get(
        "normalized_value"
    )


# ============================================================
# REVIEW REQUIREMENT
# ============================================================

def field_requires_review(
    field: Dict[str, Any],
) -> bool:

    if (
        field.get("confidence_review")
        == "required"
    ):
        return True

    validation_status = field.get(
        "validation_status"
    )

    if validation_status in {
        "warning",
        "invalid",
        "missing",
        "not_checked",
    }:
        return True

    return False


# ============================================================
# REVIEW REASONS
# ============================================================

def get_review_reasons(
    field: Dict[str, Any],
) -> List[str]:

    reasons: List[str] = []

    confidence_reason = field.get(
        "confidence_reason"
    )

    if isinstance(
        confidence_reason,
        str,
    ) and confidence_reason.strip():

        if (
            field.get("confidence_review")
            == "required"
        ):
            reasons.append(
                confidence_reason.strip()
            )

    validation_issues = field.get(
        "validation_issues"
    )

    if isinstance(
        validation_issues,
        list,
    ):

        for issue in validation_issues:

            if not isinstance(
                issue,
                dict,
            ):
                continue

            message = issue.get(
                "message"
            )

            if (
                isinstance(message, str)
                and message.strip()
            ):
                reasons.append(
                    message.strip()
                )

    # De-duplicate without changing ordering.
    unique = []

    for reason in reasons:

        if reason not in unique:
            unique.append(reason)

    return unique


# ============================================================
# FIELD ARTIFACT
# ============================================================

def build_field_artifact(
    field_name: str,
    confidence_field: Dict[str, Any],
) -> Dict[str, Any]:

    review_required = (
        field_requires_review(
            confidence_field
        )
    )

    machine_value = _machine_value(
        confidence_field
    )

    if review_required:

        decision = DECISION_PENDING
        verified_value = None

    else:

        decision = DECISION_AUTO_ACCEPTED
        verified_value = machine_value

    return {
        "field": field_name,

        # -----------------------------------------------
        # VALUES
        # -----------------------------------------------

        "machine_value": machine_value,

        "raw_value": confidence_field.get(
            "raw_value"
        ),

        "normalized_value": confidence_field.get(
            "normalized_value"
        ),

        "verified_value": verified_value,

        # -----------------------------------------------
        # HUMAN DECISION
        # -----------------------------------------------

        "review_required": review_required,

        "decision": decision,

        "reviewed_by": None,
        "reviewed_at": None,
        "human_reason": None,

        # -----------------------------------------------
        # MACHINE ASSESSMENT
        # -----------------------------------------------

        "validation_status": confidence_field.get(
            "validation_status"
        ),

        "validation_issues": copy.deepcopy(
            confidence_field.get(
                "validation_issues",
                [],
            )
        ),

        "confidence_score": confidence_field.get(
            "confidence_score"
        ),

        "confidence_level": confidence_field.get(
            "confidence_level"
        ),

        "confidence_reason": confidence_field.get(
            "confidence_reason"
        ),

        "review_reasons": get_review_reasons(
            confidence_field
        ),

        # -----------------------------------------------
        # EVIDENCE
        # -----------------------------------------------

        "source_text": confidence_field.get(
            "source_text"
        ),

        "source_line_ids": copy.deepcopy(
            confidence_field.get(
                "source_line_ids",
                [],
            )
        ),

        "source_page": confidence_field.get(
            "source_page"
        ),

        "source_bbox": copy.deepcopy(
            confidence_field.get(
                "bbox"
            )
        ),

        "evidence_type": confidence_field.get(
            "evidence_type"
        ),

        "matched_label": confidence_field.get(
            "matched_label"
        ),
    }


# ============================================================
# CREATE VERIFICATION SESSION
# ============================================================

def create_verification(
    confidence_result: Dict[str, Any],
    validation_result: Optional[
        Dict[str, Any]
    ] = None,
    duplicate_result: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:
    """
    Create a Human Verification V1.0 artifact.

    No human decisions are made here.
    """

    _require_dict(
        confidence_result,
        "confidence_result",
    )

    confidence_fields = confidence_result.get(
        "fields"
    )

    if not isinstance(
        confidence_fields,
        dict,
    ):

        raise ValueError(
            "confidence_result['fields'] "
            "must be a dictionary"
        )

    verification_fields = {}

    review_queue = []

    for field_name, confidence_field in (
        confidence_fields.items()
    ):

        if not isinstance(
            confidence_field,
            dict,
        ):
            continue

        artifact = build_field_artifact(
            field_name,
            confidence_field,
        )

        verification_fields[
            field_name
        ] = artifact

        if artifact["review_required"]:

            review_queue.append(
                field_name
            )

    # ========================================================
    # DUPLICATE REVIEW
    # ========================================================

    machine_duplicate = None

    if isinstance(
        duplicate_result,
        dict,
    ):

        machine_duplicate = (
            duplicate_result.get(
                "status"
            )
        )

    if machine_duplicate is None:

        duplicate_information = (
            confidence_result.get(
                "duplicate_information",
                {},
            )
        )

        if isinstance(
            duplicate_information,
            dict,
        ):

            machine_duplicate = (
                duplicate_information.get(
                    "classification"
                )
            )

    duplicate_requires_review = (
        machine_duplicate
        in DUPLICATE_REVIEW_REQUIRED
    )

    duplicate_decision = {
        "machine_classification": (
            machine_duplicate
        ),

        "review_required": (
            duplicate_requires_review
        ),

        "human_decision": (
            DUPLICATE_PENDING
            if duplicate_requires_review
            else None
        ),

        "verified_by": None,
        "verified_at": None,
        "reason": None,

        "best_match": (
            copy.deepcopy(
                duplicate_result.get(
                    "best_match"
                )
            )
            if isinstance(
                duplicate_result,
                dict,
            )
            else None
        ),

        "matched_identifiers": (
            copy.deepcopy(
                duplicate_result.get(
                    "matched_identifiers",
                    [],
                )
            )
            if isinstance(
                duplicate_result,
                dict,
            )
            else []
        ),

        "conflicting_identifiers": (
            copy.deepcopy(
                duplicate_result.get(
                    "conflicting_identifiers",
                    [],
                )
            )
            if isinstance(
                duplicate_result,
                dict,
            )
            else []
        ),

        "match_reasons": (
            copy.deepcopy(
                duplicate_result.get(
                    "match_reasons",
                    [],
                )
            )
            if isinstance(
                duplicate_result,
                dict,
            )
            else []
        ),
    }

    result = {
        "human_verification_version": (
            HUMAN_VERIFICATION_VERSION
        ),

        "document_id": (
            confidence_result.get(
                "document_id"
            )
        ),

        "status": STATUS_PENDING,

        "created_at": _utc_now(),

        "completed_at": None,

        "fields": verification_fields,

        "review_queue": review_queue,

        "duplicate_decision": (
            duplicate_decision
        ),

        "audit_trail": [],

        # Preserve high-level provenance between stages.
        "source_versions": {
            "confidence": (
                confidence_result.get(
                    "confidence_version"
                )
            ),

            "validation": (
                confidence_result.get(
                    "source_validation_version"
                )
            ),

            "normalization": (
                confidence_result.get(
                    "source_normalization_version"
                )
            ),

            "extraction": (
                confidence_result.get(
                    "source_extraction_version"
                )
            ),
        },
    }

    _refresh_summary(
        result
    )

    return result


# ============================================================
# FIELD DECISION
# ============================================================

def apply_field_decision(
    verification_result: Dict[str, Any],
    field_name: str,
    decision: str,
    reviewer: str,
    edited_value: Any = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply an explicit human decision.

    Valid decisions:

        accepted
        edited
        rejected

    The input artifact is not modified.
    """

    _require_dict(
        verification_result,
        "verification_result",
    )

    if decision not in {
        DECISION_ACCEPTED,
        DECISION_EDITED,
        DECISION_REJECTED,
    }:

        raise ValueError(
            "decision must be one of: "
            "'accepted', 'edited', 'rejected'"
        )

    if (
        not isinstance(reviewer, str)
        or not reviewer.strip()
    ):

        raise ValueError(
            "reviewer is required"
        )

    result = copy.deepcopy(
        verification_result
    )

    fields = result.get(
        "fields"
    )

    if not isinstance(fields, dict):

        raise ValueError(
            "verification_result['fields'] "
            "must be a dictionary"
        )

    if field_name not in fields:

        raise KeyError(
            f"Unknown field: {field_name}"
        )

    field = fields[field_name]

    before = {
        "decision": field.get(
            "decision"
        ),
        "verified_value": field.get(
            "verified_value"
        ),
    }

    timestamp = _utc_now()

    # ========================================================
    # ACCEPT
    # ========================================================

    if decision == DECISION_ACCEPTED:

        field["verified_value"] = (
            field.get(
                "machine_value"
            )
        )

    # ========================================================
    # EDIT
    # ========================================================

    elif decision == DECISION_EDITED:

        if edited_value is None:

            raise ValueError(
                "edited_value is required "
                "when decision='edited'"
            )

        if (
            isinstance(
                edited_value,
                str,
            )
            and not edited_value.strip()
        ):

            raise ValueError(
                "edited_value cannot be an empty string"
            )

        field["verified_value"] = (
            edited_value
        )

    # ========================================================
    # REJECT
    # ========================================================

    elif decision == DECISION_REJECTED:

        field["verified_value"] = None

    field["decision"] = decision

    field["reviewed_by"] = (
        reviewer.strip()
    )

    field["reviewed_at"] = (
        timestamp
    )

    field["human_reason"] = (
        reason
    )

    # ========================================================
    # AUDIT
    # ========================================================

    result.setdefault(
        "audit_trail",
        [],
    ).append({
        "event": "field_decision",

        "field": field_name,

        "decision": decision,

        "reviewer": (
            reviewer.strip()
        ),

        "timestamp": timestamp,

        "reason": reason,

        "machine_value": field.get(
            "machine_value"
        ),

        "before": before,

        "after": {
            "decision": decision,
            "verified_value": (
                field.get(
                    "verified_value"
                )
            ),
        },
    })

    _refresh_summary(
        result
    )

    return result


# ============================================================
# DUPLICATE DECISION
# ============================================================

def apply_duplicate_decision(
    verification_result: Dict[str, Any],
    decision: str,
    reviewer: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Human decision over duplicate-detector evidence.
    """

    _require_dict(
        verification_result,
        "verification_result",
    )

    allowed = {
        DUPLICATE_CONFIRMED,
        DUPLICATE_NOT_DUPLICATE,
        DUPLICATE_NEEDS_REVIEW,
    }

    if decision not in allowed:

        raise ValueError(
            "Invalid duplicate decision. Expected one of: "
            "'confirmed_duplicate', "
            "'not_duplicate', "
            "'needs_more_review'"
        )

    if (
        not isinstance(reviewer, str)
        or not reviewer.strip()
    ):

        raise ValueError(
            "reviewer is required"
        )

    result = copy.deepcopy(
        verification_result
    )

    duplicate = result.get(
        "duplicate_decision"
    )

    if not isinstance(
        duplicate,
        dict,
    ):

        raise ValueError(
            "'duplicate_decision' is missing"
        )

    timestamp = _utc_now()

    previous = duplicate.get(
        "human_decision"
    )

    duplicate[
        "human_decision"
    ] = decision

    duplicate[
        "verified_by"
    ] = reviewer.strip()

    duplicate[
        "verified_at"
    ] = timestamp

    duplicate[
        "reason"
    ] = reason

    result.setdefault(
        "audit_trail",
        [],
    ).append({
        "event": (
            "duplicate_decision"
        ),

        "reviewer": (
            reviewer.strip()
        ),

        "timestamp": timestamp,

        "reason": reason,

        "machine_classification": (
            duplicate.get(
                "machine_classification"
            )
        ),

        "previous_decision": (
            previous
        ),

        "human_decision": (
            decision
        ),
    })

    _refresh_summary(
        result
    )

    return result


# ============================================================
# REVIEW QUEUE
# ============================================================

def get_pending_review_fields(
    verification_result: Dict[str, Any],
) -> List[str]:

    fields = verification_result.get(
        "fields",
        {},
    )

    if not isinstance(
        fields,
        dict,
    ):
        return []

    pending = []

    for field_name, field in (
        fields.items()
    ):

        if not isinstance(
            field,
            dict,
        ):
            continue

        if (
            field.get(
                "review_required"
            )
            and field.get(
                "decision"
            )
            == DECISION_PENDING
        ):

            pending.append(
                field_name
            )

    return pending


# ============================================================
# SUMMARY
# ============================================================

def _refresh_summary(
    result: Dict[str, Any],
) -> None:

    fields = result.get(
        "fields",
        {},
    )

    decisions = [
        field.get(
            "decision"
        )
        for field in fields.values()
        if isinstance(
            field,
            dict,
        )
    ]

    pending_fields = (
        get_pending_review_fields(
            result
        )
    )

    duplicate = result.get(
        "duplicate_decision",
        {},
    )

    duplicate_pending = False

    if isinstance(
        duplicate,
        dict,
    ):

        duplicate_pending = (
            duplicate.get(
                "review_required"
            )
            and duplicate.get(
                "human_decision"
            )
            in {
                None,
                DUPLICATE_PENDING,
                DUPLICATE_NEEDS_REVIEW,
            }
        )

    result["review_queue"] = (
        pending_fields
    )

    result["summary"] = {
        "total_fields": len(
            decisions
        ),

        "fields_requiring_review": sum(
            1
            for field in fields.values()
            if (
                isinstance(
                    field,
                    dict,
                )
                and field.get(
                    "review_required"
                )
            )
        ),

        "fields_reviewed": sum(
            1
            for decision in decisions
            if decision in {
                DECISION_ACCEPTED,
                DECISION_EDITED,
                DECISION_REJECTED,
            }
        ),

        "fields_accepted": decisions.count(
            DECISION_ACCEPTED
        ),

        "fields_auto_accepted": (
            decisions.count(
                DECISION_AUTO_ACCEPTED
            )
        ),

        "fields_edited": decisions.count(
            DECISION_EDITED
        ),

        "fields_rejected": decisions.count(
            DECISION_REJECTED
        ),

        "fields_pending": len(
            pending_fields
        ),

        "duplicate_review_pending": bool(
            duplicate_pending
        ),
    }


# ============================================================
# CAN FINALIZE
# ============================================================

def can_finalize(
    verification_result: Dict[str, Any],
) -> bool:

    pending_fields = (
        get_pending_review_fields(
            verification_result
        )
    )

    if pending_fields:
        return False

    duplicate = verification_result.get(
        "duplicate_decision",
        {},
    )

    if isinstance(
        duplicate,
        dict,
    ):

        if duplicate.get(
            "review_required"
        ):

            decision = duplicate.get(
                "human_decision"
            )

            if decision not in {
                DUPLICATE_CONFIRMED,
                DUPLICATE_NOT_DUPLICATE,
            }:
                return False

    return True


# ============================================================
# FINALIZE
# ============================================================

def finalize_verification(
    verification_result: Dict[str, Any],
    reviewer: str,
) -> Dict[str, Any]:
    """
    Finalize only when all required human decisions are resolved.
    """

    if (
        not isinstance(reviewer, str)
        or not reviewer.strip()
    ):

        raise ValueError(
            "reviewer is required"
        )

    if not can_finalize(
        verification_result
    ):

        raise ValueError(
            "Verification cannot be finalized because "
            "required reviews are still pending."
        )

    result = copy.deepcopy(
        verification_result
    )

    timestamp = _utc_now()

    result["status"] = (
        STATUS_VERIFIED
    )

    result["completed_at"] = (
        timestamp
    )

    result["completed_by"] = (
        reviewer.strip()
    )

    result.setdefault(
        "audit_trail",
        [],
    ).append({
        "event": (
            "verification_finalized"
        ),

        "reviewer": (
            reviewer.strip()
        ),

        "timestamp": timestamp,
    })

    _refresh_summary(
        result
    )

    return result


# ============================================================
# FINAL VALUES
# ============================================================

def get_verified_values(
    verification_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Produce the clean field/value view intended for downstream
    persistence after verification.

    Audit/evidence remains in verification_result.
    """

    fields = verification_result.get(
        "fields",
        {},
    )

    verified = {}

    for field_name, field in (
        fields.items()
    ):

        if not isinstance(
            field,
            dict,
        ):
            continue

        verified[field_name] = (
            field.get(
                "verified_value"
            )
        )

    return verified


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "Human Verification V1.0 module loaded successfully."
    )