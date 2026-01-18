from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, Response, stream_with_context
import os
import json
import logging
import threading
from typing import Dict, Any
from dotenv import load_dotenv
from datetime import datetime, date
import pytz

# Load environment variables first
load_dotenv()

# Set up logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking (optional)
sentry_dsn = os.getenv('SENTRY_DSN')
if sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            environment=os.getenv('ENVIRONMENT', 'development'),
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=0.1,
        )
        logger.info("Sentry error tracking initialized")
    except ImportError:
        logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk[flask]")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")

# Import your existing chatbot modules
from config import config
from crisis_detection import detect_crisis_keywords, get_crisis_response, get_abuse_response
from llm_safety_check import analyze_content_with_llm, get_llm_detected_response
from moderation import moderate_content, categorize_flagged_content
from guardrails import regenerate_if_needed
from database import init_database, get_database
from memory_manager import MemoryManager
from rate_limiter import rate_limit, get_rate_limit_status

# Timezone configuration
# India Standard Time (IST) for production
APP_TIMEZONE = pytz.timezone('Asia/Kolkata')

def get_india_today():
    """Get today's date in configured timezone"""
    return datetime.now(APP_TIMEZONE).date().isoformat()

def get_message_date_ist(timestamp_str: str):
    """Convert a UTC timestamp to configured timezone date"""
    try:
        # Parse the timestamp (assuming it's in format: YYYY-MM-DD HH:MM:SS)
        if ' ' in timestamp_str:
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        else:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

        # Assume stored timestamps are UTC, convert to app timezone
        dt_utc = pytz.UTC.localize(dt) if dt.tzinfo is None else dt
        dt_local = dt_utc.astimezone(APP_TIMEZONE)
        return dt_local.date().isoformat()
    except:
        # Fallback: just take the date part
        return timestamp_str[:10]

app = Flask(__name__)
# Set secret key for sessions
app.secret_key = os.getenv('SECRET_KEY', 'mindmitra-secret-key-change-in-production-2024')

# Production configuration
if os.getenv('ENVIRONMENT') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    logger.info("Production configuration applied")

# Initialize OpenAI client
import openai
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize database at module load time (works with both gunicorn and python pwa_app.py)
logger.info("Initializing database...")
db_type = os.getenv('DATABASE_TYPE', 'sqlite')
logger.info(f"Using database type: {db_type}")

if db_type == 'postgresql':
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found but DATABASE_TYPE is postgresql")
        raise ValueError("DATABASE_URL environment variable required for PostgreSQL")
    db_manager = init_database(db_type, connection_string=db_url)
else:
    db_manager = init_database(db_type)

logger.info(f"Database initialized successfully: {db_manager.db_type}")

# Initialize Memory Manager
memory_manager = None

def get_memory_manager():
    """Get or initialize the memory manager"""
    global memory_manager
    if memory_manager is None:
        memory_manager = MemoryManager(openai_client, get_database())
    return memory_manager

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

# Removed get_user_access_code() - no longer needed since user_id IS the access_code

def run_moderation_check_background(user_id: str, access_code: str, message_text: str,
                                     ip_address: str = None, user_agent: str = None):
    """
    Run moderation check in background thread after chat response is sent.
    If flagged, log to database and restrict account if needed.
    """
    try:
        print(f"DEBUG: Background moderation started for user {user_id}")

        # Run moderation check
        is_safe, moderation_result = moderate_content(message_text, openai_client)

        if not is_safe:
            # Use AI to categorize the flagged content into crisis types
            print(f"DEBUG: Background moderation flagged message, attempting AI categorization...")
            crisis_category = categorize_flagged_content(message_text, openai_client)

            db = get_database()

            if crisis_category:
                # It's a crisis that slipped through keyword detection
                print(f"DEBUG: Background AI categorized as crisis type: {crisis_category}")

                # Log as the specific crisis type (not "moderation")
                db.log_flagged_chat(
                    user_id=user_id,
                    message=message_text,
                    flag_type=crisis_category,
                    confidence=0.85,  # Slightly lower than keyword detection
                    analysis={"detection_method": "ai_moderation_background", "moderation_result": moderation_result},
                    access_code=access_code,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            else:
                # Not a crisis, just general moderation flag
                print(f"DEBUG: Background AI categorized as general moderation (not crisis)")
                db.log_flagged_chat(
                    user_id=user_id,
                    message=message_text,
                    flag_type="moderation",
                    confidence=0.9,
                    analysis={"moderation_result": moderation_result, "detection_method": "background"},
                    access_code=access_code,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

            # Check if user should be restricted (3 flags in 7 days)
            db.should_restrict_user(user_id, max_flags=3, days=7)
            print(f"DEBUG: Background moderation check completed for user {user_id}")
        else:
            print(f"DEBUG: Background moderation passed for user {user_id}")

    except Exception as e:
        logger.error(f"Error in background moderation for user {user_id}: {e}")
        import traceback
        traceback.print_exc()


def process_message(user_id: str, message_text: str, ip_address: str = None, user_agent: str = None, feature_group: str = 'full') -> Dict[str, Any]:
    """
    Process incoming message using existing chatbot logic.
    Returns response data for the frontend.
    feature_group: 'full' or 'basic' - controls which features are enabled
    """
    import time
    start_time = time.time()
    
    def log_timing(step_name):
        elapsed = time.time() - start_time
        logger.info(f"⏱️ TIMING [{user_id}] {step_name}: {elapsed:.2f}s")
    
    # Simplified: user_id IS the access_code
    access_code = user_id

    # OPTIMIZATION: Skip access code validation on every message
    # User already validated at login - only check if restricted in DB during save
    # This saves 2-3 seconds per message!
    db = get_database()

    # OPTIMIZATION: Check if session already loaded to avoid redundant DB queries
    if user_id in user_sessions and len(user_sessions[user_id].get('messages', [])) > 0:
        session_messages = user_sessions[user_id]['messages']
        print(f"DEBUG: Using cached session with {len(session_messages)} messages for user {user_id}")
    else:
        # Load recent chat history from database
        # Reduced from 100 to 20 for faster response times
        try:
            chat_history = db.get_chat_history(user_id, limit=20)  # Get recent messages
            log_timing("Chat history loaded")

            # Load all recent messages (no timezone filtering)
            session_messages = []
            for msg in chat_history:
                session_messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })

            # Initialize or update user session
            user_sessions[user_id] = {
                'messages': session_messages,
                'rate_limit': user_sessions.get(user_id, {}).get('rate_limit', [])
            }

            print(f"DEBUG: Loaded {len(session_messages)} messages for user {user_id}")

        except Exception as e:
            print(f"Error loading chat history: {e}")
            # Initialize empty session if database load fails
            user_sessions[user_id] = {
                'messages': [],
                'rate_limit': user_sessions.get(user_id, {}).get('rate_limit', [])
            }
            session_messages = []

    # Save user message to database immediately
    try:
        db.save_chat_message(user_id, access_code, "user", message_text)
        log_timing("User message saved")

        # Update streak in background thread (non-blocking) - ONLY for full feature group
        # Basic users don't have streak tracking to reduce DB operations
        if feature_group == 'full':
            def update_streak_background():
                try:
                    db = get_database()
                    db.update_streak(user_id, access_code)
                    print(f"DEBUG: Streak message count incremented for user {user_id}")
                except Exception as e:
                    print(f"Error updating streak in background: {e}")

            streak_thread = threading.Thread(target=update_streak_background, daemon=True)
            streak_thread.start()

    except Exception as e:
        print(f"Error saving user message: {e}")
    
    # Check for crisis keywords first (fast, no API calls)
    is_crisis, crisis_response = detect_crisis_keywords(message_text)
    log_timing("Crisis detection check")

    print(f"DEBUG: Crisis detection result: {is_crisis}, response: {crisis_response[:50] if crisis_response else 'None'}...")

    if is_crisis:
        # Determine flag type from response content
        flag_type = "SI"  # Default
        if "Self-Harm" in crisis_response:
            flag_type = "SH"
        elif "Safety Concern" in crisis_response:
            flag_type = "HI"
        elif "Abuse" in crisis_response:
            flag_type = "EA"

        print(f"DEBUG: Logging crisis to database for user: {user_id} with flag: {flag_type}")

        # Save assistant message to database with flag
        try:
            db = get_database()
            db.save_chat_message(
                user_id=user_id,
                access_code=access_code,
                role="assistant",
                content=crisis_response,
                message_type="crisis"
            )

            # Log to flagged_chats table
            db.log_flagged_chat(
                user_id=user_id,
                message=message_text,
                flag_type=flag_type,
                confidence=0.9,
                analysis={"detection_method": "keyword", "response": crisis_response},
                access_code=access_code,
                ip_address=ip_address,
                user_agent=user_agent
            )
            print(f"DEBUG: Crisis logged with flag: {flag_type}")

            # Check if user should be restricted (3 flags in 7 days)
            db.should_restrict_user(user_id, max_flags=3, days=7)
        except Exception as e:
            print(f"DEBUG: Database logging error: {e}")
            import traceback
            traceback.print_exc()

        user_sessions[user_id]['messages'].append({"role": "user", "content": message_text})
        user_sessions[user_id]['messages'].append({"role": "assistant", "content": crisis_response})
        return {
            "type": "crisis",
            "response": crisis_response,
            "flag_type": flag_type,
            "timestamp": "now"
        }
    
    # SKIP expensive LLM safety check for normal messages (saves 2-3 seconds!)
    # Only keyword detection is sufficient for most cases
    # LLM safety check removed to improve response time
    is_llm_concerning = False
    concern_type = "none"
    analysis = {}
    
    if is_llm_concerning:
        llm_response = get_llm_detected_response(concern_type, analysis)

        # Save assistant message to database
        try:
            db = get_database()
            db.save_chat_message(
                user_id=user_id,
                access_code=access_code,
                role="assistant",
                content=llm_response,
                message_type="safety"
            )

            # Log to flagged_chats table
            db.log_flagged_chat(
                user_id=user_id,
                message=message_text,
                flag_type=concern_type,
                confidence=analysis.get('confidence', 0.8),
                analysis=analysis,
                access_code=access_code,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Check if user should be restricted (3 flags in 7 days)
            db.should_restrict_user(user_id, max_flags=3, days=7)
        except Exception as e:
            print(f"Error saving LLM safety response: {e}")

        user_sessions[user_id]['messages'].append({"role": "user", "content": message_text})
        user_sessions[user_id]['messages'].append({"role": "assistant", "content": llm_response})
        return {
            "type": "safety_concern",
            "response": llm_response,
            "concern_type": concern_type,
            "timestamp": "now"
        }
    
    # Add user message to session
    user_sessions[user_id]['messages'].append({"role": "user", "content": message_text})

    # Get long-term memory context (cached per session to avoid repeated DB queries)
    # Only fetch once per session, not on every message
    if 'long_term_context' not in user_sessions[user_id]:
        mem_manager = get_memory_manager()
        mem_start = time.time()
        long_term_context = mem_manager.get_long_term_memory(user_id, days=7)
        mem_time = time.time() - mem_start
        logger.info(f"🧠 MEMORY QUERY TIME: {mem_time:.2f}s (first message, caching)")
        user_sessions[user_id]['long_term_context'] = long_term_context
        log_timing("Long-term memory loaded (fresh)")
    else:
        long_term_context = user_sessions[user_id]['long_term_context']
        logger.info(f"🧠 MEMORY: Using cached context (0.00s)")
        log_timing("Long-term memory loaded (cached)")
    
    # Build system prompt with long-term memory
    system_prompt = load_system_prompt()
    if long_term_context:
        system_prompt = f"{system_prompt}\n\n{long_term_context}"
        print(f"DEBUG: Added long-term memory context for user {user_id}")
    
    # Prepare messages for OpenAI
    # Short-term memory: Last 20 messages from current/recent sessions
    # Long-term memory: Included in system prompt above
    messages = [
        {"role": "system", "content": system_prompt}
    ] + user_sessions[user_id]['messages']

    print(f"DEBUG: Sending {len(messages)} messages to OpenAI for user {user_id}")
    log_timing("Messages prepared for OpenAI")
    
    try:
        # Check if TEST_MODE is enabled (for load testing without OpenAI calls)
        if config.TEST_MODE:
            logger.info(f"🧪 TEST MODE: Simulating OpenAI response for user {user_id}")
            import time
            time.sleep(config.TEST_RESPONSE_DELAY)  # Simulate API latency
            
            # Generate mock response
            mock_responses = [
                "Thank you for sharing that with me. How are you feeling about this situation right now?",
                "I hear you. It sounds like you're going through a challenging time. What support do you have around you?",
                "That's a valid concern. Have you had a chance to talk to anyone else about this?",
                "I understand. What do you think would help you feel better in this moment?",
                "It's okay to feel this way. What has helped you cope with similar feelings in the past?",
            ]
            import random
            full_response = random.choice(mock_responses)
            log_timing("✅ TEST MODE: Mock response generated")
        else:
            # Get response from OpenAI
            logger.info(f"🚀 Starting OpenAI API call for user {user_id}")
            completion = openai_client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=messages,
                temperature=config.MODEL_TEMPERATURE,
                max_tokens=config.MODEL_MAX_TOKENS,
                stream=False,
            )
            log_timing("✅ OpenAI API call completed")
            
            full_response = completion.choices[0].message.content
        
        # Apply guardrails (set to False to save ~1.4s, you already have crisis detection + moderation)
        ENABLE_GUARDRAILS = False  # Set to True to enable guardrails check
        if ENABLE_GUARDRAILS:
            final_response = regenerate_if_needed(full_response, messages, openai_client)
            log_timing("Guardrails applied")
        else:
            final_response = full_response
            log_timing("Guardrails skipped (disabled for speed)")

        # Save assistant response to database
        try:
            db = get_database()
            db.save_chat_message(
                user_id=user_id,
                access_code=access_code,
                role="assistant",
                content=final_response,
                message_type="normal"
            )
            log_timing("Assistant response saved to DB")
        except Exception as e:
            print(f"Error saving assistant message: {e}")

        # Add assistant response to session
        user_sessions[user_id]['messages'].append({"role": "assistant", "content": final_response})

        # Auto-generate daily summary in background (non-blocking)
        def generate_summary_background():
            try:
                # Get TODAY's actual message count from database (not session which is capped at 20)
                db = get_database()
                today = get_india_today()
                
                # Count today's messages from database
                if hasattr(db.database, '_get_connection'):
                    conn = db.database._get_connection()
                    cursor = conn.cursor()
                    if db.db_type == 'sqlite':
                        cursor.execute("""
                            SELECT COUNT(*) FROM chat_messages 
                            WHERE user_id = ? AND DATE(timestamp) = DATE('now')
                        """, (user_id,))
                    else:
                        cursor.execute("""
                            SELECT COUNT(*) FROM chat_messages 
                            WHERE user_id = %s AND DATE(timestamp) = CURRENT_DATE
                        """, (user_id,))
                    
                    todays_message_count = cursor.fetchone()[0]
                    
                    if db.db_type != 'sqlite':
                        db.database._return_connection(conn)
                    else:
                        conn.close()
                else:
                    todays_message_count = len(user_sessions[user_id]['messages'])
                
                logger.info(f"📊 SUMMARY CHECK: User {user_id} has {todays_message_count} messages TODAY")
                
                # Check after 10 messages (only generates once per day anyway)
                if todays_message_count >= 10:
                    logger.info(f"🎯 SUMMARY MILESTONE: {todays_message_count} messages! Checking if summary needed...")
                    mem_manager = get_memory_manager()
                    
                    # Only generate once per day
                    should_generate = mem_manager.should_generate_summary(user_id, todays_message_count)
                    logger.info(f"🔍 SUMMARY should_generate returned: {should_generate}")
                    
                    if should_generate:
                        logger.info(f"✨ Auto-generating daily summary for user {user_id} ({todays_message_count} messages today)")
                        
                        # Get ALL of today's messages for the summary
                        all_todays_messages = db.get_chat_history(user_id, limit=1000)  # Get all today's messages
                        messages_for_summary = [{"role": msg['role'], "content": msg['content']} for msg in all_todays_messages]
                        
                        mem_manager.save_daily_summary(
                            user_id=user_id,
                            access_code=access_code,
                            messages=messages_for_summary
                        )
                        logger.info(f"✅ SUMMARY: Summary saved successfully for {user_id}!")
                    else:
                        logger.info(f"⏭️  SUMMARY: Summary already exists for today, skipping")
                else:
                    logger.info(f"⏳ SUMMARY: Not enough messages yet (need 10, got {todays_message_count})")
            except Exception as e:
                logger.error(f"❌ Error generating summary in background: {e}")
                import traceback
                traceback.print_exc()
        
        # Start summary generation in background
        summary_thread = threading.Thread(target=generate_summary_background, daemon=True)
        summary_thread.start()

        # Run moderation check in background thread (non-blocking)
        # This checks for content policy violations without delaying the response
        # Flagged content will be logged and accounts restricted if needed
        background_thread = threading.Thread(
            target=run_moderation_check_background,
            args=(user_id, access_code, message_text, ip_address, user_agent),
            daemon=True  # Daemon thread won't prevent app from shutting down
        )
        background_thread.start()
        print(f"DEBUG: Started background moderation thread for user {user_id}")
        
        log_timing("🏁 TOTAL REQUEST TIME")
        logger.info(f"{'='*60}")

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
    # Check if user has session
    user_id = session.get('user_id')
    if not user_id:
        # If no session, index.html will show login prompt
        return render_template('index.html')
    
    # Check if user has given consent
    db = get_database()
    has_consented = db.check_user_consent(user_id)
    
    if not has_consented:
        # Redirect to consent page if not consented yet
        return redirect(url_for('consent'))
    
    # Check if user has submitted emergency contact
    has_emergency_contact = db.check_emergency_contact_submitted(user_id)
    
    if not has_emergency_contact:
        # Redirect to emergency contact page if not submitted yet
        return redirect(url_for('emergency_contact'))
    
    return render_template('index.html')

@app.route('/login')
def login():
    """Serve the login page"""
    return render_template('login.html')

@app.route('/consent')
def consent():
    """Serve the consent page - frontend handles auth via localStorage"""
    # Don't check Flask session here - frontend handles auth via localStorage
    # The consent.html page will check localStorage and validate with the API
    return render_template('consent.html')

@app.route('/emergency-contact')
def emergency_contact():
    """Serve the emergency contact page - requires authentication"""
    # Check if user has Flask session (they must be logged in)
    user_id = session.get('user_id')
    if not user_id:
        # Not logged in, redirect to login
        return redirect(url_for('login'))

    # Check if user has consented first
    db = get_database()
    has_consented = db.check_user_consent(user_id)
    if not has_consented:
        # Must consent before emergency contact
        return redirect(url_for('consent'))

    return render_template('emergency_contact.html')

@app.route('/admin-login')
def admin_login_page():
    """Serve the admin login page"""
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    """Serve the admin dashboard"""
    return render_template('admin.html')

@app.route('/api/chat/init', methods=['POST'])
def init_chat():
    """Initialize chat with a greeting message (save to database only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        message = data.get('message', '')

        if not message or not user_id:
            return jsonify({"error": "User ID and message are required"}), 400

        # Save the initial greeting to database
        db = get_database()
        access_code = user_id  # user_id IS the access_code
        success = db.save_chat_message(user_id, access_code, "assistant", message, message_type="normal")

        if success:
            return jsonify({"success": True, "message": "Initial greeting saved"})
        else:
            return jsonify({"error": "Failed to save greeting"}), 500

    except Exception as e:
        logger.error(f"Error in init chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
# Rate limiting disabled for pilot - uncomment to enable:
# @rate_limit(max_requests=30, window_hours=1)
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        message = data.get('message', '')

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Get IP address and user agent
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', 'Unknown')

        # Get feature group from session (defaults to 'full' for backwards compatibility)
        feature_group = session.get('feature_group', 'full')

        # Process message
        result = process_message(user_id, message, ip_address, user_agent, feature_group)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/<user_id>')
def get_session(user_id):
    """Get user's chat session - loads recent messages from database"""
    messages = []

    # Load recent messages (reduced for faster loading)
    try:
        db = get_database()
        chat_history = db.get_chat_history(user_id, limit=20)  # Get recent messages

        # Return all messages (no timezone filtering)
        for msg in chat_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        print(f"DEBUG: get_session loaded {len(messages)} messages for user {user_id}")

    except Exception as e:
        print(f"Error loading chat history for session: {e}")

    return jsonify({"messages": messages})

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

@app.route('/logo.jpeg')
def logo():
    """Serve logo file"""
    return send_from_directory('static', 'logo.jpeg')

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db = get_database()
        db_status = "connected"
        db_type = db.db_type
    except Exception as e:
        db_status = f"error: {str(e)}"
        db_type = "unknown"

    return jsonify({
        "status": "healthy",
        "service": "mindmitra-pwa",
        "database": {
            "status": db_status,
            "type": db_type
        },
        "environment": os.getenv("ENVIRONMENT", "development")
    })

@app.route('/track/open/<tracking_id>')
def track_email_open(tracking_id):
    """Track email open event via 1x1 pixel"""
    import base64

    # 1x1 transparent GIF pixel
    pixel_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')

    try:
        # Get client info
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')

        # Track email open using database method
        db = get_database()
        success = db.track_email_open(tracking_id, ip_address, user_agent)

        if success:
            logger.info(f"Email opened: {tracking_id} from {ip_address}")
        else:
            logger.warning(f"Failed to track email open: {tracking_id}")

    except Exception as e:
        logger.error(f"Error tracking email open: {e}")
        # Still return the pixel even if tracking fails

    # Return the pixel image
    response = Response(pixel_data, mimetype='image/gif')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/track/click/<tracking_id>')
def track_email_click(tracking_id):
    """Track email link click and redirect to mind-mitra.com"""
    try:
        # Get client info
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')

        # Track email click using database method
        db = get_database()
        success = db.track_email_click(tracking_id, ip_address, user_agent)

        if success:
            logger.info(f"Email link clicked: {tracking_id} from {ip_address}")
        else:
            logger.warning(f"Failed to track email click: {tracking_id}")

    except Exception as e:
        logger.error(f"Error tracking email click: {e}")
        # Still redirect even if tracking fails

    # Redirect to mind-mitra.com
    return redirect('https://mind-mitra.com', code=302)

@app.route('/api/rate-limit-status', methods=['POST'])
def rate_limit_status():
    """Get rate limit status for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "User ID required"}), 400

        status = get_rate_limit_status(user_id, max_requests=30, window_hours=1)
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test-db')
def test_db():
    """Test database functionality"""
    try:
        print("DEBUG: Testing database...")
        db = get_database()
        print(f"DEBUG: Database instance type: {type(db)}")
        print(f"DEBUG: Database methods: {dir(db)}")
        
        # Test logging a flagged chat
        print("DEBUG: Attempting to log flagged chat...")
        try:
            success = db.log_flagged_chat(
                user_id="test_user",
                message="test message for database testing",
                flag_type="test",
                confidence=0.8,
                analysis={"test": True},
                ip_address="127.0.0.1",
                user_agent="Test Browser"
            )
            print(f"DEBUG: Logging result: {success}")
        except Exception as log_error:
            print(f"DEBUG: Logging error: {log_error}")
            import traceback
            traceback.print_exc()
            success = False
        
        # Get stats
        print("DEBUG: Getting stats...")
        try:
            stats = db.get_stats()
            print(f"DEBUG: Stats: {stats}")
        except Exception as stats_error:
            print(f"DEBUG: Stats error: {stats_error}")
            stats = {"error": str(stats_error)}
        
        return jsonify({
            "database_test": "success",
            "logging_success": success,
            "stats": stats,
            "database_type": getattr(db, 'db_type', 'unknown'),
            "database_class": db.__class__.__name__
        })
    except Exception as e:
        print(f"DEBUG: Database test error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/flagged-chats')
def admin_flagged_chats():
    """Admin endpoint to view flagged chats"""
    try:
        db = get_database()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit

        # Get flagged chats from flagged_chats table
        flagged_chats = db.get_flagged_chats(limit, offset)
        
        # Get stats
        stats = db.get_stats()
        
        return jsonify({
            "flagged_chats": flagged_chats,
            "stats": stats,
            "pagination": {
                "page": page,
                "limit": limit,
                "offset": offset,
                "total": stats.get('total_flagged', 0)
            }
        })
    except Exception as e:
        logger.error(f"Error getting flagged chats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/all-chats')
def admin_all_chats():
    """Admin endpoint to view all chat messages"""
    try:
        db = get_database()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = (page - 1) * limit
        access_code = request.args.get('access_code')
        flag_type = request.args.get('flag_type')

        all_chats = db.get_all_chats(
            limit=limit,
            offset=offset,
            access_code=access_code,
            flag_type=flag_type
        )

        return jsonify({
            "chats": all_chats,
            "pagination": {
                "page": page,
                "limit": limit,
                "offset": offset
            },
            "filters": {
                "access_code": access_code,
                "flag_type": flag_type
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/stats')
def admin_stats():
    """Admin endpoint to view database statistics"""
    try:
        print("DEBUG: Getting database stats...")
        db = get_database()
        print(f"DEBUG: Database instance: {db}")
        stats = db.get_stats()
        print(f"DEBUG: Stats: {stats}")
        return jsonify(stats)
    except Exception as e:
        print(f"DEBUG: Error getting stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Login with access code - simplified to use access code as user identifier"""
    try:
        data = request.get_json()
        access_code = data.get('access_code', '').strip().upper()

        if not access_code:
            return jsonify({"error": "Access code is required"}), 400

        db = get_database()
        code_validation = db.validate_access_code(access_code)

        if not code_validation.get('valid'):
            # Use the specific error message from validation
            error_message = code_validation.get('error', 'Invalid or expired access code')
            return jsonify({"error": error_message}), 401

        # Access code IS the user identifier - they can log in unlimited times
        # No need to track max_uses or create separate user accounts

        # Set Flask session - use access_code as the user_id
        session['user_id'] = access_code
        session['access_code'] = access_code
        session['login_id'] = access_code
        session['feature_group'] = code_validation.get('feature_group', 'full')

        # Check consent status
        has_consented = db.check_user_consent(access_code)
        
        # Check emergency contact status
        has_emergency_contact = db.check_emergency_contact_submitted(access_code)

        return jsonify({
            "success": True,
            "login_id": access_code,
            "user_type": code_validation['user_type'],
            "message": "Login successful",
            "has_consented": has_consented,
            "needs_consent": not has_consented,
            "has_emergency_contact": has_emergency_contact,
            "needs_emergency_contact": not has_emergency_contact
        })

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/auth/validate', methods=['POST'])
def validate_session():
    """Validate existing login session - simplified for access code auth"""
    try:
        data = request.get_json()
        login_id = data.get('login_id', '').strip()

        if not login_id:
            return jsonify({"error": "Login ID is required"}), 400

        # login_id is now the access code
        db = get_database()
        code_validation = db.validate_access_code(login_id)

        if code_validation.get('valid'):
            # Get feature group for A/B testing
            feature_group = code_validation.get('feature_group', 'full')

            # Set Flask session
            session['user_id'] = login_id
            session['access_code'] = login_id
            session['login_id'] = login_id
            session['feature_group'] = feature_group

            # Check consent status
            has_consented = db.check_user_consent(login_id)

            # Check emergency contact status
            has_emergency_contact = db.check_emergency_contact_submitted(login_id)
            
            return jsonify({
                "valid": True,
                "user": {
                    "login_id": login_id,
                    "access_code": login_id,
                    "user_type": code_validation['user_type'],
                    "feature_group": feature_group
                },
                "has_consented": has_consented,
                "needs_consent": not has_consented,
                "has_emergency_contact": has_emergency_contact,
                "needs_emergency_contact": not has_emergency_contact
            })
        else:
            return jsonify({"valid": False, "error": "Invalid access code"}), 401

    except Exception as e:
        logger.error(f"Session validation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/init', methods=['POST'])
def init_app():
    """
    Combined initialization endpoint - returns all data in ONE call.
    Replaces: validate-session + chat-history + feelings-status + streak
    Optimized for performance with 3000-4000 users.
    """
    try:
        data = request.get_json()
        login_id = data.get('login_id', '').strip()

        if not login_id:
            return jsonify({"valid": False, "error": "Login ID is required"}), 400

        db = get_database()

        # 1. Validate access code
        code_validation = db.validate_access_code(login_id)

        if not code_validation.get('valid'):
            return jsonify({
                "valid": False,
                "error": code_validation.get('error', 'Invalid access code'),
                "restricted": code_validation.get('restricted', False)
            }), 401

        # Get feature group for A/B testing
        feature_group = code_validation.get('feature_group', 'full')

        # Set Flask session
        session['user_id'] = login_id
        session['access_code'] = login_id
        session['login_id'] = login_id
        session['feature_group'] = feature_group

        # 2. Get consent and emergency contact status
        has_consented = db.check_user_consent(login_id)
        has_emergency_contact = db.check_emergency_contact_submitted(login_id)

        # 3. Get chat history (limit to 50 for performance)
        chat_history = db.get_chat_history(login_id, limit=50)
        messages = [{"role": msg['role'], "content": msg['content'], "timestamp": msg.get('timestamp')} for msg in chat_history]

        # 4. Get feelings status for today
        feeling_status = db.get_feeling_for_today(login_id)

        # 5. Get streak data (only if full access to avoid unnecessary DB call)
        streak_data = None
        if feature_group == 'full':
            streak_data = db.get_streak_data(login_id)

        return jsonify({
            "valid": True,
            "user": {
                "login_id": login_id,
                "access_code": login_id,
                "user_type": code_validation['user_type'],
                "feature_group": feature_group
            },
            "has_consented": has_consented,
            "needs_consent": not has_consented,
            "has_emergency_contact": has_emergency_contact,
            "needs_emergency_contact": not has_emergency_contact,
            "chat_history": messages,
            "feeling_status": feeling_status,
            "streak_data": streak_data
        })

    except Exception as e:
        logger.error(f"Init error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"valid": False, "error": "Internal server error"}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        data = request.get_json()
        login_id = data.get('login_id', '').strip()
        
        if login_id:
            # Clear user session from memory
            if login_id in user_sessions:
                del user_sessions[login_id]
        
        # Clear Flask session
        session.clear()
        
        return jsonify({"success": True, "message": "Logged out successfully"})
        
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/consent', methods=['POST'])
def save_consent():
    """Save user's consent decision"""
    try:
        data = request.get_json()
        consent_accepted = data.get('consent_accepted', False)

        # Get user_id from localStorage (sent in request body)
        # If not in body, try session as fallback
        user_id = data.get('user_id') or session.get('user_id')
        access_code = data.get('access_code') or session.get('access_code') or user_id

        if not user_id:
            return jsonify({"error": "Not logged in"}), 401

        db = get_database()

        # ALWAYS save consent decision (accept OR decline) for analytics
        success = db.save_user_consent(user_id, access_code, consent_accepted)

        if not success:
            return jsonify({"error": "Failed to save consent"}), 500

        if consent_accepted:
            # User ACCEPTED - grant access
            logger.info(f"User ACCEPTED consent for access code: {access_code}, user_id: {user_id}")

            # Set session for future requests
            session['user_id'] = user_id
            session['access_code'] = access_code
            session['login_id'] = user_id

            return jsonify({"success": True, "consent_accepted": True, "next": "emergency_contact"})
        else:
            # User DECLINED - save decision but log them out
            # They can log in again with the same code and see the consent form again
            logger.info(f"User DECLINED consent for access code: {access_code}, user_id: {user_id}")

            # Clear their session (no access without consent)
            session.clear()

            return jsonify({
                "success": True,
                "consent_accepted": False,
                "message": "You can log in again when ready to consent"
            })

    except Exception as e:
        logger.error(f"Consent save error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/emergency-contact', methods=['POST'])
def save_emergency_contact():
    """Save user's emergency contact information"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', '').strip()
        name = data.get('name', '').strip()
        relationship = data.get('relationship', '').strip()
        phone = data.get('phone', '').strip()

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        if not name or not relationship or not phone:
            return jsonify({"error": "All fields are required"}), 400

        db = get_database()
        success = db.save_emergency_contact(user_id, name, relationship, phone)

        if success:
            logger.info(f"Emergency contact saved for user {user_id}")
            return jsonify({"success": True, "message": "Emergency contact saved successfully"})
        else:
            return jsonify({"error": "Failed to save emergency contact"}), 500

    except Exception as e:
        logger.error(f"Error saving emergency contact: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/emergency-contact/check', methods=['POST'])
def check_emergency_contact():
    """Check if user has submitted emergency contact"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', '').strip()

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        db = get_database()
        submitted = db.check_emergency_contact_submitted(user_id)

        return jsonify({"submitted": submitted})

    except Exception as e:
        logger.error(f"Error checking emergency contact: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/emergency-contact/skip', methods=['POST'])
def skip_emergency_contact():
    """Record that user chose to skip emergency contact"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', '').strip()

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        db = get_database()
        success = db.skip_emergency_contact(user_id)

        if success:
            logger.info(f"User {user_id} skipped emergency contact")
            return jsonify({"success": True, "message": "Emergency contact skipped"})
        else:
            return jsonify({"error": "Failed to record skip"}), 500

    except Exception as e:
        logger.error(f"Error skipping emergency contact: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login with username and password"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Simple password hashing (in production, use bcrypt or similar)
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        db = get_database()
        admin_validation = db.validate_admin_login(username, password_hash)
        
        if admin_validation.get('valid'):
            # Update last login
            db.update_admin_last_login(username)
            return jsonify({
                "success": True,
                "username": username,
                "message": "Admin login successful"
            })
        else:
            return jsonify({"error": "Invalid username or password"}), 401
            
    except Exception as e:
        print(f"Admin login error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    try:
        # For now, just return success (you could add session management later)
        return jsonify({"success": True, "message": "Admin logged out successfully"})
        
    except Exception as e:
        print(f"Admin logout error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin/access-codes', methods=['GET'])
def get_access_codes():
    """Get all access codes for admin management"""
    try:
        db = get_database()
        access_codes = db.get_all_access_codes()
        return jsonify({"access_codes": access_codes})
        
    except Exception as e:
        print(f"Error getting access codes: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin/access-codes', methods=['POST'])
def create_access_code():
    """Create a new access code"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        user_type = data.get('user_type', '').strip()
        school_id = data.get('school_id', '').strip()
        max_uses = int(data.get('max_uses', 1))
        created_by = data.get('created_by', 'admin')
        
        if not code or not user_type:
            return jsonify({"error": "Code and user_type are required"}), 400
        
        if max_uses < 1:
            return jsonify({"error": "Max uses must be at least 1"}), 400
        
        db = get_database()
        success = db.create_access_code(code, user_type, school_id, max_uses, created_by)
        
        if success:
            return jsonify({"success": True, "message": f"Access code {code} created successfully"})
        else:
            return jsonify({"error": "Failed to create access code"}), 500
            
    except Exception as e:
        print(f"Error creating access code: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin/access-codes/<code>', methods=['PUT'])
def update_access_code(code):
    """Update an access code"""
    try:
        data = request.get_json()
        is_active = data.get('is_active')
        max_uses = data.get('max_uses')
        feature_group = data.get('feature_group')

        if is_active is None and max_uses is None and feature_group is None:
            return jsonify({"error": "At least one field to update is required"}), 400

        if max_uses is not None and max_uses < 1:
            return jsonify({"error": "Max uses must be at least 1"}), 400

        if feature_group is not None and feature_group not in ['full', 'basic']:
            return jsonify({"error": "Feature group must be 'full' or 'basic'"}), 400

        db = get_database()
        success = db.update_access_code(code, is_active, max_uses, feature_group)

        if success:
            return jsonify({"success": True, "message": f"Access code {code} updated successfully"})
        else:
            return jsonify({"error": "Failed to update access code"}), 500

    except Exception as e:
        print(f"Error updating access code: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin/access-codes/<code>', methods=['DELETE'])
def delete_access_code(code):
    """Delete an access code (soft delete)"""
    try:
        db = get_database()
        success = db.delete_access_code(code)

        if success:
            return jsonify({"success": True, "message": f"Access code {code} deleted successfully"})
        else:
            return jsonify({"error": "Failed to delete access code"}), 500

    except Exception as e:
        print(f"Error deleting access code: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/feelings/check', methods=['POST'])
def check_feeling_status():
    """Check if user has recorded feeling today"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', '').strip()

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        db = get_database()
        feeling_status = db.get_feeling_for_today(user_id)

        return jsonify(feeling_status)

    except Exception as e:
        print(f"Error checking feeling status: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/feelings/record', methods=['POST'])
def record_feeling():
    """Record user's daily feeling score"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', '').strip()
        feeling_score = data.get('feeling_score')

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        if feeling_score is None or not isinstance(feeling_score, int) or not (0 <= feeling_score <= 10):
            return jsonify({"error": "Feeling score must be an integer between 0 and 10"}), 400

        # Simplified: user_id IS the access_code
        access_code = user_id

        db = get_database()
        success = db.record_feeling(user_id, access_code, feeling_score)

        if success:
            return jsonify({
                "success": True,
                "message": f"Feeling recorded: {feeling_score}/10",
                "feeling_score": feeling_score
            })
        else:
            return jsonify({"error": "Failed to record feeling"}), 500

    except Exception as e:
        logger.error(f"Error recording feeling: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/feelings/history/<user_id>')
def get_feeling_history(user_id):
    """Get user's feeling history"""
    try:
        days = request.args.get('days', 30, type=int)

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        db = get_database()
        history = db.get_user_feeling_history(user_id, days)

        return jsonify({"history": history})

    except Exception as e:
        print(f"Error getting feeling history: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/memory/summary/generate', methods=['POST'])
def generate_summary():
    """Manually trigger summary generation for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', '').strip()

        if not user_id:
            return jsonify({"success": False, "error": "User ID required"}), 400

        # Simplified: user_id IS the access_code
        access_code = user_id
        
        # Get chat history to summarize
        db = get_database()
        chat_history = db.get_chat_history(user_id, limit=50)
        
        if not chat_history:
            return jsonify({
                "success": False,
                "error": "No conversation history to summarize"
            }), 400
        
        # Generate and save summary
        mem_manager = get_memory_manager()
        success = mem_manager.save_daily_summary(
            user_id=user_id,
            access_code=access_code,
            messages=[{"role": msg['role'], "content": msg['content']} for msg in chat_history]
        )
        
        if success:
            return jsonify({"success": True, "message": "Summary generated successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to generate summary"}), 500
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/memory/summary/<user_id>')
def get_user_summary(user_id):
    """Get the latest conversation summary for a user"""
    try:
        mem_manager = get_memory_manager()
        summary = mem_manager.db.get_latest_summary(user_id)
        
        if summary:
            return jsonify({"success": True, "summary": summary})
        else:
            return jsonify({"success": False, "message": "No summary found"}), 404
        
    except Exception as e:
        print(f"Error getting summary: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/memory/summaries/<user_id>')
def get_user_summaries(user_id):
    """Get all conversation summaries for a user"""
    try:
        days = request.args.get('days', 30, type=int)
        mem_manager = get_memory_manager()
        summaries = mem_manager.db.get_conversation_summaries(user_id, days=days)
        
        return jsonify({"success": True, "summaries": summaries, "count": len(summaries)})
        
    except Exception as e:
        print(f"Error getting summaries: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/streak/<user_id>')
def get_streak(user_id):
    """Get user's streak information"""
    try:
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        db = get_database()
        streak_data = db.get_streak_data(user_id)

        return jsonify({
            "success": True,
            "streak_data": streak_data
        })

    except Exception as e:
        logger.error(f"Error getting streak data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/streak/freeze', methods=['POST'])
def freeze_streak():
    """Freeze a streak for a specific date"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        freeze_date = data.get('freeze_date')
        
        if not user_id or not freeze_date:
            return jsonify({"error": "User ID and freeze date are required"}), 400

        access_code = user_id  # user_id IS the access_code
        db = get_database()
        result = db.freeze_streak(user_id, access_code, freeze_date)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error freezing streak: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/streak/freeze-status/<user_id>')
def get_freeze_status(user_id):
    """Get user's freeze status for current week"""
    try:
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        db = get_database()
        freeze_status = db.get_freeze_status(user_id)

        return jsonify({
            "success": True,
            "freeze_status": freeze_status
        })

    except Exception as e:
        logger.error(f"Error getting freeze status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin/feelings')
def admin_feelings():
    """Admin endpoint to view all feelings data"""
    try:
        db = get_database()
        conn = db.database._get_connection()
        cursor = conn.cursor()

        # Get all feelings with access code info (grouped by access_code since that's what matters)
        cursor.execute('''
            SELECT ft.id, ft.user_id, ft.access_code, ft.feeling_score,
                   ft.date, ft.timestamp, ac.user_type, ac.school_id
            FROM feelings_tracking ft
            LEFT JOIN access_codes ac ON ft.access_code = ac.code
            ORDER BY ft.timestamp DESC
            LIMIT 100
        ''')

        rows = cursor.fetchall()

        feelings_data = []
        for row in rows:
            feelings_data.append({
                'id': row[0],
                'user_id': row[1],
                'access_code': row[2],
                'feeling_score': row[3],
                'date': row[4],
                'timestamp': row[5],
                'user_type': row[6],
                'school_id': row[7]
            })

        # Get summary stats
        cursor.execute('SELECT COUNT(*) FROM feelings_tracking')
        total_records = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(feeling_score) FROM feelings_tracking')
        avg_score = cursor.fetchone()[0] or 0

        cursor.execute('SELECT date, COUNT(*) FROM feelings_tracking GROUP BY date ORDER BY date DESC LIMIT 7')
        daily_counts = dict(cursor.fetchall())

        conn.close()

        return jsonify({
            "feelings_data": feelings_data,
            "stats": {
                "total_records": total_records,
                "average_score": round(avg_score, 2),
                "daily_counts": daily_counts
            }
        })

    except Exception as e:
        print(f"Error getting feelings data: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin/users')
def admin_get_users():
    """Admin endpoint to get list of users with message counts"""
    try:
        db = get_database()
        users = db.get_users_list()
        return jsonify({"users": users})

    except Exception as e:
        logger.error(f"Error getting users list: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin/user-chats/<access_code>')
def admin_get_user_chats(access_code):
    """Admin endpoint to get all chat messages for a specific user"""
    try:
        db = get_database()
        messages = db.get_user_chats(access_code)
        
        return jsonify({
            "access_code": access_code,
            "message_count": len(messages),
            "messages": messages
        })

    except Exception as e:
        logger.error(f"Error getting user chats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Database is already initialized at module load time
    print("Starting MindMitra PWA...")
    print(f"Database type: {db_manager.db_type}")

    # Run Flask app
    port = int(os.getenv('PORT', 5002))
    app.run(debug=False, host='0.0.0.0', port=port) 