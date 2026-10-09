#!/usr/bin/env python3
"""소식 카드(feed.json) 수집 — GitHub Actions 에서 5분마다 실행 (표준 라이브러리만 사용)

탭(소스)                 가져오는 곳
- saryo  사료감지         넥슨 Open API /notice, /notice-event (+detail) 중 '메이플 운영자' NPC 에게서 보상을 받는 공지
- patch  패치내역         넥슨 Open API /notice-update  (= maplestory.nexon.com/News/Update)
                          + 공지사항 중 '마이너 패치' (처음 최신 2개 백필, 이후 새 글 누적) (/notice 목록 재사용, 홈페이지 검색은 대체용)
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
- sunday 썬데이 메이플(탭 아님) 최신 이벤트 글 1건 + 대표 이미지 → feed.json 의 sunday {id,title,url,image,start,end}
환경 변수: NEXON_API_KEY(필수, 저장소 secret), NEXON_API_KEY2(선택 — 1번 키가 호출량 초과·잘못된 키일 때 대신 사용), FEED_PROXY(선택, 박스 테스트용 http 프록시 — nexon.com/인벤 요청에만), FEED_ALL=1, FEED_OUT(출력 경로)
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
    def __init__(self, msg, status=None, body=""):
        super().__init__(msg); self.status = status; self.body = body

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
        raise FetchError(f"HTTP {e.code} {url.split('?')[0]} {body[:160]}", e.code, body)
    except Exception as e:
        raise FetchError(f"{type(e).__name__}: {e} ({url.split('?')[0]})")

# 넥슨 키 2개: NEXON_API_KEY(1순위) → 호출량 초과/잘못된 키면 NEXON_API_KEY2 로 다시 시도. 한 번 막힌 키는 이번 실행 동안 건너뜀.
#   전환 조건: HTTP 429, 또는 응답 오류 코드 OPENAPI00007(호출량 초과)·OPENAPI00005(유효하지 않은 키)·OPENAPI00001/00002(인증/권한), HTTP 401/403.
KEY_SWITCH_CODES = ("OPENAPI00007", "OPENAPI00005", "OPENAPI00001", "OPENAPI00002")
_BAD_KEYS = set()

def api_keys():
    ks = []
    for name in ("NEXON_API_KEY", "NEXON_API_KEY2"):
        k = os.environ.get(name, "").strip()
        if k and k not in ks:
            ks.append(k)
    return ks

def key_problem(e):
    return isinstance(e, FetchError) and (e.status in (401, 403, 429) or any(c in (e.body or "") for c in KEY_SWITCH_CODES))

def nx(path, **q):
    keys = api_keys()
    if not keys:
        raise FetchError("NEXON_API_KEY secret 없음")
    url = f"{API}/{path}" + ("?" + urllib.parse.urlencode(q) if q else "")
    last = None
    for i, key in enumerate(keys):
        if key in _BAD_KEYS and i < len(keys) - 1:
            continue
        try:
            _, body = http_get(url, {"x-nxopen-api-key": key, "Accept": "application/json"})
            return json.loads(body)
        except FetchError as e:
            last = e
            if not key_problem(e):
                raise
            if key not in _BAD_KEYS:
                _BAD_KEYS.add(key)
                log(f"::warning::넥슨 키 {i + 1} 사용 불가({e.status}, {(e.body or '')[:80]}) → " + ("키 2로 다시 시도" if i < len(keys) - 1 else "남은 키 없음"))
    raise last

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
        if path == "notice":
            _API_NOTICES[:] = items  # 패치내역(마이너 패치)에서 재사용
        else:
            _API_EVENTS[:] = items   # 썬데이 메이플에서 재사용
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
# (1) 업데이트 공지: Open API /notice-update (10분에 한 번)
# (2) 마이너 패치: 공식 홈페이지 공지사항(/News/Notice) 중 제목에 '마이너 패치'가 들어간 글의 처음 한 번 최신 2개를 채우고(백필), 이후 새 글은 계속 쌓임(다른 피드 글과 같음).
#     실제 제목 예: '[패치완료] 10/8(목) ver1.2.419 마이너버전(8) 패치', '… 마이너(7) 패치', '마이너패치', '마이너 패치'.
#     같은 글의 제목이 [패치예정]→[패치완료] 로 바뀌므로 매번 제목·날짜를 다시 맞춤. 예전 글은 지우지 않음(탭당 200개 한도만).
#     가져오는 곳: 1순위 Open API /notice 목록(사료감지가 이번 회차에 이미 받은 것 — 추가 호출 없음, 점검 분류 글 포함).
#                 대체: 홈페이지 공지 검색 HTML(/News/Notice/All?search=마이너) — API 실패 또는 첫 백필 때 API 에 2개 미만일 때만.
MINOR_RE = re.compile(r"마이너\s*(?:버전\s*)?(?:\(\s*\d+\s*\)\s*)?패치")
MINOR_KEEP = 2  # 처음 한 번 채우는(백필) 개수 — 이후엔 새 글이 계속 쌓임
NOTICE_SEARCH_URL = "https://maplestory.nexon.com/News/Notice/All?search=" + urllib.parse.quote("마이너")
_API_NOTICES = []  # src_saryo 가 받은 /notice 목록 (같은 회차에 재사용)

def parse_notice_list(s, today=None):
    """공식 공지사항 목록 HTML → [{n, title, url, date}] (news_board 안의 글만)"""
    i = s.find('class="news_board"')
    if i < 0:
        return []
    s = s[i:]
    j = s.find('class="page_numb')
    if j > 0:
        s = s[:j]
    today = today or datetime.datetime.now(KST).date()
    out = []
    for m in re.finditer(r'<a href="(/News/Notice/(?:All|Notice|Inspection|Event|Update)/(\d+))[^"]*"[^>]*>(.*?)</a>(.*?)</li>', s, re.S | re.I):
        sp = re.search(r"<span[^>]*>(.*?)</span>\s*(?:<img|$)", m.group(3), re.S) or re.search(r"<span[^>]*>(.*)</span>", m.group(3), re.S)
        title = plain(sp.group(1) if sp else m.group(3))
        dd = re.search(r"<dd>\s*(.*?)\s*</dd>", m.group(4), re.S)
        d = plain(dd.group(1)) if dd else ""
        date = ""
        dm = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", d)
        tm = re.match(r"(AM|PM|오전|오후)\s*(\d{1,2}):(\d{2})", d, re.I)
        if dm:
            date = f"{int(dm.group(1)):04d}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}T00:00:00+09:00"
        elif tm:  # 오늘 글은 시각만 표시됨
            hh = int(tm.group(2)) % 12 + (12 if tm.group(1).upper() in ("PM", "오후") else 0)
            date = datetime.datetime(today.year, today.month, today.day, hh, int(tm.group(3)), tzinfo=KST).isoformat()
        out.append({"n": int(m.group(2)), "title": title, "url": "https://maplestory.nexon.com" + m.group(1), "date": date})
    return out

def minor_candidates(html_rows, api_items):
    """두 출처를 합쳐 마이너 패치 글 {n: item}. 같은 글이면 API 의 날짜(시각 포함)를 우선."""
    c = {}
    for r in html_rows:
        if MINOR_RE.search(r["title"]):
            c[r["n"]] = {"id": f"minor:{r['n']}", "title": r["title"], "url": r["url"], "date": r["date"], "src": "minor"}
    for x in api_items:
        n = int(x.get("notice_id") or 0); t = x.get("title", "")
        if n and MINOR_RE.search(t):
            prev = c.get(n, {})
            c[n] = {"id": f"minor:{n}", "title": t or prev.get("title", ""), "url": x.get("url") or prev.get("url", ""),
                    "date": iso_from_api(x.get("date")) or prev.get("date", ""), "src": "minor"}
    return c

MINOR_MAX_PAGES = 5  # HTML 대체를 쓸 때: 백필 때 2개를 못 모았거나, 1쪽이 전부 새 글일 때만 다음 쪽까지
_HAVE_MINOR = set()   # main() 이 넣어 줌: feed.json 에 이미 있는 minor 글 번호

def src_minor(wm):
    """마이너 패치 후보 {n: item}.
    1순위 = Open API /notice 목록(사료감지가 이번 회차에 이미 받은 것, 추가 호출 0).
    홈페이지 검색 HTML 은 대체용 — API 목록이 없을 때(실패) 또는 처음 백필인데 API 최근 20건에 마이너 패치가 2개 미만일 때만."""
    api_c = minor_candidates([], _API_NOTICES)
    need_html = (not _API_NOTICES) or ("minor" not in wm and len(api_c) < MINOR_KEEP)
    rows, err = [], ""
    if need_html:
        for page in range(1, MINOR_MAX_PAGES + 1):
            try:
                _, s = http_get(NOTICE_SEARCH_URL + (f"&page={page}" if page > 1 else ""), proxy=True)
                got = parse_notice_list(s)
                if not got:
                    if page == 1:
                        err = f"공지 검색 목록을 읽지 못함({len(s)} bytes)"
                    break
                rows += got
            except Exception as e:
                if page == 1:
                    err = str(e)
                break
            if "minor" in wm:  # API 실패 대체: 이 쪽 글이 전부 워터마크보다 새로울 때만 다음 쪽
                if min(r["n"] for r in got) <= wm["minor"]:
                    break
            else:              # 백필: 최근 2개를 모을 때까지
                found = {r["n"] for r in rows if MINOR_RE.search(r["title"])} | set(api_c) | _HAVE_MINOR
                if len(found) >= MINOR_KEEP:
                    break
            time.sleep(1)
        if err:
            log("  마이너 패치 HTML(대체) 실패:", err)
            if not _API_NOTICES:
                raise FetchError("마이너 패치: API /notice 없음, HTML 대체도 실패: " + err)
    c = minor_candidates(rows, _API_NOTICES)
    log(f"  마이너 패치 후보 {len(c)}개 (API {len(_API_NOTICES)}건{', HTML 대체 ' + str(len(rows)) + '행' if need_html else ''})")
    return c

def apply_minor(lst, cands, wm):
    """마이너 패치 글을 패치 탭에 '쌓기'(다른 글과 같은 피드 방식).
    - 처음(워터마크 wm['minor'] 없음): 가장 최근 MINOR_KEEP(2)개만 채움(백필) → 워터마크 = 그중 가장 큰 번호.
    - 이후: 워터마크보다 번호가 큰 새 글만 추가(맨 위로, 날짜순). 예전 글은 지우지 않음(탭당 CAP=200 은 merge 가 처리).
    - 이미 있는 글은 제목·날짜만 갱신([패치예정]→[패치완료]).
    바뀐 개수 반환"""
    if cands is None:
        return 0
    have = {x["id"]: x for x in lst if x["id"].startswith("minor:")}
    changed = 0
    for n, w in cands.items():  # 제목·날짜 갱신
        x = have.get(w["id"])
        if x:
            for k in ("title", "url", "date"):
                if w.get(k) and x.get(k) != w[k]:
                    x[k] = w[k]; changed += 1
    if "minor" not in wm:
        known = [int(i.split(":")[1]) for i in have]
        add = [cands[n] for n in sorted(cands, reverse=True)[:MINOR_KEEP]]
        wm["minor"] = max([0] + known + [int(x["id"].split(":")[1]) for x in add])
    else:
        add = [cands[n] for n in sorted(cands) if n > wm["minor"]]
        if add:
            wm["minor"] = max(int(x["id"].split(":")[1]) for x in add)
    new = [x for x in add if x["id"] not in have]
    if new:
        log("  마이너 패치 새 글:", [x["title"] for x in new])
    changed += merge(lst, new)
    lst.sort(key=lambda x: (x.get("date") or "", x["id"]), reverse=True)
    return changed

def src_patch(st, wm, run_all, minute):
    new = []
    if run_all or (minute // 5) % 2 == 0:  # 업데이트 공지는 10분에 한 번(호출 절약)
        items = nx("notice-update").get("update_notice") or []
        if "notice-update" not in wm:
            wm["notice-update"] = max([0] + [int(x.get("notice_id") or 0) for x in items])
        else:
            w = wm["notice-update"]
            for x in items:
                if int(x.get("notice_id") or 0) > w:
                    new.append({"id": f"update:{x['notice_id']}", "title": x.get("title", ""), "url": x.get("url", ""), "date": iso_from_api(x.get("date"))})
            if items:
                wm["notice-update"] = max([w] + [int(x.get("notice_id") or 0) for x in items])
    global _MINOR
    _MINOR = None
    try:
        _MINOR = src_minor(wm)  # 매 회차 (HTML 은 API 할당량을 쓰지 않음)
    except Exception as e:  # 마이너 패치만 실패 → 업데이트 공지는 그대로, 기존 마이너 글 유지
        log(f"::warning::[patch] 마이너 패치 확인 실패: {e}")
    return new

_MINOR = None

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

# ---------------- 썬데이 메이플 (탭이 아니라 feed.json 의 "sunday" 한 건) ----------------
# 가장 최근 '썬데이 메이플' 이벤트 글 1건 + 본문 대표 이미지(lwi.nexon.com, 핫링크 가능·CORS *).
# 1순위 Open API: 사료감지가 15분마다 받는 /notice-event 목록(추가 호출 0) → 새 썬데이 글이면 /notice-event/detail 1회(주 1회 ≈ +1회/주).
# 대체 HTML: API 목록 실패 시, 또는 저장된 썬데이가 없는데 API(진행 중 이벤트)에 없을 때만 — 이벤트 검색(진행 중/종료) + 글 페이지.
SUNDAY_RE = re.compile(r"썬\s*데\s*이\s*메\s*이\s*플")
EVENT_BASE = "https://maplestory.nexon.com/News/Event"
_API_EVENTS = []

def parse_event_list(s):
    """이벤트 목록/사이드 목록 HTML → {n: {title, start, end}} (/News/Event[/Ongoing|/Closed]/<n> 링크)"""
    out = {}
    for m in re.finditer(r'<a href="/News/Event/(?:Ongoing/|Closed/)?(\d+)"[^>]*>(.*?)</a>', s, re.S | re.I):
        n = int(m.group(1)); t = re.sub(r"^(?:수정\d*\s+)+", "", plain(m.group(2)))
        if not t or re.match(r"^\d{4}\.", t):
            continue
        out.setdefault(n, {"title": t})
    return out

def parse_event_page(s):
    """이벤트 글 HTML → (대표 이미지 URL, 시작 ISO, 끝 ISO, 제목)"""
    img = ""
    body = s[s.find("gen_container"):] if "gen_container" in s else s
    for m in re.finditer(r"<img\b([^>]*)>", body, re.I):
        a = m.group(1)
        src = re.search(r'src="(https?://[^"]+)"', a)
        if not src or "position: absolute" in a or "position:absolute" in a:
            continue
        u = html.unescape(src.group(1))
        if re.search(r"lwi\.nexon\.com|file\.nexon\.com", u) and not re.search(r"/common/|ssl\.nexon\.com", u):
            img = u; break
    rng = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2})시\s*(\d{1,2})분\s*~\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2})시\s*(\d{1,2})분", plain(s))
    start = end = ""
    if rng:
        g = [int(x) for x in rng.groups()]
        start = datetime.datetime(g[0], g[1], g[2], g[3], g[4], tzinfo=KST).isoformat()
        end = datetime.datetime(g[5], g[6], g[7], g[8], g[9], tzinfo=KST).isoformat()
    tt = re.search(r'<p class="qs_title">(.*?)</p>', s, re.S) or re.search(r"<title>(.*?)</title>", s, re.S)
    title = plain(tt.group(1)) if tt else ""
    title = re.sub(r"^(?:수정\d*\s+)+", "", re.sub(r"\s*\|.*$", "", title))
    return img, start, end, title

BENEFIT_RE = re.compile(
    r"(미라클\s*타임|샤이닝\s*스타포스|스타포스[^.!\n]{0,24}?(?:할인|감소|성공|\d+\s*%)|"
    r"(?:익스트림\s*)?몬스터\s*파크[^.!\n]{0,24}?(?:\d+\s*%|\d+\s*배)|룬[^.!\n]{0,20}?(?:\d+\s*%|\d+\s*배|지속)|"
    r"(?:아케인|어센틱|그랜드\s*어센틱)\s*심볼[^.!\n]{0,20}?(?:\d+\s*배|\d+\s*%)|"
    r"(?:추가\s*)?경험치[^.!\n]{0,16}?(?:\d+\s*%|\d+\s*배)|메소\s*획득[^.!\n]{0,16}?(?:\d+\s*%|\d+\s*배)|"
    r"(?:명장의|레드|블랙|에디셔널|화이트\s*에디셔널)?\s*큐브[^.!\n]{0,20}?(?:할인|\d+\s*%)|"
    r"솔\s*에르다[^.!\n]{0,20}?(?:\d+\s*%|\d+\s*배)|몬스터\s*컬렉션[^.!\n]{0,20}?(?:\d+\s*%|\d+\s*배)|주문의\s*흔적[^.!\n]{0,16}?(?:할인|\d+\s*%))")

def sunday_benefit(title, text):
    """썬데이 혜택 한 줄: ① 제목·본문 글자에서 혜택 키워드(미라클 타임 등) ② 본문의 짧은 요약 문장 ③ 없으면 ''(사이트가 제목 표시).
    썬데이 공지는 보통 이미지뿐이라 ①②가 비는 경우가 많음."""
    t = re.sub(r"\s+", " ", f"{title} {text}")
    found = []
    for m in BENEFIT_RE.finditer(t):
        v = re.sub(r"\s+", " ", m.group(1)).strip()
        tail = re.match(r"\s*(할인|감소|증가|추가|적용)", t[m.end():])
        if tail and not v.endswith(tail.group(1)):
            v += " " + tail.group(1)
        v = re.sub(r"\s*(\d+)\s*%", r" \1%", v).strip()
        if v and not any(v in f or f in v for f in found):
            found.append(v)
    if found:
        return " · ".join(found[:3])[:60], "text"
    for sent in re.split(r"(?<=[.!?])\s+|\n", text or ""):
        sent = sent.strip(" -·*※")
        if 6 <= len(sent) <= 60 and not re.search(r"수정|문의|유의|참고|안내|기간|\d{4}\s*년|^\(", sent):
            return sent, "summary"
    return "", ""

def _sunday_detail_api(n):
    """/notice-event/detail (1회) → (이미지, 시작, 끝, 본문 글자, 썸네일)"""
    d = nx("notice-event/detail", notice_id=n)
    contents = d.get("contents") or ""
    img, s2, e2, _ = parse_event_page(contents)
    return img, iso_from_api(d.get("date_event_start")) or s2, iso_from_api(d.get("date_event_end")) or e2, plain(contents), d.get("thumbnail_url") or ""

def _sunday_detail_html(n):
    """대체: 공식 홈페이지 이벤트 글 HTML → (이미지, 시작, 끝, 본문 글자)"""
    _, s = http_get(f"{EVENT_BASE}/{n}", proxy=True)
    img, st, en, _ = parse_event_page(s)
    i = s.find("gen_container"); body = plain(s[i:i + 20000]) if i >= 0 else ""
    body = body.split("$(document)")[0]
    return img, st, en, body

def src_sunday(feed, run_all, minute):
    """feed['sunday'] 갱신(바뀌었으면 True).
    1순위 Open API: 사료감지가 받은 /notice-event 목록(15분마다, 추가 호출 0) → 새 썬데이 글이면 /notice-event/detail 1회(주 1회 정도).
    대체 HTML: API 목록을 못 받았을 때(실패) 또는 저장된 썬데이가 하나도 없는데 API 목록(진행 중 이벤트)에 없을 때만 홈페이지 이벤트 검색."""
    cur = feed.get("sunday") or {}
    api_ok = bool(_API_EVENTS)
    if not api_ok and cur.get("image") and not run_all and (minute // 5) % 3 != 0:
        return False
    cands = {}
    for x in _API_EVENTS:
        n = int(x.get("notice_id") or 0)
        if n and SUNDAY_RE.search(x.get("title", "")):
            cands[n] = {"title": x.get("title", ""), "start": iso_from_api(x.get("date_event_start")), "end": iso_from_api(x.get("date_event_end")),
                        "thumb": x.get("thumbnail_url") or "", "date": iso_from_api(x.get("date")), "via": "api"}
    if not api_ok or (not cands and not cur.get("id")):
        if not api_ok and cur.get("id") and (minute // 5) % 3 != 0 and not run_all:
            return False
        errs = []
        pages = [f"{EVENT_BASE}/Ongoing?search=" + urllib.parse.quote("썬데이")]
        if not cur.get("id"):
            pages.append(f"{EVENT_BASE}/Closed?search=" + urllib.parse.quote("썬데이"))
        for u in pages:
            try:
                _, s = http_get(u, proxy=True)
                for n, v in parse_event_list(s).items():
                    if SUNDAY_RE.search(v["title"]):
                        cands.setdefault(n, dict(v, via="html"))
            except Exception as e:
                errs.append(str(e))
        log(f"  썬데이 HTML 대체: 후보 {sorted(cands)[-3:]} 오류 {len(errs)}")
        if not cands and errs and not cur:
            raise FetchError("썬데이: " + "; ".join(errs)[:300])
    if not cands:
        return False
    n = max(cands); c = cands[n]
    if cur.get("id") == n and cur.get("image"):
        new = dict(cur, title=c.get("title") or cur.get("title"))
        for k in ("start", "end", "thumb"):
            if c.get(k): new[k] = c[k]
        if not new.get("benefit"):
            b, how = sunday_benefit(new.get("title", ""), "")
            if b: new["benefit"], new["benefitSrc"] = b, how
    else:
        img = start = end = text = thumb = ""; via = ""
        if os.environ.get("NEXON_API_KEY"):
            try:
                img, start, end, text, thumb = _sunday_detail_api(n); via = "api"
            except Exception as e:
                log("  썬데이 /notice-event/detail 실패:", e)
        if not img:
            try:
                img, s2, e2, text2 = _sunday_detail_html(n); via = via or "html"
                start, end, text = start or s2, end or e2, text or text2
            except Exception as e:
                log("  썬데이 글 HTML(대체) 실패:", e)
        title = c.get("title", "")
        b, how = sunday_benefit(title, text)
        new = {"id": n, "title": title, "url": f"{EVENT_BASE}/{n}", "image": img or c.get("thumb") or thumb,
               "thumb": c.get("thumb") or thumb, "start": c.get("start") or start, "end": c.get("end") or end, "date": c.get("date", ""),
               "benefit": b, "benefitSrc": how, "via": via or c.get("via", "")}
        log("  썬데이 메이플:", title, new["image"], "혜택:", b or "(제목 표시)")
    new = {k: v for k, v in new.items() if v not in (None, "")}
    if new != cur:
        feed["sunday"] = new
        return True
    return False

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
    _API_NOTICES.clear(); _API_EVENTS.clear()
    _HAVE_MINOR.clear(); _HAVE_MINOR.update(int(x["id"].split(":")[1]) for x in items.get("patch", []) if str(x.get("id", "")).startswith("minor:"))
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
            n = merge(lst, new)
            if k == "patch":
                m = apply_minor(lst, _MINOR, wm); n += m
            added += n
            s.update(ok=True, checkedAt=now_iso(), lastOkAt=now_iso(), error="")
            log(f"[{k}] OK, 새 글 {n}개")
        except Exception as e:
            s.update(ok=False, checkedAt=now_iso(), error=str(e)[:400])
            log(f"::warning::[{k}] 실패: {e}")
        if bool(prev.get("ok", True)) != s["ok"] or (not prev):
            flipped = True
        srcs[k] = s
    sun_changed = False
    try:
        sun_changed = src_sunday(feed, run_all, minute)
    except Exception as e:
        log(f"::warning::[sunday] 실패: {e}")
    last = feed.get("updatedAt") or ""
    stale = True
    try:
        stale = (datetime.datetime.now(KST) - datetime.datetime.fromisoformat(last)).total_seconds() > HEARTBEAT_H * 3600
    except Exception:
        pass
    wm_changed = (old.get("state", {}).get("watermarks") != wm)
    changed = bool(added or flipped or stale or wm_changed or sun_changed)  # 워터마크 저장 안 하면 같은 공지 detail 을 매번 다시 호출하게 됨
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
