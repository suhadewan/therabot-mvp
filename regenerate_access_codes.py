#!/usr/bin/env python3
"""
Script to regenerate access codes for MindMitra with the new non-expiring system
"""

import sqlite3
from datetime import datetime

def regenerate_access_codes():
    """Regenerate access codes in the database with new non-expiring system"""
    
    # Connect to database
    conn = sqlite3.connect('mental_health_bot.db')
    cursor = conn.cursor()
    
    try:
        # First, clear existing access codes
        cursor.execute('DELETE FROM access_codes')
        print("🗑️  Cleared existing access codes")
        
        # New access codes (no expiration dates)
        new_codes = [
            {
                'code': 'STU001',
                'user_type': 'student',
                'school_id': 'delhi_high_school',
                'max_uses': 1
            },
            {
                'code': 'STU002',
                'user_type': 'student',
                'school_id': 'delhi_high_school',
                'max_uses': 1
            },
            {
                'code': 'STU003',
                'user_type': 'student',
                'school_id': 'mumbai_academy',
                'max_uses': 1
            },
            {
                'code': 'TEACH001',
                'user_type': 'teacher',
                'school_id': 'delhi_high_school',
                'max_uses': 5
            },
            {
                'code': 'ADMIN001',
                'user_type': 'admin',
                'school_id': 'system',
                'max_uses': 100
            },
            {
                'code': 'TEST001',
                'user_type': 'student',
                'school_id': 'test_school',
                'max_uses': 10
            }
        ]
        
        # Insert new codes
        for code_data in new_codes:
            cursor.execute('''
                INSERT INTO access_codes 
                (code, user_type, school_id, is_active, max_uses, current_uses, created_at, created_by)
                VALUES (?, ?, ?, TRUE, ?, 0, ?, 'system')
            ''', (
                code_data['code'],
                code_data['user_type'],
                code_data['school_id'],
                code_data['max_uses'],
                datetime.now().isoformat()
            ))
        
        conn.commit()
        print("✅ New access codes created successfully!")
        print("\n📋 Available Access Codes:")
        print("=" * 50)
        
        for code_data in new_codes:
            print(f"🔑 {code_data['code']} - {code_data['user_type'].title()}")
            print(f"   School: {code_data['school_id']}")
            print(f"   Max Uses: {code_data['max_uses']}")
            print(f"   Status: Never Expires")
            print()
        
        print("💡 Use any of these codes to test the login system!")
        print("🎯 Recommended for testing: TEST001 (10 uses, never expires)")
        print("\n🚀 Access codes will no longer expire automatically!")
        print("🔧 Admins can manage them through the admin portal.")
        
    except Exception as e:
        print(f"❌ Error regenerating access codes: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    regenerate_access_codes() 