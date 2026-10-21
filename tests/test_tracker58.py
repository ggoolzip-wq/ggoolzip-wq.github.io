import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8863=_tutil.free_port()
# b79: 결정석 가격 카드 '마지막 확인' = KST 'MM.DD HH:MM' (checkedAt ISO), 예전 날짜만 값은 그대로, 한 줄
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8863
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
ST={'version':5,'theme':'dark','activeId':'c1','history':[],'monthHistory':[],'worldOrder':[],'characters':[{'id':'c1','name':'용사','level':280,'job':'히어로','world':'스카니아','image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}],'settings':{'accounts':[]}}
live=json.load(open(os.path.join(ROOT,'prices.json'),encoding='utf-8'))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for ck,want,w in (('2026-10-12T10:00:05Z','10.12 19:00',1280),('2026-10-12T19:00:00+09:00','10.12 19:00',390),('2026-10-11','2026-10-11',1280)):
        pg=b.new_page(viewport={'width':w,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
        pj=dict(live,checkedAt=ck); pj.pop('upcoming',None)  # b171: 테섭 반영 시각(detectedAt)이 더 늦으면 그게 '마지막 확인' → 여기선 checkedAt 형식만 봄
        body=json.dumps(pj); pg.route('**/prices.json*',(lambda bd: lambda r: r.fulfill(status=200,content_type='application/json',body=bd))(body))
        pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1200)
        t=pg.evaluate("(document.querySelector('.pc-foot')||{}).innerText||''")
        line=[l for l in t.split('\n') if '마지막 확인' in l]
        check(f'{ck} → 마지막 확인 {want} ({w}px)', bool(line) and f'마지막 확인 {want})' in line[0] and '가격 변동일 '+live.get('changedAt','') in line[0], t)
        one=pg.evaluate("(()=>{const f=document.querySelector('.pc-foot'); const lh=parseFloat(getComputedStyle(f).lineHeight)||16; return Math.round(f.getBoundingClientRect().height/lh)<=f.innerText.split('\\n').length})()")
        check(f'one line each ({w}px)', one)
        if w==1280 and 'Z' in ck: pg.locator('.pc-foot').screenshot(path='/workspace/maple-boss-tracker/oct12q_b79_test_foot.png')
        pg.close()
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
