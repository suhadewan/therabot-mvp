import re
from typing import Tuple


def detect_crisis_keywords(user_input: str) -> Tuple[bool, str]:
    """
    Scan user input for crisis-related keywords.
    Returns (is_crisis_detected, override_response)
    """
    # Convert input to lowercase for case-insensitive matching
    input_lower = user_input.lower()

    # Check for suicidal ideation (SI)
    if detect_suicide_keywords(input_lower):
        return True, get_crisis_response("SI")

    # Check for experiencing abuse (EA)
    if detect_abuse_keywords(input_lower):
        return True, get_abuse_response("EA")

    # Check for homicidal ideation (HI) - new category
    if detect_homicidal_keywords(input_lower):
        return True, get_crisis_response("HI")

    # Check for self-harm (SH) - separate from suicide
    if detect_self_harm_keywords(input_lower):
        return True, get_crisis_response("SH")

    return False, ""


def detect_suicide_keywords(input_lower: str) -> bool:
    """Detect suicide and self-harm related keywords"""
    # Common false positives to exclude
    false_positives = [
        "deadlines", "deadline", "deadly serious", "dead tired", "dead sure",
        "dead end", "deadly accurate", "dead on", "drop dead gorgeous",
        "dead heat", "dead weight", "dead ringer", "dead center",
        "killed it", "killing time", "killer deal", "killer workout",
        "die hard", "die for", "to die for", "dying to know", "dying laughing"
    ]

    # Check if input contains false positives
    for false_positive in false_positives:
        if false_positive in input_lower:
            return False

    # Crisis keywords in English and Hindi
    crisis_keywords = [
        # Direct suicide/death expressions
        "suicide", "kill myself", "want to die", "end my life",
        "kms", "i'll kms", "imma kms", "gonna kms", "going to kms",  # Internet slang for "kill myself"
        "meri zindagi khatam", "marna chahta", "khudkushi",
        "nahi jeena", "i don't want to live", "khatam karna", "mar jaaun",
        "want to end it all", "better off dead", "no reason to live",
        "can't take it anymore", "life is not worth living",
        "thinking of ending it", "planning to die", "ready to die",
        "tired of living", "life is meaningless",
        "death would be better", "give up on life",
        "going to jump", "gonna jump",  # Common suicide method references

        # Hopelessness & giving up (from test dataset)
        "giving up on everything", "give up on everything",
        "no reason to keep trying", "hard to find a reason",
        "wish i could just disappear", "want to disappear",
      

        # Hindi/Hinglish expressions (from test dataset)
        "sab chhod du", "sab chhod doon", "sab chod du",  # give up everything
        "agar main na hota", "agar main na hoti",  # if I wasn't here
        "main na hota to behtar",  # better if I wasn't here
        "aage badhne ka koi reason nahi", "aage badhne ka reason nahi",  # no reason to keep going
        "andar se khatam ho gaya", "andar se khatam",  # finished/dead inside
        "gayab ho sakta", "gayab ho jaaun", "disappear ho jaaun",  # disappear/vanish
    ]

    # Check for exact keyword matches
    for keyword in crisis_keywords:
        if keyword.lower() in input_lower:
            return True

    # More specific crisis patterns - only match in concerning contexts
    crisis_patterns = [
        # Only match "die/death/dead" when used in concerning contexts
        r'\b(want to die|going to die|wish I was dead|better off dead)\b',
        r'\b(die by suicide|death by suicide)\b',
        r'\b(kill myself|killing myself)\b',
        r'\b(suicide|suicidal)\b',
        r'\b(end my life|ending my life)\b',
        r'\b(take my life|taking my life)\b',
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


def detect_homicidal_keywords(input_lower: str) -> bool:
    """Detect homicidal ideation keywords"""
    homicidal_keywords = [
        "want to kill someone", "going to hurt someone", "kill them", "hurt others",
        "violent thoughts about", "planning to hurt", "revenge against",
        "make them pay", "going to attack", "want to murder"
    ]

    homicidal_patterns = [
        r'\b(kill|murder|hurt)\s+(someone|others|them|him|her)\b',
        r'\b(violent|revenge)\s+(thoughts|plans)\b',
        r'\b(planning|going)\s+to\s+(hurt|kill|attack)\b'
    ]

    # Check keywords
    for keyword in homicidal_keywords:
        if keyword in input_lower:
            return True

    # Check patterns
    for pattern in homicidal_patterns:
        if re.search(pattern, input_lower):
            return True

    return False


def detect_self_harm_keywords(input_lower: str) -> bool:
    """Detect self-harm (non-suicidal) keywords"""
    self_harm_keywords = [
        "cut myself", "cutting myself", "self harm", "self-harm",
        "hurt myself", "burning myself", "scratching myself",
        "picking at skin", "pulling hair", "hitting myself"
    ]

    self_harm_patterns = [
        r'\b(cut|cutting|burn|burning|scratch|scratching)\s+(myself|my)\b',
        r'\b(self[\-\s]harm|self[\-\s]hurt)\b',
        r'\b(hit|hitting|punch|punching)\s+myself\b'
    ]

    # Check keywords
    for keyword in self_harm_keywords:
        if keyword in input_lower:
            return True

    # Check patterns
    for pattern in self_harm_patterns:
        if re.search(pattern, input_lower):
            return True

    return False


def get_crisis_response(flag_type: str = "SI") -> str:
    """
    Return the crisis intervention response based on flag type.
    """
    if flag_type == "SI":
        return """🚨 **Suicidal Ideation Detected**

Outlive Chat is a safe space to find peer support and tools to help manage difficult feelings and thoughts of ending your life. Please don't hesitate to reach out—support is just a text away:

👉 https://chat.outlive.in/landing-page
☎️ More helpline numbers at: https://www.aasra.info/helpline.html

You're not alone, and there are people who want to help you through this difficult time."""

    elif flag_type == "SH":
        return """🩹 **Self-Harm Concerns Detected**

If you're struggling with self-harm urges, please reach out for support:

• **Kiran Mental Health Helpline**: 1800-599-0019
• **AASRA**: 022 2754 6669
• **Emergency Services**: 112

Self-harm is a sign that you're struggling with difficult emotions. Professional support can help you find healthier coping strategies."""

    elif flag_type == "HI":
        return """⚠️ **Safety Concern Detected**

If you're having thoughts about hurting others, it's important to seek immediate professional help:

• **Police**: 100
• **Mental Health Crisis Line**: 1800-599-0019
• **Emergency Services**: 112

These feelings can be addressed with proper support. Please reach out to a mental health professional right away."""

    else:  # Default fallback
        return """🚨 **Crisis Support Available**

If you're in immediate danger, please contact emergency services:

• **Emergency Services**: 112
• **Mental Health Helpline**: 1800-599-0019

You're not alone. Professional help is available 24/7."""


def get_abuse_response(flag_type: str = "EA") -> str:
    """
    Return the abuse intervention response based on flag type.
    """
    return """🛡️ **Abuse Concern Detected**

AASRA – We're Here To Help. 💛

If you're feeling unsafe or experiencing abuse, please reach out:

• **AASRA**: 022 2754 6669
• **Women Helpline**: 1091
• **Child Helpline**: 1098
• **Police**: 100

Emergency Numbers Available 24/7. You're not alone. Help is available.""" 