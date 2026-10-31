# test_b327_syl (t620): 상태바 닉네임 음절 템플릿 대조 — 실제 화면(소다래버린스 스샷, 영상 A·B 겟로스트로바)
#   (1) 홈페이지와 같은 arNameWatch 경로로 0.1초 안에 '음절'로 확정  (2) 목록에 정답이 없고 한 글자 다른/앞부분만 같은 이름만 있으면 확정 안 함(오인식 0)
#   (3) x0: 'Lv.281' 의 '1' 을 이름 시작으로 잡지 않음  (4) 템플릿 없는 글자가 있는 이름은 음절 대조 안 함(OCR 로 넘김)
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b327')
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
RUN="""async ([src,names])=>{ S.characters=names.map((n,i)=>({id:'c'+i,name:n,level:280,job:'',world:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}));
  const im=new Image(); im.src=src; await im.decode(); ARX.ocr=null; ARX.ocrP=Promise.resolve(); ARX.prof=null; await arProfDetect(im); ARX.profT=Date.now(); ARX.profBusy=false;
  ARX.det=ARX.det||{}; ARX.det.cid=null; ARX.nprev=null; ARX.nameOk=false; ARX.nameSrc=null; const t0=performance.now(); arNameWatch(im); const ms=performance.now()-t0;
  const H=arNameHp(im,im.width,im.height,arR('name',im)); const c=S.characters.find(c=>c.id===ARX.det.cid); return {pick:c?c.name:null,src:ARX.nameSrc,ms,x0:H.x0,sc:ARX.nSylSc}; }"""
G='겟로스트로바'; SODA='소다래버린스'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    near_s=['소다래버린','소다래머린스','다래버린스','소다래버린소','스다래버린스','림강훈망','트딕이']
    near_g=['겟로스트로','겟로스트','갯로스트로바','겟로소트로바','겟로스트로버','zetking','터래플']
    r=pg.evaluate(RUN,[u('soda'),[SODA]+near_s+[G]]); check('소다 스샷 → 소다래버린스 (음절, 0.1초 안)',r['pick']==SODA and r['src']=='음절' and r['ms']<100,r)
    for n in ['B22','B_011','A_041']:
      r=pg.evaluate(RUN,[u(n),near_g+[G,SODA]]); check(f'{n} → 겟로스트로바 (음절)',r['pick']==G and r['src']=='음절',r)
      check(f'{n} x0 = 닉네임 시작(레벨 숫자 아님)',60<=r['x0']<=75,r['x0'])
      r=pg.evaluate(RUN,[u(n),near_g+[SODA]]); check(f'{n} 정답 없는 목록 → 확정 안 함',r['pick'] is None,r)
    r=pg.evaluate(RUN,[u('soda'),near_s+[G]]); check('소다 정답 없는 목록 → 확정 안 함',r['pick'] is None,r)
    r=pg.evaluate(RUN,[u('B22'),['갯로스트로바']]); check('템플릿 없는 글자(갯) → 음절 대조 안 함',r['pick'] is None and not r['sc'],r)
    b.close()
finally:
  srv.kill()
check('페이지 오류 없음',not errs,errs[:3])
print('\nRESULT', 'FAIL' if fails else 'PASS', fails); sys.exit(1 if fails else 0)
