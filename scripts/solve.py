import requests
import hashlib
import json

BASE_URL = "https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io"
API_KEY = "sa_f3702f839dc002fb21fe8e87ab68f4214e587bcce0904e10c1766bb35451e142"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Step 1: Fetch dataset
print("=== FETCHING DATASET ===")
r = requests.get(f"{BASE_URL}/api/v1/dataset", headers=headers)
print(f"Status: {r.status_code}")
print(f"\n=== RESPONSE HEADERS ===")
for k, v in r.headers.items():
    print(f"{k}: {v}")

data = r.json()
print(f"\n=== RESPONSE KEYS ===")
print(list(data.keys()))
print(f"\n=== FULL RESPONSE ===")
print(json.dumps(data, indent=2)[:2000])

# Step 2: Try submit endpoint options
print("\n=== PROBING SUBMIT ===")
r2 = requests.post(f"{BASE_URL}/api/v1/submit", headers=headers, json={"type": "test"})
print(f"Status: {r2.status_code}")
print(r2.text[:500])

# Step 3: Check remaining time
print("\n=== CHECKING TIME ===")
for endpoint in ["/api/v1/remaining", "/api/v1/clock", "/api/v1/timer", "/api/v1/window"]:
    r3 = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    if r3.status_code != 404:
        print(f"{endpoint} → {r3.status_code}: {r3.text[:200]}")
