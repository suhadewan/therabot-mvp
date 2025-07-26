import re
from typing import Any, Dict, List, Tuple


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
    if word_count > 50:
        violations.append(f"Response has {word_count} words (max 50)")

    sentence_count = count_sentences(response)
    if sentence_count > 3:
        violations.append(f"Response has {sentence_count} sentences (max 3)")

    if not ends_with_question(response):
        violations.append("Response must end with a follow-up question")

    return len(violations) == 0, violations


def regenerate_if_needed(
    response: str, messages: List[Dict[str, Any]], client: Any, max_attempts: int = 3
) -> str:
    """
    Regenerate response if it violates guardrails.
    Uses progressively lower temperature on retries.
    """
    is_valid, violations = validate_response(response)

    if is_valid:
        return response

    attempt = 1
    temperature = 0.5

    while attempt <= max_attempts:
        try:
            messages_with_feedback = messages + [
                {
                    "role": "system",
                    "content": (
                        f"Previous response violated these rules: "
                        f"{', '.join(violations)}. Generate a new response "
                        f"that is under 50 words, has max 3 sentences, "
                        f"and ends with a follow-up question."
                    ),
                }
            ]

            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_with_feedback,
                temperature=temperature,
                max_tokens=100,
            )

            new_response = completion.choices[0].message.content
            is_valid, violations = validate_response(new_response)

            if is_valid:
                return new_response

            temperature -= 0.2
            attempt += 1

        except Exception as e:
            print(f"Regeneration attempt {attempt} failed: {e}")
            attempt += 1

    return response + " How does that make you feel?"
