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
        "Set it in PowerShell first:\n"
        '$env:PARALLEL_API_KEY="YOUR_KEY"'
    )

parallel_client = Parallel(
    api_key=PARALLEL_API_KEY
)

# In-memory cache.
# Ensures repeated agent requests for the same location do not
# generate additional Parallel Search API calls.
research_cache = {}


# ============================================================
# SOURCE AUTHORITY CLASSIFICATION
# ============================================================

def classify_source_authority(url: str) -> str:
    """
    Deterministically classify known authoritative domains.

    Gemini does NOT decide whether a source is official.
    Python does.
    """

    try:
        hostname = urlparse(str(url)).hostname or ""
    except Exception:
        hostname = ""

    hostname = hostname.lower()

    if hostname.endswith("tfl.gov.uk"):
        return "OFFICIAL_TRANSPORT"

    if hostname.endswith("cityoflondon.police.uk"):
        return "OFFICIAL_POLICE"

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


def is_official_authority(authority_level: str) -> bool:
    """
    True when Python considers the source authoritative.
    """

    return authority_level.startswith("OFFICIAL_")


# ============================================================
# JSON CLEANING
# ============================================================

def clean_json_response(text: str) -> str:
    """
    Removes markdown fences and extracts a JSON object if Gemini
    accidentally adds surrounding text.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove ```json ... ```
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

    text = text.strip()

    # Try to isolate first JSON object if extra prose exists.
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1:
        text = text[first_brace:last_brace + 1]

    return text.strip()


# ============================================================
# TOOL 1
# DETERMINISTIC SCENE ANALYSIS
# ============================================================

def analyze_scene_requirements(
    scene_description: str
) -> dict:
    """
    Detect important production elements from the proposed
    filming scene using deterministic Python logic.
    """

    print(
        "\n>>> TOOL CALLED: "
        "analyze_scene_requirements\n"
    )

    text = scene_description.lower()

    result = {
        "night_shoot": (
            "night" in text
        ),

        "drone_required": (
            "drone" in text
            or "aerial" in text
        ),

        "road_closure_required": (
            "road closure" in text
            or "close the road" in text
            or "street closure" in text
        ),

        "emergency_vehicle": (
            "police" in text
            or "ambulance" in text
            or "fire engine" in text
            or "emergency vehicle" in text
        ),

        "crowd_present": (
            "background actors" in text
            or "extras" in text
            or "crowd" in text
        ),

        "special_effects": (
            "explosion" in text
            or "pyrotechnic" in text
            or "fire effect" in text
            or "smoke effect" in text
            or "rain effect" in text
        ),

        "research_required": True
    }

    print(">>> SCENE ANALYSIS RESULT")

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
    """
    Retrieve current web evidence through Parallel Search.
    """

    normalized_location = (
        location
        .lower()
        .strip()
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # If Gemini asks for research again for the same location,
    # return previous results instead of calling Parallel again.
    # --------------------------------------------------------

    if normalized_location in research_cache:

        print(
            "\n>>> USING CACHED PARALLEL RESULT: "
            f"{location}\n"
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

    print(
        f">>> Objective: {research_objective}\n"
    )

    # --------------------------------------------------------
    # Parallel Search
    # --------------------------------------------------------

    search = parallel_client.search(

        objective=(
            f"{research_objective}. "
            f"The proposed professional filming location is "
            f"{location}. "
            "Find current evidence about filming permissions, "
            "drone restrictions, road closures, police "
            "coordination, public-location requirements, night "
            "filming considerations and operational restrictions. "
            "Prioritize government authorities, aviation "
            "regulators, transport authorities, police authorities, "
            "local authorities and official film commissions. "
            "Commercial sources may be returned only as secondary "
            "context."
        ),

        search_queries=[
            f"{location} filming permission",
            f"{location} drone filming rules",
            f"{location} filming road closure",
        ]
    )

    sources = []

    # --------------------------------------------------------
    # Turn Parallel results into structured evidence.
    #
    # Every source gets:
    #
    # S1
    # S2
    # etc.
    #
    # Every excerpt gets:
    #
    # S1-E1
    # S1-E2
    # etc.
    # --------------------------------------------------------

    for source_number, item in enumerate(
        search.results[:10],
        start=1
    ):

        source_id = f"S{source_number}"

        url = str(item.url)

        excerpts = []

        raw_excerpts = (
            item.excerpts
            if item.excerpts
            else []
        )

        for excerpt_number, excerpt in enumerate(
            raw_excerpts[:4],
            start=1
        ):

            excerpts.append(
                {
                    "excerpt_id": (
                        f"{source_id}-E{excerpt_number}"
                    ),
                    "text": str(excerpt)
                }
            )

        source = {
            "source_id": source_id,
            "title": str(item.title),
            "url": url,

            "publish_date": (
                str(item.publish_date)
                if item.publish_date
                else None
            ),

            "authority_level": (
                classify_source_authority(
                    url
                )
            ),

            "excerpts": excerpts
        }

        sources.append(source)

    response = {
        "location": location,
        "research_objective": research_objective,
        "sources": sources
    }

    # Cache the result.
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
# RESEARCH ORCHESTRATOR
# ============================================================

research_agent = Agent(

    model=MODEL,

    name="greenlight_research_agent",

    description=(
        "Research agent that identifies production requirements "
        "and retrieves current filming evidence through Parallel."
    ),

    instruction="""
You are the Greenlight Scout Research Agent.

You are responsible only for gathering evidence.

You do NOT provide the final production recommendation.

MANDATORY WORKFLOW

1. Call analyze_scene_requirements EXACTLY ONCE.

2. After receiving the scene analysis, call
   research_filming_requirements EXACTLY ONCE.

3. Use the filming location provided by the user.

4. The research objective should cover all relevant requirements
   together in one research request.

5. Do NOT make separate research calls for drones, roads,
   police, night filming, or crowds.

One single research_filming_requirements call must cover all
research topics.

6. Never invent legal, regulatory, financial, permit, safety
   or operational information.

7. After the research tool completes, respond only with:

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
# EVIDENCE VERIFICATION AGENT
# ============================================================

verification_agent = Agent(

    model=MODEL,

    name="greenlight_evidence_verifier",

    description=(
        "Evidence-verification agent that converts Parallel "
        "search evidence into structured, source-backed claims."
    ),

    instruction="""
You are the Greenlight Scout Evidence Verification Agent.

You receive evidence retrieved through Parallel Search.

YOU DO NOT HAVE WEB ACCESS.

Use ONLY the evidence included in the prompt.

Do not use your model knowledge for regulatory facts.

============================================================
CLAIM RULES
============================================================

Create individual factual claims from the supplied excerpts.

Every VERIFIED claim MUST contain:

- claim_id
- category
- statement
- status
- source_ids
- excerpt_ids
- reason

Allowed statuses:

VERIFIED
REQUIRES_CONFIRMATION

============================================================
VERIFIED
============================================================

A claim may be VERIFIED only when:

1. The supplied excerpt directly supports the claim.

2. At least one source_id is supplied.

3. At least one excerpt_id is supplied.

4. Regulatory, permit, financial, timing, legal,
   operational or safety claims have support from an
   authoritative source.

============================================================
REQUIRES_CONFIRMATION
============================================================

Use REQUIRES_CONFIRMATION when:

- evidence comes only from commercial/secondary sources
- evidence is incomplete
- evidence is ambiguous
- exact fee cannot be confirmed
- exact deadline cannot be confirmed
- exact permit requirement cannot be confirmed
- sources disagree
- the evidence does not specifically apply to this scenario

Never upgrade weak evidence into a factual statement.

============================================================
PROHIBITED BEHAVIOR
============================================================

Never invent:

- permit fees
- processing times
- legal requirements
- notice periods
- insurance requirements
- permit names
- authority requirements
- police requirements
- fines
- penalties
- drone restrictions

Do not strengthen the source's wording.

If the source says "may", your claim must not say "must".

If the source says "typically", your claim must not say
"always".

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

No Markdown.
No explanation outside JSON.

Use exactly this structure:

{
  "claims": [
    {
      "claim_id": "C1",
      "category": "DRONE",
      "statement": "Claim text",
      "status": "VERIFIED",
      "source_ids": ["S1"],
      "excerpt_ids": ["S1-E1"],
      "reason": "Explanation of why the excerpt supports it"
    }
  ],
  "open_questions": [
    "Question requiring further confirmation"
  ]
}
"""
)


verification_app = agent_engines.AdkApp(
    agent=verification_agent
)


# ============================================================
# GENERIC ADK RUNNER
# ============================================================

async def run_agent(
    app,
    user_id: str,
    message: str
) -> str:
    """
    Execute an ADK app and return its last natural-language
    response.
    """

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

        parts = content.get(
            "parts",
            []
        )

        for part in parts:

            # ------------------------------------------------
            # Show tool decisions for development visibility.
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Capture natural language / JSON output.
            # ------------------------------------------------

            if "text" in part:

                final_text = (
                    part["text"]
                )

    return final_text


# ============================================================
# DETERMINISTIC PYTHON CLAIM VALIDATOR
# ============================================================

def validate_claims(
    verifier_output: dict,
    evidence: dict
) -> dict:
    """
    Deterministic evidence validation.

    CRITICAL RULE:

    Python may DOWNGRADE:

        VERIFIED
            ->
        REQUIRES_CONFIRMATION

    Python must NEVER upgrade:

        REQUIRES_CONFIRMATION
            ->
        VERIFIED
    """

    # --------------------------------------------------------
    # Build lookup maps.
    # --------------------------------------------------------

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
                "source_id": (
                    source["source_id"]
                ),
                "text": (
                    excerpt["text"]
                )
            }

    validated_claims = []

    requires_confirmation = []

    allowed_statuses = {
        "VERIFIED",
        "REQUIRES_CONFIRMATION"
    }

    # --------------------------------------------------------
    # Validate every proposed claim.
    # --------------------------------------------------------

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

        validation_errors = []

        # ----------------------------------------------------
        # Check status.
        # ----------------------------------------------------

        if requested_status not in allowed_statuses:

            validation_errors.append(
                (
                    "Invalid verifier status: "
                    f"{requested_status}"
                )
            )

        # ----------------------------------------------------
        # Ensure source IDs exist.
        # ----------------------------------------------------

        for source_id in source_ids:

            if source_id not in source_map:

                validation_errors.append(
                    (
                        "Unknown source ID: "
                        f"{source_id}"
                    )
                )

        # ----------------------------------------------------
        # Ensure excerpt IDs exist.
        # ----------------------------------------------------

        for excerpt_id in excerpt_ids:

            if excerpt_id not in excerpt_map:

                validation_errors.append(
                    (
                        "Unknown excerpt ID: "
                        f"{excerpt_id}"
                    )
                )

        # ----------------------------------------------------
        # Ensure cited excerpts belong to cited sources.
        # ----------------------------------------------------

        for excerpt_id in excerpt_ids:

            if excerpt_id not in excerpt_map:
                continue

            parent_source_id = (
                excerpt_map[
                    excerpt_id
                ]["source_id"]
            )

            if parent_source_id not in source_ids:

                validation_errors.append(
                    (
                        f"{excerpt_id} belongs to "
                        f"{parent_source_id}, but "
                        "that source was not cited."
                    )
                )

        # ====================================================
        # IMPORTANT FIX
        #
        # Gemini already decided evidence is insufficient.
        #
        # Python MUST NOT upgrade it.
        # ====================================================

        if (
            requested_status
            == "REQUIRES_CONFIRMATION"
        ):

            claim[
                "final_status"
            ] = "REQUIRES_CONFIRMATION"

            claim[
                "confirmation_reason"
            ] = claim.get(
                "reason",
                (
                    "Evidence verifier determined "
                    "that this claim requires "
                    "confirmation."
                )
            )

            if validation_errors:

                claim[
                    "validation_errors"
                ] = validation_errors

            requires_confirmation.append(
                claim
            )

            continue

        # ====================================================
        # From this point the verifier requested VERIFIED.
        #
        # Python now checks whether VERIFIED is allowed.
        # ====================================================

        if not source_ids:

            validation_errors.append(
                "Verified claim has no source."
            )

        if not excerpt_ids:

            validation_errors.append(
                "Verified claim has no supporting excerpt."
            )

        # ----------------------------------------------------
        # Verified regulatory claims require an official
        # authority source.
        # ----------------------------------------------------

        official_source_found = False

        for source_id in source_ids:

            source = source_map.get(
                source_id
            )

            if not source:
                continue

            authority_level = source.get(
                "authority_level",
                "SECONDARY"
            )

            if is_official_authority(
                authority_level
            ):

                official_source_found = True

                break

        if not official_source_found:

            validation_errors.append(
                (
                    "No official authority source "
                    "supports this verified claim."
                )
            )

        # ----------------------------------------------------
        # Final decision.
        # ----------------------------------------------------

        if validation_errors:

            claim[
                "final_status"
            ] = "REQUIRES_CONFIRMATION"

            claim[
                "validation_errors"
            ] = validation_errors

            requires_confirmation.append(
                claim
            )

        else:

            claim[
                "final_status"
            ] = "VERIFIED"

            validated_claims.append(
                claim
            )

    return {
        "validated_claims": (
            validated_claims
        ),

        "requires_confirmation": (
            requires_confirmation
        ),

        "open_questions": verifier_output.get(
            "open_questions",
            []
        )
    }


# ============================================================
# SOURCE SORTING
# ============================================================

def source_sort_key(
    source_id: str
) -> int:
    """
    Make S2 come before S10.
    """

    try:
        return int(
            source_id.replace(
                "S",
                ""
            )
        )

    except ValueError:
        return 999999


# ============================================================
# FINAL DETERMINISTIC REPORT
# ============================================================

def render_report(
    scene_description: str,
    validation_result: dict,
    evidence: dict
):
    """
    Render the final report using Python only.

    Gemini is not allowed to introduce additional facts here.
    """

    source_map = {
        source["source_id"]: source
        for source in evidence["sources"]
    }

    verified_claims = validation_result[
        "validated_claims"
    ]

    confirmation_claims = validation_result[
        "requires_confirmation"
    ]

    open_questions = validation_result[
        "open_questions"
    ]

    print("\n")
    print("=" * 78)
    print("GREENLIGHT SCOUT")
    print(
        "EVIDENCE-VALIDATED "
        "PRE-PRODUCTION REPORT"
    )
    print("=" * 78)

    # ========================================================
    # Scene
    # ========================================================

    print("\nSCENE\n")

    print(
        scene_description.strip()
    )

    # ========================================================
    # Verified
    # ========================================================

    print("\n" + "-" * 78)
    print("VERIFIED FINDINGS")
    print("-" * 78)

    if not verified_claims:

        print(
            "\nNo claims passed evidence verification."
        )

    for claim in verified_claims:

        citation_text = " ".join(
            f"[{source_id}]"
            for source_id
            in claim.get(
                "source_ids",
                []
            )
        )

        print(
            f"\n[{claim.get('claim_id', '?')}] "
            f"{claim.get('statement', '')} "
            f"{citation_text}"
        )

        print(
            "Category:",
            claim.get(
                "category",
                "GENERAL"
            )
        )

    # ========================================================
    # Requires confirmation
    # ========================================================

    print("\n" + "-" * 78)
    print("REQUIRES CONFIRMATION")
    print("-" * 78)

    if not confirmation_claims:

        print(
            "\nNo claims require confirmation."
        )

    for claim in confirmation_claims:

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

        reason = claim.get(
            "confirmation_reason"
        )

        if reason:

            print(
                "Reason:",
                reason
            )

        for error in claim.get(
            "validation_errors",
            []
        ):

            print(
                "Validation issue:",
                error
            )

    # ========================================================
    # Open questions
    # ========================================================

    print("\n" + "-" * 78)
    print("OPEN QUESTIONS")
    print("-" * 78)

    if not open_questions:

        print(
            "\nNo additional open questions."
        )

    for question in open_questions:

        print(
            f"\n- {question}"
        )

    # ========================================================
    # Sources
    # ========================================================

    print("\n" + "-" * 78)
    print("SOURCES")
    print("-" * 78)

    # Include sources referenced by both verified and
    # requires-confirmation claims.
    used_source_ids = set()

    for claim in (
        verified_claims
        + confirmation_claims
    ):

        for source_id in claim.get(
            "source_ids",
            []
        ):

            if source_id in source_map:

                used_source_ids.add(
                    source_id
                )

    if not used_source_ids:

        print(
            "\nNo cited sources."
        )

    for source_id in sorted(
        used_source_ids,
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

        if source.get(
            "publish_date"
        ):

            print(
                "Published:",
                source[
                    "publish_date"
                ]
            )

    # ========================================================
    # Disclaimer
    # ========================================================

    print("\n" + "=" * 78)

    print(
        "This report supports pre-production research. "
        "It does not constitute legal clearance."
    )

    print(
        "Final permissions must be confirmed with the "
        "appropriate authorities and production professionals."
    )

    print("=" * 78)


# ============================================================
# MAIN MULTI-AGENT PIPELINE
# ============================================================

async def main():

    # --------------------------------------------------------
    # Test scene
    # --------------------------------------------------------

    scene_description = """
Exterior night scene in central London.

Requirements:
- drone establishing shot
- temporary road closure
- simulated police vehicle
- 25 background actors
"""

    # ========================================================
    # STAGE 1
    # Research Agent
    # ========================================================

    print("\n")
    print("=" * 78)
    print("STAGE 1 - RESEARCH AGENT")
    print("=" * 78)

    research_prompt = f"""
Analyze this proposed filming scene:

{scene_description}

The filming location is Central London.

Research all current permissions, restrictions and
operational issues that must be investigated before the
production team considers greenlighting this scene.

Perform ONE combined research operation covering the entire
scene.
"""

    research_result_text = await run_agent(
        app=research_app,
        user_id="greenlight_research_session",
        message=research_prompt
    )

    print(
        "\nResearch agent result:",
        research_result_text
    )

    # --------------------------------------------------------
    # Ensure Parallel was actually called.
    # --------------------------------------------------------

    if not research_cache:

        raise RuntimeError(
            "Parallel Search did not execute."
        )

    # Current POC has one filming location.
    evidence = list(
        research_cache.values()
    )[-1]

    # ========================================================
    # STAGE 2
    # Evidence Verification Agent
    # ========================================================

    print("\n")
    print("=" * 78)
    print(
        "STAGE 2 - EVIDENCE VERIFICATION AGENT"
    )
    print("=" * 78)

    verifier_prompt = f"""
SCENE

{scene_description}

PARALLEL SEARCH EVIDENCE

{json.dumps(
    evidence,
    indent=2,
    ensure_ascii=False
)}

Using ONLY the supplied evidence, create factual claims.

Follow your verification rules strictly.

Regulatory information supported only by secondary sources
must be marked REQUIRES_CONFIRMATION.

Return only JSON.
"""

    verifier_text = await run_agent(
        app=verification_app,
        user_id="greenlight_verification_session",
        message=verifier_prompt
    )

    print(
        "\nRAW VERIFIER RESPONSE\n"
    )

    print(
        verifier_text
    )

    # --------------------------------------------------------
    # Clean and parse JSON.
    # --------------------------------------------------------

    cleaned_json = clean_json_response(
        verifier_text
    )

    try:

        verifier_output = json.loads(
            cleaned_json
        )

    except json.JSONDecodeError as exc:

        print(
            "\nINVALID JSON RECEIVED FROM "
            "VERIFICATION AGENT:\n"
        )

        print(
            cleaned_json
        )

        raise RuntimeError(
            (
                "Evidence Verification Agent "
                "did not return valid JSON."
            )
        ) from exc

    # ========================================================
    # STAGE 3
    # Deterministic Python Validation
    # ========================================================

    print("\n")
    print("=" * 78)
    print(
        "STAGE 3 - DETERMINISTIC "
        "PYTHON VALIDATION"
    )
    print("=" * 78)

    validation_result = validate_claims(
        verifier_output=verifier_output,
        evidence=evidence
    )

    verified_count = len(
        validation_result[
            "validated_claims"
        ]
    )

    confirmation_count = len(
        validation_result[
            "requires_confirmation"
        ]
    )

    print(
        "\nValidated claims:",
        verified_count
    )

    print(
        "Claims requiring confirmation:",
        confirmation_count
    )

    # ========================================================
    # STAGE 4
    # Deterministic Final Report
    # ========================================================

    print("\n")
    print("=" * 78)
    print(
        "STAGE 4 - FINAL REPORT"
    )
    print("=" * 78)

    render_report(
        scene_description=scene_description,
        validation_result=validation_result,
        evidence=evidence
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )