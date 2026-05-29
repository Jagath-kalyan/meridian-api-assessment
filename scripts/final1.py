import json, hashlib, base64, requests, time

BASE_URL = "https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io"
API_KEY  = "sa_f3702f839dc002fb21fe8e87ab68f4214e587bcce0904e10c1766bb35451e142"
HEADERS  = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

with open("all_records.json") as f:
    all_records = json.load(f)
print(f"Loaded {len(all_records)} records")

# Extract raw base64 strings and binary blobs
raw_strs = [r if isinstance(r, str) else list(r.values())[0] for r in all_records]
blobs    = [base64.b64decode(s) for s in raw_strs]

# ── LAYER 1: Try every hash method, only stop on correct:true ──────────
print("\n=== LAYER 1: CONTENT HASH ===")

candidates = [
    ("sha256_concat_bytes",    hashlib.sha256(b"".join(blobs)).hexdigest()),
    ("sha256_concat_b64str",   hashlib.sha256("".join(raw_strs).encode()).hexdigest()),
    ("sha256_json_compact",    hashlib.sha256(json.dumps(all_records, separators=(",",":")).encode()).hexdigest()),
    ("sha256_json_sorted",     hashlib.sha256(json.dumps(all_records, sort_keys=True, separators=(",",":")).encode()).hexdigest()),
    ("sha256_json_default",    hashlib.sha256(json.dumps(all_records).encode()).hexdigest()),
    ("md5_concat_bytes",       hashlib.md5(b"".join(blobs)).hexdigest()),
    ("md5_json_compact",       hashlib.md5(json.dumps(all_records, separators=(",",":")).encode()).hexdigest()),
    ("sha1_concat_bytes",      hashlib.sha1(b"".join(blobs)).hexdigest()),
    ("sha512_concat_bytes",    hashlib.sha512(b"".join(blobs)).hexdigest()),
]

layer1_done = False
for name, h in candidates:
    print(f"Trying {name}: {h}")
    r = requests.post(f"{BASE_URL}/api/v1/submit", headers=HEADERS,
                      json={"type": "content_hash", "value": h, "notes": name})
    try:
        resp = r.json()
        correct = resp.get("correct", False)
        print(f"  → {r.status_code}: correct={correct} | {resp.get('message','')}")
        if correct:
            print(f"  *** LAYER 1 SOLVED with {name}! ***")
            layer1_done = True
            break
    except:
        print(f"  → {r.status_code}: {r.text[:150]}")
    time.sleep(1)

# ── LAYER 2: Find the key endpoint (expects an integer) ───────────────
print("\n=== LAYER 2: PROBING KEY ENDPOINT ===")

# The error said it tried to parse 'key' as i32 — so try integer paths
for path in [
    "/api/v1/dataset/0",
    "/api/v1/dataset/1",
    "/api/v1/dataset?id=0",
    "/api/v1/dataset?key=0",
    "/api/v1/dataset?key=1",
    "/api/v1/dataset?index=0",
    "/api/v1/dataset/decrypt/0",
    "/api/v1/decrypt/0",
    "/api/v1/key/0",
    "/api/v1/key/1",
]:
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS)
    print(f"  {path} → {r.status_code}: {r.text[:200]}")
    time.sleep(0.3)
