"""
Memory Manager for Mental Health Chatbot
Handles both short-term and long-term memory:
- Short-term: Recent conversation messages (session-based)
- Long-term: Daily conversation summaries (persistent across sessions)
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, List
import json
from openai import OpenAI
import pytz

logger = logging.getLogger(__name__)

# India Standard Time timezone
IST = pytz.timezone('Asia/Kolkata')

def get_india_today():
    """Get today's date in India Standard Time (IST)"""
    return datetime.now(IST).date().isoformat()


class MemoryManager:
    """
    Manages conversation memory for users
    """
    
    def __init__(self, openai_client: OpenAI, database):
        self.client = openai_client
        self.db = database
    
    def generate_summary(self, user_id: str, messages: List[Dict[str, Any]], 
                        previous_summary: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a structured summary of the conversation using LLM
        
        Args:
            user_id: User identifier
            messages: List of conversation messages
            previous_summary: Previous summary to build upon (optional)
        
        Returns:
            Dictionary with summary fields
        """
        try:
            # Build prompt for LLM to generate summary
            prompt = self._build_summary_prompt(messages, previous_summary)
            
            # Call LLM to generate summary
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a mental health support assistant that creates concise, structured summaries of conversations with students."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            summary_text = response.choices[0].message.content

            # Log the raw summary for debugging
            logger.info(f"Raw LLM summary for user {user_id}: {summary_text}")

            # Parse the LLM response into structured format
            summary = self._parse_summary(summary_text)

            # Log parsed result
            logger.info(f"Parsed summary for user {user_id}: {summary}")

            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                'main_concerns': None,
                'emotional_patterns': None,
                'coping_strategies': None,
                'progress_notes': None,
                'important_context': None
            }
    
    def _build_summary_prompt(self, messages: List[Dict[str, Any]], 
                             previous_summary: Dict[str, Any] = None) -> str:
        """Build a prompt for LLM to generate conversation summary"""
        
        # Format conversation history
        conversation = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in messages
        ])
        
        prompt = f"""Based on this conversation with a student, create a structured summary that will help maintain context in future conversations.

CONVERSATION:
{conversation}

"""
        
        # Include previous summary if available
        if previous_summary and previous_summary.get('main_concerns'):
            prompt += f"""
PREVIOUS SUMMARY:
- Main Concerns: {previous_summary.get('main_concerns', 'N/A')}
- Emotional Patterns: {previous_summary.get('emotional_patterns', 'N/A')}
- Coping Strategies: {previous_summary.get('coping_strategies', 'N/A')}
- Progress Notes: {previous_summary.get('progress_notes', 'N/A')}

Please update the summary based on today's conversation, noting any changes or progress.
"""
        
        prompt += """
Please provide a summary in the following format (each section should be 1-2 sentences, max 50 words):

MAIN CONCERNS: [What are the primary issues the student is dealing with? e.g., exam stress, family issues, loneliness]

EMOTIONAL PATTERNS: [What emotional states or patterns have been observed? e.g., anxiety in the mornings, feeling overwhelmed, mood swings]

COPING STRATEGIES: [What strategies have been discussed or tried? What worked or didn't work?]

PROGRESS NOTES: [Any notable progress, improvements, or changes since last conversation?]

IMPORTANT CONTEXT: [Any crucial details to remember? e.g., upcoming exams, family situation, friend conflicts]

Keep each section concise and actionable. Focus on information that would help provide better support in future conversations."""
        
        return prompt
    
    def _parse_summary(self, summary_text: str) -> Dict[str, Any]:
        """Parse LLM-generated summary into structured format"""

        summary = {
            'main_concerns': None,
            'emotional_patterns': None,
            'coping_strategies': None,
            'progress_notes': None,
            'important_context': None
        }

        # Parse the structured output - handle both markdown and plain text headers
        sections = {
            'MAIN CONCERNS:': 'main_concerns',
            'EMOTIONAL PATTERNS:': 'emotional_patterns',
            'COPING STRATEGIES:': 'coping_strategies',
            'PROGRESS NOTES:': 'progress_notes',
            'IMPORTANT CONTEXT:': 'important_context'
        }

        current_section = None
        current_content = []

        for line in summary_text.split('\n'):
            line = line.strip()

            # Remove markdown bold formatting if present
            line_cleaned = line.replace('**', '')

            # Check if this line starts a new section
            found_section = False
            for section_header, field_name in sections.items():
                if line_cleaned.startswith(section_header):
                    # Save previous section
                    if current_section and current_content:
                        summary[current_section] = ' '.join(current_content).strip()

                    # Start new section - extract content after header
                    content_after_header = line_cleaned[len(section_header):].strip()
                    current_section = field_name
                    current_content = [content_after_header] if content_after_header else []
                    found_section = True
                    break

            # If not a section header, add to current section
            if not found_section and line and current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            summary[current_section] = ' '.join(current_content).strip()

        return summary
    
    def save_daily_summary(self, user_id: str, access_code: str, 
                          messages: List[Dict[str, Any]]) -> bool:
        """
        Generate and save a summary of today's conversation (using IST timezone)
        
        Args:
            user_id: User identifier
            access_code: User's access code
            messages: Today's conversation messages
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get previous summary to build upon
            previous_summary = self.db.get_latest_summary(user_id)
            
            # Generate new summary
            summary = self.generate_summary(user_id, messages, previous_summary)
            
            # Save to database (using IST for today's date)
            today_ist = get_india_today()
            success = self.db.save_conversation_summary(
                user_id=user_id,
                access_code=access_code,
                summary_date=today_ist,
                main_concerns=summary.get('main_concerns'),
                emotional_patterns=summary.get('emotional_patterns'),
                coping_strategies=summary.get('coping_strategies'),
                progress_notes=summary.get('progress_notes'),
                important_context=summary.get('important_context'),
                message_count=len(messages)
            )
            
            logger.info(f"Saved daily summary for user {user_id} (IST date: {today_ist})")
            return success
            
        except Exception as e:
            logger.error(f"Error saving daily summary: {e}")
            return False
    
    def get_long_term_memory(self, user_id: str, days: int = 7) -> str:
        """
        Get formatted long-term memory context to include in prompts
        
        Args:
            user_id: User identifier
            days: Number of days of history to include
        
        Returns:
            Formatted string with long-term memory context
        """
        try:
            # Get recent summaries
            summaries = self.db.get_conversation_summaries(user_id, days=days)
            
            if not summaries:
                return ""
            
            # Get the most recent summary
            latest = summaries[0] if summaries else None
            
            if not latest:
                return ""
            
            # Format context
            context = "PREVIOUS CONVERSATIONS (Long-term Memory):\n"
            
            if latest.get('main_concerns'):
                context += f"- Main Concerns: {latest['main_concerns']}\n"
            
            if latest.get('emotional_patterns'):
                context += f"- Emotional Patterns: {latest['emotional_patterns']}\n"
            
            if latest.get('coping_strategies'):
                context += f"- Coping Strategies Discussed: {latest['coping_strategies']}\n"
            
            if latest.get('progress_notes'):
                context += f"- Progress/Changes: {latest['progress_notes']}\n"
            
            if latest.get('important_context'):
                context += f"- Important Context: {latest['important_context']}\n"
            
            context += "\nUse this context to provide more personalized and continuous support."
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting long-term memory: {e}")
            return ""
    
    def should_generate_summary(self, user_id: str, message_count: int) -> bool:
        """
        Determine if a summary should be generated (using IST timezone)

        Args:
            user_id: User identifier
            message_count: Number of messages in current session

        Returns:
            True if summary should be generated
        """
        MIN_MESSAGES_FOR_SUMMARY = 10

        try:
            # Get today's date in IST
            today_ist = get_india_today()
            summaries = self.db.get_conversation_summaries(user_id, days=1)

            # Check if summary already exists for today
            # Convert to string for comparison (DB may return date object)
            has_todays_summary = any(
                str(s.get('summary_date')) == today_ist
                for s in summaries
            )

            # Generate summary if:
            # 1. Haven't generated one today (IST) AND
            # 2. Have at least 10 messages in conversation
            return (not has_todays_summary) and (message_count >= MIN_MESSAGES_FOR_SUMMARY)

        except Exception as e:
            logger.error(f"Error checking summary status: {e}")
            return False

    def extract_user_insights(self, user_id: str, access_code: str,
                              messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract non-PII insights about the user from conversation.
        Called periodically (e.g., after summary generation) to build user profile.

        Extracts:
        - life_situation: College year, living situation (without specifics)
        - emotional_triggers: What causes stress/anxiety
        - coping_that_helps: Strategies that work for them
        - interests_hobbies: Activities they enjoy
        - support_system: General support network (without names)
        - goals_aspirations: What they're working towards
        """
        try:
            # Get existing insights to merge with
            existing = self.db.get_user_insights(user_id)

            # Format conversation
            conversation = "\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in messages[-20:]  # Last 20 messages
            ])

            prompt = f"""Based on this conversation, extract NON-IDENTIFIABLE insights about the user.
DO NOT include: names, specific schools/colleges, phone numbers, locations, or any PII.
DO include: general life stage, emotional patterns, what helps them, interests.

CONVERSATION:
{conversation}

EXISTING INSIGHTS (merge with these, update if new info):
{json.dumps(existing, indent=2) if existing else "None yet"}

Extract insights in this exact format (each 1-2 sentences max, or "Unknown" if not mentioned):

LIFE_SITUATION: [e.g., "College student in 2nd year", "Lives with family", "Working while studying"]

EMOTIONAL_TRIGGERS: [What causes them stress/anxiety, e.g., "Academic pressure especially before exams", "Comparison with peers"]

COPING_THAT_HELPS: [Strategies that work for them, e.g., "Talking to friends helps", "Music and journaling"]

INTERESTS_HOBBIES: [What they enjoy, e.g., "Enjoys playing guitar", "Likes reading fiction"]

SUPPORT_SYSTEM: [General support without names, e.g., "Has a close friend group", "Supportive sibling"]

GOALS_ASPIRATIONS: [What they want, e.g., "Wants to do well in exams", "Exploring career options"]

Remember: NO NAMES, NO SPECIFIC PLACES, NO IDENTIFIABLE INFO."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You extract non-identifiable user insights for mental health support context. Never include names, schools, or specific locations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )

            insights_text = response.choices[0].message.content
            insights = self._parse_insights(insights_text)

            # Save to database
            self.db.save_user_insights(
                user_id=user_id,
                access_code=access_code,
                life_situation=insights.get('life_situation'),
                emotional_triggers=insights.get('emotional_triggers'),
                coping_that_helps=insights.get('coping_that_helps'),
                interests_hobbies=insights.get('interests_hobbies'),
                support_system=insights.get('support_system'),
                goals_aspirations=insights.get('goals_aspirations')
            )

            logger.info(f"Extracted and saved insights for user {user_id}")
            return insights

        except Exception as e:
            logger.error(f"Error extracting user insights: {e}")
            return {}

    def _parse_insights(self, text: str) -> Dict[str, Any]:
        """Parse LLM-generated insights into structured format"""
        insights = {}

        sections = {
            'LIFE_SITUATION:': 'life_situation',
            'EMOTIONAL_TRIGGERS:': 'emotional_triggers',
            'COPING_THAT_HELPS:': 'coping_that_helps',
            'INTERESTS_HOBBIES:': 'interests_hobbies',
            'SUPPORT_SYSTEM:': 'support_system',
            'GOALS_ASPIRATIONS:': 'goals_aspirations'
        }

        for line in text.split('\n'):
            line = line.strip()
            for header, field in sections.items():
                if line.startswith(header):
                    value = line[len(header):].strip()
                    # Don't save "Unknown" values
                    if value and value.lower() != 'unknown':
                        insights[field] = value
                    break

        return insights

    def get_user_insights_context(self, user_id: str) -> str:
        """
        Get formatted user insights to include in system prompt.
        Returns empty string if no insights available.
        """
        try:
            insights = self.db.get_user_insights(user_id)

            if not insights or not any(insights.values()):
                return ""

            context = "USER CONTEXT (what you know about this person):\n"

            if insights.get('life_situation'):
                context += f"- Situation: {insights['life_situation']}\n"
            if insights.get('emotional_triggers'):
                context += f"- What triggers stress: {insights['emotional_triggers']}\n"
            if insights.get('coping_that_helps'):
                context += f"- What helps them: {insights['coping_that_helps']}\n"
            if insights.get('interests_hobbies'):
                context += f"- Interests: {insights['interests_hobbies']}\n"
            if insights.get('support_system'):
                context += f"- Support: {insights['support_system']}\n"
            if insights.get('goals_aspirations'):
                context += f"- Goals: {insights['goals_aspirations']}\n"

            context += "\nUse this context to personalize your responses."
            return context

        except Exception as e:
            logger.error(f"Error getting user insights context: {e}")
            return ""

