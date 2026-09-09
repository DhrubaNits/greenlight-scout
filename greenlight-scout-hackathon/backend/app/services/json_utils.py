import re


def clean_json_response(
    text: str
) -> str:

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