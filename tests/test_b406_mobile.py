"""b406(t377/t378): 모바일(≤768px) 정렬 + 득템 자동 기록 탭 숨김, 컴퓨터(1440) 그대로."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=str(ROOT),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox'])
  pg=b.new_page(viewport={'width':390,'height':844});pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_function('typeof render==="function"')
  assert not pg.locator('[data-tab="auto"]').is_visible() and pg.locator('#tabs .tabsep').first.is_hidden()
  assert pg.evaluate("getComputedStyle(document.querySelector('#tabs')).display")=='grid'
  pg.evaluate("()=>{tab='auto';render()}");assert pg.evaluate('tab')=='boss'
  for w in (390,360):
   pg.set_viewport_size({'width':w,'height':800})
   for t in ['boss','total','loot','cal','epic','live']:
    pg.click(f'[data-tab="{t}"]');pg.wait_for_timeout(200);assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth'),(w,t)
  pg.set_viewport_size({'width':1440,'height':900});pg.wait_for_timeout(100)
  assert pg.locator('[data-tab="auto"]').is_visible() and pg.evaluate("getComputedStyle(document.querySelector('#tabs')).display")=='flex'
  pg.evaluate("()=>{tab='auto';render()}");assert pg.evaluate('tab')=='auto'
  print('PASS b406: mobile 3-col tabs, auto tab hidden+fallback, no h-scroll; desktop unchanged');b.close()
finally:srv.terminate()
