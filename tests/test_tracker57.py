# b76: 득템 분석 '아이템 판매 누적 수익' — 제목, 아이콘=가장 많이 판 아이템, 총액 '억 메소', 분배 인원별 줄(1인/N인 분배), 한 줄·가로 스크롤 없음
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8862
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
revs={'a':{'m':500000000,'a':5,'p':1,'i':'belt'},'b':{'m':250000000,'a':5,'p':2,'i':'belt'},'c':{'m':900000000,'a':9,'p':1,'i':'eye'},'d':{'m':1200000000,'a':36,'p':3,'i':'eye'},'e':{'m':400000000,'a':4,'p':1,'i':'belt'}}
H=[{'week':'2026-09-28','total':0,'perChar':[{'id':'c1','name':'본캐용사','total':0,'revs':revs}]}]
ST={'version':5,'theme':'dark','activeId':'c1','history':H,'monthHistory':[],'worldOrder':[],'characters':[ch('c1','본캐용사')],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1280,390):
        pg=b.new_page(viewport={'width':w,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
        pg.evaluate("tab='loot'; render()"); pg.wait_for_timeout(300)
        if w==1280:
            check('title', pg.inner_text('#salesCard h2').strip()=='아이템 판매 누적 수익')
            check('b229: title icon = highest total sale amount (eye 21억 > belt 11.5억)', pg.evaluate("document.querySelector('#salesCard h2 .hbi').innerHTML===lootIco('eye')"))
            check("total has ' 메소'", pg.inner_text('#salesCard .v.acc')=='32.50억 메소', pg.inner_text('#salesCard .v.acc'))
            rows=pg.evaluate("[...document.querySelectorAll('#salesCard .sl')].map(r=>[r.querySelector('.ln').textContent,r.querySelector('.slp').textContent,r.querySelector('.lx').textContent,r.querySelector('.slm').textContent])")
            check('rows split by party size', rows==[['마력이 깃든 안대','3인 분배','x1','12.00억 메소'],['마력이 깃든 안대','1인','x1','9.00억 메소'],['몽환의 벨트','1인','x2','9.00억 메소'],['몽환의 벨트','2인 분배','x1','2.50억 메소']], rows)
        one=pg.evaluate("[...document.querySelectorAll('#salesCard .sl')].every(r=>r.getBoundingClientRect().height<40)")
        hs=pg.evaluate("(()=>{const c=document.querySelector('#salesCard'); return c.scrollWidth>c.clientWidth||document.documentElement.scrollWidth>innerWidth})()")
        check(f'{w}px: one line per row, no horizontal scroll', one and not hs, (one,hs))
        pg.close()
    pg=b.new_page(); pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",{**ST,'history':[]}); pg.reload(); pg.wait_for_timeout(600); pg.evaluate("tab='loot'; render()")  # b87: 캐릭터가 없으면 빈 화면이므로 캐릭터 1명·판매 기록 없음
    check('empty: fallback meso icon + title', '아이템 판매 누적 수익' in pg.inner_text('#salesCard h2'))
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
