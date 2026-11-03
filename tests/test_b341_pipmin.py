# test_b341 (t646): PIP 창 처음 크기 = 최소 크기. 더 줄이면 resizeTo 로 되돌림 + CSS 최소 크기, 키우기는 됨. MBT_SHOTDIR 에 pip_min.png
#  headless 에 documentPictureInPicture 없음 → iframe 창 흉내(resizeTo = iframe 크기 바꿈)
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
REW="""b=>{ const A=window.AR; A.det.boss=b; A.det.diff='hard'; A.rew={boss:b,diff:'hard',hash:null}; arLivePaint(); }"""
FAKE="""()=>{ Object.defineProperty(window,"documentPictureInPicture",{configurable:true,value:{requestWindow:async o=>{ const f=document.createElement('iframe'); f.id='fakePip'; f.style.cssText=`position:fixed;right:20px;top:20px;width:${o.width}px;height:${o.height}px;z-index:99999;border:0;outline:1px solid #39ff7a;background:#000`; f.srcdoc='<!doctype html><html><head></head><body></body></html>'; const ld=new Promise(r=>f.onload=r); document.documentElement.append(f); await ld; const w=f.contentWindow; Object.defineProperty(w,'outerWidth',{get:()=>w.innerWidth}); Object.defineProperty(w,'outerHeight',{get:()=>w.innerHeight}); w.resizeTo=(x,y)=>{ window.__rz=(window.__rz||0)+1; f.style.width=x+'px'; f.style.height=y+'px'; }; w.close=()=>{ w.dispatchEvent(new Event('pagehide')); f.remove(); }; return w; }}}); }"""
STUB="""()=>{ window.arBoxOk=()=>true; window.arTarget=()=>({c:S.characters[0]}); window.arToast=()=>{}; window.arCandidates=()=>[{k:window.__k,b:findBoss(AR.det.boss)}]; }"""
REC="""([b,k])=>arSessAdd(k,findBoss(b).name,S.characters[0].name)"""
PIPTXT="()=>{ const d=document.getElementById('fakePip')?.contentDocument; const e=d&&d.querySelector('.ar-piprec'); return e?e.innerText:null; }"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arStart(document.createElement('video')); }"); pg.evaluate(REW,'lucid'); pg.evaluate(REC,['lucid','eye'])
    pg.evaluate(FAKE); pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(400)
    sz=lambda: pg.evaluate("()=>{ const f=document.getElementById('fakePip'); const w=f.contentWindow; return [w.innerWidth,w.innerHeight]; }")
    m=pg.evaluate("()=>[window.AR.pip.minW,window.AR.pip.minH]"); s0=sz()
    check('처음 크기 = 최소 크기',s0==m,(s0,m))
    check('처음 크기 = b347 짧은 창(320×286)',m==[320,286],m)
    pg.evaluate("()=>{ const f=document.getElementById('fakePip'); f.style.width='200px'; f.style.height='150px'; }"); pg.wait_for_timeout(300)
    s1=sz(); check('더 작게 줄이면 최소 크기로 되돌아감',s1[0]>=m[0] and s1[1]>=m[1] and pg.evaluate('window.__rz')>=1,(s1,m))
    pg.evaluate("()=>{ const f=document.getElementById('fakePip'); f.style.width='%dpx'; f.style.height='%dpx'; }"%(m[0]+120,m[1]+80)); pg.wait_for_timeout(300)
    check('키우기는 그대로',sz()==[m[0]+120,m[1]+80],sz())
    css=pg.evaluate("()=>{ const d=document.getElementById('fakePip').contentDocument; return [getComputedStyle(d.body).minWidth,getComputedStyle(d.body).minHeight]; }")
    check('CSS 최소 크기',css==['%dpx'%m[0],'%dpx'%m[1]],css)
    pg.evaluate("()=>{ const f=document.getElementById('fakePip'); f.style.width='%dpx'; f.style.height='%dpx'; }"%tuple(m)); pg.wait_for_timeout(300)
    f=pg.locator('#fakePip').bounding_box(); pg.screenshot(path=os.path.join(OUT,'pip_min.png'),clip={'x':f['x']-10,'y':0,'width':f['width']+20,'height':f['y']+f['height']+10})
    pg.evaluate("()=>arDisconnect()")
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
