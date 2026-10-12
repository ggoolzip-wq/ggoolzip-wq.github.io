# b72: 본계정 키 = 항상 1번 줄 '본계정'(새 키로 바뀌면 예전 키 칸·금고에서 삭제, 중복 없음) / 부계정 이름 필수(빨간 글) / 키 없는 계정 캐릭터 숨김(데이터 유지·키 다시 넣으면 복귀) / '키 없음' 글자 없음
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
PORT, WP, NP = 8857, 8858, 8859
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

OUT='/workspace/maple-boss-tracker'
KA2='live_KEY_A2_0123456789abcde'
def ch(id,name,acc,ocid,main=False):
    return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','ocid':ocid,'accId':acc,'isMain':main,'image':'','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{'lucid':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
SIDE="[...document.querySelectorAll('#charList [data-id]')].map(e=>e.dataset.id)"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    c1,p1=mkctx(b); p1.goto(URL); p1.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); p1.reload(); p1.wait_for_timeout(500)
    login(p1,KA); wait_on(p1)
    for k,nm in ((KF,'부F'),(KG,'부G')):
        p1.evaluate("openAdd()"); p1.wait_for_selector('#newAccKey'); p1.fill('#newAccLabel',nm); p1.fill('#newAccKey',k); p1.click('#newAccBtn'); p1.wait_for_function("accounts().some(a=>a.key==='%s')"%k,timeout=15000); p1.evaluate("closeImport()")
    # 예전 버그 상태: 본계정 칸이 4번째 '계정4' + 같은 키의 중복 칸, G 계정은 키가 빠짐
    p1.evaluate("""cs=>{ const A=accounts(); const m=A[0]; m.label='계정4'; const f=A.find(a=>a.key==='%s'), g=A.find(a=>a.key==='%s');
      g.key=''; S.settings.accounts=[f,g,{id:'dup',label:'계정5',key:'%s'},m];
      S.characters=[{...cs[0],accId:m.id},{...cs[1],accId:f.id},{...cs[2],accId:g.id},{...cs[3],accId:'dup'}];
      S.history=[{week:'2026-09-28',total:1000000000,perChar:[{id:'c3',name:'부캐G',total:1000000000}]}]; save(); render(); }"""%(KF,KG,KA),
      [ch('c1','단풍용사','','o-acc-A',True),ch('c2','부캐F','','o-acc-F'),ch('c3','부캐G','','o-acc-G'),ch('c4','단풍둘','','o-acc-A')])
    p1.evaluate("svSaveNow()"); wait_on(p1)
    p1.evaluate("gdMenu(true)"); p1.click('#gdLogout'); p1.wait_for_function("!svTok()",timeout=15000); p1.wait_for_timeout(800)
    # 같은 넥슨 계정의 새 키로 로그인
    login(p1,KA2); wait_on(p1); p1.wait_for_timeout(1500)
    A=p1.evaluate("accounts().map(a=>({id:a.id,label:a.label,key:a.key||'',main:!!a.main}))")
    check('row 1 = 본계정 with the new login key', A[0]['label']=='본계정' and A[0]['key']==KA2, [(a['label'],a['key'][:10]) for a in A])
    check('old main key gone, no dup/계정N rows', not any(a['key']==KA for a in A) and len(A)==3 and not any(a['label'].startswith('계정') and a['label']!='계정 이름' for a in A) and len({a['id'] for a in A})==3, [(a['label'],a['key'][:10]) for a in A])
    check('duplicate row characters moved to 본계정', p1.evaluate("S.characters.find(c=>c.id==='c4').accId===accounts()[0].id"))
    check('keyless G account characters hidden in sidebar (data kept)', p1.evaluate(SIDE)==['c1','c4','c2'] or sorted(p1.evaluate(SIDE))==['c1','c2','c4'], p1.evaluate(SIDE))
    check('hidden char data kept', p1.evaluate("(()=>{const c=S.characters.find(c=>c.id==='c3'); return !!c&&c.weekly.lucid===true})()"))
    check('hidden char not in boss/summary views', 'c3' not in p1.evaluate("vchars().map(c=>c.id)") and '부캐G' not in p1.inner_text('#view'))
    check('history (past income) kept', p1.evaluate("S.history.length")==1)
    p1.evaluate("openAdd()"); p1.wait_for_selector('#accList'); p1.wait_for_timeout(1000)
    A=p1.evaluate("accounts().map(a=>({id:a.id,label:a.label,key:a.key||'',main:!!a.main}))")
    check('after list relink: still row1 본계정, 3 rows', A[0]['label']=='본계정' and A[0]['key']==KA2 and len(A)==3, [(a['label'],a['key'][:10]) for a in A])
    html=p1.inner_text('#importModal')
    check("no '키 없음' anywhere", '키 없음' not in html and '키 없음' not in p1.inner_text('body'))
    lbl=p1.evaluate("(()=>{const i=document.querySelector('[data-acclabel=\"%s\"]'); return [i.value,i.placeholder]})()"%A[2]['id'] if A[2]['key']=='' else "['x','x']")
    check("keyless row: empty name, placeholder '계정 이름'", lbl==['','계정 이름'], lbl)
    check("new alt name placeholder '계정 이름'", p1.get_attribute('#newAccLabel','placeholder')=='계정 이름')
    p1.screenshot(path=OUT+'/oct12j_b72_test_modal.png')
    p1.fill('#newAccLabel',''); p1.fill('#newAccKey',KG); p1.wait_for_timeout(200)
    check('empty name alone → no warning (only on 등록 click)', not p1.is_visible('#newAccLblErr') and p1.locator('text=계정 이름을 입력해주세요').count()==0)
    p1.click('#newAccBtn'); p1.wait_for_timeout(800)
    check("empty name → red '계정 이름을 입력해주세요', not registered", p1.is_visible('#newAccLblErr') and p1.inner_text('#newAccLblErr')=='계정 이름을 입력해주세요' and not p1.evaluate("accounts().some(a=>a.key==='%s')"%KG))
    check('warning is red', 'rgb(255, 90, 90)'==p1.evaluate("getComputedStyle(document.querySelector('#newAccLblErr')).color"))
    p1.screenshot(path=OUT+'/oct12j_b72_test_nameerr.png')
    p1.type('#newAccLabel','부'); p1.wait_for_timeout(200)
    check('typing a name hides the warning', not p1.is_visible('#newAccLblErr'))
    p1.fill('#newAccLabel','부G'); p1.click('#newAccBtn'); p1.wait_for_function("accounts().some(a=>a.key==='%s')"%KG,timeout=15000); p1.evaluate("closeImport()"); p1.wait_for_timeout(500)
    check('key re-registered → hidden characters back', 'c3' in p1.evaluate(SIDE) and len(p1.evaluate("accounts()"))==3, (p1.evaluate(SIDE),p1.evaluate("accounts().map(a=>a.label)")))
    wait_on(p1); p1.evaluate("svSaveNow()"); wait_on(p1); p1.wait_for_timeout(1000)
    # 다른 PC 에서 새 키로 로그인 → 금고에 예전 본계정 키 없음
    c2,p2=mkctx(b); p2.goto(URL); p2.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); p2.reload(); p2.wait_for_timeout(500)
    login(p2,KA2); wait_on(p2); p2.wait_for_timeout(1500)
    ks=p2.evaluate("accounts().map(a=>a.key||'')")
    check('other PC: vault has no old main key, row1 = new key', KA not in ks and ks[0]==KA2 and len(ks)==3, [k[:10] for k in ks])
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate(); dev.stop(); ms.shutdown()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
