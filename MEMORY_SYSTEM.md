# Memory System Documentation

## Overview

The MindMitra chatbot now includes a comprehensive memory system with both **short-term** and **long-term** memory to provide more personalized and contextually aware support to students.

## Memory Types

### 1. Short-Term Memory (Daily Session)
- **What**: ALL messages from TODAY's conversation
- **Storage**: Today's messages loaded from database
- **Purpose**: Maintains full conversation context throughout the day
- **Reset**: Automatically clears at midnight IST (new day = fresh start)
- **Implementation**: Only today's messages are loaded on each request
- **Timezone**: Uses India Standard Time (IST / Asia/Kolkata) regardless of server location

### 2. Long-Term Memory (Persistent Summaries)
- **What**: Structured summaries of conversations over time
- **Storage**: Database table `conversation_summaries`
- **Purpose**: Remembers key information across sessions (days, weeks)
- **Implementation**: AI-generated summaries stored as structured data

## How It Works

### Summary Structure

Each summary contains:
- **Main Concerns**: Primary issues the student is dealing with (e.g., exam stress, family problems)
- **Emotional Patterns**: Observable emotional states and patterns (e.g., anxiety in mornings, mood swings)
- **Coping Strategies**: What strategies have been discussed and their effectiveness
- **Progress Notes**: Any improvements, changes, or developments
- **Important Context**: Crucial details to remember (e.g., upcoming exams, family situations)

### Automatic Summary Generation

Summaries are automatically generated:
1. **Trigger**: After at least 10 messages (5 exchanges) in a day
2. **Condition**: Only once per day (won't duplicate if already generated)
3. **Process**: 
   - Analyzes entire day's conversation
   - Builds upon previous day's summaries
   - Saves to database with today's date
4. **Purpose**: Captures today's session for tomorrow's context

### Context Injection

When processing a user message:
1. **Load short-term memory**: ALL messages from today only
2. **Load long-term memory**: Most recent summary (from previous days)
3. **Build system prompt**: Base prompt + long-term memory context
4. **Send to LLM**: System prompt + today's messages

**Key Behavior:**
- **Same day**: Bot remembers everything said today
- **Next day**: Fresh conversation with context from yesterday's summary

Example context added to system prompt:
```
PREVIOUS CONVERSATIONS (Long-term Memory):
- Main Concerns: Struggling with 12th board exam preparation, feeling overwhelmed
- Emotional Patterns: Anxiety increases in the evening, difficulty sleeping
- Coping Strategies Discussed: Deep breathing exercises (tried, helped a bit), talking to friends (not tried yet)
- Progress/Changes: Started using study schedule this week, feeling slightly more organized
- Important Context: Board exams in 2 months, parents have high expectations

Use this context to provide more personalized and continuous support.
```

## API Endpoints

### Generate Summary (Manual)
```
POST /api/memory/summary/generate
Body: { "user_id": "user_login_id" }
```
Manually triggers summary generation for a user.

### Get Latest Summary
```
GET /api/memory/summary/<user_id>
```
Retrieves the most recent summary for a user.

### Get All Summaries
```
GET /api/memory/summaries/<user_id>?days=30
```
Retrieves all summaries for a user (default: last 30 days).

## Database Schema

### Table: `conversation_summaries`
```sql
CREATE TABLE conversation_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    access_code TEXT NOT NULL,
    summary_date DATE NOT NULL,
    main_concerns TEXT,
    emotional_patterns TEXT,
    coping_strategies TEXT,
    progress_notes TEXT,
    important_context TEXT,
    message_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, summary_date)
)
```

## Benefits

1. **Continuity**: Bot remembers previous conversations and builds upon them
2. **Personalization**: Responses are tailored based on known context
3. **Progress Tracking**: Can reference what worked or didn't work before
4. **Efficiency**: Don't need to re-explain situation every time
5. **Better Support**: More informed responses based on history

## Example Conversation Flow

### Day 1 - Morning:
**User**: "I'm really stressed about my board exams"
**Bot**: "That sounds really tough. Can you tell me more about what's stressing you the most?"

### Day 1 - Evening (same day):
**User**: "I'm back, tried that study schedule"
**Bot**: *(Remembers morning conversation)* "Great! How did the study schedule work out for you?"
*(At end of day: Summary automatically generated from all of Day 1's messages)*

### Day 2 - Morning (next day):
**User**: "Hi, I'm back"
**Bot**: *(Chat history is empty, but has Day 1's summary)*
"Welcome back! How have you been managing the board exam preparation since we last talked?"
*(Starts fresh conversation with context from yesterday's summary)*

## Configuration

### Summary Generation Threshold
Default: 10 messages (5 exchanges) - configurable in `pwa_app.py` line 316

```python
if session_message_count >= 10:  # At least 5 exchanges
    # Generate summary once per day
```

### Memory Window
- **Short-term**: ALL messages from today (resets daily at midnight)
- **Long-term**: Last 7 days of summaries

Both can be adjusted as needed.

## Testing

### Test Summary Generation
```bash
curl -X POST http://localhost:5000/api/memory/summary/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user_123"}'
```

### View Summary
```bash
curl http://localhost:5000/api/memory/summary/test_user_123
```

## Future Enhancements

Potential improvements:
1. **Sentiment Tracking**: Track emotional trends over time
2. **Goal Setting**: Remember and track goals set by students
3. **Trigger Detection**: Identify recurring triggers or patterns
4. **Weekly Reports**: Generate weekly summaries for reflection
5. **Export Summaries**: Allow students to export their progress

## Timezone Support

The system is designed for students in India and uses **India Standard Time (IST / UTC+5:30)** for all date-based operations:

- **Daily Reset**: Happens at midnight IST, not server time
- **Message Grouping**: Messages are grouped by IST date
- **Summary Generation**: Triggered based on IST day
- **Works Anywhere**: Server can be hosted anywhere (AWS US, Render, etc.) and will still use IST

### How It Works

1. **Date Determination**: All "today" checks use `datetime.now(IST)` 
2. **Message Filtering**: Timestamps are converted from UTC to IST before comparison
3. **Consistent Experience**: Students in Mumbai, Delhi, or Bangalore all get the same behavior

### Example

```
Server Location: AWS US-East (UTC-5)
Student Location: Mumbai, India (UTC+5:30)
Student Time: 11:30 PM IST (October 4)
Server Time: 12:00 PM EST (October 4)

✅ System correctly identifies it as October 4 in IST
✅ Student's messages are grouped with October 4
✅ At midnight IST, new day starts (even though server time is different)
```

## Privacy & Security

- Summaries are stored securely in the database
- Only accessible via authenticated user IDs
- Can be deleted if user requests data removal
- Follows same security model as chat messages

## Maintenance

### Cleanup Old Summaries
Currently, summaries are kept indefinitely. To implement cleanup:

```python
# Add to database.py
def cleanup_old_summaries(self, days: int = 90) -> int:
    """Delete summaries older than specified days"""
    # Implementation here
```

### Backup
Summaries are in the main database, so regular database backups include them.

