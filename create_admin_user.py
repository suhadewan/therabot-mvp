#!/usr/bin/env python3
"""
Script to create the default admin user for MindMitra
"""

import sqlite3
import hashlib
import os

def create_admin_user():
    """Create the default admin user"""
    
    # Default admin credentials
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "mindmitra2024"  # Change this in production!
    
    # Hash the password
    password_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
    
    # Connect to database
    conn = sqlite3.connect('mental_health_bot.db')
    cursor = conn.cursor()
    
    try:
        # Check if admin user already exists
        cursor.execute('SELECT username FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print(f"✅ Admin user '{ADMIN_USERNAME}' already exists")
            print("💡 To change password, delete the user first and recreate")
        else:
            # Create admin user
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash, is_active)
                VALUES (?, ?, TRUE)
            ''', (ADMIN_USERNAME, password_hash))
            
            conn.commit()
            print("✅ Admin user created successfully!")
            print(f"👤 Username: {ADMIN_USERNAME}")
            print(f"🔑 Password: {ADMIN_PASSWORD}")
            print("\n⚠️  IMPORTANT: Change this password in production!")
        
        # Show admin users
        cursor.execute('SELECT username, created_at, last_login FROM admin_users')
        admin_users = cursor.fetchall()
        
        print(f"\n📋 Current Admin Users:")
        print("=" * 50)
        for user in admin_users:
            print(f"👤 {user[0]}")
            print(f"   Created: {user[1]}")
            print(f"   Last Login: {user[2] or 'Never'}")
            print()
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔐 MindMitra Admin User Setup")
    print("=" * 40)
    
    # Check if database exists
    if not os.path.exists('mental_health_bot.db'):
        print("❌ Database not found. Please run the PWA app first to initialize the database.")
        exit(1)
    
    create_admin_user()
    
    print("\n🎯 Next Steps:")
    print("1. Start your PWA app: python pwa_app.py")
    print("2. Visit: http://localhost:5002/admin-login")
    print("3. Login with: admin / mindmitra2024")
    print("4. Access admin dashboard at: http://localhost:5002/admin") 