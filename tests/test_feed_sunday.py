# 썬데이 메이플 수집 (scripts/update_feed.py src_sunday) — 네트워크 없이 모의 응답
import os, sys, json, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import update_feed as F
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
FX = lambda n: open(os.path.join(ROOT, "tests", "fixtures", n), encoding="utf-8").read()
# 1) 제목 매칭·글 페이지 파싱 (실제 공지 1317 웨이백 사본)
check("SUNDAY_RE", all(F.SUNDAY_RE.search(t) for t in ["썬데이 메이플", "스페셜 썬데이메이플", "썬데이  메이플"]) and not F.SUNDAY_RE.search("메이플 선데이"))
img, st, en, title = F.parse_event_page(FX("event_sunday_1317.html"))
check("event page → main image (not absolute-positioned gif)", img == "https://lwi.nexon.com/maplestory/2026/0508_board/C30CA4F4E37C4D04.png", img)
check("event period parsed", st == "2026-05-10T00:00:00+09:00" and en == "2026-05-10T23:59:00+09:00", (st, en))
check("title without '수정' badge", title == "스페셜 썬데이 메이플", title)
closed = F.parse_event_list(FX("event_closed.html"))
check("closed-events list parsed (sunday posts found)", [n for n, v in closed.items() if F.SUNDAY_RE.search(v["title"])][:1] == [1354], list(closed.items())[:3])
# 2) 혜택 한 줄
b, how = F.sunday_benefit("스페셜 썬데이 메이플", "미라클 타임 잠재능력 등급 상승 확률 2배! 몬스터파크 클리어 경험치 추가 250%")
check("benefit from text: 미라클 타임 + 몬스터파크 250%", how == "text" and b.startswith("미라클 타임") and "250%" in b, b)
b, how = F.sunday_benefit("썬데이 메이플", "스타포스 강화 비용 30% 할인 이벤트")
check("benefit from text: 스타포스 할인", how == "text" and "스타포스" in b and "할인" in b, b)
b, how = F.sunday_benefit("썬데이 메이플", "주말을 더 즐겁게 보내세요! 공지 내용 일부를 수정하였습니다.")
check("no keyword → short summary sentence", how == "summary" and b == "주말을 더 즐겁게 보내세요!", (b, how))
check("nothing → '' (site shows title)", F.sunday_benefit("스페셜 썬데이 메이플", "") == ("", ""))
# 3) 1순위 API: /notice-event 목록(사료감지 재사용) + /notice-event/detail 1회
tmp = tempfile.mkdtemp(); out = os.path.join(tmp, "feed.json"); F.OUT = out
WM = {"notice": 1, "notice-event": 1399, "notice-update": 1, "minor": 1, "test": 1, **{f"inven:{b}": 1 for b in F.INVEN_BOARDS}}
json.dump({"version": 1, "updatedAt": "2026-10-09T10:00:00+09:00", "state": {"watermarks": WM}, "items": {}}, open(out, "w"))
EVENTS = [{"notice_id": 1399, "title": "스페셜 썬데이 메이플", "url": "https://maplestory.nexon.com/News/Event/1399", "date": "2026-10-09T10:00+09:00",
           "date_event_start": "2026-10-11T00:00+09:00", "date_event_end": "2026-10-11T23:59+09:00", "thumbnail_url": "https://file.nexon.com/thumb1399"},
          {"notice_id": 1398, "title": "다른 이벤트", "url": "u", "date": "2026-10-08T10:00+09:00"}]
DETAIL = {"contents": '<div class="gen_container"><img src="https://lwi.nexon.com/maplestory/2026/1009_board/SUN.png" style="width: 100%"><p>미라클 타임</p></div>',
          "date_event_start": "2026-10-11T00:00+09:00", "date_event_end": "2026-10-11T23:59+09:00"}
calls, pages = [], []
def nx(path, **q):
    calls.append(path)
    if path == "notice-event/detail": return DETAIL
    if path == "notice": return {"notice": []}
    if path == "notice-event": return {"event_notice": EVENTS}
    if path == "notice-update": return {"update_notice": []}
def http_get(url, **k):
    pages.append(url)
    if "/News/Event/Closed" in url: return 200, FX("event_closed.html")
    if "/News/Event/Ongoing" in url: return 200, FX("event_ongoing.html")
    if "/News/Event/" in url: return 200, FX("event_sunday_1317.html")
    raise F.FetchError("blocked")
F.nx, F.http_get = nx, http_get; F.time.sleep = lambda s: None
os.environ["FEED_ALL"] = "1"; os.environ["NEXON_API_KEY"] = "test"; os.environ.pop("GITHUB_OUTPUT", None)
load = lambda: json.load(open(out, encoding="utf-8"))
F.main(); sd = load().get("sunday", {})
print(sd)
check("API: sunday from /notice-event list + detail image", sd.get("id") == 1399 and sd.get("image", "").endswith("/SUN.png") and sd.get("via") == "api", sd)
check("API: period, url, benefit from detail text", sd.get("start") == "2026-10-11T00:00:00+09:00" and sd.get("url").endswith("/1399") and sd.get("benefit") == "미라클 타임", sd)
check("API path: exactly 1 detail call, no homepage event pages", calls.count("notice-event/detail") == 1 and not [u for u in pages if "/News/Event" in u], (calls, pages))
calls.clear(); pages.clear(); F.main()
check("same sunday next run: no detail call (0 extra API calls)", "notice-event/detail" not in calls, calls)
# 4) API 목록 실패 + 저장된 것 없음 → HTML 대체(진행 중 + 종료 검색) → 글 페이지, detail 도 실패하면 HTML 글 페이지
json.dump({"version": 1, "updatedAt": "2026-10-09T10:00:00+09:00", "state": {"watermarks": WM}, "items": {}}, open(out, "w"))
def nx_fail(path, **q):
    calls.append(path)
    if path in ("notice-event", "notice-event/detail"): raise F.FetchError("HTTP 429")
    return nx(path, **q)
F.nx = nx_fail; calls.clear(); pages.clear(); F.main(); sd = load().get("sunday", {})
check("fallback: HTML search finds latest sunday (1354), image from post page", sd.get("id") == 1354 and sd.get("image", "").endswith("C30CA4F4E37C4D04.png") and sd.get("via") == "html", sd)
check("fallback: no benefit text in image-only post → empty (site shows title)", not sd.get("benefit"), sd.get("benefit"))
# 5) 아무것도 없음 → sunday 없음(사이트 안내 문구)
json.dump({"version": 1, "updatedAt": "2026-10-09T10:00:00+09:00", "state": {"watermarks": WM}, "items": {}}, open(out, "w"))
F.http_get = lambda url, **k: (_ for _ in ()).throw(F.FetchError("blocked")); F.main()
check("nothing reachable → no sunday key, run still ok", "sunday" not in load(), load().get("sunday"))
print("FAILS", fails); sys.exit(1 if fails else 0)
