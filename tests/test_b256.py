# test_b256: 썬데이 OCR — 알려진 문장 사전+퍼지 매칭, '+N%' 허용, 수식 상자·이름표 합치지 않음, 못 믿을 글자는 비움(제목 표시), 화면 최대 4줄
# 회귀: 1405(2026-10-25) OCR 줄 → 4개 혜택. tesseract 가 있으면 실제 이미지(tests/fixtures/sunday_1405.jpg)도 확인. MBT_SHOTDIR=폴더 → 카드 사진
import os, sys, json, shutil, subprocess, tempfile, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sunday_ocr as O
O.log = lambda *a: None
fails = []; errs = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d)[:300] if d != "" else ""))
    if not c: fails.append(n)
W4 = ["메인 스탯의 강화 확률 20% 증가", "룬 기본 지속시간 50% 증가", "룬 경험치 버프 +100%", "콤보킬 경험치 획득량 +300%"]
raw = json.load(open(os.path.join(ROOT, "tests", "fixtures", "sunday_1405_lines.json"), encoding="utf-8"))
L1405 = [{"y": i * 40, "b": i * 40 + 30, "t": O.clean(t), "conf": 90} for i, t in enumerate(raw)]
b = O.benefits(L1405)
check("1405 OCR lines → 4 real benefits (no garbage, no badge)", b == W4, b)
check("clean(): '= 기본 지속…' → '룬 기본 지속…', stray 』 removed", O.clean("= 기본 지속 시간 50% 증가") == "룬 기본 지속 시간 50% 증가" and "』" not in O.clean("기본 』 룬경험"))
L = lambda y, t: {"y": y, "b": y + 30, "t": O.clean(t), "conf": 90}
check("'+N%' line kept (fix2)", O.benefits([L(0, "콤보킬 경험치 획득량 +300%")]) == ["콤보킬 경험치 획득량 +300%"])
check("label line not merged with formula box (fix3)", O.benefits([L(0, "기본 룬"), L(40, "기본 경험치 100% 룬 버프 100% 혜택 100% 300%")]) == [])
check("fuzzy dictionary: OCR typos → canonical", O.benefits([L(0, "트레저 헌터 경헙치 3배"), L(100, "주문의 흔적 강화 비옹 50% 할인")]) == ["트레져 헌터 경험치 3배", "주문의 흔적 강화 비용 50% 할인"])
check("two-line heading merged (21성 … / 파괴 확률 30% 감소)", O.benefits([L(0, "21성 이하에서 스타포스 강화 시"), L(40, "파괴 확률 30% 감소")]) == ["21성 이하 스타포스 파괴 확률 30% 감소"])
check("misread number fixed by known value (+700% → +100%)", O.benefits([L(0, "룬 경험치 버프 효과 + 700%")]) == ["룬 경험치 버프 +100%"])
check("garbage only → [] (site shows title)", O.benefits([L(0, "기본 룬 기본 』 룬경혐데 메이플 개 300%"), L(50, "등른이승금될 22 메디 셔널 잠재 능력 2배! 등른이승금될 22")]) == [])
check("note lines never become benefits", O.benefits([L(0, "ㆍ 기본 획득량에 썬데이 메이플 혜택 300% 를주가로!"), L(40, "솔에르다획득량 증가 혜택을 함께 적용 받을 수 있습니다")]) == [])
hits = [(0, "룬 경험치 버프 +100%", .9, "룬 경험치 버프 +{n}%")]
check("multi-pass vote merges hits", O.benefits([L(0, "콤보킬 경험치 획득량 +300%")], hits) == ["룬 경험치 버프 +100%", "콤보킬 경험치 획득량 +300%"])
check("max 4", len(O.benefits([L(i * 100, t) for i, t in enumerate(["미라클 타임", "트레져 헌터 경험치 3배", "주문의 흔적 강화 비용 50% 할인", "흔적 복구 비용 20% 할인", "스타포스 강화 비용 30% 할인"])])) == 4)
# feed.json: 못 믿을 글자 → 예전 OCR 혜택(쓰레기) 지우고 제목 표시 / 본문 HTML 글자(text)는 OCR 이 덮지 않음
tmp = tempfile.mkdtemp(); fp = os.path.join(tmp, "feed.json"); O.FEED, O.CROP = fp, os.path.join(tmp, "s.png")
class FakeImg:
    size = (876, 1395)
    def crop(self, box): return self
    def save(self, path, **k): open(path, "wb").write(b"PNG")
O.load_image = lambda src: FakeImg(); os.environ.pop("GITHUB_OUTPUT", None); sys.argv = ["x"]
an = O.analyse
O.analyse = lambda im: ([L(0, "기본 』 룬경혐데")], [], None)
json.dump({"sunday": {"id": 1, "title": "썬데이 메이플", "image": "https://x/a.png", "benefit": "기본 룬 기본 』 룬경혐데 메이플 개 300%", "benefitSrc": "ocr"}}, open(fp, "w")); O.main()
sd = json.load(open(fp, encoding="utf-8"))["sunday"]
check("low confidence → benefit removed (title shown), ok (no retries)", "benefit" not in sd and sd["ocr"].get("lowConf") and sd["ocr"]["ok"], sd)
O.analyse = lambda im: (L1405, O.benefits(L1405), None)
json.dump({"sunday": {"id": 2, "title": "썬데이 메이플", "image": "https://x/b.png", "benefit": "경험치 3배", "benefitSrc": "text"}}, open(fp, "w")); O.main()
sd = json.load(open(fp, encoding="utf-8"))["sunday"]
check("HTML body text wins over OCR", sd["benefit"] == "경험치 3배" and sd["benefitSrc"] == "text", sd)
json.dump({"sunday": {"id": 1405, "title": "썬데이 메이플", "image": "https://x/c.png"}}, open(fp, "w")); O.main()
sd = json.load(open(fp, encoding="utf-8"))["sunday"]
check("feed: 1405 benefit = 4 joined", sd["benefit"] == " · ".join(W4) and sd["benefitSrc"] == "ocr", sd.get("benefit"))
O.analyse = an
if shutil.which("tesseract") and importlib.util.find_spec("PIL"):
    import importlib; importlib.reload(O); O.log = lambda *a: None
    _, rb, box = O.analyse(O.load_image(os.path.join(ROOT, "tests", "fixtures", "sunday_1405.jpg")))
    check("real OCR 1405 image → 4 benefits", rb == W4, rb)
else:
    print("SKIP real OCR (tesseract/Pillow 없음)")
# 화면: 4줄 표시, 카드 안 넘침, 3줄일 때와 페이지 높이 같음(스크롤 안 늘어남)
from playwright.sync_api import sync_playwright
PORT = _tutil.free_port()
srv = _tutil.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
SUN = {"id": 1405, "title": "썬데이 메이플", "url": "https://maplestory.nexon.com/News/Event/1405", "image": "https://lwi.nexon.com/x.png", "start": "2099-10-25T00:00:00+09:00",
       "end": "2099-10-25T23:59:00+09:00", "date": "2099-10-23T10:00:00+09:00", "benefit": " · ".join(W4), "benefitSrc": "ocr"}
M = """()=>{const c=document.querySelector('#sunCard'), b=c&&c.querySelector('.sunbody'); const lis=[...(c?c.querySelectorAll('.sunben li'):[])];
  return {n:lis.length, t:lis.map(l=>l.textContent), over:b?b.scrollHeight-b.clientHeight:-1, cut:lis.filter(l=>l.scrollWidth>l.clientWidth+1).length,
    cb:c?Math.round(c.getBoundingClientRect().bottom):0, vh:innerHeight, doc:document.scrollingElement.scrollHeight}}"""
try:
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
        for vw, vh in ((1600, 1000), (1366, 768), (1920, 1080)):
            pg = br.new_page(viewport={"width": vw, "height": vh}, locale="ko-KR"); pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.route("**/lwi.nexon.com/**", lambda r: r.fulfill(path=os.path.join(ROOT, "tests", "fixtures", "sunday_1405.jpg"), content_type="image/jpeg"))
            pg.goto(f"http://127.0.0.1:{PORT}/index.html"); pg.wait_for_timeout(800)
            r = {}
            for k, ben in (("3", " · ".join(W4[:3])), ("4", " · ".join(W4))):
                pg.evaluate("s=>{feed.srv=null; feed.data=Object.assign({},feed.data||{items:[]},{sunday:s}); renderFeed&&renderFeed(); renderSun(); window.dispatchEvent(new Event('resize'))}", dict(SUN, benefit=ben))
                pg.wait_for_timeout(500); r[k] = pg.evaluate(M)
            check(f"{vw}x{vh}: 4 lines shown", r["4"]["n"] == 4 and r["4"]["t"] == W4, r["4"])
            check(f"{vw}x{vh}: card body not overflowing", r["4"]["over"] <= 1, r["4"])
            check(f"{vw}x{vh}: page height same as with 3 lines (no extra scroll)", r["4"]["doc"] == r["3"]["doc"], (r["3"]["doc"], r["4"]["doc"]))
            sd_ = os.environ.get("MBT_SHOTDIR")
            if sd_ and vw == 1600: pg.locator("#sunCard").screenshot(path=os.path.join(sd_, "b256_sun_1600.png"))
            pg.close()
        br.close()
finally:
    srv.terminate()
check("no page errors", not errs, errs)
print("FAILS", fails); sys.exit(1 if fails else 0)
