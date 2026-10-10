# 헥사 환산 칸 (hexa.json) — '전체 캐릭터 주간 합계' 대신
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8834/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8834','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
HX={'characters':{'림강혼망':{'value':123456,'updatedAt':'2026-10-10T18:07:00+09:00'}}}
chars=[{'id':f'c{i}','name':n,'level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i,n in enumerate(['림강혼망','부캐'])]
ST={'version':5,'theme':'dark','activeId':'c0','characters':chars,'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    scout=[]; pg.route('**/*maplescouter*/**',lambda r:(scout.append(r.request.url),r.abort()))
    pg.route('**/hexa.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(HX,ensure_ascii=False)))
    pg.goto(URL)
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(900)
    t=pg.inner_text('.hexastat')
    check('헥사 환산 value + small date', '헥사 환산' in t and '123,456' in t and '2026-10-10 18:07 갱신' in t, t)
    check("'전체 캐릭터 주간 합계' removed", '전체 캐릭터 주간 합계' not in pg.inner_text('#view'))
    pg.locator('.stats').first.screenshot(path='/workspace/shots/b42_hexa.png')
    pg.click('.char[data-id="c1"]'); pg.wait_for_timeout(200)
    t=pg.inner_text('.hexastat'); check('no data → —', '—' in t and '갱신' not in t, t)
    check('no maplescouter requests', not scout, scout)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
