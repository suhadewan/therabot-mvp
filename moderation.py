from typing import Any, Dict, Tuple, Optional

from config import config


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
        high_risk_categories = config.MODERATION_HIGH_RISK_CATEGORIES

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


def categorize_flagged_content(text: str, client: Any) -> Optional[str]:
    """
    Use GPT to categorize flagged content into crisis types.
    Returns one of: SI, SH, HI, EA, or None if not a crisis

    Categories:
    - SI: Suicidal Ideation / Suicide Intent
    - SH: Self-Harm (non-suicidal)
    - HI: Harm to Others / Violence
    - EA: Emotional Abuse / Trauma disclosure
    """
    try:
        categorization_prompt = """You are a mental health crisis categorization system. Analyze the following message and determine if it contains concerning content.

Categorize the message into ONE of these categories:
- SI: Suicidal ideation, intent, or planning (e.g., "I want to die", "kms", "going to kill myself")
- SH: Self-harm intent or planning (e.g., "I want to cut myself", "going to hurt myself")
- HI: Intent to harm others or violence (e.g., "I want to hurt someone", "going to fight them")
- EA: Emotional abuse disclosure or trauma (e.g., "my parents hit me", "someone touched me")
- NONE: Not a crisis, just inappropriate content

Message: "{message}"

Respond with ONLY the category code (SI, SH, HI, EA, or NONE). No explanation."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap for classification
            messages=[
                {"role": "system", "content": "You are a crisis categorization system. Respond with only the category code."},
                {"role": "user", "content": categorization_prompt.format(message=text)}
            ],
            temperature=0.0,  # Deterministic
            max_tokens=10
        )

        category = response.choices[0].message.content.strip().upper()

        # Validate response
        if category in ["SI", "SH", "HI", "EA"]:
            return category
        else:
            return None  # Not a crisis, just general moderation flag

    except Exception as e:
        print(f"Categorization error: {e}")
        return None  # Fallback to general moderation
