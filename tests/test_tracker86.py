# b114: 시세 갱신 익셉셔널 해머 채움 · 가격 목록 중복(칠흑 상자 선택 cb:x 와 직접 드롭 x) 없앰. (b112 test84 바탕)
# b112: 가격 카드 '결정석 가격 / 아이템 가격' 탭, 관리자 '시세 등록', 익셉셔널 해머 시세 이름(얼장/눈장/벨트),
# 수익 기록 전체 수정 = 보스별 묶음(초상화 1번 + 난이도 배지), '이번주 획득 아이템' 앞 아이콘, 캐릭터 정보 결정석/아이템 판매 두 줄, '이번달 검마 (10월 8일 격파 완료)',
# 429: 초당 한도는 1번 재시도 + '오늘 한도 도달' 아님. MBT_ROOT/MBT_SHOTDIR/MBT_TAG/MBT_NOCHECK. Worker·넥슨은 가짜 응답.
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAI=os.path.join(os.path.dirname(os.path.abspath(__file__)),'fixtures','mai_2026-10-13.json'); PORT='8902'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b114_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'',
   'bosses':{'lucid':B('hard'),'kaling':B('normal'),'blackmage':B('extreme'),'zakum':B('chaos')},'weekly':{'lucid':True,'kaling':True},'monthly':{},'auto':{},'sync':{},
   'drops':{'lucid|whisper':1,'lucid|g_faith':1,'kaling|oath':1},'drev':{'lucid|whisper':{'m':500000000,'a':5,'p':1,'i':'whisper'},'kaling|oath':{'m':900000000,'a':9,'p':1,'i':'oath'}}}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
SRV={'prices':{'whisper':{'p':6200000000,'t':1760000000000},'h_face':{'p':6199000000,'t':1760000000000}},'puts':[],'pub':0,'nx':[]}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1600,'height':1000},locale='ko-KR')
    H={'Access-Control-Allow-Origin':'*'}
    def api(r):
        u=r.request.url
        if u.endswith('/api/me'): return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'admin':True,'user':'u0','accounts':[]}))
        if u.endswith('/api/prices'): SRV['pub']+=1; return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'prices':SRV['prices']}))
        if '/api/admin/prices' in u:
            if r.request.method=='PUT': d=json.loads(r.request.post_data)['prices']; SRV['puts'].append(d); SRV['prices'].update(d)
            return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'prices':SRV['prices']}))
        if '/api/admin/maple-prices' in u: return r.fulfill(status=200,content_type='application/json',headers=H,body=open(MAI).read())
        if '/api/admin/users' in u: return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'users':[]}))
        return r.fulfill(status=200,content_type='application/json',headers=H,body='{}')
    def nxapi(r):  # /maplestory/v1/id: 첫 호출 429(초당), 두 번째 200
        SRV['nx'].append(time.time())
        if 'tst429' in r.request.url and len([1 for _ in SRV['nx']])==1: return r.fulfill(status=429,content_type='application/json',headers=H,body=json.dumps({'error':{'name':'OPENAPI00007','message':'rate'}}))
        return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'ocid':'x1'}))
    ctx.route('http://127.0.0.1:9998/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Methods':'GET,PUT,POST,DELETE','Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else api(r))
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else nxapi(r) if 'tst429' in r.request.url else r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9998');localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}",ST)
    pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}")
    pg.evaluate("typeof itemPriceLoad==='function'&&itemPriceLoad()"); pg.wait_for_timeout(300)
    pg.evaluate("s=>{S.characters=s.characters;S.settings.accounts=s.settings.accounts;S.activeId='c1';save();render()}",ST); pg.wait_for_timeout(300)
    pg.evaluate("()=>{const c=S.characters[0];c.monthly.blackmage=S.period.week;c.mdate={blackmage:'2026-10-08'};save();render()}"); pg.wait_for_timeout(300)
    pg.evaluate("admPriceRun()"); pg.wait_for_timeout(1500)
    pg.click('.pricecard [data-pckind=item]'); pg.wait_for_timeout(300); shot(pg.locator('.pricecard'),'pricecard_items')
    pg.evaluate("openMkt()"); pg.wait_for_timeout(300); shot(pg.locator('#mktModal .modal'),'mkt')
    if not NOCHK:
        put=SRV['puts'][0] if SRV['puts'] else {}
        check('시세 갱신: 익셉셔널 해머 얼장/눈장/벨트 채움', all(k in put and put[k]['p']>0 for k in ('h_face','h_eye','h_belt')), sorted(put))
        check('해머 가격 = 페이지 값', put.get('h_face',{}).get('p')==6199000000 and put.get('h_eye',{}).get('p')==22133000000, {k:put.get(k) for k in ('h_face','h_eye','h_belt')})
        alt=pg.evaluate("maiMap({'익셉셔널 해머 : 얼굴장식':{main:60},'익셉셔널 눈장식':{main:200},'익셉셔널 해머(벨트)':{main:50}},1)")
        check('이름이 달라도 맞춤(해머 : 얼굴장식 · 눈장식 · 해머(벨트))', alt.get('h_face',{}).get('p')==6e9 and alt.get('h_eye',{}).get('p')==2e10 and alt.get('h_belt',{}).get('p')==5e9, alt)
        for sel,n in (('.pricecard .pc-it .pc-nm','아이템 가격 탭'),('#mktModal .raname','시세 등록')):
            names=pg.eval_on_selector_all(sel,"e=>e.map(x=>(x.firstChild&&x.firstChild.textContent||x.textContent).trim())")
            dup=sorted({x for x in names if names.count(x)>1})
            check(n+': 같은 아이템 한 번씩', names and not dup, dup)
        ids=pg.evaluate("revItems().map(priceId)"); check('revItems 시세 키 중복 없음', len(ids)==len(set(ids)), ids)
    check('no page errors', not errs, errs[:3])
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
