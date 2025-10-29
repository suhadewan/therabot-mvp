# Production Cost Summary (USD)

## Quick Overview

| Scenario | Monthly Cost | Notes |
|----------|--------------|-------|
| **Minimum (Budget)** | **$60-80** | Free tiers + basic API usage |
| **Recommended (Pilot)** | **$130-150** | Proper hosting + monitoring |
| **High Usage (100 users)** | **$250-300** | Peak usage scenario |

---

## Detailed Cost Breakdown

### Option 1: Ultra Budget (~$60-80/month)
**Best for**: Testing with 10-25 users

| Service | Plan | Cost |
|---------|------|------|
| Hosting | Railway Free/Hobby | $0-10 |
| Database | Supabase Free | $0 |
| OpenAI API | ~30K messages | $60-80 |
| Monitoring | Free tiers | $0 |
| **TOTAL** | | **$60-80** |

**Pros:**
- Very low cost
- Good for testing
- Free tiers available

**Cons:**
- Limited resources
- May need upgrade quickly
- Less reliable for production

---

### Option 2: Recommended Pilot (~$130-150/month)
**Best for**: 50 active users/day, 1-month pilot

| Service | Plan | Cost |
|---------|------|------|
| Hosting | Render Standard | $25 |
| Database | Render Starter or Supabase Pro | $7-25 |
| OpenAI API | ~30K messages | $100 |
| Monitoring | Sentry + Better Uptime (Free) | $0 |
| Buffer (10%) | Overages/spikes | $15 |
| **TOTAL** | | **$147** |

**Pros:**
- ✅ Reliable for production
- ✅ Good performance
- ✅ Auto-scaling
- ✅ 24/7 support available

**Cons:**
- Higher cost
- May be overprovisioned for small pilots

**This is our recommendation!**

---

### Option 3: High Usage (~$250-300/month)
**Best for**: 100 active users/day, extended pilot

| Service | Plan | Cost |
|---------|------|------|
| Hosting | Render Standard/Pro | $25-50 |
| Database | Supabase Pro | $25 |
| OpenAI API | ~60K messages | $200 |
| Monitoring | Paid tiers | $10-20 |
| Buffer | Overages | $25 |
| **TOTAL** | | **$285-320** |

---

## OpenAI API Cost Details

### Cost per Message
```
Average message:
- Input: ~50 tokens ($0.015/1K) = $0.00075
- Output: ~100 tokens ($0.06/1K) = $0.006
- Moderation: $0.002

Total per message: ~$0.009 ($0.01 rounded)
```

### Monthly Projections

| Users/Day | Messages/Day | Messages/Month | OpenAI Cost |
|-----------|--------------|----------------|-------------|
| 25 | 500 | 15,000 | $50-60 |
| 50 | 1,000 | 30,000 | $100 |
| 75 | 1,500 | 45,000 | $150 |
| 100 | 2,000 | 60,000 | $200 |

**Assumptions:**
- Average 20 messages per user per day
- 150 tokens per message (input + output)
- 30-day month

---

## Hosting Options Comparison

### Render (Recommended)
```
Starter: $7/month
- 512 MB RAM
- Shared CPU
- Basic but works

Standard: $25/month ⭐ Recommended
- 2 GB RAM  
- 1.0 CPU
- Better for 100 users

Pro: $50/month
- 4 GB RAM
- 2.0 CPU
- For heavy load
```

### Railway
```
Hobby: $5 base + usage
- Pay per resource
- Typically $10-15/month
- Good for variable load
```

### Fly.io
```
Pay as you go
- $10-20/month typical
- Good global reach
- More complex setup
```

---

## Database Options Comparison

### Supabase (Recommended for Pilot)
```
Free Tier: $0 ⭐ Start here
- 500 MB storage
- Unlimited API requests
- Good for pilot!

Pro: $25/month
- 8 GB storage
- Better performance
- Upgrade when needed
```

### Render PostgreSQL
```
Starter: $7/month
- 256 MB RAM
- 1 GB storage
- Basic

Standard: $20/month  
- 1 GB RAM
- 10 GB storage
```

### Neon.tech
```
Free: $0
- 0.5 GB storage
- Serverless
- Good option

Pro: $19/month
```

---

## Cost Optimization Tips

### 1. Reduce OpenAI Costs (Save $20-40/month)

**Current Settings (Already Good):**
- Max tokens: 150 (keep short)
- Temperature: 0.7 (balanced)
- Model: Fine-tuned GPT-4o-mini (cheapest)

**Additional Savings:**
```python
# Cache common questions
common_responses = {
    "hi": "Hi! How are you feeling today?",
    "hello": "Hello! I'm here to listen. What's on your mind?",
    # ... more common greetings
}

# Save ~10-15% on OpenAI costs
```

**Set Budget Alerts:**
- Hard limit: $150/month
- Email alert: $100/month
- Daily check: $5/day threshold

### 2. Use Free Tiers (Save $30-50/month)

✅ **Free Services:**
- Sentry: 5,000 errors/month
- Better Uptime: 3 monitors
- Cloudflare: CDN + SSL
- Supabase: 500MB database (for pilot)

### 3. Rate Limiting (Prevent Abuse)

**CRITICAL:** Without rate limiting, one user could cost $100-200/month!

```python
# Already implemented in rate_limiter.py
@rate_limit(max_requests=20, window_hours=1)
```

This prevents:
- API abuse
- Runaway costs
- System overload

**Savings:** Prevent $50-200+/month in abuse

---

## Monthly Budget Planning

### Conservative (Recommended)
```
Base costs:           $132/month
Buffer (10%):         $15/month
Emergency fund:       $50/month

Total budget:         $197/month
```

### Aggressive (Minimum)
```
Base costs:           $70/month
Buffer (10%):         $8/month

Total budget:         $78/month
```

---

## Cost by Phase

### Week 1-2: Setup & Testing
```
Hosting (free tier):         $0-10
Database (free tier):        $0
OpenAI (testing):            $10-20
Total:                       $10-30
```

### Week 3-4: Soft Launch (10-25 users)
```
Hosting:                     $7-25
Database:                    $0-7
OpenAI:                      $40-60
Total:                       $47-92
```

### Month 2: Full Pilot (50-100 users)
```
Hosting:                     $25
Database:                    $7-25
OpenAI:                      $100-200
Monitoring:                  $0-10
Total:                       $132-260
```

---

## ROI Calculation

### Cost per User (50 active users/day)
```
Monthly cost:               $147
Active users:               50
Cost per user:              $2.94/month
Cost per user per day:      $0.10/day
```

### Cost per Message
```
Monthly cost:               $147
Messages sent:              30,000
Cost per message:           $0.0049 (~$0.005)
```

### Compared to Alternatives
- **Human counselor**: $50-100/hour
- **Therapy app**: $40-60/month
- **MindMitra**: $0.10/day per user

---

## Warning Signs & Limits

### Set Alerts For:

**OpenAI Usage:**
- [ ] $3/day = On track
- [ ] $5/day = Warning
- [ ] $10/day = Alert team

**Error Rate:**
- [ ] <1% = Good
- [ ] 1-5% = Investigate
- [ ] >5% = Emergency

**Response Time:**
- [ ] <3s = Good
- [ ] 3-5s = Acceptable
- [ ] >5s = Slow, investigate

---

## Emergency Budget

If costs spike unexpectedly:

### Immediate Actions:
1. **Check OpenAI dashboard** - Unusual spike?
2. **Review rate limiting** - Someone abusing?
3. **Check error logs** - Retry loops?
4. **Reduce limits temporarily** - 20 → 10 messages/hour

### Cost Reduction Tactics:
```python
# Temporarily reduce limits
MODEL_MAX_TOKENS = 100  # from 150
RATE_LIMIT_REQUESTS = 10  # from 20

# Can reduce costs by 30-40%
```

---

## Payment & Billing

### Setup Billing Alerts

**OpenAI:**
1. Dashboard → Billing
2. Set usage limit: $150/month
3. Email alerts: $25, $50, $100

**Render:**
1. Billing → Usage alerts
2. Email at: $30, $50

**Credit Card:**
- Use business card
- Set $200/month limit
- Enable alerts

---

## Questions to Clarify

Before finalizing budget, clarify:

1. **"200 messages per hour per user"**
   - Is this really PER USER? 
   - Or 200 total messages per hour for all users?
   - HUGE cost difference!

2. **Expected usage pattern:**
   - How many users/day?
   - Average messages/user?
   - Peak times?

3. **Budget approval:**
   - Minimum: $80/month?
   - Recommended: $150/month?
   - Maximum: $300/month?

---

## Final Recommendation

### For 1-Month Pilot:

**Go with Option 2: $130-150/month**

**Setup:**
- Render Standard ($25)
- Supabase Free → Pro if needed ($0-25)
- OpenAI with $150 hard limit
- Free monitoring tools
- 10% buffer

**Why:**
- ✅ Reliable enough for students
- ✅ Not over-engineered
- ✅ Can scale if needed
- ✅ Affordable for pilot
- ✅ Professional quality

**Start Date:** As soon as database migrated
**Duration:** 1 month pilot
**Review:** Weekly cost checks

---

## Need Help?

**Cost Questions:**
- Review OpenAI usage daily
- Check hosting metrics weekly
- Adjust rate limits as needed

**Technical Questions:**
- See PRODUCTION_READINESS.md
- See QUICK_START_PRODUCTION.md

**Quick Math:**
- 1 message ≈ $0.01
- 1 user/day ≈ $0.20 (20 messages)
- 50 users/day ≈ $10/day = $300/month

**Budget approved? Let's deploy!** 🚀


