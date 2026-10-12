# b69: 로그아웃(공용 PC) → 남은 변경 먼저 서버 저장 → 서버 세션 삭제 → 이 PC 앱 데이터 전부 삭제(다른 탭도) → 새로고침해도 빈 상태 / 세션 없는 남은 데이터·잘못된 세션 → 시작할 때 삭제 / 본계정 키로 다시 → 복원
import os, sys, json, subprocess, time, urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed'); print('FAILS: []'); sys.exit(0)
PORT, WP, NP = 8837, 8818, 8819
API=f'http://127.0.0.1:{WP}'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
KA,KF,KG,KI='live_KEY_A_0123456789abcdef','live_KEY_F_0123456789abcdef','live_KEY_G_0123456789abcdef','live_KEY_I_0123456789abcdef'
BKA='live_BK_A_0123456789abcdefg'
RESET='b64-2026-10-12'
def ch(id,name,acc,ocid):
    return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','ocid':ocid,'accId':acc,'isMain':id=='c1','image':'','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],
  'characters':[ch('c1','단풍용사','a1','o-acc-A'),ch('c2','부캐F','a2','o-acc-F'),ch('c3','부캐G','a3','o-acc-G')],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KA,'bk':BKA,'bkLabel':'본 예비'},{'id':'a2','label':'부계정F','key':KF},{'id':'a3','label':'부계정G','key':KG}],'lastSync':int(time.time()*1000)}}
def nexon(route):  # 브라우저의 넥슨 호출 → 모의 목록 (character/list 만)
    k=route.request.headers.get('x-nxopen-api-key',''); v=MN.KEYS.get(k)
    if '/character/list' not in route.request.url or not isinstance(v,list): return route.fulfill(status=400,content_type='application/json',body=json.dumps({'error':{'name':'OPENAPI0006','message':'x'}}))
    body={'account_list':[{'account_id':a,'character_list':[{'ocid':'o-'+a,'character_name':'캐릭'+a[-1],'world_name':'스카니아','character_class':'히어로','character_level':280}]} for a in v]}
    route.fulfill(status=200,content_type='application/json',body=json.dumps(body))
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
def mkctx(b):
    ctx=b.new_context(viewport={'width':1280,'height':800},locale='ko-KR')
    ctx.route('https://open.api.nexon.com/**',nexon); ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg=ctx.new_page(); pg.on('dialog',lambda d:d.accept()); pg.on('pageerror',lambda e:errs.append(str(e)))
    return ctx,pg
st=lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')||'{\"characters\":[],\"settings\":{\"accounts\":[]}}')")
keyset=lambda s: sorted(x for a in s['settings']['accounts'] for x in (a.get('key'),a.get('bk')) if x)
def wait_on(pg,t=15000,keep=False):
    pg.wait_for_function("gd.state==='on'&&!gd.busy&&!gd.timer",timeout=t); pg.wait_for_timeout(200)
    if not keep: pg.evaluate("closeImport()")
def invite(pg): pass  # b67: 초대 비밀번호 폐지 (호환용 빈 함수)
def login(pg,key):  # b67: 캐릭터 추가 창의 '본계정 API 키 등록'으로 로그인
    if not pg.evaluate("document.querySelector('#importModal').classList.contains('show')"): pg.evaluate("openAdd()")
    pg.wait_for_selector('#svMainKey'); pg.fill('#svMainKey',key); pg.click('#svMainBtn')
def jpost(path,body,tok=None):
    r=urllib.request.Request(API+path,data=json.dumps(body).encode(),method=body.pop('_m','POST') if isinstance(body,dict) and '_m' in body else 'POST',headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})})
    try: return json.loads(urllib.request.urlopen(r).read())
    except urllib.error.HTTPError as e: return json.loads(e.read())
APPKEYS="Object.keys(localStorage).filter(k=>k.startsWith('mapleBossTracker.')&&!['mapleBossTracker.syncApi','mapleBossTracker.keyReset','mapleBossTracker.officialPrices','mapleBossTracker.v1'].includes(k))"
def fresh_state(pg):  # 처음 온 사람과 같은 상태
    return pg.evaluate("[S.characters.length, accounts().length, !!svTok(), (JSON.parse(localStorage.getItem('mapleBossTracker.v1')||'{}').characters||[]).length]")==[0,0,False,0] and pg.evaluate(APPKEYS)==[]
def srvnames():
    return [[c.get('name') for c in json.loads(r['data']).get('characters',[])] for r in dev.sql("SELECT data FROM state")]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    c1,p1=mkctx(b); p1.goto(URL); p1.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); p1.reload(); p1.wait_for_timeout(500)
    login(p1,KA); wait_on(p1)
    p1.evaluate("openAdd()"); p1.wait_for_selector('#newAccKey'); p1.evaluate("()=>{const i=document.querySelector('#newAccLabel'); if(i&&!i.value) i.value='부계정'}"); p1.fill('#newAccKey',KF); p1.click('#newAccBtn'); p1.wait_for_function("accounts().some(a=>a.key==='%s')"%KF,timeout=15000); p1.evaluate("closeImport()")
    p1.evaluate("S.characters.push({id:'c1',name:'단풍용사',level:280,job:'히어로',world:'스카니아',ocid:'o-acc-A',accId:accounts()[0].id,isMain:true,image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});save();render()")
    p1.evaluate("svSaveNow()"); wait_on(p1)
    p2=c1.new_page(); p2.on('pageerror',lambda e:errs.append(str(e))); p2.goto(URL); p2.wait_for_timeout(1500)
    check('2nd tab shows the logged-in data', p2.evaluate("S.characters.length")==1)
    # 저장 안 한 변경 (자동 저장 대기 중) 을 만든 직후 로그아웃
    p1.evaluate("S.characters[0].name='단풍용사2';save();render()")
    tok=p1.evaluate("svTok()"); n_sess=len(dev.sql("SELECT 1 FROM sessions"))
    p1.evaluate("gdMenu(true)"); p1.click('#gdLogout'); p1.wait_for_function("!svTok()",timeout=15000); p1.wait_for_timeout(1500)
    check('logout pushed pending local change to server first', srvnames()==[['단풍용사2']], srvnames())
    st_code=urllib.request.Request(API+'/api/state',headers={'Authorization':'Bearer '+tok})
    try: urllib.request.urlopen(st_code); code=200
    except urllib.error.HTTPError as e: code=e.code
    check('server session invalidated (old token → 401), one session fewer', code==401 and len(dev.sql("SELECT 1 FROM sessions"))==n_sess-1, (code,n_sess))
    check('after logout: memory + localStorage fresh (no characters, keys, token, app keys)', fresh_state(p1), (p1.evaluate("[S.characters.length, accounts().length]"), p1.evaluate(APPKEYS)))
    check('b73: no toast after manual logout', not p1.evaluate("document.querySelector('#toast').classList.contains('show')"), p1.inner_text('#toast'))
    p1.screenshot(path='/workspace/maple-boss-tracker/oct12k_b73_test_logout.png')
    check('sessionStorage has no app keys', p1.evaluate("Object.keys(sessionStorage).filter(k=>k.startsWith('mapleBossTracker.'))")==[])
    p2.wait_for_timeout(1500)
    check('other tab reloaded to fresh state too', fresh_state(p2), p2.evaluate("S.characters.length"))
    p1.reload(); p1.wait_for_timeout(1500)
    check('b73: no toast after reload into empty state', not p1.evaluate("document.querySelector('#toast').classList.contains('show')"), p1.inner_text('#toast'))
    check('reload after logout → still fresh, empty dashboard', fresh_state(p1) and p1.is_visible('.empty'))
    p1.click('#addCharBtn'); p1.wait_for_selector('#svMainKey')
    check("'+ 추가' → main-key field only", p1.is_visible('#svMainKey') and not p1.is_visible('#accList') and not p1.is_visible('#newAccKey'))
    p1.evaluate("closeImport()")
    # 세션 없이 남은 예전 데이터 → 시작할 때 지움
    p1.evaluate("()=>{localStorage.setItem('mapleBossTracker.v1',JSON.stringify({version:5,characters:[{id:'x',name:'남은캐릭',level:200,job:'히어로',world:'스카니아',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}],history:[],settings:{accounts:[{id:'a1',label:'본계정',key:'%s'}]}}));localStorage.setItem('mapleBossTracker.svUser','abc')}"%KA)
    p1.reload(); p1.wait_for_timeout(1500)
    check('leftover local data without a session → wiped at load', fresh_state(p1), p1.evaluate("S.characters.map(c=>c.name)"))
    # 잘못된(만료된) 세션 + 로컬 데이터 → 서버 401 → 지움
    p1.evaluate("()=>{localStorage.setItem('mapleBossTracker.v1',JSON.stringify({version:5,characters:[{id:'x',name:'남은캐릭',level:200,job:'히어로',world:'스카니아',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}],history:[],settings:{accounts:[]}}));localStorage.setItem('mapleBossTracker.svToken','%s');localStorage.setItem('mapleBossTracker.svmeta',JSON.stringify({on:true}))}"%tok)
    p1.reload(); p1.wait_for_function("!svTok()",timeout=15000); p1.wait_for_timeout(800)
    check('invalid session at load → server 401 → local data wiped, re-login message', fresh_state(p1) and '로그인' in p1.inner_text('#gBtn'), (p1.evaluate("S.characters.map(c=>c.name)"),p1.evaluate(APPKEYS)))
    # 본계정 키로 다시 → 데이터·부계정 키 복원
    login(p1,KA); wait_on(p1); p1.wait_for_function("accounts().some(a=>a.key==='%s')"%KF,timeout=10000)
    s1=st(p1); check('re-login with main key → data + alt key restored from server', [c['id'] for c in s1['characters']]==['c1'] and keyset(s1)==sorted([KA,KF]), (keyset(s1),[c['name'] for c in s1['characters']]))
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
