import json
import uuid

from app.services.persistence import (
    save_analysis_record,
)

from app.agents.entailment_agent import (
    entailment_app,
)

from app.agents.research_agent import (
    research_app,
)

from app.agents.verification_agent import (
    verification_app,
)

from app.models.api import (
    AnalyzeRequest,
)

from app.services.agent_runner import (
    run_agent,
)

from app.services.evidence_validator import (
    apply_semantic_gate,
    build_entailment_payload,
    structural_validate_claims,
)

from app.services.json_utils import (
    clean_json_response,
)

from app.tools.scene_analysis import (
    analyze_scene_requirements,
)


# ============================================================
# GREENLIGHT SCOUT MAIN ANALYSIS PIPELINE
# ============================================================

async def analyze_scene(
    request: AnalyzeRequest
) -> dict:
    """
    Execute the complete Greenlight Scout workflow.

    Pipeline:

    1. Deterministic scene analysis
    2. ADK Research Agent
    3. Parallel Search
    4. Claim Verification Agent
    5. Deterministic structural validation
    6. Semantic evidence verification
    7. Final deterministic evidence gate
    8. Persist completed analysis
    9. Structured API response
    """

    # ========================================================
    # REQUEST ID
    # ========================================================

    request_id = str(
        uuid.uuid4()
    )

    # ========================================================
    # BUILD COMPLETE SCENE INPUT
    # ========================================================

    requirements_text = ""

    if request.requirements:

        requirements_text = "\n".join(
            f"- {requirement}"
            for requirement
            in request.requirements
        )

    full_scene = (
        f"{request.scene_description.strip()}\n\n"
        f"Location: {request.location.strip()}"
    )

    if requirements_text:

        full_scene += (
            "\n\nProduction Requirements:\n"
            f"{requirements_text}"
        )

    # ========================================================
    # STAGE 0
    # DETERMINISTIC SCENE ANALYSIS
    # ========================================================

    # The complete API input is analyzed directly.
    #
    # Gemini does not decide what text gets passed
    # into this deterministic step.

    scene_analysis = (
        analyze_scene_requirements(
            full_scene
        )
    )

    # ========================================================
    # STAGE 1
    # RESEARCH AGENT + PARALLEL SEARCH
    # ========================================================

    research_prompt = f"""
PROPOSED FILMING SCENE

{full_scene}


DETERMINISTIC SCENE ANALYSIS

{json.dumps(
    scene_analysis,
    indent=2,
    ensure_ascii=False
)}


TASK

Perform ONE combined research operation covering all
relevant current filming requirements for this proposed
scene.

Research current evidence relating to:

- general filming permissions
- drone restrictions
- restricted airspace
- road closures
- transport authority requirements
- police coordination
- simulated police or emergency vehicles
- night filming
- crew and background actor considerations
- public-location requirements
- operational restrictions
- relevant safety requirements

Use the filming location supplied in the request.

Gather evidence only.

Do not make a final legal or regulatory clearance decision.
"""

    research_result = await run_agent(

        research_app,

        user_id=(
            f"research-{request_id}"
        ),

        message=research_prompt,
    )

    # ========================================================
    # EXTRACT PARALLEL TOOL RESPONSE
    # ========================================================

    tool_responses = (
        research_result.get(
            "tool_responses",
            {}
        )
    )

    research_responses = (
        tool_responses.get(
            "research_filming_requirements",
            []
        )
    )

    if not research_responses:

        raise RuntimeError(
            "Parallel Search tool was not executed "
            "by the Research Agent."
        )

    # We instruct the research agent to make one Parallel
    # request.
    #
    # If multiple responses are returned, use the final
    # completed response.

    evidence = (
        research_responses[-1]
    )

    if not isinstance(
        evidence,
        dict
    ):

        raise RuntimeError(
            "Parallel Search returned an invalid "
            "response structure."
        )

    if "sources" not in evidence:

        raise RuntimeError(
            "Parallel Search response does not "
            "contain a sources field."
        )

    if not isinstance(
        evidence["sources"],
        list
    ):

        raise RuntimeError(
            "Parallel Search sources field "
            "is not a list."
        )

    # ========================================================
    # STAGE 2
    # CLAIM VERIFICATION AGENT
    # ========================================================

    verifier_prompt = f"""
SCENE

{full_scene}


DETERMINISTIC SCENE ANALYSIS

{json.dumps(
    scene_analysis,
    indent=2,
    ensure_ascii=False
)}


PARALLEL SEARCH EVIDENCE

{json.dumps(
    evidence,
    indent=2,
    ensure_ascii=False
)}


TASK

Create structured factual claims using ONLY the supplied
Parallel Search evidence.

Do not use external knowledge.

Important rules:

- regulatory claims supported only by secondary sources
  must be marked REQUIRES_CONFIRMATION

- preserve qualifiers exactly

- if evidence says "may", do not convert it to "must"

- do not invent fees, timelines, permits, penalties,
  restrictions, insurance requirements or police requirements

- do not broaden geographic scope

- if evidence applies specifically to the City of London,
  do not generalize it to all of Central London or London

- add open questions for important scene requirements that
  could not be resolved by the retrieved evidence
"""

    verifier_result = await run_agent(

        verification_app,

        user_id=(
            f"verification-{request_id}"
        ),

        message=verifier_prompt,
    )

    verifier_text = (
        verifier_result.get(
            "text",
            ""
        )
    )

    if not verifier_text:

        raise RuntimeError(
            "Claim Verification Agent "
            "returned an empty response."
        )

    verifier_json = (
        clean_json_response(
            verifier_text
        )
    )

    try:

        verifier_output = (
            json.loads(
                verifier_json
            )
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Claim Verification Agent returned invalid JSON. "
            f"Raw output: {verifier_text}"
        ) from exc

    if not isinstance(
        verifier_output,
        dict
    ):

        raise RuntimeError(
            "Claim Verification Agent response "
            "must be a JSON object."
        )

    # ========================================================
    # STAGE 3
    # DETERMINISTIC STRUCTURAL VALIDATION
    # ========================================================

    structural_result = (
        structural_validate_claims(
            verifier_output,
            evidence
        )
    )

    candidate_verified = (
        structural_result.get(
            "candidate_verified",
            []
        )
    )

    # ========================================================
    # STAGE 4
    # BUILD OFFICIAL-EVIDENCE-ONLY PAYLOAD
    # ========================================================

    entailment_payload = (
        build_entailment_payload(
            candidate_verified,
            evidence
        )
    )

    # ========================================================
    # STAGE 5
    # SEMANTIC EVIDENCE AGENT
    # ========================================================

    # If no claims survived structural validation,
    # there is nothing for the semantic agent to evaluate.

    if candidate_verified:

        entailment_prompt = f"""
CANDIDATE CLAIMS FOR SEMANTIC VALIDATION

{json.dumps(
    entailment_payload,
    indent=2,
    ensure_ascii=False
)}


TASK

Evaluate whether the OFFICIAL evidence supplied with each
candidate claim directly supports the COMPLETE claim.

Use ONLY the evidence provided with each claim.

Do not use external knowledge.

Support levels:

DIRECT
- complete claim is directly supported

PARTIAL
- only part of the claim is supported

INSUFFICIENT
- supplied evidence does not establish the claim

supported must be true ONLY when support_level is DIRECT.

Do not strengthen qualifiers.

Do not infer unstated legal or regulatory requirements.

GEOGRAPHIC SCOPE RULE:

The geographic scope of the evidence must directly match
the geographic scope of the claim.

Evidence about:

- City of London
- Westminster
- Camden
- a specific borough
- a specific road
- a specific venue

must not automatically establish a claim about:

- Central London
- all of London
- the United Kingdom

If the claim is geographically broader than the supplied
official evidence, return PARTIAL.
"""

        entailment_result = await run_agent(

            entailment_app,

            user_id=(
                f"entailment-{request_id}"
            ),

            message=entailment_prompt,
        )

        entailment_text = (
            entailment_result.get(
                "text",
                ""
            )
        )

        if not entailment_text:

            raise RuntimeError(
                "Semantic Evidence Agent "
                "returned an empty response."
            )

        entailment_json = (
            clean_json_response(
                entailment_text
            )
        )

        try:

            entailment_output = (
                json.loads(
                    entailment_json
                )
            )

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Semantic Evidence Agent returned invalid JSON. "
                f"Raw output: {entailment_text}"
            ) from exc

        if not isinstance(
            entailment_output,
            dict
        ):

            raise RuntimeError(
                "Semantic Evidence Agent response "
                "must be a JSON object."
            )

    else:

        entailment_output = {
            "decisions": []
        }

    # ========================================================
    # STAGE 6
    # FINAL DETERMINISTIC SEMANTIC GATE
    # ========================================================

    final_result = (
        apply_semantic_gate(
            structural_result,
            entailment_output,
            evidence
        )
    )

    verified_findings = (
        final_result.get(
            "validated_claims",
            []
        )
    )

    requires_confirmation = (
        final_result.get(
            "requires_confirmation",
            []
        )
    )

    open_questions = (
        final_result.get(
            "open_questions",
            []
        )
    )

    # ========================================================
    # BUILD CLEAN SOURCE LIST
    # ========================================================

    used_source_ids = set()

    for claim in (
        verified_findings
        + requires_confirmation
    ):

        for source_id in claim.get(
            "source_ids",
            []
        ):

            used_source_ids.add(
                source_id
            )

    response_sources = []

    for source in evidence.get(
        "sources",
        []
    ):

        source_id = (
            source.get(
                "source_id"
            )
        )

        if (
            source_id
            not in used_source_ids
        ):
            continue

        response_sources.append(
            {
                "source_id":
                    source_id,

                "title":
                    source.get(
                        "title",
                        ""
                    ),

                "url":
                    source.get(
                        "url",
                        ""
                    ),

                "publish_date":
                    source.get(
                        "publish_date"
                    ),

                "authority_level":
                    source.get(
                        "authority_level",
                        "SECONDARY"
                    ),
            }
        )

    # ========================================================
    # METRICS
    # ========================================================

    sources_retrieved = len(
        evidence.get(
            "sources",
            []
        )
    )

    claims_proposed = len(
        verifier_output.get(
            "claims",
            []
        )
    )

    candidate_verified_count = (
        len(
            candidate_verified
        )
    )

    final_verified_count = (
        len(
            verified_findings
        )
    )

    requires_confirmation_count = (
        len(
            requires_confirmation
        )
    )

    # ========================================================
    # FINAL API RESPONSE
    # ========================================================

    response = {

        "status":
            "completed",

        "request_id":
            request_id,

        "location":
            request.location,

        "scene_analysis":
            scene_analysis,

        "verified_findings":
            verified_findings,

        "requires_confirmation":
            requires_confirmation,

        "open_questions":
            open_questions,

        "sources":
            response_sources,

        "metrics": {

            "sources_retrieved":
                sources_retrieved,

            "claims_proposed":
                claims_proposed,

            "candidate_verified":
                candidate_verified_count,

            "final_verified":
                final_verified_count,

            "requires_confirmation":
                requires_confirmation_count,
        },
    }

    # ========================================================
    # STAGE 7
    # PERSIST COMPLETED ANALYSIS
    #
    # Local:
    # SQLAlchemy -> SQLite
    #
    # Production later:
    # SQLAlchemy -> Cloud SQL PostgreSQL
    # ========================================================

    save_analysis_record(

        analysis_id=
            request_id,

        location=
            request.location,

        scene_description=
            request.scene_description,

        requirements=
            request.requirements,

        analysis_data=
            response,
    )

    # ========================================================
    # RETURN RESPONSE
    # ========================================================

    return response