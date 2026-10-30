# test_b292: 30fps 공중·바닥 — 보상 맵/상자 깬 직후만 full-rate, 줄여서 뜸, 밀린 프레임 버림, 패널 표시
# (원본 b289 머리말) 보상 상자를 부순 직후 바닥에 떨어지기 전(공중) 아이템 — 실제 영상 v01·v07·v11 공중 프레임 띠(1080p y 86~680)
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
 window._reset=()=>{ ARX.abuf=[]; ARX.alocs=[]; ARX.tracks=[]; ARX.airLog=[]; ARX.airT=0; ARX.burstUntil=0; ARX.pf=null; arPf(); window._rec=[]; };
 return 1; }"""
RATE="""async ([src,burst])=>{ _reset(); ARX.det={boss:'kaling',diff:'easy',cid:'c0',src}; if(burst) arBurst(1e6); ARX.apBusy=true; const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080;
  let n=0; for(let i=0;i<30;i++){ const T=1000+i*1000/30; if(arAirWatch(cv,T,1e6+T)!==false) n++; } const e=ARX.abuf[ARX.abuf.length-1]; ARX.apBusy=false; ARX.abuf=[]; return {n,hot:ARX.airHot,sh:e&&e.sh,w:e&&e.w,k:e&&e.k}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    c=pg.evaluate("({a:ARX.cfg.airBurstFps,s:ARX.cfg.airBurstSec,h:ARX.cfg.airMaxH,st:ARX.cfg.airStale,i:ARX.cfg.itemBurstFps,f:ARX.cfg.airFps})")
    check('기본값 30fps·4초·720·200ms·바닥 10',c=={'a':30,'s':4,'h':720,'st':200,'i':10,'f':6},c)
    r=pg.evaluate(RATE,['보상 맵',False]); check('보상 맵 → 1초에 30장 (full-rate)',r['n']==30 and r['hot'],r)
    check('줄여서 뜸: 1080 → 720 높이, 폭 1280',r['sh']==720 and r['w']==1280,r)
    r=pg.evaluate(RATE,['',False]); check('보상 맵 아님 → 6장',r['n']==6 and not r['hot'],r)
    r=pg.evaluate(RATE,['',True]); check('상자 깬 직후(burst) → 30장',r['n']==30 and r['hot'],r)
    r=pg.evaluate("()=>{ _reset(); ARX.det={src:''}; arBurst(0); return [arHot(3999),arHot(4001)]; }"); check('burst 4초 뒤 끝',r==[True,False],r)
    r=pg.evaluate("""async ()=>{ _reset(); ARX.det={boss:'kaling',diff:'easy',cid:'c0',src:'보상 맵'}; ARX.apBusy=true; const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080;
      for(let i=0;i<30;i++){ const T=1000+i*1000/30; arAirWatch(cv,T,1e6+T); } const d0=ARX.pf.airDrop||0; window.arCandidates=()=>[]; await arAirStep(); return {d0,drop:(ARX.pf.airDrop||0)-d0,full:ARX.pf.air,done:ARX.abuf.filter(e=>e.done).length,n:ARX.abuf.length}; }""")
    check('밀린 옛 프레임은 버림(전체 검사 안 함)',r['drop']>=3 and r['full']==1 and r['done']==r['drop']+1,r)
    pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n+'.jpg'),'rb').read()).decode()
    seq=[[u('v02_0187'),0],[u('v11_0428'),100],[u('v11_0431'),200],[u('v11_0437'),400],[u('v02_0187'),500]]
    r=pg.evaluate("""async ([fr])=>{ _reset(); ARX.det={boss:'kaling',diff:'easy',cid:'c0',src:'보상 맵'}; ARX.apBusy=true;
      for(const [x,T] of fr){ const cv=await _frame(x); arAirWatch(cv,T,1e6+T); while(await arAirStep()); } ARX.apBusy=false; return {rec:window._rec,log:ARX.airLog.map(l=>l.hits[0])}; }""",[seq])
    xy=[(h[2],h[3]) for h in r['log']]
    check('줄여 뜬 공중 → 백옥 1번 기록',r['rec']==[['r_white','공중']],r)
    check('기록 좌표는 원래 1080 화면 기준',xy and all(850<=x<=1100 and 250<=y<=650 for x,y in xy),xy)
    t=pg.evaluate("()=>{ ARX.video={}; ARX.pf={t0:performance.now()-2000,frames:60,watched:60,missed:0,bannerMs:0,banners:0,items:0,iskip:0,air:10,airMs:300,airDrop:5,last:null}; ARX.airHot=true; const s=arPerfText(); ARX.video=null; return s; }")
    check('패널: 분석 fps·놓친 프레임·공중·버린 프레임·full-rate',all(k in t for k in ['분석 fps','놓친 프레임','공중 10회','버린 프레임 5','full-rate']),t)
    src=open(os.path.join(ROOT,'index.html'),encoding='utf-8').read()
    check('rVFC 루프: full-rate 때 바닥도',"if(ARX.airHot&&!ARX.itemBusy)" in src)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.kill(); shutil.rmtree(site,ignore_errors=True)
print('FAILS',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
