import json, hashlib, base64, requests, time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

BASE_URL = "https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io"
API_KEY  = "sa_f3702f839dc002fb21fe8e87ab68f4214e587bcce0904e10c1766bb35451e142"
HEADERS  = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

with open("all_records_529.json") as f:
    all_records = json.load(f)
print(f"Loaded {len(all_records)} records")

raw_strs = [r if isinstance(r, str) else list(r.values())[0] for r in all_records]
blobs    = [base64.b64decode(s) for s in raw_strs]

# ── Fetch the decryption key (Layer 1 solved = key should now unlock) ──
print("\n=== FETCHING DECRYPTION KEY ===")

# The submission_id from Layer 1 solve
submission_id = "db4b934b-48e4-4090-9c68-5cd6c0eb4be6"

key_bytes = None
for path in [
    f"/api/v1/dataset/key?submission_id={submission_id}",
    f"/api/v1/dataset/{submission_id}",
    "/api/v1/dataset/key",
    "/api/v1/session",
    "/api/v1/challenge",
    "/api/v1/info",
]:
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS)
    print(f"{path} → {r.status_code}: {r.text[:300]}")
    if r.status_code == 200:
        try:
            data = r.json()
            # Look for a key field
            for field in ["key", "secret", "encryption_key", "aes_key", "decryption_key", "value", "token"]:
                if field in data:
                    raw_key = data[field]
                    print(f"  *** Found key field '{field}': {raw_key}")
                    # Parse as hex
                    try:
                        key_bytes = bytes.fromhex(raw_key)
                        print(f"  Parsed as hex: {len(key_bytes)} bytes")
                    except:
                        try:
                            key_bytes = base64.b64decode(raw_key + "==")
                            print(f"  Parsed as base64: {len(key_bytes)} bytes")
                        except:
                            key_bytes = raw_key.encode()[:32].ljust(32, b'\x00')
                    break
        except:
            pass
    time.sleep(0.3)

# ── Try decrypting with the key ────────────────────────────────────────
def try_decrypt(key_bytes, blob):
    # Try AES-CBC
    try:
        iv, ct = blob[:16], blob[16:]
        c = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
        pt = c.decryptor().update(ct) + c.decryptor().finalize()
        pad = pt[-1]
        if 1 <= pad <= 16: pt = pt[:-pad]
        text = pt.decode("utf-8", errors="replace")
        score = sum(1 for ch in text if 32 <= ord(ch) < 127) / max(len(text), 1)
        if score > 0.7:
            return text
    except: pass
    # Try AES-GCM
    try:
        pt = AESGCM(key_bytes).decrypt(blob[:12], blob[12:], None)
        return pt.decode("utf-8", errors="replace")
    except: pass
    return None

if key_bytes and len(key_bytes) in (16, 24, 32):
    print(f"\n=== DECRYPTING {len(blobs)} RECORDS ===")
    plaintexts = [try_decrypt(key_bytes, b) for b in blobs]
    good = [p for p in plaintexts if p]
    print(f"Successfully decrypted: {len(good)}/{len(blobs)}")
    if good:
        print(f"Sample: {good[0][:200]}")

        # Layer 2 hash
        print("\n=== LAYER 2: SUBMIT DECRYPTED HASH ===")
        combined = "".join(good)
        for name, h in [
            ("sha256_concat",  hashlib.sha256(combined.encode()).hexdigest()),
            ("sha256_bytes",   hashlib.sha256(b"".join(p.encode() for p in good)).hexdigest()),
            ("md5_concat",     hashlib.md5(combined.encode()).hexdigest()),
        ]:
            print(f"Trying {name}: {h}")
            r = requests.post(f"{BASE_URL}/api/v1/submit", headers=HEADERS,
                              json={"type": "decrypted_hash", "value": h, "notes": name})
            resp = r.json()
            print(f"  → correct={resp.get('correct')} | {resp.get('message','')[:80]}")
            if resp.get("correct"):
                print("  *** LAYER 2 SOLVED! ***")
                print(f"  Full: {json.dumps(resp, indent=2)}")
                break
            time.sleep(1)

        # Layer 3 preview
        print("\n=== LAYER 3 PREVIEW: INSPECTING RECORDS ===")
        json_records = []
        for p in good:
            try: json_records.append(json.loads(p))
            except: json_records.append({"raw": p})
        
        all_keys = {}
        for rec in json_records:
            if isinstance(rec, dict):
                for k in rec: all_keys[k] = all_keys.get(k, 0) + 1
        print(f"Field names: {sorted(all_keys.items(), key=lambda x: -x[1])}")
        print(f"\nSample record 0: {json.dumps(json_records[0], indent=2)[:300]}")
        print(f"Sample record 1: {json.dumps(json_records[1], indent=2)[:300]}")
else:
    print("\n⚠️  No key found yet — paste output above and we'll figure out the key endpoint.")
