# b116: 스케줄러 보스 아이콘(최근접 4배) · 테두리 네 변 같음 · 난이도 네모 맨 왼쪽 위 걸침 · 이번주 아이템 판매금 줄 · 날파리 제각각
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8905'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b116_{TAG}_{name}.png'))
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
    pg.evaluate("()=>{const c=S.characters[0];c.drops['kaling|chaosbox']=1;c.drev['kaling|chaosbox']={m:20000000000,a:200,p:1,i:'cb:lcm'};save();render()}"); pg.wait_for_timeout(300)
    shot(pg.locator('.revpanel'),'revpanel'); shot(pg.locator('.boss').first,'bossrow')
    pg.evaluate("openRevAll()"); pg.wait_for_timeout(300); shot(pg.locator('#revAllModal .modal'),'revall')
    if not NOCHK:
        bd=pg.evaluate("[...document.querySelectorAll('#revAllModal .bfr, .boss .bfr')].map(p=>{const a=p.getBoundingClientRect(),b=p.querySelector('img.bicon').getBoundingClientRect();return [b.left-a.left,a.right-b.right,b.top-a.top,a.bottom-b.bottom].map(x=>Math.round(x*10)/10)})")
        check('3 테두리 네 변 같은 두께', bd and all(max(x)-min(x)<=0.6 for x in bd), bd[:4])
        bg=pg.evaluate("[...document.querySelectorAll('#revAllModal .bpic, .boss .bpic')].map(p=>{const a=p.getBoundingClientRect(),d=p.querySelector('.dbadge').getBoundingClientRect();return [d.left<a.left,d.top<a.top,d.right>a.left,d.bottom>a.top]})")
        check('4 난이도 네모 = 맨 왼쪽 위, 테두리에 걸치고 조금 밖으로', bg and all(all(x) for x in bg), bg[:4])
    pg.evaluate("document.querySelector('#revAllModal')?.remove()")
    if not NOCHK:
        nat=pg.evaluate("Promise.all(BOSSES.map(b=>new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.onerror=()=>r([0,0]);i.src=BOSS_ICONS[b.id]}))).then(a=>a)")
        check('1·2 스케줄러 아이콘 4배(정수 배율, ≥100px)', all(w>=100 and w%4==0 and h%4==0 for w,h in nat), nat[:5])
        same=pg.evaluate("Promise.all(['lotus','lucid'].map(k=>new Promise(r=>{const i=new Image();i.onload=()=>{const c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;const g=c.getContext('2d');g.drawImage(i,0,0);const d=g.getImageData(0,0,c.width,c.height).data;let n=0,t=0;for(let y=0;y<c.height-4;y+=4)for(let x=0;x<c.width-4;x+=4){const o=((y+1)*c.width+x+1)*4,q=((y+2)*c.width+x+2)*4;t++;if(Math.abs(d[o]-d[q])+Math.abs(d[o+1]-d[q+1])+Math.abs(d[o+2]-d[q+2])<40)n++;}r(n/t)};i.src=BOSS_ICONS[k]})))")
        check('2 b117 ④ 최근접 4배 + 외곽선·선명 (4×4 칸 안쪽은 거의 같은 색 = 점 느낌)', all(x>0.8 for x in same), same)
        sl=pg.evaluate("(()=>{const e=document.querySelector('.revpanel .rp-char .rp-sl');if(!e)return null;const all=[...e.parentElement.querySelectorAll('.rp-cl')].map(x=>x.textContent.trim().split(' ')[0]);return [e.textContent.trim(),e.querySelector('img')?.getAttribute('src')===(document.createRange().createContextualFragment(lootIco('chaosbox')).querySelector('img')||{}).getAttribute?.('src'),all]})()")
        check('5 이번주 아이템 판매금 줄: 검마 결정석 밑, 칠흑 상자에서 나온 최고가 = 상자 아이콘', sl and sl[0].startswith('이번주 아이템 판매금 ') and sl[1] and sl[2]==['주간','검마','이번주'], sl)
        n0=pg.evaluate("(()=>{const c=JSON.parse(JSON.stringify(S.characters[0]));c.id='c9';c.name='노판매';c.drev={};c.mdrev={};c.monthly={};S.characters.push(c);save();render();return [...document.querySelectorAll('.revpanel .rp-char')].find(e=>e.textContent.includes('노판매'))?.querySelector('.rp-sl')})()")
        check('5 판 게 없으면 줄 없음', n0 is None, n0)
    pg.click('[data-tab="loot"]'); pg.wait_for_timeout(500); shot(pg.locator('#poopKing'),'poop'); shot(pg.locator('#bossLootKing'),'lootking')
    if not NOCHK:
        fl=pg.evaluate("[...document.querySelectorAll('#poopKing tbody .poopav .fly')].map(f=>getComputedStyle(f).animationDuration+'/'+getComputedStyle(f).animationDelay)")
        check('6 날파리: 마리마다 다른 속도·시작', len(fl)>=4 and len(set(fl))==len(fl), fl[:8])
        for tab in ('boss','total','loot'):
            pg.click(f'[data-tab="{tab}"]'); pg.wait_for_timeout(400)
            bad=pg.evaluate("""()=>{ const out=[]; document.querySelectorAll('.dbadge').forEach(d=>{ const r=d.getBoundingClientRect(); if(!r.width) return;
              for(let e=d.parentElement;e&&e!==document.body;e=e.parentElement){ const cs=getComputedStyle(e); if(cs.overflowX!=='visible'||cs.overflowY!=='visible'){ const b=e.getBoundingClientRect(); if(r.left<b.left-0.5||r.top<b.top-0.5||r.right>b.right+0.5){ out.push((e.id||e.className)+''); break; } } } }); return out; }""")
            check(f'4 난이도 네모 안 잘림 ({tab})', not bad, bad[:5])
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
