# test_b246: 드롭 표 칩 = 비싼 순 (테두리 등급 시세 tierP, 반지 상자 = 리4·컨4 기댓값, 시세 없음 = 뒤, 같으면 원래 순서) — PC·모바일
# MBT_SHOTDIR=폴더 → 사진 · MBT_ROOT=다른 빌드(변경 전 사진만)
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
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard'),'kalos':B('chaos'),'limbo':B('hard'),'lucid':B('hard'),'will':B('hard')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
ORD="""()=>[...document.querySelectorAll('.drops')].filter(d=>d.offsetParent).map(d=>[...d.querySelectorAll('[data-drop]')].map(e=>{const k=e.dataset.drop.split('|')[1];return [k,dropSortP(k),typeof dropGrp==='function'?dropGrp(k):2]}).filter(x=>!isRing(x[0])))"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for vw,vh,tag in ([(1280,900,''),(390,844,'_mobile')] if CHECK else [(1280,900,'')]):
      pg=b.new_page(viewport={'width':vw,'height':vh},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1000)
      # 시세: 원래 순서 뒤쪽일수록 비싸게(정렬이 뒤집어야 함), 각 줄 첫 칩(반지 아닌 것)은 시세 없음, 리4·컨4 시세 있음
      pg.evaluate("""()=>{const P={ring_r4:{p:5e9,t:Date.now()},ring_c4:{p:3e9,t:Date.now()}}; [...document.querySelectorAll('.drops')].forEach(d=>{[...d.querySelectorAll('[data-drop]')].forEach((e,i)=>{const k=e.dataset.drop.split('|')[1]; if(!isRing(k)&&i>0&&!P[priceId(k)]) P[priceId(k)]={p:(i+1)*7e8,t:Date.now()};});}); localStorage.setItem(ITEM_PRICE_KEY,JSON.stringify(P));}""")
      pg.reload(); pg.wait_for_timeout(1000)
      if SD and not tag:
        el=pg.locator('[data-drop^="seren|"]').first.locator('xpath=ancestor::*[contains(@class,"drops")]/..')
        el.screenshot(path=f'{SD}/'+('order_after.png' if CHECK else 'order_before.png'))
      if CHECK:
        rows=pg.evaluate(ORD)
        check(f'drop rows found {vw}', len([r for r in rows if len(r)>1])>=3, len(rows))
        bad=[r for r in rows if any((r[i][2],-r[i][1])>(r[i+1][2],-r[i+1][1]) for i in range(len(r)-1))]  # b255: 에르다→큐브→나머지 그룹 안에서 비싼 순
        check(f'chips sorted by price desc {vw}', not bad, bad[:1])
        anyp=[r for r in rows if any(x[1]>0 for x in r) and any(x[1]==0 for x in r)]
        check(f'unpriced last {vw}', all(r.index(next(x for x in r if x[1]==0))>=sum(1 for x in r if x[1]>0) for r in anyp), anyp[:1])
        ring=pg.evaluate("()=>{const k=[...RING_KEYS].find(k=>ring4(k)?.r4>0); const p=ring4(k); return [dropSortP(k), (p.r4/100)*tierP('ring:r4')+(p.c4/100)*tierP('ring:c4')]}")
        rl=pg.evaluate("()=>[...document.querySelectorAll('.drops')].every(d=>{const r=[...d.querySelectorAll('[data-drop]')].map(e=>isRing(e.dataset.drop.split('|')[1])); const f=r.indexOf(true); return f<0||r.slice(f).every(Boolean);})")
        check('b247 ring boxes always last', rl)
        check('ring box = expected value', ring[0]>0 and abs(ring[0]-ring[1])<1, ring)
        check(f'order actually changed (priced rows) {vw}', sum(1 for r in rows if len({x[1] for x in r})>1)>=1, [[x[0] for x in r] for r in rows][:2])
      pg.close()
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
