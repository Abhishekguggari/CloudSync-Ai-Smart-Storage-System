import sqlite3

def init_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # 2. Create Files Table (Matching all indices used in app.py)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            filename TEXT NOT NULL,
            category TEXT,
            duplicate_status TEXT,
            sync_status TEXT,
            file_hash TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database tables initialized successfully!")

if __name__ == '__main__':
    init_database()