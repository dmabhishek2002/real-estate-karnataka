import requests

URL = "https://mobservice.sujala3lri.karnataka.gov.in/api/GetdssDistrict"

params = {
    "culture": 1
}

print("Connecting to Karnataka Government API...")
print("URL:", URL)

try:
    response = requests.get(URL, params=params, timeout=30)

    print("\nHTTP Status:", response.status_code)
    print("\nServer Response:")
    print(response.text[:2000])

except requests.RequestException as error:
    print("\nConnection Error:")
    print(error)