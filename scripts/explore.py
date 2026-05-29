import requests

BASE_URL = "https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io"
API_KEY = "sa_f3702f839dc002fb21fe8e87ab68f4214e587bcce0904e10c1766bb35451e142"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

endpoints = [
    "/api/v1/status",
    "/api/v1/time",
    "/api/v1/session",
    "/api/v1/data",
    "/api/v1/dataset",
    "/api/v1/records",
    "/api/v1/key",
    "/api/v1/submit",
    "/api/v1/challenge",
    "/api/v1/info",
]

print("=== PROBING ENDPOINTS ===\n")
for endpoint in endpoints:
    r = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    print(f"{endpoint} → {r.status_code}: {r.text[:200]}")
    print()
