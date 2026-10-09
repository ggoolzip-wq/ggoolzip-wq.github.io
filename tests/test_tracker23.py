# 동기화 서버 모드(기능 플래그) — 브라우저 2대 + wrangler dev(로컬 D1) + 넥슨 모의 서버 (2026-10-10)
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed'); print('FAILS: []'); sys.exit(0)
PORT, WP, NP = 8794, 8772, 8773
API=f'http://127.0.0.1:{WP}'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
KA='live_KEY_A_0123456789abcdef'
def ch(id,name):
    return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'a1','isMain':id=='c1','image':'','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[ch('c1','단풍용사'),ch('c2','불독메이지')],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KA}],'lastSync':int(time.time()*1000)}}
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
puts=[]; popups=[]
def mkctx(b):
    ctx=b.new_context(viewport={'width':1280,'height':800},locale='ko-KR')
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort()); ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
    def onreq(rq):
        if rq.url.startswith(API+'/api/') and rq.method in ('PUT','POST'): puts.append((rq.method,rq.url,rq.post_data or ''))
    ctx.on('request',onreq)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('popup',lambda p:popups.append(p.url))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'net::' not in m.text else None)
    return ctx,pg
st=lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1'))")
server_state=lambda: dev.sql("SELECT rev, data FROM state")
def wait_on(pg,t=15000): pg.wait_for_function("gd.state==='on'&&!gd.busy&&!gd.timer",timeout=t); pg.wait_for_timeout(150)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    # 0) 플래그 꺼짐 = 기존 구글 드라이브 그대로
    ctx0,p0=mkctx(b); p0.goto(URL); p0.wait_for_timeout(300)
    check('flag off (default): Google Drive mode unchanged', p0.evaluate("SV_ON")=='' and '구글' in p0.inner_text('#gBtn'), p0.inner_text('#gBtn')); ctx0.close()
    # 1) 기기 A: 등록된 키로 로그인 → 이 PC 데이터 첫 저장
    ca,pa=mkctx(b); pa.goto(URL)
    pa.evaluate("([p,api])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p));localStorage.setItem('mapleBossTracker.syncApi',api)}",[PRESET,API]); pa.reload(); pa.wait_for_timeout(400)
    check('flag on: header ☁ 로그인, no auto login, no popup', pa.inner_text('#gBtn')=='☁ 로그인' and not popups and not pa.evaluate("svTok()"), pa.inner_text('#gBtn'))
    pa.click('#gBtn'); pa.wait_for_selector('#gMenu:not([hidden]) #svInvite')
    check('first: invite password asked (no key buttons yet)', pa.locator('[data-svlogin]').count()==0)
    pa.fill('#svInvite','wrong'); pa.press('#svInvite','Enter'); pa.wait_for_timeout(800)
    check('wrong invite → error shown, still asking', pa.locator('#svInvite').count()==1 and '맞지 않' in pa.inner_text('#gMenu'), pa.inner_text('#gMenu')[:200])
    pa.fill('#svInvite',cf_dev.TEST_PASS); pa.click('#svInviteBtn'); pa.wait_for_selector('#gMenu:not([hidden]) [data-svlogin="a1"]')
    check('invite ok → device ticket stored, key login shown', bool(pa.evaluate("svDev()")))
    check('menu: login with stored key button, key not shown', '본계정 키로 로그인' in pa.inner_text('#gMenu') and KA not in pa.inner_text('#gMenu') and KA not in pa.content().split('<script')[0])
    shot_path=os.path.join(OUT,'sv_login_menu.png'); pa.locator('#gMenu').screenshot(path=shot_path)
    if SHOTDIR: shutil.copy(shot_path,SHOTDIR)
    pa.click('[data-svlogin="a1"]'); wait_on(pa)
    s=server_state(); d=json.loads(s[0]['data']) if s else {}
    check('A login → local data uploaded (rev 1, 2 chars)', s and s[0]['rev']==1 and len(d.get('characters',[]))==2, s and s[0]['rev'])
    check('server copy has no API key; account has ah', KA not in s[0]['data'] and d['settings']['accounts'][0].get('ah') and 'key' not in d['settings']['accounts'][0], d.get('settings'))
    check('A local keeps its key + ah', st(pa)['settings']['accounts'][0]['key']==KA and st(pa)['settings']['accounts'][0].get('ah'))
    check('no raw key in any PUT body (login POST carries it once)', all(KA not in body for m,u,body in puts if m=='PUT') and any(u.endswith('/api/login') and KA in body for m,u,body in puts))
    check('A header shows saved state', '저장' in pa.inner_text('#gBtn') or '동기화됨' in pa.inner_text('#gBtn'), pa.inner_text('#gBtn'))
    # 2) 기기 B (빈 PC): 키 입력 → 내려받기 + 그 키 자동 채움
    cb,pb=mkctx(b); pb.goto(URL)
    pb.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); pb.reload(); pb.wait_for_timeout(300)
    pb.click('#gBtn'); pb.wait_for_selector('#svInvite'); pb.fill('#svInvite',cf_dev.TEST_PASS); pb.press('#svInvite','Enter'); pb.wait_for_selector('#svKey'); pb.fill('#svKey',KA); pb.press('#svKey','Enter'); wait_on(pb)
    sb=st(pb)
    check('B (empty PC) login → pulled 2 chars, key filled for that account', len(sb['characters'])==2 and sb['settings']['accounts'][0].get('key')==KA, [a.get('key','')[:8] for a in sb['settings']['accounts']])
    # 3) B 에서 바꿈 → 자동 저장(5초) → A 가 당겨옴
    pb.evaluate("S.characters.find(c=>c.id==='c2').name='불독메이지B'; save()"); pb.wait_for_timeout(5600); wait_on(pb)
    check('B edit auto-saved (rev 2)', server_state()[0]['rev']==2, server_state()[0]['rev'])
    pa.evaluate("gd.pulledAt=0; gdPull(true)"); pa.wait_for_timeout(1200); wait_on(pa)
    check('A pulls B change', [c['name'] for c in st(pa)['characters']]==['단풍용사','불독메이지B'], [c['name'] for c in st(pa)['characters']])
    # 4) 동시 수정: A·B 가 서로 다른 항목을 바꾸고 B 는 오래된 rev 로 저장 → 409 → 3-way 병합
    pa.evaluate("S.characters.find(c=>c.id==='c1').weekly={lucid:true}; save()"); pa.evaluate("gdPush()"); wait_on(pa)
    r0=server_state()[0]['rev']
    pb.evaluate("clearTimeout(gd.timer); S.characters.find(c=>c.id==='c2').bosses.lucid.party=2; save(); clearTimeout(gd.timer); gd.timer=null")
    pb.evaluate("(async()=>{ await gdWrite(); })()"); pb.wait_for_timeout(2500); wait_on(pb)
    d=json.loads(server_state()[0]['data']); c1=[c for c in d['characters'] if c['id']=='c1'][0]; c2=[c for c in d['characters'] if c['id']=='c2'][0]
    check('stale write → 409 → merged: both A and B changes on server', c1['weekly'].get('lucid') and c2['bosses']['lucid']['party']==2 and server_state()[0]['rev']>r0, (c1['weekly'],c2['bosses']))
    check('no conflict question for different fields', not pb.is_visible('#driveModal'))
    # 5) 진짜 충돌: 같은 값을 양쪽에서 다르게 → 한 번 질문
    pa.evaluate("gd.pulledAt=0; gdPull(true)"); pa.wait_for_timeout(1200); wait_on(pa)
    pa.evaluate("S.characters.find(c=>c.id==='c1').name='A이름'; save(); gdPush()"); wait_on(pa)
    pb.evaluate("clearTimeout(gd.timer); S.characters.find(c=>c.id==='c1').name='B이름'; save(); clearTimeout(gd.timer); gd.timer=null; gdWrite()"); pb.wait_for_timeout(2000)
    check('same field changed on both → asks once (서버 vs 이 PC)', pb.is_visible('#driveModal') and '서버' in pb.inner_text('#driveModal'), pb.evaluate("gd.state"))
    pb.click('#gdUseLocal'); pb.wait_for_timeout(1500); wait_on(pb)
    check('choose 이 PC → server has B이름', [c['name'] for c in json.loads(server_state()[0]['data'])['characters']][0]=='B이름')
    # 6) 새로고침 → 토큰 재사용 (로그인 다시 안 함)
    n_login=sum(1 for m,u,_ in puts if u.endswith('/api/login'))
    pa.reload(); pa.wait_for_timeout(300); wait_on(pa)
    check('reload reuses session token (no new login)', sum(1 for m,u,_ in puts if u.endswith('/api/login'))==n_login and pa.evaluate("gd.state")=='on')
    # 7) 구글 드라이브에서 가져오기 (드라이브 함수는 가짜로 바꿔 끼움)
    pa.evaluate("""()=>{ window.driveToken=async()=> 'fake'; window.driveFind=async()=>({id:'f1'});
      window.driveRead=async()=>({app:'maple-boss-tracker',updatedAt:1,withKeys:true,data:{version:5,characters:[{id:'c9',name:'드라이브캐릭',level:270,job:'비숍',world:'스카니아',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}],history:[],monthHistory:[],worldOrder:[],settings:{accounts:[{id:'a1',label:'본계정',key:'live_KEY_A_0123456789abcdef'}]}}}); }""")
    pa.click('#gBtn'); pa.wait_for_selector('#svImportDrive', timeout=3000) if pa.evaluate("driveUsable()") else None
    if pa.evaluate("driveUsable()"):
        pa.click('#svImportDrive'); pa.wait_for_timeout(1500); wait_on(pa)
        names=[c['name'] for c in json.loads(server_state()[0]['data'])['characters']]
        check('import from Drive merges into local + saves to server', '드라이브캐릭' in names and 'B이름' in names and [c['name'] for c in st(pa)['characters']].count('드라이브캐릭')==1, names)
    else: check('drive import button needs a Google client id (skipped on this origin)', True)
    # 8) 로그아웃
    oldtok=pa.evaluate("svTok()")
    pa.click('#gBtn') if pa.is_hidden('#gMenu') else None; pa.wait_for_selector('#gdLogout'); pa.click('#gdLogout'); pa.wait_for_timeout(800)
    rq=urllib.request.Request(API+'/api/state',headers={'Authorization':'Bearer '+oldtok})
    try: urllib.request.urlopen(rq); code=200
    except urllib.error.HTTPError as e: code=e.code
    check('logout: token removed, server session dead, local data kept, header ☁ 로그인', not pa.evaluate("svTok()") and code==401 and len(st(pa)['characters'])>=2 and pa.inner_text('#gBtn')=='☁ 로그인', (code,pa.inner_text('#gBtn')))
    check('B still logged in (other device unaffected)', pb.evaluate("!!svTok()"))
    pa.click('#gBtn') if pa.is_hidden('#gMenu') else None; pa.wait_for_timeout(200)
    check('after logout: device ticket kept → key login directly (no invite again)', pa.locator('#gMenu [data-svlogin]').count()>0 and pa.locator('#svInvite').count()==0)
    check('never opened a popup', not popups, popups)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate(); dev.stop(); ms.shutdown()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
