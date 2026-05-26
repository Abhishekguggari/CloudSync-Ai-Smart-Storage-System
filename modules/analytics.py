import sqlite3
import os

UPLOAD_FOLDER = "uploads"

# =========================
# STORAGE SIZE CALCULATOR
# =========================
def get_storage_used():
    total_size = 0

    if not os.path.exists(UPLOAD_FOLDER):
        return "0 MB"

    for file in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, file)
        if os.path.isfile(path):
            total_size += os.path.getsize(path)

    gb = total_size / (1024 * 1024 * 1024)
    mb = total_size / (1024 * 1024)

    if gb >= 1:
        return f"{gb:.2f} GB"

    return f"{mb:.2f} MB"

# =========================
# ANALYTICS (FIXED UNPACKING BUG)
# =========================
def get_analytics(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # TOTAL FILES
    cursor.execute(
        '''
        SELECT COUNT(*)
        FROM files
        WHERE username=?
        ''',
        (username,)
    )
    total = cursor.fetchone()[0]

    # SYNCED FILES
    cursor.execute(
        '''
        SELECT COUNT(*)
        FROM files
        WHERE username=?
        AND sync_status=?
        ''',
        (username, "Synced")
    )
    synced = cursor.fetchone()[0]

    # DUPLICATES
    cursor.execute(
        '''
        SELECT COUNT(*)
        FROM files
        WHERE username=?
        AND duplicate_status LIKE ?
        ''',
        (username, "%Duplicate%")
    )
    duplicates = cursor.fetchone()[0]

    conn.close()

    # Returns exactly 3 values to perfectly match what app.py expects
    return total, synced, duplicates