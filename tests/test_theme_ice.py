# b167: Ice Blue Whisper 테마 + 금색 총액 + 토글 버튼 하늘색
import os, sys, subprocess, time
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 8875
src = open(os.path.join(ROOT, "tests", "test_tracker81.py")).read(); NS = {}; exec(src[src.index("B=lambda"):src.index("\ntry:")], NS)
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        for w in (1400, 390):
            pg = b.new_page(viewport={"width": w, "height": 900}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.route("https://open.api.nexon.com/**", lambda r: r.abort())
            pg.goto(f"http://127.0.0.1:{PORT}/index.html"); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}", NS["ST"]); pg.reload(); pg.evaluate(NS["SETUP"]); pg.wait_for_timeout(1800)
            r = pg.evaluate("""(()=>{const cs=e=>getComputedStyle(e);const card=document.querySelector('.card'),seg=document.querySelector('.seg button.on'),off=document.querySelector('.seg button:not(.on)'),rp=document.querySelector('.rp-total .tir-g .tl');
              return [cs(document.documentElement).getPropertyValue('--n1').trim(),cs(card).borderTopColor,cs(seg).backgroundImage,cs(seg).color,cs(off).backgroundColor,rp?cs(rp).fill:'',cs(document.querySelector('.rp-total .tir-g')).filter]})()""")
            check(f"{w}: 테마 변수 #9fdcff", r[0] == "#9fdcff", r)
            check(f"{w}: 카드 테두리 하늘색 계열", ("159, 220, 255" in r[1] or "0.623529 0.862745 1" in r[1]), r[1])
            check(f"{w}: 주간/월간 토글 선택 = 하늘색(주황 아님)", "159, 220, 255" in r[2] and "255, 138" not in r[2] and r[3] == "rgb(234, 247, 255)", r[2:4])
            check(f"{w}: 비선택 토글 주황 배경 아님", "255, 1" not in r[4], r[4])
            check(f"{w}: 이번 주 수익 합계 = 금색(#tirY)+금색 글로우", "tirY" in r[5] and "255, 170, 40" in r[6], r[5:])
            pg.evaluate("tab='total';syncTabs();render()"); pg.wait_for_timeout(1700)
            g = pg.evaluate("(()=>{const t=document.querySelector('.stats .stat .tgoldv .tir-g, .stats .tgoldv .tir-g');return t?[getComputedStyle(t.querySelector('.tl')).fill,getComputedStyle(t).filter]:null})()")
            check(f"{w}: 누적 수입 총 수익 = 금색", g and "tirY" in g[0] and "255, 170, 40" in g[1], g)
            pg.evaluate("openImport()"); pg.wait_for_timeout(500)
            m = pg.evaluate("getComputedStyle(document.querySelector('#importModal .modal')).borderTopColor")
            check(f"{w}: 모달 테두리 하늘색 계열", ("159, 220, 255" in m or "0.623529 0.862745 1" in m), m)
            check(f"{w}: JS 오류 없음", not errs, errs); pg.close()
        b.close()
finally:
    srv.terminate()
print("FAILS:", fails); sys.exit(1 if fails else 0)
