#!/usr/bin/env python3
"""썬데이 메이플 새 글 감시 — sunday-watch.yml (매일 09:45/09:50 KST 시작 → 10:00~10:20 KST 동안 5초마다 확인)

- 1순위 넥슨 Open API /notice-event (update_feed.nx: 키1 → 호출량 초과·잘못된 키면 키2). API 가 실패하면 그 회차만 홈페이지 이벤트 검색 HTML.
- 새 글(저장된 sunday.id 보다 큰 번호의 '썬데이 메이플')을 찾으면 바로 멈추고 update_feed.src_sunday 로 처리(detail 1회 → 이미지·기간·글자 혜택)
  → GITHUB_OUTPUT found=true, sunday_ocr=true|false → 워크플로가 OCR(scripts/sunday_ocr.py)·커밋.
- 이번 주 썬데이(시작일이 아직 안 지난 글)가 이미 저장돼 있으면 확인하지 않고 끝냄(호출 0).
- API 호출: 최대 20분 ÷ 5초 = 240회 + 새 글 detail 1회 ≈ 하루 최대 241회 (기존 약 530회와 합쳐 약 770회 < 1,000회, 키2 예비). 새 글을 찾으면 바로 멈춤.
옵션/환경: WATCH_TEST_MINUTES=N(지금부터 N분만, 테스트), WATCH_PRETEND_NEW=true(저장된 썬데이도 새 글로 처리, 테스트),
          WATCH_INTERVAL=5, --save 경로(feed.json 의 sunday 를 파일로) / --apply 경로(파일의 sunday 를 최신 feed.json 에 덮어쓰기 — 커밋 충돌 방지용)
"""
import datetime, json, os, sys, time, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_feed as F

KST = F.KST
START, END = (10, 0), (10, 20)

def out(**kv):
    go = os.environ.get("GITHUB_OUTPUT")
    for k, v in kv.items():
        print(f"{k}={v}", flush=True)
        if go:
            with open(go, "a") as f:
                f.write(f"{k}={v}\n")

def load():
    return json.load(open(F.OUT, encoding="utf-8"))

def save(feed):
    feed["updatedAt"] = F.now_iso()
    with open(F.OUT, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=1); f.write("\n")

def window(now):
    m = int(os.environ.get("WATCH_TEST_MINUTES") or 0)
    if m > 0:
        return now, now + datetime.timedelta(minutes=m)
    d = now.date()
    return (datetime.datetime(d.year, d.month, d.day, *START, tzinfo=KST), datetime.datetime(d.year, d.month, d.day, *END, tzinfo=KST))

def newest_sunday(cur_id):
    """(API 목록, 새 썬데이 번호 또는 None, 출처). API 실패 시 홈페이지 검색 HTML."""
    try:
        items = F.nx("notice-event").get("event_notice") or []
        ids = [int(x.get("notice_id") or 0) for x in items if F.SUNDAY_RE.search(x.get("title", ""))]
        n = max(ids) if ids else None
        return items, (n if n and n > cur_id else None), "api"
    except Exception as e:
        F.log("  API 실패 → 홈페이지 확인:", str(e)[:160])
    try:
        _, s = F.http_get(f"{F.EVENT_BASE}/Ongoing?search=" + urllib.parse.quote("썬데이"), proxy=True)
        ids = [n for n, v in F.parse_event_list(s).items() if F.SUNDAY_RE.search(v["title"])]
        n = max(ids) if ids else None
        return [], (n if n and n > cur_id else None), "html"
    except Exception as e:
        F.log("  홈페이지도 실패:", str(e)[:160])
        return [], None, "none"

def watch(now_fn=lambda: datetime.datetime.now(KST), sleep=time.sleep):
    feed = load(); cur = feed.get("sunday") or {}
    pretend = (os.environ.get("WATCH_PRETEND_NEW") or "").lower() == "true"
    cur_id = 0 if pretend else int(cur.get("id") or 0)
    now = now_fn(); start, end = window(now)
    if not pretend and cur.get("start"):
        try:
            if datetime.datetime.fromisoformat(cur["start"]) + datetime.timedelta(days=1) > now:
                F.log(f"이번 주 썬데이({cur.get('id')}, {cur['start'][:10]})가 이미 있음 → 확인 안 함")
                return out(found="false", sunday_ocr="false", calls=0)
        except ValueError:
            pass
    if now >= end:
        F.log("확인 시간(~%s)이 이미 지남 → 끝" % end.strftime("%H:%M"))
        return out(found="false", sunday_ocr="false", calls=0)
    if now < start:
        F.log("10:00 KST 까지 대기 %d초" % (start - now).total_seconds())
        sleep((start - now).total_seconds())
    interval = float(os.environ.get("WATCH_INTERVAL") or 5)  # 사용자 결정: 5초
    calls = 0
    while True:
        t0 = now_fn()
        items, n, via = newest_sunday(cur_id); calls += 1
        F.log(f"[{t0.strftime('%H:%M:%S')}] {via}: " + (f"새 썬데이 {n}" if n else "새 글 없음"))
        if n:
            F._API_EVENTS[:] = items
            if pretend:
                feed.pop("sunday", None)
            F.src_sunday(feed, True, 0)
            save(feed)
            sd = feed.get("sunday") or {}
            F.log("처리:", sd.get("id"), sd.get("title"), sd.get("image"))
            return out(found="true", sunday_ocr="true" if F.sunday_needs_ocr(sd) else "false", calls=calls)
        nxt = t0 + datetime.timedelta(seconds=interval)
        if nxt >= end:
            break
        sleep(max(0, (nxt - now_fn()).total_seconds()))
    F.log("끝: 새 썬데이 없음")
    return out(found="false", sunday_ocr="false", calls=calls)

def main():
    a = sys.argv[1:]
    if "--save" in a:
        json.dump(load().get("sunday") or {}, open(a[a.index("--save") + 1], "w", encoding="utf-8"), ensure_ascii=False); return 0
    if "--apply" in a:  # 최신 main 의 feed.json 에 썬데이만 덮어쓰기 (다른 소식은 그대로)
        sd = json.load(open(a[a.index("--apply") + 1], encoding="utf-8"))
        feed = load()
        if sd and feed.get("sunday") != sd:
            feed["sunday"] = sd; save(feed); print("applied", sd.get("id"))
        return 0
    watch()
    return 0

if __name__ == "__main__":
    sys.exit(main())
