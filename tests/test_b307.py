# test_b307 (t541): '현재 보스' 상태 — 대기 맵=노란 '대기 중', 전투 맵=빨간 '진행 중', 보상 맵+상자=초록 '보상 인식 중'. 대기/진행 중에도 보스·난이도 표시, 기록은 보상 인식 중만
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
# 맵 이름 → 상태/표시 (상자: 'rew'는 det.boss + 상자 OK 를 흉내)
ST="""([txt,rew])=>{ const A=window.AR, now=Date.now(); A.lock=null; A.box=null; A.det={cid:'c0',boss:'',diff:'',src:''}; A.mapSt=null; A.clr=null;
  arMapState(txt,now); const r=arDetectBoss(txt); if(rew&&r){ A.det.boss=r.boss; A.det.diff=r.diff; A.det.src=r.src; A.box={k:'x',t:now}; A.lock={boss:r.boss,diff:r.diff,text:'',hash:null,t:now}; }
  arPanelPaint(); const e=document.querySelector('#arPanel .ar-cboss .ar-b'), s=e.querySelector('.ar-bst'), d=s&&s.querySelector('.ar-dot');
  return {st:arBossState(), txt:s?s.textContent:'', col:s?getComputedStyle(s).color:'', glow:d?getComputedStyle(d).boxShadow:'', boss:(e.querySelector('.ar-bn')||{}).textContent||'', html:e.innerHTML, rec:!!A.det.boss, clr:!!A.clr}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    pg.click('#tabs [data-tab="auto"]'); pg.wait_for_timeout(400); pg.click('#arGuide [data-arg="x"]'); pg.wait_for_timeout(200)
    rows=pg.evaluate("AR_BMAP.filter(r=>r[1]==='slime')")
    def nm(k): return next(r[0] for r in rows if k in r[2])
    W,Bt,R=nm('w'),nm('b'),nm('r')
    print('MAPS',W,Bt,R)
    for th in ['dark','light']:
      pg.evaluate(f"document.documentElement.dataset.theme='{th}'")
      a=pg.evaluate(ST,[W+' <노멀>',False]); print(th,'W',a)
      check(f'{th}: 대기 맵 → 노란 대기 중 · 보스 이름 표시 · 기록 안 함', a['st']=='wait' and '대기 중' in a['txt'] and a['boss'] and not a['rec'] and 'rgba(0, 0, 0, 0)' not in a['glow'] and a['glow']!='none', a)
      pg.screenshot(path=os.path.join(OUT,f'b307_wait_{th}.png'),clip=pg.evaluate("(()=>{const r=document.querySelector('#arPanel .ar-cboss').getBoundingClientRect();return {x:r.x-10,y:r.y-10,width:r.width+20,height:r.height+20}})()"))
      a=pg.evaluate(ST,[Bt+' <카오스>',False]); print(th,'B',a)
      check(f'{th}: 전투 맵 → 빨간 진행 중 · 보스+난이도 표시 · 기록 안 함 · 클리어 시간 시작', a['st']=='run' and '진행 중' in a['txt'] and a['boss'] and not a['rec'] and a['clr'], a)
      pg.screenshot(path=os.path.join(OUT,f'b307_run_{th}.png'),clip=pg.evaluate("(()=>{const r=document.querySelector('#arPanel .ar-cboss').getBoundingClientRect();return {x:r.x-10,y:r.y-10,width:r.width+20,height:r.height+20}})()"))
      a=pg.evaluate(ST,[R+' <노멀>',True]); print(th,'R',a)
      check(f'{th}: 보상 맵+상자 → 초록 보상 인식 중 · 기록 대상', a['st']=='rew' and '보상 인식 중' in a['txt'] and a['boss'] and a['rec'], a)
      pg.screenshot(path=os.path.join(OUT,f'b307_rew_{th}.png'),clip=pg.evaluate("(()=>{const r=document.querySelector('#arPanel .ar-cboss').getBoundingClientRect();return {x:r.x-10,y:r.y-10,width:r.width+20,height:r.height+20}})()"))
    cols=pg.evaluate("""()=>{ const o={}; for(const th of ['dark','light']){ document.documentElement.dataset.theme=th; o[th]={}; for(const k of ['wait','run','rew']){ const e=document.createElement('div'); e.className='ar-bst '+k; document.querySelector('#arPanel').appendChild(e); o[th][k]=getComputedStyle(e).color; e.remove(); } } return o; }""")
    print('COLS',cols)
    check('세 상태 색이 서로 다름 (양 테마)', all(len(set(cols[t].values()))==3 for t in cols), cols)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
