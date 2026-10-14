# b123: 보스 드랍 테이블에 메멘토 큐브(수에큐·실버·골드) 확정 지급 개수 정보 칩
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8910'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b123')}_{TAG}_{name}.png"))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'',
   'bosses':{'lucid':B('hard'),'kaling':B('normal'),'seren':B('hard'),'blackmage':B('hard'),'kalos':B('chaos'),'magnus':B('hard')},'weekly':{'lucid':True,'kaling':True},'monthly':{},'auto':{},'sync':{},
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
    pg.evaluate("s=>{S.characters=s.characters;S.settings.accounts=s.settings.accounts;S.activeId='c1';save();render()}",ST); pg.wait_for_timeout(500)
    INFO=pg.evaluate("""(()=>{const r={};for(const b of BOSSES){const c=S.characters[0];const d=c.bosses[b.id]?.diff;if(!d)continue;const h=document.createElement('div');h.innerHTML=dropsHtml(b,d,null);r[b.id]=[...h.querySelectorAll('.memc')].map(e=>e.getAttribute('aria-label'))}return r})()""")
    # 화면 스크린샷: 메멘토 칩이 있는 첫 보스 행들
    for bid,nm in [('lucid','루시드'),('seren','세렌'),('kaling','카링')]:
        shot(pg.locator('.drops').locator('xpath=..').filter(has_text=nm).last,f'row_{bid}')
    shot(pg.locator('body'),'page')
    if not NOCHK:
        check('루시드 하드: 수에큐 8 · 실버 1', INFO.get('lucid')==['메멘토 수상한 에디셔널 큐브 8개','메멘토 실버 큐브 1개'], INFO)
        check('세렌 하드: 수에큐 8 · 골드 2', INFO.get('seren')==['메멘토 수상한 에디셔널 큐브 8개','메멘토 골드 큐브 2개'], INFO)
        check('카링 노멀: 골드 3 (수에큐 미확인 → 비움)', INFO.get('kaling')==['메멘토 골드 큐브 3개'], INFO)
        check('검마 하드: 실버 8 (수에큐 상충 → 비움)', INFO.get('blackmage')==['메멘토 실버 큐브 8개'], INFO)
        check('매그너스 하드: 수에큐 1', INFO.get('magnus')==['메멘토 수상한 에디셔널 큐브 1개'], INFO)
        check('칼로스 카오스: 미확인 → 칩 없음', INFO.get('kalos')==[], INFO)
        n=pg.evaluate("document.querySelectorAll('.drops .memc').length")
        check('화면 칩 렌더 (주간: 루8·1 + 카3 + 세8·2 + 매1 = 6)', n==6, n)
        tip=pg.evaluate("(()=>{const e=document.querySelector('.drops .memc.mc-g');return [e.getAttribute('aria-label'), !!e.querySelector('img'), e.querySelector('.ecnt').textContent, e.hasAttribute('data-drop')]})()")
        check('골드 칩: 이름(aria, 에르다처럼 툴팁 없음)·공식 아이콘 이미지·개수 배지·클릭 기록 없음', tip[0].startswith('메멘토 골드 큐브') and tip[1] and tip[2] in ('2','3') and not tip[3], tip)
    if not NOCHK:
        sz=pg.evaluate("Promise.all(['b','s','g'].map(t=>new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.src=ITEM_ICONS['mc_'+t]})))")
        check('b124 메멘토 전용 아이콘 (35×35, 일반 큐브 30/32px 아님)', all(x==[35,35] for x in sz), sz)
        same=pg.evaluate("[...document.querySelectorAll('.drops .memc img')].every(i=>Object.values({b:ITEM_ICONS.mc_b,s:ITEM_ICONS.mc_s,g:ITEM_ICONS.mc_g}).includes(i.src))")
        check('b124 화면 모든 메멘토 칩이 메멘토 아이콘 사용', same)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
