import json, hashlib, base64, requests, time

BASE_URL = "https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io"
API_KEY  = "sa_f3702f839dc002fb21fe8e87ab68f4214e587bcce0904e10c1766bb35451e142"
HEADERS  = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

with open("all_records.json") as f:
    all_records = json.load(f)

raw_strs = [r if isinstance(r, str) else list(r.values())[0] for r in all_records]
blobs    = [base64.b64decode(s) for s in raw_strs]

# ── LAYER 1: The API likely wants hash of JUST the base64 strings ──────
# sorted, one per line, or hashed individually then combined
print("=== LAYER 1: NEW HASH ATTEMPTS ===")

# Each record hashed individually, then those hashes concatenated and hashed
individual_hashes = [hashlib.sha256(b).hexdigest() for b in blobs]
combined_hash_str = "".join(individual_hashes)

# Also try hashing the newline-joined base64 strings (common API pattern)
newline_joined     = "\n".join(raw_strs)
newline_joined_nl  = "\n".join(raw_strs) + "\n"  # trailing newline

candidates = [
    ("sha256_of_sha256s",        hashlib.sha256(combined_hash_str.encode()).hexdigest()),
    ("sha256_newline_b64",       hashlib.sha256(newline_joined.encode()).hexdigest()),
    ("sha256_newline_b64_trail", hashlib.sha256(newline_joined_nl.encode()).hexdigest()),
    ("md5_newline_b64",          hashlib.md5(newline_joined.encode()).hexdigest()),
    # Hash the sorted base64 strings
    ("sha256_sorted_b64",        hashlib.sha256("\n".join(sorted(raw_strs)).encode()).hexdigest()),
    # Hash just record count as sanity
    ("sha256_each_then_xor",     ""),  # placeholder, computed below
]

# XOR all individual sha256s together
xor_result = bytes(len(individual_hashes[0])//2 * [0])
# Actually: XOR the raw digest bytes
xor_bytes = bytes(32)
for b in blobs:
    h = hashlib.sha256(b).digest()
    xor_bytes = bytes(a ^ b for a, b in zip(xor_bytes, h))
candidates[5] = ("sha256_xor_all_digests", xor_bytes.hex())

for name, h in candidates:
    if not h:
        continue
    print(f"Trying {name}: {h}")
    r = requests.post(f"{BASE_URL}/api/v1/submit", headers=HEADERS,
                      json={"type": "content_hash", "value": h, "notes": name})
    resp = r.json()
    correct = resp.get("correct", False)
    print(f"  → correct={correct} | {resp.get('message','')[:80]}")
    if correct:
        print(f"  *** LAYER 1 SOLVED! ***")
        break
    time.sleep(1)

# ── LAYER 2: Find the ACTUAL decryption key ────────────────────────────
print("\n=== LAYER 2: FINDING REAL KEY ENDPOINT ===")

# The stats endpoint often reveals hints
for path in ["/api/v1/stats", "/api/v1/info", "/api/v1/health",
             "/api/v1/session", "/api/v1/challenge"]:
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS)
    if r.status_code == 200:
        print(f"\n{path} → 200:")
        try:
            print(json.dumps(r.json(), indent=2)[:500])
        except:
            print(r.text[:300])
    time.sleep(0.3)

# Check if submitting a correct Layer 1 UNLOCKS the key endpoint
# Try fetching key after a correct layer1 submission
print("\n=== CHECKING IF LAYER 1 UNLOCK REVEALS KEY ===")
r = requests.get(f"{BASE_URL}/api/v1/dataset/key", headers=HEADERS)
print(f"/api/v1/dataset/key → {r.status_code}: {r.text[:300]}")

# Also try the submission_id from our previous submit as a token
submission_id = "6dc55ce4-c82f-4531-8e2f-38db16cc5e3a"
r = requests.get(f"{BASE_URL}/api/v1/dataset/key",
                 headers={**HEADERS, "X-Submission-ID": submission_id})
print(f"with X-Submission-ID → {r.status_code}: {r.text[:200]}")

# Try fetching key with submission_id as query param
r = requests.get(f"{BASE_URL}/api/v1/dataset/key?submission_id={submission_id}", headers=HEADERS)
print(f"?submission_id= → {r.status_code}: {r.text[:200]}")
