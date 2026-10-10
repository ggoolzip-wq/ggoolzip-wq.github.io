# 캐릭터 목록 페이지(8명씩) + 결정석 가격 마지막 확인 줄바꿈
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name,**kw):
    pth=os.path.join(OUT,name); loc.screenshot(path=pth,**kw); SHOTDIR and shutil.copy(pth,SHOTDIR)
PORT=8830
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
def C(i,w='스카니아'): return {'id':f'c{i}','name':f'캐릭{i:02d}','level':260+i,'job':'히어로','world':w,'ocid':f'o{i}','accId':'','isMain':i==1,'image':'','bosses':{'lotus':{'enabled':True,'diff':'hard','party':1}},'weekly':({'lotus':True} if i%2 else {}),'monthly':{},'auto':{},'drops':{},'sync':{}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(URL)
    chars=[C(i) for i in range(1,20)]+[C(i,'베라') for i in range(20,23)]
    ST={'version':5,'theme':'dark','activeId':'c1','characters':chars,'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[],'lastSync':int(time.time()*1000)}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(500)
    n=lambda: pg.locator('#charList .char[data-id]').count()
    btn=lambda: pg.eval_on_selector_all('#charPager .cpg',"e=>e.map(x=>[x.textContent,x.classList.contains('on')])")
    check('page 1: 8 chars, buttons 1 2 3, current bold orange', n()==8 and btn()==[['1',True],['2',False],['3',False]] and pg.evaluate("(e=>getComputedStyle(e).fontWeight>=700&&getComputedStyle(e).color===getComputedStyle(document.querySelector('.ord')||document.body).getPropertyValue('--accent')||getComputedStyle(e).color.startsWith('rgb(2'))(document.querySelector('.cpg.on'))") , (n(),btn()))
    check('no scroll on list', pg.evaluate("(e=>e.scrollHeight<=e.clientHeight+1&&!e.classList.contains('scroll'))(document.querySelector('#charList'))"))
    pg.locator('.side-sticky .card, #charList').first.screenshot(path='/workspace/shots/b37_pages.png')
    pos=lambda: pg.evaluate("(()=>{const b=document.querySelector('#charPager').getBoundingClientRect();const n=document.querySelector('#charPager').parentElement.nextElementSibling||document.querySelector('.side-sticky .card+.card');return [Math.round(b.top),n?Math.round(n.getBoundingClientRect().top):0]})()")
    p1=pos()
    pg.click('#charPager [data-cpage="3"]'); pg.wait_for_timeout(100)
    check('last page: pager + panels below do not move', pos()==p1, (p1,pos()))
    check('page 3: last 3 chars', n()==3 and btn()[2]==['3',True], n())
    pg.click('[data-csort="undone"]')
    pg.wait_for_timeout(100); check('sort change → page 1', btn() and btn()[0]==['1',True] and n()==8, btn())
    pg.click('#charPager [data-cpage="2"]'); pg.wait_for_timeout(100)
    pg.evaluate("S.characters=S.characters.filter(c=>!['c2','c4','c6','c8','c10','c12','c14','c16'].includes(c.id));save();render()"); pg.wait_for_timeout(150)
    check('count shrink → clamp (11 chars → 2 pages, stays 2)', btn()==[['1',False],['2',True]] and n()==3, (btn(),n()))
    pg.click('[data-wtab="베라"]'); pg.wait_for_timeout(150)
    check('world tab with 3 chars → buttons hidden', n()==3 and pg.evaluate("document.querySelector('#charPager').hidden"))
    pg.click('[data-wtab="스카니아"]'); pg.wait_for_timeout(150)
    check('world tab back → page 1', btn()[0]==['1',True])
    pf=pg.inner_text('.pc-foot')
    check('price foot: (마지막 확인 …) on its own line', '\n(마지막 확인' in pf, pf)
    pg.locator('.card:has(.pc-foot)').screenshot(path='/workspace/shots/b37_price.png')
    CEN="s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return [Math.round(r.left+r.width/2-innerWidth/2),Math.round(r.top+r.height/2-innerHeight/2),Math.round(r.width)]}"
    for (w,h) in [(1920,1080),(1280,800),(375,812)]:
        pg.set_viewport_size({'width':w,'height':h}); pg.wait_for_timeout(150)
        pg.evaluate("openChaos('lotus|chaosbox')"); pg.wait_for_timeout(100)
        c=pg.evaluate(CEN,'#chaosModal .cbbox')
        check(f'{w}x{h}: 칠흑 modal centered', c and abs(c[0])<=2 and abs(c[1])<=2 and c[2]<=w, c)
        if w==1920: pg.screenshot(path='/workspace/shots/b37_chaos_center.png')
        pg.click('#chaosModal .cbcancel'); pg.wait_for_timeout(80)
        pg.evaluate("celebrate(null,'eye')"); pg.wait_for_timeout(100)
        c=pg.evaluate(CEN,'#congrats .cg-in'); check(f'{w}x{h}: 축하드립니다 centered', c and abs(c[0])<=2 and abs(c[1])<=2, c)
        pg.evaluate("endCelebrate()")
        pg.evaluate("()=>{svAsk('변경사항을 저장하시겠습니까?',[['yes','예'],['no','아니오']]);}"); pg.wait_for_timeout(100)
        c=pg.evaluate(CEN,'.svaskbox'); check(f'{w}x{h}: save modal centered', c and abs(c[0])<=2 and abs(c[1])<=2, c)
        pg.click('.svaskbtns [data-k=no]'); pg.wait_for_timeout(80)
    pg.set_viewport_size({'width':1600,'height':1000})
    pg.click('[data-tab="guild"]'); pg.wait_for_timeout(150); pg.reload(); pg.wait_for_timeout(600)
    check('refresh restores last tab (길드 현황)', pg.locator('[data-tab="guild"].on').count()==1 and pg.evaluate("tab")=='guild' if False else pg.locator('[data-tab="guild"].on').count()==1 and '봉사활동' in pg.inner_text('#view'))
    pg.evaluate("localStorage.setItem('mapleBossTracker.tab','summary')"); pg.reload(); pg.wait_for_timeout(600)
    check('missing saved tab → 보스 현황', pg.locator('[data-tab="boss"].on').count()==1)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
