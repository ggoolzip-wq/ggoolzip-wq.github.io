# 입장 화면 오류 문구가 보이는지 (투명 배경 + 빨간 글자) — 초대 비밀번호 / 대표 키 단계
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name,**kw):
    pth=os.path.join(OUT,name); loc.screenshot(path=pth,**kw); SHOTDIR and shutil.copy(pth,SHOTDIR)
PORT=8829
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
API='https://fake-sync.example'
def fake(route):
    u=route.request.url
    if u.endswith('/api/invite'): return route.fulfill(status=403,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'error':'bad_invite','message':'초대 비밀번호가 맞지 않습니다'}))
    if u.endswith('/api/login'): return route.fulfill(status=400,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'error':'bad_key','message':'넥슨 API 키가 올바르지 않습니다'}))
    route.fulfill(status=404,headers={'Access-Control-Allow-Origin':'*'},body='{}')
def look(pg):
    return pg.evaluate("(()=>{const e=document.querySelector('#svGate .svgerr');if(!e)return null;const c=getComputedStyle(e),b=getComputedStyle(document.body);return {t:e.textContent,color:c.color,bg:c.backgroundColor,vis:e.offsetHeight>0&&c.opacity==='1'&&c.visibility==='visible'}})()")
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':800},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route(API+'/**',fake); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(URL); pg.evaluate("a=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',a)}",API); pg.reload(); pg.wait_for_selector('#svGate #svInvite')
    pg.fill('#svGate #svInvite','wrong'); pg.press('#svGate #svInvite','Enter'); pg.wait_for_selector('#svGate .svgerr')
    l=look(pg)
    check('invite: error visible, red #ff5a5a, transparent background', l and '초대 비밀번호' in l['t'] and l['color']=='rgb(255, 90, 90)' and l['bg'] in ('rgba(0, 0, 0, 0)','transparent') and l['vis'], l)
    pg.screenshot(path=os.path.join(OUT,'b35_gate.png')); shutil.copy(os.path.join(OUT,'b35_gate.png'),'/workspace/shots/b35_gate.png')
    pg.evaluate("localStorage.setItem('mapleBossTracker.svDevice','dev-ticket'); gd.svErr=''; svGate()"); pg.wait_for_selector('#svGate #svKey')
    pg.fill('#svGate #svKey','bad_key_value'); pg.press('#svGate #svKey','Enter'); pg.wait_for_selector('#svGate .svgerr')
    l=look(pg)
    check('key step: error visible, red, transparent background', l and l['t'] and l['color']=='rgb(255, 90, 90)' and l['bg'] in ('rgba(0, 0, 0, 0)','transparent') and l['vis'], l)
    pg.screenshot(path=os.path.join(OUT,'b35_gate_key.png')); shutil.copy(os.path.join(OUT,'b35_gate_key.png'),'/workspace/shots/b35_gate_key.png')
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
