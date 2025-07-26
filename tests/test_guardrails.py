import pytest

from guardrails import (count_sentences, count_words, ends_with_question,
                        regenerate_if_needed, validate_response)


class TestGuardrailFunctions:
    def test_count_words(self):
        assert count_words("Hello world") == 2
        assert count_words("This is a test") == 4
        assert count_words("") == 0
        assert count_words("   ") == 0
        assert count_words("One") == 1

    def test_count_sentences(self):
        assert count_sentences("Hello world.") == 1
        assert count_sentences("First. Second. Third.") == 3
        assert count_sentences("Question? Answer! Statement.") == 3
        assert count_sentences("No punctuation") == 1
        assert count_sentences("") == 0
        assert count_sentences("Trailing...") == 1

    def test_ends_with_question(self):
        assert ends_with_question("How are you?") is True
        assert ends_with_question("How are you? ") is True
        assert ends_with_question("Statement.") is False
        assert ends_with_question("Exclamation!") is False
        assert ends_with_question("") is False
        assert ends_with_question("?") is True


class TestValidateResponse:
    def test_valid_response(self):
        response = (
            "I understand how you feel. That sounds challenging. What helps you cope?"
        )
        is_valid, violations = validate_response(response)
        assert is_valid is True
        assert violations == []

    def test_too_many_words(self):
        response = " ".join(["word"] * 51) + "?"
        is_valid, violations = validate_response(response)
        assert is_valid is False
        assert any("51 words" in v for v in violations)

    def test_too_many_sentences(self):
        response = "One. Two. Three. Four?"
        is_valid, violations = validate_response(response)
        assert is_valid is False
        assert any("4 sentences" in v for v in violations)

    def test_no_question(self):
        response = "I understand how you feel."
        is_valid, violations = validate_response(response)
        assert is_valid is False
        assert any("follow-up question" in v for v in violations)

    def test_multiple_violations(self):
        response = " ".join(["word"] * 51) + ". Sentence two. Three. Four. Five."
        is_valid, violations = validate_response(response)
        assert is_valid is False
        assert len(violations) == 3


class TestRegenerateIfNeeded:
    def test_valid_response_not_regenerated(self):
        response = "That sounds tough. How long have you felt this way?"
        result = regenerate_if_needed(response, [], None)
        assert result == response

    def test_invalid_response_fallback(self):
        response = "This is a very long response that exceeds the word limit."

        class MockClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        raise Exception("API Error")

        result = regenerate_if_needed(response, [], MockClient())
        assert result.endswith("How does that make you feel?")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
