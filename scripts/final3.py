import json, hashlib, base64, requests, time

BASE_URL = "https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io"
API_KEY  = "sa_f3702f839dc002fb21fe8e87ab68f4214e587bcce0904e10c1766bb35451e142"
HEADERS  = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# ── Fetch ALL 529 records ──────────────────────────────────────────────
print("=== FETCHING ALL 529 RECORDS ===")
all_records = []

for start in range(0, 530, 100):
    end = min(start + 99, 529)
    url = f"{BASE_URL}/api/v1/dataset?batch=true&range={start}-{end}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 429:
        wait = int(r.headers.get("Retry-After", 5))
        print(f"  Rate limited, waiting {wait}s...")
        time.sleep(wait)
        r = requests.get(url, headers=HEADERS, timeout=15)
    data = r.json()
    batch = data.get("data", [])
    all_records.extend(batch)
    print(f"  Range {start}-{end}: got {len(batch)}, total={len(all_records)}")
    time.sleep(0.5)

print(f"\nTotal fetched: {len(all_records)}  (expected 529)")

with open("all_records_529.json", "w") as f:
    json.dump(all_records, f)

# ── Hash attempts ──────────────────────────────────────────────────────
raw_strs = [r if isinstance(r, str) else list(r.values())[0] for r in all_records]
blobs    = [base64.b64decode(s) for s in raw_strs]

print("\n=== LAYER 1: HASH ATTEMPTS ===")
candidates = [
    ("sha256_concat_bytes",  hashlib.sha256(b"".join(blobs)).hexdigest()),
    ("sha256_concat_b64str", hashlib.sha256("".join(raw_strs).encode()).hexdigest()),
    ("sha256_json_compact",  hashlib.sha256(json.dumps(all_records, separators=(",",":")).encode()).hexdigest()),
    ("sha256_json_sorted",   hashlib.sha256(json.dumps(all_records, sort_keys=True, separators=(",",":")).encode()).hexdigest()),
    ("sha256_newline_b64",   hashlib.sha256("\n".join(raw_strs).encode()).hexdigest()),
    ("md5_concat_bytes",     hashlib.md5(b"".join(blobs)).hexdigest()),
    ("md5_concat_b64str",    hashlib.md5("".join(raw_strs).encode()).hexdigest()),
]

for name, h in candidates:
    print(f"Trying {name}: {h}")
    r = requests.post(f"{BASE_URL}/api/v1/submit", headers=HEADERS,
                      json={"type": "content_hash", "value": h, "notes": name})
    resp = r.json()
    correct = resp.get("correct", False)
    print(f"  → correct={correct} | {resp.get('message','')[:80]}")
    if correct:
        print(f"\n  *** LAYER 1 SOLVED with {name}! ***")
        # Check if response contains key or next step info
        print(f"  Full response: {json.dumps(resp, indent=2)}")
        break
    time.sleep(1)
