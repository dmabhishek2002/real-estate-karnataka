import sqlite3

DATABASE = "database/realestate.db"


connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    district_id INTEGER NOT NULL,
    taluk_id INTEGER,
    village_id INTEGER,

    title TEXT NOT NULL,

    property_type TEXT NOT NULL,

    bhk INTEGER,

    area_sqft REAL,

    price REAL,

    price_per_sqft REAL,

    source TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (district_id)
        REFERENCES districts(id),

    FOREIGN KEY (taluk_id)
        REFERENCES taluks(id),

    FOREIGN KEY (village_id)
        REFERENCES villages(id)
)
""")


connection.commit()


cursor.execute("""
SELECT COUNT(*)
FROM properties
""")

count = cursor.fetchone()[0]


print("Property table is ready.")
print("Current property records:", count)


connection.close()