# test_b309 (t551/t552): 목록에 없는 닉네임 → 캐릭터 '-' · 기록 대상 없음 / 검은 화면·못 읽음 → 직전 유지 / 상태바 안내 문구 제거
# (was b307): '현재 보스' 상태 — 대기 맵=노란 '대기 중', 전투 맵=빨간 '진행 중', 보상 맵+상자=초록 '보상 인식 중'. 대기/진행 중에도 보스·난이도 표시, 기록은 보상 인식 중만
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  S.characters=[{id:'c1',name:'린벨자',level:280,job:'비숍',world:'스카니아',ocid:'',accId:'',isMain:false,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}},{id:'c0',name:'트딕이',level:285,job:'나이트로드',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; render(); }"""

ST="""(txt)=>{ const A=window.AR; if(!A.stream){ const cv=document.createElement('canvas'); cv.width=cv.height=8; A.stream=cv.captureStream(1); } A.video=A.video||document.createElement('video'); A.nChgT=Date.now()+1; if(txt!==null) arNameRes(txt);
  arPanelPaint(); const e=document.querySelector('#arPanel .ar-cchar .ar-b'); const t=arTarget();
  return {cid:A.det.cid, tgt:t?t.c.name:'', html:e.innerText, cand:(arCandidates()||[]).length}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    pg.click('#tabs [data-tab="auto"]'); pg.wait_for_timeout(400); pg.click('#arGuide [data-arg="x"]'); pg.wait_for_timeout(200)
    shot=lambda n: pg.screenshot(path=os.path.join(OUT,f'b309_{n}.png'),clip=pg.evaluate("(()=>{const r=document.querySelector('#arPanel .ar-cchar').getBoundingClientRect();return {x:r.x-10,y:r.y-10,width:r.width+20,height:r.height+20}})()"))
    a=pg.evaluate(ST,'Lv.280 린벨자'); print('known',a); check('목록 캐릭터 → 대상', a['cid']=='c1' and a['tgt']=='린벨자' and '린벨자' in a['html'], a); shot('known')
    a=pg.evaluate(ST,''); print('black',a); check('검은 화면(빈 OCR) → 직전 유지', a['cid']=='c1' and a['tgt']=='린벨자', a)
    a=pg.evaluate(ST,'~ .. ,'); print('noise',a); check('잡음 OCR → 직전 유지', a['cid']=='c1', a)
    a=pg.evaluate(ST,'Lv.275 모르는캐릭'); print('unk',a)
    check("목록에 없는 닉네임 → '-' · 기록 대상 없음", a['cid']=='' and a['tgt']=='' and a['cand']==0 and a['html'].strip().startswith('-'), a)
    check('상태바 안내 문구 없음', '상태바' not in a['html'] and '기록 대상' not in a['html'], a)
    shot('unknown')
    r=pg.evaluate("""()=>{ const A=window.AR; A.det.boss='slime'; arRecord('x',1); const n=JSON.stringify(S.characters.map(c=>c.drops)); A.clr={boss:'slime',diff:'',reads:[],mapT:Date.now()-60000,practice:false}; const c=arClrFinish('slime','',Date.now()); return {n, clr:c, clears:JSON.stringify(S.clears||{})}; }""")
    print('rec',r); check("'-' 상태에서 아이템·클리어 시간 저장 안 함", r['clr'] is None and r['n']=='[{},{}]' and r['clears']=='{}', r)
    a=pg.evaluate(ST,'Lv.285 트딕이'); check('목록 캐릭터로 다시 → 대상 복구', a['cid']=='c0', a)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
