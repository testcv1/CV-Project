import string
import pandas as pd
import re
from werkzeug.security import generate_password_hash, check_password_hash
import flask
from flask import Flask, request, render_template, send_file, redirect, url_for, session, jsonify,send_from_directory,flash
from flask_mail import Mail, Message
import flash
import pdfplumber
from docx import Document
from jinja2 import Environment, FileSystemLoader
import os
from xhtml2pdf import pisa
from io import BytesIO
from markupsafe import Markup, escape
import sqlite3
from datetime import datetime
import requests
import uuid
from werkzeug.utils import secure_filename
from chatbot import CVAnalyzer 
import re
import json
from datetime import datetime
from typing import Dict, List, Any
import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TensorFlow logging

app = Flask(__name__)
app.secret_key = 'd4e5f8a2b6c1e9a7f1234f6789abc012'
chat_history_ids = None

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max file size
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

@app.errorhandler(413)
def too_large(e):
    return "File is too large. Maximum size is 2MB.", 413

def allowed_image_file(filename):
    """Check if the uploaded file has an allowed image extension"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
def create_upload_directory():
    """Ensure upload directory exists"""
    upload_dir = os.path.join(app.root_path, UPLOAD_FOLDER)
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"Created upload directory: {upload_dir}")

# Call this when the app starts
create_upload_directory()
###########################
def extract_text(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

#################################################################################
#databases
#################################################################################
def create_users_database():
    if not os.path.exists('users.db'):
        with sqlite3.connect('users.db') as conn:
            conn.execute("""CREATE TABLE USERS
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            Password TEXT NOT NULL UNIQUE)""")
create_users_database()

def init_jobs_db():
    conn = sqlite3.connect('jobs.db')
    create_users_database()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 company_name TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 logo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS session_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        FOREIGN KEY(user_id) REFERENCES USERS(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
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
                 FOREIGN KEY (employer_id) REFERENCES employers(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS consultants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        specialization TEXT,
        years_experience INTEGER,
        bio TEXT,
        linkedin TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    FOREIGN KEY (user_id) REFERENCES users(id)
);''')
    c.execute('''CREATE TABLE IF NOT EXISTS blogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        consultant_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        image_url TEXT,
        summary TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(consultant_id) REFERENCES consultants(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mcq_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        FOREIGN KEY(consultant_id) REFERENCES consultants(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        selected_option INTEGER NOT NULL,
        is_correct BOOLEAN NOT NULL,
        quiz_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES USERS(id),
        FOREIGN KEY(question_id) REFERENCES mcq_questions(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS consultant_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        consultant_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        sender_type TEXT NOT NULL,  -- 'user' or 'consultant'
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES USERS(id),
        FOREIGN KEY(consultant_id) REFERENCES consultants(id)
    )''')
    conn.commit()
    conn.close()

# Add this after your init_jobs_db() function
def update_db_schema():
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    try:
        # Check if columns exist
        c.execute("PRAGMA table_info(employers)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'profile_views' not in columns:
            c.execute("ALTER TABLE employers ADD COLUMN profile_views INTEGER DEFAULT 0")
        
        if 'applications_count' not in columns:
            c.execute("ALTER TABLE employers ADD COLUMN applications_count INTEGER DEFAULT 0")
        
        if 'has_paid' not in columns:
            c.execute("ALTER TABLE employers ADD COLUMN has_paid BOOLEAN DEFAULT 0")
            
        conn.commit()
    except Exception as e:
        print(f"Error updating schema: {e}")
    finally:
        conn.close()

# Call this function after init_jobs_db()
init_jobs_db()
update_db_schema()

# Helper function to get database connection
def get_users_db():
    return sqlite3.connect('users.db')

def get_jobs_db():
    return sqlite3.connect('jobs.db')

def get_users_db2():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to get database connection
def get_db():
    conn = sqlite3.connect('jobs.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

#######################################################################################
#Main page routes
#######################################################################################
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if len(password) < 8 or not re.search(r"[a-zA-Z]", password) or not re.search(r"\d", password):
            return render_template('signup.html', error="Password must be at least 8 characters long and include both letters and numbers.")
        hashed_password = generate_password_hash(password)
        with sqlite3.connect('users.db') as connect:
            pointer = connect.cursor()
            pointer.execute("SELECT * from USERS WHERE email=?", (email,))
            exists = pointer.fetchone()
            if exists:
                return render_template('signup.html', error="ERROR! User already exists.")
            pointer.execute("INSERT INTO USERS (name, email, password) VALUES (?, ?, ?)", 
                          (name, email, hashed_password))
            connect.commit()
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM USERS WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user[3], password):
                session['user'] = user[1]
                session['user_id'] = user[0]
                return redirect(url_for('home'))
            else:
                return render_template("login.html", error="Invalid credentials")
    return render_template("login.html", error=None)

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("home.html", user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/resume')
def resume():
    return render_template('resume.html')

###############################################################################
#chatbot
###############################################################################
@app.route('/cv_chatbot')
def cv_chatbot():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("cv_chatbot.html")

@app.route('/api/analyze_cv', methods=['POST'])
def analyze_cv():
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    if 'cv' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    
    cv_file = request.files['cv']
    
    # Validate file type
    if not cv_file.filename.lower().endswith('.pdf'):
        return jsonify({'status': 'error', 'message': 'Only PDF files are accepted'}), 400
    
    try:
        # Extract text from PDF
        with pdfplumber.open(cv_file) as pdf:
            cv_text = '\n'.join([page.extract_text() for page in pdf.pages if page.extract_text()])
        
        if not cv_text.strip():
            return jsonify({'status': 'error', 'message': 'Could not extract text from PDF'}), 400
        
        # Analyze CV using the CVAnalyzer class
        analyzer = CVAnalyzer()
        analysis = analyzer.analyze_cv(cv_text)
        
        return jsonify({
            'status': 'success',
            'analysis': analysis
        })
        
    except Exception as e:
        print(f"Error analyzing CV: {e}")
        return jsonify({'status': 'error', 'message': 'Error processing your CV'}), 500

########################################################################################
#resume builder
########################################################################################
@app.route("/manual_resume", methods=["GET", "POST"])
def manual_resume():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("manual_resume.html")

def format_date(date_str):
    try:
        if date_str.lower() == 'present':
            return date_str
        if '/' in date_str:
            month, year = date_str.split('/')
            return datetime.strptime(f"{month}/01/{year}", "%m/%d/%Y").strftime("%b %Y")
        return date_str
    except:
        return date_str

@app.route('/template_selection', methods=['GET', 'POST'])
def template_selection():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        print("POST request received")
        
        # Handle photo upload
        photo_url = None
        if 'photo' in request.files:
            photo = request.files['photo']
            print(f"Photo file: {photo.filename}")
            
            if photo.filename != '':
                if not allowed_image_file(photo.filename):
                    print(f"Invalid file type: {photo.filename}")
                else:
                    try:
                        # Use consistent filename based on user ID
                        filename = secure_filename(photo.filename)
                        name, ext = os.path.splitext(filename)
                        consistent_filename = f"user_{session['user_id']}_photo{ext.lower()}"
                        
                        # Ensure upload directory exists
                        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        # Remove any existing photo for this user
                        for existing_file in os.listdir(upload_folder):
                            if existing_file.startswith(f"user_{session['user_id']}_photo"):
                                try:
                                    os.remove(os.path.join(upload_folder, existing_file))
                                    print(f"Removed existing photo: {existing_file}")
                                except:
                                    pass
                        
                        # Save the photo with consistent name
                        photo_path = os.path.join(upload_folder, consistent_filename)
                        photo.save(photo_path)
                        
                        # Verify the file was saved
                        if os.path.exists(photo_path):
                            photo_url = f"uploads/{consistent_filename}"  # Relative path from static folder
                            print(f"Photo saved successfully: {photo_url}")
                        else:
                            print("Error: File was not saved")
                    except Exception as e:
                        print(f"Error saving photo: {str(e)}")

        # Store resume data in session
        resume_data = {
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'photo_url': photo_url,
            'skills': [s.strip() for s in request.form.get("skills", "").split(",") if s.strip()],
            'certifications': [c.strip() for c in request.form.get("certifications", "").split(",") if c.strip()],
            'education': [],
            'experience': []
        }
        
        # Process education data
        degrees = request.form.getlist('degree[]')
        institutions = request.form.getlist('institution[]')
        education_start_dates = request.form.getlist('education_start_date[]')
        education_end_dates = request.form.getlist('education_end_date[]')
        education_descriptions = request.form.getlist('education_description[]')
        marks_list = request.form.getlist('marks[]')
        
        for i in range(len(degrees)):
            if degrees[i].strip():
                resume_data['education'].append({
                    'degree': degrees[i].strip(),
                    'institution': institutions[i].strip(),
                    'start_date': format_date(education_start_dates[i].strip()),
                    'end_date': format_date(education_end_dates[i].strip()),
                    'description': education_descriptions[i].strip() if i < len(education_descriptions) else '',
                    'marks': marks_list[i].strip() if i < len(marks_list) else ''
                })
        
        # Process work experience data
        job_titles = request.form.getlist('job_title[]')
        companies = request.form.getlist('company[]')
        start_dates = request.form.getlist('start_date[]')
        end_dates = request.form.getlist('end_date[]')
        job_descriptions = request.form.getlist('job_description[]')
        
        for i in range(len(job_titles)):
            if job_titles[i].strip():
                resume_data['experience'].append({
                    'job_title': job_titles[i].strip(),
                    'company': companies[i].strip(),
                    'start_date': format_date(start_dates[i].strip()),
                    'end_date': format_date(end_dates[i].strip()),
                    'description': job_descriptions[i].strip() if i < len(job_descriptions) else ''
                })
        
        session['resume_data'] = resume_data
    return render_template('template_selection.html')

@app.route('/set_template', methods=['POST'])
def set_template():
    try:
        print("Set template route called")
        
        if 'user' not in session:
            print("User not in session")
            return jsonify({'success': False, 'error': 'User not logged in'}), 401
        
        if 'resume_data' not in session:
            print("Resume data not in session")
            return jsonify({'success': False, 'error': 'Resume data missing'}), 400
        
        data = request.get_json()
        if not data:
            print("No JSON data received")
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        template_id = data.get('template_id')
        print(f"Template ID received: {template_id}")
        
        if not template_id:
            print("No template ID provided")
            return jsonify({'success': False, 'error': 'Template ID missing'}), 400
        
        # Store the selected template in session
        session['selected_template'] = template_id
        print(f"Template {template_id} stored in session")
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in set_template: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate_from_template', methods=['GET'])
def generate_from_template():
    if 'user' not in session or 'resume_data' not in session or 'selected_template' not in session:
        return redirect(url_for('login'))
    
    try:
        # Prepare user data from session
        user_data = session['resume_data'].copy()
        user_data['current_date'] = datetime.now().strftime("%B %Y")
        template_id = session['selected_template']

        # Handle photo URL for PDF generation
        if user_data.get('photo_url'):
            photo_path = os.path.join(app.root_path, 'static', user_data['photo_url'])
            if os.path.exists(photo_path):
                photo_path = os.path.abspath(photo_path).replace('\\', '/')
                user_data['photo_absolute_path'] = f"file://{photo_path}"
                print(f"Using photo path: {user_data['photo_absolute_path']}")
            else:
                print(f"Photo file not found: {photo_path}")
                user_data['photo_url'] = None

        # Load template and render HTML
        env = Environment(loader=FileSystemLoader('templates'))
        template_file = f'cv_templates/resume_template{template_id}.html'
        template = env.get_template(template_file)
        html_out = template.render(user_data)

        # Generate PDF using xhtml2pdf
        pdf_file = BytesIO()
        pisa_status = pisa.CreatePDF(src=html_out, dest=pdf_file)
        if pisa_status.err:
            print("Error during PDF generation")
            return redirect(url_for('template_selection'))

        pdf_file.seek(0)

        # Save resume data to database
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO RESUMES (user_id, resume_data, template_id)
                    VALUES (?, ?, ?)
                """, (session['user_id'], json.dumps(user_data), template_id))
                conn.commit()
        except Exception as e:
            print(f"Error saving resume to database: {e}")

        # Send generated PDF to user
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=f"{user_data['name'].replace(' ', '_')}_resume.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error in generate_from_template: {e}")
        return redirect(url_for('template_selection'))

#######################################################################################
#Blogs routes
#######################################################################################
@app.route('/blogs')
def blogs():
    conn = get_jobs_db()
    c = conn.cursor()
    # Get all blogs with author information
    c.execute('''SELECT b.*, c.name as author_name 
               FROM blogs b JOIN consultants c ON b.consultant_id = c.id
               ORDER BY b.created_at DESC''')
    blogs = c.fetchall()
    conn.close()
    # Get all unique categories for filtering
    categories = ['For Job Seekers', 'CV', 'For Employers', 
                 'Case Studies', 'Internship', 'Reports', 'News']
    return render_template('blogs.html', blogs=blogs, categories=categories)

@app.route('/consultants/add_blog', methods=['GET', 'POST'],endpoint='add_blog')
def consultant_add_blog():
    if 'consultant_id' not in session:
        return redirect(url_for('consultant_login'))
    
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        summary = request.form['summary']
        content = request.form['content']
        
        image_url = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join('static/uploads/blogs', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)
                image_url = f'/static/uploads/blogs/{filename}'
        
        with get_jobs_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO blogs 
                            (consultant_id, title, category, image_url, summary, content)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                         (session['consultant_id'], title, category, image_url, summary, content))
            conn.commit()
        
        return redirect(url_for('consultant_dashboard'))
    
    return render_template('consultant_add_blog.html')

@app.route('/consultants/add_blog', methods=['GET', 'POST'])
def consultant_add_blog():
    if 'consultant_id' not in session:
        return redirect(url_for('consultant_login'))
    
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        summary = request.form['summary']
        content = request.form['content']
        
        image_url = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join('static/uploads/blogs', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)
                image_url = f'/static/uploads/blogs/{filename}'
        
        with get_jobs_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO blogs 
                            (consultant_id, title, category, image_url, summary, content)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                         (session['consultant_id'], title, category, image_url, summary, content))
            conn.commit()
        
        return redirect(url_for('consultant_dashboard'))
    
    return redirect(url_for('consultant_dashboard'))

@app.route('/blogs')
def all_blogs():
    conn = get_jobs_db()
    c = conn.cursor()
    
    # Get the selected category from query parameters
    selected_category = request.args.get('category', 'all')
    
    # Base query
    query = '''SELECT b.*, c.name as author_name 
               FROM blogs b JOIN consultants c ON b.consultant_id = c.id'''
    
    # Add category filter if not 'all'
    if selected_category != 'all':
        query += " WHERE b.category = ?"
        c.execute(query, (selected_category,))
    else:
        c.execute(query)
    
    blogs = c.fetchall()
    
    # Get all unique categories for the filter dropdown
    c.execute("SELECT DISTINCT category FROM blogs")
    categories = [row['category'] for row in c.fetchall()]
    
    conn.close()
    
    return render_template('blogs.html', 
                         blogs=blogs, 
                         categories=categories,
                         selected_category=selected_category)

@app.route('/blog/<int:blog_id>')
def view_blog(blog_id):
    """View single blog (accessible to all users)"""
    conn = get_jobs_db()
    c = conn.cursor()
    c.execute('''SELECT b.*, c.name as author_name, c.specialization 
               FROM blogs b JOIN consultants c ON b.consultant_id = c.id
               WHERE b.id = ?''', (blog_id,))
    blog = c.fetchone()
    conn.close()    
    return render_template('view_blog.html', blog=blog)

@app.route('/delete_blog/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    if 'consultant_id' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    with get_jobs_db() as conn:
        cursor = conn.cursor()
        # First check if the blog belongs to this consultant
        cursor.execute("SELECT consultant_id FROM blogs WHERE id = ?", (blog_id,))
        blog = cursor.fetchone()
        
        if not blog:
            return jsonify({'success': False, 'error': 'Blog not found'}), 404
        
        if blog['consultant_id'] != session['consultant_id']:
            return jsonify({'success': False, 'error': 'Not authorized'}), 403
        
        # Delete the blog
        cursor.execute("DELETE FROM blogs WHERE id = ?", (blog_id,))
        conn.commit()
    
    return jsonify({'success': True})

##########################################################################
#consultant routes
##########################################################################
@app.route('/consultants')
def consultant_landing():
    print("Consultant landing page reached")
    return render_template("consultant.html")

@app.route('/consultants/register', methods=['GET', 'POST'])
def consultant_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        specialization = request.form['specialization']
        years_experience = request.form['years_experience']
        bio = request.form['bio']
        linkedin = request.form.get('linkedin', None)

        # Validate passwords match
        if password != confirm_password:
            return render_template("consultant_register.html", error="Passwords do not match")

        # Check if email exists
        with get_jobs_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consultants WHERE email = ?", (email,))
            if cursor.fetchone():
                return render_template("consultant_register.html", error="Email already registered")

            # Create consultant without photo
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO consultants 
                (name, email, password, specialization, years_experience, bio, linkedin)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, hashed_password, specialization, 
                 years_experience, bio, linkedin))
            conn.commit()

        return redirect(url_for('consultant_login'))

    return render_template("consultant_register.html")

@app.route('/consultants/login', methods=['GET', 'POST'])
def consultant_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consultants WHERE email = ?", (email,))
            consultant = cursor.fetchone()

            if consultant and check_password_hash(consultant['password'], password):
                session['consultant_id'] = consultant['id']
                return redirect(url_for('consultant_dashboard'))

        return render_template('consultant_login.html', error="Invalid credentials")

    return render_template('consultant_login.html')

@app.route('/consultants/dashboard')
def consultant_dashboard():
    if 'consultant_id' not in session:
        return redirect(url_for('consultant_login'))
    
    with get_jobs_db() as conn:
        # Set row factory to return dictionaries
        conn.row_factory = sqlite3.Row
        
        c = conn.cursor()
        c.execute("ATTACH DATABASE 'users.db' AS usersdb")
        c.execute("SELECT * FROM consultants WHERE id = ?", (session['consultant_id'],))
        consultant = c.fetchone()
        c.execute("SELECT * FROM session_requests WHERE consultant_id = ?", (session['consultant_id'],))
        requests = c.fetchall()
        c.execute('''
            SELECT DISTINCT usersdb.USERS.id as user_id, 
                            usersdb.USERS.name as user_name, 
                            MAX(c.sent_at) as last_message_time
            FROM consultant_chats c
            JOIN usersdb.USERS ON c.user_id = usersdb.USERS.id
            WHERE c.consultant_id = ?
            GROUP BY usersdb.USERS.id, usersdb.USERS.name
            ORDER BY last_message_time DESC
        ''', (session['consultant_id'],))
        active_sessions = c.fetchall()
        c.execute("SELECT * FROM blogs WHERE consultant_id = ?", (session['consultant_id'],))
        blogs = c.fetchall()
        
        # Get MCQ questions
        c.execute("SELECT * FROM mcq_questions WHERE consultant_id = ? ORDER BY created_at DESC", (session['consultant_id'],))
        questions = [dict(row) for row in c.fetchall()]
    
    return render_template("consultant_dashboard.html", 
                           consultant=dict(consultant) if consultant else None, 
                           requests=[dict(r) for r in requests],
                           active_sessions=[dict(s) for s in active_sessions],
                           blogs=[dict(b) for b in blogs],
                           questions=questions)

@app.route('/consultants/add_mcq_question', methods=['POST'])
def add_mcq_question():
    if 'consultant_id' not in session:
        return redirect(url_for('consultant_login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            job_role = request.form['job_role']
            experience_level = request.form['experience_level']
            question_text = request.form['question']
            correct_option = int(request.form['correct_option'])
            explanation = request.form.get('explanation', '')
            
            # Get all options
            option1 = request.form['option_1']
            option2 = request.form['option_2']
            option3 = request.form['option_3']
            option4 = request.form['option_4']
            
            # Validate correct option
            if correct_option < 1 or correct_option > 4:
                return redirect(url_for('consultant_dashboard'))
            
            # Insert into database
            with get_jobs_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mcq_questions 
                    (consultant_id, job_role, experience_level, question_text,
                     option1, option2, option3, option4, correct_option, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session['consultant_id'], 
                    job_role, 
                    experience_level,
                    question_text,
                    option1,
                    option2,
                    option3,
                    option4,
                    correct_option,
                    explanation
                ))
                conn.commit()
            return redirect(url_for('consultant_dashboard'))
            
        except Exception as e:
            print(f"Error adding MCQ question: {e}")
            return redirect(url_for('consultant_dashboard'))
    
    return redirect(url_for('consultant_dashboard'))

@app.route('/get_mcq/<int:question_id>')
def get_mcq(question_id):
    if 'consultant_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    with get_jobs_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mcq_questions WHERE id = ?", (question_id,))
        question = cursor.fetchone()
        
        if question:
            # Convert to dict and handle datetime serialization
            question_dict = dict(question)
            question_dict['created_at'] = str(question_dict['created_at'])
            return jsonify(question_dict)
        
    return jsonify({'error': 'Question not found'}), 404

@app.route('/delete_mcq/<int:question_id>', methods=['DELETE'])
def delete_mcq(question_id):
    if 'consultant_id' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    with get_db() as conn:
        cursor = conn.cursor()
        # Verify the question belongs to this consultant
        cursor.execute("SELECT consultant_id FROM mcq_questions WHERE id = ?", (question_id,))
        question = cursor.fetchone()
        
        if not question:
            return jsonify({'success': False, 'error': 'Question not found'}), 404
        
        if question['consultant_id'] != session['consultant_id']:
            return jsonify({'success': False, 'error': 'Not authorized'}), 403
        
        # Delete the question
        cursor.execute("DELETE FROM mcq_questions WHERE id = ?", (question_id,))
        conn.commit()
    
    return jsonify({'success': True})

#######################################################################################
#Quiz routes
#######################################################################################
@app.route('/interview_prep')
def interview_prep():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('interview_prep_dashboard.html')

@app.route('/start_quiz')
def start_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Get 5 random questions
    c.execute("SELECT * FROM mcq_questions ORDER BY RANDOM() LIMIT 5")
    questions = c.fetchall()
    conn.close()
    
    return render_template('quiz.html', questions=questions)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    answers = request.form
    
    conn = get_db()
    c = conn.cursor()
    
    results = []
    correct = 0
    
    for question_id, selected_option in answers.items():
        if question_id.startswith('question_'):
            q_id = int(question_id.replace('question_', ''))
            
            # Get correct answer
            c.execute("SELECT correct_option FROM mcq_questions WHERE id = ?", (q_id,))
            question = c.fetchone()
            is_correct = int(selected_option) == question['correct_option']
            
            if is_correct:
                correct += 1
            
            # Store result
            c.execute("""INSERT INTO user_quiz_results 
                        (user_id, question_id, selected_option, is_correct)
                        VALUES (?, ?, ?, ?)""",
                     (user_id, q_id, selected_option, is_correct))
            
            results.append({
                'question_id': q_id,
                'selected_option': selected_option,
                'is_correct': is_correct
            })
    
    conn.commit()
    conn.close()
    
    score = (correct / len(results)) * 100 if results else 0
    return render_template('quiz_results.html', score=score, total=len(results), correct=correct)

@app.route('/quiz_analytics')
def quiz_analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Initialize default analytics structure
    analytics = {
        'overall': {
            'total_quizzes': 0,
            'total_questions': 0,
            'correct_answers': 0,
            'accuracy_percentage': 0.0
        },
        'by_category': [],
        'by_date': [],
        'weakest_categories': [],
        'strongest_categories': [],
        'improvement': {
            'percentage_change': 0.0,
            'trend': 'neutral'
        }
    }
    
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Overall statistics
        c.execute('''SELECT 
                    COUNT(DISTINCT DATE(quiz_date)) as total_quizzes,
                    COUNT(*) as total_questions,
                    SUM(is_correct) as correct_answers
                    FROM user_quiz_results
                    WHERE user_id = ?''', (user_id,))
        overall_stats = c.fetchone()
        
        if overall_stats:
            accuracy = (overall_stats['correct_answers'] / overall_stats['total_questions'] * 100) if overall_stats['total_questions'] > 0 else 0
            
            analytics['overall'] = {
                'total_quizzes': overall_stats['total_quizzes'] or 0,
                'total_questions': overall_stats['total_questions'] or 0,
                'correct_answers': overall_stats['correct_answers'] or 0,
                'accuracy_percentage': round(accuracy, 1)
            }
        
        # Performance by category
        c.execute('''SELECT 
                    q.job_role,
                    COUNT(*) as total_questions,
                    SUM(r.is_correct) as correct_answers,
                    (SUM(r.is_correct) * 100.0 / COUNT(*)) as accuracy_percentage
                    FROM user_quiz_results r
                    JOIN mcq_questions q ON r.question_id = q.id
                    WHERE r.user_id = ?
                    GROUP BY q.job_role
                    HAVING COUNT(*) > 0
                    ORDER BY accuracy_percentage DESC''', (user_id,))
        
        analytics['by_category'] = [dict(row) for row in c.fetchall()]
        
        # Identify strongest and weakest categories
        if len(analytics['by_category']) > 0:
            analytics['strongest_categories'] = analytics['by_category'][:3]
            analytics['weakest_categories'] = analytics['by_category'][-3:]
        
        # Performance over time (last 7 quizzes)
        c.execute('''SELECT 
                    DATE(quiz_date) as quiz_date,
                    COUNT(*) as total_questions,
                    SUM(is_correct) as correct_answers,
                    (SUM(is_correct) * 100.0 / COUNT(*)) as accuracy_percentage
                    FROM user_quiz_results
                    WHERE user_id = ?
                    GROUP BY DATE(quiz_date)
                    ORDER BY quiz_date DESC
                    LIMIT 7''', (user_id,))
        
        by_date = [dict(row) for row in c.fetchall()]
        analytics['by_date'] = by_date
        
        # Calculate improvement over time
        if len(by_date) > 1:
            first_quiz = by_date[-1]['accuracy_percentage']
            last_quiz = by_date[0]['accuracy_percentage']
            change = last_quiz - first_quiz
            
            analytics['improvement'] = {
                'percentage_change': round(abs(change), 1),
                'trend': 'up' if change > 0 else 'down' if change < 0 else 'neutral'
            }
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
    
    return render_template('quiz_analytics.html', analytics=analytics)

@app.route('/consultant_chat', methods=['GET', 'POST'])
def consultant_chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get user info from users.db
        users_conn = get_users_db()
        users_cursor = users_conn.cursor()
        users_cursor.execute("SELECT name, email FROM users WHERE id = ?", (session['user_id'],))
        user_data = users_cursor.fetchone()
        
        # Get consultants from jobs.db
        jobs_conn = get_jobs_db()
        jobs_cursor = jobs_conn.cursor()
        jobs_cursor.execute("""
            SELECT id, name, email, specialization, years_experience, bio 
            FROM consultants 
            ORDER BY name
        """)
        consultants_data = jobs_cursor.fetchall()
        
        # Format consultants data
        consultants = []
        for consultant in consultants_data:
            consultants.append({
                'id': consultant[0],
                'name': consultant[1],
                'email': consultant[2],
                'specialization': consultant[3],
                'years_experience': consultant[4],
                'bio': consultant[5]
            })
            
        return render_template('consultant_chat.html', 
                             consultants=consultants,
                             user_name=user_data[0] if user_data else '',
                             user_email=user_data[1] if user_data else '')
        
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('home'))
        
    finally:
        users_conn.close()
        jobs_conn.close()

@app.route('/contact_consultant/<int:consultant_id>')
@app.route('/contact_consultant/<int:consultant_id>')
def contact_consultant(consultant_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get user info
        users_conn = get_users_db()
        users_cursor = users_conn.cursor()
        users_cursor.execute("SELECT name, email FROM users WHERE id = ?", (session['user_id'],))
        user_data = users_cursor.fetchone()
        
        # Get consultant info
        jobs_conn = get_jobs_db()
        jobs_cursor = jobs_conn.cursor()
        jobs_cursor.execute("SELECT name, email, specialization FROM consultants WHERE id = ?", (consultant_id,))
        consultant = jobs_cursor.fetchone()
        
        if not consultant:
            return redirect(url_for('consultants'))
        
        # Create meeting options text
        meeting_text = (
            "Please let me know your preferred meeting option:%0A%0A"
            "1. Google Meet: https://meet.google.com/new%0A"
            "2. Zoom: https://zoom.us/start/videomeeting%0A%0A"
            "Or suggest your preferred platform and time."
        )
        
        # Create Gmail URL
        gmail_url = (
            "https://mail.google.com/mail/?view=cm&fs=1"
            f"&to={consultant[1]}"
            f"&su=Career Consultation Meeting Request"
            f"&body=Dear {consultant[0]},%0A%0A"
            f"My name is {user_data[0]} ({user_data[1]}).%0A%0A"
            f"I would like to schedule a consultation regarding {consultant[2]}.%0A%0A"
            f"{meeting_text}%0A%0A"
            "Best regards,%0A"
            f"{user_data[0]}"
        )
        
        return redirect(gmail_url)
        
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('consultants'))
        
    finally:
        users_conn.close()
        jobs_conn.close()

############################################################################################
#Jobs and Employers
############################################################################################
@app.route('/employers')
def employers():
    """Landing page for employers"""
    return render_template('employers.html')

@app.route('/employers/register', methods=['GET', 'POST'])
def employer_register():
    if request.method == 'POST':
        company_name = request.form['company_name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_jobs_db()
        c = conn.cursor()
        
        # Check if email exists
        c.execute("SELECT * FROM employers WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return render_template('employer_register.html', error="Email already exists")
        
        hashed_password = generate_password_hash(password)
        logo_filename = None
        
        # Handle logo upload
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo.filename != '':
                logo_filename = secure_filename(logo.filename)
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
        
        # Insert new employer
        c.execute("INSERT INTO employers (company_name, email, password, logo) VALUES (?, ?, ?, ?)",
                 (company_name, email, hashed_password, logo_filename))
        employer_id = c.lastrowid
        
        conn.commit()
        conn.close()
        
        session['employer_id'] = employer_id
        return redirect(url_for('employer_dashboard'))
    
    return render_template('employer_register.html')

@app.route('/employers/login', methods=['GET', 'POST'])
def employer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM employers WHERE email = ?", (email,))
        employer = c.fetchone()
        conn.close()
        
        if employer and check_password_hash(employer['password'], password):
            session['employer_id'] = employer['id']
            return redirect(url_for('employer_dashboard'))
        
        return render_template('employer_login.html', error="Invalid credentials")
    
    return render_template('employer_login.html')

@app.route('/jobs')
def jobs():
    # Get filter parameters from request
    search = request.args.get('search', '')
    country = request.args.get('country', '')
    city = request.args.get('city', '')
    job_type = request.args.get('job_type', '')
    category = request.args.get('category', '')
    experience = request.args.get('experience', '')
    salary_range = request.args.get('salary_range', '')

    conn = get_jobs_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get all unique countries and cities for filters
    c.execute("SELECT DISTINCT country FROM jobs WHERE country IS NOT NULL AND country != ''")
    countries = [row['country'] for row in c.fetchall()]
    
    c.execute("SELECT DISTINCT city FROM jobs WHERE city IS NOT NULL AND city != ''")
    cities = [row['city'] for row in c.fetchall()]

    # Base query
    query = '''SELECT j.*, e.company_name, e.logo 
               FROM jobs j JOIN employers e ON j.employer_id = e.id 
               WHERE 1=1'''
    params = []

    # Add filters
    if search:
        query += " AND (j.title LIKE ? OR j.description LIKE ? OR e.company_name LIKE ? OR j.skills LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if country:
        query += " AND j.country = ?"
        params.append(country)
    
    if city:
        query += " AND j.city = ?"
        params.append(city)
    
    if job_type:
        query += " AND j.job_type = ?"
        params.append(job_type)
    
    if category:
        query += " AND j.category = ?"
        params.append(category)
    
    if experience:
        query += " AND j.experience_level = ?"
        params.append(experience)
    
    if salary_range:
        if salary_range == '0-30000':
            query += " AND (j.salary_min >= 0 AND j.salary_max <= 30000)"
        elif salary_range == '30000-60000':
            query += " AND (j.salary_min >= 30000 AND j.salary_max <= 60000)"
        elif salary_range == '60000-90000':
            query += " AND (j.salary_min >= 60000 AND j.salary_max <= 90000)"
        elif salary_range == '90000+':
            query += " AND j.salary_min >= 90000"

    query += " ORDER BY j.posted_date DESC"
    c.execute(query, params)
    jobs = []
    
    # Convert each row to a dict and ensure posted_date is a datetime object
    for row in c.fetchall():
        job = dict(row)
        # Handle posted_date conversion
        if isinstance(job['posted_date'], str):
            try:
                job['posted_date'] = datetime.strptime(job['posted_date'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                job['posted_date'] = datetime.now()
        jobs.append(job)
    
    # Prepare current filters for template
    current_filters = {
        'search': search,
        'country': country,
        'city': city,
        'job_type': job_type,
        'category': category,
        'experience': experience,
        'salary_range': salary_range
    }
    conn.close()
    return render_template('jobs.html', 
                         jobs=jobs, 
                         current_filters=current_filters,
                         countries=countries,
                         cities=cities,
                         salary_ranges=['0-30000', '30000-60000', '60000-90000', '90000+'])


@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_jobs_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT j.*, e.company_name, e.logo 
               FROM jobs j JOIN employers e ON j.employer_id = e.id 
               WHERE j.id = ?''', (job_id,))
    job = c.fetchone()
    conn.close()
    
    if not job:
        flask.flash('Job not found', 'error')
        return redirect(url_for('jobs'))
    
    if request.method == 'POST':
        print(f"POST request received for job {job_id}")  # Debug
        print(f"Form data: {request.form}")  # Debug
        print(f"Files: {request.files}")  # Debug
        
        # Check if resume file exists
        if 'resume' not in request.files:
            print("No resume file in request")  # Debug
            flask.flash('No resume file uploaded', 'error')
            return redirect(url_for('apply_job', job_id=job_id))
            
        resume = request.files['resume']
        print(f"Resume filename: {resume.filename}")  # Debug
        
        if resume.filename == '':
            print("Empty filename")  # Debug
            flask.flash('No selected resume file', 'error')
            return redirect(url_for('apply_job', job_id=job_id))
        
        # Check if allowed_file function exists and works
        try:
            is_allowed = allowed_file(resume.filename)
            print(f"File allowed: {is_allowed}")  # Debug
        except Exception as e:
            print(f"Error checking file: {e}")  # Debug
            flask.flash('Error validating file', 'error')
            return redirect(url_for('apply_job', job_id=job_id))
            
        if resume and is_allowed:
            # Create a secure filename and save it
            filename = secure_filename(resume.filename)
            unique_filename = f"{session['user_id']}_{filename}"
            
            # Check if upload folder exists
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                print(f"Creating upload folder: {app.config['UPLOAD_FOLDER']}")
                os.makedirs(app.config['UPLOAD_FOLDER'])
            
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            print(f"Saving to: {resume_path}")  # Debug
            
            # Save application to database
            conn = get_jobs_db()
            c = conn.cursor()
            
            try:
                resume.save(resume_path)
                print("File saved successfully")  # Debug
                
                # Get required form fields
                full_name = request.form.get('full_name', '').strip()
                email = request.form.get('email', '').strip()
                phone = request.form.get('phone', '').strip()
                
                print(f"Form fields - Name: {full_name}, Email: {email}, Phone: {phone}")  # Debug
                
                # Basic validation
                if not full_name or not email:
                    flask.flash('Full name and email are required', 'error')
                    return redirect(url_for('apply_job', job_id=job_id))
                
                c.execute('''INSERT INTO applications 
                          (job_id, user_id, full_name, email, phone, resume_path, 
                           cover_letter, linkedin_url, portfolio_url, application_date)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (job_id, session['user_id'], 
                          full_name,
                          email,
                          phone,
                          unique_filename,
                          request.form.get('cover_letter', ''),
                          request.form.get('linkedin_url', ''),
                          request.form.get('portfolio_url', ''),
                          datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
                print("Application inserted into database")  # Debug
                
                # Increment application count for the employer
                c.execute('''UPDATE employers 
                           SET applications_count = applications_count + 1 
                           WHERE id = (SELECT employer_id FROM jobs WHERE id = ?)''', (job_id,))
                
                conn.commit()
                print("Database committed successfully")  # Debug
                
                flask.flash('Application submitted successfully!', 'success')
                return redirect(url_for('jobs'))
                
            except Exception as e:
                print(f"Database error: {str(e)}")  # Debug
                conn.rollback()
                # Clean up the file if there was a database error
                if os.path.exists(resume_path):
                    os.remove(resume_path)
                flask.flash(f'Error submitting application: {str(e)}', 'error')
                return redirect(url_for('apply_job', job_id=job_id))
            finally:
                conn.close()
        else:
            print("File not allowed or missing")  # Debug
            flask.flash('Invalid file type. Please upload a PDF, DOC, or DOCX file.', 'error')
            return render_template('apply_job.html', job=job)
    
    # GET request - show the application form
    return render_template('apply_job.html', job=job)


# Make sure you have the allowed_file function defined
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/apply/confirmation/<int:job_id>')
def application_confirmation(job_id):
    return redirect(url_for('jobs'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/employers/post_job', methods=['GET', 'POST'])
def post_job():
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))

    if request.method == 'POST':
        # Get all form data
        title = request.form['title']
        email = request.form['email']
        contact_number = request.form['contact_number']
        description = request.form['description']
        requirements = request.form['requirements']
        country = request.form['country']
        city = request.form['city']
        job_type = request.form['job_type']
        salary_min = request.form['salary_min']
        salary_max = request.form['salary_max']
        salary_currency = request.form['salary_currency']
        salary_period = request.form['salary_period']
        skills = request.form['skills']
        category = request.form['category']
        experience_level = request.form['experience_level']
        
        # Format salary for display
        salary = f"{salary_currency}{salary_min} - {salary_max} {salary_currency} {salary_period}"
        
        posted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_jobs_db()
        c = conn.cursor()
        
        # Check if location column exists for backward compatibility
        c.execute("PRAGMA table_info(jobs)")
        columns = [col[1] for col in c.fetchall()]
        has_location = 'location' in columns
        
        # Build the insert query based on available columns
        if has_location:
            c.execute('''INSERT INTO jobs 
                        (title, email, contact_number, description, requirements, 
                        country, city, location, job_type, salary, salary_min, salary_max, 
                        salary_currency, salary_period, skills, posted_date, employer_id, 
                        category, experience_level)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (title, email, contact_number, description, requirements,
                      country, city, f"{city}, {country}", job_type, salary, salary_min, salary_max,
                      salary_currency, salary_period, skills, posted_date, session['employer_id'],
                      category, experience_level))
        else:
            c.execute('''INSERT INTO jobs 
                        (title, email, contact_number, description, requirements, 
                        country, city, job_type, salary, salary_min, salary_max, 
                        salary_currency, salary_period, skills, posted_date, employer_id, 
                        category, experience_level)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (title, email, contact_number, description, requirements,
                      country, city, job_type, salary, salary_min, salary_max,
                      salary_currency, salary_period, skills, posted_date, session['employer_id'],
                      category, experience_level))
        
        conn.commit()
        conn.close()
        return redirect(url_for('employer_dashboard'))
    
    # For GET request, show form with all options
    job_types = ['Full-Time', 'Part-Time', 'Remote', 'Temporary', 'Internship', 'Contract']
    categories = ['Technology', 'Healthcare', 'Finance', 'Education', 'Retail', 'Manufacturing', 'Other']
    experience_levels = ['Entry Level', 'Mid Level', 'Senior Level', 'Executive']
    salary_currencies = ['USD', 'EUR', 'GBP', 'PKR', 'INR', 'AED']
    salary_periods = ['hourly', 'daily', 'weekly', 'monthly', 'annually']
    
    return render_template('post_job.html', 
                         job_types=job_types,
                         categories=categories,
                         experience_levels=experience_levels,
                         salary_currencies=salary_currencies,
                         salary_periods=salary_periods)

@app.route('/employer/logout')
def employer_logout():
    session.pop('employer_id', None)
    return redirect(url_for('employers'))

# Edit Job - Display Form
@app.route('/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))
    
    conn = get_jobs_db()
    cursor = conn.cursor()
    
    # Verify the job belongs to the logged-in employer
    cursor.execute("SELECT * FROM jobs WHERE id = ? AND employer_id = ?", 
                  (job_id, session['employer_id']))
    job = cursor.fetchone()
    
    if not job:
        flask.flash('Job not found or you do not have permission to edit it', 'error')
        return redirect(url_for('employer_dashboard'))
    
    if request.method == 'POST':
        try:
            # Get all form data
            title = request.form['title']
            email = request.form['email']
            contact_number = request.form.get('contact_number', '')
            description = request.form['description']
            requirements = request.form['requirements']
            country = request.form['country']
            city = request.form['city']
            job_type = request.form['job_type']
            salary_min = request.form['salary_min']
            salary_max = request.form['salary_max']
            salary_currency = request.form['salary_currency']
            salary_period = request.form['salary_period']
            skills = request.form['skills']
            category = request.form['category']
            experience_level = request.form['experience_level']
            
            # Format salary for display
            salary = f"{salary_currency}{salary_min} - {salary_max} {salary_period}"
            
            cursor.execute("""
                UPDATE jobs SET 
                    title = ?,
                    email = ?,
                    contact_number = ?,
                    description = ?,
                    requirements = ?,
                    country = ?,
                    city = ?,
                    job_type = ?,
                    salary = ?,
                    salary_min = ?,
                    salary_max = ?,
                    salary_currency = ?,
                    salary_period = ?,
                    skills = ?,
                    category = ?,
                    experience_level = ?
                WHERE id = ?
            """, (
                title, email, contact_number, description, requirements,
                country, city, job_type, salary, salary_min, salary_max,
                salary_currency, salary_period, skills, category,
                experience_level, job_id
            ))
            
            conn.commit()
            flask.flash('Job updated successfully!', 'success')
            return redirect(url_for('employer_dashboard'))
        except Exception as e:
            conn.rollback()
            flask.flash(f'Error updating job: {str(e)}', 'error')
        finally:
            conn.close()
    
    # For GET request, show the form with job data
    columns = [column[0] for column in cursor.description]
    job_dict = dict(zip(columns, job))
    conn.close()
    
    return render_template('edit_job.html', job=job_dict)

# Edit Job - Process Form Submission
@app.route('/jobs/edit/<int:job_id>', methods=['POST'])
def update_job(job_id):
    # Get form data
    title = request.form['title']
    job_type = request.form['job_type']
    category = request.form['category']
    experience_level = request.form['experience_level']
    city = request.form['city']
    country = request.form['country']
    salary_currency = request.form['salary_currency']
    salary_min = request.form['salary_min']
    salary_max = request.form['salary_max']
    salary_period = request.form['salary_period']
    description = request.form['description']
    requirements = request.form['requirements']
    skills = request.form['skills']
    email = request.form['email']
    contact_number = request.form.get('contact_number', '')
    
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE jobs SET 
                title = ?,
                job_type = ?,
                category = ?,
                experience_level = ?,
                city = ?,
                country = ?,
                salary_currency = ?,
                salary_min = ?,
                salary_max = ?,
                salary_period = ?,
                description = ?,
                requirements = ?,
                skills = ?,
                email = ?,
                contact_number = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            title, job_type, category, experience_level, city, country,
            salary_currency, salary_min, salary_max, salary_period,
            description, requirements, skills, email, contact_number,
            job_id
        ))
        
        conn.commit()
        flask.flash('Job updated successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flask.flash(f'Error updating job: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('employer_dashboard'))

@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    conn = get_jobs_db()
    c = conn.cursor()
    
    # Update profile views
    c.execute('''UPDATE employers 
               SET profile_views = profile_views + 1 
               WHERE id = (SELECT employer_id FROM jobs WHERE id = ?)''', (job_id,))
    conn.commit()
    
    # Set row_factory to Row to get named access to columns
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT j.*, e.company_name, e.logo 
               FROM jobs j JOIN employers e ON j.employer_id = e.id 
               WHERE j.id = ?''', (job_id,))
    job = c.fetchone()
    conn.close()
    
    if not job:
        return "Job not found", 404
    
    return render_template('job_detail.html', job=job)

@app.route('/jobs/delete/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify the job belongs to the logged-in employer
    c.execute("SELECT employer_id FROM jobs WHERE id = ?", (job_id,))
    job = c.fetchone()
    
    if job and job['employer_id'] == session['employer_id']:
        try:
            c.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
    
    conn.close()
    return redirect(url_for('employer_dashboard'))

#################################################################################
@app.route('/employers/dashboard')
def employer_dashboard():
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Get employer info
    c.execute("SELECT * FROM employers WHERE id = ?", (session['employer_id'],))
    employer = c.fetchone()
    
    # Get employer's jobs
    c.execute("SELECT * FROM jobs WHERE employer_id = ? ORDER BY posted_date DESC", (session['employer_id'],))
    jobs = c.fetchall()
    
    # Get counts of application statuses
    c.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status = 'shortlisted' THEN 1 ELSE 0 END) AS shortlisted,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.employer_id = ?
    ''', (session['employer_id'],))
    counts = c.fetchone() or {'total': 0, 'pending': 0, 'shortlisted': 0, 'rejected': 0}
    
    conn.close()
    
    current_date = datetime.now().strftime('%B %d, %Y')
    return render_template('employer_dashboard.html', 
                         employer=employer, 
                         jobs=jobs,
                         counts=counts,
                         current_date=current_date)

@app.route('/employers/applications')
def view_applications():
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))
    
    conn_jobs = get_db()
    conn_users = get_users_db2()
    
    c_jobs = conn_jobs.cursor()
    c_users = conn_users.cursor()
    
    # Get employer info
    c_jobs.execute("SELECT * FROM employers WHERE id = ?", (session['employer_id'],))
    employer = c_jobs.fetchone()
    
    # Get all jobs by this employer for filter dropdown
    c_jobs.execute("SELECT id, title FROM jobs WHERE employer_id = ? ORDER BY posted_date DESC", (session['employer_id'],))
    jobs = c_jobs.fetchall()
    
    # Build the base query
    query = '''SELECT a.*, j.title as job_title, a.user_id
               FROM applications a 
               JOIN jobs j ON a.job_id = j.id 
               WHERE j.employer_id = ?'''
    params = [session['employer_id']]
    
    # Job filter
    job_id = request.args.get('job_id')
    if job_id and job_id.isdigit():
        query += " AND j.id = ?"
        params.append(int(job_id))
    
    # Status filter
    status = request.args.get('status')
    if status in ['pending', 'shortlisted', 'rejected']:
        query += " AND a.status = ?"
        params.append(status)
    
    query += " ORDER BY a.application_date DESC"
    
    c_jobs.execute(query, params)
    applications_raw = c_jobs.fetchall()
    
    # Attach user info from users DB
    applications = []
    for app in applications_raw:
        c_users.execute("SELECT name, email FROM USERS WHERE id = ?", (app['user_id'],))
        user = c_users.fetchone()
        
        if user:
            app_dict = dict(app)
            app_dict['user_name'] = user['name']
            app_dict['user_email'] = user['email']
            applications.append(app_dict)
    
    # Count applications by status
    c_jobs.execute('''SELECT 
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'shortlisted' THEN 1 ELSE 0 END) as shortlisted,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                    FROM applications a 
                    JOIN jobs j ON a.job_id = j.id 
                    WHERE j.employer_id = ?''', (session['employer_id'],))
    counts = c_jobs.fetchone() or {'pending': 0, 'shortlisted': 0, 'rejected': 0}
    
    conn_jobs.close()
    conn_users.close()
    
    current_date = datetime.now().strftime('%B %d, %Y')
    return render_template('employer_applications.html',
                         employer=employer,
                         applications=applications,
                         jobs=jobs,
                         counts=counts,
                         current_date=current_date)

@app.route('/update_application_status/<int:application_id>/<status>', methods=['POST'])
def update_application_status(application_id, status):
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Verify the application belongs to one of the employer's jobs
        c.execute('''SELECT status FROM applications a 
                   JOIN jobs j ON a.job_id = j.id 
                   WHERE a.id = ? AND j.employer_id = ?''',
                   (application_id, session['employer_id']))
        app_data = c.fetchone()
        
        if not app_data:
            flask.flash('Application not found or you do not have permission', 'error')
            return redirect(url_for('view_applications'))
        
        # Only update if status is changing
        if app_data['status'] != status:
            c.execute('''UPDATE applications SET status = ? 
                       WHERE id = ?''', (status, application_id))
            
            conn.commit()
            flask.flash(f'Application status updated to {status}', 'success')
        else:
            flask.flash('Application already has this status', 'info')
    
    except Exception as e:
        conn.rollback()
        flask.flash(f'Error updating application: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('view_applications'))

@app.route('/clear_all_applications', methods=['POST'])
def clear_all_applications():
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Delete all applications for this employer's jobs
        c.execute('''DELETE FROM applications 
                   WHERE job_id IN (
                       SELECT id FROM jobs WHERE employer_id = ?
                   )''', (session['employer_id'],))
        
        deleted_count = c.rowcount
        conn.commit()
        flask.flash(f'Successfully cleared {deleted_count} applications', 'success')
    
    except Exception as e:
        conn.rollback()
        flask.flash(f'Error clearing applications: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('view_applications'))

from urllib.parse import quote

@app.route('/send_interview_email/<int:application_id>')
def send_interview_email(application_id):
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))
    conn_jobs = get_db()
    conn_users = get_users_db2()
    c_jobs = conn_jobs.cursor()
    c_users = conn_users.cursor()
    try:
        # Get application and job details
        c_jobs.execute('''SELECT a.*, j.title as job_title, e.company_name
                          FROM applications a 
                          JOIN jobs j ON a.job_id = j.id 
                          JOIN employers e ON j.employer_id = e.id
                          WHERE a.id = ? AND j.employer_id = ?''',
                          (application_id, session['employer_id']))
        app_data = c_jobs.fetchone()

        if not app_data:
            flash('Application not found', 'error')
            return redirect(url_for('view_applications'))

        # Get candidate details
        c_users.execute("SELECT name, email FROM USERS WHERE id = ?", (app_data['user_id'],))
        user_data = c_users.fetchone()

        if not user_data:
            flash('Candidate not found', 'error')
            return redirect(url_for('view_applications'))

        candidate_email = user_data['email']
        job_title = app_data['job_title']
        company_name = app_data['company_name']

        subject = f"Interview Invitation - {job_title} at {company_name}"
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={quote(candidate_email)}&su={quote(subject)}"

        return redirect(gmail_url)

    except Exception as e:
        flash('Error sending email link.', 'error')
        return redirect(url_for('view_applications'))

    finally:
        conn_jobs.close()
        conn_users.close()


@app.route('/candidate/<int:user_id>')
def view_candidate_profile(user_id):
    if 'employer_id' not in session:
        return redirect(url_for('employer_login'))
    
    conn_jobs = get_db()
    conn_users = get_users_db()
    
    c_jobs = conn_jobs.cursor()
    c_users = conn_users.cursor()
    
    try:
        # Get candidate info from users DB
        c_users.execute("SELECT * FROM USERS WHERE id = ?", (user_id,))
        candidate = c_users.fetchone()
        
        if not candidate:
            flash('Candidate not found', 'error')
            return redirect(url_for('view_applications'))
        
        # Applications by candidate to this employer's jobs
        c_jobs.execute('''SELECT a.*, j.title as job_title 
                        FROM applications a 
                        JOIN jobs j ON a.job_id = j.id 
                        WHERE a.user_id = ? AND j.employer_id = ?
                        ORDER BY a.application_date DESC''',
                        (user_id, session['employer_id']))
        applications = c_jobs.fetchall()
        
        return render_template('candidate_profile.html',
                             candidate=candidate,
                             applications=applications)
    
    except Exception as e:
        flash(f'Error loading candidate profile: {str(e)}', 'error')
        return redirect(url_for('view_applications'))
    finally:
        conn_jobs.close()
        conn_users.close()

