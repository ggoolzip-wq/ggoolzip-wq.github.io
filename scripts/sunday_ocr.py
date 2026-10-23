#!/usr/bin/env python3
"""썬데이 메이플 이미지 OCR → '이번 주 혜택' 글자 + 본문(이벤트 기간~혜택 상자) 잘라낸 sunday.png

update-feed.yml 에서 새 썬데이 글이 있을 때만(update_feed.py 가 sunday_ocr=true 출력) 실행 — 글 하나당 한 번.
필요: tesseract-ocr + tesseract-ocr-kor (apt), Pillow (pip) — 이 단계에서만 설치. update_feed.py 는 그대로 표준 라이브러리만.
결과(feed.json 의 sunday): benefit(' · ' 로 이은 혜택, 최대 4개 — b256: 알려진 문장 사전(KNOWN)+퍼지 매칭 우선, 못 믿을 글자면 비움 → 사이트가 제목 표시), benefitSrc='ocr', crop='sunday.png?v=<id>', ocr={image, ok, at, tries, lines}
실패하면 crop 없음(사이트는 원본 이미지), benefit 은 그대로(없으면 사이트가 제목 표시). 3번 실패하면 그 글은 더 시도 안 함.
로컬 확인: python3 scripts/sunday_ocr.py --image 파일또는URL [--crop out.png]
"""
import csv, datetime, difflib, io, json, os, re, subprocess, sys, tempfile, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.environ.get("FEED_OUT") or os.path.join(ROOT, "feed.json")
CROP = os.environ.get("SUNDAY_CROP") or os.path.join(ROOT, "sunday.png")
KST = datetime.timezone(datetime.timedelta(hours=9))
MAX_TRIES = 3

KEY_RE = re.compile(r"어빌리티|스타포스|파괴|미라클\s*타임|추가\s*옵션|메소|몬스터\s*파크|경험치|큐브|심볼|룬|잠재\s*능력|에디셔널|솔\s*에르다|"
                    r"주문의\s*흔적|명성치|강화|확률|드롭|아이템\s*획득|보스|헥사|에르다|코어|유니온|재설정|샤이닝")
VAL_RE = re.compile(r"\d+\s*%|할인|감소|증가|\d+\s*배|무료|성공|추가|상승|2배|확률\s*업")
NOTE_RE = re.compile(r"^[ㆍ·•*※\-]|^단\s*[,.]|않습니다|않아요|바로\s*가기|궁금|참고|유의|확인하세요|게임\s*정보|표기|기준")
FOOT_RE = re.compile(r"바로\s*가기|궁금하다면|게임\s*정보")
PERIOD_RE = re.compile(r"(?:이|미)?\s*벤트\s*기간|\d{4}\s*년\s*\d{1,2}\s*월\s*\d{1,2}\s*일|오전.*~.*오후")

def log(*a):
    print(*a, flush=True)

def tesseract_words(img, invert, scale=2, chunk=700, ov=80):
    """긴 이미지를 chunk 높이로 나눠(겹침 ov) 키워서 OCR → 원본 좌표의 단어 목록"""
    from PIL import Image, ImageOps
    g = img.convert("L"); W, H = g.size; words = []; y = 0
    with tempfile.TemporaryDirectory() as td:
        while True:
            c = g.crop((0, y, W, min(H, y + chunk)))
            if invert:
                c = ImageOps.invert(c)
            c = c.resize((W * scale, c.height * scale), Image.LANCZOS)
            p = os.path.join(td, "c.png"); c.save(p)
            out = subprocess.run(["tesseract", p, "-", "-l", "kor+eng", "--psm", "6", "tsv"], capture_output=True, text=True, timeout=120).stdout
            for r in csv.DictReader(io.StringIO(out), delimiter="\t", quoting=csv.QUOTE_NONE):
                t = (r.get("text") or "").strip()
                try:
                    conf = float(r.get("conf") or -1)
                except ValueError:
                    conf = -1
                if t and conf > 30:
                    words.append({"t": t, "x": int(r["left"]) / scale, "y": int(r["top"]) / scale + y, "w": int(r["width"]) / scale,
                                  "h": int(r["height"]) / scale, "conf": conf, "line": (y, r["block_num"], r["par_num"], r["line_num"])})
            if y + chunk >= H:
                break
            y += chunk - ov
    return words

def join_words(ws):
    """한글이 글자마다 끊겨 나오는 것 보정: 한 글자짜리 한글 조각이 이어지면 붙여 씀
    ('어 빌 리 티 재설정 명 성 치 비용' → '어빌리티 재설정 명성치 비용'). 여러 글자 조각 사이는 띄어 씀."""
    ws = sorted(ws, key=lambda w: w["x"]); s = ""; prev = None
    one = lambda t: len(t) == 1 and "가" <= t <= "힣"
    for w in ws:
        t = w["t"]
        if prev is not None:
            s += "" if (one(prev) and one(t)) or t in (",", ".", "%", ")") or prev in ("(",) else " "
        s += t; prev = t
    return s

def to_lines(words):
    d = {}
    for w in words:
        d.setdefault(w["line"], []).append(w)
    lines = []
    for ws in d.values():
        lines.append({"y": min(w["y"] for w in ws), "b": max(w["y"] + w["h"] for w in ws), "t": clean(join_words(ws)),
                      "conf": sum(w["conf"] for w in ws) / len(ws)})
    lines.sort(key=lambda l: l["y"])
    out = []  # 겹친 조각에서 같은 줄이 두 번 나오면 하나만
    for l in lines:
        if out and abs(out[-1]["y"] - l["y"]) < 12 and (out[-1]["t"] == l["t"] or l["t"] in out[-1]["t"] or out[-1]["t"] in l["t"]):
            if len(l["t"]) > len(out[-1]["t"]): out[-1] = l
            continue
        out.append(l)
    return out

def clean(t):
    t = re.sub(r"\s+", " ", t).strip()
    # b256 fix1: 흔한 오인식 — 흰 굵은 글씨 '룬' 이 '=' / 'ㆍ' 로, 가짜 꺾쇠(』「」) 섞임
    t = re.sub(r"^[=ㆍ]\s*(?=(?:기본\s*)?(?:지속|경험치\s*버프))", "룬 ", t)
    t = re.sub(r"\s*[』「」『]\s*", " ", t).strip()
    t = re.sub(r"(\d)\s*%", r"\1%", t)
    t = re.sub(r"(\d)\s+(성|배|회|레벨|개)", r"\1\2", t)
    t = re.sub(r"\s*([,.!?])", r"\1", t)
    t = re.sub(r"[|'\"`~_=<>{}\[\]]+$", "", t).strip()
    return t

# b256 fix5: 알려진 썬데이 혜택 문장 사전. (보여줄 글, [비교용 글자(한글만, 숫자·띄어쓰기 없음)…]). {n} 은 OCR 줄의 숫자(%/배)로 채움
KNOWN = [
    ("메인 스탯의 강화 확률 {n}% 증가", ["메인스탯의강화확률증가", "메인스탯이레벨이상일때메인스탯의강화확률증가"]),
    ("룬 기본 지속시간 {n}% 증가", ["룬기본지속시간증가"]),
    ("룬 경험치 버프 +{n}%", ["룬경험치버프효과"], {"100"}),
    ("콤보킬 경험치 획득량 +{n}%", ["콤보킬경험치획득량"]),
    ("룬 재등장·재사용 대기시간 감소", ["룬재등장및재사용대기시간감소"]),
    ("트레져 헌터 경험치 {n}배", ["트레져헌터경험치배"]),
    ("사냥으로 얻는 솔 에르다 {n}배 증가", ["사냥을통해획득할수있는솔에르다배증가", "솔에르다배증가"]),
    ("몬스터파크 클리어 경험치 추가 {n}%", ["몬스터파크클리어경험치추가증가", "몬스터파크클리어경험치추가"]),
    ("주문의 흔적 강화 비용 {n}% 할인", ["주문의흔적강화비용할인"]),
    ("위대한 소울 획득 확률 {n}배", ["소울조각사용시위대한소울획득확률배"]),
    ("몬스터 컬렉션 신규 등록 확률 +{n}%", ["몬스터컬렉션신규몬스터등록확률추가"]),
    ("엘리트 몬스터 소환 수 증가", ["사냥시소환되는엘리트몬스터수증가"]),
    ("어빌리티 재설정 명성치 비용 {n}% 할인", ["어빌리티재설정명성치비용할인"]),
    ("21성 이하 스타포스 파괴 확률 {n}% 감소", ["성이하에서스타포스강화시파괴확률감소", "성이하스타포스파괴확률감소"]),
    ("스타포스 강화 비용 {n}% 할인", ["스타포스강화비용할인"]),
    ("흔적 복구 비용 {n}% 할인", ["흔적복구비용할인"]),
    ("샤이닝 스타포스 타임", ["샤이닝스타포스타임"]),
    ("미라클 타임", ["미라클타임", "스페셜미라클타임"]),
]
_hn = lambda t: re.sub(r"[^가-힣]", "", t)

def _cover(alias, t):
    """alias 글자 중 t 에 같은 순서로 나온 비율 (0~1)"""
    m = difflib.SequenceMatcher(None, alias, t, autojunk=False)
    return sum(b.size for b in m.get_matching_blocks()) / len(alias)

def _fill(tpl, raw, allowed=None):
    """{n} 채우기. allowed(늘 같은 값)가 있으면 그 밖의 숫자(오인식 '700%')는 그 값으로"""
    if "{n}" not in tpl:
        return tpl
    unit = "배" if "{n}배" in tpl else "%"
    m = re.search(r"(\d{1,4})\s*" + unit, raw)
    if not m:
        return None
    n = m.group(1)
    if allowed and n not in allowed and len(allowed) == 1:
        n = next(iter(allowed))
    return tpl.replace("{n}", n)

def known_match(t):
    """한 줄(또는 두 줄 합친 글)을 사전과 비교 → (보여줄 글, 점수) 또는 None. 안내 줄은 비교 안 함"""
    h = _hn(t); best = None
    if len(h) < 4:
        return None
    for k in KNOWN:
        tpl, aliases, allowed = k[0], k[1], (k[2] if len(k) > 2 else None)
        for a in aliases:
            if len(h) > 2 * len(a) + 6:
                continue
            c = _cover(a, h) * min(1, (len(a) + 4) / max(len(h), 1)) ** 0.25  # 길이가 너무 길면(안내 문장) 조금 감점
            if c >= 0.72 and (best is None or c > best[1]):
                v = _fill(tpl, t, allowed)
                if v: best = (v, c, tpl)
    return best

def known_hits(lines):
    """사전 일치 [(y, 글, 점수, tpl)] — 두 줄짜리 제목(…강화 시 / 파괴 확률 30% 감소)은 합쳐서도 비교"""
    L = [l for l in lines if l["t"]]; hits = {}
    for i, l in enumerate(L):
        if NOTE_RE.search(l["t"]) or l["t"].count("%") >= 2 or "=" in l["t"]:  # 안내 줄·수식 상자(100% + 100% = 300%)
            continue
        cands = [l["t"]]
        if i + 1 < len(L) and L[i + 1]["y"] - l["b"] < 40 and not NOTE_RE.search(L[i + 1]["t"]) and L[i + 1]["t"].count("%") < 2 and "=" not in L[i + 1]["t"] and not re.search(r"\d+\s*[%배]", l["t"]):
            cands.append(l["t"] + " " + L[i + 1]["t"])  # 윗줄에 값이 없을 때만(수식 상자 숫자가 아랫줄 제목에 붙는 것 방지)
        for t in cands:
            k = known_match(t)
            if k and (k[2] not in hits or k[1] > hits[k[2]][2] + 0.05):
                hits[k[2]] = (hits.get(k[2], (l["y"],))[0], k[0], k[1], k[2])
    return sorted(hits.values())

def looks_clean(t):
    """OCR 글이 믿을 만한지: 한글·숫자·% 위주, 이상한 기호·영문 조각 없음"""
    if re.search(r"[』「」『|@#$^&*_\\]|[A-Za-z]{2,}|니다|받을\s*수|있어요|적용\s*됩|함께", t):  # 안내 문장 꼬리도 혜택 아님
        return False
    if re.search(r"(?:^|\s)(?:[A-Za-z]|\d{1,3})(?=\s|$|!)|\S!\s+\S", re.sub(r"\d+\s*(?:%|배|개|성|레벨|회)", "", t)):  # 홀로 떨어진 글자·숫자 조각(오인식)
        return False
    ws = re.findall(r"[가-힣]+", t)
    if any(len(w) == 1 and w not in "및시수등의개" for w in ws) or len({w for w in ws if len(w) >= 2}) < len([w for w in ws if len(w) >= 2]):
        return False  # 홀로 떨어진 한 글자(오인식) · 같은 낱말 반복
    h = _hn(t)
    if any(_cover(a, h) >= 0.6 and 4 <= len(h) <= 1.5 * len(a) for k in KNOWN for a in k[1]):  # 사전 문장이 깨진 것 → 버림
        return False
    ok = sum(1 for ch in t if "가" <= ch <= "힣" or ch.isdigit() or ch in " %+·.,!~()")
    hang = re.findall(r"[가-힣]{2,}", t)
    return ok / max(1, len(t)) >= 0.9 and len(hang) >= 2

def legacy_benefits(lines):
    """예전 규칙(키워드+값 줄) — b256: '+N%' 허용(fix2), 수식 상자·짧은 이름표 줄과 합치지 않음(fix3)"""
    out = []; i = 0
    L = [l for l in lines if l["t"]]
    formula = lambda t: t.count("%") >= 2 or re.search(r"=|버프.*혜택|혜택.*버프", t)
    while i < len(L):
        t = L[i]["t"]
        if NOTE_RE.search(t) or not KEY_RE.search(t) or len(t) > 40 or re.search(r"[A-Za-z]{2,}", t):
            i += 1; continue
        if re.fullmatch(r"\s*(?:스페셜\s*)?미라클\s*타임\s*!?", t):
            out.append((L[i]["y"], "미라클 타임", L[i]["b"] - L[i]["y"])); i += 1; continue
        if not VAL_RE.search(t) and len(_hn(t)) < 6:  # '기본 룬'·'축복의 룬' 같은 이름표
            i += 1; continue
        y, hgt = L[i]["y"], L[i]["b"] - L[i]["y"]
        if not VAL_RE.search(t) and i + 1 < len(L) and not NOTE_RE.search(L[i + 1]["t"]) and L[i + 1]["y"] - L[i]["b"] < 40 \
                and VAL_RE.search(L[i + 1]["t"]) and not formula(L[i + 1]["t"]):
            t = t + " " + L[i + 1]["t"]; i += 1
        i += 1
        if VAL_RE.search(t) and re.search(r"\d|할인|감소|증가|무료", t) and not formula(t) and len(re.findall(r"\+", t)) <= 1 \
                and len(t) <= 44 and t.count("%") <= 1:
            out.append((y, t, hgt))
    return out

def benefits(lines, extra_hits=None):
    """혜택 최대 4개: ① 사전 일치(여러 OCR 결과 합침) ② 모자라면 예전 규칙 중 깨끗한 글만(fix4: 큰 글씨=제목 먼저, 작은 말풍선은 나중) → 위에서 아래 순서"""
    hits = {}; votes = {}
    for h in known_hits(lines) + list(extra_hits or []):  # 여러 전처리 결과: 같은 문장은 숫자가 가장 많이 나온 것(오인식 '+700%' 방지)
        votes.setdefault(h[3], []).append(h)
    for tpl, hs in votes.items():
        cnt = {}
        for h in hs: cnt[h[1]] = cnt.get(h[1], 0) + 1
        v = max(cnt, key=lambda k: (cnt[k], max(x[2] for x in hs if x[1] == k)))
        hits[tpl] = (min(x[0] for x in hs), v, max(x[2] for x in hs), tpl)
    picked = [(h[0], h[1]) for h in hits.values()]
    rest = []
    for y, t, hgt in legacy_benefits(lines):
        t = shorten(t)
        if not t or not looks_clean(t) or known_match(t) or any(t in p or p in t for _, p in picked):
            continue
        rest.append((-hgt, y, t))
    for _, y, t in sorted(rest):
        if len(picked) >= 4: break
        if not any(t == p or t in p or p in t for _, p in picked):
            picked.append((y, t))
    picked.sort()
    if len(picked) > 4:  # 사전 일치가 4개 넘으면 위에서 4개
        picked = picked[:4]
    return [t for _, t in picked]

def shorten(t):
    t = re.sub(r"(이하|이상)\s*에서", r"\1", t)
    t = re.sub(r"\b(\d{2})(?:23|3|S|s)\s*(이하|이상)", r"\1성 \2", t)  # OCR 이 '21성'을 '2123'으로 읽는 경우
    t = re.sub(r"(\d+성)\s*(이하|이상)", r"\1 \2", t)
    t = re.sub(r"\s*강화\s*시\s+", " ", t)
    t = re.sub(r"\s*시\s+(?=파괴|성공|확률)", " ", t)
    t = re.sub(r"[!.]+$", "", t)
    return re.sub(r"\s+", " ", t).strip()

def crop_box(lines, W, H, pad=30):
    """이벤트 기간 줄 ~ 마지막 혜택/안내 줄(바로가기 같은 아래쪽 안내 전)까지"""
    per = [l for l in lines if PERIOD_RE.search(l["t"])]
    ben = [l for l in lines if KEY_RE.search(l["t"]) and VAL_RE.search(l["t"]) and not NOTE_RE.search(l["t"])]
    if not per or not ben:
        return None
    top = max(0, min(per[0]["y"], ben[0]["y"]) - pad - 20)
    foot = [l for l in lines if FOOT_RE.search(l["t"]) and l["y"] > ben[-1]["b"]]
    limit = foot[0]["y"] - 10 if foot else H
    body = [l for l in lines if l["y"] >= ben[-1]["y"] and l["b"] < limit and l["y"] - ben[-1]["b"] < 260]
    bottom = min(H, max([ben[-1]["b"]] + [l["b"] for l in body]) + pad + 30, limit if foot else H)
    if bottom - top < 120:
        return None
    return (0, int(top), W, int(bottom))

def preprocess(img, mode):
    """b256: OCR 전처리 — 'inv' 반전(어두운 바탕 밝은 글씨), 'raw' 원본, 'bin' 반전+대비 늘림+이진화(3배 확대), 'wht' 흰·노란 글씨만 검게"""
    from PIL import ImageOps
    if mode == "wht":  # 흰·노란 글씨만(R·G 둘 다 밝은 픽셀) 검게 → 하늘색 상자 위 흰 글씨+노란 숫자도 읽힘
        from PIL import ImageChops
        r, g, _ = img.split()
        return ImageChops.darker(r, g).point(lambda v: 0 if v > 190 else 255).convert("RGB")
    if mode == "bin":
        g = ImageOps.autocontrast(ImageOps.invert(img.convert("L")), cutoff=2)
        return g.point(lambda v: 255 if v > 150 else 0).convert("RGB")
    return img

def analyse(img):
    runs = []
    for mode, inv, scale in (("inv", True, 2), ("raw", False, 2), ("bin", False, 3), ("wht", False, 2)):
        lines = to_lines(tesseract_words(preprocess(img, mode), inv, scale=scale))
        runs.append((mode, lines, known_hits(lines)))
    allhits = [h for _, _, hs in runs for h in hs]
    best = None
    for mode, lines, hs in runs:
        b = benefits(lines, allhits)
        score = (len(hs), len(b), sum(l["conf"] for l in lines) / max(1, len(lines)))
        log(f"  OCR({mode}): 줄 {len(lines)}, 사전 {len(hs)}, 혜택 {b}")
        if best is None or score > best[0]:
            best = (score, lines, b)
    _, lines, b = best
    box = None
    for _, ls, _ in runs:  # 자르기 상자는 예전처럼 반전 결과 먼저(없으면 다음 전처리)
        box = crop_box(ls, *img.size)
        if box: break
    return lines, b, box

def load_image(src):
    from PIL import Image
    if re.match(r"https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    else:
        data = open(src, "rb").read()
    return Image.open(io.BytesIO(data)).convert("RGB")

def save_crop(img, box, path):
    c = img.crop(box)
    c.save(path, optimize=True)
    return c.size

def main():
    args = sys.argv[1:]
    if "--image" in args:  # 로컬 확인용
        img = load_image(args[args.index("--image") + 1])
        lines, b, box = analyse(img)
        for l in lines: log(int(l["y"]), l["t"])
        log("혜택:", b, "자르기:", box)
        if box and "--crop" in args:
            log("저장:", save_crop(img, box, args[args.index("--crop") + 1]))
        return 0
    feed = json.load(open(FEED, encoding="utf-8"))
    s = feed.get("sunday") or {}
    changed = False
    if s.get("image"):
        o = s.get("ocr") or {}
        tries = (o.get("tries", 0) if o.get("image") == s["image"] else 0) + 1
        o = {"image": s["image"], "ok": False, "at": datetime.datetime.now(KST).replace(microsecond=0).isoformat(), "tries": tries}
        try:
            img = load_image(s["image"])
            lines, b, box = analyse(img)
            o["lines"] = [l["t"] for l in lines][:40]
            if s.get("benefitSrc") != "text":  # 본문 HTML 글자(text)가 있으면 그게 우선 — OCR 로 덮지 않음
                if b:
                    s["benefit"] = " · ".join(b); s["benefitSrc"] = "ocr"
                elif s.get("benefitSrc") in ("ocr", None, ""):  # 못 믿을 글자 → 비움(사이트가 제목 표시)
                    s.pop("benefit", None); s.pop("benefitSrc", None); o["lowConf"] = True
            o["ok"] = bool(b) or bool(o.get("lowConf"))
            if box:
                size = save_crop(img, box, CROP)
                s["crop"] = f"sunday.png?v={s.get('id', '')}"; o["box"] = list(box); o["cropSize"] = list(size)
            else:
                s.pop("crop", None)
            log("썬데이 OCR:", s.get("benefit"), "| 자르기:", box)
        except Exception as e:
            o["error"] = f"{type(e).__name__}: {e}"[:300]
            log(f"::warning::썬데이 OCR 실패: {o['error']}")
        s["ocr"] = o; feed["sunday"] = s; changed = True
        feed["updatedAt"] = datetime.datetime.now(KST).replace(microsecond=0).isoformat()
        with open(FEED, "w", encoding="utf-8") as f:
            json.dump(feed, f, ensure_ascii=False, indent=1); f.write("\n")
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        with open(go, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
