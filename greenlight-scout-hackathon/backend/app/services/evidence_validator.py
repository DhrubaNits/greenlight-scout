from app.services.source_classifier import (
    is_official_authority,
)


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

        for excerpt in source["excerpts"]:

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

        for source_id in source_ids:

            if source_id not in source_map:

                errors.append(
                    f"Unknown source: {source_id}"
                )

        for excerpt_id in excerpt_ids:

            if excerpt_id not in excerpt_map:

                errors.append(
                    f"Unknown excerpt: {excerpt_id}"
                )

        for excerpt_id in excerpt_ids:

            excerpt = excerpt_map.get(
                excerpt_id
            )

            if not excerpt:
                continue

            parent_source = excerpt[
                "source_id"
            ]

            if parent_source not in source_ids:

                errors.append(
                    (
                        f"{excerpt_id} belongs to "
                        f"{parent_source}, but that "
                        "source was not cited."
                    )
                )

        # Never upgrade weak evidence.
        if (
            requested_status
            == "REQUIRES_CONFIRMATION"
        ):

            claim["status"] = (
                "REQUIRES_CONFIRMATION"
            )

            claim[
                "confirmation_reason"
            ] = claim.get(
                "reason",
                "Requires confirmation."
            )

            if errors:

                claim[
                    "validation_errors"
                ] = errors

            requires_confirmation.append(
                claim
            )

            continue

        if not source_ids:

            errors.append(
                "No cited source."
            )

        if not excerpt_ids:

            errors.append(
                "No cited excerpt."
            )

        official_source_found = False

        for source_id in source_ids:

            source = source_map.get(
                source_id
            )

            if not source:
                continue

            if is_official_authority(
                source[
                    "authority_level"
                ]
            ):

                official_source_found = True

                break

        if not official_source_found:

            errors.append(
                "No official source cited."
            )

        if errors:

            claim["status"] = (
                "REQUIRES_CONFIRMATION"
            )

            claim[
                "validation_errors"
            ] = errors

            requires_confirmation.append(
                claim
            )

        else:

            claim["status"] = (
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

        for excerpt in source["excerpts"]:

            excerpt_map[
                excerpt["excerpt_id"]
            ] = {

                "source_id":
                    source["source_id"],

                "text":
                    excerpt["text"]
            }

    payload = []

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

            if not is_official_authority(
                source[
                    "authority_level"
                ]
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

        payload.append(
            {

                "claim_id":
                    claim["claim_id"],

                "category":
                    claim.get(
                        "category",
                        "GENERAL"
                    ),

                "statement":
                    claim["statement"],

                "official_evidence":
                    official_evidence
            }
        )

    return {

        "candidate_claims":
            payload
    }


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

        for excerpt in source["excerpts"]:

            excerpt_map[
                excerpt["excerpt_id"]
            ] = {

                "source_id":
                    source["source_id"],

                "text":
                    excerpt["text"]
            }

    decision_map = {

        decision.get("claim_id"):
            decision

        for decision in entailment_output.get(
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
                "No semantic decision returned."
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

            supporting_sources = decision.get(
                "supporting_source_ids",
                []
            )

            supporting_excerpts = decision.get(
                "supporting_excerpt_ids",
                []
            )

            if not supported:

                errors.append(
                    "Direct support was not confirmed."
                )

            if support_level != "DIRECT":

                errors.append(
                    (
                        f"Support level is "
                        f"{support_level}, not DIRECT."
                    )
                )

            if not supporting_sources:

                errors.append(
                    "No supporting official source."
                )

            if not supporting_excerpts:

                errors.append(
                    "No supporting official excerpt."
                )

            for source_id in supporting_sources:

                source = source_map.get(
                    source_id
                )

                if not source:

                    errors.append(
                        f"Unknown source: {source_id}"
                    )

                    continue

                if not is_official_authority(
                    source[
                        "authority_level"
                    ]
                ):

                    errors.append(
                        (
                            f"{source_id} is not "
                            "an official source."
                        )
                    )

                if source_id not in claim.get(
                    "source_ids",
                    []
                ):

                    errors.append(
                        (
                            f"{source_id} was not "
                            "originally cited."
                        )
                    )

            for excerpt_id in supporting_excerpts:

                excerpt = excerpt_map.get(
                    excerpt_id
                )

                if not excerpt:

                    errors.append(
                        (
                            f"Unknown excerpt: "
                            f"{excerpt_id}"
                        )
                    )

                    continue

                if excerpt_id not in claim.get(
                    "excerpt_ids",
                    []
                ):

                    errors.append(
                        (
                            f"{excerpt_id} was not "
                            "originally cited."
                        )
                    )

        if errors:

            claim[
                "status"
            ] = "REQUIRES_CONFIRMATION"

            claim[
                "semantic_validation_errors"
            ] = errors

            if decision:

                claim[
                    "semantic_reason"
                ] = decision.get(
                    "reason"
                )

                claim[
                    "support_level"
                ] = decision.get(
                    "support_level"
                )

            requires_confirmation.append(
                claim
            )

        else:

            claim[
                "status"
            ] = "VERIFIED"

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

            claim[
                "support_level"
            ] = "DIRECT"

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