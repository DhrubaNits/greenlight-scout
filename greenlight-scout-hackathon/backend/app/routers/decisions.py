from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.decision import (
    DecisionHistoryResponse,
    DecisionRequest,
    DecisionResponse,
)

from app.services.persistence import (
    analysis_exists,
    get_decision_history_records,
    get_decision_record,
    get_expected_review_items,
    save_decision_record,
)


router = APIRouter(
    prefix="/api/v1/decisions",
    tags=[
        "Human Decisions"
    ],
)


# ============================================================
# SAVE / UPDATE HUMAN DECISION
# ============================================================

@router.post(
    "",
    response_model=DecisionResponse,
)
async def save_decision(
    request: DecisionRequest
):

    # --------------------------------------------------------
    # Analysis must already exist.
    # --------------------------------------------------------

    if not analysis_exists(
        request.analysis_id
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Analysis not found. "
                "Run the scene analysis first."
            ),
        )

    # --------------------------------------------------------
    # Load expected review items from saved analysis.
    # --------------------------------------------------------

    expected_items = (
        get_expected_review_items(
            request.analysis_id
        )
    )

    expected_ids = {
        item["item_id"]
        for item
        in expected_items
    }

    expected_map = {
        item["item_id"]:
            item
        for item
        in expected_items
    }

    submitted_map = {
        item.item_id:
            item
        for item
        in request.reviewed_items
    }

    # --------------------------------------------------------
    # FULL GREENLIGHT VALIDATION
    #
    # Every outstanding review item must:
    #
    # 1. Be submitted
    # 2. Be marked reviewed
    # --------------------------------------------------------

    if (
        request.decision
        == "GREENLIGHT"
    ):

        missing_ids = (
            expected_ids
            - set(
                submitted_map.keys()
            )
        )

        if missing_ids:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Full Greenlight cannot "
                    "be recorded because some "
                    "review items were omitted."
                ),
            )

        unresolved_ids = [
            item_id
            for item_id
            in expected_ids
            if not submitted_map[
                item_id
            ].reviewed
        ]

        if unresolved_ids:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Full Greenlight cannot "
                    "be recorded while review "
                    "items remain unresolved."
                ),
            )

    # --------------------------------------------------------
    # NORMALIZE REVIEW ITEMS
    #
    # Do not trust titles/categories sent by frontend.
    # Use the values saved with the original analysis.
    # --------------------------------------------------------

    normalized_items = []

    for item in request.reviewed_items:

        expected = expected_map.get(
            item.item_id
        )

        if not expected:
            continue

        normalized_items.append(
            {
                "item_id":
                    item.item_id,

                "item_type":
                    expected[
                        "item_type"
                    ],

                "title":
                    expected[
                        "title"
                    ],

                "reviewed":
                    item.reviewed,

                "resolution":
                    item.resolution,
            }
        )

    # --------------------------------------------------------
    # SAVE CURRENT DECISION + AUDIT HISTORY
    # --------------------------------------------------------

    return save_decision_record(

        analysis_id=
            request.analysis_id,

        decision=
            request.decision,

        decision_notes=
            request.decision_notes,

        reviewer_name=
            request.reviewer_name,

        reviewed_items=
            normalized_items,
    )


# ============================================================
# GET CURRENT HUMAN DECISION
# ============================================================

@router.get(
    "/{analysis_id}",
    response_model=DecisionResponse,
)
async def get_decision(
    analysis_id: str
):

    decision = (
        get_decision_record(
            analysis_id
        )
    )

    if not decision:

        raise HTTPException(
            status_code=404,
            detail=(
                "No human decision has "
                "been recorded for this analysis."
            ),
        )

    return decision


# ============================================================
# GET HUMAN DECISION HISTORY
# ============================================================

@router.get(
    "/{analysis_id}/history",
    response_model=list[
        DecisionHistoryResponse
    ],
)
async def get_decision_history(
    analysis_id: str
):

    if not analysis_exists(
        analysis_id
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Analysis not found."
            ),
        )

    return (
        get_decision_history_records(
            analysis_id
        )
    )