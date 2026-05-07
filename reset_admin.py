import sqlite3
import bcrypt
import os

db_path = os.path.join('instance', 'hospital_management.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt())

c.execute("SELECT id FROM users WHERE role='admin'")
existing = c.fetchall()
print('Existing admins:', existing)

if not existing:
    c.execute(
        "INSERT INTO users (email, password_hash, role, is_verified) VALUES (?, ?, 'admin', 1)",
        ('admin@hospital.com', hashed)
    )
    conn.commit()
    print('Admin created: admin@hospital.com / admin123')
else:
    c.execute(
        "UPDATE users SET password_hash=?, is_verified=1, email='admin@hospital.com' WHERE role='admin'",
        (hashed,)
    )
    conn.commit()
    print('Admin password reset: admin@hospital.com / admin123')

c.execute("SELECT id, email, role, is_verified FROM users")
print('\nAll users:')
for row in c.fetchall():
    print(f"  ID={row[0]}  email={row[1]}  role={row[2]}  verified={row[3]}")

conn.close()
print('\nDone! Login at http://127.0.0.1:5000 with admin@hospital.com / admin123')
