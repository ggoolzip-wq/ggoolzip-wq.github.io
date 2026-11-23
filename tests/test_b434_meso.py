# test_b434 (t582u '메소 기록도 못하고있어'): 보유 메소 기록 — ① 메소 칸 배율을 HUD 프로필과 따로 찾음(1920 최적 실화면 인벤 ≈1.406배, 2560 ≈1.875배, 1366 1배)
#  ② 글자 칸 오른쪽 끝을 화면에서 찾아 자름(예전 고정 비율 → y17 '659억 6392만 4492' 를 659억 0만 6392 로 틀리게 저장) ③ 못 읽은 글자(?) 읽기 버림
#  ③-2 글자 진하기 기준 80 먼저(흐린 1366 영상 8→0 깨짐), 같은 값 두 번 규칙 유지
#  ④ 서버 동기화: meso.<키> 는 at 최신 쪽, 서버에 없으면 이 PC 값 유지(서버 통째 덮어쓰기에서 방금 읽은 메소가 사라지던 것)
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:280,job:'',world:'',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}); S.characters=[mk('c1','홀드유웨이컵')]; S.meso={}; save(); }"""
RUN="""async src=>{ const im=new Image(); im.src=src; await im.decode(); ARX.bbox=arBBox(im); ARX.bbKey=''; ARX.geo=null; ARX.prof=null; await arProfDetect(im); ARX.mesoLoc=null; ARX.mesoSus=null; ARX.mesoLast=null; ARX.mesoSaveT=0; ARX.mesoPend=null; await arMesoTpl();
 ARX.det.cid='c1'; ARX.nameSrc='직접'; ARX.nOkCid='c1'; ARX.nameOk=true; ARX.cidT=Date.now(); /* b436: 닉 확정 상태 (arNameTeach 와 같음) */ const saved=[]; const sv=window.saveMeso; window.saveMeso=(c,i,s)=>{saved.push(i); return true;}; const out=[]; for(let i=0;i<4;i++){ out.push(await arMesoNow(im)); } window.saveMeso=sv;
 return {prof:ARX.prof&&ARX.prof.id, m:ARX.mesoLoc&&ARX.mesoLoc.inv&&ARX.mesoLoc.inv.m, saved, why:out.map(o=>o&&(o.why||'ok'))}; }"""
CASES=[('b348/live_inv.jpg','1920 최적 실화면(원모님) — 인벤 ≈1.406배',337174797,1.40625,True),
       ('b348/live_inv_moved.jpg','1920 최적, 인벤 창 옮김',337174797,1.40625,True),
       ('b351/live_meso_stone.jpg','1920 최적, 밝은 돌 배경',2013574797,1.40625,True),
       ('b434/live_inv_2560.jpg','2560 (실화면 4/3 확대) — ≈1.875배',337174797,1.875,True),
       ('b434/y17_inv_1366.jpg','1366 y17 — 넓은 칸(예전 659억 0만 6392 오기록)',65963924492,1,True),
       ('b434/v09_inv_1366.jpg','1366 v09 흐린 영상(글자 기준 80)',52021298608,1,True),
       ('b434/x06_inv_1366.jpg','1366 x06 흐린 영상(예전 50 1억·51 1억 으로 깨짐)',58164433608,1,True)]
SYNC="""()=>{ const o={}; const L={meso:{'a:1':{inv:500,at:2000,by:'c1'},'c:c9':{inv:7,at:100}}}, R={meso:{'a:1':{inv:400,at:1000,by:'c1'},'a:2':{inv:9,at:50}}};
 const w=gdServerWins(L,R); o.newLocal=w.meso['a:1'].inv; o.onlyLocal=w.meso['c:c9']&&w.meso['c:c9'].inv; o.onlyServer=w.meso['a:2']&&w.meso['a:2'].inv;
 const w2=gdServerWins({meso:{'a:1':{inv:500,at:1000}}},{meso:{'a:1':{inv:600,at:3000}}}); o.newServer=w2.meso['a:1'].inv;
 const w3=gdServerWins({meso:{'a:1':{inv:500,at:1000}}},{}); o.noServerMeso=w3.meso&&w3.meso['a:1']&&w3.meso['a:1'].inv;
 const ctx={base:true,prefer:'r',conf:[]}; const m=gdMerge({meso:{'a:1':{inv:1,at:1}}},{meso:{'a:1':{inv:500,at:2000}}},{meso:{'a:1':{inv:400,at:1000}}},ctx); o.merge=m.meso['a:1'].inv; o.conf=ctx.conf.length;
 const w4=gdServerWins({settings:{x:1}},{settings:{x:2}}); o.otherServer=w4.settings.x; return o; }"""
try:
  for rnd in (1,2):
   with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    pg.evaluate("()=>{ arOcrLoad(); }"); pg.wait_for_function("()=>!!window.AR.ocr",timeout=60000)
    for f,lab,want,m,must in CASES:
      r=pg.evaluate(RUN,u(f)); wrong=[v for v in r['saved'] if v!=want]
      check(f'[{rnd}] {lab}: 틀린 저장 0',not wrong,r)
      if must: check(f'[{rnd}] {lab}: 저장 = {want}',want in r['saved'],r); check(f'[{rnd}] {lab}: 메소 칸 배율 ≈{m}',r['m'] and abs(r['m']-m)<.03,r)
    s=pg.evaluate(SYNC)
    check(f'[{rnd}] 동기화: 서버가 이겨도 이 PC 의 더 최근 메소 유지',s['newLocal']==500,s)
    check(f'[{rnd}] 동기화: 이 PC 에만 있는 메소 유지',s['onlyLocal']==7,s)
    check(f'[{rnd}] 동기화: 서버에만 있는 메소 받음',s['onlyServer']==9,s)
    check(f'[{rnd}] 동기화: 서버 메소가 더 최근이면 서버 값',s['newServer']==600,s)
    check(f'[{rnd}] 동기화: 서버에 메소 묶음이 없어도 유지',s['noServerMeso']==500,s)
    check(f'[{rnd}] 동기화: 3-way 병합도 최신 at, 충돌 질문 없음',s['merge']==500 and s['conf']==0,s)
    check(f'[{rnd}] 동기화: 메소 밖 값은 그대로 서버가 이김',s['otherServer']==2,s)
    b.close()
  check('페이지 오류 없음',not errs,errs)
finally:
  srv.terminate(); shutil.rmtree(site,ignore_errors=True)
print('RESULT',('FAIL '+str(len(fails))) if fails else 'PASS'); sys.exit(1 if fails else 0)
