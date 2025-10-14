# Quick Start: Deploy to Production in 1 Hour

## TL;DR Cost: $100-145/month

**Main cost**: OpenAI API (~$100/month for 50 active users/day)

---

## Step 1: Create Accounts (15 mins)

### Required Accounts:
1. **Render** (Hosting): https://render.com
   - Sign up with GitHub
   - Free to start

2. **Supabase** (Database): https://supabase.com
   - Sign up with GitHub
   - Free tier available

3. **Sentry** (Error Tracking): https://sentry.io
   - Sign up with GitHub
   - Free tier: 5,000 errors/month

4. **Better Uptime** (Monitoring): https://betteruptime.com
   - Sign up with email
   - Free tier: 3 monitors

---

## Step 2: Setup Database (15 mins)

### Supabase Setup:
1. Go to https://supabase.com/dashboard
2. Click "New Project"
   - Name: `mindmitra-pilot`
   - Database Password: (save this!)
   - Region: **Mumbai (ap-south-1)** ← Important for India
   - Plan: Free tier ✅
3. Wait 2 minutes for project creation
4. Go to Settings → Database → Connection string
5. Copy the **URI** (starts with `postgresql://`)
6. **Save this** - you'll need it!

### Initialize Database:
```bash
# In your local terminal
cd therabot-mvp

# Install dependencies
pip install -r requirements.txt

# Set temporary database URL
export DATABASE_URL="your_supabase_postgresql_url"

# Initialize database schema
python -c "from database import init_database; db = init_database('postgresql', connection_string='$DATABASE_URL'); db.init_db()"
```

---

## Step 3: Setup Hosting (20 mins)

### Render Setup:
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   ```
   Name: mindmitra-bot
   Region: Singapore (closest to India)
   Branch: main (or master)
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --bind 0.0.0.0:$PORT pwa_app:app
   Instance Type: Starter ($7) or Standard ($25 for better performance)
   ```
5. Click "Advanced" → Add Environment Variables:
   ```
   DATABASE_URL=your_supabase_postgresql_url
   OPENAI_API_KEY=your_openai_key
   FLASK_ENV=production
   SECRET_KEY=generate_random_string_here
   SENTRY_DSN=will_add_later
   ```
6. Click "Create Web Service"
7. Wait ~5 minutes for first deploy

---

## Step 4: Add Rate Limiting (5 mins)

### Update pwa_app.py:
```python
# Add at top of pwa_app.py, after imports
from rate_limiter import rate_limit

# Find the @app.route('/api/chat', methods=['POST']) line
# Add @rate_limit decorator above it:

@app.route('/api/chat', methods=['POST'])
@rate_limit(max_requests=20, window_hours=1)  # ← Add this line
def chat():
    """Handle chat messages"""
    # ... rest of your code
```

**Commit and push:**
```bash
git add rate_limiter.py pwa_app.py requirements.txt
git commit -m "Add rate limiting for production"
git push
```

Render will auto-deploy in ~3 minutes.

---

## Step 5: Setup Error Tracking (5 mins)

### Sentry Setup:
1. Go to https://sentry.io/projects/new/
2. Choose "Flask" platform
3. Name: `mindmitra-bot`
4. Copy the **DSN** (looks like: `https://...@sentry.io/...`)
5. Add to Render:
   - Go to your Render service
   - Environment → Add `SENTRY_DSN=your_dsn_here`
   - Save Changes (triggers redeploy)

### Update pwa_app.py:
```python
# Add at top of pwa_app.py, after imports
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Add after app = Flask(__name__)
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment="production"
    )
```

---

## Step 6: Setup Monitoring (5 mins)

### Better Uptime:
1. Go to https://betteruptime.com/monitors
2. Click "Create Monitor"
   ```
   Monitor Type: HTTP(s)
   URL: https://your-app.onrender.com/health
   Check Frequency: Every 3 minutes
   Expected Status Code: 200
   Alert: Your email
   ```
3. Save

### Add Health Endpoint:
```python
# Add to pwa_app.py
from datetime import datetime

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        db.database._get_connection().close()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(IST).isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
```

---

## Step 7: Test Everything (10 mins)

### 1. Test Basic Chat:
```bash
curl -X POST https://your-app.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "message": "I am feeling stressed"}'
```

Should return a supportive message ✅

### 2. Test Rate Limiting:
Send 21 messages quickly - 21st should be blocked ✅

### 3. Test Health Check:
```bash
curl https://your-app.onrender.com/health
```

Should return `{"status": "healthy"}` ✅

### 4. Check Sentry:
Trigger an error intentionally - should appear in Sentry dashboard ✅

### 5. Check Monitoring:
Better Uptime should show "Up" status ✅

---

## Done! 🎉

Your bot is now in production!

### Your URLs:
- **Bot**: https://your-app.onrender.com
- **Health**: https://your-app.onrender.com/health
- **Admin**: https://your-app.onrender.com/admin

### Dashboards:
- **Hosting**: https://dashboard.render.com
- **Database**: https://app.supabase.com
- **Errors**: https://sentry.io
- **Uptime**: https://betteruptime.com

---

## Daily Monitoring

### Check These Daily (5 mins):
1. **Sentry**: Any new errors?
2. **Better Uptime**: All monitors green?
3. **Render**: App healthy?
4. **OpenAI**: Usage within budget?
   - Go to: https://platform.openai.com/usage

### Weekly Tasks:
- Review error patterns
- Check response times
- Analyze user feedback
- Review costs

---

## Cost Management

### Monitor OpenAI Costs:
```python
# Add to your local tools
import openai
client = openai.OpenAI()

# Check usage
usage = client.usage.retrieve()
print(f"Current month usage: ${usage.total_cost}")
```

### Set Budget Alert:
1. Go to OpenAI dashboard
2. Organization → Billing → Usage limits
3. Set hard limit: $150/month
4. Set email alert at: $100/month

---

## Emergency Contacts

Save these for the pilot:

**Technical Issues:**
- Render Status: https://status.render.com
- Supabase Status: https://status.supabase.com
- OpenAI Status: https://status.openai.com

**If Bot Goes Down:**
1. Check Render dashboard - is app running?
2. Check Sentry - any errors?
3. Check Better Uptime - what failed?
4. Check OpenAI - quota exceeded?

**Quick Fixes:**
- App crash: Render auto-restarts in ~5 mins
- Database issue: Check Supabase dashboard
- OpenAI quota: Upgrade plan or wait for reset
- Rate limit hit: Reset in rate_limiter.py

---

## Scaling Up

### If You Need More Capacity:

**More Users (50 → 100):**
- Upgrade Render: Starter → Standard ($7 → $25)
- Upgrade Supabase: Free → Pro ($25/month)
- Monitor OpenAI costs (will ~2x)

**More Messages:**
- Implement caching for common questions
- Add Redis for better rate limiting
- Use CDN for static assets

**Better Performance:**
- Add Redis caching
- Implement response streaming
- Use load balancer

---

## Troubleshooting

### "Rate limit exceeded" errors:
```python
# Adjust in pwa_app.py
@rate_limit(max_requests=30, window_hours=1)  # Increase to 30
```

### Slow responses (>5 seconds):
1. Check Render CPU usage
2. Upgrade to Standard plan
3. Check OpenAI API latency

### Database connection errors:
1. Check Supabase dashboard
2. Verify DATABASE_URL is correct
3. Check connection limits (Supabase free: 60 connections)

### High OpenAI costs:
1. Reduce MODEL_MAX_TOKENS (150 → 100)
2. Implement response caching
3. Add stricter rate limiting (20 → 15 messages/hour)

---

## Success Metrics for Pilot

Track these for 1 month:

### Technical:
- [ ] Uptime: >99.5% (max 3.6 hours downtime/month)
- [ ] Response time: <4 seconds average
- [ ] Error rate: <1% of requests
- [ ] Rate limit hits: <5% of users

### Business:
- [ ] Active users: Track daily/weekly
- [ ] Messages per user: Average engagement
- [ ] Cost per user: OpenAI cost / active users
- [ ] Student feedback: Collect through surveys

### Safety:
- [ ] Crisis detections: How many? Appropriate?
- [ ] False positives: Students complaining about flags?
- [ ] Response quality: Review sample conversations

---

## Next Steps After Pilot

### If Successful:
1. Get permanent hosting (upgrade plans)
2. Custom domain (mindmitra.in?)
3. Add more features:
   - Progress tracking
   - Goal setting
   - Weekly summaries
4. Scale to more schools

### If Issues Found:
1. Analyze what went wrong
2. Adjust model/prompts
3. Improve crisis detection
4. Better rate limiting

---

## Quick Reference

| Task | Link | Cost |
|------|------|------|
| View Logs | Render Dashboard → Logs | Free |
| Check Errors | Sentry Dashboard | Free tier |
| Monitor Uptime | Better Uptime Dashboard | Free tier |
| Check Costs | OpenAI Usage Dashboard | Pay per use |
| Database Admin | Supabase Dashboard | Free tier |

**Need help? Check PRODUCTION_READINESS.md for detailed docs!**

