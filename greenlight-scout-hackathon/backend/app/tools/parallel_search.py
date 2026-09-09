from parallel import Parallel

from app.config import PARALLEL_API_KEY
from app.services.source_classifier import (
    classify_source_authority,
)


parallel_client = Parallel(
    api_key=PARALLEL_API_KEY
)


def research_filming_requirements(
    location: str,
    research_objective: str
) -> dict:
    """
    Search the current open web using Parallel Search API.
    """

    search = parallel_client.search(

        objective=(
            f"{research_objective}. "
            f"The proposed professional filming "
            f"location is {location}. "
            "Find current evidence regarding professional "
            "filming permissions, drone restrictions, road "
            "closures, police coordination, public-location "
            "requirements, night filming requirements and "
            "operational restrictions. "
            "Prioritize official government, aviation, police, "
            "transport, local authority and official film "
            "commission sources."
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

    return {

        "location":
            location,

        "research_objective":
            research_objective,

        "sources":
            sources
    }