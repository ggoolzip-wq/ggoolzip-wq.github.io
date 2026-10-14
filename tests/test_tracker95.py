# b127: 보스 드랍 테이블 난이도 = 게임 스케줄러 난이도 그림 (위컴알 Boss_UI_Difficulty_-_*.png)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8912'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b127')}_{TAG}_{name}.png"))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'',
   'bosses':{'lucid':B('hard'),'kaling':B('normal'),'seren':B('hard'),'blackmage':B('hard'),'kalos':B('chaos'),'magnus':B('hard'),'lotus':B('normal'),'will':B('easy'),'slime':B('chaos'),'limbo':B('normal')},'weekly':{'lucid':True,'kaling':True},'monthly':{},'auto':{},'sync':{},
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
    for bid,nm in [('lucid','루시드'),('slime','가디언 엔젤 슬라임'),('will','윌'),('kaling','카링')]:
        shot(pg.locator('.boss').filter(has_text=nm).first,f'row_{bid}')
    shot(pg.locator('#bossList, .bosslist, main').first,'list')
    pg.evaluate("()=>{const d=document.createElement('div');d.id='dShot';d.style.cssText='position:fixed;top:10px;left:10px;z-index:99999;padding:8px;background:var(--panel);display:flex;gap:10px';d.innerHTML=['easy','normal','hard','chaos','extreme'].map(x=>typeof diffImg==='function'?diffImg(x):'<span class=pill>'+D[x]+'</span>').join('');document.body.appendChild(d)}")
    shot(pg.locator('#dShot'),'all_diffs'); pg.evaluate("()=>document.getElementById('dShot').remove()")
    if not NOCHK:
        R=pg.evaluate("""[...document.querySelectorAll('.boss .bn')].map(e=>{const i=e.querySelector('.dimg img');const r=i&&i.getBoundingClientRect();return {t:e.innerText.replace(/\\s+/g,' ').trim(),src:i?i.getAttribute('src'):null,w:r?Math.round(r.width):0,h:r?Math.round(r.height):0,pill:!!e.querySelector('.pill:not(.err)'),pix:i?getComputedStyle(i).imageRendering:''}})""")
        IC=pg.evaluate("Object.fromEntries(['easy','normal','hard','chaos','extreme'].map(d=>[d,ITEM_ICONS['dif_'+d]]))")
        DK={'이지':'easy','노말':'normal','하드':'hard','카오스':'chaos','익스트림':'extreme'}
        check('모든 보스 행: 글자 난이도 pill 대신 그림', len(R)>=8 and all(x['src'] and not x['pill'] for x in R), [(x['t'],x['pill']) for x in R])
        ok=[x for x in R if any(x['src']==IC[v] and k in x['t'] for k,v in DK.items())]
        check('난이도마다 맞는 그림 (텍스트 난이도와 일치)', len(ok)==len(R), [x['t'] for x in R])
        check('원본 픽셀 크기 68×18 + pixelated', all(x['w']==68 and x['h']==18 and x['pix']=='pixelated' for x in R), [(x['w'],x['h'],x['pix']) for x in R])
        check('이지·노말·하드·카오스·익스트림 그림 5개 모두 있고 서로 다름', all(IC.values()) and len(set(IC.values()))==5)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
