import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8829=_tutil.free_port()
# b67: (예전 입장 화면 오류 문구 검사 → 대체) 캐릭터 추가 창 '본계정 API 키 등록' 오류 문구가 보이는지 — 투명 배경 + 빨간 글자
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8829
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
API='https://fake-sync.example'
RESP={'login':(401,{'error':'invalid_key','message':'넥슨이 이 API 키를 거부했습니다 (키 확인)'})}
def fake(route):
    u=route.request.url
    if u.endswith('/api/login'): s,b=RESP['login']; return route.fulfill(status=s,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps(b))
    route.fulfill(status=404,headers={'Access-Control-Allow-Origin':'*'},body='{}')
def look(pg):
    return pg.evaluate("(()=>{const e=document.querySelector('#svMainSt .keyrej');if(!e)return null;const c=getComputedStyle(e);return {t:e.textContent,color:c.color,bg:c.backgroundColor,vis:e.offsetHeight>0&&c.opacity==='1'&&c.visibility==='visible'}})()")
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':800},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route(API+'/**',fake); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(URL); pg.evaluate("a=>{localStorage.clear();localStorage.setItem('mapleBossTracker.keyReset','b64-2026-10-12');localStorage.setItem('mapleBossTracker.syncApi',a)}",API); pg.reload(); pg.wait_for_timeout(400)
    pg.evaluate('openAdd()'); pg.wait_for_selector('#svMainKey')
    pg.fill('#svMainKey','live_bad_key_value_0123456'); pg.press('#svMainKey','Enter'); pg.wait_for_selector('#svMainSt .keyrej')
    l=look(pg)
    check('invalid key: clear error, red #ff5a5a, transparent background', l and '거부' in l['t'] and l['color']=='rgb(255, 90, 90)' and l['bg'] in ('rgba(0, 0, 0, 0)','transparent') and l['vis'], l)
    check('invalid key: no session, still main-key-only', not pg.evaluate('svTok()') and pg.is_visible('#svMainKey') and not pg.is_visible('#accList'))
    RESP['login']=(403,{'error':'sub_key','message':'이미 등록된 부계정 API입니다.'})
    pg.fill('#svMainKey','live_sub_key_value_0123456'); pg.click('#svMainBtn'); pg.wait_for_function("document.querySelector('#svMainSt .keyrej')?.textContent==='이미 등록된 부계정 API입니다.'",timeout=5000)
    l=look(pg); check("alt key as main: red '이미 등록된 부계정 API입니다.' (no '등록 완료')", l and l['color']=='rgb(255, 90, 90)' and '등록 완료' not in pg.inner_text('#svMainSec'), l)
    pg.locator('#importModal .modal').screenshot(path=os.path.join(OUT,'b67_mainkey_err.png'))
    pg.evaluate('closeImport()'); pg.evaluate('openAdd()'); pg.wait_for_timeout(100)
    check('error cleared when the modal is reopened', look(pg) is None)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
