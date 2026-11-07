"""Essential party-exclusive drop UI + full-profit aggregation regression."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=str(ROOT),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
C={'id':'c0','name':'독식테스트','level':285,'job':'히어로','world':'스카니아','isMain':True,'image':'','bosses':{'kaling':{'enabled':True,'diff':'hard','party':3}},'weekly':{'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
state={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page(viewport={'width':1280,'height':900},locale='ko-KR');pg.goto(f'http://127.0.0.1:{PORT}/')
  pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",state);pg.reload()
  pg.wait_for_function('typeof askBbang === "function"')
  key=pg.evaluate(r'''()=>{const k=[...document.querySelectorAll('[data-drop^="kaling|"]')].map(e=>e.dataset.drop).find(k=>!/\|(r_|chaosbox)/.test(k));window.__k=k;const c=S.characters[0],b=findBoss('kaling');askBbang(c,b,k,()=>{dropMap(c,b.type)[k]=1},()=>askRev(c,b,k,k.split('|')[1],null));return k;}''')
  assert key
  assert pg.locator('[data-bb="n"] > span').inner_text().strip()=='독식'
  assert pg.locator('[data-bb="n"]').evaluate('(e)=>e.classList.contains("neonBtn")')
  assert pg.locator('[data-bb="n"]').bounding_box()['y']>pg.locator('[data-bb="s"]').bounding_box()['y']
  pg.locator('#bbModal .modal').screenshot(path='/workspace/maple-boss-tracker/b394_solo_button.png')
  pg.click('[data-bb="n"]');pg.wait_for_selector('#revModal')
  assert pg.locator('#rvTitle').inner_text().strip()=='수익을 기록할까요?'
  assert pg.locator('[data-fee="d"]').count()==0
  pg.fill('#rvAmt','10');pg.click('[data-fee="s"][data-v="0"]')
  pg.locator('#revModal .modal').screenshot(path='/workspace/maple-boss-tracker/b394_solo_popup.png')
  pg.click('[data-rv="ok"]')
  r=pg.evaluate('''()=>{const c=S.characters[0],d=charDrops(c,'weekly'),T=totalData();return {mode:c.dmode[__k],rev:c.drev[__k],rows:revAllRows(c).map(x=>({key:x.key,div:x.div,m:x.m})),items:d.items,sale:pItemSale(c),sum:revSum(d.revs),sales:T.sales,bb:bbangStats(T)};}''')
  assert r['mode']=='n' and r['rev']['m']==1000000000 and r['rev']['p']==1,r
  assert r['items'].get(key)==1 and r['sale']==1000000000 and r['sum']==1000000000,r
  assert r['rows'][0]['div']==1 and r['sales'][key.split('|')[1]+'#1']['m']==1000000000 and r['bb']=={},r
  print('PASS 독식 below choices, neon, solo popup, 10억 전액 p=1, fee=0, edit-all divisor, current/history/analysis sale=10억, no bbang win/loss')
  # 분배는 기존처럼 3인, 블빵승리는 전액: 독식 추가로 기존 셈법이 바뀌지 않음.
  for mode,div in [('s',3),('w',1)]:
   pg.evaluate("m=>{const c=S.characters[0];c.dmode[__k]=m;askRev(c,findBoss('kaling'),__k,__k.split('|')[1],null)}",mode)
   pg.fill('#rvAmt','9');pg.click('[data-rv="ok"]');rr=pg.evaluate('()=>S.characters[0].drev[__k]');assert rr['p']==div and rr['m']==900000000//div,rr
  b.close(); print('ALL PASS b394')
finally:srv.terminate()
