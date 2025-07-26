import re
from typing import Any, Dict, List, Tuple

from config import config


def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())


def count_sentences(text: str) -> int:
    """Count sentences in text"""
    sentences = re.split(r"[.!?]+", text.strip())
    return len([s for s in sentences if s.strip()])


def ends_with_question(text: str) -> bool:
    """Check if text ends with a question"""
    text = text.strip()
    return bool(text) and text[-1] == "?"


def validate_response(response: str) -> Tuple[bool, List[str]]:
    """
    Validate response against guardrails.
    Returns (is_valid, list_of_violations)
    """
    violations = []

    word_count = count_words(response)
    if word_count > config.GUARDRAILS_MAX_WORDS:
        violations.append(
            f"Response has {word_count} words (max {config.GUARDRAILS_MAX_WORDS})"
        )

    sentence_count = count_sentences(response)
    if sentence_count > config.GUARDRAILS_MAX_SENTENCES:
        violations.append(
            f"Response has {sentence_count} sentences "
            f"(max {config.GUARDRAILS_MAX_SENTENCES})"
        )

    if config.GUARDRAILS_REQUIRE_QUESTION and not ends_with_question(response):
        violations.append("Response must end with a follow-up question")

    return len(violations) == 0, violations


def regenerate_if_needed(
    response: str, messages: List[Dict[str, Any]], client: Any, max_attempts: int = None
) -> str:
    """
    Regenerate response if it violates guardrails.
    Uses progressively lower temperature on retries.
    """
    is_valid, violations = validate_response(response)

    if is_valid:
        return response

    if max_attempts is None:
        max_attempts = config.GUARDRAILS_MAX_RETRIES

    attempt = 1
    temperature = config.GUARDRAILS_RETRY_TEMPERATURE

    while attempt <= max_attempts:
        try:
            messages_with_feedback = messages + [
                {
                    "role": "system",
                    "content": (
                        f"Previous response violated these rules: "
                        f"{', '.join(violations)}. Generate a new response "
                        f"that is under {config.GUARDRAILS_MAX_WORDS} words, "
                        f"has max {config.GUARDRAILS_MAX_SENTENCES} sentences"
                        + (
                            ", and ends with a follow-up question."
                            if config.GUARDRAILS_REQUIRE_QUESTION
                            else "."
                        )
                    ),
                }
            ]

            completion = client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=messages_with_feedback,
                temperature=temperature,
                max_tokens=config.MODEL_MAX_TOKENS,
            )

            new_response = completion.choices[0].message.content
            is_valid, violations = validate_response(new_response)

            if is_valid:
                return new_response

            temperature -= config.GUARDRAILS_TEMPERATURE_DECREMENT
            attempt += 1

        except Exception as e:
            print(f"Regeneration attempt {attempt} failed: {e}")
            attempt += 1

    return response + " How does that make you feel?"
