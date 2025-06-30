#!/usr/bin/env python3
"""
Simple test script to verify the Flask app can start
"""

import os
import sys
import sqlite3

def test_database_creation():
    """Test database creation"""
    try:
        # Test users database
        conn = sqlite3.connect('users.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS USERS
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            Password TEXT NOT NULL UNIQUE)''')
        conn.commit()
        conn.close()
        print("✅ Users database test passed")
        
        # Test jobs database
        conn = sqlite3.connect('jobs.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS employers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     company_name TEXT NOT NULL,
                     email TEXT UNIQUE NOT NULL,
                     password TEXT NOT NULL,
                     logo TEXT)''')
        conn.commit()
        conn.close()
        print("✅ Jobs database test passed")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_app_import():
    """Test if the app can be imported"""
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Import app
        from app import app
        print("✅ App import test passed")
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint test passed")
                return True
            else:
                print(f"❌ Health endpoint test failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ App import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running tests...")
    
    # Test database creation
    if not test_database_creation():
        return False
    
    # Test app import and health endpoint
    if not test_app_import():
        return False
    
    print("🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 