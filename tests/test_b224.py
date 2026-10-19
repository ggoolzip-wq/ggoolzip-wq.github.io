# b224: /api/live = 페이지 열 때 1번만 (30초 재조회 없음) · 라이브 탭은 받아 둔 값 · 공지 결과·배지 그대로 · Worker 표 확인 isolate 당 1번 · 15초 캐시
import os, sys, json, subprocess, time, urllib.request, shutil, tempfile
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8969'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
NOW=int(time.time()*1000)
LIVE={"at":NOW,"yt":{"live":True,"vid":"IkEDT0Wy8zY","url":"https://www.youtube.com/watch?v=IkEDT0Wy8zY","title":"테스트 라이브","checked_at":NOW},"nx":{"live":False},"list":[],
      "feed":{"items":{"saryo":[{"id":"notice:999","title":"[완료] 테스트 사료 공지","url":"https://maplestory.nexon.com/News/Notice/999","date":"2026-10-19","src":"notice"}],"patch":[]},"sunday":None,"chk":{},"prices":None}}
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://127.0.0.1:{PORT}/index.html'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for kind in ('demo','real'):
        ctx=b.new_context(viewport={'width':1400,'height':800},locale='ko-KR'); n=[0]
        def live(r):
            n[0]+=1; r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps(LIVE))
        ctx.route('**/api/live*',live); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.clock.install()
        pg.goto(URL); pg.evaluate("localStorage.clear()")
        if kind=='real':
            E_=lambda d:{'enabled':True,'diff':d,'party':1}
            ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[{'id':'c1','name':'테스트','level':280,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':E_('hard')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}],'settings':{'accounts':[]}}
            pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))",ST)
        n[0]=0; pg.reload(); pg.clock.run_for(2000); pg.wait_for_timeout(300)
        check(f'{kind}: 페이지 열 때 /api/live 1번', n[0]==1, n[0])
        check(f'{kind}: 공지 결과·LIVE 배지 반영', pg.evaluate("!document.getElementById('liveBadge').hidden && !!(feed.srv&&feed.srv.items.saryo.length)"))
        pg.clock.run_for(5*60*1000); pg.wait_for_timeout(300)
        pg.evaluate("Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'});document.dispatchEvent(new Event('visibilitychange'));Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'visible'});document.dispatchEvent(new Event('visibilitychange'))")
        pg.clock.run_for(60*1000); pg.wait_for_timeout(300)
        check(f'{kind}: 5분 지나고 탭 숨김/보임 해도 재조회 없음', n[0]==1, n[0])
        pg.click('[data-tab=live]'); pg.wait_for_timeout(300)
        check(f'{kind}: 라이브 탭 = 받아 둔 값(요청 없음)', n[0]==1 and pg.evaluate("!!document.querySelector('#view .lvplay[data-embed*=IkEDT0Wy8zY]')"), n[0])
        pg.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))"); pg.wait_for_timeout(300)
        check(f'{kind}: bfcache 복원 = 1번 더', n[0]==2, n[0])
        pg.reload(); pg.clock.run_for(1500); pg.wait_for_timeout(300)
        check(f'{kind}: 새로고침 = 1번 더', n[0]==3, n[0])
        check(f'{kind}: 폴링 코드 없음', pg.evaluate("typeof livePoll==='undefined'"))
        ctx.close()
    b.close()
finally: srv.terminate()
# ---- Worker: 표 확인 isolate 당 1번 · Cache-Control 15초 ----
tmp=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'server','worker.js'),os.path.join(tmp,'w.mjs'))
js=r"""
const W=(await import(process.argv[2])).default; const Q=[];
const res=sql=>({results:[]});
const DB={prepare(sql){const st={bind(){return st;},async run(){Q.push(sql);return {};},async all(){Q.push(sql);return res(sql);},async first(){Q.push(sql);return null;}};return st;},async batch(L){}};
const env={DB,ALLOWED_ORIGINS:'https://bossmaple.pages.dev'};
const o={hdr:[]};
for(let i=0;i<3;i++){ const r=await W.fetch(new Request('https://x.workers.dev/api/live',{headers:{Origin:'https://bossmaple.pages.dev'}}),env); o.hdr.push([r.status,r.headers.get('Cache-Control'),r.headers.get('Vary')]); }
o.create=Q.filter(q=>/CREATE TABLE/.test(q)).length; o.selects=Q.filter(q=>/^SELECT/.test(q)).length;
console.log(JSON.stringify(o));
"""
open(os.path.join(tmp,'t.mjs'),'w').write(js)
O=json.loads(subprocess.check_output(['node',os.path.join(tmp,'t.mjs'),os.path.join(tmp,'w.mjs')]).decode().strip().splitlines()[-1])
check('Worker: /api/live 3번에 표 확인(CREATE) 3개만 = isolate 당 1번 (예전 9개)', O['create']==3, O)
check('Worker: Cache-Control public, max-age=15 + Vary Origin', all(h[0]==200 and 'max-age=15' in (h[1] or '') and 'Origin' in (h[2] or '') for h in O['hdr']), O['hdr'])
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
