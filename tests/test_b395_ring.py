"""Essential ring-party choices, full solo profit, and four-button alignment."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=str(ROOT),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
C={'id':'c0','name':'반지테스트','level':285,'job':'히어로','world':'스카니아','isMain':True,'image':'','bosses':{'kaling':{'enabled':True,'diff':'hard','party':3}},'weekly':{'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
state={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page(viewport={'width':1280,'height':900},locale='ko-KR');pg.goto(f'http://127.0.0.1:{PORT}/');pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",state);pg.reload();pg.wait_for_function('typeof chooseRing==="function"')
  key=pg.evaluate('''()=>{window.__key=[...document.querySelectorAll('[data-drop^="kaling|r_"]')][0].dataset.drop;celebrate=()=>{};return __key;}''');assert key
  def pick(out='r4'):
   pg.evaluate("()=>{const c=S.characters[0];c.drops={};c.dmode={};c.drev={};c.dropOut={};openRing(__key)}");pg.click(f'#ringModal [data-ring="{out}"]')
  pick();pg.wait_for_selector('#bbModal')
  boxes=pg.locator('#bbModal [data-bb]:not([data-bb=""])').evaluate_all('(els)=>els.map(e=>{const r=e.getBoundingClientRect(),s=e.querySelector(":scope > span:last-child").getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,tx:s.x}})')
  assert len(boxes)==4 and all(abs(x['x']-boxes[0]['x'])<1 and abs(x['w']-boxes[0]['w'])<1 and abs(x['h']-boxes[0]['h'])<1 and abs(x['tx']-boxes[0]['tx'])<1 for x in boxes),boxes
  gaps=[boxes[i+1]['y']-boxes[i]['y']-boxes[i]['h'] for i in range(3)];assert max(gaps)-min(gaps)<1,gaps
  pg.locator('#bbModal .modal').screenshot(path='/workspace/maple-boss-tracker/b395_ring_aligned.png')
  pg.click('[data-bb="n"]');pg.fill('#rvAmt','9');pg.click('[data-fee="s"][data-v="0"]');pg.click('[data-rv="ok"]')
  r=pg.evaluate('()=>({r:S.characters[0].drev[__key],d:charDrops(S.characters[0],"weekly")})');assert r['r']['p']==1 and r['r']['m']==900000000 and r['r']['i']=='ring:r4' and r['d']['items'][key]==1,r
  pick('c4');pg.click('[data-bb="s"]');pg.fill('#rvAmt','9');pg.click('[data-rv="ok"]');r=pg.evaluate('()=>S.characters[0].drev[__key]');assert r['p']==3 and r['m']==300000000 and r['i']=='ring:c4',r
  pick();pg.click('[data-bb="l"]');assert pg.locator('#revModal').count()==0 and pg.evaluate('()=>S.characters[0].dmode[__key]')=='l'
  pick();pg.click('#bbModal [data-bb=""]');assert pg.evaluate('()=>!S.characters[0].drops[__key]')
  pick('x');pg.click('[data-bb="n"]');assert pg.locator('#revModal').count()==0
  pg.evaluate('()=>S.characters[0].bosses.kaling.party=1');pick();assert pg.locator('#bbModal').count()==0 and pg.locator('#revModal').count()==1
  b.close();print('ALL PASS b395: ring r4/c4/x choices, solo full p=1, split p=3, loss no revenue, cancel no drop, solo bypass; 4 button x/width/height/text/gaps aligned')
finally:srv.terminate()
