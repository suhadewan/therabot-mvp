# Deployment Guide - Therabot MVP

## 🚀 Quick Deploy to Render.com (Recommended)

**Total Cost: $7/month** | **Capacity: 100+ concurrent users**

### Prerequisites
- GitHub account
- Render.com account (free to create)
- OpenAI API key

---

## Step 1: Push to GitHub

```bash
# If not already a git repo
git init
git add .
git commit -m "Ready for production deployment"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/therabot-mvp.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Render

### Option A: Using render.yaml (Easiest - One-Click Deploy)

1. Go to https://render.com and sign up/login
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create:
   - Web Service (app) - $7/month
   - PostgreSQL Database (free tier)
5. **Add Environment Variables** in the Render dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - All other variables are auto-configured!
6. Click **"Apply"** - Deploy starts automatically!

### Option B: Manual Setup

**2.1 Create PostgreSQL Database:**
- Dashboard → New → PostgreSQL
- Name: `mindmitra-db`
- Database Name: `therabot_prod`
- User: `therabot_user`
- Region: Singapore (or closest to your users)
- Plan: **Free**
- Click "Create Database"
- Copy the **External Database URL**

**2.2 Create Web Service:**
- Dashboard → New → Web Service
- Connect GitHub repo: `therabot-mvp`
- Settings:
  - **Name**: `mindmitra-pwa`
  - **Region**: Singapore (same as database)
  - **Branch**: main
  - **Root Directory**: leave blank
  - **Environment**: Python 3
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 pwa_app:app`
  - **Plan**: Starter ($7/month)

**2.3 Add Environment Variables:**
```
OPENAI_API_KEY = your_openai_api_key_here
DATABASE_TYPE = postgresql
DATABASE_URL = your_render_postgres_url_from_step_2.1
ENVIRONMENT = production
SECRET_KEY = generate_random_50_char_string
LOG_LEVEL = INFO
PYTHON_VERSION = 3.11.0
```

---

## Step 3: Verify Deployment

1. **Check Build Logs** - Should show "Build successful"
2. **Check Service Status** - Should be "Live"
3. **Test Your App**:
   - Visit: `https://mindmitra-pwa.onrender.com` (or your custom domain)
   - Test login with access code
   - Send a test message
   - Check admin portal

4. **Check Database**:
   - Render Dashboard → mindmitra-db → Connect
   - Use provided connection string to verify tables exist

---

## Step 4: Production Checklist

### Security
- ✅ Change `APP_TIMEZONE` in pwa_app.py to `'Asia/Kolkata'` for production
- ✅ Set strong `SECRET_KEY` (50+ random characters)
- ✅ Verify HTTPS is enabled (Render does this automatically)
- ✅ Review admin credentials in database

### Monitoring
- ✅ Set up Sentry error tracking (already configured)
- ✅ Monitor Render logs: Dashboard → Logs
- ✅ Check database metrics: Dashboard → mindmitra-db → Metrics

### Performance
- ✅ Current config: 4 workers (handles 100+ users)
- ✅ Database: Free tier (10,000 rows, 1GB storage - sufficient for 100 users)
- ✅ Background moderation reduces response time

### Backup
- ✅ Enable daily backups in Render: Dashboard → mindmitra-db → Backups

---

## Scaling Options

### For 200-500 Users:
- Upgrade web service to **Standard ($25/month)**
- Upgrade database to **Starter ($7/month)**
- Total: **$32/month**

### For 500-1000 Users:
- Upgrade web service to **Pro ($85/month)**
- Upgrade database to **Standard ($20/month)**
- Total: **$105/month**

---

## Alternative Platforms

### Railway.app
- Similar to Render
- $5/month for app + database
- Deploy: https://railway.app/new

### Heroku
- More expensive but established
- $7/month (app) + $9/month (database) = $16/month
- Deploy: `heroku create && git push heroku main`

### DigitalOcean App Platform
- $12/month for app + database
- More control, good scaling
- Deploy: https://cloud.digitalocean.com/apps

---

## Troubleshooting

### Build Fails
- Check Python version: Should be 3.11
- Verify all dependencies in requirements.txt
- Check build logs for specific errors

### App Crashes
- Check logs: `DATABASE_URL` connection string
- Verify OpenAI API key is valid
- Check gunicorn workers: Reduce to 2 if memory issues

### Database Connection Issues
- Verify `DATABASE_URL` format: `postgresql://user:password@host:port/database`
- Check database is in same region as web service
- Test connection using provided psql command

### Slow Response Times
- Check OpenAI API latency
- Monitor Render metrics for CPU/memory usage
- Consider upgrading to Standard plan

---

## Post-Deployment

### Custom Domain (Optional)
1. Render Dashboard → mindmitra-pwa → Settings → Custom Domains
2. Add your domain (e.g., `chat.yourdomain.com`)
3. Update DNS records as instructed
4. SSL certificate auto-generated

### Monitoring & Alerts
1. Set up Sentry alerts for errors
2. Enable Render email notifications
3. Monitor OpenAI API usage/costs

### Regular Maintenance
- Review logs weekly
- Check database size monthly
- Update dependencies quarterly
- Backup database weekly (manual download)

---

## Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Status Page**: https://status.render.com

---

## Cost Summary (First Month)

| Item | Cost |
|------|------|
| Web Service (Starter) | $7 |
| PostgreSQL (Free) | $0 |
| OpenAI API (est. 100 users) | ~$20-50 |
| **Total** | **~$27-57/month** |

**Note**: OpenAI costs vary based on usage. Monitor at https://platform.openai.com/usage
