import requests
import json

# ── Test 1: Clean CSV ─────────────────────────────────────────────────────
print("\n=== TEST 1: CLEAN CSV ===")
with open("test_clean.csv", "rb") as f:
    resp = requests.post(
        "http://localhost:8000/api/validate",
        files={"file": ("test_clean.csv", f, "text/csv")}
    )

if resp.status_code == 200:
    data = resp.json()
    qs = data["quality_score"]
    checks = data["checks"]
    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    warned  = sum(1 for c in checks if c["status"] == "warning")
    print(f"  Score  : {qs['score']} / 100  ({qs['badge']})")
    print(f"  Ready  : {data['is_ready']}")
    print(f"  Checks : {len(checks)} total  (pass={passed} fail={failed} warn={warned})")
    print(f"  Issues : {len(data['issues'])}")
    print(f"  Recs   : {len(data['recommendations'])}")
    print(f"  Session: {data['session_id']}")
    CLEAN_SESSION = data["session_id"]
else:
    print(f"  ERROR {resp.status_code}: {resp.text[:300]}")
    CLEAN_SESSION = None

# ── Test 2: Messy CSV ─────────────────────────────────────────────────────
print("\n=== TEST 2: MESSY CSV ===")
with open("test_messy.csv", "rb") as f:
    resp2 = requests.post(
        "http://localhost:8000/api/validate",
        files={"file": ("test_messy.csv", f, "text/csv")}
    )

if resp2.status_code == 200:
    data2 = resp2.json()
    qs2 = data2["quality_score"]
    checks2 = data2["checks"]
    passed2 = sum(1 for c in checks2 if c["status"] == "pass")
    failed2 = sum(1 for c in checks2 if c["status"] == "fail")
    warned2  = sum(1 for c in checks2 if c["status"] == "warning")
    print(f"  Score  : {qs2['score']} / 100  ({qs2['badge']})")
    print(f"  Ready  : {data2['is_ready']}")
    print(f"  Checks : {len(checks2)} total  (pass={passed2} fail={failed2} warn={warned2})")
    print(f"  Issues : {len(data2['issues'])}")
    for issue in data2["issues"]:
        print(f"    - [{issue['severity'].upper()}] {issue['title']}: {issue['description']}")
    print(f"  Recs   : {len(data2['recommendations'])}")
    MESSY_SESSION = data2["session_id"]
else:
    print(f"  ERROR {resp2.status_code}: {resp2.text[:300]}")
    MESSY_SESSION = None

# ── Test 3: Text file ─────────────────────────────────────────────────────
print("\n=== TEST 3: TEXT FILE ===")
with open("test_text.txt", "rb") as f:
    resp3 = requests.post(
        "http://localhost:8000/api/validate",
        files={"file": ("test_text.txt", f, "text/plain")}
    )

if resp3.status_code == 200:
    data3 = resp3.json()
    qs3 = data3["quality_score"]
    print(f"  Score  : {qs3['score']} / 100  ({qs3['badge']})")
    print(f"  Ready  : {data3['is_ready']}")
    print(f"  Checks : {len(data3['checks'])} total")
    print(f"  Session: {data3['session_id']}")
else:
    print(f"  ERROR {resp3.status_code}: {resp3.text[:300]}")

# ── Test 4: History endpoint ───────────────────────────────────────────────
print("\n=== TEST 4: HISTORY API ===")
hist = requests.get("http://localhost:8000/api/history")
if hist.status_code == 200:
    entries = hist.json()
    print(f"  History entries: {len(entries)}")
    for e in entries[:3]:
        print(f"    {e['filename']}  score={e['quality_score']}  badge={e['badge']}")
else:
    print(f"  ERROR {hist.status_code}")

# ── Test 5: Restore result ────────────────────────────────────────────────
if CLEAN_SESSION:
    print("\n=== TEST 5: RESTORE RESULT ===")
    restore = requests.get(f"http://localhost:8000/api/results/{CLEAN_SESSION}")
    if restore.status_code == 200:
        r = restore.json()
        print(f"  Restored: {r['dataset_info']['filename']}  score={r['quality_score']['score']}")
    else:
        print(f"  ERROR {restore.status_code}: {restore.text[:200]}")

# ── Test 6: PDF report generation ─────────────────────────────────────────
if CLEAN_SESSION:
    print("\n=== TEST 6: PDF REPORT ===")
    pdf = requests.get(f"http://localhost:8000/api/report/pdf/{CLEAN_SESSION}")
    if pdf.status_code == 200:
        with open("test_report.pdf", "wb") as pf:
            pf.write(pdf.content)
        print(f"  PDF generated: {len(pdf.content)} bytes -> test_report.pdf")
    else:
        print(f"  ERROR {pdf.status_code}: {pdf.text[:200]}")

# ── Test 7: Excel report generation ───────────────────────────────────────
if MESSY_SESSION:
    print("\n=== TEST 7: EXCEL REPORT ===")
    xl = requests.get(f"http://localhost:8000/api/report/excel/{MESSY_SESSION}")
    if xl.status_code == 200:
        with open("test_report.xlsx", "wb") as xf:
            xf.write(xl.content)
        print(f"  Excel generated: {len(xl.content)} bytes -> test_report.xlsx")
    else:
        print(f"  ERROR {xl.status_code}: {xl.text[:200]}")

print("\n=== ALL BACKEND TESTS COMPLETE ===")
