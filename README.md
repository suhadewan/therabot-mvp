# MindMitra - Mental Health Support PWA 🧠

A comprehensive Progressive Web App (PWA) providing mental health support for Indian high school students with advanced safety features, user management, and daily mood tracking.

## ✨ Key Features

### 🤖 **AI-Powered Mental Health Support**
- **Fine-tuned GPT-4o-mini model** specifically trained for Indian high school students
- **Culturally aware responses** understanding academic pressures and family dynamics
- **Empathetic conversation** with validation and understanding
- **Crisis intervention** with automatic keyword detection and resource provision
- **Short, focused responses** (under 50 words) with follow-up questions

### 🛡️ **Advanced Safety & Moderation**
- **Multi-layer content moderation**:
  - Crisis keyword detection (suicide, self-harm, abuse)
  - OpenAI content moderation API
  - LLM-based safety analysis
- **Automated crisis response** with helpline numbers and resources
- **Flagged conversation tracking** for admin review
- **Real-time safety intervention** when concerning content is detected

### 🌡️ **Daily Feelings Thermometer** *(New Feature)*
- **Daily mood check-ins** with 0-10 scale rating
- **Automatic popup** on first daily visit
- **Mood history tracking** for pattern analysis
- **Skip functionality** to avoid repeat prompts
- **Database integration** for long-term insights

### 👥 **User Management System**
- **Access code-based authentication** for controlled access
- **Multi-tier user types** (student, counselor, admin)
- **School-specific access codes** for institutional use
- **Session management** with automatic validation
- **User activity tracking** and analytics

### 📊 **Admin Dashboard**
- **Flagged conversation monitoring** with detailed analysis
- **User management** and access code creation
- **Usage statistics** and analytics
- **Access code management** (create, update, deactivate)
- **Crisis intervention logs** for follow-up

### 📱 **Progressive Web App Features**
- **Installable** on mobile devices and desktops
- **Offline functionality** with service worker
- **Native app experience** with custom icons and splash screens
- **Responsive design** optimized for all screen sizes
- **Fast loading** with optimized assets and caching

### 💾 **Database & Storage**
- **SQLite database** with schema migration support
- **PostgreSQL ready** for production scaling
- **Comprehensive chat history** with persistent storage
- **Feelings tracking** with daily uniqueness constraints
- **Audit trail** for all user interactions

### 🔐 **Security & Privacy**
- **Secure session management** with token validation
- **Rate limiting** (20 requests/hour per user)
- **IP tracking** for security monitoring
- **Access code validation** with usage limits
- **Admin authentication** with password hashing

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Modern web browser

### Installation

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd therabot-mvp
```

2. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Environment setup**:
```bash
# Create .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

5. **Initialize database**:
```bash
python -c "from database import init_database; init_database('sqlite')"
```

6. **Create admin user**:
```bash
python create_admin_user.py
```

7. **Generate access codes**:
```bash
python create_access_codes.py
```

8. **Run the application**:
```bash
python pwa_app.py
```

The app will be available at `http://localhost:5002`

## 📁 Project Structure

```
therabot-mvp/
├── pwa_app.py                  # Main Flask application
├── database.py                 # Database abstraction layer
├── config.py                   # Configuration management
├── system_prompt.txt           # AI system prompt
├── crisis_detection.py         # Crisis keyword detection
├── llm_safety_check.py        # LLM-based content analysis
├── moderation.py              # OpenAI moderation wrapper
├── guardrails.py              # Response validation & regeneration
├── create_admin_user.py       # Admin user creation utility
├── create_access_codes.py     # Access code generation utility
├── requirements.txt           # Python dependencies
├── templates/                 # HTML templates
│   ├── index.html            # Main chat interface
│   ├── login.html            # User authentication
│   ├── admin_login.html      # Admin authentication
│   └── admin.html            # Admin dashboard
└── static/                   # Static assets
    ├── manifest.json         # PWA manifest
    ├── sw.js                 # Service worker
    └── logo.jpeg             # App logo
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `THERABOT_MODEL_NAME` | AI model to use | `gpt-4o-mini` |
| `THERABOT_RATE_LIMIT_REQUESTS` | Requests per hour | `20` |
| `THERABOT_MODEL_TEMPERATURE` | Response creativity (0-1) | `0.7` |
| `THERABOT_MODEL_MAX_TOKENS` | Max response length | `100` |
| `PORT` | Server port | `5002` |

### Database Configuration

The app uses SQLite by default but supports PostgreSQL for production:

```python
# SQLite (default)
db_manager = init_database("sqlite", db_path="mental_health_bot.db")

# PostgreSQL
db_manager = init_database("postgresql",
                          connection_string="postgresql://user:pass@host:port/db")
```

## 🛠️ API Endpoints

### Authentication
- `POST /api/auth/login` - User login with access code
- `POST /api/auth/validate` - Validate existing session
- `POST /api/auth/logout` - User logout

### Chat
- `POST /api/chat` - Send message and get AI response
- `GET /api/session/<user_id>` - Get chat history
- `POST /api/clear-session/<user_id>` - Clear chat history

### Feelings Tracking
- `POST /api/feelings/check` - Check if feeling recorded today
- `POST /api/feelings/record` - Record daily feeling score
- `GET /api/feelings/history/<user_id>` - Get feeling history

### Admin
- `POST /api/admin/login` - Admin authentication
- `GET /admin/flagged-chats` - View flagged conversations
- `GET /admin/all-chats` - View all conversations
- `GET /admin/stats` - Get usage statistics
- `GET /admin/access-codes` - Manage access codes

## 🎯 Usage Scenarios

### For Students
1. **Access the app** using provided access code
2. **Daily check-in** with feelings thermometer (0-10 scale)
3. **Chat with AI** for mental health support
4. **Receive crisis resources** if concerning content detected
5. **View chat history** across sessions

### For School Counselors
1. **Create access codes** for students
2. **Monitor flagged conversations** through admin dashboard
3. **View usage analytics** and patterns
4. **Follow up on crisis interventions**

### For System Administrators
1. **Manage user accounts** and access codes
2. **Review safety logs** and flagged content
3. **Configure system parameters** and model settings
4. **Monitor system health** and performance

## 🛡️ Safety Features

### Crisis Detection
- **Keyword matching** for suicide, self-harm, abuse indicators
- **Contextual analysis** using LLM for nuanced detection
- **Immediate intervention** with crisis resources
- **Logging and flagging** for human review

### Content Moderation
- **OpenAI Moderation API** for harmful content detection
- **Multi-level filtering** with confidence scores
- **Automated responses** for policy violations
- **Human oversight** through admin dashboard

### Emergency Resources
- **24/7 Helplines** prominently displayed
- **Crisis chat services** (Outlive Chat integration)
- **Local emergency numbers** (India-specific)
- **Professional referral** encouragement

## 📊 Database Schema

### Core Tables
- **`user_accounts`** - User registration and activity
- **`access_codes`** - Authentication and access control
- **`chat_messages`** - Conversation history with safety flags
- **`feelings_tracking`** - Daily mood ratings
- **`flagged_chats`** - Crisis interventions and safety logs
- **`admin_users`** - Administrative access

### Key Relationships
- Users linked to access codes and schools
- Chat messages linked to users with safety annotations
- Daily feelings unique per user
- Comprehensive audit trail for all interactions

## 🔄 Deployment

### Development
```bash
python pwa_app.py
```

### Production (with Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5002 pwa_app:app
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5002
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5002", "pwa_app:app"]
```

### Environment Setup for Production
- Set up SSL certificates for HTTPS
- Configure reverse proxy (nginx recommended)
- Set up monitoring and logging
- Configure backup for SQLite database
- Consider PostgreSQL for scaling

## 🧪 Testing

### Manual Testing Checklist
- [ ] User registration with access code
- [ ] Daily feelings thermometer popup
- [ ] Chat functionality with AI responses
- [ ] Crisis detection and intervention
- [ ] Admin dashboard access
- [ ] PWA installation on mobile
- [ ] Offline functionality
- [ ] Session persistence

### Database Testing
```bash
# Test database connectivity
curl http://localhost:5002/test-db

# Test feelings API
curl -X POST http://localhost:5002/api/feelings/check \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Make changes** with proper testing
4. **Update documentation** as needed
5. **Submit pull request** with detailed description

## 📝 Important Notes

### Legal & Ethical Considerations
- **Non-clinical tool**: Not a replacement for professional mental health services
- **Data privacy**: Ensure compliance with local privacy laws
- **Crisis protocols**: Have procedures for urgent mental health situations
- **Supervision**: Trained professionals should monitor flagged conversations

### Technical Considerations
- **Rate limiting**: Prevents abuse and ensures fair usage
- **Database scaling**: Consider PostgreSQL for large deployments
- **Monitoring**: Implement logging and alerting for production
- **Backup**: Regular database backups essential for data integrity

### Customization
- **System prompt**: Modify `system_prompt.txt` for different contexts
- **Crisis resources**: Update helpline numbers for your region
- **UI themes**: Customize colors and branding in templates
- **Language support**: Add multi-language capabilities as needed

## 📞 Support Resources

### Crisis Helplines (India)
- **AASRA**: 022 2754 6669
- **Kiran National Helpline**: 1800-599-0019
- **Tele Manas**: 1800-891-4416
- **Emergency Services**: 112

### Technical Support
- Check logs in console for debugging
- Database issues: Verify permissions and file access
- API errors: Validate OpenAI API key and quotas
- PWA issues: Test in incognito/private browsing mode

## 📄 License

This project is developed for educational and mental health support purposes. Please ensure compliance with healthcare regulations and privacy laws in your jurisdiction before production deployment.

---

**⚠️ Disclaimer**: MindMitra is designed to provide supportive conversations and crisis resource information. It is not a substitute for professional mental health treatment, diagnosis, or intervention. In case of mental health emergencies, please contact local emergency services or mental health professionals immediately.