# test_b257: 소식(공지) 카드 = 데스크톱 모든 높이에서 쪽당 5줄(탭 사료감지/패치내역/테섭/마빡도로시) · 썬데이 카드 넘침 없음 · 사이드바가 페이지를 늘리지 않음
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []; errs = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d)[:300] if d != "" else ""))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
PORT = _tutil.free_port()
srv = _tutil.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
M = """()=>{const c=feedCard, fb=c.querySelector('.fbody'), s=sunCard, a=c.parentElement;
  return {per:feed.per, rows:fb.querySelectorAll('a[data-fid]').length, n:feedItems(feed.tab).length, fbo:fb.scrollHeight-fb.clientHeight, co:c.scrollHeight-c.clientHeight,
    so:s.style.display==='none'?0:s.scrollHeight-s.clientHeight, sd:s.style.display, ab:Math.round(a.getBoundingClientRect().bottom+scrollY), doc:document.scrollingElement.scrollHeight, flow:a.classList.contains('side-flow')}}"""
try:
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
        for vw, vh in [(1600, 1000), (1366, 768), (1920, 1080), (1440, 900), (1280, 720)]:
            pg = br.new_page(viewport={"width": vw, "height": vh}); pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{PORT}/", wait_until="networkidle"); pg.wait_for_timeout(1500)
            r = pg.evaluate(M)
            check(f"{vw}x{vh}: 5 rows per page", r["per"] >= 5 and r["rows"] == min(r["per"], r["n"]), r)
            check(f"{vw}x{vh}: feed card not overflowing", r["fbo"] <= 1 and r["co"] <= 1, r)
            check(f"{vw}x{vh}: sunday card not overflowing", r["so"] <= 1, r)
            check(f"{vw}x{vh}: sidebar does not lengthen page", r["flow"] or r["ab"] <= r["doc"], r)
            pg.close()
        br.close()
finally:
    srv.terminate()
check("no page errors", not errs, errs)
print("FAILS", fails); sys.exit(1 if fails else 0)
