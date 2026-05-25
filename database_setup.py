import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

# USERS TABLE

cursor.execute(
    '''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
    )
    '''
)

# FILES TABLE

cursor.execute(
    '''
    CREATE TABLE files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        filename TEXT,
        category TEXT,
        duplicate_status TEXT,
        sync_status TEXT
    )
    '''
)

conn.commit()

conn.close()

print("Database Created Successfully")