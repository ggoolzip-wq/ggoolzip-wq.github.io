"""Whole-calendar alignment/UI regression; --before captures the old layout."""
import sys,subprocess,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];PORT=_tutil.free_port();before='--before' in sys.argv
mod=ast.parse((ROOT/'tests/test_b398_detail.py').read_text());FIXTURE=next(ast.literal_eval(n.value) for n in mod.body if isinstance(n,ast.Assign) and any(getattr(t,'id','')=='FIXTURE' for t in n.targets))
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=str(ROOT),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page(viewport={'width':1440,'height':2400});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto('https://bossmaple.pages.dev/' if '--live' in sys.argv else f'http://127.0.0.1:{PORT}/');pg.wait_for_function('typeof renderCal==="function"');pg.evaluate(FIXTURE)
  pg.evaluate('''()=>{const base=__rows.slice();for(const day of [1,2,4,12,16,20,26])for(const r of base){const d=calMon+'-'+pad(day);__rows.push({...r,day:d,m:r.m*(day%3+1),ts:r.ts?Date.parse(d+'T20:15:00+09:00'):0});}for(const day of [1,8,12,16,26]){const d=calMon+'-'+pad(day);S.calNotes[d]={m:{a:{t:'메모 확인',at:Date.now()}},b:{b:{cid:'c1',n:'단풍용사',boss:'lucid',slot:'lucid',d:'hard',p:3,h:21,mi:0,at:Date.now()}}};}renderCal();}''');pg.wait_for_timeout(250)
  pg.locator('.calcard').screenshot(path='/workspace/maple-boss-tracker/b399_before.png' if before else '/workspace/maple-boss-tracker/b399_after.png')
  if not before:
   assert pg.locator('.cald-section').count()==1 and pg.locator('.cald-section h4').inner_text().startswith('아이템 드롭')
   assert pg.locator('.cald-metrics').inner_text().find('3억')>=0
   for width in [1440,390]:
    pg.set_viewport_size({'width':width,'height':1200})
    cells=pg.locator('.calgrid .calc').evaluate_all('(L)=>L.map(e=>({w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}))')
    assert max(x['w'] for x in cells)-min(x['w'] for x in cells)<1 and max(x['h'] for x in cells)-min(x['h'] for x in cells)<1,cells
    assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    assert pg.locator('.calgrid .calc:not(.emp)').count() in [28,29,30,31]
   pg.set_viewport_size({'width':1440,'height':2400});pg.click('[data-calmonth]');assert pg.locator('.calmonth-clean').count()==1 and pg.locator('.calchip').count()>=8
   pg.set_viewport_size({'width':390,'height':1200});pg.wait_for_timeout(200);assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1');pg.set_viewport_size({'width':1440,'height':2400})
   pg.locator('[data-calmd]').first.click();assert pg.locator('#calML').count()==1
   pg.locator('[data-calgo]').click();assert pg.locator('.cald-clean').count()==1
   pg.click('[data-calclose]');pg.click('[data-calym]');assert pg.locator('#calYP').count()==1
   pg.click('[data-calym2="12"]');assert pg.evaluate('calMon.endsWith("-12")')
   pg.click('[data-calmv="0"]');assert pg.evaluate('calSel===dayId(Date.now())')
   assert not errs,errs
   print('ALL PASS b399: equal cell width/height desktop+390px, no overflow, crystal sum only, unchanged totals, month chips/day navigation/year-month picker/today/close preserved, JS errors=0')
  b.close()
finally:srv.terminate()
