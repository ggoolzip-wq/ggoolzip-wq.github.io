#!/usr/bin/env python3
"""b251: 공식 공지(본섭 업데이트·테섭)에서 '새 보스 / 새 난이도'를 찾아 data/bosses_auto.json 에 자동 추가.

쉽게 말하면:
  1) 공지 본문을 읽어 '보스 X의 익스트림 모드가 추가됩니다', '신규 보스 X(노멀, 하드)가 추가됩니다' 같은 문장을 찾음
  2) 같은 공지의 결정석 가격표·'최대 N인'·'X에서 Y 획득' 문장에서 가격/파티 인원/드롭을 찾음 (확실하지 않으면 그 칸은 비움)
  3) 사이트에 이미 있는(src/app.js BOSSES) 보스·난이도는 건드리지 않음. 이미 자동 추가된 칸도 덮어쓰지 않음(빈 칸만 채움)
  4) 테섭 공지에서 찾은 것은 pending(대기)에만 넣고, 본섭 공지가 같은 보스·난이도를 확인하면 bosses 로 옮김
  5) 가격은 1e5~5e10 메소, 파티는 1~6명만 받음. 추가한 내용은 log 에 남김 (지우지 않음)
사이트(src/app.js applyAutoBosses)는 이 파일을 합치되 내장 데이터가 항상 우선.
"""
import datetime, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nexon_prices

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTO = os.path.join(ROOT, "data", "bosses_auto.json")
APP = os.path.join(ROOT, "src", "app.js")
KST = datetime.timezone(datetime.timedelta(hours=9))
PRICE_MIN, PRICE_MAX = 100_000, 50_000_000_000
DIFF = {"이지": "easy", "노멀": "normal", "노말": "normal", "하드": "hard", "카오스": "chaos", "익스트림": "extreme"}
DIFF_RE = "|".join(DIFF)
NAME = r"[가-힣A-Za-z0-9][가-힣A-Za-z0-9 ]{0,18}?"
LOG_CAP = 300

def now_iso():
    return datetime.datetime.now(KST).replace(microsecond=0).isoformat()

def norm(s):
    return re.sub(r"[\s()·:\[\]「」'\"‘’“”]", "", str(s or "")).lower()

def builtin(app_path=APP):
    """src/app.js 의 BOSSES → [{id,name,type,diffs,aliases}]"""
    s = open(app_path, encoding="utf-8").read()
    out = []
    for m in re.finditer(r"\{id:'([^']+)',name:'([^']+)',type:'(weekly|monthly)',diffs:\[([^\]]*)\](?:,aliases:\[([^\]]*)\])?", s):
        q = lambda x: re.findall(r"'([^']*)'", x or "")
        out.append({"id": m.group(1), "name": m.group(2), "type": m.group(3), "diffs": q(m.group(4)), "aliases": q(m.group(5))})
    return out

def find_boss(name, bosses):
    n = norm(name)
    for b in bosses:
        if n in [norm(x) for x in [b["name"]] + list(b.get("aliases") or [])]:
            return b
    return None

def auto_id(name):
    return "auto_" + hashlib.sha1(norm(name).encode()).hexdigest()[:8]

def _blocks(html):
    p = nexon_prices._PostParser(); p.feed(html); p.close()
    return p.blocks

def parse_notice(html):
    """공지 HTML → [{name, diff, price?, partyMax?, type?, drops?, how}] (확실한 칸만)"""
    blocks = _blocks(html)
    lines = [v for k, v in blocks if k == "p"]
    text = "\n".join(lines)
    found = {}
    def add(name, diff, how):
        name = re.sub(r"\s+", " ", name).strip(" '\"‘’“”")
        if not name or diff not in DIFF.values() or len(name) > 20:
            return None
        k = (norm(name), diff)
        if k not in found:
            found[k] = {"name": name, "diff": diff, "how": how}
        return found[k]
    for ln in lines:
        # 보스 X의 익스트림 모드가 추가됩니다 / 보스 X에 하드 난이도가 추가됩니다
        for m in re.finditer(rf"보스\s*['‘\"“]?({NAME})['’\"”]?\s*(?:의|에)\s*({DIFF_RE})\s*(?:모드|난이도)(?:가|이)?\s*추가", ln):
            add(m.group(1), DIFF[m.group(2)], "sentence")
        # 신규 보스 'X'(노멀, 하드)가 추가됩니다
        for m in re.finditer(rf"신규\s*보스\s*['‘\"“]?({NAME})['’\"”]?\s*(?:\(([^)]*)\))?\s*(?:이|가|와|과)?\s*(?:새롭게\s*)?(?:추가|등장)", ln):
            ds = [DIFF[d] for d in re.findall(DIFF_RE, m.group(2) or "")]
            for d in ds:  # 난이도가 안 적혀 있으면 추가하지 않음(추측 금지)
                add(m.group(1), d, "sentence")
    # 결정석 가격표: 표에 처음 보이는 보스/난이도도 후보 (가격과 함께)
    try:
        rows = nexon_prices.parse_post(html)["rows"]
    except Exception:
        rows = []
    prices = {}
    for r in rows:
        m = re.match(rf"^(.*?)\s*[(（]\s*({DIFF_RE})\s*[)）]\s*$", str(r.get("boss", "")).strip())
        if not m:
            continue
        k = (norm(m.group(1)), DIFF[m.group(2)])
        v = r.get("new")
        if isinstance(v, int) and PRICE_MIN <= v <= PRICE_MAX:
            prices[k] = (m.group(1).strip(), v)
    for k, (nm, v) in prices.items():
        f = found.get(k) or add(nm, k[1], "price-table")
        if f is not None:
            f["price"] = v
    # 파티 인원 / 주간·월간 / 드롭: 보스 이름이 같은 줄에 있을 때만
    for f in found.values():
        nm = re.escape(f["name"])
        for ln in lines:
            if not re.search(nm, ln):
                continue
            m = re.search(r"최대\s*([1-6])\s*(?:인|명)", ln) or re.search(r"([1-6])\s*인\s*(?:파티|까지)", ln)
            if m and "partyMax" not in f and re.search(r"입장|파티", ln):
                f["partyMax"] = int(m.group(1))
            if "type" not in f:
                if re.search(nm + r".{0,15}(월간|매월|월\s*1회)|(월간|매월).{0,15}" + nm, ln): f["type"] = "monthly"
                elif re.search(nm + r".{0,15}(주간|매주|주\s*1회)|(주간|매주).{0,15}" + nm, ln): f["type"] = "weekly"
            dn = [k for k, v in DIFF.items() if v == f["diff"]]
            dre = "(?:" + "|".join(dn) + ")"
            for m in re.finditer(rf"(?:{dre}\s*{nm}|{nm}\s*\(\s*{dre}\s*\))\s*(?:에서|처치\s*시)\s*['‘\[「]?([^'’\]」,.]+?)['’\]」]?\s*(?:을|를|이|가)?\s*(?:획득|드롭)", ln):
                item = m.group(1).strip()
                if 1 < len(item) <= 30:
                    f.setdefault("drops", [])
                    if item not in f["drops"]: f["drops"].append(item)
    return list(found.values())

def load(path=AUTO):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    d.setdefault("version", 1); d.setdefault("bosses", []); d.setdefault("pending", []); d.setdefault("log", [])
    return d

def save(d, path=AUTO):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    d["log"] = d["log"][-LOG_CAP:]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1); f.write("\n")

FIELDS = ("price", "partyMax", "drops")

def _entry(lst, name):
    for e in lst:
        if norm(e["name"]) == norm(name):
            return e
    return None

def _fill(dst, f, src, at):
    """빈 칸만 채움 → 채운 필드 목록"""
    got = []
    for k in FIELDS:
        if k in f and k not in dst:
            dst[k] = f[k]; got.append(k)
    dst.setdefault("src", src); dst.setdefault("addedAt", at)
    return got

def apply(d, findings, src, live, built=None, at=None):
    """findings 를 d 에 합침. live=False(테섭) → pending. 반환: 바뀌었으면 True"""
    built = built if built is not None else builtin()
    at = at or now_iso(); changed = False
    for f in findings:
        if f["diff"] not in DIFF.values():
            continue
        b = find_boss(f["name"], built)
        if b and f["diff"] in b["diffs"]:
            continue  # 내장 데이터 우선: 이미 있는 보스·난이도는 절대 건드리지 않음
        name = b["name"] if b else f["name"]
        lst = d["bosses"] if live else d["pending"]
        if not live and (_entry(d["bosses"], name) or {}).get("diffs", {}).get(f["diff"]):
            continue  # 이미 본섭 확인됨
        e = _entry(lst, name)
        if not e:
            e = {"id": b["id"] if b else auto_id(name), "name": name, "diffs": {}}
            if b: e["builtin"] = True
            lst.append(e)
        if "type" not in e:
            t = b["type"] if b else f.get("type")
            if t: e["type"] = t
        new = f["diff"] not in e["diffs"]
        slot = e["diffs"].setdefault(f["diff"], {})
        got = _fill(slot, f, src, at)
        if new or got:
            changed = True
            d["log"].append({"at": at, "action": ("add" if live else "pending") if new else "fill", "boss": name, "diff": f["diff"],
                             "fields": got, "how": f.get("how", ""), "src": src})
            print(f"[boss-auto] {'본섭' if live else '테섭'} {name}({f['diff']}) {'추가' if new else '보강'} {got} ← {src.get('url','')}")
        if live:  # 본섭 확인 → 테섭 대기에서 빼기
            p = _entry(d["pending"], name)
            if p and f["diff"] in p["diffs"]:
                del p["diffs"][f["diff"]]
                if not p["diffs"]: d["pending"].remove(p)
                d["log"].append({"at": at, "action": "confirm", "boss": name, "diff": f["diff"], "src": src})
    if changed:
        d["updatedAt"] = at
    return changed

def process(items, live, fetch, path=AUTO, built=None):
    """items=[{url,title,date}] 공지들 → data/bosses_auto.json 갱신. 반환 changed"""
    d = load(path); changed = False
    for it in items:
        try:
            html = fetch(it["url"])
            fs = parse_notice(html)
        except Exception as e:
            print(f"::warning::[boss-auto] {it.get('url')} 실패: {e}"); continue
        src = {"url": it["url"], "title": it.get("title", ""), "date": (it.get("date") or "")[:10], "server": "live" if live else "test"}
        changed = apply(d, fs, src, live, built) or changed
    if changed:
        save(d, path)
    return changed

if __name__ == "__main__":  # python3 scripts/boss_auto.py live|test URL_or_file [title] [date]
    kind, u = sys.argv[1], sys.argv[2]
    fetch = (lambda x: open(x, encoding="utf-8").read()) if os.path.exists(u) else nexon_prices.fetch
    print(process([{"url": u, "title": sys.argv[3] if len(sys.argv) > 3 else "", "date": sys.argv[4] if len(sys.argv) > 4 else ""}], kind == "live", fetch))
