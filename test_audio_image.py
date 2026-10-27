"""
Test audio and image validation via the Dataset Validator API.
Tests both READY and NOT READY scenarios for audio and image datasets.
"""
import requests
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://localhost:8000"

def print_result(label, resp, expected_ready):
    if resp.status_code != 200:
        print(f"  [ERROR] {resp.status_code}: {resp.text[:300]}")
        return None

    d = resp.json()
    qs = d["quality_score"]
    checks = d["checks"]
    issues = d["issues"]
    passed  = sum(1 for c in checks if c["status"] == "pass")
    failed  = sum(1 for c in checks if c["status"] == "fail")
    warned  = sum(1 for c in checks if c["status"] == "warning")
    ready_ok = d["is_ready"] == expected_ready
    ready_icon = "[PASS]" if ready_ok else "[FAIL]"

    print(f"  Score  : {qs['score']} / 100  ({qs['badge']})")
    print(f"  Ready  : {d['is_ready']}  {ready_icon}  (expected: {expected_ready})")
    print(f"  Checks : {len(checks)} total  (pass={passed}  fail={failed}  warn={warned})")
    if issues:
        print(f"  Issues :")
        for iss in issues:
            sev_icon = "[HIGH]" if iss["severity"] == "high" else "[MED]"
            print(f"    {sev_icon} {iss['title']}: {iss['description']}")
    else:
        print(f"  Issues : None")
    print(f"  Session: {d['session_id']}")
    return d["session_id"]


# ======================================================================
print("\n" + "="*60)
print("  AUDIO TESTS")
print("="*60)

# -- Audio Test 1: Clean (READY) ----------------------------------------
print("\n[AUDIO TEST 1] CLEAN AUDIO  -->  Expect: READY = True")
with open("test_audio_clean.zip", "rb") as f:
    resp = requests.post(f"{BASE}/api/validate",
                         files={"file": ("test_audio_clean.zip", f, "application/zip")})
sid_audio_clean = print_result("Clean Audio", resp, expected_ready=True)

# -- Audio Test 2: Messy (NOT READY) ------------------------------------
print("\n[AUDIO TEST 2] MESSY AUDIO  -->  Expect: READY = False")
with open("test_audio_messy.zip", "rb") as f:
    resp = requests.post(f"{BASE}/api/validate",
                         files={"file": ("test_audio_messy.zip", f, "application/zip")})
sid_audio_messy = print_result("Messy Audio", resp, expected_ready=False)


# ======================================================================
print("\n" + "="*60)
print("  IMAGE TESTS")
print("="*60)

# -- Image Test 1: Clean (READY) ----------------------------------------
print("\n[IMAGE TEST 1] CLEAN IMAGES  -->  Expect: READY = True")
with open("test_image_clean.zip", "rb") as f:
    resp = requests.post(f"{BASE}/api/validate",
                         files={"file": ("test_image_clean.zip", f, "application/zip")})
sid_img_clean = print_result("Clean Images", resp, expected_ready=True)

# -- Image Test 2: Messy (NOT READY) ------------------------------------
print("\n[IMAGE TEST 2] MESSY IMAGES  -->  Expect: READY = False")
with open("test_image_messy.zip", "rb") as f:
    resp = requests.post(f"{BASE}/api/validate",
                         files={"file": ("test_image_messy.zip", f, "application/zip")})
sid_img_messy = print_result("Messy Images", resp, expected_ready=False)


# ======================================================================
print("\n" + "="*60)
print("  REPORT GENERATION TESTS")
print("="*60)

# PDF for clean audio
if sid_audio_clean:
    print(f"\n[PDF] Clean Audio Report")
    r = requests.get(f"{BASE}/api/report/pdf/{sid_audio_clean}")
    if r.status_code == 200:
        with open("report_audio_clean.pdf", "wb") as pf:
            pf.write(r.content)
        print(f"  [PASS] {len(r.content):,} bytes -> report_audio_clean.pdf")
    else:
        print(f"  [FAIL] ERROR {r.status_code}: {r.text[:200]}")

# Excel for messy images
if sid_img_messy:
    print(f"\n[EXCEL] Messy Images Report")
    r = requests.get(f"{BASE}/api/report/excel/{sid_img_messy}")
    if r.status_code == 200:
        with open("report_image_messy.xlsx", "wb") as xf:
            xf.write(r.content)
        print(f"  [PASS] {len(r.content):,} bytes -> report_image_messy.xlsx")
    else:
        print(f"  [FAIL] ERROR {r.status_code}: {r.text[:200]}")


# -- History ---------------------------------------------------------------
print(f"\n" + "="*60)
print("  HISTORY  (most recent 6 entries)")
print("="*60)
hist = requests.get(f"{BASE}/api/history")
if hist.status_code == 200:
    for e in hist.json()[:6]:
        status = "[READY]    " if e["is_ready"] else "[NOT READY]"
        print(f"  {status}  {e['filename']:<35}  score={e['quality_score']:5}  badge={e['badge']}")

print("\n" + "="*60)
print("  ALL AUDIO & IMAGE TESTS COMPLETE")
print("="*60 + "\n")
