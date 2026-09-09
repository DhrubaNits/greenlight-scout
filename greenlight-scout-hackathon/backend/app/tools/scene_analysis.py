def analyze_scene_requirements(
    scene_description: str
) -> dict:
    """
    Deterministically detect production elements
    that can trigger research requirements.
    """

    text = scene_description.lower()

    return {

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