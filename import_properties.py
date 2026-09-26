import csv
import sqlite3

DATABASE = "database/realestate.db"
CSV_FILE = "data/properties.csv"


def normalize(value):
    return str(value).strip().lower()


connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

inserted = 0
skipped = 0

with open(CSV_FILE, "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        district_name = row["District"].strip()
        taluk_name = row["Taluk"].strip()
        village_name = row["Village"].strip()
        title = row["Title"].strip()
        property_type = row["Property Type"].strip()

        bhk = row["BHK"].strip()
        area = row["Area Sqft"].strip()
        price = row["Price"].strip()
        source = row["Source"].strip()

        if not district_name or not title or not property_type:
            skipped += 1
            continue

        # Find district
        district = cursor.execute(
            """
            SELECT id
            FROM districts
            WHERE lower(name) = ?
            """,
            (normalize(district_name),)
        ).fetchone()

        if not district:
            print("District not found:", district_name)
            skipped += 1
            continue

        district_id = district[0]

        # Find taluk
        taluk = cursor.execute(
            """
            SELECT id
            FROM taluks
            WHERE district_id = ?
            AND lower(name) = ?
            """,
            (district_id, normalize(taluk_name))
        ).fetchone()

        taluk_id = taluk[0] if taluk else None

        # Find village
        village_id = None

        if taluk_id and village_name:
            village = cursor.execute(
                """
                SELECT id
                FROM villages
                WHERE taluk_id = ?
                AND lower(name) = ?
                """,
                (taluk_id, normalize(village_name))
            ).fetchone()

            if village:
                village_id = village[0]

        # Convert numbers
        try:
            bhk_value = int(bhk) if bhk else None
        except ValueError:
            bhk_value = None

        try:
            area_value = float(area) if area else None
        except ValueError:
            area_value = None

        try:
            price_value = float(price) if price else None
        except ValueError:
            price_value = None

        # Calculate price per square foot
        price_per_sqft = None

        if area_value and area_value > 0 and price_value is not None:
            price_per_sqft = price_value / area_value

        cursor.execute(
            """
            INSERT INTO properties (
                district_id,
                taluk_id,
                village_id,
                title,
                property_type,
                bhk,
                area_sqft,
                price,
                price_per_sqft,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                district_id,
                taluk_id,
                village_id,
                title,
                property_type,
                bhk_value,
                area_value,
                price_value,
                price_per_sqft,
                source
            )
        )

        inserted += 1


connection.commit()
connection.close()

print()
print("Property import completed.")
print("Properties inserted:", inserted)
print("Rows skipped:", skipped)