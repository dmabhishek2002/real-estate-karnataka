from dbfread import DBF

DBF_FILE = r"C:\RealEstateProject\data\karnataka_villages.zip\vb_soi_ka.dbf"

table = DBF(
    DBF_FILE,
    load=False,
    encoding="latin1"
)

print("\n==============================")
print("VILLAGE DATASET INFORMATION")
print("==============================\n")

print("Number of fields:", len(table.field_names))

print("\nFIELD NAMES:")
print("------------------------------")

for field in table.field_names:
    print(field)

print("\n==============================")
print("FIRST 5 RECORDS")
print("==============================\n")

for index, record in enumerate(table):

    print("RECORD", index + 1)
    print("------------------------------")

    for field in table.field_names:
        print(f"{field}: {record[field]}")

    print()

    if index == 4:
        break