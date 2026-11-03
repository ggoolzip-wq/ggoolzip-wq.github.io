# test_b348 (t655): 실화면(1920x1080 기본 비율, 밝은 돌 배경, 인벤토리 창 왼쪽 위) — ① 메소 칸은 화면 전체에서 찾음(창 옮겨도) ② 닉네임: ㅎ↔ㅇ 묶음, 글자 끝까지 자른 OCR, 직접 알려주기 버튼
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b348'); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; const mk=(id,n)=>({id,name:n,level:280,job:'',world:'',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}); S.characters=[mk('c0','겟로스트로바'),mk('c1','홀드유웨이컵')]; S.activeId='c0'; save(); S.tab='auto'; renderAuto(); }"""
MESO="""async src=>{ const im=new Image(); im.src=src; await im.decode(); ARX.bbox=arBBox(im); ARX.bbKey=''; ARX.geo=null; ARX.prof=null; await arProfDetect(im); ARX.mesoLoc=null; await arMesoTpl(); const L=arMesoFind(im); ARX.det.cid='c1'; const r=L.inv?await arMesoRead(im,'inv'):{}; return {prof:ARX.prof.id,inv:L.inv,ms:L.ms,v:r.v}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arOcrLoad(); }"); pg.wait_for_function("()=>!!window.AR.ocr",timeout=60000)
    r=pg.evaluate(MESO,u('live_inv.jpg')); print(r)
    check('실화면 프로필 = 1920 기본 비율',r['prof']=='1920b',r)
    check('인벤 메소 칸 찾음(왼쪽 아래 x≈27,y≈869)',r['inv'] and abs(r['inv']['x']*1920-27)<12 and abs(r['inv']['y']*1080-869)<12,r)
    check('메소 = 3억 3717만 4797',r['v']==337174797,r)
    r=pg.evaluate(MESO,u('live_inv_moved.jpg')); print(r)
    check('인벤 창을 옮겨도 화면 전체에서 찾음 (x≈1467,y≈789)',r['inv'] and abs(r['inv']['x']*1920-1467)<12 and abs(r['inv']['y']*1080-789)<12,r)
    check('옮긴 창 메소도 같음',r['v']==337174797,r)
    check('ㅎ↔ㅇ 묶음: 올드유웨이컵 읽기 = 홀드유웨이컵 꼴',pg.evaluate("()=>arSylM('올드유웨이컵','홀드유웨이컵')===2&&arSylM('몰드유웨미컵','홀드유웨이컵')>0"))
    check('드 이름은 여전히 OCR 투표로 안 정함(오인식 0 규칙 유지)',pg.evaluate("()=>{ ARX.nHist=Array(8).fill('홀드유웨이컵'); return arNameVote2().cid===''; }"))
    # 연결 흉내 + 실화면 → 미인식이면 직접 알려주기 버튼
    pg.evaluate("""async src=>{ const im=new Image(); im.src=src; await im.decode(); const c=document.createElement('canvas'); c.width=1920; c.height=1080; c.getContext('2d').drawImage(im,0,0); ARX.stream=c.captureStream(1); ARX.video=document.createElement('video'); ARX.testSrc=im; ARX.det.cid=''; ARX.unkName=0; arLivePaint(); }""",u('live_inv.jpg')); pg.wait_for_timeout(300)
    check('미인식: 캐릭터 칸에 [이 캐릭터예요] 버튼',pg.locator('#arPanel .ar-cchar .ar-tbtn').count()==1)
    pg.select_option('#arPanel .ar-cchar .ar-tsel','c1'); pg.locator('#arPanel .ar-cchar .ar-tbtn').click(); pg.wait_for_timeout(500)
    st=pg.evaluate("()=>{ arLivePaint(); return {cid:ARX.det.cid,src:ARX.nameSrc,txt:document.querySelector('#arPanel .ar-cchar .ar-b').textContent}; }")
    check('직접 설정 → 홀드유웨이컵, 버튼 사라짐',st['cid']=='c1' and st['src']=='직접' and '홀드유웨이컵' in st['txt'] and pg.locator('#arPanel .ar-cchar .ar-tbtn').count()==0,st)
    pg.locator('#arPanel .ar-cchar').screenshot(path=os.path.join(OUT,'b348_teach.png'))
    pg.evaluate("()=>{ ARX.stream=null; ARX.video=null; }"); b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
