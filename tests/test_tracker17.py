# 구글 드라이브 동기화: 두 기기(집 PC · PC방) 시뮬레이션 — '어느 데이터를 쓸까요?' 반복 버그(2026-10-10) 회귀 테스트
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec=importlib.util.spec_from_file_location('t10h', os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_tracker10.py'))
src=open(spec.origin,encoding='utf-8').read()
# test10 의 Drive 모의 객체·INIT·state() 만 재사용 (본문 실행 없이)
head=src.split('with sync_playwright() as p:')[0].replace("srv=subprocess.Popen","srv=None and subprocess.Popen").replace("for _ in range(50):","for _ in range(0):")
ns={'__file__':spec.origin}; exec(compile(head,spec.origin,'exec'),ns)
Drive, INIT, state, char = ns['Drive'], ns['INIT'], ns['state'], ns['char']
import subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
PORT=8797; BASE=f'http://localhost:{PORT}/index.html'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
fails=[]; errs=[]
def check(name,cond,info=''):
    print(('PASS ' if cond else 'FAIL ')+name+(' — '+str(info) if info!='' else '')); (None if cond else fails.append(name))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def device(drive,local=None,meta=None,base=None):
        ctx=b.new_context(viewport={'width':1280,'height':900},locale='ko-KR'); ctx.add_init_script(INIT)
        ctx.route('https://www.googleapis.com/**',drive.handle)
        ctx.route('https://accounts.google.com/**',lambda r,q: r.fulfill(status=200,body='/* blocked */'))
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda d:d.accept())
        pg.goto(BASE); pg.wait_for_timeout(150)
        if local is not None: pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(local))
        if meta is not None: pg.evaluate("s=>localStorage.setItem('mapleBossTracker.gdrive',s)",json.dumps(meta))
        if base is not None: pg.evaluate("s=>localStorage.setItem('mapleBossTracker.gdbase',s)",json.dumps(base))
        if local is not None or meta is not None: pg.reload(); pg.wait_for_timeout(400)
        return ctx,pg
    def login(pg):
        pg.click('#gBtn'); pg.wait_for_selector('#gMenu #gdLogin'); pg.click('#gMenu #gdLogin'); pg.wait_for_timeout(700)
        if not pg.is_hidden('#gMenu'): pg.click('#gMenuClose')
    modal=lambda pg: pg.is_visible('#driveModal')
    names=lambda pg: pg.evaluate("S.characters.map(c=>c.name)")
    dnames=lambda d: [c['name'] for c in d.file['content']['data']['characters']]
    def ev(pg,js,wait=5800): pg.evaluate(js); pg.wait_for_timeout(wait)
    def pull(pg): pg.evaluate("gdPull(true)"); pg.wait_for_timeout(700)

    d=Drive(); now=int(time.time()*1000)
    home_local=state(['본캐','부캐1','부캐2'],now-3600e3,key='live_HOME')
    ctxH,H=device(d,local=home_local); login(H)
    check('home: first link uploads to empty drive', d.file is not None and dnames(d)==['본캐','부캐1','부캐2'], dnames(d) if d.file else None)
    ctxP,P=device(d); login(P)
    check('PC방 (empty browser): loads drive, no prompt, key restored', names(P)==['본캐','부캐1','부캐2'] and not modal(P) and P.evaluate("accounts()[0].key")=='live_HOME', names(P))

    # 1) 기기마다 다른 값/자동 갱신 값만 바뀜 → updatedAt 그대로, 드라이브 저장 안 함
    up0=len(d.uploads()); u0=P.evaluate('S.updatedAt')
    ev(P,"()=>{S.theme='dark'; S.activeId='c2'; S.settings.lastSync=Date.now(); S.characters.forEach(c=>{c.sync={at:Date.now(),ok:true,msg:''}; c.image='https://x/'+c.id+'.png'; c.exp={pct:12.3}}); S.settings.accounts[0].status={ok:true,at:Date.now()}; S.period.day='2000-01-01'; save();}")
    check('volatile-only change (theme, selected char, lastSync, sync/image/exp, account status) → no updatedAt bump, no upload', P.evaluate('S.updatedAt')==u0 and len(d.uploads())==up0, (P.evaluate('S.updatedAt')-u0, len(d.uploads())-up0))
    ev(H,"()=>{S.activeId='c3'; S.settings.lastSync=Date.now()+1; S.characters[0].sync={at:Date.now()-5,ok:false,msg:'x'}; save();}",300)

    # 2) 두 기기가 서로 다른 항목을 수정 → 자동 병합, 질문 없음
    ev(P,"()=>{S.characters[1].weekly={lotus:true}; save();}")
    check('PC방 edit pushed', d.file['content']['data']['characters'][1]['weekly']=={'lotus':True})
    ev(H,"()=>{S.characters[0].name='본캐집'; save();}")
    check('home edit while PC방 also saved → auto-merged, no prompt', not modal(H) and H.evaluate('gd.state')=='on', H.evaluate('gd.state'))
    dc=d.file['content']['data']['characters']
    check('drive has both edits', dc[0]['name']=='본캐집' and dc[1]['weekly']=={'lotus':True}, [dc[0]['name'],dc[1]['weekly']])
    check('home has both edits; home device fields kept (activeId c3)', H.evaluate("S.characters[0].name==='본캐집' && S.characters[1].weekly.lotus===true && S.activeId==='c3'"))
    pull(P)
    check('PC방 pulls home edit when tab returns, keeps its own theme/selection', P.evaluate("S.characters[0].name==='본캐집' && S.theme==='dark' && S.activeId==='c2'") and not modal(P))

    # 3) 추가/삭제도 합쳐짐
    ev(P,"()=>{S.characters.push({id:'c9',name:'새캐',level:200,job:'비숍',world:'스카니아',isMain:false,ocid:'',bosses:{},weekly:{},monthly:{},auto:{},sync:{},drops:{}}); save();}")
    ev(H,"()=>{S.characters=S.characters.filter(c=>c.id!=='c3'); save();}")
    check('add on PC방 + delete on home → both applied', H.evaluate("S.characters.map(c=>c.id).join()")=='c1,c2,c9' and dnames(d)==['본캐집','부캐1','새캐'] and not modal(H), H.evaluate("S.characters.map(c=>c.id).join()"))
    pull(P); check('PC방 after pull', P.evaluate("S.characters.map(c=>c.id).join()")=='c1,c2,c9')

    # 4) 진짜 충돌(같은 항목을 양쪽에서 다르게) → 한 번만 질문, 나머지는 합쳐짐, 고른 뒤 다시 안 물음
    ev(P,"()=>{S.characters[1].name='부캐-PC방'; S.characters[2].level=210; save();}")
    ev(H,"()=>{S.characters[1].name='부캐-집'; S.characters[0].weekly={zakum:true}; save();}")
    check('genuine conflict → prompt shown on home', modal(H) and H.evaluate('gd.state')=='conflict')
    txt=H.inner_text('#gdBody'); H.screenshot(path=OUT+'/shot17_conflict.png')
    check('prompt names the conflicting item only', '부캐' in txt and '이름' in txt and '자동으로 합쳐' in txt, txt.replace('\n',' | ')[:200])
    check('drive not overwritten while asking', dnames(d)[1]=='부캐-PC방')
    H.click('#gdUseLocal'); H.wait_for_timeout(700)
    dc=d.file['content']['data']['characters']
    check('chose this PC → name from home, other edits from both kept', dc[1]['name']=='부캐-집' and dc[0]['weekly']=={'zakum':True} and dc[2]['level']==210 and H.evaluate("S.characters[2].level")==210, [dc[1]['name'],dc[0]['weekly'],dc[2]['level']])
    check('state back to on, no modal', H.evaluate('gd.state')=='on' and not modal(H))
    pull(P); check('PC방 pulls the resolution silently (no second prompt)', P.evaluate("S.characters[1].name")=='부캐-집' and not modal(P))
    ev(H,"()=>{S.characters[0].weekly.lotus=true; save();}"); ev(P,"()=>{S.characters[2].weekly={lotus:true}; save();}")
    check('after resolving: further edits on both → no prompt again', not modal(H) and not modal(P) and d.file['content']['data']['characters'][0]['weekly']=={'zakum':True,'lotus':True}, d.file['content']['data']['characters'][0]['weekly'])

    # 5) 다시 열기(새로고침) 양쪽 → 질문 없음
    H.reload(); H.wait_for_timeout(900); P.reload(); P.wait_for_timeout(900)
    check('reload both devices → no prompt', not modal(H) and not modal(P) and H.evaluate('gd.state')=='on' and P.evaluate('gd.state')=='on', (H.evaluate('gd.state'),P.evaluate('gd.state')))
    check('both devices identical content', H.evaluate("gdSig(S)")==P.evaluate("gdSig(S)"))
    ctxH.close(); ctxP.close()

    # 6) 예전 버전으로 동기화하던 PC(메타에 시각만, base 내용 없음): 양쪽 다 바뀜 + 자동 갱신 값 차이 → 묻지 않고 합침
    d=Drive(); t0=1760000000000
    drv=state(['A','B'],t0+5000); drv['characters'][0]['weekly']={'lotus':True}; drv['characters'][1]['sync']={'at':t0+4000,'ok':True}; drv['activeId']='c2'
    d.seed(drv,t0+5000,keys=True)
    loc=state(['A','B'],t0+9000); loc['characters'][1]['weekly']={'zakum':True}; loc['characters'][0]['image']='https://x/a.png'; loc['settings']['lastSync']=t0+8000
    ctx,pg=device(d,local=loc,meta={'on':True,'base':t0,'fileId':'F1'}); pg.wait_for_timeout(900)
    check('legacy meta (both changed) → auto-merged, no prompt', not modal(pg) and pg.evaluate('gd.state')=='on', pg.evaluate('gd.state'))
    dc=d.file['content']['data']['characters']
    check('legacy merge keeps both sides', dc[0]['weekly']=={'lotus':True} and dc[1]['weekly']=={'zakum':True} and pg.evaluate("S.characters[0].weekly.lotus&&S.characters[1].weekly.zakum"), [dc[0]['weekly'],dc[1]['weekly']])
    check('base snapshot saved for next time', pg.evaluate("!!localStorage.getItem('mapleBossTracker.gdbase')"))
    ctx.close()

    # 7) 이미 같은 내용인데 자동 갱신 값만 다름 → 질문 없음, 업로드 없음
    d=Drive(); same=state(['X'],t0); d.seed(json.loads(json.dumps(same)),t0+1,keys=False)
    loc=json.loads(json.dumps(same)); loc['updatedAt']=t0+777; loc['activeId']=None; loc['characters'][0]['sync']={'at':t0+9,'ok':True}; loc['theme']='dark'
    ctx,pg=device(d,local=loc,meta={'on':True,'base':t0,'fileId':'F1'}); pg.wait_for_timeout(900)
    check('same content, only volatile differs → no prompt', not modal(pg) and pg.evaluate('gd.state')=='on')
    ctx.close()

    # 8) 다른 기기가 지난 주 데이터(주간 체크 있음)를 올려 둠 → 합칠 때 이번 주 체크로 넘어오지 않고 기록으로 감
    d=Drive(); old=state(['W'],t0); old['characters'][0]['weekly']={'lotus':True}; old['period']={'week':'2026-09-24','day':'2026-09-25','month':'2026-09'}
    d.seed(old,t0,keys=False)
    ctx,pg=device(d,local=state(['W'],t0),meta={'on':True,'base':t0-1,'fileId':'F1'}); pg.wait_for_timeout(900)
    check("other device's last-week checks are archived, not merged into this week", pg.evaluate("!S.characters[0].weekly.lotus && S.history.some(h=>h.week==='2026-09-24')") and not modal(pg), pg.evaluate("[S.characters[0].weekly,S.history.map(h=>h.week)]"))
    ctx.close()
    b.close()
srv.terminate()
check('no page errors', not errs, errs[:3])
print('FAILS',fails)
sys.exit(1 if fails else 0)
