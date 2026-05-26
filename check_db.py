import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 1. Print out the columns to make sure 'file_hash' exists
cursor.execute("PRAGMA table_info(files)")
columns = cursor.fetchall()
print("--- DATABASE COLUMNS ---")
for col in columns:
    print(f"Column ID: {col[0]}, Name: {col[1]}, Type: {col[2]}")

print("\n--- LAST 5 FILES UPLOADED ---")
# 2. Print out the last 5 entries to see what the hashes look like
cursor.execute("SELECT username, filename, duplicate_status, file_hash FROM files ORDER BY id DESC LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(f"User: {row[0]} | File: {row[1]} | Status: {row[2]} | Hash: {row[3]}")

conn.close()