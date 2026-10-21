import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8964=_tutil.free_port()
# b135: 주 평균 글씨(누적 수익·판매·총 득템) + 주간 메소 그래프 = 이번 주만(목 0시 0부터)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8964)
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b187')}_{TAG}_{name}.png"))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)

try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1400},locale='ko-KR')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(400)
    wk=pg.evaluate("S.period.week")
    wkm=lambda k: pg.evaluate("([w,k])=>{const t=new Date(w+'T00:00:00+09:00');t.setDate(t.getDate()-7*k+1);return t.toISOString().slice(0,10)}",[wk,k])
    E=lambda d:{'enabled':True,'diff':d,'party':1}
    BS={'lucid':E('hard'),'will':E('hard'),'dusk':E('chaos'),'blackmage':E('hard')}
    C1={'id':'c1','name':'캐릭A','level':280,'job':'히어로','world':'스카니아','image':'','bosses':BS,'weekly':{'lucid':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
    C2={'id':'c2','name':'캐릭B','level':270,'job':'비숍','world':'스카니아','image':'','bosses':dict(BS),'weekly':{'lucid':True,'will':True,'dusk':True},'monthly':{'blackmage':wk},'auto':{},'drops':{},'sync':{}}
    C3={'id':'c3','name':'숨김캐','level':270,'job':'비숍','world':'스카니아','image':'','accId':'a9','bosses':dict(BS),'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
    H=[{'week':wkm(k),'total':(3+k)*100000000,'crys':(3+k)*80000000,'isale':(3+k)*20000000,'cleared':3,'perChar':[]} for k in (3,2,1)]
    MW=[{'week':wkm(k),'date':wkm(k),'meso':k*150000000,'n':k,'list':[{'name':'캐릭A','n':k,'meso':k*150000000}]} for k in (3,2,1)]
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':H,'monthHistory':[],'missW':MW,'missM':MW[:2],'characters':[C1,C2,C3],'startWeek':wkm(3),'period':pg.evaluate("({...S.period})"),'settings':{'accounts':[{'id':'a9','label':'키없음','key':''}]}}
    def go(t):
        pg.evaluate("([s,t])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab',t)}",[ST,t]); pg.reload(); pg.wait_for_timeout(1000)
        pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()"); pg.wait_for_timeout(600)
    go('boss')
    pg.evaluate("()=>{window.__cl=[];const v=document.getElementById('view');new MutationObserver(()=>__cl.push(v.className)).observe(v,{attributes:true})}")
    r0=pg.evaluate("(()=>{const c=document.querySelector('#view .card');return c.getBoundingClientRect().top})()")
    pg.locator('.rp-char[data-id=c2]').first.click(); pg.wait_for_timeout(60)
    a=pg.evaluate("""(()=>{const g=document.querySelector('#view .bosslay>.grid');const cs=e=>getComputedStyle(e),an=e=>cs(e).animationName;
      const cells=[...g.querySelectorAll('.cpop')];
      const old=[g,...g.querySelectorAll('*')].filter(e=>/holo|cEnter|scan/.test(an(e)+cs(e,'::after').animationName)).length;
      const still=[...document.querySelectorAll('.rcol,.rcol *')].filter(e=>an(e)!=='none'&&/cellPop|holo|scan/.test(an(e))).length;
      const c0=cells[0],cl=cells[cells.length-1];
      return {view:document.getElementById('view').className,n:cells.length,pop:cells.filter(e=>an(e)==='cellPop').length,old,still,
        ease:cs(c0).animationTimingFunction,dur:cs(c0).animationDuration,d0:cs(c0).animationDelay,dl:cs(cl).animationDelay,
        boss:g.querySelectorAll('.boss-list>.cpop').length,stat:g.querySelectorAll('.stats>.stat.cpop').length,rcol:document.querySelectorAll('.rcol .cpop').length}})()""")
    check('b197 칸마다 작게→원래 크기(cellPop, 튕김 ease, 0.3초, 시차)', 'center' in a['view'] and a['n']>=8 and a['pop']==a['n'] and a['boss']>=3 and a['stat']==3 and a['ease']=='cubic-bezier(0.34, 1.56, 0.64, 1)' and a['dur']=='0.3s' and a['d0']=='0s' and a['dl']!='0s' and a['old']==0, a)
    check('b197 이번 주 수익·가격 표 애니메이션 없음', a['still']==0 and a['rcol']==0, a)
    kf=pg.evaluate("""(()=>{for(const sh of document.styleSheets){for(const r of sh.cssRules){if(r.name==='cellPop')return r.cssText}}return ''})()""")
    check('b197 이동 없음: transform 은 scale 만', 'scale(0.72)' in kf and 'translate' not in kf, kf)
    pg.evaluate("document.getAnimations().filter(x=>x.animationName==='cellPop').forEach(x=>{x.pause();x.currentTime=110})"); shot(pg.locator('#view .bosslay'),'pop_mid')
    pg.evaluate("document.getAnimations().filter(x=>x.animationName==='cellPop').forEach(x=>x.finish())")
    pg.wait_for_timeout(1000)
    r1=pg.evaluate("(()=>{const c=document.querySelector('#view .card');return [c.getBoundingClientRect().top,document.getElementById('view').className]})()")
    check('끝나면 클래스 제거·자리 그대로', 'center' not in r1[1] and abs(r1[0]-r0)<1, (r0,r1))
    pg.evaluate("()=>render()"); x=pg.evaluate("document.getElementById('view').className")
    check('같은 캐릭터 다시 그릴 때는 애니메이션 없음', 'center' not in x, x)
    ctx2=b.new_context(viewport={'width':1400,'height':1400},locale='ko-KR',reduced_motion='reduce'); p2=ctx2.new_page()
    p2.route('https://open.api.nexon.com/**',lambda r:r.abort()); p2.goto(f'http://127.0.0.1:{PORT}/index.html'); p2.wait_for_timeout(300)
    p2.evaluate("s=>{localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); p2.reload(); p2.wait_for_timeout(900)
    p2.locator('.rp-char[data-id=c2]').first.click(); p2.wait_for_timeout(50)
    check('줄인 동작 설정 → 애니메이션 없음', p2.evaluate("[...document.querySelectorAll('#view .bosslay>.grid *')].filter(e=>getComputedStyle(e).animationName==='cellPop').length")==0)
    g=pg.evaluate("(()=>{const e=document.querySelector('#charList .char.on'),o=document.querySelector('#charList .char:not(.on)');return [getComputedStyle(e).boxShadow.split('rgba').length,getComputedStyle(e).animationName,e.getBoundingClientRect().height===o.getBoundingClientRect().height]})()")
    check('b188 선택 캐릭터 간접등: 그림자 여러 겹 + 맥박, 높이 같음', g[0]>=5 and g[1]=='charGlow' and g[2], g)
    pg.wait_for_timeout(400)
    tx=pg.evaluate("(()=>{const on=document.querySelector('#charList .char.on'),of=document.querySelector('#charList .char:not(.on)');return [new DOMMatrix(getComputedStyle(on).transform).m41,new DOMMatrix(getComputedStyle(of).transform).m41,of.getBoundingClientRect().width===on.getBoundingClientRect().width]})()")
    check('b191 선택 캐릭터 오른쪽 6px, 다른 칸 그대로', tx[0]==6 and tx[1]==0 and tx[2], tx)
    shot(pg.locator('#charList'),'charlist')
    pg.set_viewport_size({'width':1400,'height':700}); pg.wait_for_timeout(200)
    for sel in ('.rp-char[data-id=c1]','.rp-char[data-id=c2]','#charList .char[data-id=c1]'):
        pg.evaluate("window.scrollTo(0,250)"); pg.wait_for_timeout(100); y0=pg.evaluate("scrollY")
        pg.evaluate("s=>document.querySelector(s).click()",sel); pg.wait_for_timeout(400)
        y1=pg.evaluate("scrollY"); check(f'b189 {sel} 클릭: 스크롤 그대로', y0>0 and abs(y1-y0)<2, (y0,y1))
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
