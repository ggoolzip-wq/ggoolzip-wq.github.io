# b61: (1) 못 가진 아이템 목록 — 가로 스크롤/잘림 없음, 아이템 이름·보스 묶음은 한 줄, 글자 >=10px
#      (2) 낮은 창 — 왼쪽 아래(소식·썬데이)·오른쪽(결정석 가격) 카드가 잘리지 않고 스크롤로 닿음
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8845/index.html'
SHOT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8845','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
chs=[{'id':f'c{i}','name':f'캐릭{i:02d}','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i==0,'image':'',
    'bosses':{'kaling':{'enabled':True,'diff':'hard','party':1},'blackmage':{'enabled':True,'diff':'hard','party':1},'lotus':{'enabled':True,'diff':'normal','party':1}},'weekly':{'kaling':True},'monthly':{},'auto':{},'sync':{},'drops':{}} for i in range(8)]
per=[{'id':'c0','name':'캐릭00','meso':100000000,'count':2,'bosses':['카링(하드)'],'bvals':[100000000],'items':{'kaling|g_faith':1},'outcomes':{}}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':chs,'history':[{'week':'2026-10-01','weeklyOnly':True,'total':100000000,'cleared':1,'perChar':per}],'monthHistory':[],'worldOrder':[],'startWeek':'2026-10-01','settings':{'accounts':[]}}
MISS="""(()=>{const t=document.querySelector('#missItems .misstbl'),w=t.parentElement,card=document.querySelector('#missItems');
  const multi=e=>{const r=document.createRange();r.selectNodeContents(e);return new Set([...r.getClientRects()].filter(x=>x.width>1).map(x=>Math.round(x.top/10))).size>1};
  const fs=[...t.querySelectorAll('.missbl')].map(l=>parseFloat(getComputedStyle(l).fontSize));
  return {ovw:w.scrollWidth-w.clientWidth, ovc:Math.round(t.getBoundingClientRect().right-card.getBoundingClientRect().right), page:document.scrollingElement.scrollWidth-innerWidth,
    names:[...t.querySelectorAll('td.missn')].filter(multi).map(e=>e.innerText), groups:[...t.querySelectorAll('.missbn')].filter(e=>e.getBoundingClientRect().height>24).map(e=>e.innerText),
    minfs:Math.min(...fs), wrapped:[...t.querySelectorAll('.missbl')].filter(l=>{const k=l.children;return k.length&&k[k.length-1].offsetTop-k[0].offsetTop>2}).length}})()"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':800},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','loot')}",[ST]); pg.reload(); pg.wait_for_timeout(900)
    pg.wait_for_timeout(300); pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
    n=pg.evaluate("Math.ceil(missingItems(totalData()).length/RANK_PER)")
    mx=pg.evaluate("Math.max(...missingItems(totalData()).map(o=>missGroups(o.list).length))")
    check('(1) 데이터: 보스 6개 이상 묶인 긴 줄 존재', mx>=6, mx)
    for vw in [1920,1600,1366,1280,1100,1024,1000,820,390,320]:
        pg.set_viewport_size({'width':vw,'height':800}); pg.wait_for_timeout(300)
        for i in range(1,n+1):
            pg.evaluate(f"()=>{{rankPage.miss={i};render()}}"); pg.wait_for_timeout(120)
            m=pg.evaluate(MISS)
            check(f'(1) {vw}px {i}쪽: 가로 스크롤·잘림 없음, 이름/보스 묶음 한 줄, 글자>=10px', m['ovw']<=0 and m['ovc']<=1 and not m['names'] and not m['groups'] and m['minfs']>=10, m)
            if vw>=1600: check(f'(1) {vw}px {i}쪽: 줄바꿈 없음(전부 한 줄)', m['wrapped']==0, m)
        if vw in (1920,1280,1024,390): pg.locator('#missItems').screenshot(path=os.path.join(SHOT,f'oct12_after_miss_{vw}.png'))
    # (2) 낮은 창: 아래 카드가 잘리지 않고 스크롤로 전부 보임 (캐릭터 8명 = 사이드바가 긴 경우 포함)
    VIS="""(sel=>{const e=document.querySelector(sel);if(!e)return null;if(getComputedStyle(e).display==='none')return {hidden:true};
      e.scrollIntoView({block:'end'});const r=e.getBoundingClientRect(),hb=document.querySelector('header').getBoundingClientRect().bottom;
      return {top:Math.round(r.top),bot:Math.round(r.bottom),ih:innerHeight,hb:Math.round(hb),clip:e.scrollHeight>e.clientHeight+1,ok:r.bottom<=innerHeight+1&&(r.height>innerHeight-hb||r.top>=hb-1)}})"""
    def side(st,label):
        for vw,vh in [(1366,650),(1280,720),(1024,700),(1280,560)]:
            pg.set_viewport_size({'width':vw,'height':vh}); pg.goto(URL); pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",[st]); pg.reload(); pg.wait_for_timeout(1000)
            pg.wait_for_timeout(300); pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
            for t in ['boss','total','loot','guild']:
                pg.click(f'[data-tab={t}]'); pg.wait_for_timeout(400)
                sels=['#feedCard','#sunCard']+(['.rcol>.revpanel','.rcol>.pricecard','.rcol>.resetcard'] if t=='boss' else [])
                for sel in sels:
                    v=pg.evaluate(VIS,sel)
                    check(f'(2) {label} {vw}x{vh} {t} {sel}: 보임(숨김·잘림 없음)', v and not v.get('hidden') and v['ok'] and not v['clip'], v)
                pg.evaluate('scrollTo(0,0)')
            if label=='8명': pg.click('[data-tab=boss]'); pg.wait_for_timeout(300); pg.evaluate('scrollTo(0,1e6)'); pg.wait_for_timeout(150); pg.screenshot(path=os.path.join(SHOT,f'oct12_after_side_{vw}x{vh}_bottom.png'))
    one=json.loads(json.dumps(ST)); one['characters']=one['characters'][:1]
    side(ST,'8명'); side(one,'1명')
    # 큰 화면은 예전 그대로: 1명이면 사이드바 sticky, 소식+썬데이가 남은 높이를 채우고 페이지가 안 길어짐, 오른쪽 열 sticky
    for vw,vh in [(1920,1080),(1280,800)]:
        pg.set_viewport_size({'width':vw,'height':vh}); pg.goto(URL); pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",[one]); pg.reload(); pg.wait_for_timeout(1000)
        pg.wait_for_timeout(300); pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
        r=pg.evaluate("({flow:document.querySelector('.side-sticky').classList.contains('side-flow'),pos:getComputedStyle(document.querySelector('.rcol')).position,doc:document.scrollingElement.scrollHeight,ih:innerHeight,sun:getComputedStyle(document.querySelector('#sunCard')).display,sb:document.querySelector('#sunCard').getBoundingClientRect().bottom})")
        check(f'(2) {vw}x{vh}: 큰 화면 동작 그대로(sticky, 페이지 안 길어짐, 썬데이 화면 안)', not r['flow'] and r['pos']=='sticky' and r['doc']<=r['ih'] and r['sun']!='none' and r['sb']<=r['ih'], r)
    check('JS 오류 없음', not errs, errs)
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
