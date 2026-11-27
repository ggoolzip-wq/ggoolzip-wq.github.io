# test_b437 (t638u '가끔 메소 대신 오른쪽 메이플포인트를 읽음'): 인벤 메소 칸 오른쪽 메이플포인트 칸도 '동전+흰 칸' 모양(점수 .84~.86 > 기준 .8).
# 실제 장면(원모님 1920 실화면·h4 1920·v09/x06/y17 1366 영상 프레임)에서: 정상 → 동전이 설명창에 가려짐 → 다시 정상 순서로 라이브 인식기(arMesoNow) 실행.
# 수정 전: 가려진 순간 포인트 칸을 메소 칸으로 잡고, 가림이 풀려도 그 자리(포인트)를 계속 읽어 포인트 값을 메소로 저장.
# 수정 후: 동전이 금색인 칸만 메소 칸 — 포인트 값 저장 0, 정답 메소 저장, 잡은 칸 = 메소 칸. LIVE_INDEX=다른 index.html 로 수정 전 재현.
import os, sys, tempfile, shutil, subprocess, base64, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures')
fails=[]; errs=[]; OUT=os.environ.get('B437_OUT')
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
shutil.copy(os.environ.get('LIVE_INDEX') or os.path.join(ROOT,'index.html'),os.path.join(site,'index.html')); shutil.copy(os.path.join(ROOT,'prices.json'),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:280,job:'',world:'',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}); S.characters=[mk('c1','테스트')]; S.meso={}; save(); }"""
RUN="""async srcs=>{ const ims=[]; for(const s of srcs){ const im=new Image(); im.src=s; await im.decode(); ims.push(im); }
 ARX.bbox=arBBox(ims[0]); ARX.bbKey=''; ARX.geo=null; ARX.prof=null; await arProfDetect(ims[0]); ARX.mesoLoc=null; ARX.mesoLocT=0; ARX.mesoAllKey=null; ARX.mesoS=null; ARX.mesoSus=null; ARX.mesoLast=null; ARX.mesoSaveT=0; ARX.mesoPend=null; ARX.cfg.mesoFindMs=1; ARX.cfg.mesoSaveMs=1; /* 시험: 찾기·저장 간격 없앰 */ await arMesoTpl();
 ARX.det.cid='c1'; ARX.nameSrc='직접'; ARX.nOkCid='c1'; ARX.nameOk=true; ARX.cidT=Date.now();
 const saved=[], sv=window.saveMeso; window.saveMeso=(c,i,s)=>{saved.push(i); return true;}; const steps=[];
 for(const im of ims){ for(let i=0;i<2;i++){ await new Promise(r=>setTimeout(r,5)); const o=await arMesoNow(im); const L=ARX.mesoLoc, sw=im.width, sh=im.height;
   const sp=L&&L.inv?arMesoSpan(im,'inv'):null; steps.push({why:o&&(o.why||'ok'), v:o&&o.inv, span:sp&&L.inv?{x:Math.round(sp.x*sw),w:Math.round(sp.w*sw)}:null, loc:L&&L.inv?{x:Math.round(L.inv.x*sw),y:Math.round(L.inv.y*sh),w:Math.round(L.inv.w*sw),h:Math.round(L.inv.h*sh),sc:L.inv.sc}:null, rej:(L&&L.rej||[]).map(r=>({x:Math.round(r.x*sw),y:Math.round(r.y*sh),w:Math.round(r.w*sw),h:Math.round(r.h*sh),sc:r.sc}))}); } }
 window.saveMeso=sv; return {build:document.documentElement.dataset.build, prof:ARX.prof&&ARX.prof.id, saved, steps}; }"""
# (이름, 정상 프레임, 가린 프레임, 메소 정답, 포인트 값, 메소 칸 왼쪽 위 x 대략)
CASES=[('원모님 1920 실화면','b348/live_inv.jpg','b437/live_inv_occ.jpg',337174797,888,27),
       ('h4 1920 영상','b437/h4.jpg','b437/h4_occ.jpg',2047779423,7,603),
       ('v09 1366 영상','b437/v09.jpg','b437/v09_occ.jpg',52021298608,15643,51),
       ('x06 1366 영상','b437/x06.jpg','b437/x06_occ.jpg',58164433608,15643,475),
       ('y17 1366 영상','b437/y17.jpg','b437/y17_occ.jpg',65963924492,15643,475)]
res={}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    pg.evaluate("()=>{ arOcrLoad(); }"); pg.wait_for_function("()=>!!window.AR.ocr",timeout=60000)
    for lab,fn,fo,want,pt,mx in CASES:
      r=pg.evaluate(RUN,[u(fn),u(fo),u(fn),u(fn)]); res[lab]=r
      print('  ',lab,r['build'],'저장',r['saved'],'단계',[(s['why'],s['v'],s['loc'] and s['loc']['x']) for s in r['steps']])
      check(f'{lab}: 포인트 값({pt})을 메소로 저장 0',pt not in r['saved'],r['saved'])
      check(f'{lab}: 포인트 값을 메소로 읽음 0',all(s['v']!=pt for s in r['steps']),[s['v'] for s in r['steps']])
      check(f'{lab}: 틀린 메소 저장 0',all(v==want for v in r['saved']),r['saved'])
      check(f'{lab}: 정답 메소 {want} 저장',want in r['saved'],r['saved'])
      check(f'{lab}: 잡은 칸은 언제나 메소 칸(포인트 칸 아님)',all(not s['loc'] or abs(s['loc']['x']-mx)<12 for s in r['steps']),[s['loc'] for s in r['steps']])
    b.close()
  check('페이지 오류 없음',not errs,errs)
finally:
  srv.terminate(); shutil.rmtree(site,ignore_errors=True)
  if OUT: json.dump(res,open(OUT,'w'),ensure_ascii=False,indent=1)
print('RESULT',('FAIL '+str(len(fails))) if fails else 'PASS'); sys.exit(1 if fails else 0)
