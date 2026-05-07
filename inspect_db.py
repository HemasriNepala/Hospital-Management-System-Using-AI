"""Inspect SQLite schema and fix admin user - verbose output."""
import sqlite3
import os
import sys

db_path = os.path.join('instance', 'hospital_management.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
cols = cursor.fetchall()
sys.stdout.write("Columns in 'users' table:\n")
for col in cols:
    sys.stdout.write(f"  cid={col[0]} name={col[1]} type={col[2]} notnull={col[3]}\n")
    sys.stdout.flush()

cursor.execute("SELECT id, email, role, is_verified FROM users")
rows = cursor.fetchall()
sys.stdout.write(f"\nTotal users: {len(rows)}\n")
for row in rows:
    sys.stdout.write(f"  ID={row[0]} email={row[1]} role={row[2]} verified={row[3]}\n")
    sys.stdout.flush()

conn.close()
