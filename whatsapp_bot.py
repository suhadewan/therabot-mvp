import os
import json
from typing import Dict, Any
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

# Import your existing chatbot modules
from config import config
from crisis_detection import detect_crisis_keywords
from llm_safety_check import analyze_content_with_llm, get_llm_detected_response
from moderation import moderate_content
from guardrails import regenerate_if_needed

load_dotenv()

app = Flask(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')  # Your Twilio WhatsApp number

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize OpenAI client
import openai
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# In-memory session storage (use Redis in production)
user_sessions = {}

def load_system_prompt():
    """Load system prompt from file"""
    try:
        with open(config.SYSTEM_PROMPT_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return """You are a supportive mental health companion for youth.
        Be empathetic, non-judgmental, and encouraging.
        Keep responses under 50 words and end with a follow-up question."""

def process_message(user_phone: str, message_text: str) -> str:
    """
    Process incoming message using existing chatbot logic.
    Returns the response to send back.
    """
    
    # Initialize user session if not exists
    if user_phone not in user_sessions:
        user_sessions[user_phone] = {
            'messages': [],
            'rate_limit': []
        }
    
    # Check for crisis keywords first
    is_crisis, crisis_response = detect_crisis_keywords(message_text)
    
    if is_crisis:
        user_sessions[user_phone]['messages'].append({"role": "user", "content": message_text})
        user_sessions[user_phone]['messages'].append({"role": "assistant", "content": crisis_response})
        return crisis_response
    
    # Additional LLM-based safety check
    is_llm_concerning, concern_type, analysis = analyze_content_with_llm(message_text, openai_client)
    
    if is_llm_concerning:
        llm_response = get_llm_detected_response(concern_type, analysis)
        user_sessions[user_phone]['messages'].append({"role": "user", "content": message_text})
        user_sessions[user_phone]['messages'].append({"role": "assistant", "content": llm_response})
        return llm_response
    
    # Normal flow - moderation and chat
    is_safe, moderation_result = moderate_content(message_text, openai_client)
    
    if not is_safe:
        return config.ERROR_MODERATION
    
    # Add user message to session
    user_sessions[user_phone]['messages'].append({"role": "user", "content": message_text})
    
    # Prepare messages for OpenAI
    messages = [
        {"role": "system", "content": load_system_prompt()}
    ] + user_sessions[user_phone]['messages']
    
    try:
        # Get response from OpenAI
        completion = openai_client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=messages,
            temperature=config.MODEL_TEMPERATURE,
            max_tokens=config.MODEL_MAX_TOKENS,
            stream=False,
        )
        
        full_response = completion.choices[0].message.content
        
        # Apply guardrails
        final_response = regenerate_if_needed(full_response, messages, openai_client)
        
        # Add assistant response to session
        user_sessions[user_phone]['messages'].append({"role": "assistant", "content": final_response})
        
        return final_response
        
    except Exception as e:
        return f"An error occurred: {str(e)}"

def send_whatsapp_message(to_phone: str, message: str):
    """Send WhatsApp message via Twilio"""
    try:
        message = client.messages.create(
            from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
            body=message,
            to=f'whatsapp:{to_phone}'
        )
        return message.sid
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages"""
    try:
        # Get message details from Twilio
        incoming_message = request.form.get('Body', '')
        sender_phone = request.form.get('From', '')
        
        # Remove 'whatsapp:' prefix from phone number
        if sender_phone.startswith('whatsapp:'):
            sender_phone = sender_phone[9:]
        
        print(f"Received message from {sender_phone}: {incoming_message}")
        
        # Process message using existing chatbot logic
        response = process_message(sender_phone, incoming_message)
        
        # Send response back via WhatsApp
        send_whatsapp_message(sender_phone, response)
        
        # Return empty TwiML response
        resp = MessagingResponse()
        return str(resp)
        
    except Exception as e:
        print(f"Error in webhook: {e}")
        resp = MessagingResponse()
        return str(resp)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "whatsapp-mental-health-bot"})

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get bot statistics"""
    return jsonify({
        "active_users": len(user_sessions),
        "total_conversations": sum(len(session['messages']) for session in user_sessions.values())
    })

if __name__ == '__main__':
    # Check required environment variables
    required_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        print("Please set these in your .env file")
        exit(1)
    
    print("Starting WhatsApp Mental Health Bot...")
    print(f"Twilio Phone Number: {TWILIO_PHONE_NUMBER}")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5001) 