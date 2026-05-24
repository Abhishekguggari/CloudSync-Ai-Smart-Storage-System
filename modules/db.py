import sqlite3
#database setup
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    category TEXT,
    duplicate_status TEXT,
    sync_status TEXT
)
''')

conn.commit()
conn.close()