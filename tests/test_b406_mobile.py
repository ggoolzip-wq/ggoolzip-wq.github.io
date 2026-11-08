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
  for t in ['total','loot','cal','epic','live']:
   pg.click(f'[data-tab="{t}"]');pg.wait_for_timeout(150);assert pg.locator('#charList').is_hidden(),t
  pg.click('[data-tab="boss"]');pg.wait_for_timeout(150);assert pg.locator('#charList').is_visible()
  pg.click('[data-tab="cal"]');pg.set_viewport_size({'width':1440,'height':900});pg.wait_for_timeout(100);assert pg.locator('#charList').is_visible();pg.click('[data-tab="boss"]')
  pg.set_viewport_size({'width':1440,'height':900});pg.wait_for_timeout(100)
  assert pg.locator('[data-tab="auto"]').is_visible() and pg.evaluate("getComputedStyle(document.querySelector('#tabs')).display")=='flex'
  pg.evaluate("()=>{tab='auto';render()}");assert pg.evaluate('tab')=='auto'
  pg.route('https://open.api.nexon.com/static/maplestory/character/look/**',lambda r:r.fulfill(body=open(str(ROOT/'apple-touch-icon.png'),'rb').read(),content_type='image/png'))
  pg.click('[data-tab="epic"]');pg.wait_for_timeout(300)
  r=pg.evaluate('''async()=>{const v=document.querySelector('#view');v.insertAdjacentHTML('beforeend','<div class="ecgrid">'+ecCard({id:'t',t0:Date.now(),boss:'lucid',item:'eye',cid:'zz',start:0,end:1000}).replace('<span class="ecq">?</span></i><span>캐릭터','')+'</div>');
   const h=document.createElement('div');h.className='ectl';h.innerHTML=ecAvatar({name:'가',image:'https://open.api.nexon.com/static/maplestory/character/look/X'});v.append(h);await new Promise(r=>setTimeout(r,400));
   const a=h.querySelector('.avatar').getBoundingClientRect(),i=h.querySelector('img').getBoundingClientRect();return [a.x-i.x,a.y-i.y,i.width,a.width]}''')
  assert abs(r[0]-11.3)<1.5 and abs(r[1]-13.4)<1.5 and round(r[2])==68 and round(r[3])==24,r
  print('PASS b407 epic portrait crop = 독식 portrait region (96px x16~50,y19~53)')
  print('PASS b406/b407: char list hidden on non-boss mobile tabs; mobile 3-col tabs, auto tab hidden+fallback, no h-scroll; desktop unchanged');b.close()
finally:srv.terminate()
