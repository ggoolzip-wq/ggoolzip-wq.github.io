import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8847=_tutil.free_port()
# b70: 소식 카드 — 올린 지 7일 지난 글(날짜 없으면 처음 수집 시각 seen)은 안 읽었어도 N·탭 숫자 없음 / 날짜 모르면 예전처럼 / 열어 둔 채 7일 지나면 다음 렌더에서 사라짐
import os, sys, json, subprocess, time, urllib.request, datetime
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8847
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
KST=datetime.timezone(datetime.timedelta(hours=9)); now=datetime.datetime.now(KST)
iso=lambda d: (now-d).isoformat(timespec='seconds')
D=datetime.timedelta
FEED={'version':1,'sources':{},'items':{
  'saryo':[{'id':'s1','title':'새 글 1일','url':'https://x/1','date':iso(D(days=1))},
           {'id':'s2','title':'지난 글 8일','url':'https://x/2','date':iso(D(days=8))},
           {'id':'s3','title':'경계 7일-3분','url':'https://x/3','date':iso(D(days=7)-D(minutes=3))},
           {'id':'s4','title':'날짜 없음','url':'https://x/4'},
           {'id':'s5','title':'날짜 없음 수집 10일','url':'https://x/5','seen':iso(D(days=10))},
           {'id':'s6','title':'날짜 없음 수집 2일','url':'https://x/6','seen':iso(D(days=2))}],
  'patch':[{'id':'p1','title':'오래된 패치','url':'https://x/p1','date':iso(D(days=30))}],
  'test':[{'id':'t1','title':'새 테섭','url':'https://x/t1','date':iso(D(hours=3))}],
  'mabbak':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':800}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(FEED)))
    pg.route('https://x/**',lambda r:r.fulfill(status=200,body='ok'))
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector('#feedCard .flist')
    newt=lambda: pg.evaluate("[...document.querySelectorAll('#feedCard .fit')].filter(a=>a.querySelector('.fnew')).map(a=>a.dataset.fid)")
    cnt=lambda k: pg.evaluate(f"(document.querySelector('[data-ftab={k}] .fcnt')||{{}}).textContent||''")
    pg.click('[data-ftab=saryo]'); pg.wait_for_timeout(200)
    pg.evaluate("feed.per=10; renderFeed()")
    check('N only on items within 7 days (1d, 7d-3m, no date, no date+seen 2d); not on 8d or seen 10d', sorted(newt())==['s1','s3','s4','s6'], newt())
    check('tab count excludes old items (사료감지 4, 패치내역 none, 테섭 1)', cnt('saryo')=='4' and cnt('patch')=='' and cnt('test')=='1', (cnt('saryo'),cnt('patch'),cnt('test')))
    pg.click('#feedCard .fit[data-fid=s1]'); pg.wait_for_timeout(300)
    check('within 7 days: still N until seen (click → gone, count 3)', 's1' not in newt() and cnt('saryo')=='3', (newt(),cnt('saryo')))
    # 열어 둔 채 시간이 지남 → 5분마다 하는 feedLoad(렌더) 때 7일 넘은 글 N 사라짐
    pg.evaluate("()=>{ const o=Date.now.bind(Date); Date.now=()=>o()+5*60e3; }"); pg.evaluate("feedLoad()"); pg.wait_for_timeout(500)
    check('item crossing 7 days while page open → N and count drop on next render', 's3' not in newt() and cnt('saryo')=='2', (newt(),cnt('saryo')))
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
