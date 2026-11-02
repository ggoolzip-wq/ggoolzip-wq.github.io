# test_b334 (t639): '분석 캘린더' 탭 — 득템 분석 오른쪽, 오늘 칸에 늘어난 수익·아이템, +N개 더, 달 이동, 날짜 상세, 키 지운 캐릭터 제외. MBT_SHOTDIR 에 calendar.png / calendar_detail.png
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; const mk=(id,n,acc)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:acc,image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.settings.accounts=[{id:'a1',key:''}]; S.characters=[mk('c0','트딕이',''),mk('c1','지운캐','a1')]; S.activeId='c0'; save(); render(); }"""
ADD="""()=>{ const c=S.characters[0], h=S.characters[1]; c.drops={'lucid|eye':1,'will|belt':1,'seren|book':1,'kalos|terror':2}; c.drev={'lucid|eye':{m:12e8,a:12,p:1,i:'eye'}};
  h.drops={'lucid|cfe':1}; h.drev={'lucid|cfe':{m:99e8,a:99,p:1,i:'cfe'}}; save(); render(); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1100},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    tabs=pg.evaluate("()=>[...document.querySelectorAll('#tabs button')].map(b=>b.dataset.tab)")
    check('분석 캘린더 탭 = 득템 분석 바로 오른쪽',tabs[tabs.index('loot')+1]=='cal' and pg.locator('#tabs [data-tab=cal]').inner_text()=='분석 캘린더',tabs)
    pg.evaluate(SETUP); pg.wait_for_timeout(200)
    pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(300)
    today=pg.evaluate("dayId(Date.now())")
    check('처음엔 기준만 (빈 달력)',pg.locator('.calc.has').count()==0)
    check('오늘 강조',pg.locator(f'.calc.today[data-calday="{today}"]').count()==1)
    pg.evaluate(ADD); pg.wait_for_timeout(300)
    cell=pg.locator(f'.calc[data-calday="{today}"]'); t=cell.inner_text()
    check('실시간: 오늘 칸에 수익(판매 12억)',('12억' in t),t)
    check('아이템 2개 + "+N개 더"',cell.locator('.calit').count()==2 and '+2개 더' in t,t)
    check('키 지운 캐릭터 제외(99억·커포 없음)','99' not in pg.locator('.calsum').inner_text() and 'cfe' not in pg.evaluate("JSON.stringify(calDay(calRecs(calLoad()),dayId(Date.now())).it)"),pg.locator('.calsum').inner_text())
    check('헤더 이번 달 합계',('12억' in pg.locator('.calsum').inner_text()) and '5개' in pg.locator('.calsum').inner_text(),pg.locator('.calsum').inner_text())
    f1=pg.evaluate("getComputedStyle(document.querySelector('#charList')).fontFamily"); f2=pg.evaluate("getComputedStyle(document.querySelector('.calwrap')).fontFamily")
    check('글꼴 = 캐릭터 목록과 같음',f1==f2,(f1,f2))
    pg.locator('#view').screenshot(path=os.path.join(OUT,'calendar.png'))
    cell.click(); pg.wait_for_timeout(300); d=pg.locator('#calDet').inner_text()
    check('날짜 클릭 → 상세(아이템 목록·합계)',('12억' in d) and pg.locator('#calDet .caldi').count()==4 and 'x2' in d and '트딕이' in d and '지운캐' not in d,d)
    pg.locator('#view').screenshot(path=os.path.join(OUT,'calendar_detail.png'))
    pg.evaluate("()=>{ const c=S.characters[0]; c.drops['kalos|terror']=1; save(); render(); }"); pg.wait_for_timeout(200)
    check('기록 줄이면 오늘에서도 줄어듦',pg.evaluate("calDay(calRecs(calLoad()),dayId(Date.now())).it.terror")==1)
    m0=pg.locator('.calti').inner_text(); pg.locator('[data-calmv="1"]').click(); pg.wait_for_timeout(150); m1=pg.locator('.calti').inner_text()
    pg.locator('[data-calmv="-1"]').click(); pg.locator('[data-calmv="-1"]').click(); pg.wait_for_timeout(150); m2=pg.locator('.calti').inner_text()
    check('달 이동',m0!=m1 and m1!=m2 and m0!=m2 and pg.locator('.calc.has').count()==0,(m0,m1,m2))
    pg.locator('[data-calmv="0"]').click(); pg.wait_for_timeout(150); check('오늘 버튼',pg.locator('.calti').inner_text()==m0)
    pg.evaluate("toggleTheme()"); pg.evaluate("render()"); pg.wait_for_timeout(200)
    bg=pg.evaluate("getComputedStyle(document.querySelector('.calc:not(.emp)')).backgroundImage")
    check('라이트 테마 따라감','255, 255, 255' in bg,bg)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
