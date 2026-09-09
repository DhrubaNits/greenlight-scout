from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.saved_analysis import (
    SavedAnalysisResponse,
)

from app.services.persistence import (
    get_analysis_record,
)


router = APIRouter(
    prefix="/api/v1/analyses",
    tags=[
        "Saved Analyses"
    ],
)


# ============================================================
# GET SAVED ANALYSIS
# ============================================================

@router.get(
    "/{analysis_id}",
    response_model=SavedAnalysisResponse,
)
async def get_saved_analysis(
    analysis_id: str
):

    analysis = (
        get_analysis_record(
            analysis_id
        )
    )

    if not analysis:

        raise HTTPException(
            status_code=404,
            detail=(
                "Analysis not found."
            ),
        )

    return analysis