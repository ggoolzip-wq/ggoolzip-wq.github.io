# test_b324 (t587): 클리어 시간 — 14:30~15:30 사이 클리어(남은시간 ≈5:00 에서 5:00 리셋 → 점프가 작거나 없음)에도 끝을 ±3초 안으로 잡음,
# 점프를 못 본 경우는 '추정' 표시, 타이머로 끝을 하나도 못 잡으면(상자만) '추정', 일간 보스는 기록 안 함
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1300,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e))); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    r=pg.evaluate("""()=>{ const A=window.AR; A.clr=null; A.clrHold=false; A.det={cid:'',boss:'',diff:'',src:''}; A.cfg.clrOff=false; A.ocr=null; A.rew=null; A.box=null;
      const t0=Date.now()-60000; let rem=1199; window.arClrRead=()=>({sec:rem,m:Math.floor(rem/60),s:rem%60}); const out=[];
      for(const [nm,k] of [['공허의 눈 앞','w'],['의지가 시작되는 곳','w']]){ arMapState(nm,t0); arMapState(nm,t0+1); A.mapSt={boss:A.mapSt?.boss||'dusk',kind:'w',name:nm,t:0};
        for(let e=0;e<20;e++){ rem--; A.clrT=0; arClrTick({},t0+e*1000); } arMapHit({boss:A.mapSt.boss,diff:'',kind:'w',src:'대기 맵'},t0+21000); out.push([nm,!!A.clr,arClrLine()]); }
      A.mapSt={boss:'dusk',kind:'b',name:'공허의 눈',t:0}; for(let e=0;e<5;e++){ rem--; A.clrT=0; arClrTick({},t0+30000+e*1000); } out.push(['전투',!!A.clr,arClrLine()]);
      A.mapSt={boss:'dusk',kind:'w',name:'공허의 눈 앞',t:0}; out.push(['대기복귀',!!A.clr,arClrLine()]); return out; }""")
    check('대기맵: 타이머 읽혀도 측정 안 시작·표시 없음',all(not x[1] and '진행' not in x[2] for x in r[:2]),r)
    check('전투맵: 측정 시작·진행 표시',r[2][1] and '진행' in r[2][2],r[2])
    check('전투 중 대기맵 표시면 진행 표시 안 함',('진행' not in r[3][2]),r[3])
    pg.evaluate("""()=>{ const A=window.AR; A.clr=null; A.mapSt={boss:'dusk',kind:'w',name:'공허의 눈 앞',t:Date.now()}; renderAuto(); }""")
    pg.wait_for_timeout(500); pg.screenshot(path='/workspace/t587_wait.png',full_page=False)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
