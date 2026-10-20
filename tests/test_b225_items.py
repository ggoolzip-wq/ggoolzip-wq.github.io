# b225: '이번주 획득 아이템' xN — 반지 상자만 얻은 주(사용자 실제 상황)에도 x0 표시, 검마 아이템(이번 주) 포함 · 실제 + 예시 (b221 도우미 재사용)
# b221: 이번 주 수익 총합 — 개수 줄 전부 xN(주보 결정석·검마 결정석·이번주 획득 아이템·반지 상자·이번 주 남은 결정석·검마 남은 결정석), 개수 한 세로줄, 줄바꿈·잘림 없음 · 실제 + 예시
import os, sys, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8997'
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
    def shot(pg,name):
        os.makedirs('/workspace/b225',exist_ok=True)
        bb=pg.evaluate("(()=>{const P=document.querySelector('.revpanel');const sec=P.querySelector('.rp-sec')?.getBoundingClientRect(),r=P.getBoundingClientRect();return {x:r.left,y:r.top+scrollY,width:r.width,height:(sec?sec.top:r.bottom)-r.top}})()")
        pg.screenshot(path='/workspace/b225/'+name,clip=bb,full_page=True)
    ctx,pg=mk({'width':1600,'height':1000})
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(300)
    E_=lambda d:{'enabled':True,'diff':d,'party':1}
    BS={k:E_(d) for k,d in [('lotus','hard'),('seren','hard'),('limbo','normal'),('adversary','normal'),('kaling','normal'),('slime','chaos'),('dunkel','hard'),('blackmage','extreme')]}
    # 사용자 실제 이번 주(2026-10-15)와 같은 모양: 획득 = 반지 상자 9개뿐(흰·검·생명), 반지 상자 판매 1건
    rings=[{'lotus|r_white':1,'seren|r_white':1,'limbo|r_life':1},{'adversary|r_white':1,'kaling|r_white':1,'seren|r_white':1},{'seren|r_white':1},{'slime|r_black':1},{'dunkel|r_black':1}]
    CH=[{'id':f'c{i}','name':f'테스트{i}','level':285,'job':'히어로','world':'스카니아','image':'','bosses':dict(BS),'weekly':{k.split('|')[0]:True for k in d},'monthly':{},'auto':{},'drops':d,'sync':{}} for i,d in enumerate(rings,1)]
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':CH,'settings':{'accounts':[]}}
    pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",[ST]); pg.reload(); pg.wait_for_timeout(1200)
    L=verify(pg,'반지 상자만',{'이번주 획득 아이템':'x0','반지 상자':'x9'})
    shot(pg,'b225_items_rings_only.png')
    pg.evaluate("()=>{const c=S.characters[0];c.drops['lotus|blackheart']=2;save();render()}"); pg.wait_for_timeout(300)
    verify(pg,'주간 아이템 2개',{'이번주 획득 아이템':'x2','반지 상자':'x9'})
    pg.evaluate("()=>{const c=S.characters[1],wk=S.period.week;c.monthly={blackmage:wk};c.mdrops={'blackmage|genesis':1};S.characters[2].monthly={blackmage:'2000-01-06'};S.characters[2].mdrops={'blackmage|genesis':1};save();render()}"); pg.wait_for_timeout(300)
    verify(pg,'검마 아이템(이번 주만)',{'이번주 획득 아이템':'x3'})
    shot(pg,'b225_items_after.png')
    for w in (1280,390): pg.set_viewport_size({'width':w,'height':900}); pg.wait_for_timeout(300); verify(pg,f'실제 {w}')
    ctx.close()
    for w in (1600,390):
        ctx,pg=mk({'width':w,'height':1000})
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
        L=verify(pg,f'예시 {w}')
        check(f'예시 {w}: 이번주 획득 아이템 xN 있음', any(l['lb']=='이번주 획득 아이템' and l['x'] for l in L), [l['txt'] for l in L])
        if w==1600: shot(pg,'b225_items_demo.png')
        ctx.close()
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
