import logging

from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.api import (
    AnalyzeRequest,
    AnalyzeResponse,
)

from app.services.greenlight_pipeline import (
    analyze_scene,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Greenlight Analysis"],
)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
async def analyze(
    request: AnalyzeRequest
):

    try:

        return await analyze_scene(
            request
        )

    except Exception:

        logger.exception(
            "Greenlight analysis failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Greenlight analysis failed. "
                "Check backend logs for details."
            ),
        )