# b81: [저장] 즉시 — 화면·로컬 바로 확정('저장이 완료되었습니다.', 버튼 꺼짐), 서버 저장은 뒤에서(재시도), 실패하면 '⚠ 저장 안 됨'
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
PORT, WP, NP = 8867, 8868, 8869
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

OUT='/workspace/maple-boss-tracker'
import time as _t
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    c1,p1=mkctx(b); p1.goto(URL); p1.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',api)}",API); p1.reload(); p1.wait_for_timeout(500)
    login(p1,KA); wait_on(p1)
    p1.evaluate("S.characters.push({id:'c1',name:'단풍용사',level:280,job:'히어로',world:'스카니아',ocid:'o-acc-A',accId:accounts()[0].id,isMain:true,image:'',bosses:{lucid:{enabled:true,diff:'hard',party:1}},weekly:{},monthly:{},auto:{},drops:{},sync:{}});S.activeId='c1';save();render()")
    p1.evaluate("svSaveNow(true)"); wait_on(p1)
    # 서버를 느리게 (1.5초) → 저장 버튼은 그래도 바로
    p1.route(API+'/api/**',lambda r:(_t.sleep(1.5),r.continue_()))  # (파이썬 쪽 지연 — 화면 측정은 페이지 안에서)
    p1.evaluate("pendStart(); activeChar().bosses.lucid.party=2; save(); render();"); p1.wait_for_timeout(100)
    r=p1.evaluate("(()=>{const t=performance.now(); document.querySelector('#pendSave').click(); return [!!document.querySelector('.pdone'), document.querySelector('#pendSave').disabled, !pend, performance.now()-t]})()"); el=r[:3]; dt=r[3]/1000
    check('save is instant: done text + buttons off within the click (server slow)', el==[True,True,True] and dt<1.0, (el,round(dt,2)))
    p1.screenshot(path=OUT+'/oct12s_b81_test_save.png')
    p1.wait_for_function("gd.state==='on'&&!gd.busy&&!gdLocalDirty()",timeout=20000)
    srv_party=[json.loads(r['data'])['characters'][0]['bosses']['lucid']['party'] for r in dev.sql("SELECT data FROM state")]
    check('background push reached server', srv_party==[2], srv_party)
    p1.unroute(API+'/api/**')
    # 서버 끊김 → 재시도 후 경고
    p1.route(API+'/api/**',lambda r:r.abort())
    p1.evaluate("pendStart(); activeChar().bosses.lucid.party=3; save(); render();"); p1.click('#pendSave')
    check('offline save still instant', p1.evaluate("!pend&&!!document.querySelector('.pdone')"))
    p1.wait_for_function("!!document.querySelector('#svWarn')&&!document.querySelector('#svWarn').hidden",timeout=20000)
    check("failure surfaced as '⚠ 저장 안 됨'", '저장 안 됨' in p1.inner_text('#svWarn'))
    p1.unroute(API+'/api/**'); p1.click('#svWarn'); p1.wait_for_function("gd.state==='on'&&!gdLocalDirty()",timeout=20000)
    check('retry via warning → saved', [json.loads(r['data'])['characters'][0]['bosses']['lucid']['party'] for r in dev.sql("SELECT data FROM state")]==[3])
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
