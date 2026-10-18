# 대표 키 / 부계정 키 금고 — 브라우저 2대 + wrangler dev(로컬 D1) + 넥슨 모의 서버 (2026-10-10)
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
PORT, WP, NP = 8795, 8774, 8775
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
    pg=ctx.new_page(); pg.on('dialog',lambda d:d.accept()); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('popup',lambda p:popups.append(p.url))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'net::' not in m.text else None)
    return ctx,pg
def inject(pg):  # b69: 서버 모드는 세션 없이 새로고침하면 이 PC 데이터를 지움 → '로그인 전에 이 페이지에서 만든 데이터'로 다시 넣음
    pg.wait_for_timeout(300); pg.evaluate("()=>{const p=sessionStorage.getItem('t_preset'); if(p){localStorage.setItem('mapleBossTracker.v1',p);load();render();}}")
st=lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')||'{\"characters\":[],\"settings\":{\"accounts\":[]}}')")
server_state=lambda: dev.sql("SELECT rev, data FROM state")
def wait_on(pg,t=15000): pg.wait_for_function("gd.state==='on'&&!gd.busy&&!gd.timer",timeout=t); pg.wait_for_timeout(150)
KF='live_KEY_F_0123456789abcdef'
def invite(pg): pg.evaluate('openAdd()'); pg.wait_for_selector('#svMainKey')  # b67: 초대 비밀번호 없음 → 캐릭터 추가 창 본계정 키 칸
def shot(pg,name):
    pg.evaluate('gdMenu(true)'); pg.wait_for_timeout(200); pth=os.path.join(OUT,name); pg.locator('#gMenu').screenshot(path=pth)
    if SHOTDIR: shutil.copy(pth,SHOTDIR)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ca,pa=mkctx(b); pa.goto(URL)
    pa.evaluate("([p,api])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p));sessionStorage.setItem('t_preset',JSON.stringify(p));localStorage.setItem('mapleBossTracker.keyReset','b64-2026-10-12');localStorage.setItem('mapleBossTracker.syncApi',api)}",[PRESET,API]); pa.reload(); inject(pa); pa.wait_for_timeout(400)
    invite(pa); t=pa.inner_text('#svMainSec')
    check("b71: main-key-only section = input 'API키 입력' + 등록 only", t.strip().startswith('등록\nAPI 발급 : https://openapi.nexon.com/ko/my-application/create-app/\n①링크 클릭 후 넥슨 로그인') and t.strip().endswith('API키 입력란에 Ctrl+V') and  # b209: 아래 발급 순서 안내
          pa.get_attribute('#svMainKey','placeholder')=='API키 입력', t[:200])
    pa.fill('#svMainKey',KA); pa.click('#svMainBtn'); wait_on(pa); pa.evaluate('closeImport()')
    acc=st(pa)['settings']['accounts']; check('A: login account marked main', acc[0].get('main') is True, acc)
    pa.evaluate('gdMenu(true)'); pa.wait_for_selector('#gMenu:not([hidden]) #svSubKey')
    check('logged-in panel: 부계정 키 추가', pa.inner_text('#svSubBtn')=='부계정 키 추가' and '대표 키: 본계정' in pa.inner_text('#gMenu'), pa.inner_text('#gMenu')[:300])
    pa.fill('#svSubKey',KF); pa.click('#svSubBtn')
    pa.wait_for_function("accounts().some(a=>a.key==='%s'&&a.ah)"%KF,timeout=15000); wait_on(pa)
    pa.evaluate('gdMenu(true)'); pa.wait_for_timeout(300)
    check('A: sub key added + linked, panel counts 1', '부계정 키 1개' in pa.inner_text('#gMenu'), pa.inner_text('#gMenu')[:300])
    shot(pa,'sv_sub_key_added.png')
    v=dev.sql("SELECT * FROM keyvault2"); dump=json.dumps(v)+json.dumps(server_state())
    check('server: vault row, ciphertext only (no raw keys anywhere)', len(v)==1 and KA not in dump and KF not in dump, len(v))
    # 기기 B: 대표 키만 입력 → 데이터 + 부계정 키 복원
    cb,pb=mkctx(b); pb.goto(URL); pb.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.keyReset','b64-2026-10-12');localStorage.setItem('mapleBossTracker.syncApi',api)}",API); pb.reload(); pb.wait_for_timeout(400)
    invite(pb); pb.fill('#svMainKey',KA); pb.press('#svMainKey','Enter'); wait_on(pb); pb.evaluate('closeImport()')
    pb.wait_for_function("accounts().some(a=>a.key==='%s')"%KF,timeout=10000)
    acc=st(pb)['settings']['accounts']
    check('B: main key only → sub key restored automatically', any(a.get('key')==KF for a in acc) and any(a.get('key')==KA and a.get('main') for a in acc) and len(acc)==2, [(a['label'],bool(a.get('key')),a.get('main')) for a in acc])
    check('B: characters restored', len(st(pb)['characters'])==2)
    n=len([x for x in puts if '/api/subkeys' in x[1]]); pb.wait_for_timeout(1500)
    check('B: restored keys not re-uploaded', len([x for x in puts if '/api/subkeys' in x[1]])==n, n)
    pb.wait_for_timeout(300); shot(pb,'sv_sub_key_restored.png')
    check('no google popup, no page errors', not popups and not errs, (popups,errs[:3]))
    b.close()
finally:
    srv.terminate(); dev.stop(); ms.shutdown()
print('FAILS:',fails)
