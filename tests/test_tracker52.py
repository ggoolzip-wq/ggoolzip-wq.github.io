# b68: 가입 승인 — 새 본계정 키 = '⏳ 승인 대기 중'(데이터 저장 없음) / 관리자 ☁ 메뉴 '👑 관리자' → 승인·거절·차단 / 승인 후 '승인 확인' → 로그인 / 거절 → 빨간 글 / 차단 → 로그아웃
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
PORT, WP, NP = 8827, 8808, 8809
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
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP,approval=True)
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
OUT='/workspace/maple-boss-tracker'
def fresh(pg):
    pg.goto(URL); pg.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); pg.reload(); pg.wait_for_timeout(500)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    # 관리자 = 기존 사용자(KA). 첫 로그인은 대기 → 승인 행 지우고(=예전부터 있던 사용자) meta admin_user 지정
    jpost('/api/login',{'key':KA}); UADM=dev.sql("SELECT id FROM users")[0]['id']
    dev.sql(f"DELETE FROM approval WHERE user_id='{UADM}'"); dev.sql(f"INSERT INTO meta (k,v) VALUES ('admin_user','{UADM}')")
    # ---- 새 사람(PC1): 본계정 키 등록 → 승인 대기 ----
    c1,p1=mkctx(b); fresh(p1)
    p1.click('#addCharBtn'); p1.wait_for_selector('#svMainKey'); p1.fill('#svMainKey',KF); p1.click('#svMainBtn')
    p1.wait_for_selector('#svPendCheck',timeout=15000); p1.wait_for_timeout(300)
    t=p1.inner_text('#svMainSec')
    check("new main key → modal '⏳ 승인 대기 중' with main char name·world·level", '승인 대기 중' in t and '캐릭F' in t and '스카니아' in t and 'Lv.280' in t, t)
    check('pending: no session, nothing stored on server, header ⏳ 승인 대기 중', not p1.evaluate('svTok()') and not dev.sql("SELECT 1 FROM state") and not dev.sql("SELECT 1 FROM sessions s JOIN approval a ON a.user_id=s.user_id") and p1.inner_text('#gBtn').strip()=='⏳ 승인 대기 중', p1.inner_text('#gBtn'))
    check('pending modal keeps NEXON attribution, no key list/char picker', p1.is_visible('.addm .svmattrib') and not p1.is_visible('#accList') and not p1.is_visible('#impSec'))
    p1.screenshot(path=os.path.join(OUT,'oct12f_pending.png'))
    p1.click('#svPendCheck'); p1.wait_for_timeout(800)
    check('승인 확인 while still pending → stays pending', p1.is_visible('#svPendCheck') and not p1.evaluate('svTok()'))
    p1.reload(); p1.wait_for_timeout(1500)
    check('reload → still 승인 대기 중 (checked once on open)', p1.inner_text('#gBtn').strip()=='⏳ 승인 대기 중' and not p1.evaluate('svTok()'))
    # ---- 관리자(PC2) ----
    c2,p2=mkctx(b); fresh(p2); p2.click('#addCharBtn'); p2.wait_for_selector('#svMainKey'); p2.fill('#svMainKey',KA); p2.click('#svMainBtn'); wait_on(p2)
    check('admin logs in normally (admin flag)', p2.evaluate("localStorage.getItem('mapleBossTracker.svAdmin')")=='1')
    # b77: 관리자 입구 = 헤더 '👑 관리자' (로그아웃 왼쪽), 새로고침 뒤에도
    hdr=lambda pg: pg.evaluate("(()=>{const a=document.querySelector('#svAdminHdr'),g=document.querySelector('#gBtn'); return !!a&&!a.hidden&&a.offsetParent!==null&&a.textContent.includes('관리자')&&a.getBoundingClientRect().right<=g.getBoundingClientRect().left})()")
    check('b77: admin header button visible left of 로그아웃', hdr(p2) and p2.inner_text('#gBtn').strip()=='로그아웃')
    p2.reload(); p2.wait_for_timeout(2500); check('b77: admin header button after reload', hdr(p2))
    p2.screenshot(path='/workspace/maple-boss-tracker/oct12o_b77_test_header.png')
    p2.click('#svAdminHdr'); p2.wait_for_selector('#admBody .admrow')
    t=p2.inner_text('#admBody')
    check("admin modal: 승인 대기 lists 캐릭F with 승인/거절; admin row tagged 관리자", '승인 대기' in t and '캐릭F' in t and p2.locator('[data-adm=approve]').count()==1 and p2.locator('[data-adm=reject]').count()==1 and '관리자' in t, t)
    p2.screenshot(path=os.path.join(OUT,'oct12f_admin.png'))
    p2.click('[data-adm=approve]'); p2.wait_for_function("document.querySelector('#admBody').innerText.includes('대기 중인 요청이 없어요')",timeout=8000)
    check('approve → moves to 사용 중 with 강퇴 button (no 차단)', p2.locator('[data-adm=kick]').count()==1 and p2.locator('[data-adm=block]').count()==0)
    # 새 사람: 승인 확인 → 로그인 → 평소 캐릭터 추가 창
    p1.evaluate("openAdd()"); p1.click('#svPendCheck'); wait_on(p1,keep=True)
    p1.wait_for_selector('#accList .accrow .regok',timeout=15000)
    check('after approval: 승인 확인 → logged in, normal modal, pending cleared, not admin', p1.evaluate('!!svTok()') and p1.locator('#svMainSec').count()==0 and not p1.evaluate("localStorage.getItem('mapleBossTracker.svPending')") and p1.evaluate("localStorage.getItem('mapleBossTracker.svAdmin')")=='0' and p1.inner_text('#gBtn').strip()=='로그아웃')
    p1.evaluate("closeImport()"); p1.evaluate("gdMenu(true)"); p1.wait_for_timeout(200)
    check('non-admin: no 관리자 button', p1.locator('#svAdminBtn').count()==0 and not p1.evaluate("!!document.querySelector('#svAdminHdr')&&!document.querySelector('#svAdminHdr').hidden"))
    # 관리자: 차단 → 새 사람의 다음 요청에서 로그아웃
    # b78: 강퇴 (확인 창 → 등록 키·데이터 전부 삭제)
    UF=[r['id'] for r in dev.sql("SELECT id FROM users") if r['id']!=UADM][0]
    dlg=[]; p2.once('dialog',lambda d:dlg.append(d.message))
    p2.screenshot(path=os.path.join(OUT,'oct12p_b78_test_admin.png'))
    p2.click('[data-adm=kick]'); p2.wait_for_function("!document.querySelector('#admBody [data-adm=kick]')",timeout=8000)
    check('kick confirm text with name', dlg and '정말 강퇴할까요? 이 사용자의 등록 키와 데이터가 모두 삭제됩니다.' in dlg[0] and '캐릭F' in dlg[0], dlg)
    left={t:dev.sql(f"SELECT COUNT(*) n FROM {t} WHERE user_id='{UF}'")[0]['n'] for t in ['state','state_history','sessions','accounts','keyvault2','keyreg','acct_role','seen','approval']}
    check('kick → all user rows deleted', sum(left.values())==0 and dev.sql(f"SELECT COUNT(*) n FROM users WHERE id='{UF}'")[0]['n']==0, left)
    p1.evaluate("svFetch('/api/state/meta').catch(()=>{})"); p1.wait_for_timeout(800)
    check('kicked → this PC loses session', not p1.evaluate('svTok()'))
    r=jpost('/api/login',{'key':KF}); check('kicked Nexon account can sign up again → new pending user', r.get('status')=='pending' and r.get('newUser') and dev.sql("SELECT COUNT(*) n FROM users")[0]['n']>=2, {k:r.get(k) for k in ('status','newUser')})
    kself=jpost('/api/admin/decide',{'user':UADM,'action':'kick'},p2.evaluate('svTok()')); check('admin cannot kick self', kself.get('error')=='self', kself)
    nid=[x['id'] for x in dev.sql("SELECT id FROM users") if x['id']!=UADM][0]; jpost('/api/admin/decide',{'user':nid,'action':'kick'},p2.evaluate('svTok()'))
    # ---- 또 다른 새 사람(PC3): 거절 ----
    c3,p3=mkctx(b); fresh(p3); p3.click('#addCharBtn'); p3.wait_for_selector('#svMainKey'); p3.fill('#svMainKey',KG); p3.click('#svMainBtn'); p3.wait_for_selector('#svPendCheck',timeout=15000)
    p3.wait_for_timeout(1200); p3.wait_for_function("gd.state!=='connecting'")  # 페이지 열 때 한 번 하는 자동 확인이 끝난 뒤 거절 (안 그러면 그 확인이 먼저 '거절'을 받아 감 — 정상 동작)
    p2.evaluate("admLoad()"); p2.wait_for_selector('[data-adm=reject]'); p2.click('[data-adm=reject]'); p2.wait_for_function("!document.querySelector('#admBody [data-adm=reject]')",timeout=8000)
    check('b78: no 차단·거절 section', '차단' not in p2.inner_text('#admBody') and '거절됨' not in p2.inner_text('#admBody'))
    p3.click('#svPendCheck'); p3.wait_for_selector('#svMainSt .keyrej',timeout=8000)
    check("rejected → red '가입 요청이 거절되었습니다', back to main-key input", '거절' in p3.inner_text('#svMainSt') and p3.is_visible('#svMainKey') and not p3.evaluate("localStorage.getItem('mapleBossTracker.svPending')"), p3.inner_text('#svMainSec'))
    # b78: 사용 중 10명씩 쪽 번호
    for i in range(12): dev.sql(f"INSERT INTO users (id,created_at,last_login) VALUES ('zz{i:02d}',{i},{i})")
    p2.evaluate("admLoad()"); p2.wait_for_timeout(1500)
    n1=p2.locator('#admBody .admsec:nth-of-type(2) .admrow').count(); pages=p2.locator('[data-admpage]').count()
    p2.screenshot(path=os.path.join(OUT,'oct12p_b78_test_pages.png'))
    p2.click('[data-admpage="2"]'); p2.wait_for_timeout(200); n2=p2.locator('#admBody .admsec:nth-of-type(2) .admrow').count()
    check('b78: 사용 중 10 per page + numbered pages', n1==10 and pages>=2 and 0<n2<=10, (n1,pages,n2))
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
