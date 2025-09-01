# MindMitra - Mental Health Support MVP

A supportive mental health chatbot for youth built with Streamlit and OpenAI's GPT-4o-mini.

## Features

- 🧠 Empathetic conversational AI for mental wellness support
- 🛡️ Content moderation for user safety
- 📏 Response guardrails (50 words max, follow-up questions)
- ⚡ Rate limiting (20 requests/hour per IP)
- 🔒 Secure API key management
- 🚀 Streamlit Community Cloud deployment ready

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mental-health-bot-mvp.git
cd mental-health-bot-mvp
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip3 install -r requirements.txt
```

4. Set up secrets:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and add your OpenAI API key
```

5. Run the app:
```bash
streamlit run app.py
```

### Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run linting:
```bash
black .
isort .
flake8 .
```

## Deployment

### Streamlit Community Cloud

1. Fork this repository
2. Sign in to [share.streamlit.io](https://share.streamlit.io)
3. Deploy from your GitHub repository
4. Add your OpenAI API key in the Streamlit secrets management

### Configuration

### Required Secrets
- `OPENAI_API_KEY`: Your OpenAI API key

### Optional Configuration

The app supports extensive configuration through both Streamlit secrets and environment variables. You can customize behavior by:

1. **Using Streamlit secrets** (recommended for Streamlit Cloud):
   - Add configuration sections to your `.streamlit/secrets.toml`
   - See `.streamlit/secrets.toml.example` for all options

2. **Using environment variables**:
   - Prefix any config with `THERABOT_`
   - Example: `THERABOT_RATE_LIMIT_REQUESTS=30`

#### Available Configuration Options

| Category | Config Key | Default | Description |
|----------|------------|---------|-------------|
| **Rate Limiting** | | | |
| | `rate_limit.requests_per_hour` | 20 | Max requests per hour |
| | `rate_limit.window_hours` | 1 | Time window in hours |
| **AI Model** | | | |
| | `model.name` | gpt-4o-mini | OpenAI model to use |
| | `model.temperature` | 0.7 | Response randomness (0-1) |
| | `model.max_tokens` | 100 | Max response length |
| | `model.stream` | true | Enable streaming |
| **Guardrails** | | | |
| | `guardrails.max_words` | 50 | Max words per response |
| | `guardrails.max_sentences` | 3 | Max sentences per response |
| | `guardrails.require_question` | true | End with question |
| | `guardrails.max_retries` | 3 | Max regeneration attempts |
| **UI** | | | |
| | `ui.page_title` | Mental Health Support Bot | Browser tab title |
| | `ui.chat_placeholder` | How are you feeling today? | Input placeholder |
| **Moderation** | | | |
| | `moderation.high_risk_categories` | self-harm,self-harm/intent,self-harm/instructions | Comma-separated list |

### Example Configuration

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-..."

[rate_limit]
requests_per_hour = 30
window_hours = 1

[model]
name = "gpt-4"
temperature = 0.8
max_tokens = 150

[guardrails]
max_words = 75
max_sentences = 4
```

## Project Structure

```
├── app.py                    # Main Streamlit application
├── system_prompt.txt         # AI system prompt configuration
├── guardrails.py            # Response validation and regeneration
├── moderation.py            # Content moderation wrapper
├── requirements.txt         # Python dependencies
├── tests/                   # Unit tests
├── .streamlit/              # Streamlit configuration
└── .github/workflows/       # CI/CD pipeline
```

## Important Notes

- **Non-Clinical Tool**: This is NOT a replacement for professional mental health services
- **System Prompt**: Replace the placeholder in `system_prompt.txt` with actual content before production deployment
- **Rate Limiting**: Currently uses in-memory storage; consider Redis for production
- **Safety**: Always displays crisis resources and disclaimers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is for educational purposes. Please ensure compliance with healthcare regulations in your jurisdiction before deploying.