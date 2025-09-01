import re
from typing import Tuple


def detect_crisis_keywords(user_input: str) -> Tuple[bool, str]:
    """
    Scan user input for crisis-related keywords.
    Returns (is_crisis_detected, override_response)
    """
    # Convert input to lowercase for case-insensitive matching
    input_lower = user_input.lower()
    
    # Check for suicide/crisis keywords
    if detect_suicide_keywords(input_lower):
        return True, get_crisis_response()
    
    # Check for abuse keywords
    if detect_abuse_keywords(input_lower):
        return True, get_abuse_response()
    
    return False, ""


def detect_suicide_keywords(input_lower: str) -> bool:
    """Detect suicide and self-harm related keywords"""
    # Crisis keywords in English and Hindi
    crisis_keywords = [
        "suicide", "kill myself", "want to die", "end my life", 
        "meri zindagi khatam", "marna chahta", "khudkushi", 
        "nahi jeena", "i don't want to live", "khatam karna", "mar jaaun",
        "want to end it all", "better off dead", "no reason to live",
        "can't take it anymore", "life is not worth living",
        "thinking of ending it", "planning to die", "ready to die",
        "tired of living", "hate my life", "life is meaningless",
        "death would be better", "want to disappear", "give up on life"
    ]
    
    # Check for exact keyword matches
    for keyword in crisis_keywords:
        if keyword.lower() in input_lower:
            return True
    
    # Check for partial matches and variations
    crisis_patterns = [
        r'\b(die|death|dead)\b',
        r'\b(kill|killing)\b',
        r'\b(suicide|suicidal)\b',
        r'\b(end.*life|life.*end)\b',
        r'\b(want.*die|die.*want)\b',
        r'\b(mar.*jaa|jaa.*mar)\b',  # Hindi variations
        r'\b(khatam.*karna|karna.*khatam)\b',  # Hindi variations
    ]
    
    for pattern in crisis_patterns:
        if re.search(pattern, input_lower):
            return True
    
    return False


def detect_abuse_keywords(input_lower: str) -> bool:
    """Detect abuse-related keywords"""
    
    # Physical abuse keywords
    physical_abuse_keywords = [
        "he hit me", "she hit me", "they beat me", "got slapped",
        "punched me", "hurt me physically", "physically hurt me", "kicked me", 
        "violence at home", "domestic violence", "he hurt me", "she hurt me",
        "they hurt me", "got hurt", "was hurt", "am hurt", "being hurt",
        "usne mujhe maara", "ghar pe maar pitaayi", "usne thappad maara", 
        "usne punch maara", "mujhe chot lagi", "ghar mein hinsa", 
        "domestic violence ho raha hai", "usne mujhe hurt kiya"
    ]
    
    # Sexual abuse keywords
    sexual_abuse_keywords = [
        "he raped me", "she touched me", "molested me", "abused me",
        "sexual abuse", "he forced me", "groped me", "inappropriate touching",
        "harassed me", "usne rape kiya", "usne chhua mujhe",
        "sexual abuse hua", "galat tarike se chhua", "harass kiya",
        "jabardasti ki", "usne molest kiya", "chhed chhaad hui"
    ]
    
    # Emotional/verbal abuse keywords
    emotional_abuse_keywords = [
        "called me names", "insulted me", "emotionally abusive",
        "mentally torturing", "he controls me", "gaslighting",
        "toxic relationship", "gali di", "bura bola",
        "mental torture ho raha hai", "woh mujhe control karta hai",
        "toxic relationship hai", "bar bar neecha dikhata hai",
        "mann se tod diya"
    ]
    
    # Safety/danger keywords
    safety_keywords = [
        "i feel unsafe", "i can't go home", "afraid of him", "afraid of her",
        "i'm in danger", "he's stalking me", "they won't let me leave",
        "main safe nahi hoon", "ghar nahi ja sakti", "uska darr lagta hai",
        "khatre mein hoon", "woh peecha karta hai", "woh mujhe jane nahi deta"
    ]
    
    # Check for exact matches
    all_abuse_keywords = (physical_abuse_keywords + sexual_abuse_keywords + 
                         emotional_abuse_keywords + safety_keywords)
    
    for keyword in all_abuse_keywords:
        if keyword.lower() in input_lower:
            return True
    
    # Check for pattern matches
    abuse_patterns = [
        r'\b(hit|hitting|slapped|punched|kicked|beat|beating)\b',
        # More specific hurt patterns - only when someone else is doing the hurting
        r'\b(he|she|they)\s+(hurt|hurting)\s+(me|him|her)\b',
        r'\b(someone|anyone)\s+(hurt|hurting)\s+(me|him|her)\b',
        r'\b(abuse|abused|abusive)\b',
        r'\b(rape|raped|molest|molested)\b',
        r'\b(harass|harassed|harassment)\b',
        r'\b(control|controlling|controlled)\b',
        r'\b(toxic|violence|violent)\b',
        r'\b(unsafe|danger|dangerous)\b',
        r'\b(stalk|stalking|stalked)\b',
        r'\b(maara|maari|thappad|punch)\b',  # Hindi physical abuse
        r'\b(rape|molest|chhua|chhed)\b',    # Hindi sexual abuse
        r'\b(control|torture|gali|bura)\b',  # Hindi emotional abuse
        r'\b(safe|khatra|darr|peecha)\b',    # Hindi safety
        # Combined patterns for better detection
        r'\b(he|she|they)\s+(hit|beat|slapped|punched|kicked)\s+(me|him|her)\b',
        r'\b(physically|mentally|emotionally)\s+(hurt|abused|harmed)\b',
    ]
    
    for pattern in abuse_patterns:
        if re.search(pattern, input_lower):
            return True
    
    return False


def get_crisis_response() -> str:
    """
    Return the crisis intervention response.
    """
    return """Outlive Chat is a safe space to find peer support and tools to help manage difficult feelings and thoughts of ending your life. Please don't hesitate to reach out—support is just a text away:

👉 https://chat.outlive.in/landing-page
☎️ More helpline numbers at: https://www.aasra.info/helpline.html

You're not alone, and there are people who want to help you through this difficult time."""


def get_abuse_response() -> str:
    """
    Return the abuse intervention response.
    """
    return """AASRA – We're Here To Help. 💛

If you're feeling unsafe or in pain, please reach out.

Call AASRA: 022 2754 6669

Emergency Numbers:
• Police: 100 • Women Helpline: 1091 • Child Helpline: 1098

You're not alone. Help is available.""" 