from flask import (
    Flask,
    request,
    render_template,
    redirect,
    session,
    send_file
)

import os
import io
import sqlite3
import shutil

from modules.validation import allowed_file
from modules.encryption import encrypt_file, decrypt_file
from modules.sync import sync_to_cloud
from modules.ai_features import categorize_file, file_hash, detect_duplicate
from modules.activity import log_activity
from modules.auth import register_user, login_user
from modules.search import search_files
from modules.analytics import get_analytics
from modules.settings import get_settings
from modules.sharing import share_file as generate_share_link

from config import UPLOAD_FOLDER

app = Flask(__name__)

# SECRET KEY
app.secret_key = "cloudsync_secret_key"

# UPLOAD CONFIG
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CLOUD_BUCKET'] = os.path.join(os.path.dirname(__file__), 'cloud_bucket')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(app.config['CLOUD_BUCKET'], exist_ok=True)

# =========================
# STORAGE CALCULATION
# =========================
def calculate_storage():
    """Calculates total local storage usage and returns clean raw metrics."""
    total_size = 0
    if not os.path.exists(UPLOAD_FOLDER):
        return 0, "0.00 MB", 0.0

    for file in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, file)
        if os.path.isfile(path):
            total_size += os.path.getsize(path)

    # Convert sizes
    gb = total_size / (1024 * 1024 * 1024)
    mb = total_size / (1024 * 1024)

    # Format human readable label string
    if gb >= 1:
        storage_str = f"{gb:.2f} GB"
    else:
        storage_str = f"{mb:.2f} MB"

    # Define limit threshold (e.g., 15 GB Max Storage)
    max_storage_gb = 15.0
    current_gb = total_size / (1024 * 1024 * 1024)
    storage_percent = min(round((current_gb / max_storage_gb) * 100, 1), 100.0)

    return total_size, storage_str, storage_percent

# =========================
# HOME LOGIN
# =========================
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']
    valid = login_user(username, password)

    if valid:
        session['user'] = username
        return redirect('/dashboard')

    return """
    <h2>Invalid Username or Password</h2>
    <a href='/'>Try Again</a>
    """

# =========================
# REGISTER
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    register_user(username, email, password)
    log_activity(f"{username} registered account")
    return redirect('/')

# =========================
# DASHBOARD (FIXED STORAGE PACKING)
# =========================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE username=?', (session['user'],))
    files = cursor.fetchall()
    conn.close()

    # Get verified calculations
    _, storage_used, storage_percent = calculate_storage()

    return render_template(
        'dashboard.html', 
        files=files, 
        storage_used=storage_used, 
        storage_percent=storage_percent
    )

# =========================
# UPLOAD (FIXED DUPLICATE DETECTION)
# =========================
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'GET':
        return render_template('upload.html')

    if 'file' not in request.files:
        return "No file selected"

    file = request.files['file']
    if file.filename == "":
        return "Empty filename"

    if file and allowed_file(file.filename):
        file_bytes = file.read()
        file.seek(0)

        import hashlib
        current_hash = hashlib.md5(file_bytes).hexdigest()
        duplicate = detect_duplicate(session['user'], current_hash)

        final_filename = file.filename
        path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
        
        counter = 1
        name, ext = os.path.splitext(file.filename)
        while os.path.exists(path):
            final_filename = f"{name}_{counter}{ext}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
            counter += 1

        file.save(path)
        encrypt_file(path)

        category = categorize_file(final_filename)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO files (username, filename, category, duplicate_status, sync_status, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (session['user'], final_filename, category, duplicate, 'Pending', current_hash)
        )
        conn.commit()
        conn.close()

        log_activity(f"{session['user']} uploaded {final_filename}")

    return redirect('/dashboard')

# =========================
# SIMULATED CLOUD SYNC ROUTE
# =========================
@app.route('/sync/<int:file_id>')
def sync_file_to_local_cloud(file_id):
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT filename FROM files WHERE id=? AND username=?', (file_id, session['user']))
    file_record = cursor.fetchone()

    if not file_record:
        conn.close()
        return "File record not found", 404

    filename = file_record[0]
    local_source_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    cloud_destination_path = os.path.join(app.config['CLOUD_BUCKET'], filename)

    if not os.path.exists(local_source_path):
        conn.close()
        return "Source upload file cannot be found locally", 404

    try:
        shutil.copy2(local_source_path, cloud_destination_path)
        cursor.execute('UPDATE files SET sync_status=? WHERE id=?', ('Synced', file_id))
        conn.commit()
        log_activity(f"{session['user']} successfully synced {filename} to local cloud container.")
    except Exception as e:
        conn.close()
        return f"Simulated cloud sync routine failed: {str(e)}", 500

    conn.close()
    return redirect('/dashboard')

# =========================
# SEARCH
# =========================
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user' not in session:
        return redirect('/')

    results = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        results = search_files(keyword)

    return render_template('search.html', results=results)

# =========================
# ANALYTICS
# =========================
@app.route('/analytics')
def analytics():
    if 'user' not in session:
        return redirect('/')

    total, synced, duplicates = get_analytics(session['user'])

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE username=? AND duplicate_status LIKE ?', (session['user'], 'Duplicate%'))
    duplicate_files = cursor.fetchall()
    conn.close()

    activity_logs = []
    if os.path.exists('logs/activity.log'):
        with open('logs/activity.log', 'r', encoding='utf-8') as file:
            activity_logs = file.readlines()[-10:]
            activity_logs.reverse()

    _, storage_used, storage_percent = calculate_storage()

    return render_template(
        'analytics.html',
        total=total,
        synced=synced,
        duplicates=duplicates,
        duplicate_files=duplicate_files,
        activity_logs=activity_logs,
        storage_used=storage_used,
        storage_percent=storage_percent
    )

# =========================
# SETTINGS PAGE VIEW
# =========================
@app.route('/settings')
def settings():
    if 'user' not in session:
        return redirect('/')

    settings_data = get_settings()
    return render_template('settings.html', settings=settings_data)

# =========================
# DARK MODE TOGGLE
# =========================
@app.route('/toggle-dark-mode')
def toggle_dark_mode():
    current = session.get('dark_mode', True)
    session['dark_mode'] = not current
    return redirect('/settings')

# =========================
# SHARE FILE
# =========================
@app.route('/share/<filename>')
def share(filename):
    if 'user' not in session:
        return redirect('/')

    link = generate_share_link(filename)
    log_activity(f"{session['user']} shared {filename}")

    return f"""
    <h2>Share Link Generated</h2>
    <p>{link}</p>
    <a href='/dashboard'>Back to Dashboard</a>
    """

# =========================
# DOWNLOAD FILE
# =========================
@app.route('/download/<filename>')
def download_file(filename):
    if 'user' not in session:
        return redirect('/')

    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(path):
        return "File not found"

    decrypted_data = decrypt_file(path)
    return send_file(io.BytesIO(decrypted_data), download_name=filename, as_attachment=True)

# =========================
# DELETE FILE
# =========================
@app.route('/delete/<filename>')
def delete_file(filename):
    if 'user' not in session:
        return redirect('/')

    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM files WHERE filename=? AND username=?', (filename, session['user']))
    conn.commit()
    conn.close()

    log_activity(f"{session['user']} deleted {filename}")
    return redirect('/dashboard')

# =========================
# ADMIN DASHBOARD
# =========================
@app.route('/admin')
def admin_dashboard():
    if 'user' not in session:
        return redirect('/')

    if session['user'] != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users")
    users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM files")
    all_files = cursor.fetchall()
    conn.close()

    _, storage_used, _ = calculate_storage()

    return render_template(
        'dashboard.html',
        files=all_files,
        admin_mode=True,
        users=users,
        storage_used=storage_used
    )

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)