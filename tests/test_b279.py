# test_b279: 아이템 판매 누적 수익 — 10줄씩 쪽 나눔, 소식 카드와 같은 .fpg 번호 버튼, 10줄 이하면 버튼 없음, 데이터가 줄면 쪽 clamp
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SD=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
PUT="""N=>{ const ks=Object.keys(ITEMS).filter(k=>{try{return !!lootName(k)}catch(e){return false}}); const sales={};
  for(let i=0;i<N;i++){ const k=ks[i%ks.length], p=1+Math.floor(i/ks.length); sales[k+'#'+p]={i:k,p,n:1,m:(100-i)*1e8}; }
  let c=document.querySelector('#salesCard'); if(!c){ c=document.createElement('div'); c.id='salesCard'; document.body.prepend(c); }
  const t=document.createElement('div'); t.innerHTML=salesHtml(Object.assign({},totalData(),{sales})); c.replaceWith(t.firstElementChild); document.querySelector('#salesCard').scrollIntoView(); }"""
ST="""()=>{ const c=document.querySelector('#salesCard'), r=[...c.querySelectorAll('.sl')]; return {rows:r.length, vis:r.filter(x=>x.offsetParent).length, firstVis:r.findIndex(x=>x.offsetParent), btns:[...c.querySelectorAll('.slpager .fpg')].map(b=>b.textContent+(b.classList.contains('on')?'*':'')), pg:SL_PAGE}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate(PUT,10); s=pg.evaluate(ST); check('10줄: 쪽 버튼 없음, 10줄 다 보임', s['rows']==10 and s['vis']==10 and not s['btns'], s)
    pg.evaluate(PUT,23); s=pg.evaluate(ST); check('23줄: 1쪽 10줄 + 버튼 1*,2,3', s['vis']==10 and s['firstVis']==0 and s['btns']==['1*','2','3'], s)
    if SD: os.makedirs(SD,exist_ok=True); pg.wait_for_timeout(1500); pg.locator('#salesCard').screenshot(path=os.path.join(SD,'sales_page1.png'))
    pg.click('#salesCard .slpager [data-slpage="3"]'); s=pg.evaluate(ST); check('3쪽: 21~23 (3줄)', s['vis']==3 and s['firstVis']==20 and s['btns']==['1','2','3*'], s)
    if SD: pg.wait_for_timeout(1500); pg.locator('#salesCard').screenshot(path=os.path.join(SD,'sales_page3.png'))
    st=pg.evaluate("[getComputedStyle(document.querySelector('.slpager .fpg')).fontSize, document.querySelector('.slpager').className]"); check('소식 카드 버튼과 같은 모양(.fpager/.fpg)', 'fpager' in st[1], st)
    pg.evaluate(PUT,15); s=pg.evaluate(ST); check('15줄로 줄면 3쪽→2쪽 clamp (5줄)', s['pg']==2 and s['vis']==5 and s['btns']==['1','2*'], s)
    pg.evaluate(PUT,4); s=pg.evaluate(ST); check('4줄: 버튼 없음·1쪽', s['pg']==1 and s['vis']==4 and not s['btns'], s)
    b.close()
finally: srv.terminate()
check('JS 오류 없음', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
