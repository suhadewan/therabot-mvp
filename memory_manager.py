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
    
    def should_generate_summary(self, user_id: str, message_count: int = 10) -> bool:
        """
        Determine if a summary should be generated (using IST timezone)
        
        Args:
            user_id: User identifier
            message_count: Number of messages in current session
        
        Returns:
            True if summary should be generated
        """
        try:
            # Get today's date in IST
            today_ist = get_india_today()
            summaries = self.db.get_conversation_summaries(user_id, days=1)
            
            # Check if summary already exists for today
            has_todays_summary = any(
                s.get('summary_date') == today_ist 
                for s in summaries
            )
            
            # Generate summary if:
            # 1. Haven't generated one today (IST) AND
            # 2. Have at least 10 messages in conversation
            return (not has_todays_summary) and (message_count >= message_count)
            
        except Exception as e:
            logger.error(f"Error checking summary status: {e}")
            return False

