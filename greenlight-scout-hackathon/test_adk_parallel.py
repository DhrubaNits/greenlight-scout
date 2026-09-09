import asyncio
import os

from google.adk.agents import Agent
from vertexai import agent_engines
from parallel import Parallel


# ============================================================
# CONFIGURATION
# ============================================================

PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY")

if not PARALLEL_API_KEY:
    raise RuntimeError(
        "PARALLEL_API_KEY is not set. "
        "Set it in PowerShell before running this script."
    )


parallel_client = Parallel(
    api_key=PARALLEL_API_KEY
)


# ============================================================
# SIMPLE IN-MEMORY CACHE
#
# Prevents the same location from triggering Parallel Search
# multiple times during one agent execution.
# ============================================================

research_cache = {}


# ============================================================
# TOOL 1: SCENE REQUIREMENT ANALYSIS
# ============================================================

def analyze_scene_requirements(scene_description: str) -> dict:
    """
    Detect important production requirements from a film scene.

    This is intentionally deterministic Python logic.
    """

    print("\n>>> TOOL CALLED: analyze_scene_requirements\n")

    text = scene_description.lower()

    result = {
        "night_shoot": "night" in text,

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

        "large_crowd": (
            "background actors" in text
            or "extras" in text
            or "crowd" in text
        ),

        "special_effects": (
            "explosion" in text
            or "fire" in text
            or "smoke" in text
            or "rain effect" in text
            or "special effect" in text
        ),

        "next_action": (
            "Research current permits, restrictions, "
            "safety requirements, and operational constraints."
        )
    }

    print("Scene analysis result:")
    print(result)

    return result


# ============================================================
# TOOL 2: PARALLEL WEB SEARCH
# ============================================================

def research_filming_requirements(
    location: str,
    research_objective: str
) -> dict:
    """
    Uses Parallel Search API to retrieve current web evidence
    for filming permits, restrictions, and production risks.
    """

    normalized_location = location.lower().strip()

    # --------------------------------------------------------
    # Prevent duplicate API calls for the same location
    # during this run.
    # --------------------------------------------------------

    if normalized_location in research_cache:
        print(
            "\n>>> USING CACHED PARALLEL RESULT "
            f"FOR: {location}\n"
        )

        return research_cache[normalized_location]

    print("\n>>> TOOL CALLED: research_filming_requirements")
    print(">>> PARALLEL SEARCH EXECUTING")
    print(f">>> Location: {location}")
    print(f">>> Objective: {research_objective}\n")

    # --------------------------------------------------------
    # Parallel Search API
    # --------------------------------------------------------

    search = parallel_client.search(
        objective=(
            f"{research_objective} "
            f"The proposed filming location is {location}. "
            "Find current and reliable information relevant to "
            "professional film production. "
            "Prioritize official government agencies, "
            "local authorities, transport authorities, "
            "aviation regulators, police authorities, "
            "and official film commissions. "
            "Commercial websites may be included only as "
            "secondary context."
        ),

        search_queries=[
            f"{location} filming permit",
            f"{location} drone filming rules",
            f"{location} filming road closure",
        ],
    )

    sources = []

    # --------------------------------------------------------
    # Convert Parallel results into structured evidence
    # records.
    # --------------------------------------------------------

    for index, item in enumerate(
        search.results[:10],
        start=1
    ):

        source_id = f"S{index}"

        source = {
            "source_id": source_id,
            "title": item.title,
            "url": item.url,

            "publish_date": (
                str(item.publish_date)
                if item.publish_date
                else None
            ),

            "excerpts": (
                item.excerpts[:3]
                if item.excerpts
                else []
            )
        }

        sources.append(source)

    response = {
        "location": location,
        "research_objective": research_objective,
        "result_count": len(sources),
        "sources": sources
    }

    # --------------------------------------------------------
    # Store result so that repeated agent calls do not cost
    # another Parallel Search request.
    # --------------------------------------------------------

    research_cache[normalized_location] = response

    print(
        f">>> PARALLEL SEARCH COMPLETE: "
        f"{len(sources)} sources returned\n"
    )

    return response


# ============================================================
# GOOGLE ADK AGENT
# ============================================================

agent = Agent(
    model="gemini-2.5-flash",

    name="greenlight_scout",

    description=(
        "Evidence-first agentic pre-production intelligence "
        "assistant for filmmakers and production teams."
    ),

    instruction="""

You are Greenlight Scout.

You are an evidence-first pre-production intelligence agent
for professional filmmakers and film production teams.

Your job is to help production teams identify operational,
permit, safety, logistical, and regulatory risks BEFORE they
approve a filming scene.

============================================================
MANDATORY WORKFLOW
============================================================

For every proposed filming scene:

STEP 1
ALWAYS call:

analyze_scene_requirements

before doing anything else.

STEP 2

Review the tool response.

If the scene contains anything involving:

- drones
- road closures
- public streets
- police or emergency vehicles
- night filming
- crowds
- special effects
- public locations
- permits
- safety restrictions
- local regulations
- current operational information

you MUST call:

research_filming_requirements

STEP 3

Use the filming location provided by the user.

Create a clear research objective describing exactly what
must be investigated.

STEP 4

Use the evidence returned from Parallel Search.

============================================================
SOURCE PRIORITY
============================================================

Sources do NOT have equal authority.

Prefer sources in approximately this order:

1. National government or regulatory authority

2. Local government / local authority

3. Aviation authority

4. Police authority

5. Transport authority

6. Official film commission

7. Venue owner / official location operator

8. Reputable professional or industry source

9. Commercial blog or other secondary source


Commercial sources may provide context.

However:

COMMERCIAL SOURCES MUST NOT OVERRIDE OFFICIAL SOURCES.

============================================================
STRICT EVIDENCE RULES
============================================================

Every factual claim involving:

- regulations
- permits
- fees
- dates
- timelines
- notice periods
- legal restrictions
- police requirements
- drone restrictions
- road restrictions
- operational requirements
- insurance requirements
- safety requirements

MUST have supporting evidence from the Parallel results.

Use the source IDs supplied by the tool.

Example:

Drone operations may require additional authorization
in restricted airspace [S3].

Never create or assume:

- permit fees
- processing times
- legal requirements
- permit names
- authority names
- insurance limits
- notice periods
- opening hours
- police requirements
- fines
- restrictions

unless they appear in the retrieved evidence.

============================================================
WHEN EVIDENCE IS INSUFFICIENT
============================================================

If the search results do not clearly establish something,
write:

Requires confirmation.

Do NOT fill information gaps with assumptions.

Do NOT rely on your model knowledge for regulatory facts.

============================================================
CONFLICTING INFORMATION
============================================================

If retrieved sources disagree:

DO NOT silently choose one.

Instead say:

Conflicting information detected.

Then explain:

- Source A says X
- Source B says Y
- Production team should confirm with the appropriate
  authority.

============================================================
CITATION REQUIREMENT
============================================================

Use inline citations with source IDs.

Example:

Film London states that road closure enquiries should begin
through the relevant Borough Film Service [S1].

Another example:

The applicable road authority depends on whether the road
is managed by the borough or Transport for London [S2].

Every important regulatory or operational finding should
have at least one source ID.

============================================================
FINAL RESPONSE FORMAT
============================================================

Always structure the final answer exactly like this:

SCENE REQUIREMENTS

Summarize the proposed filming scene and detected production
requirements.

------------------------------------------------------------

VERIFIED FINDINGS

Only include findings supported by retrieved evidence.

Every finding must contain one or more citations such as:

[S1]
[S2]
[S3]

------------------------------------------------------------

UNVERIFIED / REQUIRES CONFIRMATION

List any important question that could not be reliably
confirmed from the retrieved evidence.

Do not guess.

------------------------------------------------------------

KEY RISKS

Explain the major production risks.

Connect each risk back to evidence where appropriate.

------------------------------------------------------------

ACTIONS BEFORE GREENLIGHT

Give a prioritized checklist for the production team.

Clearly distinguish:

- confirmed required actions
- recommended actions
- items needing human confirmation

------------------------------------------------------------

SOURCES

List the sources actually used.

Format:

[S1] Source title
URL

[S2] Source title
URL

Do not list sources that were not relevant to the final
analysis.

============================================================
SAFETY / HUMAN OVERSIGHT
============================================================

You assist production professionals.

You do not give final legal approval.

Never say that a production is legally cleared.

Instead use language such as:

"Based on the retrieved evidence..."

"Production should confirm..."

"Final authorization should be obtained from the relevant
authority."

The final greenlight decision belongs to the production
team and appropriate authorities.

""",

    tools=[
        analyze_scene_requirements,
        research_filming_requirements,
    ],
)


# ============================================================
# LOCAL AGENT ENGINE APP
# ============================================================

app = agent_engines.AdkApp(
    agent=agent
)


# ============================================================
# TEST SCENARIO
# ============================================================

async def main():

    message = """

We want to shoot an exterior night scene in central London.

The proposed scene includes:

- a drone establishing shot
- temporary road closure
- simulated police vehicle
- 25 background actors

The production manager wants to understand what permits,
restrictions, operational risks, and approvals need to be
investigated before approving the scene.

Research the current requirements and produce an
evidence-backed pre-production assessment.

"""

    print("\n")
    print("=" * 70)
    print("GREENLIGHT SCOUT")
    print("AGENTIC PRE-PRODUCTION INTELLIGENCE TEST")
    print("=" * 70)
    print()

    async for event in app.async_stream_query(
        user_id="greenlight_parallel_test",
        message=message,
    ):

        content = event.get("content")

        if not content:
            continue

        parts = content.get("parts", [])

        for part in parts:

            # ------------------------------------------------
            # Print tool decisions made by Gemini
            # ------------------------------------------------

            if "function_call" in part:

                function_call = part["function_call"]

                print("\n" + "=" * 70)

                print(
                    "AGENT REQUESTED TOOL:",
                    function_call["name"]
                )

                print("=" * 70 + "\n")

            # ------------------------------------------------
            # Print final natural-language response
            # ------------------------------------------------

            if "text" in part:

                text = part["text"]

                print("\n")
                print("=" * 70)
                print("GREENLIGHT SCOUT REPORT")
                print("=" * 70)
                print()

                print(text)

                print()
                print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())