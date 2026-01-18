from typing import Any, Dict, Tuple, Optional, Union

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


def assess_mental_health_risk(text: str, client: Any) -> Tuple[bool, Optional[str], float]:
    """
    Dedicated mental health risk assessment using GPT.
    More sensitive than generic content moderation - specifically tuned for mental health.

    Returns: (is_risk_detected, risk_category, confidence_score)

    Categories:
    - SI: Suicidal Ideation / Suicide Intent
    - SH: Self-Harm (non-suicidal)
    - HI: Harm to Others / Violence
    - EA: Emotional Abuse / Trauma disclosure
    - None: No significant risk detected
    """
    try:
        assessment_prompt = """You are a mental health crisis detection system for a student mental health chatbot in India.

Analyze the following message for mental health risk. Look for:

**SUICIDE/SELF-HARM INDICATORS:**
- Direct expressions: "want to die", "kill myself", "end my life", "suicide"
- Indirect hopelessness: "no reason to keep going", "better if I wasn't here", "giving up on everything"
- Disappearing/escape wishes: "wish I could disappear", "want to vanish"
- Hinglish/Hindi expressions: "sab chhod du" (give up everything), "agar main na hota" (if I wasn't here), "gayab ho jaaun" (disappear)

**SELF-HARM (non-suicidal):**
- Cutting, burning, hurting self
- "want to hurt myself", "need to feel pain"

**HARM TO OTHERS:**
- Wanting to hurt/harm someone else
- Violent ideation

**EMOTIONAL ABUSE/TRAUMA:**
- "someone hit me", "being hurt", "touched inappropriately"
- Disclosure of abuse

**FALSE POSITIVES TO IGNORE:**
- Academic stress without hopelessness: "stressed about exams but I'll manage"
- Temporary tiredness: "tired from studying"
- General anxiety that will pass: "anxious before tests but it goes away"

Message: "{message}"

Respond in this EXACT format:
RISK: YES or NO
CATEGORY: SI, SH, HI, EA, or NONE
CONFIDENCE: 0.0 to 1.0
REASONING: One sentence explaining your decision

Be SENSITIVE but not overly cautious. Err on the side of flagging if there's genuine concern."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a mental health risk assessment system. Be thorough and sensitive."},
                {"role": "user", "content": assessment_prompt.format(message=text)}
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=100
        )

        result = response.choices[0].message.content.strip()

        # Parse the structured response
        lines = result.split('\n')
        risk_detected = False
        category = None
        confidence = 0.0

        for line in lines:
            if line.startswith('RISK:'):
                risk_detected = 'YES' in line.upper()
            elif line.startswith('CATEGORY:'):
                cat = line.split(':')[1].strip().upper()
                if cat in ['SI', 'SH', 'HI', 'EA']:
                    category = cat
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.split(':')[1].strip())
                except:
                    confidence = 0.5

        return risk_detected, category, confidence

    except Exception as e:
        print(f"Mental health risk assessment error: {e}")
        return False, None, 0.0


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
