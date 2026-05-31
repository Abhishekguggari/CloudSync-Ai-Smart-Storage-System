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
from modules.settings import get_settings, save_settings
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
# DATABASE MIGRATION CHECK
# =========================
def check_db_schema():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users LIMIT 1")
        conn.close()
    except sqlite3.OperationalError:
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            cursor.execute("UPDATE users SET role='admin' WHERE username='admin'")
            conn.commit()
            conn.close()
        except Exception:
            pass

check_db_schema()

# =========================
# NETWORK CHECKER
# =========================
def check_internet_connection():
    import socket
    try:
        # Attempt to connect to Google's public DNS to verify real internet access
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

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
# SESSION ROLE REFRESHER
# =========================
@app.before_request
def refresh_session_role():
    """Ensures user roles are instantly updated without requiring a relogin."""
    if 'user' in session:
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username=?", (session['user'],))
            user_record = cursor.fetchone()
            conn.close()
            if user_record:
                session['role'] = user_record[0]
        except Exception:
            pass

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
        session['role'] = valid.get('role', 'user') if isinstance(valid, dict) else 'user'
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

    user_settings = get_settings(session['user'])

    return render_template(
        'dashboard.html', 
        files=files, 
        storage_used=storage_used, 
        storage_percent=storage_percent,
        settings=user_settings
    )

# =========================
# UPLOAD (FIXED DUPLICATE DETECTION)
# =========================
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'GET':
        user_settings = get_settings(session['user'])
        return render_template('upload.html', settings=user_settings)

    if 'file' not in request.files:
        return "No file selected"

    file = request.files['file']
    if file.filename == "":
        return "Empty filename"

    if file and allowed_file(file.filename):
        file_bytes = file.read()
        file.seek(0)

        final_filename = file.filename
        
        user_settings = get_settings(session['user'])

        if user_settings.get('ai_features', 'Enabled') == 'Enabled':
            import hashlib
            current_hash = hashlib.md5(file_bytes).hexdigest()
            duplicate = detect_duplicate(session['user'], current_hash)
        else:
            current_hash = "N/A"
            duplicate = "Unique"

        path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
        
        counter = 1
        name, ext = os.path.splitext(file.filename)
        while os.path.exists(path):
            final_filename = f"{name}_{counter}{ext}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
            counter += 1

        file.save(path)

        if user_settings.get('encryption', 'Enabled') == 'Enabled':
            encrypt_file(path)

        if user_settings.get('cloud_sync', 'Enabled') == 'Enabled':
            # Check real physical network status before syncing
            is_online = check_internet_connection()
            session['is_online'] = is_online
            
            if is_online:
                sync_result = sync_to_cloud(path, app.config['CLOUD_BUCKET'])
            else:
                sync_result = 'Not Synced'
        else:
            sync_result = 'Sync Disabled'

        category = categorize_file(final_filename) if user_settings.get('ai_features', 'Enabled') == 'Enabled' else "Uncategorized"

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO files (username, filename, category, duplicate_status, sync_status, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (session['user'], final_filename, category, duplicate, sync_result, current_hash)
        )
        conn.commit()
        conn.close()

        log_activity(f"{session['user']} uploaded {final_filename}")

    return redirect('/dashboard')

# =========================
# NETWORK STATUS CHECK & BULK SYNC
# =========================
@app.route('/check-network')
def check_network():
    if 'user' not in session:
        return redirect('/')
        
    was_offline = not session.get('is_online', True)
    
    # Check actual real connection
    is_online = check_internet_connection()
    session['is_online'] = is_online
    
    # If we transitioned from offline to online, sync pending files
    if is_online and was_offline:
        user_settings = get_settings(session['user'])
        if user_settings.get('cloud_sync', 'Enabled') == 'Enabled':
            # Sync pending offline files
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, filename FROM files WHERE username=? AND sync_status IN (?, ?)', (session['user'], 'Not Synced', 'Sync Disabled'))
            unsynced_files = cursor.fetchall()
            
            for file_id, filename in unsynced_files:
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(path):
                    sync_result = sync_to_cloud(path, app.config['CLOUD_BUCKET'])
                    cursor.execute('UPDATE files SET sync_status=? WHERE id=?', (sync_result, file_id))
            
            conn.commit()
            conn.close()
            log_activity(f"{session['user']} network restored and bulk synced pending files.")

    return redirect(request.referrer or '/dashboard')

# =========================
# SIMULATED CLOUD SYNC ROUTE
# =========================
@app.route('/sync/<int:file_id>')
def sync_file_to_local_cloud(file_id):
    if 'user' not in session:
        return redirect('/')

    # Prevent manual sync if offline
    if not session.get('is_online', True):
        return redirect('/dashboard')
    if not check_internet_connection():
        session['is_online'] = False
        return redirect('/dashboard')

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
        results = search_files(keyword, session['user'])

    user_settings = get_settings(session['user'])

    return render_template('search.html', results=results, settings=user_settings)

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
    
    user_settings = get_settings(session['user'])

    return render_template(
        'analytics.html',
        total=total,
        synced=synced,
        duplicates=duplicates,
        duplicate_files=duplicate_files,
        activity_logs=activity_logs,
        storage_used=storage_used,
        storage_percent=storage_percent,
        settings=user_settings
    )

# =========================
# SETTINGS PAGE VIEW
# =========================
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        cloud_sync = request.form.get('cloud_sync', 'Disabled')
        encryption = request.form.get('encryption', 'Disabled')
        ai_features = request.form.get('ai_features', 'Disabled')
        dark_mode = request.form.get('dark_mode', 'Disabled')
        notifications = request.form.get('notifications', 'Disabled')
        
        settings_data = {
            'cloud_sync': cloud_sync,
            'encryption': encryption,
            'ai_features': ai_features,
            'dark_mode': dark_mode,
            'notifications': notifications
        }
        save_settings(session['user'], settings_data)
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        if cloud_sync == 'Enabled':
            cursor.execute('UPDATE files SET sync_status=? WHERE username=? AND sync_status=?', ('Not Synced', session['user'], 'Sync Disabled'))
            conn.commit()
            if check_internet_connection():
                session['is_online'] = True
                cursor.execute('SELECT id, filename FROM files WHERE username=? AND sync_status=?', (session['user'], 'Not Synced'))
                unsynced_files = cursor.fetchall()
                for file_id, filename in unsynced_files:
                    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    if os.path.exists(path):
                        sync_result = sync_to_cloud(path, app.config['CLOUD_BUCKET'])
                        cursor.execute('UPDATE files SET sync_status=? WHERE id=?', (sync_result, file_id))
                conn.commit()
        else:
            cursor.execute('UPDATE files SET sync_status=? WHERE username=? AND sync_status=?', ('Sync Disabled', session['user'], 'Not Synced'))
            conn.commit()
        conn.close()

        return redirect('/settings')

    settings_data = get_settings(session['user'])
    return render_template('settings.html', settings=settings_data)

# =========================
# SAVE SETTINGS ACTION
# =========================
@app.route('/save_settings', methods=['GET', 'POST'], strict_slashes=False)
@app.route('/save-settings', methods=['GET', 'POST'], strict_slashes=False)
@app.route('/save', methods=['GET', 'POST'], strict_slashes=False)
@app.route('/update_settings', methods=['GET', 'POST'], strict_slashes=False)
@app.route('/settings/save', methods=['GET', 'POST'], strict_slashes=False)
def handle_save_settings():
    if 'user' not in session:
        return redirect('/')

    # Support both POST (form data) and GET (query parameters)
    source = request.form if request.method == 'POST' else request.args

    # If it's an empty GET request, just redirect back to the settings page
    if request.method == 'GET' and not source:
        return redirect('/settings')

    cloud_sync = source.get('cloud_sync', 'Disabled')
    encryption = source.get('encryption', 'Disabled')
    ai_features = source.get('ai_features', 'Disabled')
    dark_mode = source.get('dark_mode', 'Disabled')
    notifications = source.get('notifications', 'Disabled')
    
    settings_data = {
        'cloud_sync': cloud_sync,
        'encryption': encryption,
        'ai_features': ai_features,
        'dark_mode': dark_mode,
        'notifications': notifications
    }
    save_settings(session['user'], settings_data)

    # Update file sync statuses based on the new setting
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if cloud_sync == 'Enabled':
        cursor.execute('UPDATE files SET sync_status=? WHERE username=? AND sync_status=?', ('Not Synced', session['user'], 'Sync Disabled'))
        conn.commit()

        if check_internet_connection():
            session['is_online'] = True
            cursor.execute('SELECT id, filename FROM files WHERE username=? AND sync_status=?', (session['user'], 'Not Synced'))
            unsynced_files = cursor.fetchall()
            
            for file_id, filename in unsynced_files:
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(path):
                    sync_result = sync_to_cloud(path, app.config['CLOUD_BUCKET'])
                    cursor.execute('UPDATE files SET sync_status=? WHERE id=?', (sync_result, file_id))
            
            conn.commit()
    else:
        cursor.execute('UPDATE files SET sync_status=? WHERE username=? AND sync_status=?', ('Sync Disabled', session['user'], 'Not Synced'))
        conn.commit()

    conn.close()

    return redirect('/settings')

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

    if session.get('role') != 'admin' and session['user'] != 'admin':
        return "Access Denied"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users")
    users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM files")
    all_files = cursor.fetchall()
    conn.close()

    _, storage_used, _ = calculate_storage()

    user_settings = get_settings(session['user'])

    return render_template(
        'dashboard.html',
        files=all_files,
        admin_mode=True,
        users=users,
        storage_used=storage_used,
        settings=user_settings
    )

# =========================
# ADMIN: CHANGE ROLE
# =========================
@app.route('/admin/change_role/<int:user_id>/<new_role>')
def admin_change_role(user_id, new_role):
    if 'user' not in session or (session.get('role') != 'admin' and session['user'] != 'admin'):
        return "Access Denied"
        
    if new_role in ['admin', 'user']:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
        conn.commit()
        conn.close()
    return redirect('/admin')

# =========================
# ADMIN: DELETE USER
# =========================
@app.route('/admin/delete_user/<int:user_id>')
def admin_delete_user(user_id):
    if 'user' not in session or (session.get('role') != 'admin' and session['user'] != 'admin'):
        return "Access Denied"
        
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
    user_record = cursor.fetchone()
    
    if user_record:
        username_to_delete = user_record[0]
        
        # Prevent the admin from accidentally deleting their own account
        if username_to_delete != session['user']:
            # Delete the user and all their associated files from the database
            cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            cursor.execute("DELETE FROM files WHERE username=?", (username_to_delete,))
            conn.commit()
            log_activity(f"Admin {session['user']} deleted user {username_to_delete}")
            
    conn.close()
    return redirect('/admin')

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)