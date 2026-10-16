# b135: 주 평균 글씨(누적 수익·판매·총 득템) + 주간 메소 그래프 = 이번 주만(목 0시 0부터)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8961'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b183')}_{TAG}_{name}.png"))
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
    H={'week':prev,'total':400000000,'cleared':1,'perChar':[{'id':'c1','name':'캐릭A','meso':400000000,'count':1,'bosses':['루시드(하드)'],'bvals':[400000000],'items':{'lucid|eye':1,'lucid|r_black':3,'lucid|r_white':1},'outcomes':{'lucid|r_black':['r4','x','x'],'lucid|r_white':['c4']},'revs':{}}]}
    C={'id':'c1','name':'캐릭A','level':280,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{'lucid':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[H],'monthHistory':[],'characters':[C],'startWeek':prev,'period':pg.evaluate("({...S.period})"),'settings':{}}
    def go(t):
        pg.evaluate("([s,t])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab',t)}",[ST,t]); pg.reload(); pg.wait_for_timeout(1000)
        pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()"); pg.wait_for_timeout(500)
    go('boss')
    r=pg.evaluate("(()=>{const e=[...document.querySelectorAll('.rp-line .tsmn')];return [e.length,document.querySelectorAll('.rp-line .tir.tsm').length,e[0]?getComputedStyle(e[0]).fontFamily:'',getComputedStyle(document.body).fontFamily]})()")
    check('3 이번 주 수익 작은 문구 = 기본 글씨체(디지털 아님)', r[0]>=2 and r[1]==0 and r[2]==r[3], r)
    f=pg.evaluate("(()=>{const q=s=>{const e=document.querySelector(s);return e?getComputedStyle(e).fontFamily:null};return [q('.pc-foot'),q('.pc-date'),getComputedStyle(document.body).fontFamily]})()")
    check('4 결정석 가격 밑 문구 = 기본 글씨체', f[0]==f[2] and f[1] in (None,f[2]), f)
    if pg.locator('.rp-total').count(): shot(pg.locator('.card:has(.rp-total)').last,'week_card')
    if pg.locator('.pricecard').count(): shot(pg.locator('.pricecard').first,'cry_price')
    if pg.locator('[data-pckind=item]').count():
        pg.locator('[data-pckind=item]').first.click(); pg.wait_for_timeout(300)
        f=pg.evaluate("(()=>{const e=document.querySelector('.pc-foot,.pc-date');return [e?getComputedStyle(e).fontFamily:null,getComputedStyle(document.body).fontFamily]})()")
        check('4 아이템 가격 밑 문구 = 기본 글씨체', f[0] in (None,f[1]), f); shot(pg.locator('.pricecard').first,'item_price')
    go('loot')
    t=pg.evaluate("(()=>{const c=[...document.querySelectorAll('#lootTop .ltcap')];return [c.length,c.map(e=>parseFloat(getComputedStyle(e).fontSize)),c.every(e=>e.scrollWidth<=e.clientWidth+1),document.querySelector('#ltTotal').innerText.replace(/\\s+/g,' ')]})()")
    check('2 총 득템·반상·블빵 밑 글씨 커짐(≥13px), 안 잘림', t[0]>=2 and min(t[1])>=13 and t[2], t)
    check('b182 총 득템 = 반지 상자 제외 (눈1 + 리4 1 + 컨4 1 = 3개)', t[3].startswith('총 득템 3개'), t[3])
    m=pg.evaluate("(()=>{const n=[...document.querySelectorAll('#missItems .missn')].map(e=>parseFloat(getComputedStyle(e).fontSize));const bl=[...document.querySelectorAll('#missItems .missbl')].map(e=>parseFloat(getComputedStyle(e).fontSize));const h=document.querySelector('#missItems .misstbl')?.getBoundingClientRect().height;return [n,bl,h,[...document.querySelectorAll('#missItems .missn')].every(e=>e.scrollWidth<=e.clientWidth+1)]})()")
    check('1 못 가진 아이템 표: 아이템 이름 15px·보스 이름 최대 15px(전 13px), 안 잘림', m[0] and min(m[0])>=15 and max(m[1])>=15 and m[3], m)
    shot(pg.locator('#lootTop'),'loot_top'); shot(pg.locator('#missItems'),'missing')
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
