# b221: 이번 주 수익 총합 — 개수 줄 전부 xN(주보 결정석·검마 결정석·이번주 획득 아이템·반지 상자·이번 주 남은 결정석·검마 남은 결정석), 개수 한 세로줄, 줄바꿈·잘림 없음 · 실제 + 예시
import os, sys, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8973'
SHOT=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
M="""(()=>{const P=document.querySelector('.revpanel');const L=[...P.querySelectorAll(':scope > .rp-line')].map(r=>{const lb=r.querySelector('.rplb'),x=r.querySelector('.rpx'),n=r.querySelector('.rpn');const rr=r.getBoundingClientRect();
  return {cls:r.className,lb:lb&&lb.textContent,lbFit:lb?lb.scrollWidth<=lb.clientWidth+1:false,x:x&&x.textContent,xl:x?Math.round(x.getBoundingClientRect().left*2)/2:null,
    xr:x?x.getBoundingClientRect().right:0,nl:n?n.getBoundingClientRect().left:9e9,h:Math.round(rr.height),fit:r.scrollWidth<=r.clientWidth+1,rr:rr.right,pr:P.getBoundingClientRect().right,txt:r.innerText.replace(/\\s+/g,' ')}});
  return L})()"""
def verify(pg,tag,expect=None):
    L=pg.evaluate(M)
    cnt=[l for l in L if l['lb']]
    check(f'{tag}: 개수 줄 = xN(개 없음)', cnt and all(('개' not in l['txt']) and (l['x'] is None or (l['x'].startswith('x') and l['x'][1:].isdigit())) for l in cnt), [l['txt'] for l in L])
    xs={l['xl'] for l in cnt if l['x']}
    check(f'{tag}: xN 한 세로줄(왼쪽 끝 같음)', len(xs)==1, [(l['lb'],l['xl']) for l in cnt])
    check(f'{tag}: 이름 안 잘림·줄바꿈 없음·패널 안·숫자와 안 겹침', all(l['lbFit'] and l['fit'] and l['h']<=24 and l['rr']<=l['pr']+0.5 and l['xr']<=l['nl']+0.5 for l in cnt), [(l['lb'],l['lbFit'],l['fit'],l['h'],round(l['xr']),round(l['nl'])) for l in cnt])
    if expect:
        got={l['lb']:l['x'] for l in cnt}
        check(f'{tag}: 개수 값', all(got.get(k)==v for k,v in expect.items()), got)
    return L
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def mk(vp):
        ctx=b.new_context(viewport=vp,locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); return ctx,pg
    ctx,pg=mk({'width':1600,'height':1000})
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(300)
    E_=lambda d:{'enabled':True,'diff':d,'party':1}
    BS={'lucid':E_('hard'),'will':E_('hard'),'dusk':E_('chaos'),'dunkel':E_('hard'),'jinhilla':E_('hard'),'seren':E_('hard'),'kalos':E_('normal'),'kaling':E_('normal'),'gaze':E_('hard'),'verus':E_('hard'),'damien':E_('hard'),'lotus':E_('hard'),'slime':E_('chaos'),'papulatus':E_('chaos'),'blackmage':E_('hard')}
    # c1: 5개 잡음 → 남은 7, c2: 12개 다 잡음 → 0, c3: 하나도 → 12 (켜 둔 보스 14개 이상) → 남은 19 · 검마: c1 이번 달 잡음, c2·c3 안 잡음 → 2
    CH=[{'id':f'c{i}','name':f'테스트{i}','level':285,'job':'히어로','world':'스카니아','image':'','bosses':dict(BS),'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i in range(1,4)]
    W5=['lucid','will','dusk','dunkel','jinhilla']; W12=W5+['seren','kalos','kaling','gaze','verus','damien','lotus']
    CH[0]['weekly']={k:True for k in W5}; CH[1]['weekly']={k:True for k in W12}; CH[0]['drops']={'lucid|twilight':0,'will|eye':1}
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':CH,'settings':{'accounts':[]}}
    pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",[ST]); pg.reload(); pg.wait_for_timeout(1200)
    pg.evaluate("()=>{const wk=S.period.week;S.characters[0].monthly={blackmage:wk};save();render()}"); pg.wait_for_timeout(300)
    exp=pg.evaluate("(()=>{let wn=0;for(const c of vchars()){wn+=remainingWeekly(c).list.length;}return wn})()")
    per=pg.evaluate("vchars().map(c=>[weeklyCount(c),expectedAll(c).filter(x=>!c.weekly[x.slot]).length])")
    exp2=sum(min(12-d,a) for d,a in per); cr=pg.evaluate("allRevenue(vchars()).count")
    check('남은 개수 = 캐릭터별 min(12 − 잡은 수, 켜 둔 안 잡은 보스) 합 (다 잡은 캐릭터 0)', exp==exp2 and exp>0, (exp,per))
    verify(pg,'실제 1600',{'주보 결정석':None,'검마 결정석':'x1','이번주 획득 아이템':'x1','이번 주 남은 결정석':None,'검마 남은 결정석':'x2'}) # b230: 주보 결정석·이번 주 남은 결정석 = 개수 없음
    if SHOT:
        bb=pg.evaluate("(()=>{const P=document.querySelector('.revpanel');const sec=P.querySelector('.rp-sec').getBoundingClientRect(),r=P.getBoundingClientRect();return {x:r.left,y:r.top+scrollY,width:r.width,height:sec.top-r.top}})()")
        pg.screenshot(path=os.path.join(SHOT,'b221_real_closeup.png'),clip=bb,full_page=True)
    # 남은 0 → 줄 없음 그대로, 반지 상자 줄도 같은 세로줄
    pg.evaluate("()=>{const c=S.characters[2];c.weekly={lucid:true};c.drops={'lucid|r_life':2};c.dropOut={'lucid|r_life':['gl','x']};save();render()}"); pg.wait_for_timeout(300)
    L=verify(pg,'반지 상자 포함')
    check('반지 상자 x2 도 같은 칸', any(l['lb']=='반지 상자' and l['x']=='x2' for l in L), [l['txt'] for l in L])
    for w in (1280,1024,390,360):
        pg.set_viewport_size({'width':w,'height':900}); pg.wait_for_timeout(300); verify(pg,f'실제 {w}')
    # 큰 금액(캐릭터 많음): 주보·남은 결정석 금액이 11자리 이상이어도 한 줄
    pg.evaluate("()=>{const base=S.characters[0];for(let i=4;i<=24;i++){const c=JSON.parse(JSON.stringify(base));c.id='c'+i;c.name='큰'+i;c.weekly=i%2?Object.fromEntries(Object.keys(c.bosses).filter(k=>findBoss(k)?.type==='weekly').slice(0,12).map(k=>[k,true])):{};S.characters.push(c);}save();render()}"); pg.wait_for_timeout(400)
    big=pg.evaluate("[...document.querySelectorAll('.revpanel > .rp-line .rpn')].map(e=>e.textContent)")
    check('큰 금액 데이터', any(len(x)>=15 for x in big), big)
    for w in (1600,1440,1280,1181,1100,390,360):
        pg.set_viewport_size({'width':w,'height':900}); pg.wait_for_timeout(300); verify(pg,f'큰 금액 {w}')
        if SHOT and w in (1280,360):
            bb=pg.evaluate("(()=>{const P=document.querySelector('.revpanel');const sec=P.querySelector('.rp-sec').getBoundingClientRect(),r=P.getBoundingClientRect();return {x:r.left,y:r.top+scrollY,width:r.width,height:sec.top-r.top}})()")
            pg.screenshot(path=os.path.join(SHOT,f'b221_real_bigamount_{w}.png'),clip=bb,full_page=True)
    if SHOT:
        bb=pg.evaluate("(()=>{const P=document.querySelector('.revpanel');const sec=P.querySelector('.rp-sec').getBoundingClientRect(),r=P.getBoundingClientRect();return {x:r.left,y:r.top+scrollY,width:r.width,height:sec.top-r.top}})()")
        pg.screenshot(path=os.path.join(SHOT,'b221_real_closeup_360.png'),clip=bb,full_page=True)
    ctx.close()
    for w in (1600,390):
        ctx,pg=mk({'width':w,'height':1000})
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
        check(f'예시 {w}: 켜짐', pg.evaluate("!!document.querySelector('.demotop,.dmbanner')"))
        L=verify(pg,f'예시 {w}')
        check(f'예시 {w}: 주보 결정석·이번 주 남은 결정석 xN 없음(b230)', not any(l['lb'] in ('주보 결정석','이번 주 남은 결정석') and l['x'] for l in L), [l['txt'] for l in L])
        if SHOT:
            bb=pg.evaluate("(()=>{const P=document.querySelector('.revpanel');const sec=P.querySelector('.rp-sec').getBoundingClientRect(),r=P.getBoundingClientRect();return {x:r.left,y:r.top+scrollY,width:r.width,height:sec.top-r.top}})()")
            pg.screenshot(path=os.path.join(SHOT,f'b221_demo_closeup_{w}.png'),clip=bb,full_page=True)
        ctx.close()
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
