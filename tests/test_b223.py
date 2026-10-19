# b223: 새로고침하면 페이지 맨 위에서 시작 (바로, 애니메이션 없음) · 실제 + 예시 · 사용자가 움직인 뒤엔 안 건드림
import os, sys, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8972'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://127.0.0.1:{PORT}/index.html'
# 맨 처음 그려질 때부터 scrollY 기록 (애니메이션이면 0 이 아닌 중간값이 남음)
REC="""(()=>{window.__ys=[];const t0=performance.now();const f=()=>{window.__ys.push(Math.round(scrollY));if(performance.now()-t0<2500)requestAnimationFrame(f)};requestAnimationFrame(f);
  document.addEventListener('DOMContentLoaded',()=>{document.documentElement.style.scrollBehavior='smooth';});})()"""
def down(pg):
    pg.mouse.wheel(0,4000); pg.wait_for_timeout(400); return pg.evaluate("scrollY")
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def mk(vp):
        ctx=b.new_context(viewport=vp,locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        ctx.add_init_script(REC)
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); return ctx,pg
    for vp in ({'width':1400,'height':600},{'width':390,'height':700}):
        tag=f"{vp['width']}"
        ctx,pg=mk(vp)
        pg.goto(URL); pg.wait_for_timeout(300)
        E_=lambda d:{'enabled':True,'diff':d,'party':1}
        CH=[{'id':f'c{i}','name':f'테스트{i}','level':280,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':E_('hard'),'will':E_('hard'),'dusk':E_('chaos')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i in range(1,9)]
        ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':CH,'settings':{'accounts':[]}}
        pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",[ST]); pg.reload(); pg.wait_for_timeout(1200)
        check(f'실제 {tag}: 스크롤 복원 manual', pg.evaluate("history.scrollRestoration")=='manual')
        y0=down(pg); pg.reload(); pg.wait_for_timeout(2700)
        ys=pg.evaluate("__ys")
        check(f'실제 {tag}: 아래로 내린 뒤 F5 → 처음부터 끝까지 맨 위(중간값 없음 = 애니메이션 없음)', y0>200 and ys and max(ys)==0 and pg.evaluate("scrollY")==0, (y0,sorted(set(ys))[:10]))
        # 사용자가 내린 뒤 다시 그리기 = 그대로
        y1=down(pg); pg.evaluate("render()"); pg.wait_for_timeout(300)
        check(f'실제 {tag}: 사용자가 내린 뒤 render = 위치 그대로', y1>200 and abs(pg.evaluate("scrollY")-y1)<2, (y1,pg.evaluate("scrollY")))
        # 탭 바꾸면 맨 위 (b213 그대로)
        if vp['width']>1000:
            down(pg); pg.click('#tabs [data-tab="total"]'); pg.wait_for_timeout(200)
            check(f'실제 {tag}: 탭 바꾸면 맨 위 그대로', pg.evaluate("scrollY")==0)
        ctx.close()
        ctx,pg=mk(vp)
        pg.goto(URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
        check(f'예시 {tag}: 켜짐', pg.evaluate("!!document.querySelector('.demotop,.dmbanner')"))
        y0=down(pg); pg.reload(); pg.wait_for_timeout(2700); ys=pg.evaluate("__ys")
        check(f'예시 {tag}: F5 → 맨 위, 애니메이션 없음', y0>200 and ys and max(ys)==0 and pg.evaluate("scrollY")==0, (y0,sorted(set(ys))[:10]))
        ctx.close()
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
