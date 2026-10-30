# test_b286: v01 최초의 대적자 노멀 — 보상이 한꺼번에 와서 '백옥의 보스 반지 상자를 획득했습니다' 배너가 1프레임(33ms)만 보임 (13.43초)
#            → 배너 순간 감시(arBannerWatch)가 아이콘으로 잡아 1번만 · 최초의 대적자에 기록. 1프레임 놓친 기존 방식(3fps·연속 2프레임)은 못 잡음.
import os, sys, tempfile, shutil, subprocess, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
shutil.copytree(os.path.join(ROOT,'tests','fixtures','b286'),os.path.join(site,'fx'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  const C=(id,name,lv)=>({id,name,level:lv,job:'',world:'스카니아',ocid:'',accId:'',isMain:id==='c0',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.characters=[C('c0','트딕이',285),C('c1','팬더데이',285)]; S.activeId='c0'; save&&save(); render();
  const A=window.AR; A.logPrev=[]; A.recent={}; A.hits={}; A.counted=[]; A.log=[]; A.bq=[]; A.bprev=null; A.bannerHits=[]; A.det={cid:'c0',boss:'adversary',diff:'normal',src:'t'}; A.detT=Date.now(); A.cidT=Date.now(); A.cfg.on=true; }"""
LOAD="""async f=>{ const im=new Image(); im.src='fx/'+f; await im.decode(); const cv=document.createElement('canvas'); cv.width=im.width; cv.height=im.height; cv.getContext('2d').drawImage(im,0,0); window._cv=cv; }"""
FR=sorted(os.path.basename(x) for x in glob.glob(os.path.join(ROOT,'tests','fixtures','b286','v01_*.jpg')))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("ARX.cfg.boxGate=false")  # t522: 이 테스트는 아이템 인식만 봄 — 보상 상자 게이트는 test_b300
    # 1) 예전 방식: 3fps 로 받은 프레임(0128, 0138)만 → 배너 1프레임은 안 보임 (기록 없음이 맞음 — 놓치던 이유 재현)
    pg.evaluate(SETUP)
    for f in ['v01_0128.jpg','v01_0138.jpg']: pg.evaluate(LOAD,f); pg.evaluate("arFrame(window._cv,false)")
    old=pg.evaluate("window.AR.log.filter(l=>l.includes('자동 기록'))")
    check('예전 방식(3fps·연속 2프레임)은 백옥 1프레임 배너를 못 봄', not old, old)
    # 2) 배너 순간 감시: 실제 원본 프레임 순서대로
    pg.evaluate(SETUP)
    for f in FR: pg.evaluate(LOAD,f); pg.evaluate("arBannerWatch(window._cv)")
    pg.evaluate("window.AR.bpP")
    fin=pg.evaluate("(async()=>{ await window.AR.bpP; const A=window.AR; return {hits:A.bannerHits, log:A.log, drop:+(dropMap(S.characters[0],'weekly')['adversary|r_white']||dropMap(S.characters[0],'monthly')['adversary|r_white']||0)}; })()")
    print('FIN',json.dumps(fin,ensure_ascii=False)[:600])
    rec=[l for l in fin['log'] if '자동 기록' in l]
    check('v01: 1프레임 배너에서 백옥 아이콘 잡음', any(h[0]=='r_white' for h in fin['hits']), fin['hits'])
    check('v01: 백옥의 보스 반지 상자 · 최초의 대적자 정확히 1번 기록', len(rec)==1 and '백옥의 보스 반지 상자 · 최초의 대적자' in rec[0], rec)
    check('v01: 백옥 말고 다른 아이템 잘못 기록 없음', all('백옥' in l for l in rec), rec)
    # 3) 같은 프레임 다시 와도(로그·배너 중복) 1번만
    for f in FR: pg.evaluate(LOAD,f); pg.evaluate("arBannerWatch(window._cv)")
    rec2=pg.evaluate("(async()=>{ await window.AR.bpP; return window.AR.log.filter(l=>l.includes('자동 기록')); })()")
    check('v01: 같은 배너 다시 봐도 중복 기록 없음', len(rec2)==1, rec2)
    # 4) v11 카링 이지: 배너 1초쯤 보이지만 점수 .75 (예전 기준 .84 미만이라 놓침) → 배너 순간 감시로 카링에 기록
    pg.evaluate(SETUP); pg.evaluate("()=>{ window.AR.det={cid:'c0',boss:'kaling',diff:'easy',src:'t'}; }")
    for f in ['v11_1500.jpg','v11_1560.jpg']: pg.evaluate(LOAD,f); pg.evaluate("arBannerWatch(window._cv)")
    r11=pg.evaluate("(async()=>{ await window.AR.bpP; return window.AR.log.filter(l=>l.includes('자동 기록')); })()")
    check('v11: 백옥의 보스 반지 상자 · 카링 1번 기록', len(r11)==1 and '백옥의 보스 반지 상자 · 카링' in r11[0], r11)
    # 5) 듄켈 맵
    q=pg.evaluate("()=>{ const r=arDetectBoss('끝에 가까운 곳 <하드>'); return r&&[r.boss,r.diff]; }")
    check("'끝에 가까운 곳' → 듄켈 하드 (검은 마법사 아님)", q==['dunkel','hard'], q)
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else 'FAILED: '+', '.join(fails)); sys.exit(1 if fails else 0)
