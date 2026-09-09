from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# CLAIM VERIFICATION OUTPUT
# ============================================================

class VerifiedClaim(BaseModel):

    claim_id: str = Field(
        description="Unique claim identifier such as C1."
    )

    category: str = Field(
        description=(
            "Claim category such as DRONE, ROAD_CLOSURE, "
            "POLICE_ASSISTANCE, NIGHT_FILMING or GENERAL."
        )
    )

    statement: str = Field(
        description="The factual statement being evaluated."
    )

    status: Literal[
        "VERIFIED",
        "REQUIRES_CONFIRMATION"
    ] = Field(
        description=(
            "VERIFIED only when supplied evidence supports "
            "the claim. Otherwise REQUIRES_CONFIRMATION."
        )
    )

    source_ids: list[str] = Field(
        default_factory=list,
        description="Source identifiers supporting the claim."
    )

    excerpt_ids: list[str] = Field(
        default_factory=list,
        description="Exact evidence excerpt identifiers."
    )

    reason: str = Field(
        description=(
            "Short explanation of why the evidence supports "
            "or does not sufficiently support the claim."
        )
    )


class VerificationOutput(BaseModel):

    claims: list[VerifiedClaim] = Field(
        default_factory=list,
        description=(
            "Structured factual claims derived only from "
            "the supplied evidence."
        )
    )

    open_questions: list[str] = Field(
        default_factory=list,
        description=(
            "Important questions not resolved by the "
            "retrieved evidence."
        )
    )


# ============================================================
# SEMANTIC ENTAILMENT OUTPUT
# ============================================================

class EntailmentDecision(BaseModel):

    claim_id: str = Field(
        description="Claim identifier being evaluated."
    )

    supported: bool = Field(
        description=(
            "True only when the official evidence directly "
            "supports the complete claim."
        )
    )

    support_level: Literal[
        "DIRECT",
        "PARTIAL",
        "INSUFFICIENT"
    ] = Field(
        description="Strength of semantic support."
    )

    supporting_source_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Official source identifiers that directly "
            "support the claim."
        )
    )

    supporting_excerpt_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Exact official excerpts that directly "
            "support the claim."
        )
    )

    reason: str = Field(
        description="Explanation of the semantic decision."
    )


class EntailmentOutput(BaseModel):

    decisions: list[EntailmentDecision] = Field(
        default_factory=list,
        description=(
            "Semantic support decision for every "
            "candidate claim."
        )
    )