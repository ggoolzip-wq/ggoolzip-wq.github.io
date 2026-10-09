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
    pg.click('#charPager [data-cpage="3"]'); pg.wait_for_timeout(100)
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
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
