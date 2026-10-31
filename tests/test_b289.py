# test_b289: 보상 상자를 부순 직후 바닥에 떨어지기 전(공중) 아이템 — 실제 영상 v01·v07·v11 공중 프레임 띠(1080p y 86~680)
#   (1) 공중 백옥 인식 (10° 회전, 보스 드롭 후보만)  (2) 45° 회전이면 놓침(원인)  (3) 상자 없는 장면·다른 보스 후보 = 0
#   (4) 0.4초뿐인 v11: 버퍼+후보 근처 다시 보기 → 1번만 기록  (5) Worker 소스에 arXcache
import os, sys, tempfile, shutil, subprocess, base64, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b289')
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
 window._frame=async(u)=>{ const im=new Image(); im.src=u; await im.decode(); const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d',{willReadFrequently:true}); g.fillStyle='#000'; g.fillRect(0,0,1920,1080); g.drawImage(im,0,86); return cv; };
 window._scan=async(u,boss,diff)=>{ ARX.det={boss,diff,cid:'c0'}; const cv=await _frame(u), r=ARX.cfg.airBand, y=Math.round(r.y*1080), h=Math.round(r.h*1080);
   const hs=await arAirScan({img:cv.getContext('2d').getImageData(0,y,1920,h)},1080,0,y,ARX.cfg.airThr); return hs.filter(h=>h.ok).map(h=>[h.k,+h.score.toFixed(3),h.x,h.y]); };
 return 1; }"""
SEQ="""async ([fr,boss,diff])=>{ ARX.det={boss,diff,cid:'c0'}; ARX.abuf=[]; ARX.alocs=[]; ARX.tracks=[]; ARX.airLog=[]; ARX.airT=0; ARX.apBusy=true; window._rec=[]; let busy=0;
  for(const [u,T] of fr){ const cv=await _frame(u); arAirWatch(cv,T,1e6+T); while(busy<=T){ const t0=performance.now(); if(!await arAirStep()) break; busy=Math.max(busy,T)+(performance.now()-t0); } }
  while(await arAirStep()); ARX.apBusy=false; return {rec:window._rec,log:ARX.airLog.length}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    for n,bo,di in [('v01_0366','adversary','normal'),('v07_0206','bellona','easy'),('v11_0431','kaling','easy')]:
      h=pg.evaluate("([u,b,d])=>_scan(u,b,d)",[u(n),bo,di]); check(f'공중 백옥 {n}',len(h)>=1 and all(x[0]=='r_white' for x in h) and 150<=h[0][3]<=600,h)
    st=pg.evaluate("ARX.cfg.airStep"); pg.evaluate("ARX.cfg.airStep=45")
    h=pg.evaluate("([u])=>_scan(u,'kaling','easy')",[u('v11_0431')]); check('45° 회전이면 놓침 (b288 원인)',len(h)==0,h); pg.evaluate(f"ARX.cfg.airStep={st}")
    for n in ['v02_0187','v12_0146']:
      for bo,di in [('kaling','easy'),('jinhilla','hard')]:
        h=pg.evaluate("([u,b,d])=>_scan(u,b,d)",[u(n),bo,di]); check(f'상자 없음 {n} {bo} → 0',len(h)==0,h)
    h=pg.evaluate("([u])=>_scan(u,'jinhilla','hard')",[u('v11_0431')]); check('진 힐라 후보(백옥 없음) → 0',len(h)==0,h)
    seq=[[u('v02_0187'),0],[u('v11_0428'),170],[u('v11_0431'),340],[u('v11_0437'),510],[u('v02_0187'),680],[u('v02_0187'),850]]
    r=pg.evaluate(SEQ,[seq,'kaling','easy']); check('v11 0.4초 공중 → 백옥 1번 기록(공중)',r['rec']==[['r_white','공중']],r)
    r=pg.evaluate(SEQ,[seq+[[u('v11_0431'),1020],[u('v11_0437'),1190]],'kaling','easy']); check('같은 자리 또 보여도 1번',len(r['rec'])==1,r)
    r=pg.evaluate(SEQ,[[[u('v02_0187'),0],[u('v12_0146'),200],[u('v02_0187'),400]],'kaling','easy']); check('상자 없는 연속 프레임 → 기록 0',r['rec']==[],r)
    src=pg.evaluate("arStart.toString()+arWorkerSrc?.toString?.()") if pg.evaluate("typeof arWorkerSrc!=='undefined'") else open(os.path.join(ROOT,'index.html'),encoding='utf-8').read()
    check('Worker 소스에 arXcache·AR_XC',"'const AR_XC=new WeakMap();\\n'+[" in src and 'arXcache,' in src and 'arVarDist,' in src)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.kill(); shutil.rmtree(site,ignore_errors=True)
print('FAILS',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
