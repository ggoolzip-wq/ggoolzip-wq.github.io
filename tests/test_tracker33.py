# b42: 일퀘 현황 — 10분 자동 갱신 삭제, 🔄 버튼, 페이지 열 때 1회(3초 규칙), 로그인 창 없음
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8833/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8833','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
SCH={'date':time.strftime('%Y-%m-%d'),'character_level':285,'daily_contents':[{'content_name':'[일일 퀘스트] 세르니움 조사','type':'quest','quest_state':'2','now_count':0,'max_count':0},{'content_name':'몬스터파크','now_count':3,'max_count':14}],'weekly_contents':[],'boss_contents':[]}
calls=[]
def api(r):
    u=r.request.url
    if '/scheduler/character-state' in u:
        calls.append(u); r.fulfill(status=200,content_type='application/json',body=json.dumps(SCH))
    else: r.fulfill(status=200,content_type='application/json',body='{}')
chars=[{'id':f'c{i}','name':f'캐릭{i}','level':285,'job':'히어로','world':'스카니아','ocid':f'o{i}','accId':'a1','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i in range(2)]
ST={'version':5,'theme':'dark','activeId':'c0','characters':chars,'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[{'id':'a1','name':'본계정','key':'test_key'}],'lastSync':0}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1600,'height':1000},locale='ko-KR'); pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pops=[]; pg.on('popup',lambda x:pops.append(x.url))
    pg.route('https://open.api.nexon.com/**',api)
    pg.goto(URL)
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','daily')}",ST)
    calls.clear(); pg.reload(); pg.wait_for_timeout(2500)
    check('page load → one refresh (scheduler per char)', len(calls)==2, len(calls))
    txt=pg.inner_text('.dqtop')
    check("no '10분마다 자동' text", '10분마다' not in pg.inner_text('body'), txt[:120])
    btn=pg.evaluate("(()=>{const b=document.querySelector('#dqSync'),s=document.querySelector('#syncBtn');return b&&{svg:b.innerHTML===s.innerHTML,cls:b.className.includes('ibtn sbtn'),w:b.getBoundingClientRect().width,w2:s.getBoundingClientRect().width}})()")
    check('refresh button: same icon/style as character sync', btn and btn['svg'] and btn['cls'] and abs(btn['w']-btn['w2'])<1, btn)
    n=len(calls); pg.reload(); pg.wait_for_timeout(1500)
    check('reload within 3s → skipped', len(calls)==n, len(calls)-n)
    n=len(calls); pg.evaluate("tabTick()"); pg.wait_for_timeout(500)
    check('no timer/tab auto refresh for daily', len(calls)==n, len(calls)-n)
    n=len(calls); pg.wait_for_timeout(3200); pg.click('#dqSync'); pg.wait_for_timeout(1500)
    check('button click → refresh all shown chars', len(calls)-n==2, len(calls)-n)
    pg.mouse.move(5,5); pg.locator('.dqtop').screenshot(path='/workspace/shots/b42_daily.png')
    check('no login popup', not pops, pops)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
