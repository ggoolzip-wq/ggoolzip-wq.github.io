#!/usr/bin/env python3
"""메이플스토리 공식 '업데이트' 공지에서 '강렬한 힘의 결정' 판매 가격표를 찾아 읽는 파서
(GitHub Actions 의 scripts/update_prices.py 가 사용. 표준 라이브러리만 사용)

테스트: MBT_FIXTURE_DIR 환경 변수에 저장된 HTML 폴더를 주면 실제 접속 대신 그 파일을 읽습니다.
"""
import json, os, re, sys, time, urllib.parse, urllib.request, urllib.error
from html.parser import HTMLParser

SITE = "https://maplestory.nexon.com"
LIST_URL = SITE + "/News/Update?page={page}"
POST_URL = SITE + "/News/Update/{id}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
FIXTURE_DIR = os.environ.get("MBT_FIXTURE_DIR")  # 테스트용: 실제 접속 대신 저장된 HTML 사용


# ---------------------------------------------------------------- 가져오기
def fetch(url, timeout=15):
    if FIXTURE_DIR:  # list_page1.html, post_813.html ...
        m = re.search(r"page=(\d+)", url)
        name = f"list_page{m.group(1)}.html" if "page=" in url else "post_%s.html" % url.rstrip("/").rsplit("/", 1)[-1]
        path = os.path.join(FIXTURE_DIR, name)
        if not os.path.exists(path):
            raise urllib.error.HTTPError(url, 404, "fixture not found", None, None)
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ko-KR,ko;q=0.9", "Referer": SITE + "/News/Update"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        cs = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(cs, errors="replace")


def parse_list(html):
    """업데이트 목록 → [{id, title, date}] (최신순)"""
    out, seen = [], set()
    for m in re.finditer(r'<a[^>]+href="(?:https?://maplestory\.nexon\.com)?/news/update/(\d+)[^"]*"[^>]*>(.*?)</a>(.*?)(?=<a[^>]+href="[^"]*/news/update/\d+|</ul>|$)',
                         html, re.I | re.S):
        pid = int(m.group(1))
        if pid in seen:
            continue
        seen.add(pid)
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        title = re.sub(r"&nbsp;", " ", title)
        d = re.search(r"(\d{4}\.\d{2}\.\d{2})", m.group(3))
        out.append({"id": pid, "title": title, "date": d.group(1) if d else ""})
    out.sort(key=lambda x: -x["id"])
    return out


class _PostParser(HTMLParser):
    """공지 본문의 표(셀 텍스트)와 문단 텍스트를 순서대로 모음"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []          # ('p', text) | ('table', [[cell,...],...])
        self.title = ""
        self._t = []              # 표 스택
        self._cell = None
        self._buf = []
        self._in_title = 0
        self._title_buf = []

    BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "li", "br"}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "p" and "qs_title" in (a.get("class") or ""):
            self._in_title = 1
        if tag == "table":
            self._flush()
            self._t.append([])
        elif tag == "tr" and self._t:
            self._t[-1].append([])
        elif tag in ("td", "th") and self._t:
            self._cell = []
        elif tag in self.BLOCK and self._cell is None and not self._t:
            self._flush()

    def handle_endtag(self, tag):
        if tag == "p" and self._in_title:
            self._in_title = 0
            self.title = re.sub(r"\s+", " ", "".join(self._title_buf)).strip()
        if tag in ("td", "th") and self._t and self._cell is not None:
            txt = re.sub(r"\s+", " ", " ".join(self._cell)).strip()
            if not self._t[-1]:
                self._t[-1].append([])
            self._t[-1][-1].append(txt)
            self._cell = None
        elif tag == "table" and self._t:
            rows = [r for r in self._t.pop() if any(c for c in r)]
            self.blocks.append(("table", rows))
        elif tag in self.BLOCK and self._cell is None and not self._t:
            self._flush()

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)
        if self._cell is not None:
            self._cell.append(data)
        elif not self._t:
            self._buf.append(data)

    def _flush(self):
        t = re.sub(r"\s+", " ", "".join(self._buf)).strip()
        if t:
            self.blocks.append(("p", t))
        self._buf = []

    def close(self):
        super().close()
        self._flush()


def _num(s):
    s = (s or "").replace(",", "").replace(" ", "")
    m = re.fullmatch(r"(\d+)(?:메소)?", s)
    if m:
        return int(m.group(1))
    # '1억 2,345만' 같은 표기도 허용
    m = re.fullmatch(r"(?:(\d+)억)?(?:(\d+)만)?(\d+)?(?:메소)?", s)
    if m and any(m.groups()):
        return int(m.group(1) or 0) * 100000000 + int(m.group(2) or 0) * 10000 + int(m.group(3) or 0)
    return None


DATE_RE = re.compile(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일")


def parse_post(html):
    """공지 HTML → {title, rows:[{boss, old, new}], notes:[...]} (가격표가 없으면 rows=[])"""
    p = _PostParser()
    p.feed(html)
    p.close()
    rows, notes, ctx = [], [], ""
    for kind, val in p.blocks:
        if kind == "p":
            ctx = val
            if re.search(r"힘의 결정|결정 판매|결정 가격|결정의 판매|결정석", val):
                if val not in notes:
                    notes.append(val)
            continue
        table = val
        if not table:
            continue
        head = " ".join(table[0])
        is_price = ("보스" in head and any(k in head for k in ("가격", "기존", "변경"))) or ("결정" in ctx and "가격" in ctx)
        if not is_price:
            continue
        body = table[1:] if not any(_num(c) for c in table[0][1:]) else table
        for r in body:
            if len(r) < 2:
                continue
            nums = [_num(c) for c in r[1:]]
            nums = [n for n in nums if n is not None]
            if not nums or not r[0]:
                continue
            rows.append({"boss": r[0], "old": nums[0] if len(nums) > 1 else None, "new": nums[-1]})
    # 적용일 메모 (예: '※ 검은 마법사의 결정 판매 가격은 2026년 10월 1일(목)부터 적용됩니다.')
    for r in rows:
        for n in notes:
            m = DATE_RE.search(n)
            name = re.sub(r"\s*\(.*\)$", "", r["boss"]).strip()
            if m and name and name in n:
                r["effective"] = "%04d-%02d-%02d" % tuple(map(int, m.groups()))
                r["effective_note"] = n
    return {"title": p.title, "rows": rows, "notes": notes}


def nexon_prices(posts=8, gather=1, pages=1):
    scanned, found = [], []
    items = []
    for page in range(1, pages + 1):
        items += parse_list(fetch(LIST_URL.format(page=page)))
    if not items:
        raise RuntimeError("업데이트 목록을 읽지 못했습니다 (페이지 구조가 바뀌었을 수 있음)")
    for it in items[:posts]:
        url = POST_URL.format(id=it["id"])
        try:
            info = parse_post(fetch(url))
        except Exception as e:  # 한 글 실패는 건너뜀
            scanned.append({"url": url, "title": it["title"], "error": str(e)[:200]})
            continue
        scanned.append({"url": url, "title": info["title"] or it["title"], "rows": len(info["rows"])})
        if info["rows"]:
            found.append({"url": url, "title": info["title"] or it["title"], "date": it["date"],
                          "rows": info["rows"], "notes": info["notes"]})
            if len(found) >= gather:
                break
    if not found:
        return {"ok": False, "error": {"name": "NO_PRICE_TABLE", "message": f"최근 업데이트 공지 {len(scanned)}개에서 결정 가격표를 찾지 못했습니다."}, "scanned": scanned}
    first = found[0]
    return {"ok": True, "source": {"url": first["url"], "title": first["title"], "date": first["date"]},
            "rows": first["rows"], "notes": first["notes"], "more": found[1:], "scanned": scanned,
            "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
