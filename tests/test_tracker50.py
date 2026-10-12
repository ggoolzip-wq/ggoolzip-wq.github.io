# b66→b67: NEXON Open API 표기 — 서버 모드 첫 화면(입장 화면 없음)·캐릭터 추가 창(본계정 키 등록만)·github.io 첫 화면 / 다크 전용(테마 버튼 없음)
import os, sys, json, time, subprocess, shutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR') or '/workspace/maple-boss-tracker'
os.makedirs(SHOTDIR, exist_ok=True)
PORT=8850
ATTRIB='Data based on NEXON Open API'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def vis_in_vp(pg, sel):
    return pg.evaluate("""sel=>{
      const e=document.querySelector(sel); if(!e) return {ok:false,why:'missing'};
      const r=e.getBoundingClientRect(), cs=getComputedStyle(e);
      const ok=r.width>0&&r.height>0&&r.top>=0&&r.bottom<=innerHeight+0.5&&r.left>=-1&&r.right<=innerWidth+1
        && cs.visibility!=='hidden'&&cs.display!=='none'&&parseFloat(cs.opacity||'1')>0;
      return {ok, top:r.top, bottom:r.bottom, h:innerHeight, color:cs.color, text:e.textContent.trim(), fs:cs.fontSize, ta:cs.textAlign};
    }""", sel)
def shot(pg,name,loc=None):
    pth=os.path.join(OUT,name); (loc or pg).screenshot(path=pth); shutil.copy(pth,os.path.join(SHOTDIR,name)); print('SHOT',os.path.join(SHOTDIR,name))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(0.7)
API='https://fake-sync-b67.example'
def fake(route): route.fulfill(status=404,headers={'Access-Control-Allow-Origin':'*'},body='{}')
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',args=['--no-sandbox'])
    # --- 서버 모드, 처음 온 사람: 입장 화면 없이 바로 대시보드 ---
    pg=b.new_page(viewport={'width':1280,'height':800},locale='ko-KR',color_scheme='light'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route(API+'/**',fake); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"items":[]}'))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("a=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',a);localStorage.setItem('mapleBossTracker.v1',JSON.stringify({version:5,theme:'light',characters:[],settings:{}}))}",API)
    pg.reload(); pg.wait_for_timeout(600)
    check('landing: no gate, no password prompt, dashboard visible', pg.locator('#svGate').count()==0 and pg.locator('input[type=password]:visible').count()==0 and pg.is_visible('#charList') and pg.is_visible('#addCharBtn'))
    ea=pg.inner_text('.empty-attrib') if pg.locator('.empty-attrib').count() else ''; ft=pg.inner_text('.foot')
    check('landing: empty view + footer carry NEXON attribution', ea==ATTRIB and ATTRIB in ft, (ea,ft[:100]))
    check('landing: attribution visible without scrolling', vis_in_vp(pg,'.empty-attrib')['ok'], vis_in_vp(pg,'.empty-attrib'))
    check('dark only: saved light theme + light OS preference ignored, no toggle, theme removed from storage',
          pg.evaluate("document.documentElement.dataset.theme")=='dark' and pg.locator('#themeBtn').count()==0 and pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).theme")==None,
          (pg.evaluate("document.documentElement.dataset.theme"),pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).theme")))
    check('header: ☁ 로그인 (logged out)', pg.inner_text('#gBtn').strip()=='☁ 로그인', pg.inner_text('#gBtn'))
    shot(pg,'oct12e_landing.png')
    # --- + 추가 → 본계정 키 등록만 ---
    pg.click('#addCharBtn'); pg.wait_for_selector('#svMainKey'); pg.wait_for_timeout(200)
    only=pg.evaluate("""(()=>{const m=document.querySelector('#importModal .modal');const vis=e=>e&&e.offsetParent!==null;
      return {secs:[...m.querySelectorAll('section.addsec')].filter(vis).map(s=>s.id||'?'),inputs:[...m.querySelectorAll('input,select,button')].filter(vis).map(e=>e.id||e.className)}})()""")
    check('modal: only the 본계정 key section (key input + 등록 button), no alt/spare rows, no character picker',
          only['secs']==['svMainSec'] and set(only['inputs'])<={'svMainKey','svMainBtn','pin acclbl','impClose'} and 'svMainKey' in only['inputs'] and 'svMainBtn' in only['inputs'], only)
    b71=pg.evaluate("(()=>{const s=document.querySelector('#svMainSec');const vis=e=>e&&e.offsetParent!==null;return {text:s.innerText.trim(),ph:document.querySelector('#svMainKey').placeholder,ctl:[...s.querySelectorAll('input,button,a,select')].filter(vis).map(e=>e.id||e.tagName)}})()")
    check("b71: 등록 칸 = 'API키 입력' 입력 + 등록 버튼만 (안내 문구·제목·링크 없음)", b71['text']=='등록' and b71['ph']=='API키 입력' and b71['ctl']==['svMainKey','svMainBtn'], b71)
    v=vis_in_vp(pg,'.addm .svmattrib'); check('modal: NEXON attribution visible (1280x800)', v['ok'] and v['text']==ATTRIB, v)
    shot(pg,'oct12e_mainkey_modal.png')
    pg.set_viewport_size({'width':390,'height':844}); pg.wait_for_timeout(200)
    v=vis_in_vp(pg,'.addm .svmattrib'); check('modal mobile: attribution in viewport, no horizontal overflow', v['ok'] and not pg.evaluate("document.documentElement.scrollWidth>innerWidth"), v)
    shot(pg,'oct12e_mainkey_modal_mobile.png')
    pg.click('#impClose'); pg.wait_for_timeout(100)
    check('closing the modal leaves the dashboard', not pg.evaluate("document.querySelector('#importModal').classList.contains('show')"))
    # --- github.io (드라이브 모드): 게이트·본계정 칸 없음, 표기 그대로 ---
    pg2=b.new_page(viewport={'width':1280,'height':800},locale='ko-KR')
    pg2.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg2.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"items":[]}'))
    pg2.goto(f'http://127.0.0.1:{PORT}/index.html'); pg2.evaluate("localStorage.clear()"); pg2.reload(); pg2.wait_for_timeout(500)
    ea=pg2.inner_text('.empty-attrib') if pg2.locator('.empty-attrib').count() else ''
    check('github.io mode: no gate, attribution on first run', pg2.locator('#svGate').count()==0 and ea==ATTRIB and ATTRIB in pg2.inner_text('.foot'))
    pg2.click('#addCharBtn'); pg2.wait_for_selector('#newAccKey',state='attached')
    check('github.io mode: + 추가 = normal key modal (no main-key-only section)', pg2.locator('#svMainSec').count()==0 and pg2.is_visible('#newAccKey'))
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
