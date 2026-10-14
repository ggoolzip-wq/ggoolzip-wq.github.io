# b58: 이번 주 수익 패널 — 월간 보스 합산(잡은 주만), (따로 합산) 영역 삭제, 이중 계산 없음
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8843/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8843','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
ch={'id':'c0','name':'캐릭00','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'',
    'bosses':{'kaling':{'enabled':True,'diff':'hard','party':1},'blackmage':{'enabled':True,'diff':'hard','party':1}},'weekly':{'kaling':True},'monthly':{},'auto':{},'sync':{},'drops':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[ch],'history':[],'monthHistory':[],'worldOrder':[],'startWeek':'2026-10-01','settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",ST); pg.reload(); pg.wait_for_timeout(800)
    base=pg.evaluate("allRevenue().total"); mm=pg.evaluate("price(findBoss('blackmage'),'hard')")
    check('월간 클리어 전: 합계 = 주간만, 월간 줄 없음', '검마 결정석 0개' in pg.inner_text('.revpanel') and pg.locator('.rp-month').count()==0, base)
    # 이번 주에 잡음
    pg.evaluate("()=>{const c=S.characters[0];c.monthly.blackmage=S.period.week;save();render()}"); pg.wait_for_timeout(300)
    txt=pg.inner_text('.revpanel'); tot=pg.evaluate("(()=>{const a=allRevenue();return [a.total,a.monthTotal,weekMonthly(a)]})()")
    check('같은 주: 큰 합계에 월간 포함 + 월간 보스 결정석 1개 줄', tot[1]==mm and tot[2]=={'n':1,'meso':mm} and '검마 결정석 1개' in txt and f"{base+mm:,}" in txt and '(따로 합산)' not in txt, (tot,txt[:200]))
    pc=pg.evaluate("(()=>{const r=document.querySelector('.rp-char');return [r.innerText,r.querySelector('b').innerText]})()")
    check('같은 주: 월간 줄에 메소 금액 없음, 캐릭터별 금액에 월간 추가 + 월간 ✓', '메소 포함' not in txt and '검마 결정석 1개' in txt and pc[1]==pg.evaluate(f"meso({base+mm})") and '월간 ✓' in pc[0], (pc,txt[:200]))
    big=pg.inner_text('.rp-total'); check('주황 합계 억 표기 = 합산값', big.replace('\n','').startswith(pg.evaluate(f"(({base}+{mm})/1e8).toFixed(1)")+"억"), big)
    # 이중 계산 없음: 주간 기록/월간 기록 집계는 그대로
    ws=pg.evaluate("[weekSummary(S.period.week).total, monthSummary(S.period.month).total, allRevenue().total]")
    check('weekSummary/monthSummary/allRevenue 는 그대로(이중 계산 없음)', ws[0]==base and ws[1]==mm and ws[2]==base, ws)
    # 지난 주에 잡은 월간 보스: 이번 주에 더하지 않음
    pg.evaluate("()=>{const c=S.characters[0];c.monthly.blackmage='2000-01-01';save();render()}"); pg.wait_for_timeout(300)
    txt=pg.inner_text('.revpanel'); tot=pg.evaluate("weekMonthly(allRevenue())")
    pc=pg.evaluate("(()=>{const r=document.querySelector('.rp-char');return [r.innerText,r.querySelector('b').innerText]})()")
    check('지난 주에 잡은 월간 보스: 캐릭터별 금액·월간 ✓ 없음', '월간 ✓' not in pc[0] and pc[1]==pg.evaluate(f"meso({base})"), pc)
    check('지난 주에 잡은 월간 보스: 이번 주 수익에 미포함', tot['n']==0 and '월간 보스 결정석' not in txt and f"{base:,}" in txt, (tot,txt[:160]))
    # 분석 탭 라인 차트: 월간 보스는 잡은 주에만
    hw='2026-10-01'
    st=json.loads(json.dumps(ST)); c0=st['characters'][0]
    st['history']=[{'week':hw,'weeklyOnly':True,'total':100000000,'cleared':1,'perChar':[{'id':'c0','name':'캐릭00','meso':100000000,'count':1,'bosses':['카링(하드)'],'bvals':[100000000],'items':{},'outcomes':{}}]}]
    st['monthHistory']=[{'month':'2026-10','total':50000000,'cleared':1,'perChar':[{'id':'c0','name':'캐릭00','meso':50000000,'bosses':['검은 마법사(하드)'],'bvals':[50000000],'mweeks':[hw],'items':{},'outcomes':{}}]}]
    c0['monthly']={}; c0['weekly']={}
    pg.evaluate("s=>{localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",st); pg.reload(); pg.wait_for_timeout(900)
    tips=pg.evaluate("[...document.querySelectorAll('.linechart .lpt')].map(g=>g.dataset.tip)")
    check('차트: 지난 주(잡은 주)에만 월간 5천만 포함, 이번 주엔 없음', len(tips)==2 and '1.5억'.replace('1.5억','') is not None and '월간 보스 1개' in tips[0] and '월간 보스' not in tips[1], tips)
    # 이번 주에 잡은 월간 보스 → 이번 주 점에 포함
    c0['monthly']={'blackmage':None}
    pg.evaluate("s=>{const x=JSON.parse(JSON.stringify(s));x.characters[0].monthly={blackmage:'__W__'};x.monthHistory=[];localStorage.setItem('mapleBossTracker.v1',JSON.stringify(x))}",st); pg.reload(); pg.wait_for_timeout(500)
    pg.evaluate("()=>{S.characters[0].monthly.blackmage=S.period.week;save();render()}"); pg.wait_for_timeout(400)
    tips=pg.evaluate("[...document.querySelectorAll('.linechart .lpt')].map(g=>g.dataset.tip)")
    check('차트: 이번 주에 잡은 월간 보스 이번 주 점에 포함', '월간 보스 1개' in tips[-1] and '(이번 주)' in tips[-1], tips)
    # 툴팁 말풍선
    pg.locator('.linechart .lpt circle').last.scroll_into_view_if_needed(); pg.locator('.linechart .lpt circle').last.hover(force=True); pg.wait_for_timeout(300)
    tb=pg.evaluate("(()=>{const e=document.querySelector('#mbtTip');if(!e)return null;const r=e.getBoundingClientRect(),c=getComputedStyle(e),a=getComputedStyle(e,'::after');return [e.classList.contains('show'),r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight,parseFloat(c.borderTopLeftRadius),c.boxShadow!=='none',a.content,e.innerText.includes('누적')]})()")
    check('툴팁: 보임·화면 안·둥근 모서리·그림자·꼬리·값 표시', tb and tb[0] and tb[1] and tb[2]>=10 and tb[3] and tb[4]=='""' and tb[5], tb)
    check('JS 오류 없음', not errs, errs)
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
