from flask import (
    Flask,
    request,
    render_template,
    redirect,
    send_from_directory,
    session
)

import os
import sqlite3

from modules.validation import allowed_file

from modules.encryption import encrypt_file, decrypt_file
import io
from flask import send_file

from modules.sync import sync_to_cloud

from modules.ai_features import (
    categorize_file,
    detect_duplicate
)

from modules.activity import log_activity

from modules.auth import (
    register_user,
    login_user
)

from modules.search import search_files

from modules.analytics import (
    get_analytics
)

from modules.settings import (
    get_settings
)

from modules.sharing import (
    share_file
)

from config import UPLOAD_FOLDER

app = Flask(__name__)

# SECRET KEY

app.secret_key = "cloudsync_secret_key"

# UPLOAD CONFIG

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

# LOGIN PAGE

@app.route('/', methods=['GET', 'POST'])
def home():

    if request.method == 'GET':

        return render_template(
            'login.html'
        )

    username = request.form['username']

    password = request.form['password']

    valid = login_user(
        username,
        password
    )

    if valid:

        session['user'] = username

        return redirect('/dashboard')

    return "Invalid Username or Password"

# REGISTER PAGE

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'GET':

        return render_template(
            'register.html'
        )

    username = request.form['username']

    email = request.form['email']

    password = request.form['password']

    register_user(
        username,
        email,
        password
    )

    return redirect('/')

# DASHBOARD

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:

        return redirect('/')

    conn = sqlite3.connect(
        'database.db'
    )

    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT * FROM files
        WHERE username=?
        ''',
        (
            session['user'],
        )
    )

    files = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        files=files
    )

# UPLOAD PAGE + FILE UPLOAD

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():

    if 'user' not in session:

        return redirect('/')

    if request.method == 'GET':

        return render_template(
            'upload.html'
        )

    file = request.files['file']

    if file and allowed_file(file.filename):

        path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            file.filename
        )

        file.save(path)

        # ENCRYPT FILE

        encrypt_file(path)

        # AI CATEGORY

        category = categorize_file(
            file.filename
        )

        # DUPLICATE DETECTION

        duplicate = detect_duplicate(
            file.filename
        )

        # CLOUD SYNC

        sync_status = sync_to_cloud(
            path
        )

        # DATABASE SAVE

        conn = sqlite3.connect(
            'database.db'
        )

        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO files
            (
                username,
                filename,
                category,
                duplicate_status,
                sync_status
            )

            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                session['user'],
                file.filename,
                category,
                duplicate,
                sync_status
            )
        )

        conn.commit()

        conn.close()

        # ACTIVITY LOG

        log_activity(
            f"{session['user']} uploaded {file.filename}"
        )

    return redirect('/dashboard')

# AI SEARCH

@app.route('/search', methods=['GET', 'POST'])
def search():

    if 'user' not in session:

        return redirect('/')

    results = []

    if request.method == 'POST':

        keyword = request.form['keyword']

        results = search_files(
            keyword
        )

    return render_template(
        'search.html',
        results=results
    )

# ANALYTICS

@app.route('/analytics')
def analytics():

    if 'user' not in session:

        return redirect('/')

    total, synced, duplicates = get_analytics(session["user"])
    
    # Fetch duplicate files for cleanup suggestions
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE username=? AND duplicate_status LIKE ?", (session['user'], '%Duplicate%'))
    duplicate_files = cursor.fetchall()
    conn.close()

    # Fetch activity logs
    activity_logs = []
    if os.path.exists('logs/activity.log'):
        with open('logs/activity.log', 'r', encoding='utf-8') as f:
            # Get last 10 lines
            activity_logs = f.readlines()[-10:]
            activity_logs.reverse()

    return render_template(
        'analytics.html',
        total=total,
        synced=synced,
        duplicates=duplicates,
        duplicate_files=duplicate_files,
        activity_logs=activity_logs
    )

# SETTINGS

@app.route('/settings')
def settings():

    if 'user' not in session:

        return redirect('/')

    settings_data = get_settings()

    return render_template(
        'settings.html',
        settings=settings_data
    )

# FILE SHARING

@app.route('/share/<filename>')
def share_file(filename):

    if 'user' not in session:

        return redirect('/')

    link = share_file(
        filename
    )

    return f"""
    <h2>Share Link Generated</h2>

    <p>{link}</p>

    <a href='/dashboard'>
    Back to Dashboard
    </a>
    """

# DOWNLOAD FILE

@app.route('/download/<filename>')
def download_file(filename):

    if 'user' not in session:

        return redirect('/')

    path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )
    
    if not os.path.exists(path):
        return "File not found", 404

    # Decrypt file on-the-fly to prevent serving encrypted bytes to user
    decrypted_data = decrypt_file(path)
    
    return send_file(
        io.BytesIO(decrypted_data),
        download_name=filename,
        as_attachment=True
    )

# DELETE FILE

@app.route('/delete/<filename>')
def delete_file(filename):

    if 'user' not in session:

        return redirect('/')

    path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    if os.path.exists(path):

        os.remove(path)

    conn = sqlite3.connect(
        'database.db'
    )

    cursor = conn.cursor()

    cursor.execute(
        '''
        DELETE FROM files
        WHERE filename=?
        ''',
        (
            filename,
        )
    )

    conn.commit()

    conn.close()

    log_activity(
        f"{session['user']} deleted {filename}"
    )

    return redirect('/dashboard')

# ADMIN DASHBOARD

@app.route('/admin')
def admin_dashboard():

    if 'user' not in session or session['user'] != 'admin':

        return "Access Denied: Admin only", 403

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, username, email FROM users")
    users = cursor.fetchall()
    
    # Get all files
    cursor.execute("SELECT * FROM files")
    all_files = cursor.fetchall()
    
    conn.close()

    return render_template(
        'dashboard.html',
        files=all_files,
        admin_mode=True,
        users=users
    )

# LOGOUT

@app.route('/logout')
def logout():

    session.pop(
        'user',
        None
    )

    return redirect('/')

# RUN SERVER

if __name__ == '__main__':

    app.run(debug=True)