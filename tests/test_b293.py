# test_b293: 공중 띠를 바닥 바로 위(y .72)까지 확장 — v01 실제 프레임(1080p 전체)
#   낙하 중 바닥 근처 백옥 인식 / 예전 띠는 놓침 / 내려앉은 뒤·상자 없는 장면 오검출 0
import os, sys, tempfile, shutil, subprocess, base64, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b293')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n+'.jpg'),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
 S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save&&save(); render();
 ARX.cfg.worker=false; ARX.wk=null; window._rec=[]; window.arRecord=function(k,s,via){ window._rec.push([k,via]); };
 window._frame=async(u)=>{ const im=new Image(); im.src=u; await im.decode(); const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d',{willReadFrequently:true}); g.fillStyle='#000'; g.fillRect(0,0,1920,1080); g.drawImage(im,0,0); return cv; };
 window._scan=async(u,boss,diff)=>{ ARX.det={boss,diff,cid:'c0'}; const cv=await _frame(u), r=ARX.cfg.airBand, y=Math.round(r.y*1080), h=Math.round(r.h*1080);
   const hs=await arAirScan({img:cv.getContext('2d').getImageData(0,y,1920,h)},1080,0,y,ARX.cfg.airThr); return hs.filter(h=>h.ok).map(h=>[h.k,+h.score.toFixed(3),h.x,h.y]); };
 return 1; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    r=pg.evaluate("ARX.cfg.airBand"); check('공중 띠 y .08~.72 (바닥 바로 위)',abs(r['y']-.08)<1e-9 and abs(r['y']+r['h']-.72)<1e-9,r)
    for n in ['v01_0402','v01_0412']:
      h=pg.evaluate("([u])=>_scan(u,'adversary','normal')",[u(n)]); check(f'바닥 근처 낙하 백옥 {n}',len(h)>=1 and all(x[0]=='r_white' for x in h) and 640<=h[0][3]<=760,h)
    pg.evaluate("window._old=ARX.cfg.airBand; ARX.cfg.airBand={x:0,y:.08,w:1,h:.55}")
    h=pg.evaluate("([u])=>_scan(u,'adversary','normal')",[u('v01_0402')]); check('예전 띠(.08~.63)는 놓침 (b293 원인)',len(h)==0,h)
    pg.evaluate("ARX.cfg.airBand=window._old")
    h=pg.evaluate("([u])=>_scan(u,'adversary','normal')",[u('v01_0440')]); check('바닥에 내려앉은 뒤 → 공중 0 (오검출 없음)',len(h)==0,h)
    for bo,di in [('adversary','normal'),('kaling','easy'),('jinhilla','hard')]:
      h=pg.evaluate("([u,b,d])=>_scan(u,b,d)",[u('v12_0146'),bo,di]); check(f'상자 없음 v12_0146 {bo} → 0',len(h)==0,h)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.kill(); shutil.rmtree(site,ignore_errors=True)
print('FAILS',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
