#!/usr/bin/env python3
"""
Simple script to create admin user - works with both SQLite and PostgreSQL
"""
import os
import hashlib
from datetime import datetime

# Check if we're using PostgreSQL (production) or SQLite (development)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///namaskah_app.db")

print(f"🔍 Using database: {DATABASE_URL[:50]}...")  # Log for debugging

if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    # PostgreSQL (production)
    import psycopg2
    from urllib.parse import urlparse
    
    # Parse database URL
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
        user=url.username,
        password=url.password
    )
    cursor = conn.cursor()
    
    # PostgreSQL syntax
    CREATE_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        is_verified BOOLEAN DEFAULT TRUE,
        role TEXT DEFAULT 'user',
        subscription_plan TEXT DEFAULT 'free',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    '''
    
    INSERT_SQL = '''
    INSERT INTO users 
    (id, email, username, hashed_password, full_name, is_active, is_verified, role)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (email) DO NOTHING
    '''
    
else:
    # SQLite (development)
    import sqlite3
    
    # Create/connect to database
    conn = sqlite3.connect('namaskah_app.db')
    cursor = conn.cursor()
    
    # SQLite syntax
    CREATE_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        is_active BOOLEAN DEFAULT 1,
        is_verified BOOLEAN DEFAULT 1,
        role TEXT DEFAULT 'user',
        subscription_plan TEXT DEFAULT 'free',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    '''
    
    INSERT_SQL = '''
    INSERT OR IGNORE INTO users 
    (id, email, username, hashed_password, full_name, is_active, is_verified, role)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''

# Create users table if it doesn't exist
cursor.execute(CREATE_TABLE_SQL)

# Hash password (simple version)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Create admin user
admin_id = "admin-001"
admin_email = "admin@namaskah.app"
admin_username = "admin"
admin_password = hash_password("admin123")

try:
    # Check if users already exist
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        cursor.execute("SELECT COUNT(*) FROM users WHERE email IN (%s, %s)", (admin_email, "demo@namaskah.app"))
    else:
        cursor.execute("SELECT COUNT(*) FROM users WHERE email IN (?, ?)", (admin_email, "demo@namaskah.app"))
    
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        print(f"ℹ️ Found {existing_count} existing users, skipping creation")
    else:
        print("👤 Creating admin and demo users...")
        
        cursor.execute(INSERT_SQL, (admin_id, admin_email, admin_username, admin_password, "Admin User", True, True, "admin"))
        
        # Create demo user
        demo_id = "demo-001"
        cursor.execute(INSERT_SQL, (demo_id, "demo@namaskah.app", "demo", hash_password("demo123"), "Demo User", True, True, "user"))
        
        conn.commit()
        print("✅ Users created successfully!")
    
    # Verify users exist
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        cursor.execute("SELECT email, role FROM users WHERE email IN (%s, %s)", (admin_email, "demo@namaskah.app"))
    else:
        cursor.execute("SELECT email, role FROM users WHERE email IN (?, ?)", (admin_email, "demo@namaskah.app"))
    
    users = cursor.fetchall()
    print("📋 Current users:")
    for user in users:
        print(f"   - {user[0]} ({user[1]})")
    
    print("\n🔑 Login credentials:")
    print("   Admin: admin@namaskah.app / admin123")
    print("   Demo: demo@namaskah.app / demo123")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    conn.close()