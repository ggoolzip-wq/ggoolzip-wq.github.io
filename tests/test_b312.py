# test_b312 (t558): 모든 보스 '대기맵 이름' 과 '대기맵 이름 <난이도>'(도핑 준비 맵) → 대기 중(노랑), 태그로 난이도 갱신, 보상(기록) 아님
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
AMB={'검은 마법사','선택받은 세렌'}  # 대기맵=보상맵 같은 이름·지역 → 보상 후보지만 상자 전엔 대기 중
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
BM=json.load(open(os.path.join(ROOT,'tests','fixtures','boss_maps.json')))
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
F="""([txt])=>{ const A=window.AR, now=Date.now(); A.lock=null; A.box=null; A.det={cid:'',boss:'',diff:'',src:''}; A.mapSt=null; A.clr=null; A.mOffN=0;
  const T=arMapState(txt,now); const r=arDetectBoss(txt); return {st:arBossState(), boss:A.mapSt&&A.mapSt.boss, diff:A.mapSt&&A.mapSt.diff, rew:!!r}; }"""
D={'이지':'easy','노멀':'normal','하드':'hard','카오스':'chaos','익스트림':'extreme'}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    dk=pg.evaluate("typeof D==='object'?D:{}")
    for bo in BM:
      if not bo['prep']: continue
      a=pg.evaluate(F,[bo['waiting_base']]); check(f"{bo['boss']} 대기맵 '{bo['waiting_base']}' → 대기 중", a['st']=='wait' and (not a['rew'] or bo['boss'] in AMB), a)
      for k,v in bo['prep'].items():
        a=pg.evaluate(F,[v[0]]); want=[x for x,y in dk.items() if y==k or y.replace('말','멀')==k]
        check(f"{bo['boss']} 준비맵 '{v[0]}' → 대기 중 · 난이도 {k}", a['st']=='wait' and (not a['rew'] or bo['boss'] in AMB) and (a['diff'] in want or a['diff']==k), [a,want])
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
