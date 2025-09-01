from typing import Tuple, Dict, Any
import json


def analyze_content_with_llm(user_input: str, client: Any) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Use LLM to analyze user input for concerning content.
    Returns (is_concerning, response_type, analysis_details)
    """
    
    analysis_prompt = f"""
You are a mental health safety analyst. Analyze the following user input for concerning content related to:
1. Suicide/self-harm (including passive thoughts)
2. Abuse (physical, sexual, emotional, verbal) - including phrases like "he hurt me", "she hit me", "they beat me", "physically hurt", "abused me"
3. Crisis situations (feeling unsafe, in danger)
4. Severe mental health distress

User input: "{user_input}"

Respond with a JSON object containing:
{{
    "is_concerning": true/false,
    "concern_type": "suicide"|"abuse"|"crisis"|"distress"|"none",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this is concerning",
    "severity": "low"|"medium"|"high"|"critical",
    "response_needed": true/false
}}

IMPORTANT: Be very sensitive to abuse indicators. Mark as concerning if the user mentions:
- Being hurt by someone (physically, emotionally, sexually)
- Violence or abuse from family, partner, or others
- Feeling unsafe or in danger
- Being controlled or threatened

Only mark as concerning if you have high confidence (>0.7) that the content indicates:
- Active suicidal thoughts or plans
- Current abuse or violence (including "he hurt me", "she hit me", etc.)
- Immediate safety concerns
- Severe mental health crisis

Be conservative - false positives are better than missing real concerns.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using a more capable model for analysis
            messages=[
                {"role": "system", "content": "You are a mental health safety analyst. Always respond with valid JSON."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=200
        )
        
        analysis_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            analysis = json.loads(analysis_text)
            
            # Validate required fields
            required_fields = ["is_concerning", "concern_type", "confidence", "reasoning", "severity", "response_needed"]
            if all(field in analysis for field in required_fields):
                
                # Only act if confidence is high and response is needed
                # Lower threshold for abuse detection (0.6) vs other concerns (0.7)
                confidence_threshold = 0.6 if analysis["concern_type"] == "abuse" else 0.7
                
                if (analysis["is_concerning"] and 
                    analysis["confidence"] > confidence_threshold and 
                    analysis["response_needed"]):
                    
                    return True, analysis["concern_type"], analysis
                
        except json.JSONDecodeError:
            # If JSON parsing fails, do a simple keyword check as fallback
            return simple_fallback_check(user_input)
            
    except Exception as e:
        print(f"LLM safety analysis failed: {e}")
        return simple_fallback_check(user_input)
    
    return False, "none", {}


def simple_fallback_check(user_input: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Simple fallback check when LLM analysis fails.
    """
    input_lower = user_input.lower()
    
    # Basic concerning patterns
    concerning_patterns = [
        ("suicide", ["suicide", "kill myself", "want to die", "end my life"]),
        ("abuse", ["hit me", "beat me", "abuse", "rape", "molest", "harass"]),
        ("crisis", ["unsafe", "danger", "afraid", "scared", "terrified"]),
        ("distress", ["can't take it", "overwhelmed", "hopeless", "desperate"])
    ]
    
    for concern_type, keywords in concerning_patterns:
        for keyword in keywords:
            if keyword in input_lower:
                return True, concern_type, {
                    "is_concerning": True,
                    "concern_type": concern_type,
                    "confidence": 0.8,
                    "reasoning": f"Detected keyword: {keyword}",
                    "severity": "medium",
                    "response_needed": True
                }
    
    return False, "none", {}


def get_llm_detected_response(concern_type: str, analysis: Dict[str, Any]) -> str:
    """
    Generate appropriate response based on LLM-detected concern type.
    """
    
    if concern_type == "suicide":
        return """🚨 Crisis Support Available

I'm concerned about what you're sharing. You're not alone, and help is available right now.

Immediate Support:
👉 Outlive Chat: https://chat.outlive.in/landing-page
☎️ AASRA Helpline: 022 2754 6669
📞 Crisis Helpline: 1800-599-0019

You matter, and there are people who want to help you through this difficult time.

If you're in immediate danger, please call emergency services (112) or go to the nearest hospital."""
    
    elif concern_type == "abuse":
        return """🛡️ Safety Support Available

I'm concerned about your safety. You deserve to feel safe and supported.

Immediate Help:
☎️ AASRA: 022 2754 6669
📞 Women Helpline: 1091
🚔 Police: 100

For immediate safety:
• If you're in immediate danger, call 100 (Police) or 112 (Emergency)
• Reach out to a trusted friend, family member, or teacher
• Consider contacting a counselor or mental health professional

You deserve to feel safe. There are people who want to help you."""
    
    elif concern_type == "crisis":
        return """⚠️ Safety Concern Detected

I'm concerned about your safety. Please know that help is available.

Emergency Resources:
🚔 Police: 100
🚑 Emergency: 112
☎️ AASRA: 022 2754 6669

If you're feeling unsafe:
• Call emergency services immediately if in danger
• Reach out to someone you trust
• Consider speaking with a mental health professional

Your safety matters. Don't hesitate to ask for help."""
    
    else:  # distress or other concerns
        return """💙 Support Available

I can see you're going through a difficult time. You don't have to face this alone.

Professional Support:
☎️ AASRA: 022 2754 6669
📞 Kiran Helpline: 1800-599-0019
🌐 Tele Manas: 1800-891-4416

Consider reaching out to:
• A trusted friend or family member
• A school counselor or teacher
• A mental health professional

It's okay to ask for help. You deserve support.""" 