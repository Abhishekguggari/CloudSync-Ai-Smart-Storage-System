import os
import hashlib
import sqlite3

UPLOAD_FOLDER = "uploads"

# =========================
# CATEGORY DETECTION
# =========================
def categorize_file(filename):
    extension = filename.split('.')[-1].lower()
    if extension in ['jpg', 'jpeg', 'png', 'gif']:
        return "Image"
    elif extension in ['pdf', 'docx', 'txt']:
        return "Document"
    elif extension in ['mp4', 'mkv', 'avi']:
        return "Video"
    elif extension in ['mp3', 'wav']:
        return "Audio"
    else:
        return "Other"

# =========================
# FILE HASH
# =========================
def file_hash(file_input):
    hasher = hashlib.md5()
    
    # Process memory byte arrays
    if isinstance(file_input, bytes):
        hasher.update(file_input)
        return hasher.hexdigest()
        
    # Process standard text paths
    elif isinstance(file_input, str):
        if not os.path.exists(file_input):
            return ""
        with open(file_input, 'rb') as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    return ""

# =========================
# DUPLICATE DETECTION
# =========================
def detect_duplicate(username, current_hash):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT id FROM files
        WHERE username=? AND file_hash=?
        ''',
        (username, current_hash)
    )
    existing = cursor.fetchone()
    conn.close()

    if existing:
        return "Duplicate Found"
    return "Unique"