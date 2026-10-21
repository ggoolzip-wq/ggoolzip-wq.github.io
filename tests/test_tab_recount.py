import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8879=_tutil.free_port()
# b173: 탭 갔다 오면 디지털 숫자·그래프 디지털 숫자 다시 카운팅, 매분 재렌더는 안 튐
import os, sys, subprocess, time
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = _P8879
src = open(os.path.join(ROOT, "tests", "test_tracker81.py")).read(); NS = {}; exec(src[src.index("B=lambda"):src.index("\ntry:")], NS)
SHOT = os.environ.get("SHOT"); fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
srv = _tutil.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ST = "[[...document.querySelectorAll('#view .tir[data-tv]')].map(e=>e.dataset.tanim||''),[...document.querySelectorAll('#view g.tsv[data-st]')].map(g=>g.dataset.tanim||'')]"
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1400, "height": 2400}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("https://open.api.nexon.com/**", lambda r: r.abort())
        pg.goto(f"http://127.0.0.1:{PORT}/index.html"); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}", NS["ST"]); pg.reload(); pg.wait_for_timeout(400)
        pg.evaluate(NS["SETUP"]); pg.click("#tabs button[data-tab=total]"); pg.wait_for_timeout(2500)
        a = pg.evaluate(ST); check("처음 진입: 숫자·그래프 카운팅 끝", a[0] and a[1] and all(x == "done" for x in a[1]) and "done" in a[0], a)
        pg.evaluate("render()"); pg.wait_for_timeout(1500); a = pg.evaluate(ST)
        check("같은 탭 재렌더(매분 갱신): 다시 안 돎", all(x == "" for x in a[0]) and all(x == "" for x in a[1]), a)
        pg.click("#tabs button[data-tab=boss]"); pg.wait_for_timeout(600); pg.click("#tabs button[data-tab=total]"); pg.wait_for_timeout(450)
        a = pg.evaluate(ST); check("탭 복귀 직후: 숫자·그래프 카운팅 중", "run" in a[0] and "run" in a[1], a)
        if SHOT: pg.screenshot(path=SHOT + "_mid.png", full_page=True)
        pg.wait_for_timeout(1500); a = pg.evaluate(ST); check("복귀 후 끝까지 → 최종값", all(x == "done" for x in a[1]) and "run" not in a[0], a)
        fin = pg.evaluate("[...document.querySelectorAll('#view g.tsv[data-st]')].every(g=>{const r=tirSvg(g.dataset.st,...g.dataset.sa.split(',').map(Number),'',1);const t=document.createElementNS('http://www.w3.org/2000/svg','g');t.innerHTML=r.inner;return g.innerHTML===t.innerHTML&&g.getAttribute('transform')===r.tr})")
        check("그래프 숫자 최종 글자 그대로", fin)
        if SHOT: pg.screenshot(path=SHOT + "_end.png", full_page=True)
        check("JS 오류 없음", not errs, errs); b.close()
finally:
    srv.terminate()
print("FAILS:", fails); sys.exit(1 if fails else 0)
