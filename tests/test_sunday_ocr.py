# 썬데이 OCR (scripts/sunday_ocr.py) — 혜택 줄 추출·자르기 상자·feed.json 갱신. tesseract+Pillow 가 있으면 실제 이미지(1397)도 확인
import os, sys, json, shutil, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sunday_ocr as O, update_feed as F
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
# 1) 글자마다 끊긴 한글 붙이기
W = lambda ts: [{"t": t, "x": i * 10, "w": 8, "y": 0, "h": 10} for i, t in enumerate(ts)]
check("join split Hangul syllables", O.join_words(W("어 빌 리 티 재설정 명 성 치 비용 50% 할인".split())) == "어빌리티 재설정 명성치 비용 50% 할인")
# 2) 1397 실제 OCR 줄(반전 결과) → 혜택 2줄, 안내(단, …) 제외, 다음 줄 값 합치기
L = lambda y, t: {"y": y, "b": y + 30, "t": O.clean(t), "conf": 90}
lines1397 = [L(29, "4 = od."), L(520, "： 2026년 10월 11일 (일) 오전 0시 ~ 오후 11시 59분"), L(710, "어빌리티 재설정 명성치 비용 50% 할인"),
             L(750, "ㆍ 단, 어빌리티 고급 재설정에 사용되는 메소에는"), L(775, "할인 효과가 적용되지 않습니다."), L(904, "2123 이하 에서 스타포스 강화 시"),
             L(949, "파괴 확률 30% 감소"), L(986, "ㆍ 단, 슈페리얼 장비는 파괴 확률 30% 감소 효과가"), L(1025, "적용되지 않습니다."), L(1252, "+ 게임정보 '어빌리티' 바로가기 >")]
b = O.benefits(lines1397)
check("1397 lines → ability + starforce benefits", b == ["어빌리티 재설정 명성치 비용 50% 할인", "21성 이하 스타포스 파괴 확률 30% 감소"], b)
box = O.crop_box(lines1397, 876, 1395)
check("crop box = period line .. last note (before '바로가기')", box and box[1] < 520 and 1055 <= box[3] < 1252 and box[0] == 0 and box[2] == 876, box)
check("미라클 타임 alone counts; sums/notes skipped", O.benefits([L(100, "미라클 타임"), L(200, "몬스터 파크 클리어 경험치 추가 250%"), L(240, "경험치 100% + 혜택 50% = 400%"), L(300, "ㆍ 단, 미라클 타임은 …")]) == ["미라클 타임", "몬스터 파크 클리어 경험치 추가 250%"])
check("no period/benefit → no crop", O.crop_box([L(10, "썬데이 메이플")], 876, 1000) is None)
# 3) update_feed: OCR 필요 판단 (글 하나당 한 번, 실패는 3번까지)
img = "https://lwi.nexon.com/x.png"
check("new image → OCR needed", F.sunday_needs_ocr({"image": img}))
check("done once → not again", not F.sunday_needs_ocr({"image": img, "ocr": {"image": img, "ok": True, "tries": 1}}))
check("failed < 3 → retry", F.sunday_needs_ocr({"image": img, "ocr": {"image": img, "ok": False, "tries": 2}}))
check("failed 3× → give up", not F.sunday_needs_ocr({"image": img, "ocr": {"image": img, "ok": False, "tries": 3}}))
check("new post (other image) → OCR again", F.sunday_needs_ocr({"image": img + "2", "ocr": {"image": img, "ok": True}}))
# 4) feed.json 갱신 (OCR 은 모의) — 혜택·crop·ocr 기록, 실패 시 crop 없음
tmp = tempfile.mkdtemp(); fp = os.path.join(tmp, "feed.json"); cp = os.path.join(tmp, "sunday.png")
O.FEED, O.CROP = fp, cp
class FakeImg:
    size = (876, 1395)
    def crop(self, box): return self
    def save(self, path, **k): open(path, "wb").write(b"PNG")
O.load_image = lambda src: FakeImg()
O.analyse = lambda im: (lines1397, O.benefits(lines1397), O.crop_box(lines1397, 876, 1395))
json.dump({"sunday": {"id": 1397, "title": "썬데이 메이플", "image": img}}, open(fp, "w"))
os.environ.pop("GITHUB_OUTPUT", None); sys.argv = ["x"]; O.main()
sd = json.load(open(fp, encoding="utf-8"))["sunday"]
check("feed: benefit from OCR, crop path, ocr cache", sd["benefit"] == "어빌리티 재설정 명성치 비용 50% 할인 · 21성 이하 스타포스 파괴 확률 30% 감소" and sd["benefitSrc"] == "ocr"
      and sd["crop"] == "sunday.png?v=1397" and sd["ocr"]["image"] == img and sd["ocr"]["ok"] and os.path.exists(cp) and not F.sunday_needs_ocr(sd), sd)
def boom(src): raise OSError("download failed")
O.load_image = boom
json.dump({"sunday": {"id": 1398, "title": "썬데이 메이플", "image": img + "2"}}, open(fp, "w")); O.main()
sd = json.load(open(fp, encoding="utf-8"))["sunday"]
check("OCR failure → recorded (tries 1), no crop, title fallback stays", sd["ocr"]["ok"] is False and sd["ocr"]["tries"] == 1 and "crop" not in sd and "benefit" not in sd and "error" in sd["ocr"], sd)
# 5) 실제 OCR (tesseract + Pillow 가 있을 때만): 이번 주 1397 이미지
import importlib, importlib.util
if shutil.which("tesseract") and importlib.util.find_spec("PIL"):
    importlib.reload(O)
    from PIL import Image
    im = O.load_image(os.path.join(ROOT, "tests", "fixtures", "sunday_1397.jpg"))
    lines, b, box = O.analyse(im)
    check("real OCR 1397: ability + starforce lines", any("어빌리티" in x and "50%" in x for x in b) and any("스타포스" in x and "30%" in x and "감소" in x for x in b), b)
    check("real OCR 1397: crop covers period + both boxes", box and 400 <= box[1] <= 520 and 1050 <= box[3] <= 1200, box)
    out = os.path.join(ROOT, "tests", "out"); os.makedirs(out, exist_ok=True); O.save_crop(im, box, os.path.join(out, "sunday_crop_1397.png"))
else:
    print("SKIP real OCR (tesseract/Pillow 없음)")
wf = open(os.path.join(ROOT, ".github", "workflows", "update-feed.yml"), encoding="utf-8").read()
check("workflow: OCR step only when sunday_ocr, installs tesseract-ocr-kor + pillow, commits sunday.png",
      "if: steps.feed.outputs.sunday_ocr == 'true'" in wf and "tesseract-ocr-kor" in wf and "pip install -q pillow" in wf and "git add sunday.png" in wf and "steps.ocr.outputs.changed == 'true'" in wf)
print("FAILS", fails); sys.exit(1 if fails else 0)
