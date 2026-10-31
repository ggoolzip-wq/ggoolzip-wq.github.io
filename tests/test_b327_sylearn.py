# test_b327_sylearn (t622): OCR 정확 일치로 확정된 이름의 음절을 그 화면에서 잘라 localStorage('arSyl')에 저장 → 다른 목록 이름도 음절로 0.1초 안에 확정
#   실제 화면 A_041(겟로스트로바) 에서 '겟','바' 템플릿을 지운 상태로 시작. A_041_roba = 같은 화면의 '로바' 두 칸을 이름 자리로 옮긴 합성(실제 픽셀).
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b327')
fails=[]; errs=[]; reqs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n+'.jpg'),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
G='겟로스트로바'; NAMES=[G,'로바','바로','로버','겟로','소다래버린스']
PREP="()=>{ delete AR_SYL['겟']; delete AR_SYL['바']; ARX.sylT=null; ARX.sylPend=null; }"
RUN="""async ([src,names])=>{ S.characters=names.map((n,i)=>({id:'c'+i,name:n,level:280,job:'',world:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}));
  const im=new Image(); im.src=src; await im.decode(); ARX.ocr=null; ARX.ocrP=Promise.resolve(); ARX.prof=null; await arProfDetect(im); ARX.profT=Date.now(); ARX.profBusy=false;
  ARX.det=ARX.det||{}; ARX.det.cid=null; ARX.nprev=null; ARX.nameOk=false; ARX.nameSrc=null; ARX.nameBusy=false; const t0=performance.now(); arNameWatch(im); const ms=performance.now()-t0;
  const c=S.characters.find(c=>c.id===ARX.det.cid); return {pick:c?c.name:null,src:ARX.nameSrc,ms,sc:ARX.nSylSc}; }"""
OCR="""(name)=>{ ARX.nOcrHp2=ARX.lastHp2; const c=S.characters.find(c=>c.name===name); arSylLearn(c.id); return Object.keys(JSON.parse(localStorage.getItem('arSyl')||'{}')); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.on('request',lambda r:reqs.append(r.url))
    pg.evaluate(PREP)
    r=pg.evaluate(RUN,[u('A_041_roba'),NAMES]); check('학습 전: 로바 화면 → 음절로 안 정함(바 모름)',r['src']!='음절' and r['pick'] is None,r)
    r=pg.evaluate(RUN,[u('A_041'),NAMES]); check('학습 전: 겟로스트로바 화면 → 음절로 안 정함(겟·바 모름)',r['src']!='음절',r)
    k=pg.evaluate(OCR,G); check('OCR 확정 1번 → 아직 저장 안 함(2번 일치 필요)',k==[],k)
    r=pg.evaluate(RUN,[u('B22'),NAMES]); k=pg.evaluate(OCR,G); check('흐린 바 화면(B22) OCR 확정 → 깨끗하지 않아 저장 안 함',k==[],k)
    r=pg.evaluate(RUN,[u('A_041'),NAMES]); pg.evaluate(OCR,G); r=pg.evaluate(RUN,[u('A_041'),NAMES]); k=pg.evaluate(OCR,G); check('같은 화면 OCR 확정 2번 → 겟·바 저장(localStorage)',sorted(k)==['겟','바'],k)
    r=pg.evaluate(RUN,[u('A_041_roba'),NAMES]); check('학습 뒤: 다른 이름 로바 → 음절로 0.1초 안 확정',r['pick']=='로바' and r['src']=='음절' and r['ms']<100,r)
    r=pg.evaluate(RUN,[u('A_041'),NAMES]); check('학습 뒤: 겟로스트로바 → 음절',r['pick']==G and r['src']=='음절',r)
    r=pg.evaluate(RUN,[u('A_041_roba'),['바로','로버','겟로',G]]); check('학습 뒤: 목록에 로바 없으면 확정 안 함(오인식 0)',r['pick'] is None,r)
    pre=list(reqs); pg.reload(); pg.wait_for_timeout(1500); reqs.clear(); pg.evaluate("()=>{ delete AR_SYL['겟']; delete AR_SYL['바']; ARX.sylT=null; }")
    r=pg.evaluate(RUN,[u('A_041_roba'),NAMES]); check('새로고침 뒤에도 유지(localStorage) → 로바 음절',r['pick']=='로바' and r['src']=='음절',r)
    ext=[x for x in pre+reqs if not x.startswith(f'http://127.0.0.1:{PORT}') and not x.startswith('data:')]
    check('학습·대조 중 서버 호출 없음(페이지 첫 로딩 제외)',not ext,ext[:3])
    b.close()
finally:
  srv.kill()
check('페이지 오류 없음',not errs,errs[:3])
print('\nRESULT', 'FAIL' if fails else 'PASS', fails); sys.exit(1 if fails else 0)
