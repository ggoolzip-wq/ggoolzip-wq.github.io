# test_b346 (t650): 화면 공유 시작 → PIP 자동 열기(사용자 동작 남아 있을 때) / 만료면 한 번 클릭 안내, 위치 = 메이플 창 오른쪽 가운데 계산, moveTo 막히면 안내
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save(); S.tab='auto'; renderAuto(); }"""
# 가짜 PiP: iframe, moveTo = 크롬처럼 아무 것도 안 함(window.__mv 기록만)
FAKE="""(act)=>{ window.__act=act; Object.defineProperty(navigator,'userActivation',{configurable:true,get:()=>({isActive:window.__act,hasBeenActive:true})});
 Object.defineProperty(screen,'availLeft',{configurable:true,get:()=>0}); Object.defineProperty(screen,'availTop',{configurable:true,get:()=>0}); Object.defineProperty(screen,'availWidth',{configurable:true,get:()=>1920}); Object.defineProperty(screen,'availHeight',{configurable:true,get:()=>1040});
 Object.defineProperty(window,"documentPictureInPicture",{configurable:true,value:{requestWindow:async o=>{ if(!window.__act&&!window.__clicked) throw new DOMException('no activation','NotAllowedError'); const f=document.createElement('iframe'); f.id='fakePip'; f.style.cssText=`position:fixed;right:20px;top:20px;width:${o.width}px;height:${o.height}px;z-index:99999;border:0;outline:1px solid #39ff7a;background:#000`; f.srcdoc='<!doctype html><html><head></head><body></body></html>'; const ld=new Promise(r=>f.onload=r); document.documentElement.append(f); await ld; const w=f.contentWindow; Object.defineProperty(w,'outerWidth',{get:()=>w.innerWidth}); Object.defineProperty(w,'outerHeight',{get:()=>w.innerHeight}); w.moveTo=(x,y)=>{ window.__mv=[x,y]; }; w.resizeTo=()=>{}; w.close=()=>{ w.dispatchEvent(new Event('pagehide')); f.remove(); }; return w; }}});
 navigator.mediaDevices.getDisplayMedia=async()=>{ const c=document.createElement('canvas'); c.width=1366; c.height=768; c.getContext('2d').fillRect(0,0,9,9); const s=c.captureStream(5); const t=s.getVideoTracks()[0]; t.getSettings=()=>({width:1366,height:768,displaySurface:'window'}); return s; };
 document.addEventListener('click',e=>{ if(e.target.closest('#arPipAsk [data-pa="ok"]')) window.__clicked=1; },true); }"""
def run(b,act):
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate(FAKE,act); pg.evaluate("()=>arConnect()"); pg.wait_for_timeout(700); return pg
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=run(b,True)
    check('사용자 동작 남음 → PIP 자동으로 열림',pg.evaluate("()=>!!window.AR.pip&&!!document.getElementById('fakePip')"))
    check('한 번 클릭 안내는 안 뜸',pg.evaluate("()=>{ const a=document.getElementById('arPipAsk'); return !a||a.hidden; }"))
    m=pg.evaluate("()=>[window.AR.pip.minW,window.AR.pip.minH]"); T=pg.evaluate("()=>window.AR.pipPos"); mv=pg.evaluate("()=>window.__mv")
    # 1366x768 창 공유(dpr 1), 화면 1920x1040 가운데 가정 → 창 x 277..1643, y 136..904
    ex=277+1366-m[0]; ey=round(136+(768-m[1])/2)
    check('최소 크기 = b349 짧은 창+캐릭터 줄(b350 320×368)',m==[320,368],m)
    check('목표 = 메이플 창 오른쪽 가운데',T['gw']==1366 and T['gh']==768 and abs(T['x']-ex)<=1 and abs(T['y']-max(0,ey))<=1,(T,ex,ey))
    check('moveTo 시도함',mv==[T['x'],T['y']],mv)
    pg.wait_for_timeout(300)
    check('moveTo 막혀도 위치 안내 없음(b347)',pg.evaluate("()=>!document.getElementById('fakePip').contentDocument.querySelector('.ar-piphint')"))
    f=pg.locator('#fakePip').bounding_box(); pg.screenshot(path=os.path.join(OUT,'pip_auto.png'),clip={'x':f['x']-10,'y':0,'width':f['width']+20,'height':f['y']+f['height']+10})
    pg.evaluate("()=>arPipClose()"); pg.wait_for_timeout(200)
    pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(400)
    check('기존 PIP 버튼 그대로 동작',pg.evaluate("()=>!!window.AR.pip"))
    pg.evaluate("()=>arDisconnect()"); pg.close()
    pg=run(b,False)
    check('동작 만료 → 자동으로 안 열림',pg.evaluate("()=>!window.AR.pip&&window.AR.pipAuto==='expired'"))
    check('눈에 띄는 한 번 클릭 안내',pg.evaluate("()=>{ const a=document.getElementById('arPipAsk'); return !!a&&!a.hidden&&a.getBoundingClientRect().width>200; }"))
    pg.screenshot(path=os.path.join(OUT,'pip_ask.png'))
    pg.locator('#arPipAsk [data-pa="ok"]').click(); pg.wait_for_timeout(500)
    check('안내 클릭 → PIP 열리고 안내 사라짐',pg.evaluate("()=>!!window.AR.pip&&document.getElementById('arPipAsk').hidden"))
    # 모니터 공유 1920x1080 @ dpr 1 → x = 1920-W, 가운데
    T2=pg.evaluate("()=>{ window.AR.stream.getVideoTracks()[0].getSettings=()=>({width:1920,height:1080,displaySurface:'monitor'}); return arPipTarget(320,368); }")
    check('모니터 공유: 화면 오른쪽 가운데',T2['x']==1600 and T2['y']==336,T2)
    pg.evaluate("()=>arDisconnect()"); b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
