# Production Readiness Guide - MindMitra Pilot

## Pilot Requirements
- **Users**: 100 concurrent (max)
- **Messages**: 200 per hour per user (clarify: 200 total or per user?)
- **Duration**: 1 month
- **Critical**: Mental health support - needs 99.9% uptime

## Executive Summary

**Estimated Monthly Cost: $95 - $145**

Major costs:
- OpenAI API: $60-100 (60-70% of cost)
- Hosting: $20-30
- Database: $5-12
- Monitoring: $5-12

---

## 🚨 Critical Issues to Fix First

### 1. Database Migration (URGENT)
**Current**: SQLite file in repository
**Problem**: 
- SQLite doesn't support concurrent writes well (100 users = problems)
- File-based = data loss risk on crashes
- No backups
- Not scalable

**Solution**: Migrate to PostgreSQL

### 2. Rate Limiting (REQUIRED)
**Current**: 200 messages per hour per user
**Problem**: Each message costs ~$0.006-0.012 in OpenAI costs
**Risk**: One user sending 200 messages/hour = $1.20-2.40/hour = $864/month for ONE user!

### 3. No Monitoring (DANGEROUS)
**Problem**: If bot crashes, students in crisis can't get help
**Solution**: Add error tracking and alerts

---

## Production Infrastructure

### Option A: All Render (Simplest)
```
✅ Pros: Easy setup, one platform
❌ Cons: More expensive, less control
Cost: ~$120/month
```

### Option B: Render + External DB (Recommended)
```
✅ Pros: Better performance, cheaper database
❌ Cons: Two platforms to manage
Cost: ~$95/month
```

### Option C: Railway/Fly.io (Alternative)
```
✅ Pros: Generous free tier, good pricing
❌ Cons: Learning curve
Cost: ~$70/month
```

---

## Detailed Cost Breakdown

### 1. OpenAI API Costs (Biggest Expense)

**Your Current Setup:**
- Model: Fine-tuned GPT-4o-mini
- Input: ~$0.30 per 1M tokens
- Output: ~$1.20 per 1M tokens

**Estimated Usage (Conservative):**
```
Assumptions:
- 50 active users per day (average)
- 20 messages per user per day
- 150 tokens per message (input + output)

Daily:
- Messages: 50 users × 20 = 1,000 messages
- Tokens: 1,000 × 150 = 150,000 tokens

Monthly:
- Messages: 1,000 × 30 = 30,000 messages
- Tokens: 150,000 × 30 = 4,500,000 tokens (~4.5M)

Cost Calculation:
- Input tokens: 2.25M × $0.30/1M = $0.68
- Output tokens: 2.25M × $1.20/1M = $2.70
- Moderation: 30,000 × $0.002 = $0.06

Total: ~$3.44/day × 30 = ~$103/month
```

**Peak Usage (If 100 users active):**
- Could spike to $200-300/month

### 2. Hosting Costs

#### Option A: Render
```
Starter Plan: $7/month
- 512 MB RAM
- Shared CPU
- Good for pilot
- Auto-scaling

Pro Plan: $25/month - Better
- 2 GB RAM
- Dedicated CPU
- Better for 100 users
```

#### Option B: Railway
```
Hobby Plan: $5/month + usage
- Pay per use (CPU/RAM/Network)
- Typically $10-15/month for pilot
- More cost-effective
```

#### Option C: Fly.io
```
Pay as you go
- Estimated $10-20/month
- Good global coverage
```

### 3. Database Costs

#### Option A: Render PostgreSQL
```
Starter: $7/month
- 256 MB RAM
- 1 GB Storage
- Limited connections
- Basic for pilot

Standard: $20/month
- 1 GB RAM
- 10 GB Storage
- Better for production
```

#### Option B: Supabase (Recommended for pilot)
```
Free tier:
- 500 MB database
- 1 GB file storage
- Good for pilot!

Pro: $25/month if needed
```

#### Option C: Neon.tech
```
Free tier:
- 0.5 GB storage
- Serverless PostgreSQL
- Good for pilot

Pro: $19/month
```

### 4. Monitoring & Tools

```
Sentry (Error Tracking):
- Free tier: 5,000 errors/month ✅
- Team: $26/month if needed

Better Uptime (Monitoring):
- Free tier: 3 monitors ✅
- Paid: $10/month

Total: FREE to $12/month
```

---

## Recommended Stack for Pilot

### Budget Option (~$80/month):
```
✅ Hosting: Railway Hobby ($10-15)
✅ Database: Supabase Free → Pro if needed ($0-25)
✅ OpenAI API: ~$60-80
✅ Monitoring: Free tiers
✅ Domain: Cloudflare (Free SSL)

Total: $10-40 hosting + $60-80 OpenAI = $70-120/month
BUT: Can use free tiers = ~$70-80 minimum
```

### Recommended Option (~$120/month):
```
✅ Hosting: Render Pro ($25)
✅ Database: Render Starter ($7)
✅ OpenAI API: ~$100
✅ Monitoring: Free tiers
✅ CDN: Cloudflare (Free)

Total: $32 hosting + $100 OpenAI = ~$132/month
```

---

## Step-by-Step Production Deployment

### Phase 1: Pre-Deployment (Week 1)

#### Step 1: Add Production Dependencies
```bash
cd therabot-mvp

# Add to requirements.txt
echo "psycopg2-binary==2.9.9" >> requirements.txt
echo "sentry-sdk[flask]==1.40.0" >> requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt  # already there
echo "redis==5.0.1" >> requirements.txt  # for rate limiting

pip install -r requirements.txt
```

#### Step 2: Add Environment Variables
Create `production.env`:
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# OpenAI
OPENAI_API_KEY=your_key_here

# Flask
FLASK_ENV=production
SECRET_KEY=generate_a_secure_key_here

# Sentry
SENTRY_DSN=your_sentry_dsn

# Rate Limiting
REDIS_URL=redis://localhost:6379

# Security
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

#### Step 3: Add Rate Limiting (CRITICAL!)
Create `rate_limiter.py`:
```python
from functools import wraps
from flask import request, jsonify
import time
from collections import defaultdict
import threading

# In-memory rate limiter (upgrade to Redis for production)
rate_limit_store = defaultdict(list)
lock = threading.Lock()

def rate_limit(max_requests=20, window_hours=1):
    """
    Rate limiter decorator
    max_requests: Max messages per window
    window_hours: Time window in hours
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = request.json.get('user_id') if request.json else None
            if not user_id:
                return jsonify({"error": "User ID required"}), 400
            
            current_time = time.time()
            window_seconds = window_hours * 3600
            
            with lock:
                # Clean old entries
                rate_limit_store[user_id] = [
                    t for t in rate_limit_store[user_id]
                    if current_time - t < window_seconds
                ]
                
                # Check limit
                if len(rate_limit_store[user_id]) >= max_requests:
                    return jsonify({
                        "error": f"Rate limit exceeded. Maximum {max_requests} messages per {window_hours} hour(s).",
                        "retry_after": window_seconds
                    }), 429
                
                # Add current request
                rate_limit_store[user_id].append(current_time)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator
```

Update `pwa_app.py`:
```python
from rate_limiter import rate_limit

@app.route('/api/chat', methods=['POST'])
@rate_limit(max_requests=20, window_hours=1)  # Add this!
def chat():
    # ... existing code
```

#### Step 4: Add Error Tracking
Update `pwa_app.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Add at top after imports
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,  # 10% of requests
        environment="production"
    )
```

#### Step 5: Migrate to PostgreSQL

Create `migrate_to_postgres.py`:
```python
"""
Migrate SQLite data to PostgreSQL
"""
import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    # Connect to both databases
    sqlite_conn = sqlite3.connect('mental_health_bot.db')
    pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    print("Starting migration...")
    
    # Migrate each table
    tables = [
        'access_codes',
        'user_accounts',
        'chat_messages',
        'feelings_tracking',
        'conversation_summaries',
        'admin_users'
    ]
    
    for table in tables:
        print(f"Migrating {table}...")
        
        # Get data from SQLite
        sqlite_cur.execute(f"SELECT * FROM {table}")
        rows = sqlite_cur.fetchall()
        
        # Get column names
        column_names = [description[0] for description in sqlite_cur.description]
        
        # Insert into PostgreSQL
        for row in rows:
            placeholders = ','.join(['%s'] * len(row))
            columns = ','.join(column_names)
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            try:
                pg_cur.execute(query, row)
            except Exception as e:
                print(f"Error migrating row: {e}")
        
        pg_conn.commit()
        print(f"✅ Migrated {len(rows)} rows from {table}")
    
    sqlite_conn.close()
    pg_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
```

Update `database_config.py`:
```python
import os

def get_database_config():
    """Get database configuration based on environment"""
    
    if os.getenv('DATABASE_URL'):
        # Production: Use PostgreSQL
        return {
            'type': 'postgresql',
            'url': os.getenv('DATABASE_URL')
        }
    else:
        # Development: Use SQLite
        return {
            'type': 'sqlite',
            'path': 'mental_health_bot.db'
        }
```

#### Step 6: Add Health Check Endpoint
Update `pwa_app.py`:
```python
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db = get_database()
        db.database._get_connection().close()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(IST).isoformat(),
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
```

### Phase 2: Database Setup (Week 1)

#### Option 1: Supabase (Recommended for Pilot)

1. **Sign up**: https://supabase.com
2. **Create project**: 
   - Name: mindmitra-pilot
   - Region: Mumbai (closest to India)
   - Plan: Free tier (enough for pilot)
3. **Get connection string**:
   ```
   Settings → Database → Connection string (URI)
   postgres://postgres:[PASSWORD]@[HOST]:5432/postgres
   ```
4. **Run schema**:
   ```bash
   # Connect to Supabase SQL editor
   # Run your database.py init_db() schema
   # Or use migration script
   ```

#### Option 2: Render Database

1. **Create database**: Dashboard → New → PostgreSQL
2. **Choose plan**: Starter ($7/month)
3. **Get connection string**: Copy from dashboard
4. **Connect**: Update DATABASE_URL in environment

### Phase 3: Hosting Setup (Week 1-2)

#### Render Deployment (Recommended)

1. **Create Web Service**:
   ```
   - Name: mindmitra-bot
   - Environment: Python
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn pwa_app:app
   - Plan: Pro ($25/month) - Needed for 100 users
   ```

2. **Environment Variables**:
   ```
   DATABASE_URL=your_postgresql_url
   OPENAI_API_KEY=your_key
   FLASK_ENV=production
   SECRET_KEY=generate_secure_key
   SENTRY_DSN=your_sentry_dsn
   ```

3. **Health Checks**:
   ```
   Path: /health
   Interval: 30 seconds
   ```

4. **Custom Domain** (if needed):
   ```
   - Add CNAME record in Cloudflare
   - Point to: your-app.onrender.com
   ```

### Phase 4: Monitoring Setup (Week 2)

#### 1. Sentry (Error Tracking)
```bash
# Sign up: https://sentry.io
# Create project: Flask
# Copy DSN
# Add to environment variables
```

#### 2. Better Uptime (Uptime Monitoring)
```bash
# Sign up: https://betteruptime.com
# Create monitor:
#   - URL: https://your-app.com/health
#   - Check every: 1 minute
#   - Alert: Email + SMS
```

#### 3. OpenAI Usage Dashboard
```python
# Add to pwa_app.py
import logging

usage_logger = logging.getLogger('openai_usage')
usage_logger.setLevel(logging.INFO)

# Log every API call
def log_openai_usage(user_id, tokens_used, cost):
    usage_logger.info(f"User: {user_id}, Tokens: {tokens_used}, Cost: ${cost:.4f}")
```

### Phase 5: Testing (Week 2-3)

#### Load Testing
```bash
# Install locust
pip install locust

# Create locustfile.py
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(5, 15)
    
    @task
    def send_message(self):
        self.client.post("/api/chat", json={
            "user_id": f"test_user_{self.user_id}",
            "message": "I'm feeling stressed about exams"
        })

# Run test
locust -f locustfile.py --host=https://your-app.com
```

#### Security Audit
- [ ] HTTPS enabled
- [ ] Rate limiting active
- [ ] Input validation working
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CORS configured properly

### Phase 6: Go Live (Week 3-4)

#### Pre-Launch Checklist
- [ ] Database migrated and backed up
- [ ] Environment variables set
- [ ] Rate limiting tested
- [ ] Error tracking configured
- [ ] Health checks working
- [ ] Load testing passed (50-100 concurrent users)
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team trained on monitoring dashboard

#### Launch Day
1. **Final backup** of development data
2. **Deploy** to production
3. **Smoke test** all features
4. **Monitor** logs and errors closely
5. **Have rollback plan** ready

---

## Cost Optimization Tips

### 1. Reduce OpenAI Costs
```python
# In config.py - already set well
MODEL_MAX_TOKENS = 150  # Keep responses short
MODEL_TEMPERATURE = 0.7  # Good balance

# Add caching for common questions
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(question):
    # Cache common greetings, FAQs
    pass
```

### 2. Use Free Tiers Smartly
- ✅ Supabase Free: Good for pilot
- ✅ Sentry Free: 5,000 errors/month
- ✅ Better Uptime Free: 3 monitors
- ✅ Cloudflare Free: CDN + SSL

### 3. Monitor and Alert on Costs
```python
# Add daily cost tracker
import schedule

def check_daily_cost():
    # Query OpenAI usage
    # If cost > threshold, send alert
    pass

schedule.every().day.at("23:00").do(check_daily_cost)
```

---

## Emergency Procedures

### If OpenAI Quota Exceeded
```python
# Add fallback message
OPENAI_ERROR_MESSAGE = """
I'm experiencing high demand right now. 
Please try again in a few minutes, or contact:
- AASRA: 022 2754 6669
- Kiran Helpline: 1800-599-0019
"""
```

### If Database Down
```python
# Implement graceful degradation
try:
    db.save_message(...)
except:
    # Log to file as backup
    with open('emergency_logs.txt', 'a') as f:
        f.write(f"{timestamp}: {message}\n")
```

### If App Crashes
- Render auto-restarts (within 5 minutes)
- Monitoring alerts team
- Users see maintenance message
- Crisis resources still visible on frontend

---

## Monthly Maintenance Tasks

### Week 1:
- [ ] Review error logs in Sentry
- [ ] Check OpenAI usage and costs
- [ ] Review user feedback
- [ ] Database backup verification

### Week 2:
- [ ] Performance review
- [ ] Security updates
- [ ] Dependency updates
- [ ] Cost analysis

### Week 3:
- [ ] User metrics analysis
- [ ] Feature usage stats
- [ ] System health review

### Week 4:
- [ ] Monthly report
- [ ] Plan next month
- [ ] Budget review

---

## Budget Summary (Conservative)

### Minimum Viable Production
```
Hosting (Railway Free → $10):     $0-10/month
Database (Supabase Free):         $0/month
OpenAI API:                       $60-100/month
Monitoring (Free tiers):          $0/month
Domain (optional):                $10/year

Total: $60-110/month
```

### Recommended Production
```
Hosting (Render Pro):             $25/month
Database (Render Starter):        $7/month
OpenAI API:                       $100/month
Monitoring (Free tiers):          $0/month
Buffer (10%):                     $15/month

Total: ~$147/month
```

### If 100 Users Active Daily
```
Higher API usage:                 $190-240/month
Same hosting:                     $32/month
Buffer:                           $25/month

Total: ~$247-297/month
```

---

## Timeline

| Week | Tasks | Status |
|------|-------|--------|
| 1 | Add dependencies, rate limiting, error tracking | □ |
| 1-2 | Database migration, hosting setup | □ |
| 2 | Monitoring setup, initial testing | □ |
| 2-3 | Load testing, security audit | □ |
| 3 | Soft launch with 10 users | □ |
| 3-4 | Full pilot launch | □ |
| 4+ | Monitor and optimize | □ |

---

## Next Steps

1. **Clarify requirement**: 200 messages total or per user?
2. **Choose stack**: Recommend Render + Supabase for simplicity
3. **Budget approval**: Get ₹12,000-15,000/month approved
4. **Start Week 1 tasks**: Add rate limiting and error tracking
5. **Set up accounts**: Render, Supabase, Sentry, Better Uptime

**Ready to start? I can help with each step!**

