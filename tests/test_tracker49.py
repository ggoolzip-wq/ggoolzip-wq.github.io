# b64: 등록된 API 키 전체 초기화(기기마다 1번, 키만 비움·캐릭터 그대로) → 대표 키 로그인 → 부계정 키 다시 추가하면 예전 계정 칸에 재연결
#      / 다른 데이터(캐릭터 있음)에 묶인 키 추가 → '이미 등록된 부계정 API입니다.' 빨간 글, 저장 안 함 / 집 PC(예전 키) → 비워진 뒤 대표 키로 복원
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
PORT, WP, NP = 8807, 8788, 8789
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
st=lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1'))")
keyset=lambda s: sorted(x for a in s['settings']['accounts'] for x in (a.get('key'),a.get('bk')) if x)
def wait_on(pg,t=15000): pg.wait_for_function("gd.state==='on'&&!gd.busy&&!gd.timer",timeout=t); pg.wait_for_timeout(200); pg.evaluate("closeImport()")
def invite(pg): pass  # b67: 초대 비밀번호 폐지 (호환용 빈 함수)
def login(pg,key):  # b67: 캐릭터 추가 창의 '본계정 API 키 등록'으로 로그인
    if not pg.evaluate("document.querySelector('#importModal').classList.contains('show')"): pg.evaluate("openAdd()")
    pg.wait_for_selector('#svMainKey'); pg.fill('#svMainKey',key); pg.click('#svMainBtn')
def jpost(path,body,tok=None):
    r=urllib.request.Request(API+path,data=json.dumps(body).encode(),method=body.pop('_m','POST') if isinstance(body,dict) and '_m' in body else 'POST',headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})})
    try: return json.loads(urllib.request.urlopen(r).read())
    except urllib.error.HTTPError as e: return json.loads(e.read())
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    # 다른 사람 데이터 I (캐릭터 있음)
    tI=jpost('/api/login',{'key':KI})['token']
    rq=urllib.request.Request(API+'/api/state',data=json.dumps({'baseRev':0,'updatedAt':1,'data':{'characters':[{'id':'x','name':'남의캐릭'}]}}).encode(),method='PUT',headers={'Content-Type':'application/json','Authorization':'Bearer '+tI}); urllib.request.urlopen(rq)
    # ---- 집 PC(H): 키 전부 있는 예전 상태 (초기화 전) → 로그인·금고 보관 ----
    ch_,ph=mkctx(b); ph.goto(URL)
    ph.evaluate("([p,api,r])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p));localStorage.setItem('mapleBossTracker.keyReset',r);localStorage.setItem('mapleBossTracker.syncApi',api)}",[PRESET,API,RESET]); ph.reload(); ph.wait_for_timeout(400)
    invite(ph); login(ph,KA); wait_on(ph)
    ph.evaluate("()=>{S.updatedAt=Date.now();svSaveNow()}"); ph.wait_for_function("localStorage.getItem('mapleBossTracker.svSubSig')===svSubSig()",timeout=20000); wait_on(ph)
    check('준비: 금고·등록부에 부계정 2 + 예비 1', len(dev.sql("SELECT * FROM keyvault2"))==1 and len(dev.sql("SELECT * FROM keyreg"))==3, dev.sql("SELECT kind FROM keyreg"))
    # ---- 서버 초기화 (운영자가 D1 에서 한 것과 같음) ----
    before=dev.sql("SELECT rev,data FROM state ORDER BY user_id")
    dev.sql("DELETE FROM keyvault2"); dev.sql("DELETE FROM keyvault"); dev.sql("DELETE FROM keyreg")
    # ---- PC방(P): 이미 로그인돼 있던 기기 → 새 버전 처음 열면 키만 비우고 입장 화면 ----
    cp,pp=mkctx(b); pp.goto(URL)
    dump=ph.evaluate("JSON.stringify({...localStorage})")  # PC방 = 예전 버전으로 로그인해 둔 기기 (키·세션·금고 표시 그대로, 초기화 표시 없음)
    pp.evaluate("d=>{localStorage.clear();const o=JSON.parse(d);for(const k in o) localStorage.setItem(k,o[k]);localStorage.removeItem('mapleBossTracker.keyReset')}",dump)
    pp.reload(); pp.wait_for_function("!svTok()&&typeof gd!=='undefined'",timeout=15000); pp.wait_for_timeout(300)
    sp=st(pp)
    check('P: 새 버전 첫 실행 → 이 기기 키(대표·부계정·예비) 전부 비움', keyset(sp)==[] and not any(a.get('bkLabel') for a in sp['settings']['accounts']), keyset(sp))
    check('P: 계정 칸(id·이름)·캐릭터·연결(accId) 그대로', [a['id'] for a in sp['settings']['accounts']]==['a1','a2','a3'] and [(c['name'],c['accId']) for c in sp['characters']]==[(c['name'],c['accId']) for c in json.loads(json.loads(dump)['mapleBossTracker.v1'])['characters']] and [c['accId'] for c in sp['characters']]==['a1','a2','a3'], [(c['name'],c.get('accId')) for c in sp['characters']])
    check('P: 세션·금고 표시 지움(대표 키로 다시 로그인), 초기화 표시 저장', not pp.evaluate("localStorage.getItem('mapleBossTracker.svToken')") and not pp.evaluate("localStorage.getItem('mapleBossTracker.svVault')") and pp.evaluate("localStorage.getItem('mapleBossTracker.keyReset')")==RESET)
    login(pp,KA); wait_on(pp); pp.wait_for_timeout(500)
    sp=st(pp); a1=[a for a in sp['settings']['accounts'] if a['id']=='a1'][0]
    check('P: 대표 키 로그인 → 본계정 칸(a1)에 대표 키, 부계정 키 없음(금고 비었음)', a1.get('key')==KA and keyset(sp)==[KA] and len(sp['settings']['accounts'])==3, keyset(sp))
    pp.reload(); pp.wait_for_timeout(800); check('P: 다시 열어도 또 지우지 않음 (1번만)', keyset(st(pp))==[KA] and bool(pp.evaluate('svTok()')))
    # 캐릭터 추가 창에서 부계정 F 키 다시 추가 → 예전 '부계정F' 칸에 재연결 (새 칸 안 생김)
    pp.evaluate("openAdd()"); pp.wait_for_selector('#newAccKey')
    pp.fill('#newAccKey',KF); pp.click('#newAccBtn'); pp.wait_for_function("accounts().some(a=>a.id==='a2'&&a.key)",timeout=15000); pp.wait_for_timeout(500)
    sp=st(pp); a2=[a for a in sp['settings']['accounts'] if a['id']=='a2'][0]
    check('P: 다시 추가한 F 키 → 예전 a2(부계정F) 칸에 들어감, 계정 칸 3개 그대로', a2.get('key')==KF and len(sp['settings']['accounts'])==3 and [c['accId'] for c in sp['characters']]==['a1','a2','a3'], [(a['id'],a['label'],bool(a.get('key'))) for a in sp['settings']['accounts']])
    pp.fill('#newAccKey',KG); pp.click('#newAccBtn'); pp.wait_for_function("accounts().some(a=>a.id==='a3'&&a.key)",timeout=15000)
    pp.wait_for_function("localStorage.getItem('mapleBossTracker.svSubSig')===svSubSig()",timeout=20000)
    check('P: 다시 등록한 부계정 2개 → 서버 금고·등록부', len(dev.sql("SELECT * FROM keyvault2"))==1 and sorted(r['kind'] for r in dev.sql("SELECT kind FROM keyreg"))==['sub','sub'])
    # 다른 데이터(캐릭터 있음)의 키 → 빨간 글, 저장 안 함
    pp.fill('#newAccLabel','남의키'); pp.fill('#newAccKey',KI); pp.click('#newAccBtn'); pp.wait_for_selector('#accRej .keyrej',timeout=10000); pp.wait_for_timeout(300)
    t=pp.inner_text('#accRej'); col=pp.evaluate("getComputedStyle(document.querySelector('#accRej .keyrej')).color")
    sp=st(pp)
    check("P: 다른 데이터 키 추가 → '이미 등록된 부계정 API입니다.' 빨간 글만 ('등록 완료' 없음)", t.strip().endswith('이미 등록된 부계정 API입니다.') and '등록 완료' not in t and col=='rgb(255, 90, 90)', (t,col))
    check('P: 그 키는 저장 안 함 (계정 칸 3개, 키 목록에 없음)', KI not in json.dumps(sp) and len(sp['settings']['accounts'])==3 and pp.evaluate("accounts().length")==3, keyset(sp))
    pp.screenshot(path=os.path.join(ROOT,'tests','out','b64_keyrej.png')) if os.path.isdir(os.path.join(ROOT,'tests','out')) else None
    pp.evaluate("closeImport()"); check('P: 창 닫으면 빨간 글 사라짐', pp.locator('#accRej').count()==0)
    # ---- 집 PC(H): 예전 키가 남아 있던 기기 → 새 버전 열면 비우고, 대표 키 로그인으로 PC방에서 다시 등록한 것만 복원 ----
    ph.evaluate("()=>localStorage.removeItem('mapleBossTracker.keyReset')")  # (집 PC 는 아직 새 버전을 연 적 없음)
    ph.reload(); ph.wait_for_function("!svTok()&&typeof gd!=='undefined'",timeout=15000); ph.wait_for_timeout(300)
    check('H: 새 버전 첫 실행 → 예전 키 전부 비움', keyset(st(ph))==[], keyset(st(ph)))
    login(ph,KA); wait_on(ph); ph.wait_for_timeout(800)
    sh=st(ph)
    check('H: 대표 키만 → PC방에서 다시 등록한 키(대표·F·G) 복원, 예전 예비 키는 안 돌아옴', keyset(sh)==sorted([KA,KF,KG]), keyset(sh))
    check('H: 같은 계정 칸에 복원 (중복 칸 없음), 캐릭터 연결 그대로', [(a['id'],bool(a.get('key'))) for a in sh['settings']['accounts']]==[('a1',True),('a2',True),('a3',True)] and [c['accId'] for c in sh['characters']]==['a1','a2','a3'], [(a['id'],a['label']) for a in sh['settings']['accounts']])
    check('H: 금고는 그대로 (예전 키가 다시 올라가지 않음)', sorted(r['kind'] for r in dev.sql("SELECT kind FROM keyreg"))==['sub','sub'])
    after=dev.sql("SELECT rev,data FROM state ORDER BY user_id")
    ca=[[c['name'] for c in json.loads(r['data'])['characters']] for r in after]; cb=[[c['name'] for c in json.loads(r['data'])['characters']] for r in before]
    check('서버 데이터: 캐릭터 그대로', ca==cb, (ca,cb))
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
