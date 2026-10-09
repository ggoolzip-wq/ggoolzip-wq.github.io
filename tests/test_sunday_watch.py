# 썬데이 감시 (scripts/sunday_watch.py) — 모의 시계·모의 API
import os, sys, json, tempfile, datetime, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import update_feed as F, sunday_watch as W
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
KST = F.KST
tmp = tempfile.mkdtemp(); fp = os.path.join(tmp, "feed.json"); F.OUT = fp
OLD = {"id": 1397, "title": "썬데이 메이플", "image": "https://lwi.nexon.com/old.png", "start": "2026-10-11T00:00:00+09:00", "ocr": {"image": "https://lwi.nexon.com/old.png", "ok": True}}
def reset(sunday, extra=None):
    d = {"version": 1, "updatedAt": "x", "items": {"patch": [{"id": "update:1", "title": "u", "url": "u", "date": "2026-10-01T00:00:00+09:00"}]}, "sunday": sunday}
    if extra: d.update(extra)
    json.dump(d, open(fp, "w"), ensure_ascii=False)
class Clock:
    def __init__(self, t): self.t = t
    def now(self): return self.t
    def sleep(self, s): self.t += datetime.timedelta(seconds=s)
calls = []; STATE = {"new_at": None, "api_fail": False}
EV = lambda n: {"notice_id": n, "title": "썬데이 메이플", "url": f"https://maplestory.nexon.com/News/Event/{n}", "date": "2026-10-15T10:00+09:00",
                "date_event_start": "2026-10-18T00:00+09:00", "date_event_end": "2026-10-18T23:59+09:00"}
def nx(path, **q):
    calls.append((path, clock.now().strftime("%H:%M:%S")))
    if STATE["api_fail"]: raise F.FetchError("HTTP 429", 429, "OPENAPI00007")
    if path == "notice-event":
        if STATE["api_fail"]: raise F.FetchError("HTTP 429", 429, "OPENAPI00007")
        ev = [{"notice_id": 1397, "title": "썬데이 메이플", "url": "u", "date": "2026-10-08T10:00+09:00"}]
        if STATE["new_at"] and clock.now() >= STATE["new_at"]: ev.insert(0, EV(1405))
        return {"event_notice": ev}
    if path == "notice-event/detail":
        return {"contents": '<div class="gen_container"><img src="https://lwi.nexon.com/new1405.png" style="width:100%"></div>', "date_event_start": "2026-10-18T00:00+09:00", "date_event_end": "2026-10-18T23:59+09:00"}
    raise AssertionError(path)
html_hits = []
def http_get(url, **k):
    html_hits.append(url)
    if "Ongoing" in url:
        return 200, '<a href="/News/Event/Ongoing/1405"><em class="event_listMt">썬데이 메이플</em></a>' if STATE["new_at"] and clock.now() >= STATE["new_at"] else "<p></p>"
    if "/News/Event/1405" in url:
        return 200, '<div class="gen_container"><img src="https://lwi.nexon.com/new1405.png" style="width:100%"></div>2026년 10월 18일 00시 00분 ~ 2026년 10월 18일 23시 59분'
    raise F.FetchError("blocked")
F.nx, F.http_get = nx, http_get
os.environ["NEXON_API_KEY"] = "k"; os.environ.pop("GITHUB_OUTPUT", None); os.environ.pop("WATCH_TEST_MINUTES", None); os.environ.pop("WATCH_PRETEND_NEW", None)
outs = {}
W.out = lambda **kv: outs.update(kv)
def run(t0, sunday, **st):
    global clock
    clock = Clock(t0); calls.clear(); html_hits.clear(); outs.clear(); STATE.update(new_at=None, api_fail=False); STATE.update(st)
    reset(sunday); W.watch(clock.now, clock.sleep)
    return json.load(open(fp, encoding="utf-8"))
D = lambda h, m, s=0, day=16: datetime.datetime(2026, 10, day, h, m, s, tzinfo=KST)   # 16일(금): 저장된 썬데이(11일)는 지난 주
# 1) 새 글 없음: 09:47 시작 → 10:00 까지 대기 → 5초마다 → 10:20 전에 끝, 호출 240회
run(D(9, 47), OLD)
lc = [c for c in calls if c[0] == "notice-event"]
check("no new post: waits until 10:00, polls every 5s until 10:20 (240 calls)", len(lc) == 240 and lc[0][1] == "10:00:00" and lc[1][1] == "10:00:05" and lc[-1][1] == "10:19:55" and outs.get("found") == "false", (len(lc), lc[:2], lc[-1:]))
# 2) 10:03:12 에 새 글 → 10:03:15 확인에서 발견, 즉시 멈춤, detail 1회, feed 갱신, OCR 필요
feed = run(D(9, 50), OLD, new_at=D(10, 3, 12))
sd = feed["sunday"]
check("new post found at next poll, polling stops", outs.get("found") == "true" and calls[-1][0] == "notice-event/detail" and [c for c in calls if c[0] == "notice-event"][-1][1] == "10:03:15" and outs.get("calls") == 40, (outs, calls[-2:]))
check("processed like update_feed (detail image, period), OCR requested", sd.get("id") == 1405 and sd.get("image") == "https://lwi.nexon.com/new1405.png" and sd.get("start") == "2026-10-18T00:00:00+09:00" and outs.get("sunday_ocr") == "true", sd)
check("other feed items untouched", feed["items"]["patch"][0]["id"] == "update:1")
# 3) API 실패(두 키 모두) → 홈페이지 HTML 로 발견
feed = run(D(10, 5), OLD, new_at=D(10, 5), api_fail=True)
check("API down → homepage fallback finds the post", outs.get("found") == "true" and feed["sunday"].get("id") == 1405 and any("Ongoing" in u for u in html_hits) and feed["sunday"].get("via") == "html", (outs, feed["sunday"]))
# 4) 이번 주 썬데이가 이미 있음(시작일 18일) → 호출 0
run(D(9, 45), dict(OLD, id=1405, start="2026-10-18T00:00:00+09:00"))
check("this week's post already stored → no polling (0 calls)", outs.get("calls") == 0 and not calls, outs)
# 5) 10:20 이후 시작(예약 지연) → 바로 끝
run(D(10, 21), OLD); check("started after 10:20 → exits, 0 calls", outs.get("calls") == 0 and not calls)
# 6) 테스트 옵션: N분만 + 저장된 글도 새 글처럼
os.environ["WATCH_TEST_MINUTES"] = "1"; os.environ["WATCH_PRETEND_NEW"] = "true"
feed = run(D(15, 0), dict(OLD, id=1405, start="2026-10-18T00:00:00+09:00"), new_at=D(0, 0))
check("test mode: starts now, pretend_new re-processes the stored post", outs.get("found") == "true" and calls[0][1] == "15:00:00" and feed["sunday"].get("id") == 1405 and "ocr" not in feed["sunday"] and outs.get("sunday_ocr") == "true", (outs, calls[:2]))
os.environ["WATCH_PRETEND_NEW"] = "false"
run(D(15, 0), OLD)
check("test mode 1 minute: 12 polls (5s) then stop", outs.get("calls") == 12 and outs.get("found") == "false", outs)
os.environ.pop("WATCH_TEST_MINUTES"); os.environ.pop("WATCH_PRETEND_NEW")
# 7) --save / --apply: 최신 main 의 feed.json(다른 소식이 바뀐 상태)에 sunday 만 덮어씀
sp = os.path.join(tmp, "s.json")
reset(dict(OLD, id=1405, benefit="미라클 타임")); subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "sunday_watch.py"), "--save", sp], env=dict(os.environ, FEED_OUT=fp), check=True)
reset(OLD, {"items": {"patch": [{"id": "update:2", "title": "new from update-feed", "url": "u", "date": "x"}]}})
subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "sunday_watch.py"), "--apply", sp], env=dict(os.environ, FEED_OUT=fp), check=True, capture_output=True)
f2 = json.load(open(fp, encoding="utf-8"))
check("--apply keeps update-feed's newer items, replaces only sunday", f2["items"]["patch"][0]["id"] == "update:2" and f2["sunday"]["id"] == 1405 and f2["sunday"]["benefit"] == "미라클 타임", f2)
# 8) 워크플로
wf = open(os.path.join(ROOT, ".github", "workflows", "sunday-watch.yml"), encoding="utf-8").read()
check("workflow: two staggered crons 00:45/00:50 UTC, own concurrency group, key1+key2, OCR step, merge-commit",
      "'45 0 * * *'" in wf and "'50 0 * * *'" in wf and "group: sunday-watch" in wf and "NEXON_API_KEY2: ${{ secrets.NEXON_API_KEY2 }}" in wf
      and "steps.watch.outputs.sunday_ocr == 'true'" in wf and "--apply" in wf and "git reset -q --hard origin/main" in wf and "test_minutes" in wf and "pretend_new" in wf and "timeout-minutes: 50" in wf)
fw = open(os.path.join(ROOT, ".github", "workflows", "update-feed.yml"), encoding="utf-8").read()
check("update-feed keeps its own concurrency group (not blocked by the 20-min watch)", "group: update-feed" in fw and "sunday-watch" not in fw)
print("FAILS", fails); sys.exit(1 if fails else 0)
