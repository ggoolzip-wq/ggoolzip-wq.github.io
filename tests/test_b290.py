# test_b290: v11(카링 이지) 끝에 '고통의 미궁 / 욕망의 제단 입구'(진 힐라 입구 맵)로 이동 → 진 힐라(난이도 빈칸 → 캐릭터 설정 하드)로 바뀌던 문제
#   입구 맵은 보스 방이 아님 → 보스 안 바꾸고 직전 인식 유지. 진짜 진 힐라 방(욕망의 제단 <하드>)은 그대로 진 힐라 하드.
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b290')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/png;base64,'+base64.b64encode(open(os.path.join(FX,n+'.png'),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]};
 S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save&&save(); render();
 window._T=1e7; const D0=Date.now; Date.now=()=>window._T; window.arItemScan=async()=>[]; window.arFindIcons=async()=>[]; ARX.stream=null; ARX.det={cid:'',boss:'',diff:'',src:''};
 window._img=async(u)=>{ const im=new Image(); im.src=u; await im.decode(); const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'); g.fillStyle='#223'; g.fillRect(0,0,1920,1080); g.drawImage(im,0,0); return cv; };
 window._step=async(u,dt)=>{ window._T+=dt; await arFrame2(await _img(u),true); const t=arTarget(); return {det:[ARX.det.boss,ARX.det.diff],tgt:t&&t.b?[t.b.id,t.diff]:null,txt:ARX.mapText,lobby:!!ARX.lobby}; };
 window._seq=async(texts,dt)=>{ const o=arOcr; let i=0; window.arOcr=async()=>texts[Math.min(i++>>1,texts.length-1)]; const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const out=[];
   for(let k=0;k<texts.length;k++){ window._T+=dt; await arFrame2(cv,true); out.push([ARX.det.boss,ARX.det.diff]); } window.arOcr=o; return out; };
 return 1; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    D=lambda t: pg.evaluate("t=>arDetectBoss(t)",t)
    for t in ['고통의 미궁\n욕망의 제단 입구','[ 고통의 미궁\n록망의 제단 입구','고통의 미궁\n혹망의 께단 입구','고통의 미궁\n옥망의 제단 입구']:
      r=D(t); check(f'입구 맵 → 무시 (b291: 보상 맵 아님 → null) {t!r}',r is None,r)
    for t,bo,di in [('고통의 미궁\n욕망의 제단 <하드>','jinhilla','hard'),('도원경 빛을 되찾은 사계 <미지>','kaling','easy'),('도원경 빛을 되찾은 사계 <이지>','kaling','easy')]:
      r=D(t); check(f'보스 방 {t!r} → {bo} {di}',r and r['boss']==bo and r['diff']==di,r)
    # 실제 미니맵 (v11 #421 카링 이지 → #691 진 힐라 입구, OCR 그대로)
    r1=pg.evaluate("u=>_step(u,500)",u('v11_0421')); check('v11 #421 실제 OCR → 카링 이지',r1['det']==['kaling','easy'],r1)
    r2=pg.evaluate("u=>_step(u,500)",u('v11_0691')); check('v11 #691 진 힐라 입구 → 카링 이지 유지 (예전: 진 힐라 하드)',r2['det']==['kaling','easy'] and r2['tgt']==['kaling','easy'],r2)
    for k in range(6): r3=pg.evaluate("u=>_step(u,2000)",u('v11_0691'))
    check('입구에 오래 있어도 진 힐라로 안 바뀜',r3['det']==['kaling','easy'],r3)
    r4=pg.evaluate("u=>_step(u,500)",u('v02_0181')); check('v02 진 힐라 방 실제 OCR → 진 힐라 하드 (입구에서 들어가면 바로 바뀜)',r4['det']==['jinhilla','hard'],r4)
    s=pg.evaluate("""()=>{ ARX.det={cid:'',boss:'',diff:'',src:''}; return _seq(['고통의 미궁\\n욕망의 제단 입구','고통의 미궁\\n욕망의 제단 <하드>','','고통의 미궁\\n욕망의 제단 입구'],500); }""")
    check('인식 없는 상태에서 입구 → 보스 없음, 방 → 진 힐라 하드, 다시 입구 → 유지',s==[['',''],['jinhilla','hard'],['jinhilla','hard'],['jinhilla','hard']],s)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.kill(); shutil.rmtree(site,ignore_errors=True)
print('FAILS',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
