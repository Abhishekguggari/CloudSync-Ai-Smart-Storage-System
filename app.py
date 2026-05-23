from flask import Flask, request, render_template, redirect, send_from_directory
import os
import sqlite3

from modules.validation import allowed_file
from modules.encryption import encrypt_file
from modules.sync import sync_to_cloud
from modules.ai_features import categorize_file, detect_duplicate
from modules.activity import log_activity

from config import UPLOAD_FOLDER

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# HOME PAGE

@app.route('/')
def home():
    return render_template('login.html')

# REGISTER PAGE

@app.route('/register')
def register():
    return render_template('register.html')

# DASHBOARD

@app.route('/dashboard')
def dashboard():

    conn = sqlite3.connect('database.db')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM files")

    files = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        files=files
    )

# UPLOAD PAGE + FILE UPLOAD

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():

    # OPEN UPLOAD PAGE

    if request.method == 'GET':
        return render_template('upload.html')

    # FILE UPLOAD

    file = request.files['file']

    if file and allowed_file(file.filename):

        path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            file.filename
        )

        file.save(path)

        # ENCRYPT FILE

        encrypt_file(path)

        # AI FEATURES

        category = categorize_file(file.filename)

        duplicate = detect_duplicate(file.filename)

        # CLOUD SYNC

        sync_status = sync_to_cloud(path)

        # DATABASE SAVE

        conn = sqlite3.connect('database.db')

        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO files
            (filename, category, duplicate_status, sync_status)

            VALUES (?, ?, ?, ?)
            ''',
            (
                file.filename,
                category,
                duplicate,
                sync_status
            )
        )

        conn.commit()

        conn.close()

        # ACTIVITY LOG

        log_activity(f"Uploaded {file.filename}")

    return redirect('/dashboard')

# DOWNLOAD FILE

@app.route('/download/<filename>')
def download_file(filename):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )

# DELETE FILE

@app.route('/delete/<filename>')
def delete_file(filename):

    path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    if os.path.exists(path):

        os.remove(path)

    conn = sqlite3.connect('database.db')

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM files WHERE filename=?",
        (filename,)
    )

    conn.commit()

    conn.close()

    log_activity(f"Deleted {filename}")

    return redirect('/dashboard')

# RUN SERVER

if __name__ == '__main__':

    app.run(debug=True)