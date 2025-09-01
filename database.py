import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseInterface(ABC):
    """Abstract base class for database operations"""
    
    @abstractmethod
    def init_db(self):
        """Initialize database tables"""
        pass
    
    @abstractmethod
    def log_flagged_chat(self, user_id: str, message: str, flag_type: str, 
                        confidence: float, analysis: Dict[str, Any], 
                        ip_address: str = None, user_agent: str = None) -> bool:
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
            
            # Create flagged chats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flagged_chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
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
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_flagged_chats_timestamp 
                ON flagged_chats(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_flagged_chats_flag_type 
                ON flagged_chats(flag_type)
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
                        ip_address: str = None, user_agent: str = None) -> bool:
        """Log a flagged chat message to SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flagged_chats 
                (user_id, message, flag_type, confidence, analysis, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, 
                message, 
                flag_type, 
                confidence, 
                json.dumps(analysis), 
                ip_address, 
                user_agent
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Flagged chat logged: {flag_type} for user {user_id}")
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
                SELECT id, user_id, message, flag_type, confidence, analysis, 
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
            
            cursor.execute('''
                SELECT code, user_type, school_id, is_active, max_uses, current_uses, expires_at
                FROM access_codes 
                WHERE code = ? AND is_active = TRUE
            ''', (code,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'code': row[0],
                    'user_type': row[1],
                    'school_id': row[2],
                    'is_active': row[3],
                    'max_uses': row[4],
                    'current_uses': row[5],
                    'expires_at': row[6],
                    'valid': True
                }
            return {'valid': False}
            
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
    
    def close(self):
        """Close SQLite database connection"""
        # No persistent connection to close
        logger.info("SQLite database connection closed")

class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL implementation of the database interface"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
        # Note: PostgreSQL implementation would go here
        # For now, this is a placeholder for easy switching
        logger.info("PostgreSQL database initialized (placeholder)")
    
    def init_db(self):
        """Initialize PostgreSQL database and tables"""
        # PostgreSQL implementation would go here
        pass
    
    def log_flagged_chat(self, user_id: str, message: str, flag_type: str, 
                        confidence: float, analysis: Dict[str, Any], 
                        ip_address: str = None, user_agent: str = None) -> bool:
        """Log a flagged chat message to PostgreSQL"""
        # PostgreSQL implementation would go here
        pass
    
    def get_flagged_chats(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get flagged chats with pagination from PostgreSQL"""
        # PostgreSQL implementation would go here
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics from PostgreSQL"""
        # PostgreSQL implementation would go here
        pass
    
    def validate_access_code(self, code: str) -> Dict[str, Any]:
        """Validate an access code and return its details"""
        # PostgreSQL implementation would go here
        pass
    
    def create_user_account(self, access_code: str, login_id: str) -> bool:
        """Create a new user account"""
        # PostgreSQL implementation would go here
        pass
    
    def get_user_by_login_id(self, login_id: str) -> Dict[str, Any]:
        """Get user account by login ID"""
        # PostgreSQL implementation would go here
        pass
    
    def update_user_activity(self, login_id: str) -> bool:
        """Update user's last activity timestamp"""
        # PostgreSQL implementation would go here
        pass
    
    def get_access_code_stats(self) -> Dict[str, Any]:
        """Get statistics about access codes"""
        # PostgreSQL implementation would go here
        pass
    
    def create_admin_user(self, username: str, password_hash: str) -> bool:
        """Create a new admin user"""
        # PostgreSQL implementation would go here
        pass
    
    def validate_admin_login(self, username: str, password_hash: str) -> Dict[str, Any]:
        """Validate admin login credentials"""
        # PostgreSQL implementation would go here
        pass
    
    def update_admin_last_login(self, username: str) -> bool:
        """Update admin's last login timestamp"""
        # PostgreSQL implementation would go here
        pass
    
    def close(self):
        """Close PostgreSQL database connection"""
        # PostgreSQL implementation would go here
        pass

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
                        ip_address: str = None, user_agent: str = None) -> bool:
        """Log a flagged chat message"""
        try:
            logger.info(f"DatabaseManager: Logging flagged chat via {self.db_type} database")
            result = self.database.log_flagged_chat(
                user_id, message, flag_type, confidence, analysis, ip_address, user_agent
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