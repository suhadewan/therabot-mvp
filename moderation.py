from typing import Any, Dict, Tuple


def moderate_content(text: str, client: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Use OpenAI's moderation API to check content safety.
    Returns (is_safe, moderation_result)
    """
    try:
        response = client.moderations.create(input=text)
        result = response.results[0]

        is_flagged = result.flagged

        categories = result.categories
        high_risk_categories = [
            "self-harm",
            "self-harm/intent",
            "self-harm/instructions",
        ]

        for category in high_risk_categories:
            if hasattr(categories, category.replace("/", "_")) and getattr(
                categories, category.replace("/", "_")
            ):
                is_flagged = True
                break

        return not is_flagged, result.model_dump()

    except Exception as e:
        print(f"Moderation error: {e}")
        return True, {}
