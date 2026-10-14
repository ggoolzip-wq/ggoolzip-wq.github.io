# b135: 주 평균 글씨(누적 수익·판매·총 득템) + 주간 메소 그래프 = 이번 주만(목 0시 0부터)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8916'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b135')}_{TAG}_{name}.png"))
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
    wk=pg.evaluate("S.period.week"); prev=pg.evaluate("w=>{const t=new Date(w+'T00:00:00+09:00');t.setDate(t.getDate()-7+1);return t.toISOString().slice(0,10)}",wk)
    H={'week':prev,'total':400000000,'cleared':1,'perChar':[{'id':'c1','name':'캐릭A','meso':400000000,'count':1,'bosses':['루시드(하드)'],'bvals':[400000000],'items':{'lucid|eye':1},'outcomes':{},'revs':{'lucid|eye':{'m':200000000,'a':2,'p':1,'i':'eye'}}}]}
    C={'id':'c1','name':'캐릭A','level':280,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[H],'monthHistory':[],'characters':[C],'startWeek':prev,'period':pg.evaluate("({...S.period})"),'settings':{}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",ST)
    pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("()=>{S.characters[0].weekly.lucid=true;(S.characters[0].wat={}).lucid=Date.now();save();render()}"); pg.wait_for_timeout(400)
    g=pg.evaluate("[document.querySelector('#grandAvg')?.innerText||'', document.querySelector('#weekLine')?.dataset.total, totalData().grand, totalData().weeks.length, totalData().weeks.find(w=>w.cur).total]")
    check('1 누적 수익(총 수익) 밑: 주 평균 메소', g[0]==f"주 평균 {round(g[2]/g[3]):,} 메소", g)
    tips=pg.evaluate("[...document.querySelectorAll('.linechart .lpt')].map(x=>x.dataset.tip)")
    xl=pg.evaluate("[...document.querySelectorAll('.linechart svg > text')].map(t=>t.textContent)")
    check('b136 그래프: 주마다 점 1개, 점 = 그 주 메소(누적 아님)', len(tips)==2 and '주간 수익 6억' in tips[0] and '주간 수익 5,970만' in tips[1], tips)
    check('b136 x축 1주차·2주차', '1주차' in xl and '2주차' in xl, xl)
    shot(pg.locator('#view .card').nth(0),'total_card'); shot(pg.locator('#view .card').nth(1),'week_graph')
    pg.evaluate("()=>{localStorage.setItem('mapleBossTracker.tab','loot');location.reload()}"); pg.wait_for_timeout(900)
    t=pg.evaluate("[document.querySelector('#salesAvg')?.innerText||'', document.querySelector('#itemsAvg')?.innerText||'', totalData().weeks.length]")
    check('2 아이템 판매 누적 수익 밑: 주 평균 판매 메소', t[0]==f"주 평균 {round(200000000/t[2]):,} 메소", t)
    check('3 총 득템 밑: 주 평균 아이템 개수', t[1]=='주 평균 0.5개', t)
    if pg.locator('#salesCard').count(): shot(pg.locator('#salesCard'),'sales')
    if pg.locator('#ltTotal').count(): shot(pg.locator('#ltTotal').locator('xpath=ancestor::div[contains(@class,"card")][1]'),'loot_total')
    # 목 리셋: c.wat 도 지움
    pg.evaluate("w=>{S.characters[0].wat={lucid:1};S.period.week=w;checkResets()}",prev)
    check('목 리셋 때 처치 시간(c.wat)도 비움 → 그래프 0부터', pg.evaluate("JSON.stringify(S.characters[0].wat)")=='{}', pg.evaluate("JSON.stringify(S.characters[0].wat)"))
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
