# test_b415 (t495): 현재 1920 최적 비율 실영상(게임 바 캡처)이 기본 비율로 오인되지 않고,
# 상태바 'Lv.NNN 이름' 칸이 글자를 포함하며, 한글 이름 토큰이 목록과 같으면 캐릭터로 확정된다.
import os, sys, json, base64, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b415')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
du=lambda f:'data:image/png;base64,'+base64.b64encode(open(os.path.join(FX,f),'rb').read()).decode()
DET="""async (u)=>{ const im=new Image(); await new Promise(r=>{im.onload=r; im.src=u;});
  const w=1920,h=1080, cv=document.createElement('canvas'); cv.width=w; cv.height=h;
  const g=cv.getContext('2d'); g.fillStyle='#000'; g.fillRect(0,0,w,h); g.drawImage(im,0,h-im.height);
  ARX.bbox=null; ARX.bbKey=''; ARX.prof=null; ARX.geo=null;
  const P=await arProfDetect(cv);
  const r=arR('name',cv); const name=[Math.round(r.x*w),Math.round(r.y*h),Math.round(r.w*w),Math.round(r.h*h)];
  const Sall={characters:[{id:'c0',name:'더래플'}], activeId:'c0'};
  const prev=S; Object.assign(S,Sall);
  const cid=arDetectChar('Lv.289 더래플');
  const cid2=arDetectChar('4.289 더래플');
  Object.assign(S,prev);
  return P?{id:P.id,s:P.s,lab:P.lab,sc:P.score,name,cid,cid2}:null; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1200,'height':800},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    for fn,tag in [('status_v2.png','벨로나 보상'),('status_v3.png','세렌 보상')]:
      r=pg.evaluate(DET, du(fn))
      check(f'{tag} 프로필 = 1920 최적 비율', bool(r) and r['id']=='1920o' and r['s']==1 and not r.get('est') and r['sc']>=.8, r)
      # 이름 칸이 상태바 글자(y≈1028~1051)를 포함
      y,h=(r['name'][1],r['name'][3]) if r else (0,0)
      check(f'{tag} 닉네임 칸이 Lv 글자 위치(1028~1051)를 포함', r and y<=1028 and y+h>=1051, r and r['name'])
      check(f'{tag} 더래플 토큰 → 캐릭터 확정', r and r['cid']=='c0' and r['cid2']=='c0', r)
    b.close()
finally:
  srv.terminate()
if errs: print('errs', errs[:5]); fails.append('pageerror')
if fails:
    print('FAILED', fails); sys.exit(1)
print('OK')
