# b211: 주간 메소 그래프 — 점 말풍선 범위 넓힘(점 반지름 3배 원 + 그 밑 x축까지, 점 크기 그대로, 막대 말풍선 우선) · 5주씩 페이지(기본 최신, 총 누적 = 전체)
#       + 예시 화면에서도 같음 · 예시 블빵 상위 · 디지털 숫자 소수점 1.5배
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8968'
SHOT=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b211_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
H={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'}
TIP="(()=>{const t=document.getElementById('mbtTip');return t&&t.classList.contains('show')?t.innerText:''})()"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1100},locale='ko-KR',reduced_motion='reduce'); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(400)
    wk=pg.evaluate("S.period.week")
    wkm=lambda k: pg.evaluate("([w,k])=>{const t=new Date(w+'T00:00:00+09:00');t.setDate(t.getDate()-7*k+1);return t.toISOString().slice(0,10)}",[wk,k])
    E=lambda d:{'enabled':True,'diff':d,'party':1}
    C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':E('hard'),'will':E('hard'),'dusk':E('chaos')},'weekly':{'lucid':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
    HI=[{'week':wkm(k),'total':(10+(k*37)%9)*100000000,'crys':(8+(k*37)%9)*100000000,'isale':(k%3)*100000000,'cleared':30,'perChar':[]} for k in range(11,0,-1)]
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':HI,'monthHistory':[],'characters':[C],'startWeek':wkm(11),'settings':{'accounts':[]}}
    pg.evaluate("([s,t])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab',t)}",[ST,'total']); pg.reload(); pg.wait_for_timeout(1200)
    pg.evaluate("(()=>{if(tab!=='total'){tab='total';syncTabs();render();}})()"); pg.wait_for_timeout(800)
    ch=pg.locator('.chart.lux.wk'); ch.scroll_into_view_if_needed(); pg.wait_for_timeout(600)
    info=lambda: pg.evaluate("""(()=>{const c=document.querySelector('.chart.lux.wk');return {pn:c.querySelector('.wkpn')?.innerText,lab:[...c.querySelectorAll('.cxl:not(.sub)')].map(e=>e.textContent),tot:c.querySelector('.ctot b').innerText,
      dis:[...c.querySelectorAll('.wkpb')].map(x=>x.disabled),w:c.getBoundingClientRect().width,svgw:c.querySelector('svg').getBoundingClientRect().width,whit:c.querySelectorAll('.whit').length,dots:c.querySelectorAll('circle.wdot').length}})()""")
    a=info(); allsum=sum(h['total'] for h in HI)
    check('5주 페이지: 기본 = 최신 5주(8~12주차), 1/3 아닌 3/3, 다음 버튼 꺼짐', a['pn']=='3 / 3' and a['lab']==[f'{i}주차' for i in range(8,13)] and a['dis']==[False,True] and a['dots']==5 and a['whit']==5, a)
    tot=pg.evaluate("S.history.reduce((t,h)=>t+h.total,0)+weekSummary(S.period.week).total")
    check('총 누적 = 전체 주 합 (페이지와 상관없이)', a['tot']==pg.evaluate("n=>meso(n)",tot), (a['tot'],tot))
    shot(ch,'page3_latest')
    pg.click('.chart.lux.wk [data-wkpg="1"]'); pg.wait_for_timeout(500); a2=info()
    check('◀ 이전 → 3~7주차 (2/3), 카드·그래프 크기 그대로', a2['pn']=='2 / 3' and a2['lab']==[f'{i}주차' for i in range(3,8)] and abs(a2['w']-a['w'])<1 and abs(a2['svgw']-a['svgw'])<1 and a2['tot']==a['tot'], a2)
    shot(pg.locator('.chart.lux.wk'),'page2')
    def clipshot(name):
        if not SHOT: return
        r=pg.evaluate("(()=>{const r=document.querySelector('.chart.lux.wk').getBoundingClientRect();return [r.left,r.top,r.width,r.height]})()")
        pg.screenshot(path=os.path.join(SHOT,f'b211_{name}.png'),clip={'x':max(0,r[0]-10),'y':max(0,r[1]-150),'width':r[2]+20,'height':r[3]+160})
    pg.click('.chart.lux.wk [data-wkpg="1"]'); pg.wait_for_timeout(500); a3=info(); shot(pg.locator('.chart.lux.wk'),'page1')
    check('◀ 이전 → 1~2주차 (1/3), 이전 버튼 꺼짐', a3['pn']=='1 / 3' and a3['lab']==['1주차','2주차'] and a3['dis']==[True,False], a3)
    pg.click('.chart.lux.wk [data-wkpg="-1"]'); pg.click('.chart.lux.wk [data-wkpg="-1"]'); pg.wait_for_timeout(500)
    check('다음 ▶ 두 번 → 다시 최신', info()['pn']=='3 / 3')
    # 넓힌 범위: 점 바로 옆(반지름 3배 안) · 점 밑(막대 사이 빈 곳) → 점 말풍선, 점 크기 그대로
    g=pg.evaluate("""(()=>{const c=document.querySelector('.chart.lux.wk'),L=[...c.querySelectorAll('.lpt')],l=L[2],d=l.querySelector('circle.wdot'),r=d.getBoundingClientRect(),bars=[...l.querySelectorAll('.cbar.wb')].map(b=>b.getBoundingClientRect());
      const ax=c.querySelector('.cg0').getBoundingClientRect(); return {cx:r.left+r.width/2,cy:r.top+r.height/2,dr:r.width,bars:bars.map(b=>[b.left,b.right,b.top,b.bottom]),axis:ax.top,tip:d.dataset.tip}})()""")
    k=pg.evaluate("(()=>{const s=document.querySelector('.chart.lux.wk svg');return s.getBoundingClientRect().width/s.viewBox.baseVal.width})()")
    def at(x,y): pg.mouse.move(x,y); pg.wait_for_timeout(250); return pg.evaluate(TIP), pg.evaluate("(()=>{const d=document.querySelectorAll('.chart.lux.wk circle.wdot')[2];return d.getBoundingClientRect().width})()")
    t1,dw1=at(g['cx']+9*k,g['cy']-6*k)
    check('점 옆(반지름 3배 안, 점 밖)에서도 점 말풍선', t1.startswith(g['tip'].split('\n')[0]) and '주간 결정석' in t1 and abs(dw1-g['dr'])<0.6, (t1[:60],dw1,g['dr']))
    pg.evaluate("(()=>{const o=document.createElement('div');o.id='dbgHit';document.body.appendChild(o)})()")
    # 점 밑 막대 사이 빈 곳 (막대 1·2 사이 x, 막대보다 위·아래 아닌 빈 곳 찾기)
    xs=sorted(g['bars']); gapx=(xs[1][1]+xs[2][0])/2; yb=g['axis']-3
    hit=pg.evaluate("([x,y])=>{const e=document.elementFromPoint(x,y);return e&&e.getAttribute('class')}",[gapx,yb])
    t2,_=at(gapx,yb)
    if SHOT:  # 디버그 복사본: 넓힌 범위를 하늘색으로 보이게 + 마우스 위치 빨간 점 (실제 화면엔 안 보임)
        pg.add_style_tag(content='.linechart .whit{fill:rgba(60,200,255,.22)!important;stroke:#5ce1ff!important;stroke-width:1!important;stroke-dasharray:3 2}')
        pg.evaluate("([x,y])=>{const d=document.createElement('div');d.id='dbgPt';d.style.cssText=`position:fixed;left:${x-4}px;top:${y-4}px;width:8px;height:8px;border-radius:50%;background:#ff3b3b;box-shadow:0 0 0 2px #fff;z-index:2147483647;pointer-events:none`;document.body.appendChild(d)}",[gapx,yb])
        pg.mouse.move(gapx,yb+1); pg.mouse.move(gapx,yb); pg.wait_for_timeout(400); clipshot('zone_debug_overlay')
        pg.evaluate("document.getElementById('dbgPt').remove();document.querySelectorAll('style').forEach(s=>{if(s.textContent.includes('rgba(60,200,255,.22)'))s.remove()})")
        pg.mouse.move(gapx,yb+1); pg.mouse.move(gapx,yb); pg.wait_for_timeout(400); clipshot('zone_bubble_real')
    check('점 밑(막대 사이, x축 바로 위)도 점 말풍선', hit=='whit' and t2.startswith(g['tip'].split('\n')[0]), (hit,t2[:40]))
    hl=pg.evaluate("[...document.querySelectorAll('.chart.lux.wk .lpt')].map(l=>getComputedStyle(l.querySelector('.cbar.wb')).opacity)")
    check('넓힌 범위에서도 그 주만 밝게(다른 주 흐리게)', hl.count('1')>=1 and any(float(x)<0.5 for x in hl), hl)
    # 막대 위 = 막대 말풍선 (범위 안이어도)
    b1=xs[1]; t3,_=at((b1[0]+b1[1])/2,b1[3]-3)
    check('범위 안의 막대 위 = 막대 말풍선 그대로', ('주간 결정석' in t3 and '총 수익' not in t3.split('\n')[0]) and '검마 결정석' not in t3, t3[:60])
    clipshot('bar_tip_still_works')
    # 범위 밖(옆 주 사이 빈 곳) = 말풍선 없음
    # b212: 범위 = 그 주 칸 전체(위 = 그래프 맨 위부터, 아래 = 0선), 옆 주와 안 겹침
    z=pg.evaluate("[...document.querySelectorAll('.chart.lux.wk .whit')].map(e=>{const r=e.getBoundingClientRect();return [r.left,r.right,r.top,r.bottom]})")
    check('b212: 주 칸마다 범위, 옆 주와 안 겹침, 높이 = 그래프 맨 위~0선', all(z[i][1]<z[i+1][0] for i in range(len(z)-1)) and all(abs(q[3]-g['axis'])<3 and q[2]<g['cy']-40*k for q in z), z)
    cxs=pg.evaluate("[...document.querySelectorAll('.chart.lux.wk circle.wdot')].map(e=>{const r=e.getBoundingClientRect();return (r.left+r.right)/2})")
    col=cxs[1]-cxs[0]; ww=[q[1]-q[0] for q in z]
    check('b213: 범위 좌우 = b212 칸의 약 70%, 점 가운데', all(abs(w-0.7*(col-6*k))<3 for w in ww) and all(abs((q[0]+q[1])/2-c)<1.5 for q,c in zip(z,cxs)), (col,ww[:2]))
    zt=z[2]; t5,_=at((zt[0]+zt[1])/2-20*k, zt[2]+6)
    check('b212: 점 위쪽(그래프 맨 위 근처)에서도 점 말풍선', t5.startswith(g['tip'].split('\n')[0]), t5[:40])
    if SHOT:
        pg.add_style_tag(content='.linechart .whit{fill:rgba(60,200,255,.18)!important;stroke:#5ce1ff!important;stroke-width:1!important;stroke-dasharray:3 2}')
        px,py=(zt[0]+zt[1])/2-20*k, zt[2]+6
        pg.evaluate("([x,y])=>{const d=document.createElement('div');d.id='dbgPt';d.style.cssText=`position:fixed;left:${x-4}px;top:${y-4}px;width:8px;height:8px;border-radius:50%;background:#ff3b3b;box-shadow:0 0 0 2px #fff;z-index:2147483647;pointer-events:none`;document.body.appendChild(d)}",[px,py])
        pg.mouse.move(px,py+1); pg.mouse.move(px,py); pg.wait_for_timeout(400); clipshot('b212_zone_debug_top')
        pg.evaluate("document.getElementById('dbgPt').remove();document.querySelectorAll('style').forEach(s=>{if(s.textContent.includes('rgba(60,200,255,.18)'))s.remove()})")
        pg.mouse.move(px,py+1); pg.mouse.move(px,py); pg.wait_for_timeout(400); clipshot('b212_bubble_from_top')
    gx=(z[2][1]+z[3][0])/2; hit=pg.evaluate("([x,y])=>{const e=document.elementFromPoint(x,y);return e&&e.getAttribute('class')}",[gx,g['cy']-30*k])
    check('b212: 주 사이 틈 = 점 범위 아님', hit!='whit', hit)
    pg.set_viewport_size({'width':390,'height':900}); pg.wait_for_timeout(500)
    m=pg.evaluate("(()=>{const p=document.querySelector('.chart.lux.wk .wkpg');const r=p.getBoundingClientRect();return {one:r.height<30,inside:r.left>=0&&r.right<=innerWidth+1}})()")
    check('390px: 페이지 버튼 한 줄·화면 안', m['one'] and m['inside'], m)
    ctx.close()
    # 예시 화면: 같은 그래프(넓힌 범위) + 블빵 상위 값 있음 + 소수점 1.5배
    ctx=b.new_context(viewport={'width':1400,'height':1000},locale='ko-KR',reduced_motion='reduce',device_scale_factor=2); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    ctx.route('http://127.0.0.1:9996/**',lambda r:r.fulfill(status=204,headers={**H,'Access-Control-Allow-Methods':'GET'}) if r.request.method=='OPTIONS' else r.fulfill(status=200 if r.request.url.endswith('/api/prices') else 401,headers=H,content_type='application/json',body=json.dumps({'prices':{'g_life':{'p':889000000,'t':1},'ring:r4':{'p':3600000000,'t':1},'ring:c4':{'p':2500000000,'t':1}}}) if r.request.url.endswith('/api/prices') else '{}'))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9996')"); pg.reload(); pg.wait_for_timeout(2500)
    pg.click('#tabs [data-tab=total]'); pg.wait_for_timeout(1000)
    d=pg.evaluate("(()=>{const c=document.querySelector('.chart.lux.wk');return c&&{whit:c.querySelectorAll('.whit').length,dots:c.querySelectorAll('circle.wdot').length,pg:!!c.querySelector('.wkpg')}})()")
    check('예시 화면 주간 메소도 넓힌 범위', d and d['whit']==d['dots']>0, d)
    pg.click('#tabs [data-tab=loot]'); pg.wait_for_timeout(1200)
    bb=pg.evaluate("(()=>{const e=document.getElementById('ltBbang');return {v:e.querySelector('.v .tir-sr')?.textContent||e.querySelector('.v').innerText,cap:e.querySelector('.bbrows')?.innerText||''}})()")
    check('예시 득템 분석 블빵 상위 = 값(승·패 기록)', bb['v'].startswith('상위') and '승' in bb['cap'], bb)
    shot(pg.locator('#ltBbang'),'demo_bbang')
    dot=pg.evaluate("(()=>{const p=[...document.querySelectorAll('.revpanel .rp-total .tl, .tir .tl')].map(e=>e.getAttribute('d')).find(d=>/h15v15h-15z$/.test(d||''));return p||''})()")
    pg.click('#tabs [data-tab=boss]'); pg.wait_for_timeout(800)
    dd=pg.evaluate("[...document.querySelectorAll('.revpanel .rp-total .tl')].map(e=>e.getAttribute('d')).filter(d=>/^M[\\d.]+,61h15v15h-15z$/.test(d)).length")
    check('디지털 숫자 소수점 15×15(1.5배)', dd==1, dd)
    ctx.close(); b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
