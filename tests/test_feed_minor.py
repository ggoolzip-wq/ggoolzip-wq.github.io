# 패치내역 탭의 '마이너 패치' 수집 (scripts/update_feed.py) — 네트워크 없이 모의 응답으로 확인
import os, sys, json, tempfile, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import update_feed as F
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)

# 1) 제목 매칭 (띄어쓰기·차수 표기)
for t, want in [("[패치완료] 6/23(화) ver1.2.416 마이너(7) 패치(19:21 적용)", True), ("10/8(수) 마이너패치 안내", True),
                ("[패치예정] 10/9(목) 마이너 패치 (오후 3시)", True), ("마이너 ( 12 ) 패치", True), ("[패치완료] 10/8(목) ver1.2.419 마이너버전(8) 패치 (14:00 적용)", True), ("마이너 버전 패치", True),
                ("클라이언트 1.2.419(5) 업데이트 안내", False), ("마이너 갤러리 이벤트", False)]:
    check(f"match {t!r} → {want}", bool(F.MINOR_RE.search(t)) == want)

# 2) 실제 공지사항 목록 HTML(웨이백 사본 2026-06-23) 파싱
html = open(os.path.join(ROOT, "tests", "fixtures", "notice_all.html"), encoding="utf-8").read()
rows = F.parse_notice_list(html, today=datetime.date(2026, 6, 23))
print(len(rows), rows[:2])
check("list parsed (news_board only)", len(rows) >= 10 and all(r["url"].startswith("https://maplestory.nexon.com/News/Notice/") for r in rows))
mi = [r for r in rows if F.MINOR_RE.search(r["title"])]
check("2 minor patches found in real list", [r["n"] for r in mi] == [149386, 149371], [(r["n"], r["title"], r["date"]) for r in mi])
check("today's time-only date → today + PM time", mi[0]["date"] == "2026-06-23T19:22:00+09:00", mi[0]["date"])
check("older date → yyyy-mm-dd", mi[1]["date"] == "2026-06-22T00:00:00+09:00", mi[1]["date"])

# 3) main() 전체: 기존 feed + HTML/API 모의 → 최신 2개만, API 날짜 우선, 제목 갱신, 예전 마이너 글 제거
tmp = tempfile.mkdtemp(); out = os.path.join(tmp, "feed.json")
old = {"version": 1, "updatedAt": "2026-06-23T10:00:00+09:00", "sources": {},
       "state": {"watermarks": {"notice": 149380, "notice-event": 1, "notice-update": 814, "test": 199,
                                **{f"inven:{b}": 1 for b in F.INVEN_BOARDS}}},
       "items": {"patch": [{"id": "update:814", "title": "클라이언트 1.2.419(5) 업데이트 안내", "url": "u", "date": "2026-06-20T09:00:00+09:00"},
                           {"id": "minor:149300", "title": "6/1 마이너 패치", "url": "x", "date": "2026-06-01T00:00:00+09:00", "src": "minor"},
                           {"id": "minor:149371", "title": "[패치예정] 6/22(월) ver1.2.416 마이너(6) 패치", "url": "y", "date": "2026-06-22T00:00:00+09:00", "src": "minor"}]}}
json.dump(old, open(out, "w"), ensure_ascii=False)
F.OUT = out
api_notice = [{"notice_id": 149386, "title": "[패치완료] 6/23(화) ver1.2.416 마이너(7) 패치(19:21 적용)", "url": "https://maplestory.nexon.com/News/Notice/Notice/149386", "date": "2026-06-23T19:22+09:00"},
              {"notice_id": 149380, "title": "기타 공지", "url": "z", "date": "2026-06-23T16:00+09:00"}]
calls = []
def nx(path, **q):
    calls.append(path)
    if path.endswith("/detail"): return {"contents": "<p>공지 본문</p>"}
    return {"notice": {"notice": api_notice}, "notice-event": {"event_notice": []}, "notice-update": {"update_notice": []}}[path]
def http_get(url, headers=None, proxy=False, timeout=25):
    if "News/Notice/All" in url: return 200, html
    raise F.FetchError("blocked in test")
F.nx, F.http_get = nx, http_get
F.time.sleep = lambda s: None
os.environ["FEED_ALL"] = "1"; os.environ.pop("GITHUB_OUTPUT", None)
F.main()
feed = json.load(open(out, encoding="utf-8"))
pt = feed["items"]["patch"]; print(json.dumps(pt, ensure_ascii=False, indent=1))
ids = [x["id"] for x in pt]
check("patch tab = 2 latest minor + update, sorted by date", ids == ["minor:149386", "minor:149371", "update:814"], ids)
check("API date (with time) preferred", pt[0]["date"] == "2026-06-23T19:22:00+09:00", pt[0]["date"])
check("title refreshed ([패치예정] → [패치완료])", pt[1]["title"].startswith("[패치완료] 6/22"), pt[1]["title"])
check("patch source ok", feed["sources"]["patch"]["ok"] is True)
check("no extra API calls for minor patches (only saryo's /notice + detail, /notice-event, /notice-update)", calls == ["notice", "notice/detail", "notice-event", "notice-update"], calls)

# 4) HTML 실패 → API 목록만으로도 유지/갱신, 기존 2개 유지
def http_fail(url, **k): raise F.FetchError("HTTP 403")
F.http_get = http_fail; F.main()
pt2 = json.load(open(out, encoding="utf-8"))["items"]["patch"]
check("HTML blocked: keeps 2 minor items", [x["id"] for x in pt2] == ids, [x["id"] for x in pt2])
# 5) 둘 다 실패 → 패치 탭은 OK(업데이트 공지) + 기존 마이너 글 유지
api_notice.clear(); F.main()
pt3 = json.load(open(out, encoding="utf-8"))["items"]["patch"]
check("HTML + API minor both unavailable: items kept", [x["id"] for x in pt3] == ids, [x["id"] for x in pt3])
# 6) 1쪽에 마이너 패치가 1개뿐이면 다음 쪽까지 (최대 5쪽), 2개 모이면 멈춤
p1 = html.replace("마이너(6) 패치", "정기 패치")
p2 = html.replace("/News/Notice/All/1493", "/News/Notice/All/1492")
pages = []
def http_pages(url, **k):
    pages.append(url)
    return 200, (p2 if "page=2" in url else p1 if "page=" not in url else "<html></html>")
F.http_get = http_pages
fresh = {"version": 1, "updatedAt": "2026-06-23T10:00:00+09:00", "state": {"watermarks": old["state"]["watermarks"]}, "items": {}}
json.dump(fresh, open(out, "w"), ensure_ascii=False); F.main()
pt4 = json.load(open(out, encoding="utf-8"))["items"]["patch"]
check("paging: 2nd minor found on page 2, stops there", [x["id"] for x in pt4] == ["minor:149386", "minor:149286"] and len([u for u in pages if "News/Notice/All" in u]) == 2, ([x["id"] for x in pt4], pages))
pages.clear(); F.main()
check("steady state (2 known): only page 1 fetched", len([u for u in pages if "News/Notice/All" in u]) == 1, pages)
print("FAILS", fails); sys.exit(1 if fails else 0)
