import sqlite3

conn = sqlite3.connect(
    'database.db'
)

cursor = conn.cursor()

# USERS TABLE

cursor.execute(
'''
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE,

    email TEXT,

    password BLOB
)
'''
)

# FILES TABLE

cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS files(

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