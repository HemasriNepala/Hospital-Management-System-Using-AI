import sqlite3
import os

db_path = os.path.join('instance', 'hospital_management.db')
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, role, is_verified FROM users")
    rows = cursor.fetchall()
    print("Users in database:")
    for row in rows:
        print(f"ID: {row[0]}, Email: {row[1]}, Role: {row[2]}, Verified: {row[3]}")
    conn.close()
