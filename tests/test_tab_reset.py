# b166: 새로고침하면 저장된 탭·해시와 상관없이 항상 '이번 주 보스'
import os, sys, subprocess, time
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 8874
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), args=["--no-sandbox"]); pg = b.new_page()
        pg.route("https://open.api.nexon.com/**", lambda r: r.abort())
        pg.goto(f"http://127.0.0.1:{PORT}/index.html"); pg.wait_for_timeout(800)
        for t in ["total", "loot", "guild", "live"]:
            pg.click(f"[data-tab={t}]"); pg.wait_for_timeout(300)
            check(f"{t} 탭 클릭됨", pg.evaluate("tab") == t)
            pg.reload(); pg.wait_for_timeout(700)
            check(f"{t} 에서 새로고침 → 이번 주 보스", pg.evaluate("[tab,document.querySelector('nav.tabs button.on').dataset.tab]") == ["boss", "boss"])
        pg.goto(f"http://127.0.0.1:{PORT}/index.html#loot"); pg.evaluate("localStorage.setItem('mapleBossTracker.tab','loot')"); pg.reload(); pg.wait_for_timeout(700)
        check("해시·저장값 있어도 이번 주 보스", pg.evaluate("tab") == "boss")
        b.close()
finally:
    srv.terminate()
print("FAILS:", fails); sys.exit(1 if fails else 0)
