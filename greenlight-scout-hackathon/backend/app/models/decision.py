from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# DECISION TYPES
# ============================================================

DecisionType = Literal[
    "GREENLIGHT",
    "GREENLIGHT_WITH_CONDITIONS",
    "DO_NOT_GREENLIGHT",
]


ReviewItemType = Literal[
    "CONFIRMATION",
    "OPEN_QUESTION",
]


# ============================================================
# REVIEW ITEM
# ============================================================

class ReviewedItem(
    BaseModel
):

    item_id: str = Field(
        min_length=1
    )

    item_type: ReviewItemType

    title: str = Field(
        min_length=1
    )

    reviewed: bool = False

    resolution: str | None = None


# ============================================================
# SAVE DECISION REQUEST
# ============================================================

class DecisionRequest(
    BaseModel
):

    analysis_id: str = Field(
        min_length=1
    )

    decision: DecisionType

    decision_notes: str | None = None

    reviewer_name: str | None = None

    reviewed_items: list[
        ReviewedItem
    ] = Field(
        default_factory=list
    )


# ============================================================
# CURRENT DECISION RESPONSE
# ============================================================

class DecisionResponse(
    BaseModel
):

    analysis_id: str

    decision: DecisionType

    decision_notes: str | None = None

    reviewer_name: str | None = None

    reviewed_items: list[
        ReviewedItem
    ]

    created_at: datetime

    updated_at: datetime

    status: str


# ============================================================
# DECISION HISTORY
# ============================================================

class DecisionHistoryResponse(
    BaseModel
):

    history_id: int

    analysis_id: str

    decision: DecisionType

    decision_notes: str | None = None

    reviewer_name: str | None = None

    reviewed_items: list[
        ReviewedItem
    ]

    recorded_at: datetime