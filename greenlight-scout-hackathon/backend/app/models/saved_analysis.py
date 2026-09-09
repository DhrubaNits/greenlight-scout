from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SavedAnalysisResponse(
    BaseModel
):

    analysis_id: str

    location: str

    scene_description: str

    requirements: list[str]

    analysis: dict[
        str,
        Any
    ]

    created_at: datetime