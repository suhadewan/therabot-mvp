# MindMitra - Mental Health Support Chatbot

A Progressive Web App providing AI-powered mental health support for Indian college students, built with Flask and OpenAI's GPT-4o-mini. Developed as part of a research study on peer-support chatbots.

## Features

### AI Chat
- Fine-tuned GPT-4o-mini for culturally aware, empathetic conversations
- Long-term memory with daily conversation summaries and user insights
- Short, focused responses with follow-up questions

### Safety System
- **Crisis keyword detection** for suicidal ideation, self-harm, abuse, and harm to others
- **OpenAI Moderation API** for background content screening
- **Automated flagging** with email notifications to on-call reviewers
- **Manual reviewer flagging** from the reviewer portal
- Crisis responses append helpline resources to the bot's natural reply

### Reviewer Portal
- Three-reviewer dashboard with user assignment
- View full chat histories with flag indicators
- Manually flag or dismiss flagged messages
- Flag types: SI (Suicidal Ideation), SH (Self-Harm), HI (Harm to Others), EA (Abuse)

### Engagement Features
- Daily feelings thermometer (0-10 scale)
- Streak tracking with freeze support
- Badge progression system
- Daily check-in checklists (A/B tested with feature groups)

### User Management
- Access code authentication
- Auto-assignment of reviewers on first message
- User restriction after repeated flags (3 in 7 days)
- Emergency contact collection

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- PostgreSQL database (or SQLite for local dev)

### Setup

```bash
# Clone and install
git clone <repo-url>
cd therabot-mvp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp production.env.template .env
# Edit .env with your API keys and database URL

# Run
python pwa_app.py
```

The app runs at `http://localhost:5002`

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `DATABASE_TYPE` | `sqlite` or `postgresql` | No (default: sqlite) |
| `DATABASE_URL` | PostgreSQL connection string | If using postgresql |
| `SECRET_KEY` | Flask session secret | Yes (for production) |
| `REVIEWER_PASSWORD` | Reviewer portal password | Yes |
| `POSTMARK_API_KEY` | Postmark email API key | For email notifications |
| `SENTRY_DSN` | Sentry error tracking | No |

## Project Structure

```
therabot-mvp/
├── pwa_app.py                 # Main Flask application
├── database.py                # Database layer (SQLite + PostgreSQL)
├── config.py                  # App configuration
├── crisis_detection.py        # Crisis keyword detection
├── moderation.py              # OpenAI moderation wrapper
├── llm_safety_check.py        # LLM-based safety analysis
├── guardrails.py              # Response validation
├── memory_manager.py          # Long-term memory & daily summaries
├── email_notifications.py     # Reviewer email alerts
├── name_filter.py             # PII name redaction
├── rate_limiter.py            # Request rate limiting
├── system_prompt.txt          # Active system prompt
├── templates/
│   ├── index.html             # Chat interface
│   ├── login.html             # Access code login
│   ├── consent.html           # Study consent form
│   ├── emergency_contact.html # Emergency contact form
│   ├── reviewer.html          # Reviewer dashboard
│   ├── admin.html             # Admin dashboard
│   └── ...
├── static/
│   ├── manifest.json          # PWA manifest
│   ├── sw.js                  # Service worker
│   └── ...
└── tests/
    └── test_guardrails.py
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with access code
- `POST /api/auth/logout` - Logout

### Chat
- `POST /api/chat` - Send message, get AI response
- `POST /api/chat/stream` - SSE streaming response

### Reviewer Portal
- `GET /api/reviewer/<id>/users` - Get assigned users
- `GET /api/reviewer/<id>/user-chats/<code>` - Get user's chat history
- `POST /api/reviewer/dismiss-flag` - Dismiss a flag
- `POST /api/reviewer/manual-flag` - Manually flag a message

### Admin
- `GET /admin/flagged-chats` - View flagged conversations
- `GET /admin/stats` - Usage statistics

## Deployment

Configured for [Render](https://render.com) via `render.yaml`. Uses Gunicorn in production:

```bash
gunicorn -w 4 -b 0.0.0.0:$PORT pwa_app:app
```

## Safety Resources

### Crisis Helplines (India)
- **AASRA**: 022 2754 6669
- **Kiran National Helpline**: 1800-599-0019
- **Emergency Services**: 112

---

**Disclaimer**: MindMitra is a research tool providing supportive conversations and crisis resource information. It is not a substitute for professional mental health treatment or diagnosis. In case of emergencies, contact local emergency services immediately.
