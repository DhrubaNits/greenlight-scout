from urllib.parse import urlparse


def classify_source_authority(
    url: str
) -> str:

    try:

        hostname = (
            urlparse(str(url)).hostname
            or ""
        ).lower()

    except Exception:

        hostname = ""

    if hostname.endswith(
        "tfl.gov.uk"
    ):
        return "OFFICIAL_TRANSPORT"

    if hostname.endswith(
        ".police.uk"
    ):
        return "OFFICIAL_POLICE"

    if hostname.endswith(
        "filmlondon.org.uk"
    ):
        return "OFFICIAL_FILM_COMMISSION"

    if hostname.endswith(
        "caa.co.uk"
    ):
        return "OFFICIAL_REGULATOR"

    if hostname.endswith(
        "nats.aero"
    ):
        return "OFFICIAL_AVIATION"

    if hostname.endswith(
        ".gov.uk"
    ):
        return "OFFICIAL_GOVERNMENT"

    return "SECONDARY"


def is_official_authority(
    authority_level: str
) -> bool:

    return authority_level.startswith(
        "OFFICIAL_"
    )