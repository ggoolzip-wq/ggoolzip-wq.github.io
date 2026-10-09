#!/usr/bin/env python3
"""소식 카드(feed.json) 수집 — GitHub Actions 에서 5분마다 실행 (표준 라이브러리만 사용)

탭(소스)                 가져오는 곳
- saryo  사료감지         넥슨 Open API /notice, /notice-event (+detail) 중 '메이플 운영자' NPC 에게서 보상을 받는 공지
- patch  패치내역         넥슨 Open API /notice-update  (= maplestory.nexon.com/News/Update)
- test   테섭             maplestory.nexon.com/Testworld/News/Update 목록 페이지 (Open API 에 없음)
- mabbak 마빡도로시        인벤 메이플 게시판(5974, 2304, 2314, 2316, 2587) 닉네임 검색 + 글 페이지(articleDate)

동작
- 소스마다 try/except — 하나가 실패해도 나머지는 계속. 결과는 feed.json 의 sources[소스] = {ok, checkedAt, lastOkAt, error}.
- 새 글 판별은 소스별 '워터마크'(이미 본 가장 큰 글 번호) 기준. 처음 설정(--seed) 이후의 새 글만 추가(예전 글을 다시 채우지 않음).
- 탭마다 최신순, id 중복 제거, 최대 200개.
- feed.json 은 '새 글이 있거나 / 소스 성공·실패 상태가 바뀌었거나 / 마지막 저장 후 3시간'일 때만 다시 씀 → 커밋 남발 방지.
  (GITHUB_OUTPUT 에 changed=true|false)
- API 호출 절약(개발 키 하루 1,000회): /notice 는 매번, /notice-update 는 10분에 한 번, /notice-event 는 15분에 한 번(수동 실행·FEED_ALL=1 이면 전부).
  detail 은 워터마크보다 새 공지에만 호출.
환경 변수: NEXON_API_KEY(필수, 저장소 secret), FEED_PROXY(선택, 박스 테스트용 http 프록시 — nexon.com/인벤 요청에만), FEED_ALL=1, FEED_OUT(출력 경로)
"""
import datetime, html, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("FEED_OUT") or os.path.join(ROOT, "feed.json")
KST = datetime.timezone(datetime.timedelta(hours=9))
CAP = 200
HEARTBEAT_H = 3
API = "https://open.api.nexon.com/maplestory/v1"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
INVEN_BOARDS = ["5974", "2304", "2314", "2316", "2587"]
INVEN_NICK = "마빡도로시"
LABELS = {"saryo": "사료감지", "patch": "패치내역", "test": "테섭", "mabbak": "마빡도로시"}

def now_iso():
    return datetime.datetime.now(KST).replace(microsecond=0).isoformat()

def log(*a):
    print(*a, flush=True)

class FetchError(Exception):
    pass

def http_get(url, headers=None, proxy=False, timeout=25):
    h = {"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    px = os.environ.get("FEED_PROXY") if proxy else None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": px, "https": px} if px else {}))
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        raise FetchError(f"HTTP {e.code} {url.split('?')[0]} {body[:160]}")
    except Exception as e:
        raise FetchError(f"{type(e).__name__}: {e} ({url.split('?')[0]})")

def nx(path, **q):
    key = os.environ.get("NEXON_API_KEY", "").strip()
    if not key:
        raise FetchError("NEXON_API_KEY secret 없음")
    url = f"{API}/{path}" + ("?" + urllib.parse.urlencode(q) if q else "")
    _, body = http_get(url, {"x-nxopen-api-key": key, "Accept": "application/json"})
    return json.loads(body)

def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()

def iso_from_api(s):
    s = str(s or "")
    m = re.match(r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})", s)
    return f"{m.group(1)}T{m.group(2)}:00+09:00" if m else s

# ---------------- 사료감지 ----------------
NPC_RE = re.compile(r"메이플\s*운영자|운영자\s*[’'\"」』]?\s*NPC")
RECV_RE = re.compile(r"수령|지급|받기|받으|받아|받을")
EXCL_RE = re.compile(r"수령\s*(?:이\s*)?불가|수령할\s*수\s*없|받을\s*수\s*없|지급되지\s*않|코인\s*(?:샵|상점)|소울\s*(?:교환|조각)|교환\s*(?:하기|해\s*주|할\s*수)")

def saryo_match(title, body):
    t = f"{title} {body}"
    for m in NPC_RE.finditer(t):
        w = t[max(0, m.start() - 100): m.end() + 70]
        if RECV_RE.search(w) and not EXCL_RE.search(w):
            return True
    return False

DATE_RE = re.compile(r"(?:(\d{4})\s*년\s*)?(\d{1,2})\s*월\s*(\d{1,2})\s*일(?:\s*\(\s*\S\s*\))?(?:\s*(오전|오후)\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?)?")

def saryo_end(body, default_year):
    """'수령 기간 : … ~ 10월 21일(수) 오후 11시 59분' → ISO (KST). 없으면 None"""
    m = re.search(r"수령\s*기간\s*[:：]?\s*(.{0,90}?)~\s*(.{0,70})", body)
    if not m:
        return None
    left, right = m.group(1), m.group(2)
    d = DATE_RE.search(right)
    if not d:
        return None
    ly = re.search(r"(\d{4})\s*년", left)
    y = int(d.group(1) or (ly.group(1) if ly else default_year))
    mo, dd = int(d.group(2)), int(d.group(3))
    if d.group(4):
        hh = int(d.group(5)) % 12 + (12 if d.group(4) == "오후" else 0)
        mi = int(d.group(6) or 0)
    else:
        hh, mi = 23, 59
    try:
        return datetime.datetime(y, mo, dd, hh, mi, tzinfo=KST).isoformat()
    except ValueError:
        return None

def src_saryo(st, wm, run_all, minute):
    new = []
    lists = [("notice", "notice", "notice/detail")]
    if run_all or (minute // 5) % 3 == 0:
        lists.append(("notice-event", "event_notice", "notice-event/detail"))
    for path, key, det in lists:
        items = nx(path).get(key) or []
        if path not in wm:  # 처음: 지금 있는 공지는 이미 본 것으로 (예전 글 채우지 않음)
            wm[path] = max([0] + [int(x.get("notice_id") or 0) for x in items]); continue
        w = wm[path]
        fresh = sorted([x for x in items if int(x.get("notice_id") or 0) > w], key=lambda x: int(x["notice_id"]))
        for x in fresh[:10]:  # 한 번에 최대 10건 상세 조회
            d = nx(det, notice_id=x["notice_id"])
            body = plain(d.get("contents"))
            if saryo_match(x.get("title", ""), body):
                date = iso_from_api(x.get("date"))
                new.append({"id": f"{path}:{x['notice_id']}", "title": x.get("title", ""), "url": x.get("url", ""),
                            "date": date, "end": saryo_end(body, int(date[:4]) if date[:4].isdigit() else datetime.datetime.now(KST).year), "src": path})
                log("  사료감지 발견:", x.get("title"))
            wm[path] = max(wm.get(path, 0), int(x["notice_id"]))
        if items and not fresh[10:]:
            wm[path] = max([wm[path]] + [int(x.get("notice_id") or 0) for x in items])
    return new

# ---------------- 패치내역 ----------------
def src_patch(st, wm, run_all, minute):
    if not (run_all or (minute // 5) % 2 == 0):
        return None  # 이번 회차는 건너뜀(호출 절약)
    items = nx("notice-update").get("update_notice") or []
    if "notice-update" not in wm:
        wm["notice-update"] = max([0] + [int(x.get("notice_id") or 0) for x in items]); return []
    w = wm["notice-update"]; new = []
    for x in items:
        if int(x.get("notice_id") or 0) > w:
            new.append({"id": f"update:{x['notice_id']}", "title": x.get("title", ""), "url": x.get("url", ""), "date": iso_from_api(x.get("date"))})
    if items:
        wm["notice-update"] = max([w] + [int(x.get("notice_id") or 0) for x in items])
    return new

# ---------------- 테섭 ----------------
TEST_URL = "https://maplestory.nexon.com/Testworld/News/Update"
def parse_test(s):
    out = []
    for m in re.finditer(r'<a href="(/testworld/news/update/(\d+))"[^>]*>.*?<span>(.*?)</span>.*?<dd>\s*([\d.]+)\s*</dd>', s, re.S | re.I):
        title = plain(re.sub(r"<em[^>]*>.*?</em>", "", m.group(3), flags=re.S))
        y, mo, d = (m.group(4).split(".") + ["", "", ""])[:3]
        out.append({"id": f"test:{m.group(2)}", "n": int(m.group(2)), "title": title,
                    "url": f"https://maplestory.nexon.com/Testworld/News/Update/{m.group(2)}", "date": f"{y}-{mo}-{d}T00:00:00+09:00" if d else ""})
    return out

def src_test(st, wm, run_all, minute):
    _, s = http_get(TEST_URL, proxy=True)
    rows = parse_test(s)
    if not rows:
        raise FetchError(f"테섭 목록을 읽지 못함(형식 변경 또는 차단, {len(s)} bytes)")
    if "test" not in wm:
        wm["test"] = max(r["n"] for r in rows); return []
    w = wm["test"]
    new = [{k: r[k] for k in ("id", "title", "url", "date")} for r in rows if r["n"] > w]
    wm["test"] = max([w] + [r["n"] for r in rows])
    return new

# ---------------- 마빡도로시 (인벤) ----------------
def inven_rows(s):
    out = []
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", s, re.S):
        t = m.group(1)
        link = re.search(r'href="(https://www\.inven\.co\.kr/board/maple/(\d+)/(\d+))[^"]*"', t)
        if not link or INVEN_NICK not in t:
            continue
        out.append((link.group(1), link.group(2), int(link.group(3))))
    return out

def inven_post(url):
    _, p = http_get(url, proxy=True)
    date = re.search(r'articleDate[^>]*>\s*([\d-]+\s+[\d:]+)', p)
    title = re.search(r'articleTitle[^>]*>\s*(?:<[^>]*>\s*)*([^<]+)', p)
    if not title:
        title = re.search(r"<title>(.*?)</title>", p, re.S)
    t = plain(title.group(1)) if title else url
    t = re.sub(r"^메이플스토리 인벤\s*:\s*|\s*-\s*메이플스토리 인벤.*$", "", t).strip()
    d = date.group(1).strip() if date else ""
    iso = (d.replace(" ", "T") + ":00+09:00") if re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", d) else ""
    return t, iso

def src_mabbak(st, wm, run_all, minute):
    new, errs, ok = [], [], 0
    q = urllib.parse.quote(INVEN_NICK)
    for b in INVEN_BOARDS:
        try:
            _, s = http_get(f"https://www.inven.co.kr/board/maple/{b}?name=nicname&keyword={q}", proxy=True)
            if len(s) < 5000 or "inven" not in s.lower():
                raise FetchError(f"응답이 비정상({len(s)} bytes, 차단 가능)")
            ok += 1
            rows = inven_rows(s)
            k = f"inven:{b}"; w = wm.get(k)
            if w is None:  # 이 게시판 처음: 현재 글들은 이미 본 것으로
                wm[k] = max([0] + [n for _, _, n in rows]); continue
            for url, _, n in sorted(set(rows), key=lambda r: r[2]):
                if n > w:
                    title, iso = inven_post(url)
                    new.append({"id": f"inven:{b}:{n}", "title": title, "url": url, "date": iso, "board": b})
                    log("  마빡도로시 새 글:", title)
                    time.sleep(1)
            wm[k] = max([w] + [n for _, _, n in rows])
        except Exception as e:
            errs.append(f"{b}: {e}")
        time.sleep(1.2)
    if not ok:
        raise FetchError("; ".join(errs)[:400])
    if errs:
        log("  일부 게시판 실패:", errs)
    return new

SOURCES = [("saryo", src_saryo), ("patch", src_patch), ("test", src_test), ("mabbak", src_mabbak)]

def load():
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def merge(lst, new):
    seen = {x["id"] for x in lst}; added = 0
    for x in new:
        if x["id"] not in seen:
            lst.append(x); seen.add(x["id"]); added += 1
    lst.sort(key=lambda x: (x.get("date") or "", x["id"]), reverse=True)
    del lst[CAP:]
    return added

def main():
    feed = load(); old = json.loads(json.dumps(feed))
    feed.setdefault("version", 1)
    items = feed.setdefault("items", {}); srcs = feed.setdefault("sources", {})
    wm = feed.setdefault("state", {}).setdefault("watermarks", {})
    run_all = os.environ.get("FEED_ALL") == "1" or os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    minute = datetime.datetime.now(datetime.timezone.utc).minute
    added = 0; flipped = False
    for k, fn in SOURCES:
        lst = items.setdefault(k, []); prev = srcs.get(k, {})
        s = {"label": LABELS[k], "ok": prev.get("ok", True), "checkedAt": prev.get("checkedAt", ""), "lastOkAt": prev.get("lastOkAt", ""), "error": prev.get("error", "")}
        try:
            new = fn(srcs, wm, run_all, minute)
            if new is None:
                log(f"[{k}] 이번 회차 건너뜀"); continue
            n = merge(lst, new); added += n
            s.update(ok=True, checkedAt=now_iso(), lastOkAt=now_iso(), error="")
            log(f"[{k}] OK, 새 글 {n}개")
        except Exception as e:
            s.update(ok=False, checkedAt=now_iso(), error=str(e)[:400])
            log(f"::warning::[{k}] 실패: {e}")
        if bool(prev.get("ok", True)) != s["ok"] or (not prev):
            flipped = True
        srcs[k] = s
    last = feed.get("updatedAt") or ""
    stale = True
    try:
        stale = (datetime.datetime.now(KST) - datetime.datetime.fromisoformat(last)).total_seconds() > HEARTBEAT_H * 3600
    except Exception:
        pass
    wm_changed = (old.get("state", {}).get("watermarks") != wm)
    changed = bool(added or flipped or stale or wm_changed)  # 워터마크 저장 안 하면 같은 공지 detail 을 매번 다시 호출하게 됨
    if changed:
        feed["updatedAt"] = now_iso()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(feed, f, ensure_ascii=False, indent=1)
            f.write("\n")
    log(f"새 글 {added}개, 상태 변경 {flipped}, 하트비트 {stale} → {'저장' if changed else '변경 없음'}")
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        with open(go, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
