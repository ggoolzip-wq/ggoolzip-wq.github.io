# b121: 이번 주 수익 위 두 줄 — 숫자 오른쪽, 이번주 획득 아이템에서 반지 상자 제외, 그 밑 반지 상자 줄
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8909'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b121_{TAG}_{name}.png'))
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
    pg.evaluate("s=>{S.characters=s.characters;S.settings.accounts=s.settings.accounts;S.activeId='c1';const c=S.characters[0];c.bosses.blackmage={enabled:true,diff:'extreme',party:1};c.monthly={blackmage:S.period.week};c.mdate={blackmage:'2026-10-08'};c.mdrops={'blackmage|genesis':1};c.mdrev={'blackmage|genesis':{m:3000000000,a:30,p:1,i:'genesis'}};save();render()}",ST); pg.wait_for_timeout(400)
    pg.evaluate("()=>{const c=S.characters[0];c.bosses.seren={enabled:true,diff:'hard',party:1};c.weekly.seren=true;c.drops['seren|r_black']=3;c.drops['seren|r_white']=3;c.drops['lucid|r_life']=1;c.outcomes=c.outcomes||{};save();render()}"); pg.wait_for_timeout(300)
    pg.evaluate("()=>{const c=S.characters[0];c.dropOut={'seren|r_black':['r4','x','x'],'seren|r_white':['c4','gl']};save();render()}"); pg.wait_for_timeout(300)
    shot(pg.locator('.revpanel'),'revpanel')
    shot(pg.locator('.revpanel .rp-total').locator('xpath=..'),'revtop')
    if not NOCHK:
        L=pg.evaluate("[...document.querySelectorAll('.revpanel .rp-line:not(.rp-left)')].map(e=>{const n=e.querySelector('.rpn'),l=e.querySelector('.rpl');return {t:e.innerText.replace(/\\s+/g,' ').trim(),nr:n?Math.round(n.getBoundingClientRect().right):null,er:Math.round(e.getBoundingClientRect().right),nl:n&&l?n.getBoundingClientRect().left>=l.getBoundingClientRect().right:false,ic:[...e.querySelectorAll('img,svg,.ric')].map(i=>Math.round(i.getBoundingClientRect().width))}})")
        check('결정석·아이템 줄: 글자 먼저, 숫자 오른쪽 끝', len(L)>=3 and all(x['nr'] is not None and abs(x['nr']-x['er'])<=2 and x['nl'] for x in L[:2]), L)
        check('이번주 획득 아이템: 반지 상자 제외 (벨트·연마석·맹세 3개)', '이번주 획득 아이템 3개' in L[-2]['t'], L[-2])
        rg=L[-1]
        check('반지 상자 줄: 가장 많은 상자 아이콘(흑옥·백옥 3개 동점 → 아이템 순서 백옥) 16px + 7개, 결과 0개는 숨김 (b213: 리4·컨4 아이콘 = 글씨 높이)', rg['t'].startswith('반지 상자 7개') and len(rg['ic'])>=1 and rg['ic'][0]==16 and all(w<16 for w in rg['ic'][1:]) and pg.evaluate("(()=>{const d=document.createElement('div');d.innerHTML=itemIcon('r_white');const a=document.querySelector('.revpanel .rp-ring .rpg > :first-child');return !!a&&a.outerHTML===d.firstElementChild.outerHTML})()"), rg)
        check('결과: 리4 1 · 컨4 1 · 연마석 1 · 꽝 2 (0개 숨김)', rg['t']=='반지 상자 7개 리4 1개 컨4 1개 연마석 1개 꽝 2개', rg)
    pg.evaluate("()=>{const c=S.characters[0];c.dropOut['lucid|r_life']=['gl'];save();render()}"); pg.click('[data-tab=loot]'); pg.wait_for_timeout(600)
    shot(pg.locator('#lootTop'),'loot_top'); shot(pg.locator('.ringcard'),'ringcard')
    if not NOCHK:
        rt=pg.evaluate("document.querySelector('#ltRing').innerText.replace(/\\s+/g,' ')")
        # 기록한 상자: 흑옥 3(5%) · 백옥 2(10%) · 생명 1(리4+컨4 14.51613×0.7×2 + 연마석 14.51613 = 34.84%) / 성공 r41+c41+gl1 = 3
        ps=[12.5*.2*2/100]*3+[14.28571*.35*2/100]*2+[(14.51613*.7*2+14.51613)/100]
        import itertools, math
        pp=sum(math.prod(ps[i] if r[i] else 1-ps[i] for i in range(6)) for r in itertools.product([0,1],repeat=6) if sum(r)>=3)*100
        js=pg.evaluate("lootSummary(totalData()).ringTop")
        check('b122 반상 상위: 생명 상자 연마석도 성공으로 (상자마다 리4+컨4+연마석 확률)', abs(js-pp)<1e-9, (rt,js,pp))
        ex=pg.evaluate("document.querySelector('.ringcard .ringexp').innerText")
        check('b122 시드링 기댓값 끝에 연마석 (생명 상자 1개 × 14.51613% = 0.15개)', ex.endswith(' · 연마석 0.15개'), ex)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
