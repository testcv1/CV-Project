#!/bin/bash

echo "🚀 Starting CV Project Application..."

# Get port from environment variable or default to 5000
PORT=${PORT:-5000}
echo "🌐 Using port: $PORT"

# Create upload directories
mkdir -p static/images static/uploads

# Initialize databases with a simple Python script
echo "📊 Initializing databases..."
python3 << 'EOF'
import sqlite3
import os

def init_db():
    # Users database
    try:
        conn = sqlite3.connect('users.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS USERS
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            Password TEXT NOT NULL UNIQUE)''')
        conn.commit()
        conn.close()
        print('✅ Users database initialized')
    except Exception as e:
        print(f'⚠️  Users database error: {e}')

    # Jobs database
    try:
        conn = sqlite3.connect('jobs.db')
        c = conn.cursor()
        
        # Basic tables
        tables = [
            '''CREATE TABLE IF NOT EXISTS employers
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               company_name TEXT NOT NULL,
               email TEXT UNIQUE NOT NULL,
               password TEXT NOT NULL,
               logo TEXT)''',
            
            '''CREATE TABLE IF NOT EXISTS jobs
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               title TEXT NOT NULL,
               email TEXT NOT NULL,
               contact_number TEXT,
               description TEXT NOT NULL,
               requirements TEXT,
               location TEXT,
               country TEXT,
               city TEXT,
               job_type TEXT NOT NULL,
               salary TEXT,
               salary_min INTEGER,
               salary_max INTEGER,
               salary_currency TEXT,
               salary_period TEXT,
               skills TEXT,
               posted_date TEXT NOT NULL,
               employer_id INTEGER NOT NULL,
               category TEXT,
               experience_level TEXT,
               FOREIGN KEY (employer_id) REFERENCES employers(id))''',
            
            '''CREATE TABLE IF NOT EXISTS consultants
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               email TEXT UNIQUE NOT NULL,
               password TEXT NOT NULL,
               specialization TEXT,
               years_experience INTEGER,
               bio TEXT,
               linkedin TEXT,
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''',
            
            '''CREATE TABLE IF NOT EXISTS applications
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               job_id INTEGER NOT NULL,
               user_id INTEGER NOT NULL,
               full_name TEXT NOT NULL,
               email TEXT NOT NULL,
               phone TEXT NOT NULL,
               resume_path TEXT NOT NULL,
               cover_letter TEXT,
               linkedin_url TEXT,
               portfolio_url TEXT,
               application_date TEXT NOT NULL,
               status TEXT DEFAULT 'Pending',
               FOREIGN KEY (job_id) REFERENCES jobs(id),
               FOREIGN KEY (user_id) REFERENCES users(id))''',
            
            '''CREATE TABLE IF NOT EXISTS blogs
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               consultant_id INTEGER NOT NULL,
               title TEXT NOT NULL,
               category TEXT NOT NULL,
               image_url TEXT,
               summary TEXT NOT NULL,
               content TEXT NOT NULL,
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY(consultant_id) REFERENCES consultants(id))''',
            
            '''CREATE TABLE IF NOT EXISTS mcq_questions
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               consultant_id INTEGER NOT NULL,
               job_role TEXT NOT NULL,
               experience_level TEXT NOT NULL,
               question_text TEXT NOT NULL,
               option1 TEXT NOT NULL,
               option2 TEXT NOT NULL,
               option3 TEXT NOT NULL,
               option4 TEXT NOT NULL,
               correct_option INTEGER NOT NULL,
               explanation TEXT,
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY(consultant_id) REFERENCES consultants(id))''',
            
            '''CREATE TABLE IF NOT EXISTS user_quiz_results
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER NOT NULL,
               question_id INTEGER NOT NULL,
               selected_option INTEGER NOT NULL,
               is_correct BOOLEAN NOT NULL,
               quiz_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY(user_id) REFERENCES USERS(id),
               FOREIGN KEY(question_id) REFERENCES mcq_questions(id))''',
            
            '''CREATE TABLE IF NOT EXISTS consultant_chats
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER NOT NULL,
               consultant_id INTEGER NOT NULL,
               message TEXT NOT NULL,
               sender_type TEXT NOT NULL,
               sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY(user_id) REFERENCES USERS(id),
               FOREIGN KEY(consultant_id) REFERENCES consultants(id))''',
            
            '''CREATE TABLE IF NOT EXISTS session_requests
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               consultant_id INTEGER NOT NULL,
               user_id INTEGER NOT NULL,
               name TEXT NOT NULL,
               email TEXT NOT NULL,
               phone TEXT,
               purpose TEXT NOT NULL,
               preferred_date TEXT,
               preferred_time TEXT,
               status TEXT DEFAULT 'pending',
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY(consultant_id) REFERENCES consultants(id),
               FOREIGN KEY(user_id) REFERENCES USERS(id))'''
        ]
        
        for table_sql in tables:
            c.execute(table_sql)
        
        conn.commit()
        conn.close()
        print('✅ Jobs database initialized')
    except Exception as e:
        print(f'⚠️  Jobs database error: {e}')

if __name__ == '__main__':
    init_db()
EOF

echo "🎯 Starting Gunicorn server on port $PORT..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --preload --log-level debug app:app 