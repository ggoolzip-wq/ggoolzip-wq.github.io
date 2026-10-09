# 넥슨 키 2개 전환 (scripts/update_feed.py nx) — 모의 응답
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import update_feed as F
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
used = []; MODE = {"k1": "ok"}
def http_get(url, headers=None, **k):
    key = headers["x-nxopen-api-key"]; used.append(key)
    if key == "K1":
        m = MODE["k1"]
        if m == "429": raise F.FetchError("HTTP 429", 429, '{"error":{"name":"OPENAPI00007","message":"Too many request"}}')
        if m == "quota": raise F.FetchError("HTTP 400", 400, '{"error":{"name":"OPENAPI00007","message":"quota exceeded"}}')
        if m == "invalid": raise F.FetchError("HTTP 400", 400, '{"error":{"name":"OPENAPI00005","message":"Please input valid parameter"}}')
        if m == "badparam": raise F.FetchError("HTTP 400", 400, '{"error":{"name":"OPENAPI00004","message":"Please input valid parameter"}}')
    if key == "K2" and MODE.get("k2") == "429": raise F.FetchError("HTTP 429", 429, '{"error":{"name":"OPENAPI00007"}}')
    return 200, json.dumps({"by": key})
F.http_get = http_get
def reset(k1, k2="ok"):
    used.clear(); F._BAD_KEYS.clear(); MODE["k1"] = k1; MODE["k2"] = k2
os.environ["NEXON_API_KEY"] = "K1"; os.environ["NEXON_API_KEY2"] = "K2"
reset("ok"); check("key 1 used when fine", F.nx("notice") == {"by": "K1"} and used == ["K1"], used)
for m in ["429", "quota", "invalid"]:
    reset(m); r = F.nx("notice"); check(f"key 1 {m} → falls back to key 2", r == {"by": "K2"} and used == ["K1", "K2"], used)
reset("429"); F.nx("notice"); used.clear(); F.nx("notice-update")
check("after key 1 is blocked, later calls go straight to key 2", used == ["K2"], used)
reset("badparam")
try: F.nx("notice"); ok = False
except F.FetchError: ok = True
check("other errors (bad parameter) do not switch keys", ok and used == ["K1"], used)
reset("429", "429")
try: F.nx("notice"); ok = False
except F.FetchError as e: ok = e.status == 429
check("both keys blocked → error raised", ok and used == ["K1", "K2"], used)
del os.environ["NEXON_API_KEY2"]; reset("429")
try: F.nx("notice"); ok = False
except F.FetchError: ok = True
check("no key 2 → original error", ok and used == ["K1"], used)
os.environ["NEXON_API_KEY"] = ""; os.environ["NEXON_API_KEY2"] = "K2"; reset("ok")
check("only key 2 set → uses it", F.nx("notice") == {"by": "K2"}, used)
wf = open(os.path.join(ROOT, ".github", "workflows", "update-feed.yml")).read()
check("workflow passes NEXON_API_KEY2 secret", "NEXON_API_KEY2: ${{ secrets.NEXON_API_KEY2 }}" in wf)
print("FAILS", fails); sys.exit(1 if fails else 0)
