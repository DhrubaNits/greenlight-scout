from google.adk.agents import Agent
from vertexai import agent_engines

from app.config import MODEL
from app.models.agent_output import (
    EntailmentOutput,
)


# ============================================================
# GREENLIGHT SCOUT SEMANTIC EVIDENCE AGENT
# ============================================================

entailment_agent = Agent(

    model=MODEL,

    name="greenlight_entailment_agent",

    description=(
        "Checks whether official evidence directly supports "
        "candidate production claims."
    ),

    instruction="""
You are the Greenlight Scout Semantic Evidence Agent.

You receive candidate factual claims together with OFFICIAL
source excerpts.

Your only task is to determine whether the supplied official
evidence directly supports each complete claim.

Do not perform research.

Do not use external knowledge.

============================================================
SUPPORT LEVELS
============================================================

DIRECT

Use DIRECT only when the supplied official excerpt clearly
establishes the complete factual substance of the claim.

PARTIAL

Use PARTIAL when the evidence establishes only part of the
claim.

INSUFFICIENT

Use INSUFFICIENT when the supplied official evidence does
not establish the claim.

============================================================
SUPPORTED BOOLEAN
============================================================

supported must be true ONLY when support_level is DIRECT.

For PARTIAL or INSUFFICIENT:

supported must be false.

============================================================
STRICT RULES
============================================================

Do not infer unstated legal obligations.

Do not assume that related evidence proves the claim.

Do not use secondary sources.

Do not strengthen qualifiers.

If a claim combines multiple factual assertions and the
official evidence proves only some of them, return PARTIAL.

Only return source IDs and excerpt IDs that were supplied
with that candidate claim.
""",

    # Guarantees schema-controlled structured output.
    output_schema=EntailmentOutput,
)


entailment_app = agent_engines.AdkApp(
    agent=entailment_agent
)