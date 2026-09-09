import asyncio
import json
import os
import re
from urllib.parse import urlparse

from google.adk.agents import Agent
from vertexai import agent_engines
from parallel import Parallel


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "gemini-2.5-flash"

PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY")

if not PARALLEL_API_KEY:
    raise RuntimeError(
        "PARALLEL_API_KEY is not set.\n"
        'Run: $env:PARALLEL_API_KEY="YOUR_KEY"'
    )

parallel_client = Parallel(
    api_key=PARALLEL_API_KEY
)

research_cache = {}


# ============================================================
# SOURCE AUTHORITY
# ============================================================

def classify_source_authority(url: str) -> str:

    hostname = (
        urlparse(str(url)).hostname
        or ""
    ).lower()

    if hostname.endswith("tfl.gov.uk"):
        return "OFFICIAL_TRANSPORT"

    if hostname.endswith(".police.uk"):
        return "OFFICIAL_POLICE"

    if hostname.endswith("filmlondon.org.uk"):
        return "OFFICIAL_FILM_COMMISSION"

    if hostname.endswith("caa.co.uk"):
        return "OFFICIAL_REGULATOR"

    if hostname.endswith("nats.aero"):
        return "OFFICIAL_AVIATION"

    if hostname.endswith(".gov.uk"):
        return "OFFICIAL_GOVERNMENT"

    return "SECONDARY"


def is_official_authority(
    authority_level: str
) -> bool:

    return authority_level.startswith(
        "OFFICIAL_"
    )


# ============================================================
# JSON CLEANING
# ============================================================

def clean_json_response(text: str) -> str:

    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if (
        first_brace != -1
        and last_brace != -1
    ):
        text = text[
            first_brace:last_brace + 1
        ]

    return text.strip()


# ============================================================
# TOOL 1
# SCENE ANALYSIS
# ============================================================

def analyze_scene_requirements(
    scene_description: str
) -> dict:

    print(
        "\n>>> TOOL CALLED: "
        "analyze_scene_requirements\n"
    )

    text = scene_description.lower()

    result = {

        "night_shoot":
            "night" in text,

        "drone_required":
            (
                "drone" in text
                or "aerial" in text
            ),

        "road_closure_required":
            (
                "road closure" in text
                or "close the road" in text
                or "street closure" in text
            ),

        "emergency_vehicle":
            (
                "police" in text
                or "ambulance" in text
                or "emergency vehicle" in text
            ),

        "crowd_present":
            (
                "background actors" in text
                or "extras" in text
                or "crowd" in text
            ),

        "special_effects":
            (
                "explosion" in text
                or "pyrotechnic" in text
                or "smoke effect" in text
                or "fire effect" in text
            ),

        "research_required": True
    }

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    return result


# ============================================================
# TOOL 2
# PARALLEL SEARCH
# ============================================================

def research_filming_requirements(
    location: str,
    research_objective: str
) -> dict:

    normalized_location = (
        location.lower().strip()
    )

    if (
        normalized_location
        in research_cache
    ):

        print(
            "\n>>> USING CACHED "
            "PARALLEL RESULT:",
            location,
            "\n"
        )

        return research_cache[
            normalized_location
        ]

    print(
        "\n>>> TOOL CALLED: "
        "research_filming_requirements"
    )

    print(
        ">>> PARALLEL SEARCH EXECUTING"
    )

    print(
        f">>> Location: {location}"
    )

    search = parallel_client.search(

        objective=(
            f"{research_objective}. "
            f"The proposed filming location "
            f"is {location}. "
            "Find current evidence about "
            "professional filming permissions, "
            "drone restrictions, road closures, "
            "police coordination, public-location "
            "requirements, night filming and "
            "operational restrictions. "
            "Prioritize official government, "
            "police, aviation, transport, "
            "local authority and film commission "
            "sources."
        ),

        search_queries=[
            f"{location} filming permission",
            f"{location} drone filming rules",
            f"{location} filming road closure",
        ]
    )

    sources = []

    for source_number, item in enumerate(
        search.results[:10],
        start=1
    ):

        source_id = (
            f"S{source_number}"
        )

        url = str(
            item.url
        )

        excerpts = []

        for excerpt_number, excerpt in enumerate(
            item.excerpts[:4]
            if item.excerpts
            else [],
            start=1
        ):

            excerpts.append(
                {
                    "excerpt_id":
                        (
                            f"{source_id}"
                            f"-E{excerpt_number}"
                        ),

                    "text":
                        str(excerpt)
                }
            )

        sources.append(
            {
                "source_id":
                    source_id,

                "title":
                    str(item.title),

                "url":
                    url,

                "publish_date":
                    (
                        str(item.publish_date)
                        if item.publish_date
                        else None
                    ),

                "authority_level":
                    classify_source_authority(
                        url
                    ),

                "excerpts":
                    excerpts
            }
        )

    response = {

        "location":
            location,

        "research_objective":
            research_objective,

        "sources":
            sources
    }

    research_cache[
        normalized_location
    ] = response

    print(
        f">>> PARALLEL RETURNED "
        f"{len(sources)} SOURCES\n"
    )

    return response


# ============================================================
# AGENT 1
# RESEARCH AGENT
# ============================================================

research_agent = Agent(

    model=MODEL,

    name="greenlight_research_agent",

    description=(
        "Retrieves current filmmaking "
        "evidence through Parallel Search."
    ),

    instruction="""
You are the Greenlight Scout Research Agent.

Your only responsibility is gathering evidence.

MANDATORY FLOW:

1. Call analyze_scene_requirements exactly once.

2. Call research_filming_requirements exactly once.

3. The single research request must cover all relevant
   aspects of the scene together.

4. Do not make separate calls for drones, roads, police,
   actors, or night filming.

5. Never invent regulatory facts.

6. After research finishes return only:

RESEARCH_COMPLETE
""",

    tools=[
        analyze_scene_requirements,
        research_filming_requirements
    ]
)


research_app = agent_engines.AdkApp(
    agent=research_agent
)


# ============================================================
# AGENT 2
# CLAIM EXTRACTION / VERIFICATION
# ============================================================

verification_agent = Agent(

    model=MODEL,

    name="greenlight_claim_verifier",

    description=(
        "Creates structured claims from "
        "retrieved Parallel evidence."
    ),

    instruction="""
You are the Greenlight Scout Claim Verification Agent.

Use ONLY evidence contained in the prompt.

Do not rely on your general knowledge.

For every factual regulatory or operational claim,
return structured evidence references.

A claim may be VERIFIED only if the supplied evidence
appears to support it.

If evidence is uncertain, secondary-only, incomplete,
or location-specific applicability is unclear, use:

REQUIRES_CONFIRMATION

Never invent:

- fees
- timelines
- legal duties
- permit names
- penalties
- insurance requirements
- police requirements
- restrictions

Preserve qualifiers.

If evidence says "may", never change that to "must".

Return ONLY JSON:

{
  "claims": [
    {
      "claim_id": "C1",
      "category": "DRONE",
      "statement": "Claim",
      "status": "VERIFIED",
      "source_ids": ["S1"],
      "excerpt_ids": ["S1-E1"],
      "reason": "Reason"
    }
  ],
  "open_questions": [
    "Question"
  ]
}
"""
)


verification_app = agent_engines.AdkApp(
    agent=verification_agent
)


# ============================================================
# AGENT 3
# SEMANTIC ENTAILMENT AGENT
# ============================================================

entailment_agent = Agent(

    model=MODEL,

    name="greenlight_entailment_agent",

    description=(
        "Checks whether official evidence "
        "directly supports candidate claims."
    ),

    instruction="""
You are the Greenlight Scout Evidence Entailment Agent.

Your only task is to determine whether an OFFICIAL
source excerpt directly supports each candidate claim.

You are NOT a research agent.

You have no web access.

Do not use general knowledge.

For each candidate claim:

DIRECT means:
The official excerpt itself clearly establishes the
substance of the claim.

PARTIAL means:
The excerpt supports only part of the claim.

INSUFFICIENT means:
The excerpt does not establish the claim.

STRICT RULES:

1. Do not infer legal requirements not stated.

2. Do not accept a claim because it merely sounds
   reasonable.

3. Do not accept a claim because another secondary
   source supports it.

4. Only the official excerpts supplied for that claim
   count.

5. Preserve qualifiers exactly.

6. If the claim is broader or stronger than the excerpt,
   it is not DIRECT.

7. If multiple facts are combined into one claim and
   the official evidence supports only some of them,
   use PARTIAL.

Return ONLY JSON:

{
  "decisions": [
    {
      "claim_id": "C1",
      "supported": true,
      "support_level": "DIRECT",
      "supporting_source_ids": ["S1"],
      "supporting_excerpt_ids": ["S1-E1"],
      "reason": "The official excerpt directly states..."
    }
  ]
}

Allowed support_level:

DIRECT
PARTIAL
INSUFFICIENT

supported must be true ONLY when support_level is DIRECT.
"""
)


entailment_app = agent_engines.AdkApp(
    agent=entailment_agent
)


# ============================================================
# GENERIC ADK RUNNER
# ============================================================

async def run_agent(
    app,
    user_id: str,
    message: str
) -> str:

    final_text = ""

    async for event in app.async_stream_query(
        user_id=user_id,
        message=message
    ):

        content = event.get(
            "content"
        )

        if not content:
            continue

        for part in content.get(
            "parts",
            []
        ):

            if "function_call" in part:

                function_call = (
                    part["function_call"]
                )

                print(
                    "\nAGENT REQUESTED TOOL:",
                    function_call.get(
                        "name"
                    )
                )

            if "text" in part:

                final_text = (
                    part["text"]
                )

    return final_text


# ============================================================
# BASIC STRUCTURAL VALIDATION
# ============================================================

def structural_validate_claims(
    verifier_output: dict,
    evidence: dict
) -> dict:

    source_map = {
        source["source_id"]: source
        for source in evidence["sources"]
    }

    excerpt_map = {}

    for source in evidence["sources"]:

        for excerpt in source[
            "excerpts"
        ]:

            excerpt_map[
                excerpt["excerpt_id"]
            ] = {
                "source_id":
                    source["source_id"],

                "text":
                    excerpt["text"]
            }

    candidate_verified = []

    requires_confirmation = []

    for original_claim in verifier_output.get(
        "claims",
        []
    ):

        claim = dict(
            original_claim
        )

        requested_status = claim.get(
            "status",
            "REQUIRES_CONFIRMATION"
        )

        source_ids = claim.get(
            "source_ids",
            []
        )

        excerpt_ids = claim.get(
            "excerpt_ids",
            []
        )

        errors = []

        # --------------------------------------------
        # Validate IDs
        # --------------------------------------------

        for source_id in source_ids:

            if source_id not in source_map:

                errors.append(
                    f"Unknown source: "
                    f"{source_id}"
                )

        for excerpt_id in excerpt_ids:

            if excerpt_id not in excerpt_map:

                errors.append(
                    f"Unknown excerpt: "
                    f"{excerpt_id}"
                )

        # --------------------------------------------
        # Ensure excerpt belongs to cited source
        # --------------------------------------------

        for excerpt_id in excerpt_ids:

            if excerpt_id not in excerpt_map:
                continue

            parent_source = (
                excerpt_map[
                    excerpt_id
                ]["source_id"]
            )

            if (
                parent_source
                not in source_ids
            ):

                errors.append(
                    f"{excerpt_id} belongs "
                    f"to {parent_source}, "
                    "which was not cited."
                )

        # --------------------------------------------
        # Never upgrade verifier's
        # REQUIRES_CONFIRMATION
        # --------------------------------------------

        if (
            requested_status
            == "REQUIRES_CONFIRMATION"
        ):

            claim[
                "final_status"
            ] = (
                "REQUIRES_CONFIRMATION"
            )

            claim[
                "confirmation_reason"
            ] = claim.get(
                "reason",
                "Verifier requires confirmation."
            )

            if errors:
                claim[
                    "validation_errors"
                ] = errors

            requires_confirmation.append(
                claim
            )

            continue

        # --------------------------------------------
        # Candidate VERIFIED must contain evidence
        # --------------------------------------------

        if not source_ids:

            errors.append(
                "No cited sources."
            )

        if not excerpt_ids:

            errors.append(
                "No cited excerpts."
            )

        # --------------------------------------------
        # Candidate must contain at least one
        # official cited source.
        # --------------------------------------------

        official_source_found = False

        for source_id in source_ids:

            source = source_map.get(
                source_id
            )

            if (
                source
                and is_official_authority(
                    source[
                        "authority_level"
                    ]
                )
            ):

                official_source_found = True

        if not official_source_found:

            errors.append(
                "No official source cited."
            )

        if errors:

            claim[
                "final_status"
            ] = (
                "REQUIRES_CONFIRMATION"
            )

            claim[
                "validation_errors"
            ] = errors

            requires_confirmation.append(
                claim
            )

        else:

            # Not final VERIFIED yet.
            # Must pass semantic gate.
            claim[
                "final_status"
            ] = (
                "CANDIDATE_VERIFIED"
            )

            candidate_verified.append(
                claim
            )

    return {

        "candidate_verified":
            candidate_verified,

        "requires_confirmation":
            requires_confirmation,

        "open_questions":
            verifier_output.get(
                "open_questions",
                []
            )
    }


# ============================================================
# BUILD SEMANTIC-GATE INPUT
# ============================================================

def build_entailment_payload(
    candidate_claims: list,
    evidence: dict
) -> dict:

    source_map = {
        source["source_id"]: source
        for source in evidence["sources"]
    }

    excerpt_map = {}

    for source in evidence["sources"]:

        for excerpt in source[
            "excerpts"
        ]:

            excerpt_map[
                excerpt["excerpt_id"]
            ] = {
                "source_id":
                    source["source_id"],

                "text":
                    excerpt["text"]
            }

    payload_claims = []

    for claim in candidate_claims:

        official_evidence = []

        for excerpt_id in claim.get(
            "excerpt_ids",
            []
        ):

            excerpt = excerpt_map.get(
                excerpt_id
            )

            if not excerpt:
                continue

            source_id = excerpt[
                "source_id"
            ]

            source = source_map.get(
                source_id
            )

            if not source:
                continue

            # Critical:
            # secondary excerpts are NOT sent
            # to semantic verification.
            if not is_official_authority(
                source["authority_level"]
            ):
                continue

            official_evidence.append(
                {
                    "source_id":
                        source_id,

                    "excerpt_id":
                        excerpt_id,

                    "source_title":
                        source["title"],

                    "authority_level":
                        source[
                            "authority_level"
                        ],

                    "excerpt":
                        excerpt["text"]
                }
            )

        payload_claims.append(
            {
                "claim_id":
                    claim["claim_id"],

                "statement":
                    claim["statement"],

                "category":
                    claim.get(
                        "category",
                        "GENERAL"
                    ),

                "official_evidence":
                    official_evidence
            }
        )

    return {
        "candidate_claims":
            payload_claims
    }


# ============================================================
# FINAL SEMANTIC VALIDATION
# ============================================================

def apply_semantic_gate(
    structural_result: dict,
    entailment_output: dict,
    evidence: dict
) -> dict:

    source_map = {
        source["source_id"]: source
        for source in evidence["sources"]
    }

    excerpt_map = {}

    for source in evidence["sources"]:

        for excerpt in source[
            "excerpts"
        ]:

            excerpt_map[
                excerpt["excerpt_id"]
            ] = {
                "source_id":
                    source["source_id"],

                "text":
                    excerpt["text"]
            }

    decision_map = {
        decision.get(
            "claim_id"
        ): decision

        for decision
        in entailment_output.get(
            "decisions",
            []
        )
    }

    final_verified = []

    requires_confirmation = list(
        structural_result[
            "requires_confirmation"
        ]
    )

    for claim in structural_result[
        "candidate_verified"
    ]:

        claim_id = claim[
            "claim_id"
        ]

        decision = decision_map.get(
            claim_id
        )

        errors = []

        if not decision:

            errors.append(
                "Semantic gate returned "
                "no decision."
            )

        else:

            supported = decision.get(
                "supported",
                False
            )

            support_level = decision.get(
                "support_level",
                "INSUFFICIENT"
            )

            support_source_ids = (
                decision.get(
                    "supporting_source_ids",
                    []
                )
            )

            support_excerpt_ids = (
                decision.get(
                    "supporting_excerpt_ids",
                    []
                )
            )

            if not supported:

                errors.append(
                    "Semantic gate did not "
                    "confirm direct support."
                )

            if support_level != "DIRECT":

                errors.append(
                    f"Support level is "
                    f"{support_level}, "
                    "not DIRECT."
                )

            if not support_source_ids:

                errors.append(
                    "No direct supporting "
                    "official source returned."
                )

            if not support_excerpt_ids:

                errors.append(
                    "No direct supporting "
                    "official excerpt returned."
                )

            # ----------------------------------------
            # Validate semantic gate IDs.
            # ----------------------------------------

            for source_id in (
                support_source_ids
            ):

                source = source_map.get(
                    source_id
                )

                if not source:

                    errors.append(
                        f"Unknown entailment "
                        f"source: {source_id}"
                    )

                    continue

                if not is_official_authority(
                    source[
                        "authority_level"
                    ]
                ):

                    errors.append(
                        f"{source_id} is not "
                        "an official source."
                    )

                if (
                    source_id
                    not in claim.get(
                        "source_ids",
                        []
                    )
                ):

                    errors.append(
                        f"{source_id} was not "
                        "originally cited by "
                        "the verifier."
                    )

            for excerpt_id in (
                support_excerpt_ids
            ):

                excerpt = excerpt_map.get(
                    excerpt_id
                )

                if not excerpt:

                    errors.append(
                        f"Unknown entailment "
                        f"excerpt: {excerpt_id}"
                    )

                    continue

                if (
                    excerpt_id
                    not in claim.get(
                        "excerpt_ids",
                        []
                    )
                ):

                    errors.append(
                        f"{excerpt_id} was not "
                        "originally cited."
                    )

                parent_source = (
                    excerpt[
                        "source_id"
                    ]
                )

                if (
                    parent_source
                    not in support_source_ids
                ):

                    errors.append(
                        f"{excerpt_id} belongs "
                        f"to {parent_source}, "
                        "which semantic gate did "
                        "not cite."
                    )

        # --------------------------------------------
        # FINAL DECISION
        # --------------------------------------------

        if errors:

            claim[
                "final_status"
            ] = (
                "REQUIRES_CONFIRMATION"
            )

            claim[
                "semantic_validation_errors"
            ] = errors

            if decision:

                claim[
                    "semantic_reason"
                ] = decision.get(
                    "reason"
                )

            requires_confirmation.append(
                claim
            )

        else:

            claim[
                "final_status"
            ] = "VERIFIED"

            # Replace broad original citations
            # with the official excerpts that
            # actually passed semantic validation.
            claim[
                "source_ids"
            ] = decision[
                "supporting_source_ids"
            ]

            claim[
                "excerpt_ids"
            ] = decision[
                "supporting_excerpt_ids"
            ]

            claim[
                "semantic_reason"
            ] = decision.get(
                "reason"
            )

            final_verified.append(
                claim
            )

    return {

        "validated_claims":
            final_verified,

        "requires_confirmation":
            requires_confirmation,

        "open_questions":
            structural_result[
                "open_questions"
            ]
    }


# ============================================================
# REPORT
# ============================================================

def source_sort_key(
    source_id: str
):

    try:
        return int(
            source_id.replace(
                "S",
                ""
            )
        )

    except Exception:
        return 999


def render_report(
    scene_description: str,
    validation_result: dict,
    evidence: dict
):

    source_map = {
        source["source_id"]: source
        for source in evidence["sources"]
    }

    verified = (
        validation_result[
            "validated_claims"
        ]
    )

    confirmation = (
        validation_result[
            "requires_confirmation"
        ]
    )

    print("\n")
    print("=" * 78)
    print("GREENLIGHT SCOUT")
    print(
        "SEMANTICALLY VALIDATED "
        "PRE-PRODUCTION REPORT"
    )
    print("=" * 78)

    print("\nSCENE\n")

    print(
        scene_description.strip()
    )

    # ========================================================
    # VERIFIED
    # ========================================================

    print("\n" + "-" * 78)
    print("VERIFIED FINDINGS")
    print("-" * 78)

    if not verified:

        print(
            "\nNo claims passed all "
            "evidence gates."
        )

    for claim in verified:

        citations = " ".join(
            f"[{source_id}]"
            for source_id
            in claim.get(
                "source_ids",
                []
            )
        )

        print(
            f"\n[{claim['claim_id']}] "
            f"{claim['statement']} "
            f"{citations}"
        )

        print(
            "Category:",
            claim.get(
                "category",
                "GENERAL"
            )
        )

    # ========================================================
    # REQUIRES CONFIRMATION
    # ========================================================

    print("\n" + "-" * 78)
    print("REQUIRES CONFIRMATION")
    print("-" * 78)

    if not confirmation:

        print(
            "\nNo claims require confirmation."
        )

    for claim in confirmation:

        print(
            f"\n[{claim.get('claim_id', '?')}] "
            f"{claim.get('statement', '')}"
        )

        print(
            "Category:",
            claim.get(
                "category",
                "GENERAL"
            )
        )

        if claim.get(
            "confirmation_reason"
        ):

            print(
                "Reason:",
                claim[
                    "confirmation_reason"
                ]
            )

        if claim.get(
            "semantic_reason"
        ):

            print(
                "Semantic reason:",
                claim[
                    "semantic_reason"
                ]
            )

        for error in claim.get(
            "validation_errors",
            []
        ):

            print(
                "Validation issue:",
                error
            )

        for error in claim.get(
            "semantic_validation_errors",
            []
        ):

            print(
                "Semantic issue:",
                error
            )

    # ========================================================
    # OPEN QUESTIONS
    # ========================================================

    print("\n" + "-" * 78)
    print("OPEN QUESTIONS")
    print("-" * 78)

    questions = (
        validation_result[
            "open_questions"
        ]
    )

    if not questions:

        print(
            "\nNo open questions."
        )

    for question in questions:

        print(
            f"\n- {question}"
        )

    # ========================================================
    # SOURCES
    # ========================================================

    print("\n" + "-" * 78)
    print("VERIFIED SOURCES")
    print("-" * 78)

    used_sources = set()

    for claim in verified:

        used_sources.update(
            claim.get(
                "source_ids",
                []
            )
        )

    for source_id in sorted(
        used_sources,
        key=source_sort_key
    ):

        source = source_map[
            source_id
        ]

        print(
            f"\n[{source_id}] "
            f"{source['title']}"
        )

        print(
            source["url"]
        )

        print(
            "Authority:",
            source[
                "authority_level"
            ]
        )

    print("\n" + "=" * 78)

    print(
        "Greenlight Scout supports "
        "pre-production research."
    )

    print(
        "It does not constitute legal "
        "or regulatory clearance."
    )

    print(
        "Final approval must be confirmed "
        "with the appropriate authorities."
    )

    print("=" * 78)


# ============================================================
# MAIN PIPELINE
# ============================================================

async def main():

    scene_description = """
Exterior night scene in Central London.

Requirements:
- drone establishing shot
- temporary road closure
- simulated police vehicle
- 25 background actors
"""

    # ========================================================
    # STAGE 1
    # RESEARCH
    # ========================================================

    print("\n")
    print("=" * 78)
    print("STAGE 1 - RESEARCH AGENT")
    print("=" * 78)

    research_prompt = f"""
Analyze the following proposed filming scene:

{scene_description}

Location: Central London.

Perform ONE combined research operation covering current:

- filming permissions
- drone restrictions
- road closures
- police coordination
- night filming
- background actors
- operational restrictions

Gather evidence only.
"""

    research_result = await run_agent(

        research_app,

        "greenlight_research",

        research_prompt
    )

    print(
        "\nResearch result:",
        research_result
    )

    if not research_cache:

        raise RuntimeError(
            "Parallel Search was not executed."
        )

    evidence = list(
        research_cache.values()
    )[-1]

    # ========================================================
    # STAGE 2
    # CLAIM VERIFICATION
    # ========================================================

    print("\n")
    print("=" * 78)
    print("STAGE 2 - CLAIM VERIFICATION AGENT")
    print("=" * 78)

    verifier_prompt = f"""
SCENE

{scene_description}

PARALLEL EVIDENCE

{json.dumps(
    evidence,
    indent=2,
    ensure_ascii=False
)}

Create structured claims using ONLY
this evidence.

Return JSON only.
"""

    verifier_text = await run_agent(

        verification_app,

        "greenlight_claim_verification",

        verifier_prompt
    )

    verifier_json = clean_json_response(
        verifier_text
    )

    try:

        verifier_output = json.loads(
            verifier_json
        )

    except json.JSONDecodeError as exc:

        print(
            "\nVerifier raw output:\n"
        )

        print(
            verifier_text
        )

        raise RuntimeError(
            "Verifier returned invalid JSON."
        ) from exc

    print(
        "\nVerifier proposed:",
        len(
            verifier_output.get(
                "claims",
                []
            )
        ),
        "claims"
    )

    # ========================================================
    # STAGE 3
    # STRUCTURAL PYTHON VALIDATION
    # ========================================================

    print("\n")
    print("=" * 78)
    print(
        "STAGE 3 - STRUCTURAL "
        "PYTHON VALIDATION"
    )
    print("=" * 78)

    structural_result = (
        structural_validate_claims(
            verifier_output,
            evidence
        )
    )

    print(
        "\nCandidate verified claims:",
        len(
            structural_result[
                "candidate_verified"
            ]
        )
    )

    print(
        "Already requires confirmation:",
        len(
            structural_result[
                "requires_confirmation"
            ]
        )
    )

    # ========================================================
    # STAGE 4
    # BUILD OFFICIAL-EVIDENCE-ONLY PAYLOAD
    # ========================================================

    entailment_payload = (
        build_entailment_payload(
            structural_result[
                "candidate_verified"
            ],
            evidence
        )
    )

    # ========================================================
    # STAGE 5
    # SEMANTIC ENTAILMENT AGENT
    # ========================================================

    print("\n")
    print("=" * 78)
    print(
        "STAGE 4 - SEMANTIC "
        "EVIDENCE GATE"
    )
    print("=" * 78)

    entailment_prompt = f"""
Evaluate these claims.

Use ONLY the official evidence provided
with each individual claim.

Do not use external knowledge.

{json.dumps(
    entailment_payload,
    indent=2,
    ensure_ascii=False
)}

Return JSON only.
"""

    entailment_text = await run_agent(

        entailment_app,

        "greenlight_entailment",

        entailment_prompt
    )

    entailment_json = clean_json_response(
        entailment_text
    )

    try:

        entailment_output = json.loads(
            entailment_json
        )

    except json.JSONDecodeError as exc:

        print(
            "\nEntailment raw output:\n"
        )

        print(
            entailment_text
        )

        raise RuntimeError(
            "Entailment Agent returned "
            "invalid JSON."
        ) from exc

    print(
        "\nSemantic decisions:",
        len(
            entailment_output.get(
                "decisions",
                []
            )
        )
    )

    # ========================================================
    # STAGE 5
    # FINAL PYTHON GATE
    # ========================================================

    print("\n")
    print("=" * 78)
    print(
        "STAGE 5 - FINAL "
        "DETERMINISTIC VALIDATION"
    )
    print("=" * 78)

    final_result = apply_semantic_gate(

        structural_result,

        entailment_output,

        evidence
    )

    print(
        "\nFINAL VERIFIED:",
        len(
            final_result[
                "validated_claims"
            ]
        )
    )

    print(
        "FINAL REQUIRES CONFIRMATION:",
        len(
            final_result[
                "requires_confirmation"
            ]
        )
    )

    # ========================================================
    # STAGE 6
    # REPORT
    # ========================================================

    print("\n")
    print("=" * 78)
    print("STAGE 6 - FINAL REPORT")
    print("=" * 78)

    render_report(

        scene_description,

        final_result,

        evidence
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )