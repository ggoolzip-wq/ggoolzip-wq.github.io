# b139: 그래프 애니메이션은 화면에 들어올 때 시작 (IntersectionObserver), reduced-motion 이면 바로 표시
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8922'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b139')}_{TAG}_{name}.png"))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)

try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for rm in ['no-preference','reduce']:
        ctx=b.new_context(viewport={'width':1300,'height':700},locale='ko-KR',color_scheme='dark',reduced_motion=rm)
        ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(300)
        wk=pg.evaluate("S.period.week"); W=pg.evaluate("w=>[2,1].map(k=>dayId(Date.parse(w+'T00:00:00+09:00')-k*7*864e5))",wk)
        H=[{'week':w,'total':5e8*(i+1),'cleared':1,'perChar':[{'id':'c1','name':'A','meso':5e8*(i+1),'count':1,'bosses':['루시드(하드)'],'bvals':[5e8],'items':{},'outcomes':{}}]} for i,w in enumerate(W)]
        MW=[{'week':w,'date':w.replace('-','.'),'n':1,'meso':1e8,'list':[{'name':'A','n':1,'meso':1e8}]} for w in W]
        C={'id':'c1','name':'A','level':280,'job':'x','world':'스카니아','image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
        ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':H,'monthHistory':[],'missW':MW,'characters':[C],'startWeek':W[0],'period':pg.evaluate("({...S.period})"),'settings':{}}
        pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total');localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST)
        pg.reload(); pg.wait_for_timeout(1800)
        st=lambda: pg.evaluate("(()=>{const m=document.querySelector('.misschart.lux');const l=m.querySelector('.cline');return [m.classList.contains('inview'),getComputedStyle(l).animationPlayState,+getComputedStyle(m.querySelector('.mpt')).opacity]})()")
        a=st()
        if rm=='no-preference':
            check('화면 밖 빠뜨린 보스메소 그래프: 시작 전 멈춤·숨김', a[0]==False and a[1]=='paused' and a[2]==0, a)
            pg.locator('.misschart.lux').first.scroll_into_view_if_needed(); pg.wait_for_timeout(1800); a=st()
            check('스크롤해서 보이면 시작 → 다 그려짐', a[0] and a[1]=='running' and a[2]==1, a)
            check('맨 위 주간 메소 그래프는 처음부터 보임', pg.evaluate("document.querySelector('.linechart.lux').classList.contains('inview')"))
            shot(pg.locator('.misschart.lux').first,'miss_after_scroll')
        else:
            check('reduced-motion: 화면 밖이어도 애니메이션 없이 바로 보임', a[2]==1 and pg.evaluate("getComputedStyle(document.querySelector('.misschart .cline')).animationName")=='none', a)
        ctx.close()
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
