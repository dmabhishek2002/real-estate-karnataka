import sqlite3
from dbfread import DBF

DATABASE = r"C:\RealEstateProject\database\realestate.db"
DBF_FILE = r"C:\RealEstateProject\data\karnataka_villages.zip\vb_soi_ka.dbf"


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


# ==========================================
# CONNECT TO DATABASE
# ==========================================

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()


# ==========================================
# GET DATABASE TALUKS
# ==========================================

cursor.execute("""
SELECT
    taluks.name,
    districts.name
FROM taluks
JOIN districts
ON taluks.district_id = districts.id
ORDER BY districts.name, taluks.name
""")

database_taluks = cursor.fetchall()

connection.close()


print()
print("======================================")
print("TALUK MATCHING CHECK")
print("======================================")
print()

print("Taluks in our database:", len(database_taluks))
print("Reading village dataset...")
print()


# ==========================================
# READ DBF
# ==========================================

table = DBF(
    DBF_FILE,
    load=False,
    encoding="latin1"
)


# ==========================================
# UNIQUE COMBINATIONS
# ==========================================

combinations = set()

for record in table:

    district = record.get("district")
    taluk = record.get("subdistric")

    if district and taluk:

        combinations.add(
            (
                str(district).strip(),
                str(taluk).strip()
            )
        )


print("Unique dataset combinations:", len(combinations))
print()


# ==========================================
# MATCH
# ==========================================

matched = 0
unmatched = []


for dataset_district, dataset_taluk in sorted(combinations):

    found = False

    for database_taluk, database_district in database_taluks:

        if (
            normalize(dataset_district)
            == normalize(database_district)
            and
            normalize(dataset_taluk)
            == normalize(database_taluk)
        ):

            found = True
            break

    if found:

        matched += 1

    else:

        unmatched.append(
            f"{dataset_district} → {dataset_taluk}"
        )


# ==========================================
# RESULT
# ==========================================

print("======================================")
print("MATCHING RESULT")
print("======================================")
print()

print("Matched combinations:", matched)
print("Unmatched combinations:", len(unmatched))
print()


if unmatched:

    print("UNMATCHED COMBINATIONS")
    print("----------------------")

    for item in unmatched:
        print(item)

else:

    print("ALL TALUK COMBINATIONS MATCHED!")


print()
print("======================================")
print("CHECK COMPLETED")
print("======================================")