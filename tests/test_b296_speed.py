# test_b296_speed: 화면 공유 맵 전환 속도 — 윌 보상 맵(v10) → 다른 맵(입구) → 가엔슬 보상 맵(v06). 실제 tesseract.
#   연결 상태(arStart, 캔버스 스트림)로 돌려서 보스가 바뀌기까지 ms. B296_INDEX=다른 index.html 로 예전 코드도 잴 수 있음.
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); IDX=os.environ.get('B296_INDEX') or os.path.join(ROOT,'index.html')
shutil.copy(IDX,os.path.join(site,'index.html')); shutil.copy(os.path.join(ROOT,'prices.json'),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
os.makedirs(os.path.join(site,'fx'))
for v in ['v10','v06']: shutil.copy(os.path.join(ROOT,'tests','fixtures','b285',f'map_{v}.jpg'),os.path.join(site,'fx'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
RUN="""async ()=>{ const A=window.AR; A.cfg.on=false; await arOcrLoad(); const L=s=>new Promise(r=>{ const i=new Image(); i.onload=()=>r(i); i.src=s; });
  const w=await L('fx/map_v10.jpg'), s=await L('fx/map_v06.jpg'); const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'), m=A.cfg.map;
  let ph='will'; const draw=()=>{ g.drawImage(ph==='will'?w:s,0,0,1920,1080); if(ph==='other'){ g.fillStyle='#1b2230'; g.fillRect(0,0,m.w*1920,m.h*1080); g.fillStyle='#fff'; g.font='bold 15px sans-serif'; g.fillText('고요한 제단 입구',40,24); } if(A._run) requestAnimationFrame(draw); }; A._run=1; draw();
  const v=document.createElement('video'); v.muted=true; v.srcObject=cv.captureStream(30); await v.play(); arStart(v);
  const wait=async(f,ms)=>{ const t=performance.now(); while(performance.now()-t<ms){ if(f()) return Math.round(performance.now()-t); await new Promise(r=>setTimeout(r,20)); } return -1; };
  const tWill=await wait(()=>A.det.boss==='will',15000); await new Promise(r=>setTimeout(r,1500));
  ph='other'; const tClr=await wait(()=>!A.det.boss,15000);
  ph='slime'; const tSlime=await wait(()=>A.det.boss==='slime',15000); const dif=A.det.diff;
  A._run=0; arDisconnect(); return {tWill,tClr,tSlime,diff:dif,map:A.mapText}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1920,'height':1080},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    r=pg.evaluate(RUN); print('SPEED',r)
    if not os.environ.get('B296_INDEX'):
        check('윌 보상 맵 인식 1.5초 안', 0<=r['tWill']<=1500, r['tWill'])
        check('다른 맵으로 옮기면 윌 비움 4초 안', 0<=r['tClr']<=4000, r['tClr'])
        check('가엔슬 보상 맵(고요한 제단) → 가엔슬 카오스 1초 안', 0<=r['tSlime']<=1000 and r['diff']=='chaos', (r['tSlime'],r['diff']))
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
