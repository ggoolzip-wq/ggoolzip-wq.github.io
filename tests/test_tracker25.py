# 사용자 바꿈: 다른 사람 키로 로그인해도 이 PC 데이터를 올리지/합치지 않음 + 로그아웃 시 비움 + 입장 화면 — 브라우저 2대 + wrangler dev(로컬 D1) + 넥슨 모의 서버 (2026-10-10)
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
PORT, WP, NP = 8796, 8776, 8777
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
puts=[]; popups=[]; dialogs=[]; ANSWER=[True]
def mkctx(b):
    ctx=b.new_context(viewport={'width':1280,'height':800},locale='ko-KR')
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort()); ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
    def onreq(rq):
        if rq.url.startswith(API+'/api/') and rq.method in ('PUT','POST'): puts.append((rq.method,rq.url,rq.post_data or ''))
    ctx.on('request',onreq)
    pg=ctx.new_page(); pg.on('dialog',lambda d:(dialogs.append(d.message),(d.accept() if ANSWER[0] else d.dismiss()))); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('popup',lambda p:popups.append(p.url))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'net::' not in m.text else None)
    return ctx,pg
st=lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1'))")
server_state=lambda: dev.sql("SELECT rev, data FROM state")
def wait_on(pg,t=15000): pg.wait_for_function("gd.state==='on'&&!gd.busy&&!gd.timer",timeout=t); pg.wait_for_timeout(150)
KF='live_KEY_F_0123456789abcdef'
def invite(pg):
    pg.wait_for_selector('#svGate #svInvite'); pg.fill('#svGate #svInvite',cf_dev.TEST_PASS); pg.click('#svGate #svInviteBtn'); pg.wait_for_selector('#svGate #svKey')
def shot(pg,name):
    pg.evaluate('gdMenu(true)'); pg.wait_for_timeout(200); pth=os.path.join(OUT,name); pg.locator('#gMenu').screenshot(path=pth)
    if SHOTDIR: shutil.copy(pth,SHOTDIR)
KB='live_KEY_B_0123456789abcdef'
def chars_of(u):
    rows=dev.sql("SELECT s.data FROM state s JOIN accounts a ON a.user_id=s.user_id WHERE a.acct_hash='%s'"%u)
    return [c['name'] for c in json.loads(rows[0]['data'])['characters']] if rows else None
def login(pg,key):
    pg.wait_for_selector('#svGate #svKey'); pg.fill('#svGate #svKey',key); pg.press('#svGate #svKey','Enter'); wait_on(pg)
def nusers(): return dev.sql("SELECT COUNT(*) n FROM users")[0]['n']
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ca,pa=mkctx(b); pa.goto(URL)
    pa.evaluate("([p,api])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p));localStorage.setItem('mapleBossTracker.syncApi',api)}",[PRESET,API]); pa.reload(); pa.wait_for_timeout(400)
    check('gate shown before any content', pa.is_visible('#svGate') and pa.evaluate("document.elementFromPoint(640,400).closest('#svGate')!==null"))
    shot(pa,'x') if False else None
    pth=os.path.join(OUT,'sv_entry_gate.png'); pa.screenshot(path=pth); SHOTDIR and shutil.copy(pth,SHOTDIR)
    def gshot(n): pth=os.path.join(OUT,n); pa.screenshot(path=pth); SHOTDIR and shutil.copy(pth,SHOTDIR)
    pa.evaluate("localStorage.setItem('mapleBossTracker.v1',JSON.stringify({...JSON.parse(localStorage.getItem('mapleBossTracker.v1')),theme:'dark'}))")
    gshot('gate_1_invite.png'); invite(pa); gshot('gate_2_main_key.png')
    check('step 2: still blank (content hidden), main key box', pa.evaluate("document.documentElement.classList.contains('gated')") and pa.is_visible('#svGate #svKey'))
    # 1) 이 기기 첫 로그인 (A) → 질문 → 예 → 올림
    login(pa,KA); ah_a=st(pa)['settings']['accounts'][0]['ah']
    gshot('gate_3_site.png'); check('step 3: site visible after main-key login', pa.locator('#svGate').count()==0 and pa.is_visible('#charList'))
    # 세션이 있는 기기: 새로고침하면 바로 사이트
    pa.reload(); pa.wait_for_timeout(800); check('valid session → reload goes straight to site', pa.locator('#svGate').count()==0, pa.locator('#svGate').count())
    check('first login: asked "이 PC 데이터를 이 계정으로 올릴까요?" and uploaded on yes', any('이 계정으로 올릴까요' in m for m in dialogs) and chars_of(ah_a)==['단풍용사','불독메이지'], (dialogs,chars_of(ah_a)))
    # 2) 로그아웃 → 비움 → B 로그인 → A 데이터 안 올라감
    pa.evaluate('gdMenu(true)'); pa.click('#gdLogout'); pa.wait_for_timeout(800)
    check('logout clears local boss data', st(pa)['characters']==[] and not st(pa)['settings'].get('accounts'))
    n=len(dialogs); login(pa,KB); ah_b=st(pa)['settings']['accounts'][0]['ah']
    check('B after logout: no question, B data empty, A untouched', len(dialogs)==n and st(pa)['characters']==[] and chars_of(ah_b) in (None,[]) and chars_of(ah_a)==['단풍용사','불독메이지'], (chars_of(ah_b),dialogs[n:]))
    # 3) 로그아웃 없이 사용자 바꿈 (세션 토큰만 사라진 경우) → 이 PC(B) 데이터를 A 에 합치지 않음
    pa.evaluate("S.characters.push({...S.characters[0]||{},id:'cb',name:'B캐릭',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});save();svSaveNow()"); pa.wait_for_timeout(1500); wait_on(pa)
    check('B saved its own char', chars_of(ah_b)==['B캐릭'], chars_of(ah_b))
    pa.evaluate("localStorage.removeItem('mapleBossTracker.svToken');gdMeta={};gdSaveMeta();gdSet('off');svGate()")
    n=len(dialogs); login(pa,KA)
    check('switch B→A without logout: local B data wiped, A data loaded, nothing merged', [c['name'] for c in st(pa)['characters']]==['단풍용사','불독메이지'] and chars_of(ah_a)==['단풍용사','불독메이지'] and chars_of(ah_b)==['B캐릭'] and len(dialogs)==n, ([c['name'] for c in st(pa)['characters']],chars_of(ah_a)))
    check('2 users total, A and B separate', nusers()==2, nusers())
    # 4) 새 기기, 이 PC 데이터 있음 → 질문에 [취소] → 지우고 서버(A) 데이터만
    cc,pc=mkctx(b); pc.goto(URL); pc.evaluate("([p,api])=>{localStorage.clear();p.characters=[{...p.characters[0],id:'z',name:'남의캐릭'}];localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p));localStorage.setItem('mapleBossTracker.syncApi',api)}",[PRESET,API]); pc.reload(); pc.wait_for_timeout(400)
    invite(pc); ANSWER[0]=False; n=len(dialogs); login(pc,KA); ANSWER[0]=True
    check('first login + cancel → local wiped, server A data only (no merge)', len(dialogs)==n+1 and '합칠까요' in dialogs[-1] and [c['name'] for c in st(pc)['characters']]==['단풍용사','불독메이지'] and chars_of(ah_a)==['단풍용사','불독메이지'], ([c['name'] for c in st(pc)['characters']],dialogs[n:]))
    # 헤더: 로그인 중이면 [로그아웃]만, 저장 실패 시 작은 경고, 누르면 확인 없이 로그아웃 → 대표 키 화면
    check('header shows only 로그아웃 when logged in', pc.text_content('#gBtn')=='로그아웃' and pc.locator('#svWarn:visible').count()==0, pc.text_content('#gBtn'))
    pth=os.path.join(OUT,'header_logout.png'); pc.screenshot(path=pth,clip={'x':0,'y':0,'width':1280,'height':120}); SHOTDIR and shutil.copy(pth,SHOTDIR)
    puts_n=len([x for x in puts if x[1].endswith('/api/state')])
    pc.evaluate("S.characters[0].name='바뀐이름';save()"); pc.wait_for_timeout(6500)
    check('no autosave in sync mode (no PUT), header still only 로그아웃', len([x for x in puts if x[1].endswith('/api/state')])==puts_n and pc.text_content('#gBtn')=='로그아웃' and pc.evaluate('svUnsaved()'))
    check('beforeunload warns when unsaved', pc.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented})()"))
    pc.click('#gBtn'); pc.wait_for_selector('#svAsk')
    check('logout with unsaved changes → warning with 저장 후 로그아웃', '로그아웃하면 사라져요' in pc.inner_text('#svAsk') and pc.locator('#svAsk [data-k=save]').count()==1)
    pth=os.path.join(OUT,'logout_unsaved.png'); pc.screenshot(path=pth); SHOTDIR and shutil.copy(pth,SHOTDIR)
    pc.click('#svAsk [data-k=cancel]'); pc.wait_for_timeout(300); check('cancel keeps login + data', pc.evaluate('!!svTok()') and st(pc)['characters'][0]['name']=='바뀐이름')
    pc.route(API+'/api/state',lambda r: r.fulfill(status=500,body='{"error":"server","message":"서버 오류"}') if r.request.method=='PUT' else r.continue_())
    pc.click('#gBtn'); pc.click('#svAsk [data-k=save]'); pc.wait_for_timeout(2000)
    check('save fails → stays logged in, small warning chip', pc.evaluate('!!svTok()') and pc.is_visible('#svWarn') and pc.text_content('#gBtn')=='로그아웃', pc.evaluate('gd.state'))
    pc.unroute(API+'/api/state'); n=len(dialogs)
    pc.click('#gBtn'); pc.click('#svAsk [data-k=save]'); pc.wait_for_selector('#svGate #svKey',timeout=8000)
    check('저장 후 로그아웃 → server has the change, local cleared, main-key gate', chars_of(ah_a)[0]=='바뀐이름' and st(pc)['characters']==[], chars_of(ah_a))
    login(pc,KA); n=len(dialogs); pc.click('#gBtn'); pc.wait_for_selector('#svGate #svKey',timeout=8000)
    check('logout with nothing unsaved → no prompt', pc.locator('#svAsk').count()==0 and len(dialogs)==n)
    check('no google popup, no page errors', not popups and not errs, (popups,errs[:3]))
    b.close()
finally:
    srv.terminate(); dev.stop(); ms.shutdown()
print('FAILS:',fails)
