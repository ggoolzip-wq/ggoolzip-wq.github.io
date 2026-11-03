# test_b353 (t657): 데미안 붉은 불꽃 이펙트가 '마력이 깃든 안대'(eye) 공중으로 오탐(.737~.762) → eye 공중 기준 .8 (저장된 설정도 이전)
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
Q="()=>({eye:arAirK('airKeyThr','eye',ARX.cfg.airThr), mc:arAirK('airKeyThr','mc_x',ARX.cfg.airThr), other:arAirK('airKeyThr','r_white',ARX.cfg.airThr), thr:ARX.cfg.airThr})"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    o=pg.evaluate(Q); print(o)
    check('기본: eye 공중 기준 .8 (오탐 최고 .762 위)',o['eye']==.8,o)
    check('다른 아이템 공중 기준 그대로(.73, mc_ .7)',o['other']==.73 and o['mc']==.7,o)
    key=pg.evaluate("AR_KEY")
    pg.evaluate("k=>{ const c=JSON.parse(localStorage.getItem(k)||'{}'); c.airKeyThr={mc_:.7}; delete c.v353; localStorage.setItem(k,JSON.stringify(c)); }",key); pg.reload(); pg.wait_for_timeout(800)
    o=pg.evaluate(Q); print(o)
    check('예전 저장 설정(airKeyThr {mc_:.7})에도 eye .8 적용',o['eye']==.8 and o['mc']==.7,o)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
