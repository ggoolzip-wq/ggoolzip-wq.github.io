# test_b253: 드롭 전수 보강 — 에테르넬 방어구 상자 추가(2출처; b254: 로이드·소울 조각 삭제, 칼로스·대적자·카링 상자는 정보 칩), 에리온의 조각 칩, 정렬 유지, 못 가진 아이템 목록 제외
import os, sys, json, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT,'scripts'))
import boss_auto as A
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
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
    r=pg.evaluate("""()=>{const f=id=>BOSSES.find(b=>b.id===id);const d=(id,x)=>dropsFor(f(id),x);
      const order=(id,x)=>{const L=d(id,x);const ri=L.findIndex(k=>RING_DROPS&&String(k).includes('ring')||(ITEMS[k]&&/반지/.test(ITEMS[k].n)));return {L,ri}};
      return {ke:d('kalos','extreme'),ae:d('adversary','extreme'),jh:d('jupiter','hard'),le:order('limbo','extreme'),
        er:[erionFor(f('jupiter'),'hard'),erionFor(f('kalos'),'extreme'),erionFor(f('adversary'),'hard'),erionFor(f('kaling'),'extreme')],
        miss:missingItems(totalData()).some(o=>['방어구','정보'].includes((ITEMS[o.k]||{}).set)),
        names:[ITEMS.b_jupiter.n,ITEMS.b_limbo.n,ITEMS.b_baldrix.n], gone:Object.keys(ITEMS).filter(k=>/^[as]_/.test(k)), ib:[infoBoxFor(f('kalos'),'extreme'),infoBoxFor(f('adversary'),'extreme')]}}""")
    check('b254: 칼로스·대적자 익스트림 방어구 상자 = 기록 안 함(DROPS 에 없음, 정보 칩)', 'b_kalos' not in r['ke'] and 'b_adv' not in r['ae'] and r['ib']==[['b_kalos'],['b_adv']], [r['ke'],r['ae'],r['ib']])
    check('유피테르 하드: 갈망 방어구 상자 기록 가능, 로이드·소울 없음', 'b_jupiter' in r['jh'] and not any(k.startswith(('a_','s_')) for k in r['jh']), r['jh'])
    check('b254: 로이드·소울 조각 아이템 전부 삭제', r['gone']==[], r['gone'])
    check('이름: 갈망·욕망·맹세 방어구 상자', r['names']==['갈망의 에테르넬 방어구 상자','욕망의 에테르넬 방어구 상자','맹세의 에테르넬 방어구 상자'], r['names'])
    L=r['le']['L']; check('정렬: 반지 상자 맨 끝 유지, 새 항목은 그 앞', 'b_limbo' in L and L.index('b_limbo')<len(L)-1 and '반지' in pg.evaluate("k=>ITEMS[k].n",L[-1]), L)
    check('에리온: 유피테르 하드 360·칼로스 익스 180·대적자 하드 30, 카링 익스 480(b264 나무위키)', r['er']==[360,180,30,480], r['er'])
    check('못 가진 아이템 목록에 새 세트 없음', not r['miss'])
    pg.evaluate("()=>{const c=S.characters[0];c.bosses={jupiter:{enabled:true,diff:'hard',party:1}};render()}"); pg.wait_for_timeout(500)
    e=pg.evaluate("()=>[...document.querySelectorAll('.drop.erion')].map(x=>x.getAttribute('aria-label')+'|'+x.innerText)")
    check('화면: 에리온의 조각 360 칩', any('에리온의 조각 360' in x for x in e), e)
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
