# b216: ① 서버 동기화 '어느 데이터를 쓸까요?' 없음 — 서버 저장 값이 항상 이김 (wat 처치 시각이 기기마다 달라 다시 떴던 문제)
#       ② 본계정 키 삭제 = 이 브라우저만 처음 온 사람(예시 화면) · 서버 기록 유지 → 같은 키 다시 등록하면 본캐·부캐 복원
#       ③ '(총 0캐릭 등록 중)'·'· 0캐릭 등록 중' 숨김  ④ 실제 주소(github.io 포함)는 서버 모드 — '☁ 구글 로그인' 없음
import os, sys, json, subprocess, time, urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
from playwright.sync_api import sync_playwright
SHOT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out')
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT, WP, NP = 8941, 8942, 8943
API=f'http://127.0.0.1:{WP}'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
KA,KF='live_KEY_A_0123456789abcdef','live_KEY_F_0123456789abcdef'
def nexon(route):
    k=route.request.headers.get('x-nxopen-api-key',''); v=MN.KEYS.get(k)
    if '/character/list' not in route.request.url or not isinstance(v,list): return route.fulfill(status=400,content_type='application/json',body=json.dumps({'error':{'name':'OPENAPI0006','message':'x'}}))
    body={'account_list':[{'account_id':a,'character_list':[{'ocid':'o-'+a,'character_name':'캐릭'+a[-1],'world_name':'스카니아','character_class':'히어로','character_level':280}]} for a in v]}
    route.fulfill(status=200,content_type='application/json',body=json.dumps(body))
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
def fresh(pg): pg.goto(URL); pg.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); pg.reload(); pg.wait_for_timeout(500)
def login(pg,key):
    if not pg.evaluate("document.querySelector('#importModal').classList.contains('show')"): pg.evaluate("openAdd()")
    pg.wait_for_selector('#svMainKey'); pg.fill('#svMainKey',key); pg.click('#svMainBtn')
srvchars=lambda: sorted(c['id'] for c in json.loads(dev.sql("SELECT data FROM state")[0]['data'])['characters'])
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed'); print('FAILS: []'); srv.terminate(); sys.exit(0)
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    # ---- ④ 실제 주소(github.io) = 서버 모드, '구글' 버튼 없음 ----
    html=open(os.path.join(ROOT,'index.html'),'rb').read()
    cg=b.new_context(viewport={'width':1280,'height':800},locale='ko-KR')
    cg.route('https://ggoolzip-wq.github.io/**',lambda r:r.fulfill(status=200,content_type='text/html; charset=utf-8',body=html) if r.request.resource_type=='document' else r.fulfill(status=404,body=''))
    cg.route('https://ggoolzip-sync.bossmaple.workers.dev/**',lambda r:r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body='{}'))
    cg.route('https://accounts.google.com/**',lambda r:r.abort()); cg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pgx=cg.new_page(); pgx.on('pageerror',lambda e:errs.append('gh:'+str(e))); pgx.goto('https://ggoolzip-wq.github.io/'); pgx.wait_for_timeout(1200)
    hdr=pgx.evaluate("[...document.querySelectorAll('header button, .hbtn, #gBtn')].filter(e=>e.offsetParent).map(e=>e.textContent).join('|')")
    check('github.io: server mode (SV_ON set), no ☁ 구글 로그인 button', bool(pgx.evaluate("SV_ON")) and '구글' not in hdr and pgx.is_hidden('#gBtn'), hdr)
    check('github.io: first visit = demo landing', pgx.locator('#view>.demotop').count()>0)
    pgx.screenshot(path=SHOT+'/github_io_no_google.png'); cg.close()
    # ---- PC1: 본계정 + 부계정 등록, 캐릭터 2명 저장 ----
    c1,p1=mkctx(b); fresh(p1); login(p1,KA); wait_on(p1,keep=True)
    p1.wait_for_selector('#accList .accrow .regok',timeout=15000); p1.wait_for_timeout(300)
    hdr0=p1.evaluate("getComputedStyle(document.querySelector('#accKeyTotal').closest('.addsec-h')).display"); row0=' '.join(p1.inner_text('#accList .accrow .regok').split())
    check("③ 0캐릭: '🔑 넥슨 API 키 (총 0캐릭 등록 중)' 줄 숨김, 행은 '✔ 등록 완료'만", hdr0=='none' and row0=='✔ 등록 완료', (hdr0,row0))
    p1.locator('#importModal .modal').screenshot(path=SHOT+'/zero_chars_modal.png')
    p1.evaluate("accAddShow(true)"); p1.evaluate("()=>{const i=document.querySelector('#newAccLabel'); if(i&&!i.value) i.value='부계정'}"); p1.fill('#newAccKey',KF); p1.click('#newAccBtn'); p1.wait_for_function("accounts().some(a=>a.key==='%s')"%KF,timeout=15000)
    p1.wait_for_function("localStorage.getItem('mapleBossTracker.svSubSig')===svSubSig()",timeout=20000); p1.evaluate("closeImport()")
    p1.evaluate("""()=>{ const A=accounts(); const mk=(id,nm,acc,o,main)=>({id,name:nm,level:280,job:'히어로',world:'스카니아',ocid:o,accId:acc,isMain:main,image:'',bosses:{lucid:{enabled:true,diff:'hard',party:1}},weekly:{},monthly:{},auto:{},drops:{},sync:{}});
      S.characters.push(mk('c1','본캐A',A.find(a=>a.key==='%s').id,'o-acc-A',true), mk('c2','부캐F',A.find(a=>a.key==='%s').id,'o-acc-F',false)); save(); render(); }"""%(KA,KF))
    p1.evaluate("svSaveNow()"); wait_on(p1)
    p1.evaluate("openAdd()"); p1.wait_for_timeout(400)
    check("③ 캐릭 있으면 '(총 N캐릭 등록 중)' 보임", p1.is_visible('#accKeyTotal') and '캐릭 등록 중' in p1.inner_text('#accKeyTotal'), p1.inner_text('#accKeyTotal'))
    p1.evaluate("closeImport()")
    vault0=len(dev.sql("SELECT * FROM keyvault2")); chars0=srvchars()
    check('setup: server has 2 chars + alt key vault', chars0==['c1','c2'] and vault0==1, (chars0,vault0))
    # ---- ① 동기화 충돌(같은 보스 처치 시각 wat 가 기기마다 다름) → 질문 없이 서버 값 ----
    c2,p2=mkctx(b); fresh(p2); login(p2,KA); wait_on(p2)
    p2.evaluate("S.characters.find(c=>c.id==='c1').weekly={lucid:true}; S.characters.find(c=>c.id==='c1').wat={lucid:111}; save(); svSaveNow()"); wait_on(p2)
    p1.evaluate("clearTimeout(gd.timer); const c=S.characters.find(c=>c.id==='c1'); c.weekly={lucid:true}; c.wat={lucid:222}; c.name='이PC이름'; save(); clearTimeout(gd.timer); gd.timer=null")
    p1.evaluate("gd.pulledAt=0; gd.busy=false"); p1.evaluate("(async()=>{ await gdConnect(false); })()"); p1.wait_for_timeout(2500); wait_on(p1)
    s1=st(p1); c1x=[c for c in s1['characters'] if c['id']=='c1'][0]
    check('① 페이지 열 때(불러오기): 묻지 않음, 서버 값으로 덮어씀 (wat·이름)', not p1.is_visible('#driveModal') and p1.evaluate("gd.state")=='on' and c1x.get('wat',{}).get('lucid')==111 and c1x['name']!='이PC이름', (p1.evaluate("gd.state"),c1x.get('wat'),c1x['name']))
    srvc=[c for c in json.loads(dev.sql("SELECT data FROM state")[0]['data'])['characters'] if c['id']=='c1'][0]
    check('① 이 PC 의 예전 값이 서버로 올라가지 않음', srvc['name']!='이PC이름' and srvc.get('wat',{}).get('lucid')==111, (srvc['name'],srvc.get('wat')))
    # 저장 중 충돌(409): 겹치는 항목은 서버, 이 PC 에서 바꾼 다른 항목은 유지
    p2.evaluate("S.characters.find(c=>c.id==='c2').name='서버부캐'; save(); svSaveNow()"); wait_on(p2)
    p1.evaluate("clearTimeout(gd.timer); S.characters.find(c=>c.id==='c2').name='PC부캐'; S.characters.find(c=>c.id==='c1').bosses.lucid.party=3; save(); clearTimeout(gd.timer); gd.timer=null; svSaveNow()"); p1.wait_for_timeout(2500); wait_on(p1)
    d=json.loads(dev.sql("SELECT data FROM state")[0]['data']); cc={c['id']:c for c in d['characters']}
    check('① 저장 버튼 중 충돌: 질문 없음, 겹친 항목=서버 값, 다른 수정은 저장됨', not p1.is_visible('#driveModal') and cc['c2']['name']=='서버부캐' and cc['c1']['bosses']['lucid']['party']==3 and [c['name'] for c in st(p1)['characters'] if c['id']=='c2']==['서버부캐'], (cc['c2']['name'],cc['c1']['bosses']['lucid']))
    c2.close()
    # ---- ② 본계정 키 삭제 → 처음 온 사람 화면, 서버 기록 유지 ----
    rev0=dev.sql("SELECT rev FROM state")[0]['rev']
    p1.evaluate("openAdd()"); p1.wait_for_selector('#accList .accrow'); p1.wait_for_timeout(300)
    p1.locator('#accList .accrow').nth(0).locator('[data-accdel]').click()
    p1.wait_for_function("!svTok()",timeout=10000); p1.wait_for_timeout(800)
    s=st(p1)
    check('② 삭제 후: 세션 없음, 이 PC 캐릭터·키 비움', not p1.evaluate("svTok()") and len(s['characters'])==0 and not keyset(s), (len(s['characters']),keyset(s)))
    check('② 처음 온 사람 화면(예시 탭 랜딩), 헤더 로그인/구글 버튼 없음', p1.locator('#view>.demotop').count()>0 and p1.is_hidden('#gBtn') and '아직 캐릭터가 없습니다' not in p1.inner_text('body') and '구글' not in p1.inner_text('header'), p1.inner_text('header')[:120])
    p1.screenshot(path=SHOT+'/after_main_key_delete.png')
    check('② 서버 기록 그대로 (캐릭터·부계정 키 금고)', srvchars()==['c1','c2'] and len(dev.sql("SELECT * FROM keyvault2"))==1, (srvchars(),len(dev.sql("SELECT * FROM keyvault2"))))
    # 같은 본계정 키 다시 등록 → 본캐·부캐·부계정 키 복원
    p1.click('#addCharBtn') if p1.is_visible('#addCharBtn') else p1.evaluate("openAdd()")
    login(p1,KA); wait_on(p1); p1.wait_for_function("accounts().some(a=>a.key==='%s')"%KF,timeout=15000); p1.wait_for_timeout(500)
    s=st(p1)
    check('② 다시 등록 → 본캐·부캐 캐릭터와 부계정 키 복원, 화면에 보임', sorted(c['id'] for c in s['characters'])==['c1','c2'] and keyset(s)==sorted([KA,KF]) and p1.evaluate("S.characters.filter(charShown).length")==2, (keyset(s),[c['name'] for c in s['characters']]))
    p1.screenshot(path=SHOT+'/after_reregister.png')
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
