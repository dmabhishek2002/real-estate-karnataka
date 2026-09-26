import sqlite3

DATABASE = "database/realestate.db"

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

cursor.execute("DELETE FROM properties")

connection.commit()

print("All demo property records removed.")

cursor.execute("SELECT COUNT(*) FROM properties")
count = cursor.fetchone()[0]

print("Properties remaining:", count)

connection.close()