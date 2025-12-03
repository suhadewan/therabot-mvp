import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging
import pytz

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Timezone configuration - India Standard Time (IST)
INDIA_TZ = pytz.timezone('Asia/Kolkata')

def get_india_now():
    """Get current datetime in India timezone"""
    return datetime.now(INDIA_TZ)

def get_india_today():
    """Get today's date in India timezone"""
    return get_india_now().date()

class DatabaseInterface(ABC):
    """Abstract base class for database operations"""
    
    @abstractmethod
    def init_db(self):
        """Initialize database tables"""
        pass
    
    @abstractmethod
    def log_flagged_chat(self, user_id: str, message: str, flag_type: str,
                        confidence: float, analysis: Dict[str, Any],
                        access_code: str = None, ip_address: str = None, user_agent: str = None) -> bool:
        """Log a flagged chat message"""
        pass
    
    @abstractmethod
    def get_flagged_chats(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get flagged chats with pagination"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        pass
    
    @abstractmethod
    def close(self):
        """Close database connection"""
        pass
    
    @abstractmethod
    def validate_access_code(self, code: str) -> Dict[str, Any]:
        """Validate an access code and return its details"""
        pass
    
    @abstractmethod
    def create_user_account(self, access_code: str, login_id: str) -> bool:
        """Create a new user account"""
        pass
    
    @abstractmethod
    def get_user_by_login_id(self, login_id: str) -> Dict[str, Any]:
        """Get user account by login ID"""
        pass
    
    @abstractmethod
    def update_user_activity(self, login_id: str) -> bool:
        """Update user's last activity timestamp"""
        pass
    
    @abstractmethod
    def get_access_code_stats(self) -> Dict[str, Any]:
        """Get statistics about access codes"""
        pass
    
    @abstractmethod
    def create_admin_user(self, username: str, password_hash: str) -> bool:
        """Create a new admin user"""
        pass
    
    @abstractmethod
    def validate_admin_login(self, username: str, password_hash: str) -> Dict[str, Any]:
        """Validate admin login credentials"""
        pass
    
    @abstractmethod
    def update_admin_last_login(self, username: str) -> bool:
        """Update admin's last login timestamp"""
        pass

    @abstractmethod
    def create_access_code(self, code: str, user_type: str, school_id: str, max_uses: int, created_by: str) -> bool:
        """Create a new access code"""
        pass

    @abstractmethod
    def get_all_access_codes(self) -> List[Dict[str, Any]]:
        """Get all access codes with their details"""
        pass

    @abstractmethod
    def update_access_code(self, code: str, is_active: bool = None, max_uses: int = None) -> bool:
        """Update access code properties"""
        pass

    @abstractmethod
    def delete_access_code(self, code: str) -> bool:
        """Delete an access code (soft delete by setting inactive)"""
        pass

    @abstractmethod
    def save_chat_message(self, user_id: str, access_code: str, role: str, content: str,
                         session_id: str = None, message_type: str = "normal") -> bool:
        """Save a chat message to database"""
        pass

    @abstractmethod
    def get_chat_history(self, user_id: str, limit: int = 50, session_id: str = None) -> List[Dict[str, Any]]:
        """Get chat history for a user"""
        pass

    @abstractmethod
    def get_all_chats(self, limit: int = 100, offset: int = 0,
                     access_code: str = None, flag_type: str = None) -> List[Dict[str, Any]]:
        """Get all chat messages with filtering options"""
        pass

    @abstractmethod
    def cleanup_old_chats(self, days: int = 30) -> int:
        """Clean up old chat messages older than specified days"""
        pass

    @abstractmethod
    def record_feeling(self, user_id: str, access_code: str, feeling_score: int) -> bool:
        """Record a user's daily feeling score (0-10)"""
        pass

    @abstractmethod
    def get_feeling_for_today(self, user_id: str) -> Dict[str, Any]:
        """Get today's feeling record for a user"""
        pass

    @abstractmethod
    def get_user_feeling_history(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user's feeling history for the last N days"""
        pass

    @abstractmethod
    def save_conversation_summary(self, user_id: str, access_code: str, summary_date: str,
                                  main_concerns: str = None, emotional_patterns: str = None,
                                  coping_strategies: str = None, progress_notes: str = None,
                                  important_context: str = None, message_count: int = 0) -> bool:
        """Save or update a conversation summary"""
        pass

    @abstractmethod
    def get_conversation_summaries(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get conversation summaries for the last N days"""
        pass

    @abstractmethod
    def get_latest_summary(self, user_id: str) -> Dict[str, Any]:
        """Get the most recent conversation summary for a user"""
        pass

    @abstractmethod
    def check_user_consent(self, user_id: str) -> bool:
        """Check if user has given consent"""
        pass

    @abstractmethod
    def get_user_flag_count(self, user_id: str, days: int = 7) -> int:
        """Get the number of flags for a user in the last N days"""
        pass

    @abstractmethod
    def should_restrict_user(self, user_id: str, max_flags: int = 3, days: int = 7) -> bool:
        """Check if user should be restricted based on flag count"""
        pass

    @abstractmethod
    def save_user_consent(self, user_id: str, access_code: str, consent_accepted: bool) -> bool:
        """Save user's consent decision"""
        pass

    @abstractmethod
    def update_streak(self, user_id: str, access_code: str) -> bool:
        """Update user's streak for today"""
        pass

    @abstractmethod
    def get_streak_data(self, user_id: str) -> Dict[str, Any]:
        """Get user's streak information including current streak and weekly activity"""
        pass

    @abstractmethod
    def freeze_streak(self, user_id: str, access_code: str, freeze_date: str) -> Dict[str, Any]:
        """Freeze the streak for a specific date (max 1 per week)"""
        pass

    @abstractmethod
    def get_freeze_status(self, user_id: str) -> Dict[str, Any]:
        """Get information about user's freeze usage this week"""
        pass

    @abstractmethod
    def track_email_open(self, tracking_id: str, ip_address: str, user_agent: str) -> bool:
        """Track email open event"""
        pass

    @abstractmethod
    def track_email_click(self, tracking_id: str, ip_address: str, user_agent: str) -> bool:
        """Track email link click event"""
        pass

class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation of the database interface"""
    
    def __init__(self, db_path: str = "mental_health_bot.db"):
        self.db_path = db_path
        self.db_type = "sqlite"
        # Don't create connection in __init__ - create per request
    
    def _get_connection(self):
        """Get a new database connection for the current thread"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Initialize SQLite database and tables"""
        try:
            logger.info(f"SQLiteDatabase: Initializing database at {self.db_path}")
            logger.info(f"SQLiteDatabase: Current working directory: {os.getcwd()}")
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create comprehensive chat messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'normal',
                    flag_type TEXT,
                    confidence REAL,
                    analysis TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Create flagged chats table (legacy - keep for compatibility)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flagged_chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    access_code TEXT,
                    message TEXT NOT NULL,
                    flag_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    analysis TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')
            
            # Create chat sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_end DATETIME,
                    message_count INTEGER DEFAULT 0,
                    has_flagged_content BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Create access codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    user_type TEXT NOT NULL,
                    school_id TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    max_uses INTEGER DEFAULT 1,
                    current_uses INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    created_by TEXT
                )
            ''')
            
            # Create user accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login_id TEXT UNIQUE NOT NULL,
                    access_code TEXT NOT NULL,
                    first_login DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')
            
            # Create admin users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            ''')

            # Create feelings tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feelings_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    feeling_score INTEGER NOT NULL CHECK (feeling_score >= 0 AND feeling_score <= 10),
                    date DATE NOT NULL DEFAULT (DATE('now')),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code),
                    UNIQUE(access_code, date)
                )
            ''')

            # Create conversation summaries table for long-term memory
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    summary_date DATE NOT NULL,
                    main_concerns TEXT,
                    emotional_patterns TEXT,
                    coping_strategies TEXT,
                    progress_notes TEXT,
                    important_context TEXT,
                    message_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, summary_date),
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Create consent tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_consents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    access_code TEXT NOT NULL,
                    consent_accepted BOOLEAN NOT NULL,
                    consent_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Create streak tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS streak_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    activity_date DATE NOT NULL DEFAULT (DATE('now')),
                    message_count INTEGER DEFAULT 0,
                    is_freeze BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code),
                    UNIQUE(user_id, activity_date)
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp
                ON chat_messages(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id
                ON chat_messages(user_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_messages_access_code
                ON chat_messages(access_code)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_flagged_chats_timestamp
                ON flagged_chats(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_flagged_chats_flag_type
                ON flagged_chats(flag_type)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feelings_tracking_user_date
                ON feelings_tracking(user_id, date)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feelings_tracking_date
                ON feelings_tracking(date)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_streak_tracking_user_date
                ON streak_tracking(user_id, activity_date)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_streak_tracking_date
                ON streak_tracking(activity_date)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("SQLite database initialized successfully")
            
            # Verify table creation
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            logger.info(f"SQLiteDatabase: Tables created: {tables}")
            
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {e}")
            raise
    
    def log_flagged_chat(self, user_id: str, message: str, flag_type: str,
                        confidence: float, analysis: Dict[str, Any],
                        access_code: str = None, ip_address: str = None, user_agent: str = None) -> bool:
        """Log a flagged chat message to SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flagged_chats
                (user_id, access_code, message, flag_type, confidence, analysis, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                access_code,
                message,
                flag_type,
                confidence,
                json.dumps(analysis),
                ip_address,
                user_agent
            ))

            conn.commit()
            conn.close()
            logger.info(f"Flagged chat logged: {flag_type} for user {user_id}, access_code {access_code}")
            return True

        except Exception as e:
            logger.error(f"Error logging flagged chat: {e}")
            return False
    
    def get_flagged_chats(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get flagged chats with pagination from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, access_code, message, flag_type, confidence, analysis,
                       timestamp, ip_address, user_agent
                FROM flagged_chats
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            result = []
            for row in rows:
                chat_dict = dict(zip(columns, row))
                # Parse JSON analysis
                if chat_dict['analysis']:
                    try:
                        chat_dict['analysis'] = json.loads(chat_dict['analysis'])
                    except:
                        chat_dict['analysis'] = {}
                result.append(chat_dict)
            
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting flagged chats: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total flagged chats
            cursor.execute('SELECT COUNT(*) FROM flagged_chats')
            total_flagged = cursor.fetchone()[0]
            
            # Flag type breakdown
            cursor.execute('''
                SELECT flag_type, COUNT(*) 
                FROM flagged_chats 
                GROUP BY flag_type
            ''')
            flag_breakdown = dict(cursor.fetchall())
            
            # Recent activity (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM flagged_chats 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            recent_24h = cursor.fetchone()[0]
            
            # Recent activity (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM flagged_chats 
                WHERE timestamp > datetime('now', '-7 days')
            ''')
            recent_7d = cursor.fetchone()[0]
            
            conn.close()
            return {
                'total_flagged': total_flagged,
                'flag_breakdown': flag_breakdown,
                'recent_24h': recent_24h,
                'recent_7d': recent_7d,
                'database_type': 'SQLite'
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def validate_access_code(self, code: str) -> Dict[str, Any]:
        """Validate an access code and return its details"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # First check if code exists at all
            cursor.execute('''
                SELECT code, user_type, school_id, is_active, max_uses, current_uses
                FROM access_codes
                WHERE code = ?
            ''', (code,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                # Code doesn't exist
                return {
                    'valid': False,
                    'error': 'Invalid access code'
                }

            code_data = row[0]
            user_type = row[1]
            school_id = row[2]
            is_active = row[3]
            max_uses = row[4]
            current_uses = row[5]

            # Check if code is inactive (restricted)
            if not is_active:
                return {
                    'valid': False,
                    'restricted': True,
                    'error': 'This account has been temporarily restricted for safety reasons. A staff member will review your account and contact you if needed.'
                }

            # Check if code has reached max uses
            if current_uses >= max_uses:
                return {
                    'valid': False,
                    'error': 'Access code has reached maximum uses'
                }

            return {
                    'code': code_data,
                    'user_type': user_type,
                    'school_id': school_id,
                    'is_active': is_active,
                    'max_uses': max_uses,
                    'current_uses': current_uses,
                    'valid': True
                }
            return {'valid': False, 'error': 'Invalid access code'}
            
        except Exception as e:
            logger.error(f"Error validating access code: {e}")
            return {'valid': False, 'error': str(e)}
    
    def create_user_account(self, access_code: str, login_id: str) -> bool:
        """Create a new user account"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create user account
            cursor.execute('''
                INSERT INTO user_accounts (login_id, access_code)
                VALUES (?, ?)
            ''', (login_id, access_code))
            
            # Update access code usage count
            cursor.execute('''
                UPDATE access_codes 
                SET current_uses = current_uses + 1
                WHERE code = ?
            ''', (access_code,))
            
            conn.commit()
            conn.close()
            logger.info(f"User account created: {login_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user account: {e}")
            return False
    
    def get_user_by_login_id(self, login_id: str) -> Dict[str, Any]:
        """Get user account by login ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ua.login_id, ua.access_code, ua.first_login, ua.last_active, ua.total_messages,
                       ac.user_type, ac.school_id
                FROM user_accounts ua
                JOIN access_codes ac ON ua.access_code = ac.code
                WHERE ua.login_id = ? AND ua.is_active = TRUE
            ''', (login_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'login_id': row[0],
                    'access_code': row[1],
                    'first_login': row[2],
                    'last_active': row[3],
                    'total_messages': row[4],
                    'user_type': row[5],
                    'school_id': row[6]
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return {}
    
    def update_user_activity(self, login_id: str) -> bool:
        """Update user's last activity timestamp"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_accounts 
                SET last_active = CURRENT_TIMESTAMP
                WHERE login_id = ?
            ''', (login_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user activity: {e}")
            return False
    
    def get_access_code_stats(self) -> Dict[str, Any]:
        """Get statistics about access codes"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total access codes
            cursor.execute('SELECT COUNT(*) FROM access_codes')
            total_codes = cursor.fetchone()[0]
            
            # Active codes
            cursor.execute('SELECT COUNT(*) FROM access_codes WHERE is_active = TRUE')
            active_codes = cursor.fetchone()[0]
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM user_accounts')
            total_users = cursor.fetchone()[0]
            
            # Recent users (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM user_accounts 
                WHERE last_active >= datetime('now', '-7 days')
            ''')
            recent_users = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_codes': total_codes,
                'active_codes': active_codes,
                'total_users': total_users,
                'recent_users': recent_users
            }
            
        except Exception as e:
            logger.error(f"Error getting access code stats: {e}")
            return {}
    
    def create_admin_user(self, username: str, password_hash: str) -> bool:
        """Create a new admin user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash)
                VALUES (?, ?)
            ''', (username, password_hash))
            
            conn.commit()
            conn.close()
            logger.info(f"Admin user created: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            return False
    
    def validate_admin_login(self, username: str, password_hash: str) -> Dict[str, Any]:
        """Validate admin login credentials"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, is_active, created_at, last_login
                FROM admin_users 
                WHERE username = ? AND password_hash = ? AND is_active = TRUE
            ''', (username, password_hash))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'username': row[0],
                    'is_active': row[1],
                    'created_at': row[2],
                    'last_login': row[3],
                    'valid': True
                }
            return {'valid': False}
            
        except Exception as e:
            logger.error(f"Error validating admin login: {e}")
            return {'valid': False, 'error': str(e)}
    
    def update_admin_last_login(self, username: str) -> bool:
        """Update admin's last login timestamp"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE admin_users 
                SET last_login = CURRENT_TIMESTAMP
                WHERE username = ?
            ''', (username,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating admin last login: {e}")
            return False

    def create_access_code(self, code: str, user_type: str, school_id: str, max_uses: int, created_by: str) -> bool:
        """Create a new access code"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_codes 
                (code, user_type, school_id, is_active, max_uses, current_uses, created_at, created_by)
                VALUES (?, ?, ?, TRUE, ?, 0, CURRENT_TIMESTAMP, ?)
            ''', (code, user_type, school_id, max_uses, created_by))
            
            conn.commit()
            conn.close()
            logger.info(f"Access code created: {code}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating access code: {e}")
            return False

    def get_all_access_codes(self) -> List[Dict[str, Any]]:
        """Get all access codes with their details"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT code, user_type, school_id, is_active, max_uses, current_uses, created_at, created_by
                FROM access_codes 
                ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            access_codes = []
            for row in rows:
                access_codes.append({
                    'code': row[0],
                    'user_type': row[1],
                    'school_id': row[2],
                    'is_active': row[3],
                    'max_uses': row[4],
                    'current_uses': row[5],
                    'created_at': row[6],
                    'created_by': row[7]
                })
            
            return access_codes
            
        except Exception as e:
            logger.error(f"Error getting access codes: {e}")
            return []

    def update_access_code(self, code: str, is_active: bool = None, max_uses: int = None) -> bool:
        """Update access code properties"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            if is_active is not None:
                update_fields.append("is_active = ?")
                params.append(is_active)
            
            if max_uses is not None:
                update_fields.append("max_uses = ?")
                params.append(max_uses)
            
            if not update_fields:
                return False
            
            params.append(code)
            
            cursor.execute(f'''
                UPDATE access_codes 
                SET {', '.join(update_fields)}
                WHERE code = ?
            ''', params)
            
            conn.commit()
            conn.close()
            logger.info(f"Access code updated: {code}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating access code: {e}")
            return False

    def delete_access_code(self, code: str) -> bool:
        """Delete an access code (soft delete by setting inactive)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE access_codes
                SET is_active = FALSE
                WHERE code = ?
            ''', (code,))

            conn.commit()
            conn.close()
            logger.info(f"Access code deleted: {code}")
            return True

        except Exception as e:
            logger.error(f"Error deleting access code: {e}")
            return False

    def save_chat_message(self, user_id: str, access_code: str, role: str, content: str,
                         session_id: str = None, message_type: str = "normal") -> bool:
        """Save a chat message to SQLite database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO chat_messages
                (user_id, access_code, session_id, role, content, message_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, access_code, session_id, role, content, message_type))

            conn.commit()
            conn.close()
            logger.info(f"Chat message saved: {role} message for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return False

    def get_chat_history(self, user_id: str, limit: int = 50, session_id: str = None) -> List[Dict[str, Any]]:
        """Get chat history for a user from SQLite - user_id is now the access_code"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if session_id:
                cursor.execute('''
                    SELECT id, user_id, access_code, role, content, message_type, timestamp
                    FROM chat_messages
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, session_id, limit))
            else:
                # Simplified: user_id is now the access_code, no join needed
                cursor.execute('''
                    SELECT id, user_id, access_code, role, content, message_type, timestamp
                    FROM chat_messages
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, limit))

            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

            result = []
            for row in rows:
                message_dict = dict(zip(columns, row))
                result.append(message_dict)

            conn.close()

            # Reverse the order to get chronological order (oldest first)
            # since we fetched with DESC to get the most recent messages
            result.reverse()

            return result

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    def get_all_chats(self, limit: int = 100, offset: int = 0,
                     access_code: str = None, flag_type: str = None) -> List[Dict[str, Any]]:
        """Get all chat messages with filtering options from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Build query with filters
            query = '''
                SELECT id, user_id, access_code, session_id, role, content,
                       message_type, flag_type, confidence, analysis, timestamp
                FROM chat_messages
                WHERE 1=1
            '''
            params = []

            if access_code:
                query += ' AND access_code = ?'
                params.append(access_code)

            if flag_type:
                query += ' AND flag_type = ?'
                params.append(flag_type)

            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

            result = []
            for row in rows:
                message_dict = dict(zip(columns, row))
                # Parse JSON analysis if present
                if message_dict.get('analysis'):
                    try:
                        message_dict['analysis'] = json.loads(message_dict['analysis'])
                    except:
                        message_dict['analysis'] = {}
                result.append(message_dict)

            conn.close()
            return result

        except Exception as e:
            logger.error(f"Error getting all chats: {e}")
            return []

    def cleanup_old_chats(self, days: int = 30) -> int:
        """Clean up old chat messages older than specified days from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM chat_messages
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Cleaned up {deleted_count} old chat messages")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old chats: {e}")
            return 0
    
    def record_feeling(self, user_id: str, access_code: str, feeling_score: int) -> bool:
        """Record a user's daily feeling score (0-10) in SQLite"""
        try:
            if not (0 <= feeling_score <= 10):
                logger.error(f"Invalid feeling score: {feeling_score}. Must be 0-10")
                return False

            conn = self._get_connection()
            cursor = conn.cursor()

            # Use INSERT OR REPLACE to handle the case where access code already recorded today
            cursor.execute('''
                INSERT OR REPLACE INTO feelings_tracking
                (user_id, access_code, feeling_score, date)
                VALUES (?, ?, ?, DATE('now'))
            ''', (user_id, access_code, feeling_score))

            conn.commit()
            conn.close()
            logger.info(f"Feeling recorded: {feeling_score}/10 for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error recording feeling: {e}")
            return False

    def get_feeling_for_today(self, user_id: str) -> Dict[str, Any]:
        """Get today's feeling record for a user from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Simplified: user_id IS the access_code
            cursor.execute('''
                SELECT id, feeling_score, date, timestamp, user_id, access_code
                FROM feelings_tracking
                WHERE access_code = ? AND date = DATE('now')
                LIMIT 1
            ''', (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'feeling_score': row[1],
                    'date': row[2],
                    'timestamp': row[3],
                    'user_id': row[4],
                    'access_code': row[5],
                    'recorded_today': True
                }
            else:
                return {'recorded_today': False}

        except Exception as e:
            logger.error(f"Error getting today's feeling: {e}")
            return {'recorded_today': False}

    def get_user_feeling_history(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user's feeling history for the last N days from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, feeling_score, date, timestamp
                FROM feelings_tracking
                WHERE access_code = (
                    SELECT access_code FROM user_accounts WHERE login_id = ?
                ) AND date >= DATE('now', '-' || ? || ' days')
                ORDER BY date DESC
            ''', (user_id, days))

            rows = cursor.fetchall()
            conn.close()

            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'feeling_score': row[1],
                    'date': row[2],
                    'timestamp': row[3]
                })

            return history

        except Exception as e:
            logger.error(f"Error getting feeling history: {e}")
            return []

    def save_conversation_summary(self, user_id: str, access_code: str, summary_date: str,
                                  main_concerns: str = None, emotional_patterns: str = None,
                                  coping_strategies: str = None, progress_notes: str = None,
                                  important_context: str = None, message_count: int = 0) -> bool:
        """Save or update a conversation summary to SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Try to update existing summary first
            cursor.execute('''
                UPDATE conversation_summaries
                SET main_concerns = ?,
                    emotional_patterns = ?,
                    coping_strategies = ?,
                    progress_notes = ?,
                    important_context = ?,
                    message_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND summary_date = ?
            ''', (main_concerns, emotional_patterns, coping_strategies, progress_notes,
                  important_context, message_count, user_id, summary_date))

            # If no rows updated, insert new summary
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO conversation_summaries
                    (user_id, access_code, summary_date, main_concerns, emotional_patterns,
                     coping_strategies, progress_notes, important_context, message_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, access_code, summary_date, main_concerns, emotional_patterns,
                      coping_strategies, progress_notes, important_context, message_count))

            conn.commit()
            conn.close()
            logger.info(f"Saved conversation summary for user {user_id} on {summary_date}")
            return True

        except Exception as e:
            logger.error(f"Error saving conversation summary: {e}")
            return False

    def get_conversation_summaries(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get conversation summaries for the last N days from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, user_id, summary_date, main_concerns, emotional_patterns,
                       coping_strategies, progress_notes, important_context,
                       message_count, created_at, updated_at
                FROM conversation_summaries
                WHERE user_id = ? AND summary_date >= DATE('now', '-' || ? || ' days')
                ORDER BY summary_date DESC
            ''', (user_id, days))

            rows = cursor.fetchall()
            conn.close()

            summaries = []
            for row in rows:
                summaries.append({
                    'id': row[0],
                    'user_id': row[1],
                    'summary_date': row[2],
                    'main_concerns': row[3],
                    'emotional_patterns': row[4],
                    'coping_strategies': row[5],
                    'progress_notes': row[6],
                    'important_context': row[7],
                    'message_count': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                })

            return summaries

        except Exception as e:
            logger.error(f"Error getting conversation summaries: {e}")
            return []

    def get_latest_summary(self, user_id: str) -> Dict[str, Any]:
        """Get the most recent conversation summary for a user from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, user_id, summary_date, main_concerns, emotional_patterns,
                       coping_strategies, progress_notes, important_context,
                       message_count, created_at, updated_at
                FROM conversation_summaries
                WHERE user_id = ?
                ORDER BY summary_date DESC
                LIMIT 1
            ''', (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'summary_date': row[2],
                    'main_concerns': row[3],
                    'emotional_patterns': row[4],
                    'coping_strategies': row[5],
                    'progress_notes': row[6],
                    'important_context': row[7],
                    'message_count': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                }
            else:
                return {}

        except Exception as e:
            logger.error(f"Error getting latest summary: {e}")
            return {}

    def check_user_consent(self, user_id: str) -> bool:
        """Check if user has given consent from SQLite - user_id is now the access_code"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Simplified: user_id is now the access_code, check directly
            cursor.execute('''
                SELECT consent_accepted
                FROM user_consents
                WHERE access_code = ?
            ''', (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return bool(row[0])
            else:
                return False

        except Exception as e:
            logger.error(f"Error checking user consent: {e}")
            return False

    def get_user_flag_count(self, user_id: str, days: int = 7) -> int:
        """Get the number of flags for a user in the last N days from SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*)
                FROM flagged_chats
                WHERE access_code = ?
                AND timestamp >= datetime('now', '-' || ? || ' days')
            ''', (user_id, days))

            row = cursor.fetchone()
            conn.close()

            return row[0] if row else 0

        except Exception as e:
            logger.error(f"Error getting user flag count: {e}")
            return 0

    def should_restrict_user(self, user_id: str, max_flags: int = 3, days: int = 7) -> bool:
        """Check if user should be restricted based on flag count from SQLite"""
        try:
            flag_count = self.get_user_flag_count(user_id, days)
            logger.info(f"User {user_id} has {flag_count} flags in the last {days} days")

            if flag_count >= max_flags:
                logger.warning(f"User {user_id} has reached flag limit ({flag_count}/{max_flags})")
                # Deactivate the access code
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE access_codes
                    SET is_active = FALSE
                    WHERE code = ?
                ''', (user_id,))
                conn.commit()
                conn.close()
                logger.info(f"Access code {user_id} has been deactivated due to excessive flags")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking if user should be restricted: {e}")
            return False

    def save_user_consent(self, user_id: str, access_code: str, consent_accepted: bool) -> bool:
        """Save user's consent decision to SQLite (by access_code)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if consent already exists for this access_code
            cursor.execute('''
                SELECT id FROM user_consents WHERE access_code = ?
            ''', (access_code,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing consent
                cursor.execute('''
                    UPDATE user_consents 
                    SET consent_accepted = ?,
                        user_id = ?,
                        consent_timestamp = CURRENT_TIMESTAMP
                    WHERE access_code = ?
                ''', (consent_accepted, user_id, access_code))
            else:
                # Insert new consent
                cursor.execute('''
                    INSERT INTO user_consents (user_id, access_code, consent_accepted)
                    VALUES (?, ?, ?)
                ''', (user_id, access_code, consent_accepted))

            conn.commit()
            conn.close()
            logger.info(f"Saved consent for access_code {access_code}: {consent_accepted}")
            return True

        except Exception as e:
            logger.error(f"Error saving user consent: {e}")
            return False

    def update_streak(self, user_id: str, access_code: str) -> bool:
        """Update user's streak for today"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get today's date in India timezone
            today = get_india_today().isoformat()
            
            # Check if entry exists for today
            cursor.execute('''
                SELECT message_count FROM streak_tracking
                WHERE user_id = ? AND activity_date = ?
            ''', (user_id, today))
            
            existing = cursor.fetchone()
            
            if existing:
                # Increment message count for today
                cursor.execute('''
                    UPDATE streak_tracking
                    SET message_count = message_count + 1,
                        timestamp = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND activity_date = ?
                ''', (user_id, today))
            else:
                # Create new entry for today
                cursor.execute('''
                    INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count)
                    VALUES (?, ?, ?, 1)
                ''', (user_id, access_code, today))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating streak: {e}")
            return False

    def get_streak_data(self, user_id: str) -> Dict[str, Any]:
        """Get user's streak information including current streak and weekly activity"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get all activity dates for this user, ordered by date desc
            cursor.execute('''
                SELECT activity_date, message_count, is_freeze
                FROM streak_tracking
                WHERE user_id = ?
                ORDER BY activity_date DESC
            ''', (user_id,))

            activity_records = cursor.fetchall()
            conn.close()

            if not activity_records:
                return {
                    'current_streak': 0,
                    'longest_streak': 0,
                    'total_days': 0,
                    'weekly_activity': {},
                    'frozen_days': {},
                    'has_activity_today': False
                }

            # Calculate current streak
            current_streak = 0
            today = get_india_today()
            from datetime import timedelta
            check_date = today

            # Parse records: only count days with 5+ messages OR frozen days
            # activity_dates = days that count toward streak (5+ messages or frozen)
            activity_dates = [datetime.fromisoformat(record[0]).date() for record in activity_records
                            if record[1] >= 5 or record[2]]  # message_count >= 5 OR is_freeze
            frozen_days_set = {datetime.fromisoformat(record[0]).date() for record in activity_records if record[2]}
            
            # Check if they have activity today or yesterday (for streak continuation)
            has_activity_today = today in activity_dates
            yesterday = today - timedelta(days=1)
            has_activity_yesterday = yesterday in activity_dates
            
            # Calculate current streak
            # Start from today if they have activity, otherwise start from yesterday if they have activity there
            # This gives users until end of day to maintain their streak
            check_date = today
            if not has_activity_today and has_activity_yesterday:
                # They haven't posted today yet, but posted yesterday - streak is still alive
                check_date = yesterday
            elif not has_activity_today and not has_activity_yesterday:
                # No activity today or yesterday - streak is broken
                current_streak = 0
                check_date = None
            
            # Count consecutive days backwards
            while check_date and check_date in activity_dates:
                current_streak += 1
                check_date = check_date - timedelta(days=1)
            
            # Calculate longest streak
            longest_streak = 0
            temp_streak = 1
            
            for i in range(len(activity_dates) - 1):
                days_diff = (activity_dates[i] - activity_dates[i + 1]).days
                if days_diff == 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            
            longest_streak = max(longest_streak, temp_streak, current_streak)
            
            # Get weekly activity (current week: Monday to Sunday)
            from datetime import timedelta
            weekly_activity = {}
            frozen_days = {}
            
            # Find Monday of current week
            current_day_of_week = today.weekday()  # Monday = 0, Sunday = 6
            monday = today - timedelta(days=current_day_of_week)
            
            # Generate dates for Monday through Sunday of current week
            for i in range(7):
                day = monday + timedelta(days=i)
                day_str = day.isoformat()
                weekly_activity[day_str] = day in activity_dates
                frozen_days[day_str] = day in frozen_days_set
            
            return {
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'total_days': len(activity_dates),
                'weekly_activity': weekly_activity,
                'frozen_days': frozen_days,
                'has_activity_today': has_activity_today
            }
            
        except Exception as e:
            logger.error(f"Error getting streak data: {e}")
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_days': 0,
                'weekly_activity': {},
                'frozen_days': {},
                'has_activity_today': False,
                'error': str(e)
            }

    def freeze_streak(self, user_id: str, access_code: str, freeze_date: str) -> Dict[str, Any]:
        """Freeze the streak for a specific date (max 1 per week)"""
        try:
            from datetime import datetime, timedelta
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get Monday of current week (in India timezone)
            today = get_india_today()
            current_day_of_week = today.weekday()
            monday = today - timedelta(days=current_day_of_week)
            sunday = monday + timedelta(days=6)
            
            # Check how many freezes used this week
            cursor.execute('''
                SELECT COUNT(*) FROM streak_tracking
                WHERE user_id = ? AND is_freeze = 1
                AND activity_date >= ? AND activity_date <= ?
            ''', (user_id, monday.isoformat(), sunday.isoformat()))
            
            freeze_count = cursor.fetchone()[0]
            
            if freeze_count >= 1:
                conn.close()
                return {
                    'success': False,
                    'error': 'You have already used your freeze for this week'
                }
            
            # Parse the freeze date
            freeze_date_obj = datetime.fromisoformat(freeze_date).date()
            
            # Check if trying to freeze a future date beyond today
            if freeze_date_obj > today:
                conn.close()
                return {
                    'success': False,
                    'error': 'Cannot freeze future dates'
                }
            
            # Check if this date already has activity
            cursor.execute('''
                SELECT message_count, is_freeze FROM streak_tracking
                WHERE user_id = ? AND activity_date = ?
            ''', (user_id, freeze_date))
            
            existing = cursor.fetchone()
            
            if existing and existing[0] > 0:
                conn.close()
                return {
                    'success': False,
                    'error': 'Cannot freeze a day you already have activity on'
                }
            
            if existing and existing[1]:
                conn.close()
                return {
                    'success': False,
                    'error': 'This day is already frozen'
                }
            
            # Create freeze entry
            cursor.execute('''
                INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count, is_freeze)
                VALUES (?, ?, ?, 0, 1)
                ON CONFLICT(user_id, activity_date)
                DO UPDATE SET is_freeze = 1
            ''', (user_id, access_code, freeze_date))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Streak frozen successfully!',
                'freeze_date': freeze_date
            }
            
        except Exception as e:
            logger.error(f"Error freezing streak: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_freeze_status(self, user_id: str) -> Dict[str, Any]:
        """Get information about user's freeze usage this week"""
        try:
            from datetime import datetime, timedelta
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get Monday and Sunday of current week (in India timezone)
            today = get_india_today()
            current_day_of_week = today.weekday()
            monday = today - timedelta(days=current_day_of_week)
            sunday = monday + timedelta(days=6)
            
            # Count freezes used this week
            cursor.execute('''
                SELECT COUNT(*), activity_date FROM streak_tracking
                WHERE user_id = ? AND is_freeze = 1
                AND activity_date >= ? AND activity_date <= ?
                GROUP BY activity_date
            ''', (user_id, monday.isoformat(), sunday.isoformat()))
            
            freeze_records = cursor.fetchall()
            conn.close()
            
            freezes_used = len(freeze_records)
            freeze_dates = [record[1] for record in freeze_records] if freeze_records else []
            
            return {
                'freezes_available': 1 - freezes_used,
                'freezes_used': freezes_used,
                'freeze_dates': freeze_dates,
                'can_freeze': freezes_used < 1
            }
            
        except Exception as e:
            logger.error(f"Error getting freeze status: {e}")
            return {
                'freezes_available': 0,
                'freezes_used': 0,
                'freeze_dates': [],
                'can_freeze': False,
                'error': str(e)
            }

    def track_email_open(self, tracking_id: str, ip_address: str, user_agent: str) -> bool:
        """Track email open event - SQLite stub"""
        logger.warning("Email tracking not implemented for SQLite")
        return False

    def track_email_click(self, tracking_id: str, ip_address: str, user_agent: str) -> bool:
        """Track email link click event - SQLite stub"""
        logger.warning("Email tracking not implemented for SQLite")
        return False

    def close(self):
        """Close SQLite database connection"""
        # No persistent connection to close
        logger.info("SQLite database connection closed")

class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL implementation of the database interface"""

    def __init__(self, connection_string: str):
        try:
            import psycopg2
            from psycopg2 import pool
            from psycopg2 import extras
            from urllib.parse import urlparse, parse_qs

            self.psycopg2 = psycopg2  # Store module reference
            self.connection_string = connection_string
            self.db_type = "postgresql"

            # Parse connection string to add Supabase-specific parameters
            parsed = urlparse(connection_string)

            # Supabase Transaction pooler requires these settings
            if 'sslmode' not in parsed.query:
                if '?' in connection_string:
                    self.connection_string += '&sslmode=require'
                else:
                    self.connection_string += '?sslmode=require'

            logger.info("PostgreSQL: Initialized for Supabase with transaction pooling")

            # Test connection on init
            self._test_connection()

        except ImportError as e:
            logger.error(f"Failed to import psycopg2. Install with: pip install psycopg2-binary")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise

    def _test_connection(self):
        """Test database connection on initialization"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            self._return_connection(conn)
            logger.info("PostgreSQL: Connection test successful")
        except Exception as e:
            logger.error(f"PostgreSQL: Connection test failed: {e}")
            raise

    def _get_connection(self):
        """Create a fresh connection for each request (Supabase Transaction Mode handles pooling)"""
        try:
            conn = self.psycopg2.connect(
                self.connection_string,
                connect_timeout=5,  # 5 second connect timeout (Supabase recommendation)
                options='-c statement_timeout=10000 -c timezone=Asia/Kolkata'  # Set timezone to IST
            )
            # Autocommit=False for explicit transaction control
            conn.autocommit = False
            return conn
        except self.psycopg2.OperationalError as e:
            logger.error(f"PostgreSQL connection failed (check credentials/network): {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection: {e}")
            raise

    def _return_connection(self, conn):
        """Properly close the connection after use"""
        if conn and not conn.closed:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    def init_db(self):
        """Initialize PostgreSQL database and tables"""
        conn = None
        try:
            logger.info("PostgreSQL: Checking tables and creating if needed...")

            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if tables already exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'access_codes'
                )
            """)
            tables_exist = cursor.fetchone()[0]

            if tables_exist:
                logger.info("PostgreSQL: Tables already exist, skipping creation")
                cursor.close()
                self._return_connection(conn)
                return

            logger.info("PostgreSQL: Creating tables...")

            # Create all tables in a single transaction
            # Access codes table (must be first due to foreign keys)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_codes (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    user_type TEXT NOT NULL,
                    school_id TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    max_uses INTEGER DEFAULT 1,
                    current_uses INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_by TEXT
                )
            ''')

            # User accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id SERIAL PRIMARY KEY,
                    login_id TEXT UNIQUE NOT NULL,
                    access_code TEXT NOT NULL,
                    first_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Admin users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')

            # Chat messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'normal',
                    flag_type TEXT,
                    confidence REAL,
                    analysis TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Flagged chats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flagged_chats (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    access_code TEXT,
                    message TEXT NOT NULL,
                    flag_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    analysis TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')

            # Feelings tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feelings_tracking (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    feeling_score INTEGER NOT NULL CHECK (feeling_score >= 0 AND feeling_score <= 10),
                    date DATE NOT NULL DEFAULT CURRENT_DATE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code),
                    UNIQUE(access_code, date)
                )
            ''')

            # Conversation summaries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    summary_date DATE NOT NULL,
                    main_concerns TEXT,
                    emotional_patterns TEXT,
                    coping_strategies TEXT,
                    progress_notes TEXT,
                    important_context TEXT,
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, summary_date),
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # User consents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_consents (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    access_code TEXT NOT NULL,
                    consent_accepted BOOLEAN NOT NULL,
                    consent_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Chat sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_end TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    has_flagged_content BOOLEAN DEFAULT FALSE
                )
            ''')

            # Email tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_tracking (
                    id SERIAL PRIMARY KEY,
                    tracking_id TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    access_code TEXT,
                    campaign TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    opened_count INTEGER DEFAULT 1,
                    clicked_at TIMESTAMP,
                    click_ip_address TEXT,
                    click_user_agent TEXT,
                    click_count INTEGER DEFAULT 0
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_access_code ON chat_messages(access_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_flagged_chats_timestamp ON flagged_chats(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_flagged_chats_flag_type ON flagged_chats(flag_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feelings_tracking_date ON feelings_tracking(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_tracking_tracking_id ON email_tracking(tracking_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_tracking_email ON email_tracking(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_tracking_campaign ON email_tracking(campaign)')

            conn.commit()
            cursor.close()
            self._return_connection(conn)
            logger.info("PostgreSQL: Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing PostgreSQL database: {e}")
            if conn:
                try:
                    conn.rollback()
                    self._return_connection(conn)
                except:
                    pass
            raise
        
        # Original initialization code kept for reference but never runs
        conn = None
        try:
            logger.info("PostgreSQL: Checking if tables exist...")

            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if tables already exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'access_codes'
                )
            """)
            tables_exist = cursor.fetchone()[0]
            
            if tables_exist:
                logger.info("PostgreSQL: Tables already exist, skipping initialization")
                cursor.close()
                self._return_connection(conn)
                return
            
            logger.info("PostgreSQL: Tables not found, creating them...")
            cursor = conn.cursor()

            # Create comprehensive chat messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'normal',
                    flag_type TEXT,
                    confidence REAL,
                    analysis TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create flagged chats table (legacy - keep for compatibility)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flagged_chats (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    access_code TEXT,
                    message TEXT NOT NULL,
                    flag_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    analysis TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')

            # Create chat sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_end TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    has_flagged_content BOOLEAN DEFAULT FALSE
                )
            ''')

            # Create access codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_codes (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    user_type TEXT NOT NULL,
                    school_id TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    max_uses INTEGER DEFAULT 1,
                    current_uses INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_by TEXT
                )
            ''')

            # Create user accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id SERIAL PRIMARY KEY,
                    login_id TEXT UNIQUE NOT NULL,
                    access_code TEXT NOT NULL,
                    first_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Create admin users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')

            # Create feelings tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feelings_tracking (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    feeling_score INTEGER NOT NULL CHECK (feeling_score >= 0 AND feeling_score <= 10),
                    date DATE NOT NULL DEFAULT CURRENT_DATE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code),
                    UNIQUE(access_code, date)
                )
            ''')

            # Create conversation summaries table for long-term memory
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    access_code TEXT NOT NULL,
                    summary_date DATE NOT NULL,
                    main_concerns TEXT,
                    emotional_patterns TEXT,
                    coping_strategies TEXT,
                    progress_notes TEXT,
                    important_context TEXT,
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, summary_date),
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Create consent tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_consents (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    access_code TEXT NOT NULL,
                    consent_accepted BOOLEAN NOT NULL,
                    consent_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES access_codes (code)
                )
            ''')

            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_flagged_chats_timestamp ON flagged_chats(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_flagged_chats_reviewed ON flagged_chats(reviewed)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feelings_tracking_date ON feelings_tracking(date)')

            conn.commit()
            self._return_connection(conn)
            logger.info("PostgreSQL database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing PostgreSQL database: {e}")
            if conn:
                try:
                    conn.rollback()
                    self._return_connection(conn)
                except:
                    pass
            raise
    
    def log_flagged_chat(self, user_id: str, message: str, flag_type: str,
                        confidence: float, analysis: Dict[str, Any],
                        access_code: str = None, ip_address: str = None, user_agent: str = None) -> bool:
        """Log a flagged chat message to PostgreSQL"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flagged_chats
                (user_id, access_code, message, flag_type, confidence, analysis, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                access_code,
                message,
                flag_type,
                confidence,
                json.dumps(analysis),
                ip_address,
                user_agent
            ))

            conn.commit()
            cursor.close()
            logger.info(f"Flagged chat logged: {flag_type} for user {user_id}, access_code {access_code}")
            return True

        except Exception as e:
            logger.error(f"Error logging flagged chat: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            return False
        finally:
            self._return_connection(conn)
    
    def get_flagged_chats(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get flagged chats with pagination from PostgreSQL"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, access_code, message, flag_type, confidence, analysis,
                       timestamp, ip_address, user_agent
                FROM flagged_chats
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            ''', (limit, offset))

            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

            result = []
            for row in rows:
                chat_dict = dict(zip(columns, row))
                # Parse JSON analysis
                if chat_dict['analysis']:
                    try:
                        chat_dict['analysis'] = json.loads(chat_dict['analysis'])
                    except:
                        chat_dict['analysis'] = {}
                result.append(chat_dict)

            cursor.close()
            return result

        except Exception as e:
            logger.error(f"Error getting flagged chats: {e}")
            return []
        finally:
            self._return_connection(conn)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics from PostgreSQL"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Total flagged chats
            cursor.execute('SELECT COUNT(*) FROM flagged_chats')
            total_flagged = cursor.fetchone()[0]

            # Flag type breakdown
            cursor.execute('''
                SELECT flag_type, COUNT(*)
                FROM flagged_chats
                GROUP BY flag_type
            ''')
            flag_breakdown = dict(cursor.fetchall())

            # Recent activity (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM flagged_chats
                WHERE timestamp > NOW() - INTERVAL '1 day'
            ''')
            recent_24h = cursor.fetchone()[0]

            # Recent activity (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM flagged_chats
                WHERE timestamp > NOW() - INTERVAL '7 days'
            ''')
            recent_7d = cursor.fetchone()[0]

            cursor.close()
            return {
                'total_flagged': total_flagged,
                'flag_breakdown': flag_breakdown,
                'recent_24h': recent_24h,
                'recent_7d': recent_7d,
                'database_type': 'PostgreSQL'
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            import traceback
            traceback.print_exc()
            return {}
        finally:
            self._return_connection(conn)
    
    def validate_access_code(self, code: str) -> Dict[str, Any]:
        """Validate an access code and return its details"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # First check if code exists (regardless of is_active)
            cursor.execute('''
                SELECT code, user_type, school_id, is_active, max_uses, current_uses
                FROM access_codes
                WHERE code = %s
            ''', (code,))

            row = cursor.fetchone()
            self._return_connection(conn)

            if not row:
                # Code doesn't exist
                return {
                    'valid': False,
                    'error': 'Invalid access code'
                }

            # Code exists - extract details
            code_data = row[0]
            user_type = row[1]
            school_id = row[2]
            is_active = row[3]
            max_uses = row[4]
            current_uses = row[5]

            # Check if code is inactive (restricted)
            if not is_active:
                return {
                    'valid': False,
                    'restricted': True,
                    'error': 'This account has been temporarily restricted for safety reasons. A staff member will review your account and contact you if needed.'
                }

            # Check if code has reached max uses
            if current_uses >= max_uses:
                return {
                    'valid': False,
                    'error': 'Access code has reached maximum uses'
                }

            return {
                'code': code_data,
                'user_type': user_type,
                'school_id': school_id,
                'is_active': is_active,
                'max_uses': max_uses,
                'current_uses': current_uses,
                'valid': True
            }

        except Exception as e:
            logger.error(f"Error validating access code: {e}")
            return {'valid': False, 'error': str(e)}
    
    def create_user_account(self, access_code: str, login_id: str) -> bool:
        """Create a new user account"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Create user account
            cursor.execute('''
                INSERT INTO user_accounts (login_id, access_code)
                VALUES (%s, %s)
            ''', (login_id, access_code))

            # Update access code usage count
            cursor.execute('''
                UPDATE access_codes
                SET current_uses = current_uses + 1
                WHERE code = %s
            ''', (access_code,))

            conn.commit()
            self._return_connection(conn)
            logger.info(f"User account created: {login_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating user account: {e}")
            return False
    
    def get_user_by_login_id(self, login_id: str) -> Dict[str, Any]:
        """Get user account by login ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT ua.login_id, ua.access_code, ua.first_login, ua.last_active, ua.total_messages,
                       ac.user_type, ac.school_id
                FROM user_accounts ua
                JOIN access_codes ac ON ua.access_code = ac.code
                WHERE ua.login_id = %s AND ua.is_active = TRUE
            ''', (login_id,))

            row = cursor.fetchone()
            self._return_connection(conn)

            if row:
                return {
                    'login_id': row[0],
                    'access_code': row[1],
                    'first_login': row[2],
                    'last_active': row[3],
                    'total_messages': row[4],
                    'user_type': row[5],
                    'school_id': row[6]
                }
            return {}

        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return {}
    
    def update_user_activity(self, login_id: str) -> bool:
        """Update user's last activity timestamp"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE user_accounts
                SET last_active = CURRENT_TIMESTAMP
                WHERE login_id = %s
            ''', (login_id,))

            conn.commit()
            self._return_connection(conn)
            return True

        except Exception as e:
            logger.error(f"Error updating user activity: {e}")
            return False
    
    def get_access_code_stats(self) -> Dict[str, Any]:
        """Get statistics about access codes"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Total access codes
            cursor.execute('SELECT COUNT(*) FROM access_codes')
            total_codes = cursor.fetchone()[0]

            # Active codes
            cursor.execute('SELECT COUNT(*) FROM access_codes WHERE is_active = TRUE')
            active_codes = cursor.fetchone()[0]

            # Total users
            cursor.execute('SELECT COUNT(*) FROM user_accounts')
            total_users = cursor.fetchone()[0]

            # Recent users (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM user_accounts
                WHERE last_active >= NOW() - INTERVAL '7 days'
            ''')
            recent_users = cursor.fetchone()[0]

            self._return_connection(conn)

            return {
                'total_codes': total_codes,
                'active_codes': active_codes,
                'total_users': total_users,
                'recent_users': recent_users
            }

        except Exception as e:
            logger.error(f"Error getting access code stats: {e}")
            return {}
    
    def create_admin_user(self, username: str, password_hash: str) -> bool:
        """Create a new admin user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO admin_users (username, password_hash)
                VALUES (%s, %s)
            ''', (username, password_hash))

            conn.commit()
            self._return_connection(conn)
            logger.info(f"Admin user created: {username}")
            return True

        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            return False
    
    def validate_admin_login(self, username: str, password_hash: str) -> Dict[str, Any]:
        """Validate admin login credentials"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT username, is_active, created_at, last_login
                FROM admin_users
                WHERE username = %s AND password_hash = %s AND is_active = TRUE
            ''', (username, password_hash))

            row = cursor.fetchone()
            self._return_connection(conn)

            if row:
                return {
                    'username': row[0],
                    'is_active': row[1],
                    'created_at': row[2],
                    'last_login': row[3],
                    'valid': True
                }
            return {'valid': False}

        except Exception as e:
            logger.error(f"Error validating admin login: {e}")
            return {'valid': False, 'error': str(e)}
    
    def update_admin_last_login(self, username: str) -> bool:
        """Update admin's last login timestamp"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE admin_users
                SET last_login = CURRENT_TIMESTAMP
                WHERE username = %s
            ''', (username,))

            conn.commit()
            self._return_connection(conn)
            return True

        except Exception as e:
            logger.error(f"Error updating admin last login: {e}")
            return False

    def create_access_code(self, code: str, user_type: str, school_id: str, max_uses: int, created_by: str) -> bool:
        """Create a new access code"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO access_codes
                (code, user_type, school_id, is_active, max_uses, current_uses, created_at, created_by)
                VALUES (%s, %s, %s, TRUE, %s, 0, CURRENT_TIMESTAMP, %s)
            ''', (code, user_type, school_id, max_uses, created_by))

            conn.commit()
            self._return_connection(conn)
            logger.info(f"Access code created: {code}")
            return True

        except Exception as e:
            logger.error(f"Error creating access code: {e}")
            return False

    def get_all_access_codes(self) -> List[Dict[str, Any]]:
        """Get all access codes with their details"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT code, user_type, school_id, is_active, max_uses, current_uses, created_at, created_by
                FROM access_codes
                ORDER BY created_at DESC
            ''')

            rows = cursor.fetchall()
            self._return_connection(conn)

            access_codes = []
            for row in rows:
                access_codes.append({
                    'code': row[0],
                    'user_type': row[1],
                    'school_id': row[2],
                    'is_active': row[3],
                    'max_uses': row[4],
                    'current_uses': row[5],
                    'created_at': row[6],
                    'created_by': row[7]
                })

            return access_codes

        except Exception as e:
            logger.error(f"Error getting access codes: {e}")
            return []

    def update_access_code(self, code: str, is_active: bool = None, max_uses: int = None) -> bool:
        """Update access code properties"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            update_fields = []
            params = []

            if is_active is not None:
                update_fields.append("is_active = %s")
                params.append(is_active)

            if max_uses is not None:
                update_fields.append("max_uses = %s")
                params.append(max_uses)

            if not update_fields:
                return False

            params.append(code)

            cursor.execute(f'''
                UPDATE access_codes
                SET {', '.join(update_fields)}
                WHERE code = %s
            ''', params)

            conn.commit()
            self._return_connection(conn)
            logger.info(f"Access code updated: {code}")
            return True

        except Exception as e:
            logger.error(f"Error updating access code: {e}")
            return False

    def delete_access_code(self, code: str) -> bool:
        """Delete an access code (soft delete by setting inactive)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE access_codes
                SET is_active = FALSE
                WHERE code = %s
            ''', (code,))

            conn.commit()
            self._return_connection(conn)
            logger.info(f"Access code deleted: {code}")
            return True

        except Exception as e:
            logger.error(f"Error deleting access code: {e}")
            return False

    def save_chat_message(self, user_id: str, access_code: str, role: str, content: str,
                         session_id: str = None, message_type: str = "normal") -> bool:
        """Save a chat message to PostgreSQL database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO chat_messages
                (user_id, access_code, session_id, role, content, message_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, access_code, session_id, role, content, message_type))

            conn.commit()
            self._return_connection(conn)
            logger.info(f"Chat message saved: {role} message for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return False

    def get_chat_history(self, user_id: str, limit: int = 50, session_id: str = None) -> List[Dict[str, Any]]:
        """Get chat history for a user from PostgreSQL - user_id is now the access_code"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if session_id:
                cursor.execute('''
                    SELECT id, user_id, access_code, role, content, message_type, timestamp
                    FROM chat_messages
                    WHERE user_id = %s AND session_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                ''', (user_id, session_id, limit))
            else:
                # Simplified: user_id is now the access_code, no join needed
                cursor.execute('''
                    SELECT id, user_id, access_code, role, content, message_type, timestamp
                    FROM chat_messages
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                ''', (user_id, limit))

            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

            result = []
            for row in rows:
                message_dict = dict(zip(columns, row))
                result.append(message_dict)

            self._return_connection(conn)

            # Reverse the order to get chronological order (oldest first)
            result.reverse()

            return result

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_all_chats(self, limit: int = 100, offset: int = 0,
                     access_code: str = None, flag_type: str = None) -> List[Dict[str, Any]]:
        """Get all chat messages with filtering options from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Build query with filters
            query = '''
                SELECT id, user_id, access_code, session_id, role, content,
                       message_type, flag_type, confidence, analysis, timestamp
                FROM chat_messages
                WHERE 1=1
            '''
            params = []

            if access_code:
                query += ' AND access_code = %s'
                params.append(access_code)

            if flag_type:
                query += ' AND flag_type = %s'
                params.append(flag_type)

            query += ' ORDER BY timestamp DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

            result = []
            for row in rows:
                message_dict = dict(zip(columns, row))
                # Parse JSON analysis if present
                if message_dict.get('analysis'):
                    try:
                        message_dict['analysis'] = json.loads(message_dict['analysis'])
                    except:
                        message_dict['analysis'] = {}
                result.append(message_dict)

            self._return_connection(conn)
            return result

        except Exception as e:
            logger.error(f"Error getting all chats: {e}")
            return []

    def cleanup_old_chats(self, days: int = 30) -> int:
        """Clean up old chat messages older than specified days from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM chat_messages
                WHERE timestamp < NOW() - INTERVAL '%s days'
            ''', (days,))

            deleted_count = cursor.rowcount
            conn.commit()
            self._return_connection(conn)

            logger.info(f"Cleaned up {deleted_count} old chat messages")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old chats: {e}")
            return 0
    
    def record_feeling(self, user_id: str, access_code: str, feeling_score: int) -> bool:
        """Record a user's daily feeling score (0-10) in PostgreSQL"""
        try:
            if not (0 <= feeling_score <= 10):
                logger.error(f"Invalid feeling score: {feeling_score}. Must be 0-10")
                return False

            conn = self._get_connection()
            cursor = conn.cursor()

            # Use INSERT ON CONFLICT to handle the case where access code already recorded today
            cursor.execute('''
                INSERT INTO feelings_tracking (user_id, access_code, feeling_score, date)
                VALUES (%s, %s, %s, CURRENT_DATE)
                ON CONFLICT (access_code, date)
                DO UPDATE SET feeling_score = EXCLUDED.feeling_score, user_id = EXCLUDED.user_id
            ''', (user_id, access_code, feeling_score))

            conn.commit()
            self._return_connection(conn)
            logger.info(f"Feeling recorded: {feeling_score}/10 for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error recording feeling: {e}")
            return False

    def get_feeling_for_today(self, user_id: str) -> Dict[str, Any]:
        """Get today's feeling record for a user from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Simplified: user_id IS the access_code
            cursor.execute('''
                SELECT id, feeling_score, date, timestamp, user_id, access_code
                FROM feelings_tracking
                WHERE access_code = %s AND date = CURRENT_DATE
                LIMIT 1
            ''', (user_id,))

            row = cursor.fetchone()
            self._return_connection(conn)

            if row:
                return {
                    'id': row[0],
                    'feeling_score': row[1],
                    'date': row[2],
                    'timestamp': row[3],
                    'user_id': row[4],
                    'access_code': row[5],
                    'recorded_today': True
                }
            else:
                return {'recorded_today': False}

        except Exception as e:
            logger.error(f"Error getting today's feeling: {e}")
            return {'recorded_today': False}

    def get_user_feeling_history(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user's feeling history for the last N days from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, feeling_score, date, timestamp
                FROM feelings_tracking
                WHERE access_code = (
                    SELECT access_code FROM user_accounts WHERE login_id = %s
                ) AND date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY date DESC
            ''', (user_id, days))

            rows = cursor.fetchall()
            self._return_connection(conn)

            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'feeling_score': row[1],
                    'date': row[2],
                    'timestamp': row[3]
                })

            return history

        except Exception as e:
            logger.error(f"Error getting feeling history: {e}")
            return []

    def save_conversation_summary(self, user_id: str, access_code: str, summary_date: str,
                                  main_concerns: str = None, emotional_patterns: str = None,
                                  coping_strategies: str = None, progress_notes: str = None,
                                  important_context: str = None, message_count: int = 0) -> bool:
        """Save or update a conversation summary to PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Use INSERT ON CONFLICT to update if exists
            cursor.execute('''
                INSERT INTO conversation_summaries
                (user_id, access_code, summary_date, main_concerns, emotional_patterns,
                 coping_strategies, progress_notes, important_context, message_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, summary_date)
                DO UPDATE SET
                    main_concerns = EXCLUDED.main_concerns,
                    emotional_patterns = EXCLUDED.emotional_patterns,
                    coping_strategies = EXCLUDED.coping_strategies,
                    progress_notes = EXCLUDED.progress_notes,
                    important_context = EXCLUDED.important_context,
                    message_count = EXCLUDED.message_count,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, access_code, summary_date, main_concerns, emotional_patterns,
                  coping_strategies, progress_notes, important_context, message_count))

            conn.commit()
            self._return_connection(conn)
            logger.info(f"Saved conversation summary for user {user_id} on {summary_date}")
            return True

        except Exception as e:
            logger.error(f"Error saving conversation summary: {e}")
            return False

    def get_conversation_summaries(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get conversation summaries for the last N days from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, user_id, summary_date, main_concerns, emotional_patterns,
                       coping_strategies, progress_notes, important_context,
                       message_count, created_at, updated_at
                FROM conversation_summaries
                WHERE user_id = %s AND summary_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY summary_date DESC
            ''', (user_id, days))

            rows = cursor.fetchall()
            self._return_connection(conn)

            summaries = []
            for row in rows:
                summaries.append({
                    'id': row[0],
                    'user_id': row[1],
                    'summary_date': row[2],
                    'main_concerns': row[3],
                    'emotional_patterns': row[4],
                    'coping_strategies': row[5],
                    'progress_notes': row[6],
                    'important_context': row[7],
                    'message_count': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                })

            return summaries

        except Exception as e:
            logger.error(f"Error getting conversation summaries: {e}")
            return []

    def get_latest_summary(self, user_id: str) -> Dict[str, Any]:
        """Get the most recent conversation summary for a user from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, user_id, summary_date, main_concerns, emotional_patterns,
                       coping_strategies, progress_notes, important_context,
                       message_count, created_at, updated_at
                FROM conversation_summaries
                WHERE user_id = %s
                ORDER BY summary_date DESC
                LIMIT 1
            ''', (user_id,))

            row = cursor.fetchone()
            self._return_connection(conn)

            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'summary_date': row[2],
                    'main_concerns': row[3],
                    'emotional_patterns': row[4],
                    'coping_strategies': row[5],
                    'progress_notes': row[6],
                    'important_context': row[7],
                    'message_count': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                }
            else:
                return {}

        except Exception as e:
            logger.error(f"Error getting latest summary: {e}")
            return {}

    def check_user_consent(self, user_id: str) -> bool:
        """Check if user has given consent from PostgreSQL - user_id is now the access_code"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Simplified: user_id is now the access_code, check directly
            cursor.execute('''
                SELECT consent_accepted
                FROM user_consents
                WHERE access_code = %s
            ''', (user_id,))

            row = cursor.fetchone()
            cursor.close()

            if row:
                return bool(row[0])
            else:
                return False

        except Exception as e:
            logger.error(f"Error checking user consent: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self._return_connection(conn)

    def get_user_flag_count(self, user_id: str, days: int = 7) -> int:
        """Get the number of flags for a user in the last N days from PostgreSQL"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*)
                FROM flagged_chats
                WHERE access_code = %s
                AND timestamp >= NOW() - INTERVAL '%s days'
            ''', (user_id, days))

            row = cursor.fetchone()
            cursor.close()

            return row[0] if row else 0

        except Exception as e:
            logger.error(f"Error getting user flag count: {e}")
            return 0
        finally:
            self._return_connection(conn)

    def should_restrict_user(self, user_id: str, max_flags: int = 3, days: int = 7) -> bool:
        """Check if user should be restricted based on flag count from PostgreSQL"""
        conn = None
        try:
            flag_count = self.get_user_flag_count(user_id, days)
            logger.info(f"User {user_id} has {flag_count} flags in the last {days} days")

            if flag_count >= max_flags:
                logger.warning(f"User {user_id} has reached flag limit ({flag_count}/{max_flags})")
                # Deactivate the access code
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE access_codes
                    SET is_active = FALSE
                    WHERE code = %s
                ''', (user_id,))
                conn.commit()
                cursor.close()
                logger.info(f"Access code {user_id} has been deactivated due to excessive flags")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking if user should be restricted: {e}")
            return False
        finally:
            if conn:
                self._return_connection(conn)

    def save_user_consent(self, user_id: str, access_code: str, consent_accepted: bool) -> bool:
        """Save user's consent decision to PostgreSQL (by access_code)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Use INSERT ON CONFLICT to update if exists
            cursor.execute('''
                INSERT INTO user_consents (user_id, access_code, consent_accepted)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    consent_accepted = EXCLUDED.consent_accepted,
                    consent_timestamp = CURRENT_TIMESTAMP
            ''', (user_id, access_code, consent_accepted))

            conn.commit()
            self._return_connection(conn)
            logger.info(f"Saved consent for access_code {access_code}: {consent_accepted}")
            return True

        except Exception as e:
            logger.error(f"Error saving user consent: {e}")
            return False

    def update_streak(self, user_id: str, access_code: str) -> bool:
        """Update user's streak for today"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get today's date in India timezone
            today = get_india_today().isoformat()
            
            # Use INSERT ON CONFLICT to update if exists
            cursor.execute('''
                INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT (user_id, activity_date)
                DO UPDATE SET
                    message_count = streak_tracking.message_count + 1,
                    timestamp = CURRENT_TIMESTAMP
            ''', (user_id, access_code, today))
            
            conn.commit()
            self._return_connection(conn)
            return True
            
        except Exception as e:
            logger.error(f"Error updating streak: {e}")
            return False

    def get_streak_data(self, user_id: str) -> Dict[str, Any]:
        """Get user's streak information including current streak and weekly activity"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all activity dates for this user, ordered by date desc
            cursor.execute('''
                SELECT activity_date, message_count, is_freeze
                FROM streak_tracking
                WHERE user_id = %s
                ORDER BY activity_date DESC
            ''', (user_id,))
            
            activity_records = cursor.fetchall()
            self._return_connection(conn)
            
            if not activity_records:
                return {
                    'current_streak': 0,
                    'longest_streak': 0,
                    'total_days': 0,
                    'weekly_activity': {},
                    'frozen_days': {},
                    'has_activity_today': False
                }
            
            # Calculate current streak
            current_streak = 0
            today = get_india_today()

            # Parse records: only count days with 5+ messages OR frozen days
            # activity_dates = days that count toward streak (5+ messages or frozen)
            activity_dates = [record[0] if isinstance(record[0], datetime) else datetime.fromisoformat(str(record[0])).date()
                            for record in activity_records if record[1] >= 5 or record[2]]  # message_count >= 5 OR is_freeze
            frozen_days_set = {(record[0] if isinstance(record[0], datetime) else datetime.fromisoformat(str(record[0])).date()) for record in activity_records if record[2]}
            
            # Check if they have activity today
            has_activity_today = today in activity_dates
            
            # Calculate current streak
            # Start from today if they have activity, otherwise start from yesterday if they have activity there
            # This gives users until end of day to maintain their streak
            from datetime import timedelta
            yesterday = today - timedelta(days=1)
            has_activity_yesterday = yesterday in activity_dates
            
            check_date = today
            if not has_activity_today and has_activity_yesterday:
                # They haven't posted today yet, but posted yesterday - streak is still alive
                check_date = yesterday
            elif not has_activity_today and not has_activity_yesterday:
                # No activity today or yesterday - streak is broken
                current_streak = 0
                check_date = None
            
            # Count consecutive days backwards
            while check_date and check_date in activity_dates:
                current_streak += 1
                check_date = check_date - timedelta(days=1)
            
            # Calculate longest streak
            longest_streak = 0
            temp_streak = 1
            
            for i in range(len(activity_dates) - 1):
                days_diff = (activity_dates[i] - activity_dates[i + 1]).days
                if days_diff == 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            
            longest_streak = max(longest_streak, temp_streak, current_streak)
            
            # Get weekly activity (current week: Monday to Sunday)
            weekly_activity = {}
            frozen_days = {}
            
            # Find Monday of current week
            current_day_of_week = today.weekday()  # Monday = 0, Sunday = 6
            monday = today - timedelta(days=current_day_of_week)
            
            # Generate dates for Monday through Sunday of current week
            for i in range(7):
                day = monday + timedelta(days=i)
                day_str = day.isoformat()
                weekly_activity[day_str] = day in activity_dates
                frozen_days[day_str] = day in frozen_days_set
            
            return {
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'total_days': len(activity_dates),
                'weekly_activity': weekly_activity,
                'frozen_days': frozen_days,
                'has_activity_today': has_activity_today
            }
            
        except Exception as e:
            logger.error(f"Error getting streak data: {e}")
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_days': 0,
                'weekly_activity': {},
                'frozen_days': {},
                'has_activity_today': False,
                'error': str(e)
            }

    def freeze_streak(self, user_id: str, access_code: str, freeze_date: str) -> Dict[str, Any]:
        """Freeze the streak for a specific date (max 1 per week)"""
        try:
            from datetime import datetime, timedelta
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get Monday of current week (in India timezone)
            today = get_india_today()
            current_day_of_week = today.weekday()
            monday = today - timedelta(days=current_day_of_week)
            sunday = monday + timedelta(days=6)
            
            # Check how many freezes used this week
            cursor.execute('''
                SELECT COUNT(*) FROM streak_tracking
                WHERE user_id = %s AND is_freeze = TRUE
                AND activity_date >= %s AND activity_date <= %s
            ''', (user_id, monday.isoformat(), sunday.isoformat()))
            
            freeze_count = cursor.fetchone()[0]
            
            if freeze_count >= 1:
                cursor.close()
                self._return_connection(conn)
                return {
                    'success': False,
                    'error': 'You have already used your freeze for this week'
                }
            
            # Parse the freeze date
            freeze_date_obj = datetime.fromisoformat(freeze_date).date()
            
            # Check if trying to freeze a future date beyond today
            if freeze_date_obj > today:
                cursor.close()
                self._return_connection(conn)
                return {
                    'success': False,
                    'error': 'Cannot freeze future dates'
                }
            
            # Check if this date already has activity
            cursor.execute('''
                SELECT message_count, is_freeze FROM streak_tracking
                WHERE user_id = %s AND activity_date = %s
            ''', (user_id, freeze_date))
            
            existing = cursor.fetchone()
            
            if existing and existing[0] > 0:
                cursor.close()
                self._return_connection(conn)
                return {
                    'success': False,
                    'error': 'Cannot freeze a day you already have activity on'
                }
            
            if existing and existing[1]:
                cursor.close()
                self._return_connection(conn)
                return {
                    'success': False,
                    'error': 'This day is already frozen'
                }
            
            # Create freeze entry
            cursor.execute('''
                INSERT INTO streak_tracking (user_id, access_code, activity_date, message_count, is_freeze)
                VALUES (%s, %s, %s, 0, TRUE)
                ON CONFLICT (user_id, activity_date)
                DO UPDATE SET is_freeze = TRUE
            ''', (user_id, access_code, freeze_date))
            
            conn.commit()
            cursor.close()
            self._return_connection(conn)
            
            return {
                'success': True,
                'message': 'Streak frozen successfully!',
                'freeze_date': freeze_date
            }
            
        except Exception as e:
            logger.error(f"Error freezing streak: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_freeze_status(self, user_id: str) -> Dict[str, Any]:
        """Get information about user's freeze usage this week"""
        try:
            from datetime import datetime, timedelta
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get Monday and Sunday of current week (in India timezone)
            today = get_india_today()
            current_day_of_week = today.weekday()
            monday = today - timedelta(days=current_day_of_week)
            sunday = monday + timedelta(days=6)
            
            # Count freezes used this week
            cursor.execute('''
                SELECT COUNT(*), activity_date FROM streak_tracking
                WHERE user_id = %s AND is_freeze = TRUE
                AND activity_date >= %s AND activity_date <= %s
                GROUP BY activity_date
            ''', (user_id, monday.isoformat(), sunday.isoformat()))
            
            freeze_records = cursor.fetchall()
            cursor.close()
            self._return_connection(conn)
            
            freezes_used = len(freeze_records)
            freeze_dates = [str(record[1]) for record in freeze_records] if freeze_records else []
            
            return {
                'freezes_available': 1 - freezes_used,
                'freezes_used': freezes_used,
                'freeze_dates': freeze_dates,
                'can_freeze': freezes_used < 1
            }
            
        except Exception as e:
            logger.error(f"Error getting freeze status: {e}")
            return {
                'freezes_available': 0,
                'freezes_used': 0,
                'freeze_dates': [],
                'can_freeze': False,
                'error': str(e)
            }

    def track_email_open(self, tracking_id: str, ip_address: str, user_agent: str) -> bool:
        """Track email open event"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if tracking_id exists and update
            cursor.execute("""
                UPDATE email_tracking
                SET opened_count = opened_count + 1,
                    opened_at = CURRENT_TIMESTAMP,
                    ip_address = %s,
                    user_agent = %s
                WHERE tracking_id = %s
            """, (ip_address, user_agent, tracking_id))

            rows_affected = cursor.rowcount
            conn.commit()
            cursor.close()
            self._return_connection(conn)

            return rows_affected > 0

        except Exception as e:
            logger.error(f"Error tracking email open: {e}")
            return False

    def track_email_click(self, tracking_id: str, ip_address: str, user_agent: str) -> bool:
        """Track email link click event"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Update click tracking
            cursor.execute("""
                UPDATE email_tracking
                SET click_count = COALESCE(click_count, 0) + 1,
                    clicked_at = CURRENT_TIMESTAMP,
                    click_ip_address = %s,
                    click_user_agent = %s
                WHERE tracking_id = %s
            """, (ip_address, user_agent, tracking_id))

            rows_affected = cursor.rowcount
            conn.commit()
            cursor.close()
            self._return_connection(conn)

            return rows_affected > 0

        except Exception as e:
            logger.error(f"Error tracking email click: {e}")
            return False

    def close(self):
        """Close PostgreSQL database connection pool"""
        try:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connection pool: {e}")

class DatabaseManager:
    """Database manager that handles switching between database types"""
    
    def __init__(self, db_type: str = "sqlite", **kwargs):
        self.db_type = db_type.lower()
        self.database = None
        
        if self.db_type == "sqlite":
            db_path = kwargs.get('db_path', 'mental_health_bot.db')
            self.database = SQLiteDatabase(db_path)
        elif self.db_type == "postgresql":
            connection_string = kwargs.get('connection_string')
            if not connection_string:
                raise ValueError("PostgreSQL requires connection_string parameter")
            self.database = PostgreSQLDatabase(connection_string)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        # Ensure the database is properly initialized
        if self.database:
            self.database.init_db()
    
    def log_flagged_chat(self, user_id: str, message: str, flag_type: str,
                        confidence: float, analysis: Dict[str, Any],
                        access_code: str = None, ip_address: str = None, user_agent: str = None) -> bool:
        """Log a flagged chat message"""
        try:
            logger.info(f"DatabaseManager: Logging flagged chat via {self.db_type} database")
            result = self.database.log_flagged_chat(
                user_id, message, flag_type, confidence, analysis, access_code, ip_address, user_agent
            )
            logger.info(f"DatabaseManager: Logging result: {result}")
            return result
        except Exception as e:
            logger.error(f"DatabaseManager: Error in log_flagged_chat: {e}")
            return False
    
    def get_flagged_chats(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get flagged chats with pagination"""
        return self.database.get_flagged_chats(limit, offset)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.database.get_stats()
    
    def validate_access_code(self, code: str) -> Dict[str, Any]:
        """Validate an access code and return its details"""
        return self.database.validate_access_code(code)
    
    def create_user_account(self, access_code: str, login_id: str) -> bool:
        """Create a new user account"""
        return self.database.create_user_account(access_code, login_id)
    
    def get_user_by_login_id(self, login_id: str) -> Dict[str, Any]:
        """Get user account by login ID"""
        return self.database.get_user_by_login_id(login_id)
    
    def update_user_activity(self, login_id: str) -> bool:
        """Update user's last activity timestamp"""
        return self.database.update_user_activity(login_id)
    
    def get_access_code_stats(self) -> Dict[str, Any]:
        """Get statistics about access codes"""
        return self.database.get_access_code_stats()
    
    def create_admin_user(self, username: str, password_hash: str) -> bool:
        """Create a new admin user"""
        return self.database.create_admin_user(username, password_hash)
    
    def validate_admin_login(self, username: str, password_hash: str) -> Dict[str, Any]:
        """Validate admin login credentials"""
        return self.database.validate_admin_login(username, password_hash)
    
    def update_admin_last_login(self, username: str) -> bool:
        """Update admin's last login timestamp"""
        return self.database.update_admin_last_login(username)

    def create_access_code(self, code: str, user_type: str, school_id: str, max_uses: int, created_by: str) -> bool:
        """Create a new access code"""
        return self.database.create_access_code(code, user_type, school_id, max_uses, created_by)

    def get_all_access_codes(self) -> List[Dict[str, Any]]:
        """Get all access codes with their details"""
        return self.database.get_all_access_codes()

    def update_access_code(self, code: str, is_active: bool = None, max_uses: int = None) -> bool:
        """Update access code properties"""
        return self.database.update_access_code(code, is_active, max_uses)

    def delete_access_code(self, code: str) -> bool:
        """Delete an access code (soft delete by setting inactive)"""
        return self.database.delete_access_code(code)

    def save_chat_message(self, user_id: str, access_code: str, role: str, content: str,
                         session_id: str = None, message_type: str = "normal") -> bool:
        """Save a chat message to database"""
        return self.database.save_chat_message(user_id, access_code, role, content, session_id, message_type)

    def get_chat_history(self, user_id: str, limit: int = 50, session_id: str = None) -> List[Dict[str, Any]]:
        """Get chat history for a user"""
        return self.database.get_chat_history(user_id, limit, session_id)

    def get_all_chats(self, limit: int = 100, offset: int = 0,
                     access_code: str = None, flag_type: str = None) -> List[Dict[str, Any]]:
        """Get all chat messages with filtering options"""
        return self.database.get_all_chats(limit, offset, access_code, flag_type)

    def cleanup_old_chats(self, days: int = 30) -> int:
        """Clean up old chat messages older than specified days"""
        return self.database.cleanup_old_chats(days)

    def record_feeling(self, user_id: str, access_code: str, feeling_score: int) -> bool:
        """Record a user's daily feeling score (0-10)"""
        return self.database.record_feeling(user_id, access_code, feeling_score)

    def get_feeling_for_today(self, user_id: str) -> Dict[str, Any]:
        """Get today's feeling record for a user"""
        return self.database.get_feeling_for_today(user_id)

    def get_user_feeling_history(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user's feeling history for the last N days"""
        return self.database.get_user_feeling_history(user_id, days)

    def save_conversation_summary(self, user_id: str, access_code: str, summary_date: str,
                                  main_concerns: str = None, emotional_patterns: str = None,
                                  coping_strategies: str = None, progress_notes: str = None,
                                  important_context: str = None, message_count: int = 0) -> bool:
        """Save or update a conversation summary"""
        return self.database.save_conversation_summary(
            user_id, access_code, summary_date, main_concerns, emotional_patterns,
            coping_strategies, progress_notes, important_context, message_count
        )

    def get_conversation_summaries(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get conversation summaries for the last N days"""
        return self.database.get_conversation_summaries(user_id, days)

    def get_latest_summary(self, user_id: str) -> Dict[str, Any]:
        """Get the most recent conversation summary for a user"""
        return self.database.get_latest_summary(user_id)

    def check_user_consent(self, user_id: str) -> bool:
        """Check if user has given consent"""
        return self.database.check_user_consent(user_id)

    def get_user_flag_count(self, user_id: str, days: int = 7) -> int:
        """Get the number of flags for a user in the last N days"""
        return self.database.get_user_flag_count(user_id, days)

    def should_restrict_user(self, user_id: str, max_flags: int = 3, days: int = 7) -> bool:
        """Check if user should be restricted based on flag count"""
        return self.database.should_restrict_user(user_id, max_flags, days)

    def save_user_consent(self, user_id: str, access_code: str, consent_accepted: bool) -> bool:
        """Save user's consent decision"""
        return self.database.save_user_consent(user_id, access_code, consent_accepted)

    def update_streak(self, user_id: str, access_code: str) -> bool:
        """Update user's streak for today"""
        return self.database.update_streak(user_id, access_code)

    def get_streak_data(self, user_id: str) -> Dict[str, Any]:
        """Get user's streak information including current streak and weekly activity"""
        return self.database.get_streak_data(user_id)

    def freeze_streak(self, user_id: str, access_code: str, freeze_date: str) -> Dict[str, Any]:
        """Freeze the streak for a specific date (max 1 per week)"""
        return self.database.freeze_streak(user_id, access_code, freeze_date)

    def get_freeze_status(self, user_id: str) -> Dict[str, Any]:
        """Get information about user's freeze usage this week"""
        return self.database.get_freeze_status(user_id)

    def track_email_open(self, tracking_id: str, ip_address: str, user_agent: str) -> bool:
        """Track email open event"""
        return self.database.track_email_open(tracking_id, ip_address, user_agent)

    def track_email_click(self, tracking_id: str, ip_address: str, user_agent: str) -> bool:
        """Track email link click event"""
        return self.database.track_email_click(tracking_id, ip_address, user_agent)

    def close(self):
        """Close database connection"""
        if self.database:
            self.database.close()
    
    def switch_database(self, new_db_type: str, **kwargs):
        """Switch to a different database type"""
        if self.database:
            self.database.close()
        
        self.db_type = new_db_type.lower()
        if self.db_type == "sqlite":
            db_path = kwargs.get('db_path', 'mental_health_bot.db')
            self.database = SQLiteDatabase(db_path)
        elif self.db_type == "postgresql":
            connection_string = kwargs.get('connection_string')
            if not connection_string:
                raise ValueError("PostgreSQL requires connection_string parameter")
            self.database = PostgreSQLDatabase(connection_string)
        else:
            raise ValueError(f"Unsupported database type: {new_db_type}")
        
        logger.info(f"Switched to {new_db_type} database")

# Global database instance
db_manager = None

def init_database(db_type: str = "sqlite", **kwargs):
    """Initialize the global database manager"""
    global db_manager
    db_manager = DatabaseManager(db_type, **kwargs)
    return db_manager

def get_database():
    """Get the global database manager instance"""
    global db_manager
    if db_manager is None:
        # Default to SQLite if not initialized
        db_manager = init_database("sqlite")
    return db_manager 