#!/usr/bin/env python3
"""썬데이 메이플 이미지 OCR → '이번 주 혜택' 글자 + 본문(이벤트 기간~혜택 상자) 잘라낸 sunday.png

update-feed.yml 에서 새 썬데이 글이 있을 때만(update_feed.py 가 sunday_ocr=true 출력) 실행 — 글 하나당 한 번.
필요: tesseract-ocr + tesseract-ocr-kor (apt), Pillow (pip) — 이 단계에서만 설치. update_feed.py 는 그대로 표준 라이브러리만.
결과(feed.json 의 sunday): benefit(' · ' 로 이은 혜택, 최대 3개), benefitSrc='ocr', crop='sunday.png?v=<id>', ocr={image, ok, at, tries, lines}
실패하면 crop 없음(사이트는 원본 이미지), benefit 은 그대로(없으면 사이트가 제목 표시). 3번 실패하면 그 글은 더 시도 안 함.
로컬 확인: python3 scripts/sunday_ocr.py --image 파일또는URL [--crop out.png]
"""
import csv, datetime, io, json, os, re, subprocess, sys, tempfile, urllib.request

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
    t = re.sub(r"(\d)\s*%", r"\1%", t)
    t = re.sub(r"(\d)\s+(성|배|회|레벨)", r"\1\2", t)
    t = re.sub(r"\s*([,.!?])", r"\1", t)
    t = re.sub(r"[|'\"`~_=<>{}\[\]]+$", "", t).strip()
    return t

def benefits(lines):
    """혜택 줄 찾기: 키워드가 있고 값(%, 할인, 감소, N배 …)이 있는 줄. 값이 다음 줄에 있으면 합침. 안내(단, …않습니다) 줄은 뺌"""
    out = []; i = 0
    L = [l for l in lines if l["t"]]
    while i < len(L):
        t = L[i]["t"]
        if NOTE_RE.search(t) or not KEY_RE.search(t) or len(t) > 40 or re.search(r"[A-Za-z]{2,}", t):
            i += 1; continue
        if re.fullmatch(r"\s*(?:스페셜\s*)?미라클\s*타임\s*!?", t):
            out.append("미라클 타임"); i += 1; continue
        if not VAL_RE.search(t) and i + 1 < len(L) and not NOTE_RE.search(L[i + 1]["t"]) and L[i + 1]["y"] - L[i]["b"] < 40 and VAL_RE.search(L[i + 1]["t"]):
            t = t + " " + L[i + 1]["t"]; i += 1
        i += 1
        if VAL_RE.search(t) and re.search(r"\d|할인|감소|증가|무료", t) and not re.search(r"[=+]", t) and len(t) <= 44 and t.count("%") <= 1:
            out.append(t)
    res = []
    for t in out:
        t = shorten(t)
        if t and not any(t == r or t in r for r in res):
            res.append(t)
    return res[:3]

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

def analyse(img):
    best = None
    for inv in (True, False):
        lines = to_lines(tesseract_words(img, inv))
        b = benefits(lines)
        score = (len(b), sum(l["conf"] for l in lines) / max(1, len(lines)))
        log(f"  OCR({'반전' if inv else '원본'}): 줄 {len(lines)}, 혜택 {b}")
        if best is None or score > best[0]:
            best = (score, lines, b)
    _, lines, b = best
    return lines, b, crop_box(lines, *img.size)

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
            if b:
                if s.get("benefitSrc") != "text":
                    s["benefit"] = " · ".join(b); s["benefitSrc"] = "ocr"
                o["ok"] = True
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
