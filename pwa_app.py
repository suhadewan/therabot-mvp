from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Import your existing chatbot modules
from config import config
from crisis_detection import detect_crisis_keywords
from llm_safety_check import analyze_content_with_llm, get_llm_detected_response
from moderation import moderate_content
from guardrails import regenerate_if_needed

load_dotenv()

app = Flask(__name__)

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

def process_message(user_id: str, message_text: str) -> Dict[str, Any]:
    """
    Process incoming message using existing chatbot logic.
    Returns response data for the frontend.
    """
    
    # Initialize user session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'messages': [],
            'rate_limit': []
        }
    
    # Check for crisis keywords first
    is_crisis, crisis_response = detect_crisis_keywords(message_text)
    
    if is_crisis:
        user_sessions[user_id]['messages'].append({"role": "user", "content": message_text})
        user_sessions[user_id]['messages'].append({"role": "assistant", "content": crisis_response})
        return {
            "type": "crisis",
            "response": crisis_response,
            "timestamp": "now"
        }
    
    # Additional LLM-based safety check
    is_llm_concerning, concern_type, analysis = analyze_content_with_llm(message_text, openai_client)
    
    if is_llm_concerning:
        llm_response = get_llm_detected_response(concern_type, analysis)
        user_sessions[user_id]['messages'].append({"role": "user", "content": message_text})
        user_sessions[user_id]['messages'].append({"role": "assistant", "content": llm_response})
        return {
            "type": "safety_concern",
            "response": llm_response,
            "concern_type": concern_type,
            "timestamp": "now"
        }
    
    # Normal flow - moderation and chat
    is_safe, moderation_result = moderate_content(message_text, openai_client)
    
    if not is_safe:
        return {
            "type": "moderation",
            "response": config.ERROR_MODERATION,
            "timestamp": "now"
        }
    
    # Add user message to session
    user_sessions[user_id]['messages'].append({"role": "user", "content": message_text})
    
    # Prepare messages for OpenAI
    messages = [
        {"role": "system", "content": load_system_prompt()}
    ] + user_sessions[user_id]['messages']
    
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
        user_sessions[user_id]['messages'].append({"role": "assistant", "content": final_response})
        
        return {
            "type": "normal",
            "response": final_response,
            "timestamp": "now"
        }
        
    except Exception as e:
        return {
            "type": "error",
            "response": f"An error occurred: {str(e)}",
            "timestamp": "now"
        }

@app.route('/')
def index():
    """Serve the main PWA page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Process message
        result = process_message(user_id, message)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/<user_id>')
def get_session(user_id):
    """Get user's chat session"""
    if user_id in user_sessions:
        return jsonify({
            "messages": user_sessions[user_id]['messages']
        })
    return jsonify({"messages": []})

@app.route('/api/clear-session/<user_id>', methods=['POST'])
def clear_session(user_id):
    """Clear user's chat session"""
    if user_id in user_sessions:
        user_sessions[user_id]['messages'] = []
    return jsonify({"success": True})

@app.route('/manifest.json')
def manifest():
    """Serve PWA manifest"""
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    """Serve service worker"""
    return send_from_directory('static', 'sw.js')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "mental-health-pwa"})

if __name__ == '__main__':
    # Check required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("Missing OPENAI_API_KEY environment variable")
        print("Please set it in your .env file")
        exit(1)
    
    print("Starting Mental Health PWA...")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5002) 