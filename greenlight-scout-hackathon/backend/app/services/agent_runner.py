async def run_agent(
    app,
    user_id: str,
    message: str
) -> dict:

    final_text = ""

    tool_responses = {}

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

            if "text" in part:

                final_text = (
                    part["text"]
                )

            if "function_response" in part:

                response = (
                    part["function_response"]
                )

                name = response.get(
                    "name"
                )

                value = response.get(
                    "response"
                )

                if name:

                    tool_responses.setdefault(
                        name,
                        []
                    ).append(
                        value
                    )

    return {

        "text":
            final_text,

        "tool_responses":
            tool_responses
    }