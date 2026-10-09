import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 결정석 가격 자동 갱신 (prices.json) + 가격표 정렬 + 가격 갱신 버튼 제거
from playwright.sync_api import sync_playwright
import json, subprocess, os, time, urllib.request
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''));
    if not c: fails.append(n)
srv=subprocess.Popen(['python3','-m','http.server','8787','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen('http://127.0.0.1:8787/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
base=json.load(open(ROOT+'/prices.json',encoding='utf-8'))
base_price=lambda name: next(r['new'] for r in base['rows'] if r['boss']==name)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':1000},locale='ko-KR')
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    pg.goto('http://localhost:8787/index.html'); pg.wait_for_timeout(300)
    # 예전 수동 수정 가격이 있는 상태 → 무시/정리되어야 함
    st=json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')")); st['settings']['prices']={'seren_hard':777,'kalos_chaos':1}; st['settings']['priceSource']={'url':'x'}
    st['characters']=[{'id':'c1','name':'단풍용사','level':287,'job':'히어로','world':'스카니아','isMain':True,'ocid':'','bosses':{'seren':{'enabled':True,'diff':'hard','party':1}},'weekly':{'seren':True},'monthly':{},'auto':{},'sync':{},'drops':{}}]; st['activeId']='c1'
    pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(st)); pg.reload(); pg.wait_for_timeout(800)
    pr=lambda b,d: pg.evaluate(f"price(findBoss('{b}'),'{d}')")
    check('old manual overrides cleared', pg.evaluate("Object.keys(S.settings.prices).length")==0 and pr('seren','hard')==base_price('선택받은 세렌 (하드)'), pr('seren','hard'))
    foot=pg.inner_text('.pricecard .pc-foot'); check('card foot auto line', foot.startswith('공식 패치 노트 기준 자동 갱신 (마지막 확인 2026-10-09)'), foot)
    check('card title has crystal icon', pg.query_selector('.pricecard .pc-head h2 img.ric') is not None)
    check('no 수정 link in card', pg.query_selector('.pricecard [data-tab]') is None)
    check('46 official rows applied', pg.evaluate('officialInfo.applied')==46 and not pg.evaluate('officialInfo.pending.length'))
    wk=pg.evaluate("priceRows('weekly').map(r=>r.p)"); shown=pg.eval_on_selector_all('.pricecard .pc-list > .pc-row','e=>e.length')
    check('card rows sorted ascending', wk==sorted(wk) and shown==len(wk)+2, (shown,len(wk)))
    check('card list scrolls (max height)', pg.evaluate("(()=>{const l=document.querySelector('.pc-list');return l.scrollHeight>l.clientHeight&&l.clientHeight<=270})()"))
    check('no settings tab / price editing / update button', pg.query_selector('[data-tab="settings"]') is None and pg.query_selector('input[data-price]') is None and pg.query_selector('#priceUpdBtn') is None and pg.query_selector('#priceModal') is None)
    mod=json.loads(json.dumps(base)); mod['checkedAt']='2026-10-15'
    for r in mod['rows']:
        if r['boss']=='감시자 칼로스 (카오스)': r['new']=1250000000
        if r['boss'].startswith('스우 (하드)'): r['new']=50000000; r['effective']='2099-01-01'
    ctx.route('**/prices.json*',lambda rt,rq: rt.fulfill(status=200,content_type='application/json',body=json.dumps(mod,ensure_ascii=False)))
    pg.reload(); pg.wait_for_timeout(800)
    check('changed official price applied', pr('kalos','chaos')==1250000000, pr('kalos','chaos'))
    check('future effective not yet applied', pr('lotus','hard')!=50000000 and pg.evaluate('officialInfo.pending.length')==1, pr('lotus','hard'))
    foot=pg.inner_text('.pricecard .pc-foot'); check('foot shows new date + pending', '마지막 확인 2026-10-15' in foot and '2099-01-01부터 적용' in foot, foot)
    check('revenue uses official price', pg.evaluate("charRevenue(activeChar()).meso")==pr('seren','hard'))
    ctx.unroute('**/prices.json*'); ctx.route('**/prices.json*',lambda rt,rq: rt.fulfill(status=404,body='nf'))
    pg.reload(); pg.wait_for_timeout(600)
    check('cached official prices used when fetch fails', pr('kalos','chaos')==1250000000)
    ctx.unroute('**/prices.json*'); pg.reload(); pg.wait_for_timeout(800)
    pg.screenshot(path=''+OUT+'/price_card.png')
    m=ctx.new_page(); m.set_viewport_size({'width':375,'height':812}); m.on('pageerror',lambda e:errs.append(str(e)))
    m.goto('http://localhost:8787/index.html'); m.wait_for_timeout(600)
    check('mobile: card stacks, no overflow', not m.evaluate('document.documentElement.scrollWidth>innerWidth') and m.evaluate("document.querySelector('.pricecard').getBoundingClientRect().top>document.querySelector('.revpanel').getBoundingClientRect().bottom"))
    m.screenshot(path=OUT+'/shot9_mobile.png',full_page=True)
    f=b.new_context().new_page(); f.on('pageerror',lambda e:errs.append(str(e)))
    f.goto('file://'+ROOT+'/index.html'); f.wait_for_timeout(300)
    check('file:// foot line', '온라인 주소' in f.evaluate('priceAutoText()'), f.evaluate('priceAutoText()'))
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
