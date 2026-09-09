import asyncio

from google.adk.agents import Agent
from vertexai import agent_engines


def analyze_scene_requirements(scene_description: str) -> dict:
    """Extracts a basic production checklist from a filming scene."""

    print("\n>>> TOOL CALLED: analyze_scene_requirements\n")

    scene_lower = scene_description.lower()

    return {
        "night_shoot": "night" in scene_lower,
        "drone_required": "drone" in scene_lower,
        "road_closure_required": "road closure" in scene_lower,
        "emergency_vehicle": (
            "police" in scene_lower
            or "ambulance" in scene_lower
            or "emergency vehicle" in scene_lower
        ),
        "next_action": "Research permits and operational restrictions",
    }


agent = Agent(
    model="gemini-2.5-flash",
    name="greenlight_scout",
    description="Pre-production intelligence agent for film crews.",
    instruction="""
You are Greenlight Scout, an AI assistant for film production teams.

Whenever the user provides a filming scene or filming requirements,
you MUST call the analyze_scene_requirements tool first.

After receiving the tool result:
1. Summarize the detected production requirements.
2. Explain what needs external research.
3. Do not invent permit rules or legal requirements.
""",
    tools=[analyze_scene_requirements],
)

app = agent_engines.AdkApp(agent=agent)


async def main():
    message = """
We want to shoot an exterior night scene in central London.
The scene requires a drone establishing shot, a temporary road closure,
a simulated police vehicle, and 25 background actors.
"""

    async for event in app.async_stream_query(
        user_id="hackathon_test_user",
        message=message,
    ):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())