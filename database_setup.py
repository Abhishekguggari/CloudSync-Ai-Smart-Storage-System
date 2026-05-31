import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

# USERS TABLE
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )
    '''
)

# FILES TABLE

cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        filename TEXT,
        category TEXT,
        duplicate_status TEXT,
        sync_status TEXT,
        file_hash TEXT
    )
    '''
)

conn.commit()

conn.close()

print("Database Created Successfully")