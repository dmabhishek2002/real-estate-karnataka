import sqlite3

DATABASE = "database/realestate.db"


properties = [
    # Bengaluru
    {
        "district_id": 4,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Modern 2 BHK Apartment",
        "property_type": "Apartment",
        "bhk": 2,
        "area_sqft": 1150,
        "price": 7200000
    },
    {
        "district_id": 4,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Premium 3 BHK Apartment",
        "property_type": "Apartment",
        "bhk": 3,
        "area_sqft": 1550,
        "price": 10500000
    },

    # Ballari
    {
        "district_id": 2,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Residential House",
        "property_type": "House",
        "bhk": 3,
        "area_sqft": 1800,
        "price": 4800000
    },

    # Mysuru
    {
        "district_id": 20,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Mysuru Family Home",
        "property_type": "House",
        "bhk": 3,
        "area_sqft": 1650,
        "price": 6200000
    },

    # Dharwad
    {
        "district_id": 7,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Dharwad Residential Plot",
        "property_type": "Plot",
        "bhk": None,
        "area_sqft": 1200,
        "price": 3000000
    },

    # Hubballi
    {
        "district_id": 7,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Hubballi 2 BHK Apartment",
        "property_type": "Apartment",
        "bhk": 2,
        "area_sqft": 1100,
        "price": 4200000
    },

    # Tumakuru
    {
        "district_id": 25,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Tumakuru Villa",
        "property_type": "Villa",
        "bhk": 3,
        "area_sqft": 1900,
        "price": 5500000
    },

    # Hassan
    {
        "district_id": 9,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Hassan Independent House",
        "property_type": "House",
        "bhk": 2,
        "area_sqft": 1400,
        "price": 3600000
    },

    # Belagavi
    {
        "district_id": 3,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Belagavi 3 BHK Home",
        "property_type": "House",
        "bhk": 3,
        "area_sqft": 1750,
        "price": 4600000
    },

    # Shivamogga
    {
        "district_id": 24,
        "taluk_id": 0,
        "village_id": 0,
        "title": "Shivamogga Family Villa",
        "property_type": "Villa",
        "bhk": 3,
        "area_sqft": 2100,
        "price": 5800000
    }
]


connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_id INTEGER,
    taluk_id INTEGER,
    village_id INTEGER,
    title TEXT NOT NULL,
    property_type TEXT NOT NULL,
    bhk INTEGER,
    area_sqft REAL NOT NULL,
    price REAL NOT NULL,
    price_per_sqft REAL NOT NULL,
    FOREIGN KEY (district_id) REFERENCES districts(id),
    FOREIGN KEY (taluk_id) REFERENCES taluks(id),
    FOREIGN KEY (village_id) REFERENCES villages(id)
)
""")


cursor.execute("SELECT COUNT(*) FROM properties")
existing_count = cursor.fetchone()[0]

if existing_count == 0:

    for property_data in properties:

        price_per_sqft = (
            property_data["price"] /
            property_data["area_sqft"]
        )

        cursor.execute("""
            INSERT INTO properties (
                district_id,
                taluk_id,
                village_id,
                title,
                property_type,
                bhk,
                area_sqft,
                price,
                price_per_sqft
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            property_data["district_id"],
            property_data["taluk_id"],
            property_data["village_id"],
            property_data["title"],
            property_data["property_type"],
            property_data["bhk"],
            property_data["area_sqft"],
            property_data["price"],
            price_per_sqft
        ))

    print("Property demo data inserted successfully.")

else:
    print(f"Properties table already contains {existing_count} records.")


connection.commit()
connection.close()

print("Property database setup completed.")