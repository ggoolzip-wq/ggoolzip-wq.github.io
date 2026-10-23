# test_b252: 익스트림 림보·발드릭스 내장 데이터 — 결정석 75억/96억(커뮤니티, 사용자 승인), 익셉셔널 해머 (포켓)/(펜던트), 하드 이월 드롭, 내장 우선 + 가격 충돌 기록
import os, sys, json, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT,'scripts'))
import boss_auto as A
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
bp=A.builtin_prices(); check('boss_auto.builtin_prices: 75억/96억', bp.get('limbo_extreme')==7500000000 and bp.get('baldrix_extreme')==9600000000, bp.get('limbo_extreme'))
d=A.load(os.path.join(tempfile.mkdtemp(),'x.json')); src={'url':'https://maplestory.nexon.com/News/Update/900'}
ch=A.apply(d,[{'name':'림보','diff':'extreme','price':8000000000}],src,True,A.builtin(),'T')
check('boss_auto: 공지 가격 다르면 덮지 않고 conflicts 기록', ch and d['bosses']==[] and d['conflicts'][0]['official']==8000000000 and d['conflicts'][0]['builtin']==7500000000 and d['log'][-1]['action']=='conflict', d)
A.apply(d,[{'name':'림보','diff':'extreme','price':8000000000}],src,True,A.builtin(),'T2'); check('conflicts 중복 없음', len(d['conflicts'])==1)
A.apply(d,[{'name':'발드릭스','diff':'extreme','price':9600000000}],src,True,A.builtin(),'T3'); check('같은 가격이면 기록 없음', len(d['conflicts'])==1)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'limbo':{'enabled':True,'diff':'extreme','party':1},'baldrix':{'enabled':True,'diff':'extreme','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1500)
    r=pg.evaluate("()=>{const f=id=>BOSSES.find(b=>b.id===id);const n=(id)=>dropsFor(f(id),'extreme').map(k=>ITEMS[k].n);return {lp:price(f('limbo'),'extreme'),bp:price(f('baldrix'),'extreme'),ld:n('limbo'),bd:n('baldrix'),lh:dropsFor(f('limbo'),'hard'),bh:dropsFor(f('baldrix'),'hard'),el:ETERNAL.limbo.extreme,eb:ETERNAL.baldrix.extreme||null,unk:priceRows0('weekly').filter(x=>['limbo','baldrix'].includes(x.b.id)&&!(x.p>0)).length}}")
    check('가격: 림보 익스트림 7,500,000,000 / 발드릭스 9,600,000,000', r['lp']==7500000000 and r['bp']==9600000000, r)
    check('가격 미확인 행 없음 (림보·발드릭스)', r['unk']==0, r)
    check('림보 익스트림 드롭 (가격순, 해머 다음 반지 상자 맨 끝)', r['ld']==['근원의 속삭임','혼돈의 칠흑 장신구 상자','신념의 연마석','3단계 소울 에테르','익셉셔널 해머 (포켓)',r['ld'][-1]] and '반지' in r['ld'][-1], r['ld'])
    check('발드릭스 익스트림 드롭', r['bd'][0]=='죽음의 맹세' and r['bd'][-2]=='익셉셔널 해머 (펜던트)' and '반지' in r['bd'][-1] and len(r['bd'])==6, r['bd'])
    check('하드에는 새 해머 없음', 'h_pocket' not in r['lh'] and 'h_pendant' not in r['bh'], r)
    check('에테르넬: 림보 익스트림 5개(2출처), 발드릭스 익스트림은 단일 출처라 없음', r['el']==['e_limbo',5] and r['eb'] is None, r)
    c=pg.evaluate("()=>{const ok=applyOfficialPrices({rows:[{boss:'림보 (익스트림)',new:8000000000},{boss:'카링 (익스트림)',new:4845000000}],source:{url:'u'}});return {p:PRICE_CONFIG.limbo_extreme,c:priceConflicts}}")
    check('공식 가격표가 달라도 내장 75억 유지 + priceConflicts 기록', c['p']==7500000000 and c['c'] and c['c'][0]['official']==8000000000, c)
    pg.evaluate("()=>render()"); body=pg.inner_text('body')
    check('화면: 해머 칩 이름', all(x in pg.content() for x in ('익셉셔널 해머 (포켓)','익셉셔널 해머 (펜던트)')))
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
