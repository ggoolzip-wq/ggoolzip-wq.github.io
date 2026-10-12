# b67: 초대 비밀번호·입장 화면 폐지 — 처음 온 사람 흐름 / 캐릭터 추가 창 본계정 키만 / 부계정 키를 본계정으로 → 빨간 글 / 잘못된 키 / 로그아웃 후 다시 / 새 PC 에서 본계정 키로 복원
# (공통 준비는 test_tracker49 와 같음)
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
PORT, WP, NP = 8817, 8798, 8799
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
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    # ---- 처음 온 사람(PC1): 입장 화면 없이 대시보드 → + 추가 → 본계정 키만 ----
    c1,p1=mkctx(b); p1.goto(URL); p1.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); p1.reload(); p1.wait_for_timeout(500)
    check('fresh visitor: no gate/password, empty dashboard', p1.locator('#svGate').count()==0 and p1.locator('input[type=password]:visible').count()==0 and p1.is_visible('.empty'))
    p1.click('#addCharBtn'); p1.wait_for_selector('#svMainKey')
    check('main-key-only modal (no key list/alt/spare/char picker)', p1.is_visible('#svMainKey') and not p1.is_visible('#accList') and not p1.is_visible('#newAccKey') and not p1.is_visible('#impSec') and p1.locator('.bkrow:visible').count()==0)
    p1.fill('#svMainKey','live_WRONG_0123456789abcdef'); p1.click('#svMainBtn'); p1.wait_for_selector('#svMainSt .keyrej')
    check('invalid key → clear red error, no session', '거부' in p1.inner_text('#svMainSt') and not p1.evaluate('svTok()'), p1.inner_text('#svMainSt'))
    n0=dev.sql("SELECT COUNT(*) n FROM users")[0]['n']
    p1.fill('#svMainKey',KA); p1.click('#svMainBtn'); wait_on(p1,keep=True)
    p1.wait_for_selector('#accList .accrow .regok',timeout=15000); p1.wait_for_selector('#impList .imp-row, #impList label, #impList > *',timeout=15000)
    check('main key registered → new account on server, modal switches to normal (본계정 등록 완료 + 캐릭터 목록)', dev.sql("SELECT COUNT(*) n FROM users")[0]['n']==n0+1 and p1.locator('#svMainSec').count()==0 and '등록 완료' in p1.inner_text('#accList') and p1.is_visible('#accAddOpen') and p1.is_visible('#impSec'), p1.inner_text('#accList')[:200])
    p1.evaluate("accAddShow(true)"); p1.evaluate("()=>{const i=document.querySelector('#newAccLabel'); if(i&&!i.value) i.value='부계정'}"); p1.fill('#newAccKey',KF); p1.click('#newAccBtn'); p1.wait_for_function("accounts().some(a=>a.key==='%s')"%KF,timeout=15000)
    p1.wait_for_function("localStorage.getItem('mapleBossTracker.svSubSig')===svSubSig()",timeout=20000)
    p1.evaluate("closeImport()")
    p1.evaluate("S.characters.push({id:'c1',name:'단풍용사',level:280,job:'히어로',world:'스카니아',ocid:'o-acc-A',accId:accounts()[0].id,isMain:true,image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});save();render()")
    p1.evaluate("svSaveNow()"); wait_on(p1)
    check('alt key added → vault + registry on server', len(dev.sql("SELECT * FROM keyvault2"))==1 and [r['kind'] for r in dev.sql("SELECT kind FROM keyreg")]==['sub'])
    names1=sorted(c['id'] for c in st(p1)['characters'])  # 이름은 넥슨 새로고침(ocid)으로 바뀔 수 있어 id 로 비교
    check('PC1 has characters to restore later', len(names1)>0, names1)
    # 로그아웃(헤더) → 다시 '본계정 키 등록만'
    p1.evaluate("document.getElementById('gBtn').click()"); p1.wait_for_function("!svTok()",timeout=8000); p1.wait_for_timeout(300)
    check('logout → dashboard empty, no gate, header ☁ 로그인', p1.locator('#svGate').count()==0 and p1.evaluate("S.characters.length")==0 and p1.text_content('#gBtn').strip()=='☁ 로그인')
    p1.evaluate("document.getElementById('gBtn').click()"); p1.wait_for_selector('#svMainKey')
    check('☁ 로그인 → main-key-only modal again', p1.is_visible('#svMainKey') and not p1.is_visible('#accList'))
    # 부계정 키를 본계정으로 → 빨간 글
    p1.fill('#svMainKey',KF); p1.click('#svMainBtn'); p1.wait_for_selector('#svMainSt .keyrej'); p1.wait_for_timeout(200)
    t=p1.inner_text('#svMainSt').strip(); col=p1.evaluate("getComputedStyle(document.querySelector('#svMainSt .keyrej')).color")
    check("alt key as main → red '이미 등록된 부계정 API입니다.' instead of 등록 완료, no session", t=='이미 등록된 부계정 API입니다.' and col=='rgb(255, 90, 90)' and '등록 완료' not in p1.inner_text('#importModal') and not p1.evaluate('svTok()'), (t,col))
    # ---- 다시 온 사람, 새 PC(PC2): 본계정 키만 → 데이터·부계정 키 복원 ----
    c2,p2=mkctx(b); p2.goto(URL); p2.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); p2.reload(); p2.wait_for_timeout(500)
    p2.click('#addCharBtn'); p2.wait_for_selector('#svMainKey'); p2.fill('#svMainKey',KA); p2.press('#svMainKey','Enter')
    wait_on(p2)
    p2.wait_for_function("accounts().some(a=>a.key==='%s')"%KF,timeout=10000); s2=st(p2)
    check('returning user (new PC): main key only → characters + alt key restored', sorted(c['id'] for c in s2['characters'])==names1 and keyset(s2)==sorted([KA,KF]), (keyset(s2),[c['name'] for c in s2['characters']]))
    check('header 로그아웃 when logged in', p2.text_content('#gBtn').strip()=='로그아웃')
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
