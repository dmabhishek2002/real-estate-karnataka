import sqlite3
from database.karnataka_taluks import KARNATAKA_TALUKS

DATABASE = "database/realestate.db"

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()


# ===============================
# DISTRICTS TABLE
# ===============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS districts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
""")


# ===============================
# TALUKS TABLE
# ===============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS taluks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_id INTEGER NOT NULL,
    name TEXT NOT NULL,

    FOREIGN KEY (district_id)
    REFERENCES districts(id),

    UNIQUE(district_id, name)
)
""")


# ===============================
# VILLAGES TABLE
# ===============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS villages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taluk_id INTEGER NOT NULL,
    name TEXT NOT NULL,

    FOREIGN KEY (taluk_id)
    REFERENCES taluks(id),

    UNIQUE(taluk_id, name)
)
""")


# ===============================
# INSERT DISTRICTS AND TALUKS
# ===============================

for district_name, taluks in KARNATAKA_TALUKS.items():

    # Insert district
    cursor.execute(
        """
        INSERT OR IGNORE INTO districts (name)
        VALUES (?)
        """,
        (district_name,)
    )

    # Get district ID
    cursor.execute(
        """
        SELECT id
        FROM districts
        WHERE name = ?
        """,
        (district_name,)
    )

    district_id = cursor.fetchone()[0]


    # Insert taluks
    for taluk_name in taluks:

        cursor.execute(
            """
            INSERT OR IGNORE INTO taluks
            (district_id, name)
            VALUES (?, ?)
            """,
            (district_id, taluk_name)
        )


# ===============================
# SAVE DATABASE
# ===============================

connection.commit()


# ===============================
# VERIFICATION
# ===============================

district_count = cursor.execute(
    "SELECT COUNT(*) FROM districts"
).fetchone()[0]

taluk_count = cursor.execute(
    "SELECT COUNT(*) FROM taluks"
).fetchone()[0]

village_count = cursor.execute(
    "SELECT COUNT(*) FROM villages"
).fetchone()[0]


connection.close()


print("Database updated successfully!")
print("Districts:", district_count)
print("Taluks:", taluk_count)
print("Villages:", village_count)