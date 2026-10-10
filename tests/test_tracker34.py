# 최고 전투력 칸 (동기화 서버 /api/cp 값) — 헥사 환산·hexa.json 없음
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8834/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8834','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
at=int(time.mktime(time.strptime('2026-10-10 18:07','%Y-%m-%d %H:%M'))*1000)
CP={'o0':{'name':'림강혼망','value':433060423,'combo':{'equip':2,'hyper':3,'ability':1,'link':1},'apiCP':226966178,'at':at}}
chars=[{'id':f'c{i}','name':n,'level':285,'job':'렌','world':'스카니아','ocid':f'o{i}','accId':'','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i,n in enumerate(['림강혼망','부캐'])]
ST={'version':5,'theme':'dark','activeId':'c0','characters':chars,'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    hx=[]; pg.route('**/hexa.json*',lambda r:(hx.append(1),r.abort()))
    pg.goto(URL)
    pg.evaluate("([s,cp])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.cp',JSON.stringify(cp))}",[ST,CP]); pg.reload(); pg.wait_for_timeout(900)
    t=pg.inner_text('.cpstat')
    check('최고 전투력: 억/만 value + combo + date', '최고 전투력' in t and '4억 3,306만' in t and '장비 2 · 하이퍼 3 · 어빌 1 · 링크 1' in t and '2026-10-10 18:07 갱신' in t, t)
    v=pg.inner_text('#view'); check("no '헥사 환산' / '전체 캐릭터 주간 합계'", '헥사 환산' not in v and '전체 캐릭터 주간 합계' not in v)
    pg.locator('.stats').first.screenshot(path='/workspace/shots/b43_cp.png')
    pg.click('.char[data-id="c1"]'); pg.wait_for_timeout(200)
    t=pg.inner_text('.cpstat'); check('no data → —', '—' in t and '갱신' not in t, t)
    g=pg.evaluate("(()=>{const r=document.querySelector('.char[data-id=c1]'),R=r.getBoundingClientRect(),a=r.querySelector('.avatar').getBoundingClientRect(),e=r.querySelector('[data-edit]').getBoundingClientRect();return [a.left-R.left,R.right-e.right]})()")
    check('char row: portrait…edit group centered (left gap = right gap)', abs(g[0]-g[1])<=1.5, g)
    check('hexa.json not requested', not hx)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
