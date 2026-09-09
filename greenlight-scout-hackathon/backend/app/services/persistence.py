from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db.database import (
    database_session,
)

from app.db.models import (
    AnalysisRecord,
    DecisionHistoryRecord,
    DecisionRecord,
)


# ============================================================
# TIME
# ============================================================

def utc_now() -> datetime:

    return datetime.now(
        timezone.utc
    )


# ============================================================
# ANALYSIS
# ============================================================

def save_analysis_record(
    analysis_id: str,
    location: str,
    scene_description: str,
    requirements: list[str],
    analysis_data: dict[str, Any],
) -> AnalysisRecord:

    with database_session() as session:

        existing = session.get(
            AnalysisRecord,
            analysis_id,
        )

        if existing:

            existing.location = (
                location
            )

            existing.scene_description = (
                scene_description
            )

            existing.requirements = (
                requirements
            )

            existing.analysis_data = (
                analysis_data
            )

            session.flush()

            return existing

        record = AnalysisRecord(
            analysis_id=analysis_id,
            location=location,
            scene_description=scene_description,
            requirements=requirements,
            analysis_data=analysis_data,
        )

        session.add(
            record
        )

        session.flush()

        return record


def get_analysis_record(
    analysis_id: str
) -> dict[str, Any] | None:

    with database_session() as session:

        record = session.get(
            AnalysisRecord,
            analysis_id,
        )

        if not record:
            return None

        return {
            "analysis_id":
                record.analysis_id,

            "location":
                record.location,

            "scene_description":
                record.scene_description,

            "requirements":
                record.requirements,

            "analysis":
                record.analysis_data,

            "created_at":
                record.created_at,
        }


def analysis_exists(
    analysis_id: str
) -> bool:

    with database_session() as session:

        record = session.get(
            AnalysisRecord,
            analysis_id,
        )

        return record is not None


# ============================================================
# EXPECTED HUMAN REVIEW ITEMS
# ============================================================

def get_expected_review_items(
    analysis_id: str
) -> list[dict[str, Any]]:

    saved = get_analysis_record(
        analysis_id
    )

    if not saved:
        return []

    analysis = saved[
        "analysis"
    ]

    result: list[
        dict[str, Any]
    ] = []

    # --------------------------------------------------------
    # Claims requiring confirmation
    # --------------------------------------------------------

    for claim in analysis.get(
        "requires_confirmation",
        []
    ):

        claim_id = claim.get(
            "claim_id"
        )

        if not claim_id:
            continue

        result.append(
            {
                "item_id":
                    f"claim-{claim_id}",

                "item_type":
                    "CONFIRMATION",

                "title":
                    claim.get(
                        "statement",
                        ""
                    ),
            }
        )

    # --------------------------------------------------------
    # Open questions
    # --------------------------------------------------------

    for index, question in enumerate(
        analysis.get(
            "open_questions",
            []
        )
    ):

        result.append(
            {
                "item_id":
                    f"question-{index}",

                "item_type":
                    "OPEN_QUESTION",

                "title":
                    str(question),
            }
        )

    return result


# ============================================================
# HUMAN DECISION
# ============================================================

def save_decision_record(
    analysis_id: str,
    decision: str,
    decision_notes: str | None,
    reviewer_name: str | None,
    reviewed_items: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    now = utc_now()

    with database_session() as session:

        current = session.get(
            DecisionRecord,
            analysis_id,
        )

        if current:

            current.decision = (
                decision
            )

            current.decision_notes = (
                decision_notes
            )

            current.reviewer_name = (
                reviewer_name
            )

            current.reviewed_items = (
                reviewed_items
            )

            current.updated_at = (
                now
            )

            created_at = (
                current.created_at
            )

        else:

            current = DecisionRecord(
                analysis_id=
                    analysis_id,

                decision=
                    decision,

                decision_notes=
                    decision_notes,

                reviewer_name=
                    reviewer_name,

                reviewed_items=
                    reviewed_items,

                created_at=
                    now,

                updated_at=
                    now,
            )

            session.add(
                current
            )

            created_at = now

        # ----------------------------------------------------
        # Append-only audit record.
        # ----------------------------------------------------

        history = (
            DecisionHistoryRecord(
                analysis_id=
                    analysis_id,

                decision=
                    decision,

                decision_notes=
                    decision_notes,

                reviewer_name=
                    reviewer_name,

                reviewed_items=
                    reviewed_items,

                recorded_at=
                    now,
            )
        )

        session.add(
            history
        )

        session.flush()

        return {
            "analysis_id":
                analysis_id,

            "decision":
                decision,

            "decision_notes":
                decision_notes,

            "reviewer_name":
                reviewer_name,

            "reviewed_items":
                reviewed_items,

            "created_at":
                created_at,

            "updated_at":
                now,

            "status":
                "RECORDED",
        }


def get_decision_record(
    analysis_id: str
) -> dict[str, Any] | None:

    with database_session() as session:

        record = session.get(
            DecisionRecord,
            analysis_id,
        )

        if not record:
            return None

        return {
            "analysis_id":
                record.analysis_id,

            "decision":
                record.decision,

            "decision_notes":
                record.decision_notes,

            "reviewer_name":
                record.reviewer_name,

            "reviewed_items":
                record.reviewed_items,

            "created_at":
                record.created_at,

            "updated_at":
                record.updated_at,

            "status":
                "RECORDED",
        }


# ============================================================
# DECISION HISTORY
# ============================================================

def get_decision_history_records(
    analysis_id: str
) -> list[dict[str, Any]]:

    with database_session() as session:

        statement = (
            select(
                DecisionHistoryRecord
            )
            .where(
                DecisionHistoryRecord.analysis_id
                == analysis_id
            )
            .order_by(
                DecisionHistoryRecord.history_id.desc()
            )
        )

        records = (
            session
            .scalars(
                statement
            )
            .all()
        )

        return [
            {
                "history_id":
                    record.history_id,

                "analysis_id":
                    record.analysis_id,

                "decision":
                    record.decision,

                "decision_notes":
                    record.decision_notes,

                "reviewer_name":
                    record.reviewer_name,

                "reviewed_items":
                    record.reviewed_items,

                "recorded_at":
                    record.recorded_at,
            }

            for record
            in records
        ]