# test_b351 (t657): 데미안 실화면(밝은 돌 배경)에서 메소 저장 안 되던 문제 + 캐릭터 고정(잠금) — 원본 test_b348 (t655): 실화면(1920x1080 기본 비율, 밝은 돌 배경, 인벤토리 창 왼쪽 위) — ① 메소 칸은 화면 전체에서 찾음(창 옮겨도) ② 닉네임: ㅎ↔ㅇ 묶음, 글자 끝까지 자른 OCR, 직접 알려주기 버튼
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b351'); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
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
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; const mk=(id,n)=>({id,name:n,level:280,job:'',world:'',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}); S.characters=[mk('c0','겟로스트로바'),mk('c1','홀드유웨이컵'),mk('c2','트딕이')]; S.activeId='c0'; save(); S.tab='auto'; renderAuto(); }"""
RUN="""async src=>{ const im=new Image(); im.src=src; await im.decode(); ARX.bbox=arBBox(im); ARX.bbKey=''; ARX.geo=null; ARX.prof=null; await arProfDetect(im); ARX.mesoLoc=null; await arMesoTpl();
 ARX.det.cid='c1'; ARX.nameSrc='직접'; const saved=[]; const sv=window.saveMeso; window.saveMeso=(c,i,s)=>{saved.push([c,i]); return true;}; const r=await arMesoNow(im); window.saveMeso=sv;
 ARX.det.cid=''; ARX.nLock=null; ARX.nHist=[]; for(let i=0;i<30&&!ARX.det.cid;i++){ arNameWatch(im); await new Promise(r=>setTimeout(r,250)); } return {r, saved, cid:ARX.det.cid}; }"""
LOCK="""()=>{ const T=1e6; ARX.det.cid=''; ARX.nLock=null; ARX.nSw=null; ARX.nDrop=null; ARX.blackEnd=0; ARX.blackLen=0;
 const o={}; arCidPut('c1',T,'t'); o.a=ARX.det.cid;
 for(let i=0;i<10;i++) arCidDrop(T+500+i*400,'vote'); o.noBlack=ARX.det.cid;           /* 검은 화면 없이 다른 이름 읽기 10번 → 유지 */
 arCidPut('c2',T+5000,'t'); o.sw1=ARX.det.cid;                                         /* 다른 캐릭터 한 번 → 유지 */
 ARX.blackEnd=T+6000; ARX.blackLen=2000; for(let i=0;i<6;i++) arCidDrop(T+6500+i*800,'vote'); o.drop=ARX.det.cid; /* 검은 화면(2초) 뒤 다른 이름 4번+3초 → 풀림 */
 arCidPut('c1',T+20000,'t'); for(let i=1;i<=4;i++) arCidPut('c2',T+20000+i*800,'t'); o.sw3=ARX.det.cid; return o; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arOcrLoad(); }"); pg.wait_for_function("()=>!!window.AR.ocr",timeout=60000)
    r=pg.evaluate(RUN,u('live_meso_stone.jpg')); print(r)
    check('메소 = 20억 1357만 4797 읽음',r['r'] and r['r'].get('inv')==2013574797,r['r'])
    check('밝은 돌 배경 이름칸이어도 저장됨(예전 why:name)',r['saved']==[['c1',2013574797]],r)
    check('이름 자동 인식 = 홀드유웨이컵(ㅎ→ㄷ 읽기, 5글자 드 허용)',r['cid']=='c1',r['cid'])
    check('arSylM 5글자 초성 하나 틀림 허용',pg.evaluate("()=>arSylM('돌드유웨미컵','홀드유웨이컵')>0"))
    o=pg.evaluate(LOCK); print(o)
    check('잠금: 검은 화면 없이 다른 이름 읽기로는 안 풀림',o['a']=='c1' and o['noBlack']=='c1',o)
    check('잠금: 다른 캐릭터 한 번 읽기로는 안 바뀜',o['sw1']=='c1',o)
    check('잠금: 검은 화면 + 다른 이름 반복 → 풀림',o['drop']=='',o)
    check('잠금: 다른 캐릭터 3번·2초 이상 → 바뀜',o['sw3']=='c2',o)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
