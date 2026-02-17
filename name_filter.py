"""
Name filtering utility for privacy protection.
Redacts names from chat messages before showing to admins.
"""

import os
import re
import csv
import logging

logger = logging.getLogger(__name__)

# Cache for loaded names
_names_cache = None

# Minimum name length to consider for filtering
MIN_NAME_LENGTH = 3


def load_names(csv_path: str = None) -> set:
    """
    Load names from the study participants CSV file into a set for fast lookup.
    Splits full names (e.g. "Himanshu Arora") into individual words.
    Names are stored lowercase for case-insensitive matching.
    """
    global _names_cache

    if _names_cache is not None:
        return _names_cache

    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), 'real_study', 'MindMitra_Students.csv')

    names = set()

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                full_name = row.get('name', '').strip()
                for part in full_name.split():
                    part = part.strip().lower()
                    if part and len(part) >= MIN_NAME_LENGTH:
                        names.add(part)

        logger.info(f"Loaded {len(names)} names for filtering")
        _names_cache = names
        return names

    except FileNotFoundError:
        logger.warning(f"Names CSV not found at {csv_path}")
        _names_cache = set()
        return _names_cache
    except Exception as e:
        logger.error(f"Error loading names CSV: {e}")
        _names_cache = set()
        return _names_cache


def redact_phone_numbers(text: str, replacement: str = "[PHONE]") -> str:
    """
    Redact 10-digit phone numbers from text.
    Handles formats like: 1234567890, 123-456-7890, 123 456 7890, +91 1234567890
    """
    if not text:
        return text

    # Pattern for 10 digit numbers (with optional separators and country code)
    # Matches: 1234567890, 123-456-7890, 123 456 7890, +91 1234567890, etc.
    patterns = [
        r'\+?\d{1,3}[-.\s]?\d{10}\b',  # With country code
        r'\b\d{10}\b',  # Plain 10 digits
        r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',  # XXX-XXX-XXXX format
        r'\b\d{5}[-.\s]\d{5}\b',  # XXXXX-XXXXX format
    ]

    for pattern in patterns:
        text = re.sub(pattern, replacement, text)

    return text


def redact_names(text: str, replacement: str = "[NAME]") -> str:
    """
    Redact any names found in the text.

    Args:
        text: The text to filter
        replacement: What to replace names with (default: [NAME])

    Returns:
        Text with names redacted
    """
    if not text:
        return text

    names = load_names()
    if not names:
        return text

    # Split text into words while preserving punctuation
    # This regex splits on word boundaries but keeps the structure
    words = re.findall(r'\b\w+\b|\W+', text)

    result = []
    for word in words:
        # Check if this is a word (not punctuation/whitespace)
        if re.match(r'^\w+$', word):
            # Check if lowercase version is in our names set
            if word.lower() in names:
                result.append(replacement)
            else:
                result.append(word)
        else:
            result.append(word)

    return ''.join(result)


def redact_all(text: str) -> str:
    """
    Redact both names and phone numbers from text.
    """
    text = redact_phone_numbers(text)
    text = redact_names(text)
    return text


def redact_names_in_messages(messages: list) -> list:
    """
    Redact names and phone numbers in a list of message dictionaries.

    Args:
        messages: List of message dicts with 'content' field

    Returns:
        List of messages with names and phone numbers redacted
    """
    redacted = []
    for msg in messages:
        msg_copy = dict(msg)  # Don't modify original
        if 'content' in msg_copy:
            msg_copy['content'] = redact_all(msg_copy['content'])
        if 'message' in msg_copy:  # For flagged chats
            msg_copy['message'] = redact_all(msg_copy['message'])
        redacted.append(msg_copy)
    return redacted


def redact_names_in_users(users: list) -> list:
    """
    Redact names in user list (in case access codes contain names).
    Generally access codes shouldn't contain names, but just in case.
    """
    # For now, just return as-is since access codes are typically codes not names
    return users


# Preload names on module import
try:
    load_names()
except Exception:
    pass  # Will try again on first use
