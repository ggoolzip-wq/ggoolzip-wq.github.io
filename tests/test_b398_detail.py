"""Essential day-detail visual/data regression; --before saves pre-change reference."""
import sys,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];PORT=_tutil.free_port();before='--before' in sys.argv
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=str(ROOT),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
FIXTURE="""()=>{S.settings.accounts=[{id:'fixture'}];S.characters=[{id:'c1',name:'단풍용사',world:'스카니아',bosses:{},weekly:{},monthly:{},auto:{},drops:{}},{id:'c2',name:'새벽마법사',world:'스카니아',bosses:{},weekly:{},monthly:{},auto:{},drops:{}}];
const day=dayId(),ts=Date.parse(day+'T20:15:00+09:00');window.__day=day;window.__rows=[
 {day,id:'c1',name:'단풍용사',m:100000000,k:null,n:0,bs:'루시드(하드)',ts,ap:false},
 {day,id:'c2',name:'새벽마법사',m:200000000,k:null,n:0,bs:'듄켈(하드)',ts:ts+60000,ap:false},
 {day,id:'c1',name:'단풍용사',m:900000000,k:'eye',n:1,bs:'루시드',ts,ap:false},
 {day,id:'c2',name:'새벽마법사',m:300000000,k:'belt',n:2,bs:'듄켈',ts:ts+60000,ap:false},
 {day,id:'c2',name:'새벽마법사',m:0,k:'r_white',n:1,bs:'카링',ts:0,ap:true}];
S.calNotes={[day]:{m:{sample:{t:'21시 길드 파티 · 도핑 확인',at:ts}}}};calRecs=()=>__rows;calMon=day.slice(0,7);calSel=day;calDef=1;tab='cal';renderCal();return day;}"""
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page(viewport={'width':1440,'height':2400});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_function('typeof renderCal==="function"');pg.evaluate(FIXTURE);pg.wait_for_timeout(250);pg.locator('#calDet').screenshot(path='/workspace/maple-boss-tracker/b398_before.png' if before else '/workspace/maple-boss-tracker/b399_detail_regression.png')
  if not before:
   assert pg.locator('.cald-section').count()==1 and pg.locator('.cald-row').count()==3 and pg.evaluate('__rows.length')==5
   assert pg.evaluate('calDay(__rows,__day).m')==1500000000
   assert pg.locator('.cald-total b').inner_text()=='15억 메소'
   assert pg.locator('[data-calclose]').evaluate('(e)=>e.classList.contains("neonBtn")')
   assert pg.locator('.cald-metrics').inner_text().find('3억')>=0
   assert pg.locator('.cald-section').nth(0).inner_text().find('12억')>=0
   assert pg.locator('.cald-row .cald-money').evaluate_all('(L)=>L.every(e=>getComputedStyle(e).textAlign==="right")')
   assert pg.locator('[data-calmemo]').count()==1 and pg.locator('.calmx').inner_text()=='21시 길드 파티 · 도핑 확인'
   pg.set_viewport_size({'width':390,'height':844});assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   pg.click('[data-calclose]');assert pg.locator('#calDet').count()==0
   pg.evaluate("()=>{calSel='M:'+calMon;renderCal()}");assert pg.locator('#calML').count()==1
   assert not errs,errs
   print('ALL PASS b398: crystal sum + 3 item rows/5 unchanged records, 15억 total=3억 crystals+12억 items, amounts right-aligned, notes/close/month retained, mobile no overflow, JS errors=0')
  b.close()
finally:srv.terminate()
