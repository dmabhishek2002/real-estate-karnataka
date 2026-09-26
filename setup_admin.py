import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "database/realestate.db"

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
""")

username = "admin"
password = "admin123"

password_hash = generate_password_hash(password)

cursor.execute("""
SELECT id FROM admins
WHERE username = ?
""", (username,))

existing_admin = cursor.fetchone()

if existing_admin:
    print("Admin account already exists.")
else:
    cursor.execute("""
    INSERT INTO admins (username, password_hash)
    VALUES (?, ?)
    """, (username, password_hash))

    connection.commit()
    print("Admin account created successfully.")

connection.close()

print("Username: admin")
print("Password: admin123")
