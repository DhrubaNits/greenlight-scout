from datetime import (
    datetime,
    timezone,
)

from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.database import (
    Base,
)


# ============================================================
# UTC TIMESTAMP
# ============================================================

def utc_now() -> datetime:

    return datetime.now(
        timezone.utc
    )


# ============================================================
# ANALYSIS
# ============================================================

class AnalysisRecord(
    Base
):

    __tablename__ = (
        "analyses"
    )


    analysis_id: Mapped[str] = (
        mapped_column(
            String(64),
            primary_key=True,
        )
    )


    location: Mapped[str] = (
        mapped_column(
            String(500),
            nullable=False,
        )
    )


    scene_description: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )


    requirements: Mapped[
        list[Any]
    ] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )


    analysis_data: Mapped[
        dict[str, Any]
    ] = mapped_column(
        JSON,
        nullable=False,
    )


    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
    )


# ============================================================
# CURRENT HUMAN DECISION
# ============================================================

class DecisionRecord(
    Base
):

    __tablename__ = (
        "decisions"
    )


    analysis_id: Mapped[str] = (
        mapped_column(
            String(64),

            ForeignKey(
                "analyses.analysis_id"
            ),

            primary_key=True,
        )
    )


    decision: Mapped[str] = (
        mapped_column(
            String(64),
            nullable=False,
        )
    )


    decision_notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )


    reviewer_name: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )


    reviewed_items: Mapped[
        list[Any]
    ] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )


    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
    )


    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


# ============================================================
# HUMAN DECISION AUDIT HISTORY
# ============================================================

class DecisionHistoryRecord(
    Base
):

    __tablename__ = (
        "decision_history"
    )


    history_id: Mapped[int] = (
        mapped_column(
            Integer,
            primary_key=True,
            autoincrement=True,
        )
    )


    analysis_id: Mapped[str] = (
        mapped_column(
            String(64),

            ForeignKey(
                "analyses.analysis_id"
            ),

            nullable=False,
            index=True,
        )
    )


    decision: Mapped[str] = (
        mapped_column(
            String(64),
            nullable=False,
        )
    )


    decision_notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )


    reviewer_name: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )


    reviewed_items: Mapped[
        list[Any]
    ] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )


    recorded_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
    )