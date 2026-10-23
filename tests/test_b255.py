# test_b255: 드롭 표 칩 = 에르다(이름에 '에르다') → 큐브('큐브') → 나머지, 그룹 안 비싼 순. 정보 칩(에르다 기운 → 메멘토 큐브 → 에테르넬/에리온/상자)
# MBT_SHOTDIR=폴더 → 1600px 사진 · MBT_ROOT=다른 빌드(변경 전 사진만)
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK=not os.environ.get('MBT_ROOT'); SD=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kalos':B('chaos'),'limbo':B('hard'),'will':B('hard')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
INJ="""()=>{ Object.assign(ITEMS,{zt_e1:{n:'솔 에르다의 조각',set:'정보'},zt_e2:{n:'솔 에르다',set:'정보'},zt_c1:{n:'블랙 큐브',set:'정보'},zt_c2:{n:'명장의 큐브',set:'정보'}});
  for(const k of ['zt_e1','zt_c1','zt_e2','zt_c2']) DROPS.seren.push([k,['extreme']]);
  const P=JSON.parse(localStorage.getItem(ITEM_PRICE_KEY)||'{}'), t=Date.now();
  P[priceId('zt_e1')]={p:3e7,t}; P[priceId('zt_e2')]={p:9e7,t}; P[priceId('zt_c1')]={p:2e8,t}; P[priceId('zt_c2')]={p:5e6,t};
  (DROPS.seren||[]).forEach(([k],i)=>{ if(!/^zt_/.test(k)&&!isRing(k)&&!P[priceId(k)]) P[priceId(k)]={p:(i+2)*2e9,t}; });
  localStorage.setItem(ITEM_PRICE_KEY,JSON.stringify(P)); render(); }"""
ORD="""()=>[...document.querySelectorAll('.drops')].filter(d=>d.offsetParent).map(d=>[...d.querySelectorAll('[data-drop]')].map(e=>{const k=e.dataset.drop.split('|')[1];return [k,dropSortP(k),dropGrp(k),isRing(k)?1:0]}))"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate(INJ); pg.wait_for_timeout(500)
    if SD:
      el=pg.locator('[data-drop^="seren|"]').first.locator('xpath=ancestor::*[contains(@class,"drops")]/..')
      el.screenshot(path=f'{SD}/'+('after_seren_drops_1600.png' if CHECK else 'before_seren_drops_1600.png'))
    if CHECK:
      rows=pg.evaluate(ORD)
      sr=[r for r in rows if any(x[0]=='zt_e1' for x in r)]
      check('seren row found', len(sr)==1, len(sr))
      r=sr[0] if sr else []
      ks=[x[0] for x in r]
      check('erda first, by price', ks[:2]==['zt_e2','zt_e1'], ks)
      check('cube next, by price', ks[2:4]==['zt_c1','zt_c2'], ks)
      rest=[x for x in r[4:] if not x[3]]
      check('rest by price desc', len(rest)>=2 and all(rest[i][1]>=rest[i+1][1] for i in range(len(rest)-1)), rest)
      check('rest more expensive than erda (order not price-only)', rest and rest[0][1]>r[0][1])
      bad=[q for q in rows if any((q[i][2],q[i][3],-q[i][1])>(q[i+1][2],q[i+1][3],-q[i+1][1]) for i in range(len(q)-1))]
      check('all rows: group → ring last → price', not bad, bad[:1])
      check('dropGrp names', pg.evaluate("()=>[dropGrp('zt_e1'),dropGrp('zt_c2'),dropGrp('lcm')]")==[0,1,2])
      info=pg.evaluate("""()=>[...document.querySelectorAll('.drops')].map(d=>[...d.querySelectorAll('.drop.erda:not(.off)')].map(e=>e.classList.contains('memc')?'c':e.classList.contains('eter')||e.classList.contains('erion')||e.classList.contains('ibox')?'o':'e').join(''))""")
      okinfo=all(s==''.join(sorted(s,key='eco'.index)) for s in info)
      check('info chips: 에르다 → 큐브 → others', okinfo and any('c' in s and 'o' in s for s in info), info)
    pg.close(); b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
