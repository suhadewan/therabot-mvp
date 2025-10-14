#!/usr/bin/env python3
"""
Migrate database schema to Supabase PostgreSQL.
This script creates all necessary tables in your Supabase database.
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

def create_tables():
    """Create all tables in Supabase PostgreSQL"""
    
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return False
    
    try:
        print("🔌 Connecting to Supabase...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✓ Connected to Supabase!")
        print("\n📋 Creating tables...\n")
        
        # Access codes table
        print("Creating access_codes table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_codes (
                id SERIAL PRIMARY KEY,
                code VARCHAR(20) UNIQUE NOT NULL,
                user_type VARCHAR(20) NOT NULL,
                school_id VARCHAR(100),
                max_uses INTEGER DEFAULT 1,
                current_uses INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ access_codes")
        
        # User accounts table
        print("Creating user_accounts table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_accounts (
                id SERIAL PRIMARY KEY,
                login_id VARCHAR(100) UNIQUE NOT NULL,
                access_code VARCHAR(20) NOT NULL,
                first_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (access_code) REFERENCES access_codes (code)
            )
        ''')
        print("✓ user_accounts")
        
        # Chat messages table
        print("Creating chat_messages table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                access_code VARCHAR(20) NOT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(100),
                message_type VARCHAR(50) DEFAULT 'normal',
                FOREIGN KEY (access_code) REFERENCES access_codes (code)
            )
        ''')
        print("✓ chat_messages")
        
        # Flagged chats table
        print("Creating flagged_chats table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flagged_chats (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                flag_type VARCHAR(50) NOT NULL,
                confidence DECIMAL(5, 2),
                analysis JSONB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT,
                reviewed BOOLEAN DEFAULT FALSE
            )
        ''')
        print("✓ flagged_chats")
        
        # Admin users table
        print("Creating admin_users table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        print("✓ admin_users")
        
        # Feelings tracking table
        print("Creating feelings_tracking table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feelings_tracking (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                access_code VARCHAR(20) NOT NULL,
                feeling_score INTEGER NOT NULL,
                date DATE NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (access_code) REFERENCES access_codes (code),
                UNIQUE(access_code, date)
            )
        ''')
        print("✓ feelings_tracking")
        
        # Conversation summaries table
        print("Creating conversation_summaries table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                access_code VARCHAR(20) NOT NULL,
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
        print("✓ conversation_summaries")
        
        # User consents table
        print("Creating user_consents table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_consents (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL UNIQUE,
                access_code VARCHAR(20) NOT NULL,
                consent_accepted BOOLEAN NOT NULL,
                consent_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (access_code) REFERENCES access_codes (code)
            )
        ''')
        print("✓ user_consents")
        
        # Create indexes
        print("\n📊 Creating indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_flagged_chats_timestamp ON flagged_chats(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_flagged_chats_reviewed ON flagged_chats(reviewed)')
        print("✓ Indexes created")
        
        # Verify tables
        print("\n🔍 Verifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\n✅ Successfully created {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Migration complete! Your Supabase database is ready.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Supabase Database Migration")
    print("=" * 60)
    print()
    
    success = create_tables()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Next Steps:")
        print("=" * 60)
        print("1. Create admin user: python3 create_admin_user.py")
        print("2. Create access codes: python3 create_access_codes.py")
        print("3. Start your app: python3 pwa_app.py")
        print()
    else:
        print("\n⚠️  Migration failed. Check your DATABASE_URL in .env file.")

