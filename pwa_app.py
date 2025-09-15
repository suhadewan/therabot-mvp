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
from database import init_database, get_database

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

def get_user_access_code(user_id: str) -> str:
    """Get access code for a user from database"""
    try:
        db = get_database()
        user = db.get_user_by_login_id(user_id)
        return user.get('access_code', 'UNKNOWN') if user else 'UNKNOWN'
    except Exception as e:
        print(f"Error getting user access code: {e}")
        return 'UNKNOWN'

def process_message(user_id: str, message_text: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
    """
    Process incoming message using existing chatbot logic.
    Returns response data for the frontend.
    """

    # Get user's access code
    access_code = get_user_access_code(user_id)

    # Initialize user session if not exists (load from database)
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'messages': [],
            'rate_limit': []
        }

        # Load recent chat history from database
        try:
            db = get_database()
            chat_history = db.get_chat_history(user_id, limit=20)  # Load last 20 messages
            # Convert to the format expected by OpenAI
            for msg in chat_history:
                user_sessions[user_id]['messages'].append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        except Exception as e:
            print(f"Error loading chat history: {e}")

    # Save user message to database immediately
    try:
        db = get_database()
        db.save_chat_message(user_id, access_code, "user", message_text)
    except Exception as e:
        print(f"Error saving user message: {e}")
    
    # Check for crisis keywords first
    is_crisis, crisis_response = detect_crisis_keywords(message_text)

    print(f"DEBUG: Crisis detection result: {is_crisis}, response: {crisis_response[:50]}...")

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

            # Update the user message with flag information
            conn = db.database._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chat_messages
                SET flag_type = ?, confidence = ?, analysis = ?
                WHERE id = (
                    SELECT id FROM chat_messages
                    WHERE user_id = ? AND role = "user" AND flag_type IS NULL
                    ORDER BY id DESC LIMIT 1
                )
            ''', (flag_type, 0.9, json.dumps({"detection_method": "keyword", "flag_type": flag_type}), user_id))
            conn.commit()
            conn.close()

            # Legacy flagged_chats table for compatibility
            db.log_flagged_chat(
                user_id=user_id,
                message=message_text,
                flag_type=flag_type,
                confidence=0.9,
                analysis={"detection_method": "keyword", "response": crisis_response},
                ip_address=ip_address,
                user_agent=user_agent
            )
            print(f"DEBUG: Crisis logged with flag: {flag_type}")
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
    
    # Additional LLM-based safety check
    is_llm_concerning, concern_type, analysis = analyze_content_with_llm(message_text, openai_client)
    
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

            # Update user message with flag information
            conn = db.database._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chat_messages
                SET flag_type = ?, confidence = ?, analysis = ?
                WHERE id = (
                    SELECT id FROM chat_messages
                    WHERE user_id = ? AND role = "user" AND flag_type IS NULL
                    ORDER BY id DESC LIMIT 1
                )
            ''', (concern_type, analysis.get('confidence', 0.8), json.dumps(analysis), user_id))
            conn.commit()
            conn.close()

            # Legacy flagged_chats table for compatibility
            db.log_flagged_chat(
                user_id=user_id,
                message=message_text,
                flag_type=concern_type,
                confidence=analysis.get('confidence', 0.8),
                analysis=analysis,
                ip_address=ip_address,
                user_agent=user_agent
            )
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
    
    # Normal flow - moderation and chat
    is_safe, moderation_result = moderate_content(message_text, openai_client)
    
    if not is_safe:
        # Log flagged chat to database
        db = get_database()
        db.log_flagged_chat(
            user_id=user_id,
            message=message_text,
            flag_type="moderation",
            confidence=0.9,
            analysis={"moderation_result": moderation_result},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
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
        except Exception as e:
            print(f"Error saving assistant message: {e}")

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

@app.route('/login')
def login():
    """Serve the login page"""
    return render_template('login.html')

@app.route('/admin-login')
def admin_login_page():
    """Serve the admin login page"""
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    """Serve the admin dashboard"""
    return render_template('admin.html')

@app.route('/api/chat', methods=['POST'])
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
        
        # Process message
        result = process_message(user_id, message, ip_address, user_agent)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/<user_id>')
def get_session(user_id):
    """Get user's chat session"""
    messages = []

    # First check in-memory session
    if user_id in user_sessions:
        messages = user_sessions[user_id]['messages']
    else:
        # Load from database if not in memory
        try:
            db = get_database()
            chat_history = db.get_chat_history(user_id, limit=50)  # Load recent messages
            # Convert to the format expected by frontend
            messages = []
            for msg in chat_history:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })

            # Store in memory for future requests
            if user_id not in user_sessions:
                user_sessions[user_id] = {
                    'messages': messages,
                    'rate_limit': []
                }
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
    return jsonify({"status": "healthy", "service": "mindmitra-pwa"})

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

        # Get flagged chats from chat_messages table (primary source)
        conn = db.database._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, user_id, access_code, role, content, message_type,
                   flag_type, confidence, analysis, timestamp
            FROM chat_messages
            WHERE flag_type IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        flagged_chats = []
        for row in rows:
            chat_dict = dict(zip(columns, row))
            # Parse JSON analysis if present
            if chat_dict.get('analysis'):
                try:
                    chat_dict['analysis'] = json.loads(chat_dict['analysis'])
                except:
                    chat_dict['analysis'] = {}

            # Map 'content' to 'message' for compatibility with admin template
            if 'content' in chat_dict:
                chat_dict['message'] = chat_dict['content']

            flagged_chats.append(chat_dict)

        # Get count of total flagged chats
        cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE flag_type IS NOT NULL')
        total_flagged = cursor.fetchone()[0]

        # Get flag type breakdown
        cursor.execute('''
            SELECT flag_type, COUNT(*)
            FROM chat_messages
            WHERE flag_type IS NOT NULL
            GROUP BY flag_type
        ''')
        flag_breakdown = dict(cursor.fetchall())

        conn.close()

        stats = {
            "total_flagged": total_flagged,
            "flag_breakdown": flag_breakdown,
            "recent_24h": 0,  # Can be implemented if needed
            "recent_7d": 0    # Can be implemented if needed
        }

        return jsonify({
            "flagged_chats": flagged_chats,
            "stats": stats,
            "pagination": {
                "page": page,
                "limit": limit,
                "offset": offset,
                "total": total_flagged
            }
        })
    except Exception as e:
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
    """Login with access code"""
    try:
        data = request.get_json()
        access_code = data.get('access_code', '').strip().upper()
        
        if not access_code:
            return jsonify({"error": "Access code is required"}), 400
        
        db = get_database()
        code_validation = db.validate_access_code(access_code)
        
        if not code_validation.get('valid'):
            return jsonify({"error": "Invalid or expired access code"}), 401
        
        # Check if code has reached max uses
        if code_validation['current_uses'] >= code_validation['max_uses']:
            return jsonify({"error": "Access code has reached maximum uses"}), 401
        
        # Check if code has expired
        if code_validation.get('expires_at'):
            from datetime import datetime
            if datetime.now() > datetime.fromisoformat(code_validation['expires_at']):
                return jsonify({"error": "Access code has expired"}), 401
        
        # Generate unique login ID
        import uuid
        login_id = f"user_{uuid.uuid4().hex[:8]}"
        
        # Create user account
        if db.create_user_account(access_code, login_id):
            return jsonify({
                "success": True,
                "login_id": login_id,
                "user_type": code_validation['user_type'],
                "school_id": code_validation.get('school_id'),
                "message": "Login successful"
            })
        else:
            return jsonify({"error": "Failed to create user account"}), 500
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/auth/validate', methods=['POST'])
def validate_session():
    """Validate existing login session"""
    try:
        data = request.get_json()
        login_id = data.get('login_id', '').strip()
        
        if not login_id:
            return jsonify({"error": "Login ID is required"}), 400
        
        db = get_database()
        user = db.get_user_by_login_id(login_id)
        
        if user:
            # Update last activity
            db.update_user_activity(login_id)
            return jsonify({
                "valid": True,
                "user": user
            })
        else:
            return jsonify({"valid": False, "error": "Invalid login ID"}), 401
            
    except Exception as e:
        print(f"Session validation error: {e}")
        return jsonify({"error": "Internal server error"}), 500

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
        
        return jsonify({"success": True, "message": "Logged out successfully"})
        
    except Exception as e:
        print(f"Logout error: {e}")
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
        
        if is_active is None and max_uses is None:
            return jsonify({"error": "At least one field to update is required"}), 400
        
        if max_uses is not None and max_uses < 1:
            return jsonify({"error": "Max uses must be at least 1"}), 400
        
        db = get_database()
        success = db.update_access_code(code, is_active, max_uses)
        
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

        # Get user's access code
        access_code = get_user_access_code(user_id)

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
        print(f"Error recording feeling: {e}")
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

@app.route('/admin/feelings')
def admin_feelings():
    """Admin endpoint to view all feelings data"""
    try:
        db = get_database()
        conn = db.database._get_connection()
        cursor = conn.cursor()

        # Get all feelings with user info
        cursor.execute('''
            SELECT ft.id, ft.user_id, ft.access_code, ft.feeling_score,
                   ft.date, ft.timestamp, ua.login_id, ac.user_type, ac.school_id
            FROM feelings_tracking ft
            LEFT JOIN user_accounts ua ON ft.user_id = ua.login_id
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
                'login_id': row[6],
                'user_type': row[7],
                'school_id': row[8]
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

if __name__ == '__main__':
    # Check required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("Missing OPENAI_API_KEY environment variable")
        print("Please set it in your .env file")
        exit(1)
    
    print("Starting MindMitra PWA...")
    
    # Initialize database
    try:
        print("Initializing database...")
        db_manager = init_database("sqlite")
        print("Database initialized successfully")
        print(f"Database type: {db_manager.db_type}")
        print(f"Database instance: {db_manager.database}")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    # Run Flask app
    port = int(os.getenv('PORT', 5002))
    app.run(debug=False, host='0.0.0.0', port=port) 