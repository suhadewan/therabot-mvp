import os


class Config:
    """Centralized configuration for the Mental Health Support Bot"""

    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(
        os.getenv("THERABOT_RATE_LIMIT_REQUESTS", 20)
    )
    RATE_LIMIT_WINDOW_HOURS = int(
        os.getenv("THERABOT_RATE_LIMIT_WINDOW_HOURS", 1)
    )

    # AI Model Configuration
    MODEL_NAME = os.getenv("THERABOT_MODEL_NAME", "gpt-4o-mini")
    # MODEL_NAME = os.getenv("THERABOT_MODEL_NAME", "ft:gpt-4o-mini-2024-07-18:personal:mindmitra2:CUWHRT6Y")
                        #    "ft:gpt-4o-mini-2024-07-18:personal:mindmitra:CG4e85Er")
    MODEL_TEMPERATURE = float(
        os.getenv("THERABOT_MODEL_TEMPERATURE", 0.7)
    )
    MODEL_MAX_TOKENS = int(
        os.getenv("THERABOT_MODEL_MAX_TOKENS", 100)
    )
    MODEL_STREAM = (
        os.getenv("THERABOT_MODEL_STREAM", "true").lower() == "true"
    )

    # Response Guardrails
    GUARDRAILS_MAX_WORDS = int(
        os.getenv("THERABOT_GUARDRAILS_MAX_WORDS", 100)  # Relaxed from 50 to 100
    )
    GUARDRAILS_MAX_SENTENCES = int(
        os.getenv("THERABOT_GUARDRAILS_MAX_SENTENCES", 6)  # Relaxed from 3 to 6
    )
    GUARDRAILS_REQUIRE_QUESTION = (
        os.getenv("THERABOT_GUARDRAILS_REQUIRE_QUESTION", "false").lower() == "true"  # Made optional
    )
    GUARDRAILS_MAX_RETRIES = int(
        os.getenv("THERABOT_GUARDRAILS_MAX_RETRIES", 3)
    )
    GUARDRAILS_RETRY_TEMPERATURE = float(
        os.getenv("THERABOT_GUARDRAILS_RETRY_TEMPERATURE", 0.5)
    )
    GUARDRAILS_TEMPERATURE_DECREMENT = float(
        os.getenv("THERABOT_GUARDRAILS_TEMPERATURE_DECREMENT", 0.2)
    )

    # Testing Configuration
    TEST_MODE = (
        os.getenv("THERABOT_TEST_MODE", "false").lower() == "true"
    )
    TEST_RESPONSE_DELAY = float(
        os.getenv("THERABOT_TEST_RESPONSE_DELAY", 0.5)  # Simulate API latency in seconds
    )

    # UI Configuration
    PAGE_TITLE = os.getenv(
        "THERABOT_PAGE_TITLE", "Mental Health Support Bot"
    )
    PAGE_ICON = os.getenv("THERABOT_PAGE_ICON", "🧠")
    PAGE_LAYOUT = os.getenv("THERABOT_PAGE_LAYOUT", "centered")
    APP_TITLE = os.getenv(
        "THERABOT_APP_TITLE", "Mental Health Support Bot 🧠"
    )
    APP_CAPTION = os.getenv(
        "THERABOT_APP_CAPTION",
        "A supportive companion for youth mental wellness"
    )
    CHAT_PLACEHOLDER = os.getenv(
        "THERABOT_CHAT_PLACEHOLDER",
        "How are you feeling today?"
    )

    # File Paths
    SYSTEM_PROMPT_FILE = os.getenv(
        "THERABOT_SYSTEM_PROMPT_FILE",
        "system_prompt.txt"
    )

    # Moderation
    MODERATION_HIGH_RISK_CATEGORIES = os.getenv(
        "THERABOT_MODERATION_HIGH_RISK_CATEGORIES",
        "self-harm,self-harm/intent,self-harm/instructions"
    ).split(",")

    # Error Messages
    ERROR_RATE_LIMIT = os.getenv(
        "THERABOT_ERROR_RATE_LIMIT",
        f"You've reached the hourly message limit "
        f"({RATE_LIMIT_REQUESTS}). Please try again later."
    )
    ERROR_MODERATION = os.getenv(
        "THERABOT_ERROR_MODERATION",
        "I noticed your message might contain sensitive content. "
        "Let's focus on constructive support."
    )
    ERROR_API_KEY = os.getenv(
        "THERABOT_ERROR_API_KEY",
        "⚠️ OpenAI API key not found. Please add it to environment variables."
    )
    ERROR_GENERIC = os.getenv(
        "THERABOT_ERROR_GENERIC",
        "An error occurred: {error}"
    )

    # Safety Banner
    SAFETY_BANNER_HTML = os.getenv(
        "THERABOT_SAFETY_BANNER",
        """<div style='background-color: #fef3c7; border: 2px solid #f59e0b; padding: 1rem;
border-radius: 0.5rem; margin-bottom: 1rem; color: #92400e; font-weight: 500;'>
⚠️ <strong style='color: #78350f;'>Important Notice</strong>: This is a non-clinical support tool for
general mental wellness. If you're experiencing a crisis, please contact
emergency services (911) or a crisis hotline immediately.
</div>"""
    )

    # Crisis Hotlines Banner
    CRISIS_HOTLINES_HTML = os.getenv(
        "THERABOT_CRISIS_HOTLINES",
        """<div style='background-color: #dbeafe; border: 2px solid #2563eb; padding: 1rem;
border-radius: 0.5rem; margin-bottom: 1rem; color: #1e40af; font-weight: 500;'>
📞 <strong style='color: #1e3a8a;'>24/7 Mental Health Helplines (India)</strong><br><br>
<strong>Mobile Mental Health Unit (MMHU) - Delhi:</strong><br>
• Landline: 011-22592818<br>
• Mobile: 9868396910 / 9868396911<br><br>
<strong>Kiran - National Mental Health Helpline:</strong><br>
• Toll-free: 1800-599-0019<br><br>
<strong>Tele Manas - Ministry of Health:</strong><br>
• Toll-free: 1800-891-4416
</div>"""
    )


# Create a single instance
config = Config()
