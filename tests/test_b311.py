# test_b311 (t556): 검은 화면·맵 이름 못 읽음 → 현재 보스 상태 유지 / 보스와 무관한 맵 읽음 → '-'
# (base b307): '현재 보스' 상태 — 대기 맵=노란 '대기 중', 전투 맵=빨간 '진행 중', 보상 맵+상자=초록 '보상 인식 중'. 대기/진행 중에도 보스·난이도 표시, 기록은 보상 인식 중만
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
  S.characters=[{id:'c0',name:'트딕이',level:285,job:'나이트로드',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; render(); }"""

ST="""(txt)=>{ const A=window.AR, now=Date.now(); arMapState(txt,now); arPanelPaint(); const e=document.querySelector('#arPanel .ar-cboss .ar-b');
  return {st:arBossState(), txt:e.innerText.trim(), rec:!!A.det.boss}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    pg.click('#tabs [data-tab="auto"]'); pg.wait_for_timeout(400); pg.click('#arGuide [data-arg="x"]'); pg.wait_for_timeout(200)
    pg.evaluate("()=>{ const A=window.AR; A.lock=null; A.box=null; A.det={cid:'c0',boss:'',diff:'',src:''}; A.mapSt=null; A.clr=null; }")
    rows=pg.evaluate("AR_BMAP.filter(r=>r[1]==='slime')"); nm=lambda k: next(r[0] for r in rows if k in r[2])
    shot=lambda n: pg.screenshot(path=os.path.join(OUT,f'b311_{n}.png'),clip=pg.evaluate("(()=>{const r=document.querySelector('#arPanel .ar-cboss').getBoundingClientRect();return {x:r.x-10,y:r.y-10,width:r.width+20,height:r.height+20}})()"))
    a=pg.evaluate(ST,nm('w')+' <노멀>'); check('대기 맵 → 대기 중', a['st']=='wait', a)
    for t in ['','  ','·']:
      c=pg.evaluate(ST,t); check(f'못 읽음({t!r}) → 대기 중 유지', c['st']=='wait' and c['txt']==a['txt'], c)
    a=pg.evaluate(ST,nm('b')+' <카오스>'); check('전투 맵 → 진행 중', a['st']=='run', a)
    c=pg.evaluate(ST,''); check('검은 화면 → 진행 중 유지', c['st']=='run' and c['txt']==a['txt'], c); shot('keep')
    pg.evaluate("()=>{ const A=window.AR, r=arDetectBoss('"+nm('r')+" <노멀>'); A.det.boss=r.boss; A.det.diff=r.diff; A.box={k:'x',t:Date.now()}; A.lock={boss:r.boss,diff:r.diff,text:'',hash:null,t:Date.now()}; }")
    c=pg.evaluate(ST,''); check('보상 인식 중 + 검은 화면 → 유지', c['st']=='rew' and c['rec'], c)
    c=pg.evaluate(ST,'헤네시스'); check('무관한 맵 1번(잡음일 수 있음) → 아직 유지', c['st']=='rew', c); c=pg.evaluate(ST,'헤네시스'); print(c); check("보스와 무관한 맵 읽음 → 현재 보스 '-' · 기록 안 함", c['st']=='' and not c['rec'] and c['txt'].endswith('-') and '슬라임' not in c['txt'], c); shot('off')
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
