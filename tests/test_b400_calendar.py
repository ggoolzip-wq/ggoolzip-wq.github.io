import ast,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
m=ast.parse(Path('tests/test_b398_detail.py').read_text());fixture=next(ast.literal_eval(n.value) for n in m.body if isinstance(n,ast.Assign) and any(getattr(t,'id','')=='FIXTURE' for t in n.targets));port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page(viewport={'width':1440,'height':2000});pg.goto('https://bossmaple.pages.dev/' if '--live' in sys.argv else f'http://127.0.0.1:{port}');pg.evaluate(fixture);pg.evaluate("()=>{__rows.push({...__rows[2],id:'c2',name:'새벽마법사',n:2,m:1800000000});renderCal();}");pg.wait_for_timeout(200)
  assert pg.locator('.cald-clean').evaluate('(e)=>e.children[0].classList.contains("cald-head")&&e.children[1].classList.contains("cald-notes")&&e.children[2].classList.contains("cald-metrics")');assert pg.locator('[data-calmemo]').count()==1 and pg.locator('[data-calboss]').count()==1
  assert pg.locator('.cald-row').count()==3 and pg.locator('.cald-row time').count()==0
  row=pg.locator('.cald-row').filter(has_text='마력이 깃든 안대');assert row.locator('.cald-qty').inner_text()=='×3' and row.locator('.cald-money').inner_text()=='27억';assert pg.locator('.cald-total b').inner_text()=='33억 메소'
  pg.locator('#calDet').screenshot(path='/workspace/maple-boss-tracker/b400_calendar_memo_top.png');pg.set_viewport_size({'width':390,'height':1000});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1');print('PASS b400: header→notes/schedule→metrics; no time; same item ×3/27억; total33억; mobile no overflow');b.close()
finally:srv.terminate()
