import sqlite3
from dbfread import DBF

DATABASE = r"C:\RealEstateProject\database\realestate.db"
DBF_FILE = r"C:\RealEstateProject\data\karnataka_villages.zip\vb_soi_ka.dbf"


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize(value):

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace(".", "")
        .replace("'", "")
    )


# =========================================================
# DISTRICT NAME ALIASES
# Dataset name -> Database name
# =========================================================

DISTRICT_ALIASES = {

    "bagalkote": "Bagalkot",

    "chamarajanagara": "Chamarajanagar",

    "chikkamagaluru": "Chikkamagaluru",

    "davangere": "Davanagere",

    "kalaburagi": "Kalaburagi",

    "tumakuru": "Tumkur",

    "shivamogga": "Shivamogga",

    "belagavi": "Belagavi",

    "bengaluru": "Bengaluru",

    "uttarakannada": "Uttara Kannada",

    "dakshin kannada": "Dakshina Kannada",

    "dakshinakannada": "Dakshina Kannada",
}


# =========================================================
# TALUK NAME ALIASES
# Dataset name -> Database name
# =========================================================

TALUK_ALIASES = {

    # -----------------------------------------------------
    # Chikkamagaluru
    # -----------------------------------------------------

    "kadur": "Kaduru",

    "narasimharajapura": "Narasimharajapura",

    # -----------------------------------------------------
    # Davangere
    # -----------------------------------------------------

    "harihar": "Harihara",

    "jagalur": "Jagaluru",

    # -----------------------------------------------------
    # Dharwad
    # -----------------------------------------------------

    "hubballi": "Hubballi",

    "hubballiurban": "Hubballi Urban",

    # -----------------------------------------------------
    # Gadag
    # -----------------------------------------------------

    "gajendragad": "Gajendragada",

    "laxmeshwar": "Lakshmeshwar",

    # -----------------------------------------------------
    # Hassan
    # -----------------------------------------------------

    "hole narsipur": "Holennarasipura",

    "holenarsipur": "Holennarasipura",

    # -----------------------------------------------------
    # Kolar
    # -----------------------------------------------------

    "kolar gold field": "Kolar",

    "kolargoldfield": "Kolar",

    # -----------------------------------------------------
    # Koppal
    # -----------------------------------------------------

    "gangawati": "Gangavathi",

    "koppal": "Koppala",

    "kukunoor": "Kukanuru",

    "yelbarga": "Yelaburga",

    # -----------------------------------------------------
    # Raichur
    # -----------------------------------------------------

    "lingsugur": "Lingasugur",

    "raichur": "Raichuru",

    "sindhnur": "Sindhanur",

    "sirwar": "Sirwar",

    # -----------------------------------------------------
    # Yadgir
    # -----------------------------------------------------

    "gurumitkal": "Gurmitkal",

    "hunasagi": "Hunasagi",

    "shahpur": "Shahpur",

    "shorapur": "Shorapur",

    "wadagera": "Wadgera",

    "yadgir": "Yadgir",

    # -----------------------------------------------------
    # Mysuru
    # -----------------------------------------------------

    "tirumakudálnarsipur": "Tirumakudalu Narasipura",

    "tirumakudalnarsipur": "Tirumakudalu Narasipura",

    # -----------------------------------------------------
    # Bengaluru Rural
    # -----------------------------------------------------

    "doddaballapur": "Doddaballapura",

    # -----------------------------------------------------
    # Chamarajanagar
    # -----------------------------------------------------

    "chamarajanagar": "Chamarajanagar",

    # -----------------------------------------------------
    # Dakshina Kannada
    # -----------------------------------------------------

    "bantval": "Bantwal",

    "moodubidire": "Moodbidri",

    # -----------------------------------------------------
    # Udupi
    # -----------------------------------------------------

    "bainduru": "Byndoor",

    "karkal": "Karkala",

    # -----------------------------------------------------
    # Uttara Kannada
    # -----------------------------------------------------

    "honavar": "Honnavar",

    "karwar": "Karwar",

    "mundgod": "Mundgod",

    "siddapur": "Siddapur",

    "supa": "Joida",

    "yellapur": "Yellapur",
}


# =========================================================
# CONNECT DATABASE
# =========================================================

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()


# =========================================================
# GET ALL TALUKS
# =========================================================

cursor.execute("""
SELECT
    taluks.id,
    taluks.name,
    districts.name
FROM taluks
JOIN districts
ON taluks.district_id = districts.id
""")

taluk_rows = cursor.fetchall()


# =========================================================
# BUILD EXACT DISTRICT + TALUK LOOKUP
# =========================================================

taluk_lookup = {}

for taluk_id, taluk_name, district_name in taluk_rows:

    key = (
        normalize(district_name),
        normalize(taluk_name)
    )

    taluk_lookup[key] = taluk_id


# =========================================================
# BUILD GLOBAL TALUK LOOKUP
#
# Only taluk names that occur ONCE are stored.
# This prevents accidental matching when the same
# taluk name exists in multiple districts.
# =========================================================

global_taluks = {}

for taluk_id, taluk_name, district_name in taluk_rows:

    key = normalize(taluk_name)

    if key not in global_taluks:

        global_taluks[key] = []

    global_taluks[key].append(
        (
            taluk_id,
            district_name,
            taluk_name
        )
    )


# Keep only unique taluk names

unique_taluk_lookup = {}

for key, values in global_taluks.items():

    if len(values) == 1:

        unique_taluk_lookup[key] = values[0]


print()
print("======================================")
print("VILLAGE IMPORT")
print("======================================")
print()

print("Taluks in database:", len(taluk_rows))
print("Reading village dataset...")
print()


# =========================================================
# READ DBF
# =========================================================

table = DBF(
    DBF_FILE,
    load=False,
    encoding="latin1"
)


# =========================================================
# COUNTERS
# =========================================================

inserted = 0
duplicates = 0
skipped = 0

matched_exact = 0
matched_alias = 0
matched_unique_taluk = 0

unmatched = set()


# =========================================================
# IMPORT
# =========================================================

for record in table:

    village_name = record.get("village")

    dataset_district = record.get("district")

    dataset_taluk = record.get("subdistric")

    village_code = record.get("vlcode")

    district_code = record.get("dtcode")

    taluk_code = record.get("sdcode")


    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not village_name:
        skipped += 1
        continue

    if not dataset_district:
        skipped += 1
        continue

    if not dataset_taluk:
        skipped += 1
        continue


    dataset_district = str(dataset_district).strip()
    dataset_taluk = str(dataset_taluk).strip()


    district_key = normalize(dataset_district)

    taluk_key = normalize(dataset_taluk)


    # -----------------------------------------------------
    # IGNORE NON-TALUK ADMINISTRATIVE RECORD
    # -----------------------------------------------------

    if taluk_key.startswith("99999"):
        skipped += 1
        continue


    # =====================================================
    # STEP 1
    # EXACT DISTRICT + TALUK MATCH
    # =====================================================

    lookup_key = (
        district_key,
        taluk_key
    )

    taluk_id = taluk_lookup.get(lookup_key)


    if taluk_id is not None:

        matched_exact += 1


    else:

        # =================================================
        # STEP 2
        # DISTRICT ALIAS + EXACT TALUK
        # =================================================

        database_district_name = DISTRICT_ALIASES.get(
            district_key,
            dataset_district
        )

        alias_key = (
            normalize(database_district_name),
            taluk_key
        )

        taluk_id = taluk_lookup.get(alias_key)


        if taluk_id is not None:

            matched_alias += 1


        else:

            # =============================================
            # STEP 3
            # TALUK NAME ALIAS
            # =============================================

            database_taluk_name = TALUK_ALIASES.get(
                taluk_key,
                dataset_taluk
            )

            alias_taluk_key = normalize(
                database_taluk_name
            )

            alias_lookup_key = (
                normalize(database_district_name),
                alias_taluk_key
            )

            taluk_id = taluk_lookup.get(
                alias_lookup_key
            )


            if taluk_id is not None:

                matched_alias += 1


            else:

                # =========================================
                # STEP 4
                # UNIQUE GLOBAL TALUK MATCH
                #
                # This handles cases where district names
                # changed or were represented differently,
                # but the taluk name itself is unique.
                # =========================================

                global_taluk = unique_taluk_lookup.get(
                    alias_taluk_key
                )

                if global_taluk is not None:

                    taluk_id = global_taluk[0]

                    matched_unique_taluk += 1


                else:

                    # =====================================
                    # NO SAFE MATCH
                    # =====================================

                    unmatched.add(
                        f"{dataset_district} → {dataset_taluk}"
                    )

                    skipped += 1
                    continue


    # =====================================================
    # INSERT VILLAGE
    # =====================================================

    cursor.execute(
        """
        INSERT OR IGNORE INTO villages
        (
            taluk_id,
            name,
            village_code,
            district_code,
            taluk_code
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            taluk_id,
            str(village_name).strip(),
            str(village_code) if village_code else "",
            str(district_code) if district_code else "",
            str(taluk_code) if taluk_code else ""
        )
    )


    if cursor.rowcount > 0:

        inserted += 1

    else:

        duplicates += 1


# =========================================================
# SAVE
# =========================================================

connection.commit()


# =========================================================
# TOTAL VILLAGES
# =========================================================

total_villages = cursor.execute(
    "SELECT COUNT(*) FROM villages"
).fetchone()[0]


connection.close()


# =========================================================
# RESULT
# =========================================================

print()
print("======================================")
print("VILLAGE IMPORT COMPLETED")
print("======================================")
print()

print("Exact matches:", matched_exact)

print("Alias matches:", matched_alias)

print(
    "Unique taluk matches:",
    matched_unique_taluk
)

print()

print("New villages imported:", inserted)

print("Duplicate records ignored:", duplicates)

print("Records skipped:", skipped)

print(
    "Total villages in database:",
    total_villages
)

print(
    "Still unmatched combinations:",
    len(unmatched)
)

print()


# =========================================================
# SHOW UNMATCHED
# =========================================================

if unmatched:

    print("STILL UNMATCHED")
    print("----------------")

    for item in sorted(unmatched):

        print(item)

else:

    print("ALL VILLAGE RECORDS MATCHED!")


print()
print("======================================")