from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):

    location: str = Field(
        ...,
        min_length=2,
        description="Proposed filming location",
    )

    scene_description: str = Field(
        ...,
        min_length=5,
        description="Description of the filming scene",
    )

    requirements: List[str] = Field(
        default_factory=list,
        description="Additional production requirements",
    )


class ClaimResponse(BaseModel):

    claim_id: str

    category: str

    statement: str

    status: str

    source_ids: List[str] = Field(
        default_factory=list
    )

    excerpt_ids: List[str] = Field(
        default_factory=list
    )

    reason: Optional[str] = None

    semantic_reason: Optional[str] = None

    support_level: Optional[str] = None


class SourceResponse(BaseModel):

    source_id: str

    title: str

    url: str

    publish_date: Optional[str] = None

    authority_level: str


class AnalysisMetrics(BaseModel):

    sources_retrieved: int

    claims_proposed: int

    candidate_verified: int

    final_verified: int

    requires_confirmation: int


class AnalyzeResponse(BaseModel):

    status: str

    request_id: str

    location: str

    scene_analysis: dict

    verified_findings: List[ClaimResponse]

    requires_confirmation: List[ClaimResponse]

    open_questions: List[str]

    sources: List[SourceResponse]

    metrics: AnalysisMetrics