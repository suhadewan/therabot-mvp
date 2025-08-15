# WhatsApp Bot Setup Guide

## Step-by-Step Instructions

### 1. Set Up Twilio Account

1. **Go to [Twilio Console](https://console.twilio.com/)**
2. **Sign up for free account** (get $15-20 free credit)
3. **Navigate to WhatsApp Sandbox** in the console
4. **Note your Account SID and Auth Token** from the console dashboard

### 2. Configure WhatsApp Sandbox

1. **In Twilio Console, go to Messaging → Try it out → Send a WhatsApp message**
2. **Join the sandbox** by sending the provided code to the Twilio WhatsApp number
3. **Note the Twilio WhatsApp number** (usually +14155238886)

### 3. Set Up Environment Variables

1. **Create a `.env` file** in your project root:
```bash
cp env_example.txt .env
```

2. **Edit `.env` file** with your actual values:
```env
TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcdef
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+14155238886
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Test Locally (Optional)

1. **Install ngrok** for local testing:
```bash
# On macOS
brew install ngrok

# Or download from https://ngrok.com/
```

2. **Start your bot**:
```bash
python whatsapp_bot.py
```

3. **In another terminal, start ngrok**:
```bash
ngrok http 5000
```

4. **Note the ngrok URL** (e.g., `https://abc123.ngrok.io`)

### 6. Configure Twilio Webhook

1. **In Twilio Console, go to Messaging → Settings → WhatsApp Sandbox Settings**
2. **Set Webhook URL** to your ngrok URL + `/webhook`:
   - Local testing: `https://abc123.ngrok.io/webhook`
   - Production: `https://yourdomain.com/webhook`
3. **Save the configuration**

### 7. Test the Bot

1. **Send a message** to your Twilio WhatsApp number
2. **The bot should respond** using your existing chatbot logic
3. **Test crisis detection** with messages like "he hurt me"

## Production Deployment

### Option 1: Heroku

1. **Create Heroku app**:
```bash
heroku create your-whatsapp-bot
```

2. **Set environment variables**:
```bash
heroku config:set TWILIO_ACCOUNT_SID=your_sid
heroku config:set TWILIO_AUTH_TOKEN=your_token
heroku config:set TWILIO_PHONE_NUMBER=+14155238886
heroku config:set OPENAI_API_KEY=your_key
```

3. **Deploy**:
```bash
git add .
git commit -m "Add WhatsApp bot"
git push heroku main
```

4. **Update webhook URL** in Twilio console to your Heroku URL

### Option 2: Railway

1. **Connect your GitHub repo** to Railway
2. **Set environment variables** in Railway dashboard
3. **Deploy automatically**

### Option 3: DigitalOcean App Platform

1. **Create app** from GitHub repository
2. **Set environment variables**
3. **Deploy**

## Troubleshooting

### Common Issues:

1. **"Invalid webhook URL"**
   - Make sure ngrok is running
   - Check the webhook URL in Twilio console

2. **"Authentication failed"**
   - Verify your Twilio credentials
   - Check environment variables

3. **"No response from bot"**
   - Check Flask app logs
   - Verify OpenAI API key

4. **"Session not maintained"**
   - In production, use Redis instead of in-memory storage

### Debug Mode:

Run with debug logging:
```bash
FLASK_ENV=development python whatsapp_bot.py
```

## Security Considerations

1. **Use HTTPS** in production
2. **Validate Twilio requests** (add signature verification)
3. **Rate limiting** per user
4. **Input sanitization**
5. **Error handling** for sensitive information

## Monitoring

Check bot health:
```bash
curl https://yourdomain.com/health
```

Get statistics:
```bash
curl https://yourdomain.com/stats
```

## Cost Estimation

- **Twilio**: $0.005 per message (both ways)
- **OpenAI**: ~$0.0015 per 1K tokens
- **1000 conversations/month**: ~$10-15

## Next Steps

1. **Add Redis** for session persistence
2. **Implement rate limiting**
3. **Add user analytics**
4. **Set up monitoring**
5. **Add message encryption**
6. **Implement user authentication** 