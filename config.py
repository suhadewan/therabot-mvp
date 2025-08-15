import os

import streamlit as st


class Config:
    """Centralized configuration for the Mental Health Support Bot"""

    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(
        os.getenv(
            "THERABOT_RATE_LIMIT_REQUESTS",
            st.secrets.get("rate_limit", {}).get("requests_per_hour", 20),
        )
    )
    RATE_LIMIT_WINDOW_HOURS = int(
        os.getenv(
            "THERABOT_RATE_LIMIT_WINDOW_HOURS",
            st.secrets.get("rate_limit", {}).get("window_hours", 1),
        )
    )

    # AI Model Configuration
    MODEL_NAME = os.getenv(
        "THERABOT_MODEL_NAME", st.secrets.get("model", {}).get("name", "gpt-4o-mini")
    )
    MODEL_TEMPERATURE = float(
        os.getenv(
            "THERABOT_MODEL_TEMPERATURE",
            st.secrets.get("model", {}).get("temperature", 0.7),
        )
    )
    MODEL_MAX_TOKENS = int(
        os.getenv(
            "THERABOT_MODEL_MAX_TOKENS",
            st.secrets.get("model", {}).get("max_tokens", 100),
        )
    )
    MODEL_STREAM = (
        os.getenv(
            "THERABOT_MODEL_STREAM",
            str(st.secrets.get("model", {}).get("stream", True)),
        ).lower()
        == "true"
    )

    # Response Guardrails
    GUARDRAILS_MAX_WORDS = int(
        os.getenv(
            "THERABOT_GUARDRAILS_MAX_WORDS",
            st.secrets.get("guardrails", {}).get("max_words", 50),
        )
    )
    GUARDRAILS_MAX_SENTENCES = int(
        os.getenv(
            "THERABOT_GUARDRAILS_MAX_SENTENCES",
            st.secrets.get("guardrails", {}).get("max_sentences", 3),
        )
    )
    GUARDRAILS_REQUIRE_QUESTION = (
        os.getenv(
            "THERABOT_GUARDRAILS_REQUIRE_QUESTION",
            str(st.secrets.get("guardrails", {}).get("require_question", True)),
        ).lower()
        == "true"
    )
    GUARDRAILS_MAX_RETRIES = int(
        os.getenv(
            "THERABOT_GUARDRAILS_MAX_RETRIES",
            st.secrets.get("guardrails", {}).get("max_retries", 3),
        )
    )
    GUARDRAILS_RETRY_TEMPERATURE = float(
        os.getenv(
            "THERABOT_GUARDRAILS_RETRY_TEMPERATURE",
            st.secrets.get("guardrails", {}).get("retry_temperature", 0.5),
        )
    )
    GUARDRAILS_TEMPERATURE_DECREMENT = float(
        os.getenv(
            "THERABOT_GUARDRAILS_TEMPERATURE_DECREMENT",
            st.secrets.get("guardrails", {}).get("temperature_decrement", 0.2),
        )
    )

    # UI Configuration
    PAGE_TITLE = os.getenv(
        "THERABOT_PAGE_TITLE",
        st.secrets.get("ui", {}).get("page_title", "Mental Health Support Bot"),
    )
    PAGE_ICON = os.getenv(
        "THERABOT_PAGE_ICON", st.secrets.get("ui", {}).get("page_icon", "🧠")
    )
    PAGE_LAYOUT = os.getenv(
        "THERABOT_PAGE_LAYOUT", st.secrets.get("ui", {}).get("page_layout", "centered")
    )
    APP_TITLE = os.getenv(
        "THERABOT_APP_TITLE",
        st.secrets.get("ui", {}).get("app_title", "Mental Health Support Bot 🧠"),
    )
    APP_CAPTION = os.getenv(
        "THERABOT_APP_CAPTION",
        st.secrets.get("ui", {}).get(
            "app_caption", "A supportive companion for youth mental wellness"
        ),
    )
    CHAT_PLACEHOLDER = os.getenv(
        "THERABOT_CHAT_PLACEHOLDER",
        st.secrets.get("ui", {}).get("chat_placeholder", "How are you feeling today?"),
    )

    # File Paths
    SYSTEM_PROMPT_FILE = os.getenv(
        "THERABOT_SYSTEM_PROMPT_FILE",
        st.secrets.get("files", {}).get("system_prompt", "system_prompt.txt"),
    )

    # Moderation
    MODERATION_HIGH_RISK_CATEGORIES = os.getenv(
        "THERABOT_MODERATION_HIGH_RISK_CATEGORIES",
        st.secrets.get("moderation", {}).get(
            "high_risk_categories", "self-harm,self-harm/intent,self-harm/instructions"
        ),
    ).split(",")

    # Error Messages
    ERROR_RATE_LIMIT = os.getenv(
        "THERABOT_ERROR_RATE_LIMIT",
        st.secrets.get("errors", {}).get(
            "rate_limit",
            f"You've reached the hourly message limit "
            f"({RATE_LIMIT_REQUESTS}). Please try again later.",
        ),
    )
    ERROR_MODERATION = os.getenv(
        "THERABOT_ERROR_MODERATION",
        st.secrets.get("errors", {}).get(
            "moderation",
            "I noticed your message might contain sensitive content. "
            "Let's focus on constructive support.",
        ),
    )
    ERROR_API_KEY = os.getenv(
        "THERABOT_ERROR_API_KEY",
        st.secrets.get("errors", {}).get(
            "api_key",
            "⚠️ OpenAI API key not found. Please add it to Streamlit Cloud secrets.",
        ),
    )
    ERROR_GENERIC = os.getenv(
        "THERABOT_ERROR_GENERIC",
        st.secrets.get("errors", {}).get("generic", "An error occurred: {error}"),
    )

    # Safety Banner
    SAFETY_BANNER_HTML = os.getenv(
        "THERABOT_SAFETY_BANNER",
        st.secrets.get("ui", {}).get(
            "safety_banner",
            """<div style='background-color: #fef3c7; border: 2px solid #f59e0b; padding: 1rem;
border-radius: 0.5rem; margin-bottom: 1rem; color: #92400e; font-weight: 500;'>
⚠️ <strong style='color: #78350f;'>Important Notice</strong>: This is a non-clinical support tool for
general mental wellness. If you're experiencing a crisis, please contact
emergency services (911) or a crisis hotline immediately.
</div>""",
        ),
    )

    # Crisis Hotlines Banner
    CRISIS_HOTLINES_HTML = os.getenv(
        "THERABOT_CRISIS_HOTLINES",
        st.secrets.get("ui", {}).get(
            "crisis_hotlines",
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
</div>""",
        ),
    )


# Create a single instance
config = Config()
