import requests
import hashlib
import json

BASE_URL = "https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io"
API_KEY = "sa_f3702f839dc002fb21fe8e87ab68f4214e587bcce0904e10c1766bb35451e142"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Step 1: Use batch endpoint to get ALL data efficiently (saves rate limit!)
print("=== FETCHING FULL BATCH DATASET ===")
r = requests.get(f"{BASE_URL}/api/v1/dataset?batch=true&range=0-99", headers=headers)
print(f"Status: {r.status_code}")
print(f"ETag: {r.headers.get('etag')}")
data = r.json()
print(f"Keys: {list(data.keys())}")
print(f"Total records: {data.get('total')}")
print(f"Has more: {data.get('has_more')}")
print(f"Page size: {data.get('page_size')}")

# Save full response
with open("dataset.json", "w") as f:
    json.dump(data, f, indent=2)
print("Saved to dataset.json")

# Show first record structure
records = data.get("data", [])
print(f"\nNumber of records: {len(records)}")
if records:
    print(f"\nFirst record sample:")
    print(json.dumps(records[0], indent=2)[:500])
    print(f"\nLast record sample:")
    print(json.dumps(records[-1], indent=2)[:500])

# Step 2: Check stats endpoint
print("\n=== CHECKING STATS ===")
r2 = requests.get(f"{BASE_URL}/api/v1/stats", headers=headers)
print(f"Status: {r2.status_code}")
print(r2.text[:1000])

# Step 3: Compute integrity hash
print("\n=== COMPUTING INTEGRITY HASH ===")
raw = json.dumps(records, sort_keys=True, separators=(',', ':')).encode()
sha256 = hashlib.sha256(raw).hexdigest()
md5 = hashlib.md5(raw).hexdigest()
print(f"SHA256: {sha256}")
print(f"MD5: {md5}")
print(f"ETag from header: {r.headers.get('etag')}")
