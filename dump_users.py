import sqlite3, os
db_path = os.path.join('instance', 'hospital_management.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, email, role, is_verified FROM users ORDER BY id")
rows = c.fetchall()
with open('users_list.txt', 'w') as f:
    for row in rows:
        line = f"ID={row[0]} email={row[1]} role={row[2]} verified={row[3]}\n"
        f.write(line)
print("Written to users_list.txt")
conn.close()
