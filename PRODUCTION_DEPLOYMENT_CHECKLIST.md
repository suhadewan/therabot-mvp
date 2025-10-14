# Production Deployment Checklist

## Pre-Deployment Testing

### ✅ Database Setup
- [x] PostgreSQL connection working with Supabase
- [x] All tables created and indexed
- [x] Connection pooling configured for Supabase transaction mode
- [x] Database timeout and SSL settings optimized
- [ ] Backup strategy in place (Supabase handles this automatically)
- [ ] Test database failover/recovery

### ✅ Code Quality & Security
- [x] Rate limiting enabled (30 messages/hour per user)
- [x] Crisis detection keywords active
- [x] Content moderation enabled (OpenAI moderation API)
- [x] Guardrails enforced (50 words, follow-up questions)
- [x] Session security configured (HTTPS cookies, HTTPOnly)
- [x] Environment variables secured (never commit .env)
- [x] Sensitive data in database (not in logs)
- [x] SQL injection prevented (parameterized queries)
- [ ] HTTPS enforced (configure on hosting platform)

### ⚠️ Testing Required
- [ ] **End-to-end user flow test**
  - [ ] Login with access code
  - [ ] Consent form acceptance
  - [ ] Send normal chat messages
  - [ ] Test crisis keyword detection
  - [ ] Test rate limiting (send 31 messages)
  - [ ] Check daily feeling thermometer
  - [ ] Test logout and re-login
- [ ] **Admin portal test**
  - [ ] Admin login works
  - [ ] View flagged chats
  - [ ] View all chats
  - [ ] View statistics
  - [ ] Create/edit access codes
  - [ ] View feelings data
- [ ] **Load testing**
  - [ ] Test with 10 concurrent users
  - [ ] Check database connection under load
  - [ ] Monitor response times
  - [ ] Check memory usage

### 📊 Monitoring & Error Tracking
- [x] Sentry integration ready (install when needed)
- [ ] Set up Sentry project and add DSN to .env
- [ ] Configure alerting thresholds
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Monitor OpenAI API usage and costs
- [ ] Set up log aggregation (optional)

### 🔐 Environment Variables (Production)
Review and set these on your hosting platform:

```bash
# Required
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
OPENAI_API_KEY=sk-proj-...
SECRET_KEY=<generate-new-secure-key>
ENVIRONMENT=production

# Optional but recommended
SENTRY_DSN=https://...@sentry.io/...
LOG_LEVEL=INFO
THERABOT_RATE_LIMIT_REQUESTS=30
THERABOT_RATE_LIMIT_WINDOW_HOURS=1
```

### 📦 Dependencies
- [x] requirements.txt up to date
- [ ] Install on production server: `pip install -r requirements.txt`
- [ ] Verify psycopg2-binary installed for PostgreSQL
- [ ] Verify sentry-sdk[flask] installed if using Sentry

### 🚀 Deployment Steps

#### Option 1: Deploy to Render.com (Recommended)
1. Push code to GitHub
2. Create new Web Service on Render
3. Connect GitHub repository
4. Set Build Command: `pip install -r requirements.txt`
5. Set Start Command: `gunicorn pwa_app:app --workers 2 --threads 2 --timeout 120`
6. Add environment variables from `.env`
7. Set health check path: `/health`
8. Deploy!

#### Option 2: Deploy to Heroku
```bash
heroku create mindmitra-pilot
heroku config:set DATABASE_TYPE=postgresql
heroku config:set DATABASE_URL=<your-supabase-url>
heroku config:set OPENAI_API_KEY=<your-key>
heroku config:set SECRET_KEY=<your-secret>
heroku config:set ENVIRONMENT=production
git push heroku main
```

#### Option 3: Deploy to Railway
1. Connect GitHub repository
2. Add PostgreSQL database (or use Supabase URL)
3. Set environment variables
4. Deploy automatically on push

### 📈 Post-Deployment Verification

#### Immediately After Deployment
- [ ] Check `/health` endpoint returns healthy status
- [ ] Verify database connection in health check
- [ ] Test login with a pilot access code
- [ ] Send test message and verify response
- [ ] Check admin portal is accessible
- [ ] Verify HTTPS is working
- [ ] Test on mobile device (PWA features)

#### Within 24 Hours
- [ ] Monitor error rates in Sentry
- [ ] Check database query performance
- [ ] Review flagged conversations
- [ ] Monitor OpenAI API costs
- [ ] Verify rate limiting is working
- [ ] Check no memory leaks (restart if needed)

#### Weekly During Pilot
- [ ] Review all flagged chats
- [ ] Analyze usage patterns
- [ ] Check user feedback
- [ ] Monitor response quality
- [ ] Review costs vs budget
- [ ] Database performance optimization

### 🚨 Crisis Protocol
**If a high-risk message is detected:**
1. System automatically logs to `flagged_chats` table
2. Admin receives notification (set up email alerts)
3. Response protocol (detailed in your research protocol)
4. Follow institutional guidelines for crisis intervention

### 📊 Success Metrics (Track These)
- Daily active users (target: 70-80 of 100)
- Messages per user per day (average)
- Crisis detections per week
- Response satisfaction (post-pilot survey)
- Technical uptime (target: >99%)
- Average response time (target: <2 seconds)

### 🔧 Troubleshooting

#### Database Connection Issues
```bash
# Test connection
python3 -c "from database import init_database; db = init_database('postgresql', connection_string='<url>'); print('OK')"

# Check Supabase status
curl https://status.supabase.com/api/v2/status.json
```

#### Rate Limiting Not Working
- Check logs for "Rate limit:" messages
- Verify decorator is on `/api/chat` endpoint
- Clear rate limit: `reset_rate_limit(user_id)`

#### High OpenAI Costs
- Reduce `MODEL_MAX_TOKENS` in config
- Tighten `GUARDRAILS_MAX_WORDS`
- Check for abuse/bot traffic
- Implement stricter rate limits

### 📝 Access Code Management

#### Creating Access Codes for Pilot
```bash
# Generate 100 unique access codes
# Already done via admin portal

# Track distribution:
# - School A: Codes 1-50
# - School B: Codes 51-100
```

#### Deactivating After Pilot
```bash
# Via admin portal or database:
UPDATE access_codes SET is_active = FALSE WHERE school_id = 'pilot';
```

### 🎓 User Onboarding (For Pilot Participants)

**What to provide to each participant:**
1. Unique access code (write on paper, don't text)
2. App URL (or QR code)
3. Quick start guide:
   - Open URL in mobile browser
   - Enter access code
   - Read and accept consent form
   - Start chatting!
4. Crisis hotline card (backup support)

### 📱 Technical Support During Pilot

**Common Issues:**
- "Access code doesn't work" → Check if deactivated after consent decline
- "Can't send messages" → Rate limit reached (explain 30/hour limit)
- "App is slow" → Check internet connection, server health
- "Lost my conversation" → Explained: Fresh start each day by design

### 🔒 Data Privacy & Compliance

- [ ] Consent form legally reviewed
- [ ] Data retention policy documented (30 days? End of pilot?)
- [ ] Data export procedure for participants (GDPR-style request)
- [ ] Data deletion procedure after pilot
- [ ] IRB approval obtained (if applicable)
- [ ] Parental consent for minors (if required)

### 🎯 Pilot Success Criteria

**Technical:**
- 99% uptime
- <5% error rate
- Response time <3 seconds
- Zero data breaches

**Research:**
- 70% completion rate
- Positive user feedback (>3.5/5)
- Effective crisis detection (review flagged chats)
- Evidence of sustained engagement

---

## Quick Commands

### Start Local Server (Testing)
```bash
python3 pwa_app.py
```

### Start Production Server (on deployment)
```bash
gunicorn pwa_app:app --workers 2 --threads 2 --bind 0.0.0.0:$PORT
```

### Check Database Stats
```bash
curl https://your-app-url.com/admin/stats
```

### Test Health Endpoint
```bash
curl https://your-app-url.com/health
```

### View Logs (Render)
```bash
# Via Render dashboard → Logs tab
```

---

## Emergency Contacts

- **Technical Issues:** [Your email]
- **Crisis Protocol:** [Research supervisor]
- **Supabase Support:** support@supabase.com
- **OpenAI Support:** https://help.openai.com
- **Render Support:** https://render.com/support

---

## Final Pre-Launch Checklist

The night before launch:
- [ ] Backup production database
- [ ] Test all critical paths one more time
- [ ] Verify crisis hotline numbers are correct and current
- [ ] Team briefed on crisis protocol
- [ ] Monitoring alerts configured
- [ ] On-call schedule set (who responds to issues)
- [ ] Rollback plan documented
- [ ] Participant support materials printed
- [ ] Access codes distributed

**🎉 When all checked: You're ready to launch!**
