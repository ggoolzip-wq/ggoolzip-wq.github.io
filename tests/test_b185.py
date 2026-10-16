# b135: 주 평균 글씨(누적 수익·판매·총 득템) + 주간 메소 그래프 = 이번 주만(목 0시 0부터)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8963'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b185')}_{TAG}_{name}.png"))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
    r=pg.evaluate("""(()=>{const P=document.querySelector('.revpanel');const g=s=>[...P.querySelectorAll(s)].map(e=>e.innerText.replace(/\\s+/g,' ').trim());
      const exp=vchars().reduce((t,c)=>t+leftOf(c).w,0), expm=vchars().reduce((t,c)=>t+leftOf(c).m,0);
      const ch=[...P.querySelectorAll('.rp-char')].map(e=>[e.querySelector('.rp-nm')?.innerText.trim(),[...e.querySelectorAll('.rp-left')].map(x=>x.className.includes('rl-m')?'m':'w'),[...e.children].findIndex(x=>x.classList.contains('rp-left'))<[...e.children].findIndex(x=>x.querySelector&&x.querySelector('.mini'))]);
      const lines=[...P.querySelectorAll('.rp-line.rp-left')];
      return {top:g('.rp-line.rp-left'),exp,expm,ch,wrap:lines.every(e=>e.scrollWidth<=e.clientWidth+1&&e.getBoundingClientRect().height<26),
        order:[...P.children].map(e=>e.className).join('|'), font:lines[0]?getComputedStyle(lines[0].querySelector('.tsmn')).fontFamily===getComputedStyle(document.body).fontFamily:false}})()""")
    check('A1 이번 주 남은 결정석 줄 = 보이는 캐릭터 합', any(t.startswith('이번 주 남은 결정석') and f"-{r['exp']:,}" in t for t in r['top']) and r['exp']>0, r)
    check('A2 검마 남은 결정석 줄 = 캐릭A만(캐릭B 이번 달 잡음)', any(t.startswith('검마 남은 결정석') and f"-{r['expm']:,}" in t for t in r['top']) and r['expm']>0, r)
    check('A 줄 위치: 반지/아이템 줄 다음 · 캐릭터별 위, 한 줄, 기본 글씨체', r['wrap'] and r['font'] and r['order'].index('rp-sec')>0, r['order'])
    d=dict((x[0].replace('★','').strip(),x) for x in r['ch'])
    check('B 캐릭A: 주간·검마 줄 둘 다, 닉네임과 게이지 사이', d['캐릭A'][1]==['w','m'] and d['캐릭A'][2], d)
    check('B 캐릭B: 검마 0 → 줄 숨김', 'm' not in d['캐릭B'][1], d)
    check('규칙 9 숨김캐 안 보임', '숨김캐' not in d, list(d))
    col=pg.evaluate("(()=>{const c=s=>{const e=document.querySelector(s);return e?getComputedStyle(e).color:null};return [c('.revpanel .rp-cry.rc-g .rpn .tsmn'),c('.revpanel .rp-sale .rpl .tsmn'),c('.revpanel .rp-left .rpn .tsmn'),c('.revpanel .rp-char .rc-g span'),c('.revpanel .rp-char .rp-left span'),c('.revpanel .rp-cm.rc-g .rpn .tsmn'),document.querySelector('.revpanel .rp-cm .rpn')?.innerText||'',document.querySelector('.revpanel .rp-cry .rpn').innerText,document.querySelector('.revpanel .rp-char .rc-g').innerText]})()")
    check('b192 색: 초록(+)·빨강(-)', col[0]==col[1]==col[3]=='rgb(95, 224, 138)' and col[2]==col[4]=='rgb(255, 107, 107)' and col[7].startswith('+') and '+' in col[8], col)
    check('b196 검마 결정석(획득) 초록 +', col[5]=='rgb(95, 224, 138)' and col[6].startswith('+'), col)
    shot(pg.locator('.revpanel'),'week_panel')
    go('total')
    c=pg.evaluate("""(()=>{const ch=document.querySelector('.linechart');const g=[...ch.querySelectorAll('.lpt')];return {n:g.length,bars:g.map(x=>x.querySelectorAll('.cbar.wb').length),dots:g.every(x=>x.querySelector('circle')),line:!!ch.querySelector('.cline'),leg:ch.querySelector('.wlegend')?.innerText.replace(/\\s+/g,' ')}})()""")
    check('주간 메소: 주마다 막대 4개 + 점 + 선 + 범례', c['n']>=3 and all(x==4 for x in c['bars']) and c['dots'] and c['line'] and '검마' in (c['leg'] or ''), c)
    pg.locator('.linechart .lpt').nth(1).locator('circle.wdot').hover(force=True); pg.wait_for_timeout(400)
    z=pg.evaluate("(()=>{const t=document.getElementById('mbtTip');if(!t)return null;const r=t.getBoundingClientRect();const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);const cs=getComputedStyle(t);return [cs.zIndex,cs.position==='fixed'&&cs.visibility!=='hidden'&&+cs.opacity>0&&r.width>0&&t.parentElement===document.body&&t.innerText.includes('총 수익')]})()")
    check('툴팁 맨 위 (가운데 점에서 툴팁이 보임)', z and z[1], z)
    shot(pg.locator('.card:has(.linechart)').first,'week_chart')
    pg.locator('.linechart .lpt').nth(2).locator('circle.wdot').hover(force=True); pg.wait_for_timeout(700)
    d=pg.evaluate("(()=>{const t=document.getElementById('mbtTip');const L=[...document.querySelectorAll('.linechart .lpt')];return [t.innerText,L.map(x=>getComputedStyle(x.querySelector('circle[data-tipanchor]')).opacity),getComputedStyle(L[2].querySelector('.cbar.wb')).animationName,getComputedStyle(L[2].querySelector('circle[data-tipanchor]')).animationName]})()")
    lines=d[0].split('\n')
    check('b191 점 hover 말풍선 4줄(누적 없음)', len(lines)==4 and lines[0].startswith('3주차 총 수익 : ') and lines[1].startswith('주간 결정석 : ') and lines[2].startswith('검마 결정석 : ') and lines[3].startswith('아이템 판매 : ') and '누적' not in d[0], d[0])
    check('b191 점 hover: 다른 주 흐림 + 그 주 막대·점 맥박', all(float(o)<.5 for i,o in enumerate(d[1]) if i!=2) and float(d[1][2])==1 and d[2]=='wbPulse' and d[3]=='dotPulse', d)
    rr=pg.evaluate("(()=>{const c=document.querySelectorAll('.linechart .lpt')[2].querySelector('circle.wdot');return [getComputedStyle(c).r,c.getAttribute('r'),document.querySelectorAll('.linechart.wk .lpt[data-tip], .linechart.wk .lpt > rect:not(.cbar)').length]})()")
    check('b195 점 hover 크기 그대로·hit=점 자체(열 전체 hover 없음)', rr[0]==rr[1]+'px' and rr[2]==0, rr)
    shot(pg.locator('.card:has(.linechart)').first,'week_chart_dot')
    pg.mouse.move(5,5); pg.wait_for_timeout(300)
    bar=pg.locator('.linechart .lpt').nth(3).locator('.cbar.wb1'); bar.hover(); pg.wait_for_timeout(900)
    q=pg.evaluate("(()=>{const t=document.getElementById('mbtTip'),b=document.querySelectorAll('.linechart .lpt')[3].querySelector('.cbar.wb1');const tr=t.getBoundingClientRect(),br=b.getBoundingClientRect(),cs=getComputedStyle(b);return [t.innerText,tr.bottom<=br.top+1&&Math.abs((tr.left+parseFloat(t.style.getPropertyValue('--ax')))-(br.left+br.width/2))<3,cs.animationName,parseFloat(cs.strokeWidth)]})()")
    check('막대 hover: 그 막대 말풍선(위·꼬리 가운데) + 금빛 테두리 애니메이션', '주간 결정석' in q[0] and q[1] and 'wbDraw' in q[2] and q[3]>1, q)
    shot(pg.locator('.card:has(.linechart)').first,'week_chart_hover')
    m=pg.evaluate("[...document.querySelectorAll('.misschart .ctot')].map(e=>e.innerText.replace(/\\s+/g,' '))")
    check('빠뜨린 보스메소 주간·월간 총 누적 표시', len(m)==2 and all('빠뜨린 보스메소 총 누적' in x for x in m), m)
    pg.locator('.card:has(.misschart)').nth(1).scroll_into_view_if_needed(); pg.wait_for_timeout(2500)
    for i,nm in ((0,'miss_w'),(1,'miss_m')): shot(pg.locator('.card:has(.misschart)').nth(i),nm)
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
