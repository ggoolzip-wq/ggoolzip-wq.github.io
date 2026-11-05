# test_b381 (t422): PIP 최소화 중 ·득템 기록 확인(득템 대기)일 때만 보스 칸(.ar-pminrow) 눌러 최소화 해제. 평소엔 유지. MBT_SHOTDIR 에 b381_*.png
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
STUB="""()=>{ window.arBoxOk=()=>true; window.arTarget=()=>({c:S.characters[0]}); window.arToast=()=>{}; window.arCandidates=()=>[{k:window.__k,b:findBoss(window.AR.det.boss)}]; }"""
REC="""([b,k])=>arSessAdd(k,findBoss(b).name,S.characters[0].name)"""
def shot(pg,n):
    f=pg.locator('#fakePip').bounding_box(); pg.screenshot(path=n,clip={'x':f['x']-10,'y':f['y']-10,'width':f['width']+20,'height':f['height']+20})
# PIP 안 내용이 창 안에 다 보이는지 (스크롤 없이, 목록만 자체 스크롤)
FIT="""()=>{ const d=document.getElementById('fakePip').contentDocument, w=d.defaultView; return {sh:d.documentElement.scrollHeight, ih:w.innerHeight, iw:w.innerWidth, sw:d.documentElement.scrollWidth}; }"""
VIS="""s=>{ const d=document.getElementById('fakePip').contentDocument, e=d.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return {h:r.height,b:r.bottom,ih:d.defaultView.innerHeight,show:getComputedStyle(e).display!=='none'&&r.height>0}; }"""

B="""()=>{ const d=document.getElementById('fakePip').contentDocument, q=s=>d.querySelector(s), R=e=>e?e.getBoundingClientRect():null, vis=s=>{ const e=q(s); return !!e&&getComputedStyle(e).display!=='none'&&R(e).height>0; }; const pc=q('.ar-pipchar'), mb=q('.ar-pipchar .ar-pipminb'), nw=q('.ar-pmnew'), row=q('.ar-pminrow'), cb=q('.ar-cboss');
 return {pc:pc.textContent, btn:mb?mb.textContent:null, btnCls:mb?mb.className:'', btnR:mb?R(mb).right:0, iw:d.defaultView.innerWidth, ih:d.defaultView.innerHeight, sh:d.documentElement.scrollHeight, min:d.body.classList.contains('pip-min'), meso:vis('.ar-pipmeso'), rec:vis('.ar-piprec'), sale:vis('.ar-pipsale'), h2:vis('.ar-cboss h2'), row:row?row.textContent:null, rowCls:row?row.className:'', rowAnim:row?getComputedStyle(row).animationName:null, rowShine:row?getComputedStyle(row,'::after').animationName:null, nw:nw?nw.textContent:null, nwc:nw?getComputedStyle(nw).color:null, nwAnim:nw?getComputedStyle(nw).animationName:null, cbb:R(cb).bottom, minH:window.AR.pip.minH}; }"""
CLICK="""()=>document.getElementById('fakePip').contentDocument.querySelector('.ar-pipminb').click()"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark',device_scale_factor=int(os.environ.get('B376_DSF','1'))); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arStart(document.createElement('video')); }"); pg.evaluate(REW,'lucid'); pg.evaluate(STUB)
    pg.evaluate(FAKE); pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(500)
    pg.evaluate("()=>{ ARX.det.cid='c0'; }"); pg.wait_for_timeout(500)
    RC="()=>{ const d=document.getElementById('fakePip').contentDocument; d.querySelector('.ar-pminrow .ar-pml').click(); }"
    MIN="()=>document.getElementById('fakePip').contentDocument.body.classList.contains('pip-min')"
    pg.evaluate(CLICK); pg.wait_for_timeout(400); check('최소화됨',pg.evaluate(MIN))
    pg.evaluate(RC); pg.wait_for_timeout(400)
    check('득템 없음: 보스 칸 눌러도 최소화 유지',pg.evaluate(MIN) and not pg.evaluate("()=>!!document.getElementById('fakePip').contentDocument.querySelector('.ar-pmnew')"))
    shot(pg,os.path.join(OUT,'b381_min_idle_click.png'))
    pg.evaluate(STUB); pg.evaluate("()=>{ window.__k='eye'; arRecord('eye',.9,'t'); }"); pg.wait_for_timeout(400)
    nw=pg.evaluate("()=>{ const d=document.getElementById('fakePip').contentDocument; const r=d.querySelector('.ar-pminrow'); return [!!d.querySelector('.ar-pmnew'), getComputedStyle(r).cursor]; }")
    check('득템: ·득템 기록 확인 + 손가락 커서',nw==[True,'pointer'],nw)
    shot(pg,os.path.join(OUT,'b381_min_warn.png'))
    pg.evaluate(RC); pg.wait_for_timeout(400)
    vis=pg.evaluate("()=>{ const e=document.getElementById('fakePip').contentDocument.querySelector('.ar-pipsale'); return !!e&&getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().height>0; }")
    check('득템 중 보스 칸 클릭 → 최소화 해제 + 고르기/수익 칸 보임',not pg.evaluate(MIN) and vis,vis)
    check('해제 저장',pg.evaluate("localStorage.getItem('arPipMin')")=='0')
    shot(pg,os.path.join(OUT,'b381_unmin.png'))
    pg.evaluate("()=>arDisconnect()"); b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
