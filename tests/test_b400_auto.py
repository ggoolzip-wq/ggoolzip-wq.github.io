import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);before='--before' in sys.argv
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page(viewport={'width':1440,'height':1800});pg.goto('https://bossmaple.pages.dev/' if before or '--live' in sys.argv else f'http://127.0.0.1:{port}');pg.evaluate("()=>{tab='auto';renderAuto();}");pg.wait_for_timeout(200);pg.locator('#arPanel').screenshot(path='/workspace/maple-boss-tracker/b400_auto_before.png' if before else '/workspace/maple-boss-tracker/b400_auto_after.png')
  if not before:
   assert pg.locator('#arGuideInline li').count()==3 and '어센트로 보상 까기' in pg.locator('#arGuideInline').inner_text();assert pg.locator('.ar-example').count()==1;pg.locator('.ar-example summary').click();assert pg.locator('.ar-gimg img').count()==2;pg.locator('.ar-example summary').click()
   assert pg.locator('.ar-maple-connect').inner_text()=='메이플 연결';assert pg.locator('.ar-maple-connect').evaluate('(e)=>e.classList.contains("neonBtn")')
   pg.set_viewport_size({'width':390,'height':1200});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1');print('PASS b400 auto: 3 aligned guide bullets, expandable examples, bottom neon connect, 390px no overflow')
  b.close()
finally:srv.terminate()
