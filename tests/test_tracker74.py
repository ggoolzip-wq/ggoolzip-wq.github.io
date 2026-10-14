# b100 (zosu): 🔄 동기화 성공 → 아래 알림(toast) 없음, 버튼 옆 초록 '새로고침 완료!' / 실패는 계속 알림 / 자동 병합(merged) 알림 없음 (넥슨 API 는 가짜 응답)
import os, sys, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8873'
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
ST={'version':5,'theme':'dark','activeId':'c0','characters':[{'id':'c0','name':'테스트','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'a1','isMain':True,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}],
 'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'dummy','main':True}]}}
mode={'fail':False}
def route(r):
    if mode['fail']: r.fulfill(status=400,content_type='application/json',body='{"error":{"name":"OPENAPI00005","message":"bad"}}')
    else: r.fulfill(status=200,content_type='application/json',body='{"account_list":[]}')
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':900}); pg.route('**/open.api.nexon.com/**',route)
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(2000)
    pg.evaluate("toastHide()"); pg.evaluate("syncAll()"); pg.wait_for_timeout(300)
    check('성공: 아래 알림 없음', not pg.evaluate("document.querySelector('#toast').classList.contains('show')"))
    f=pg.evaluate("(()=>{const e=document.querySelector('#syncDone');return e&&{t:e.innerText,c:getComputedStyle(e).color,next:document.querySelector('#syncBtn').nextElementSibling===e}})()")
    check("성공: 버튼 옆 초록 '새로고침 완료!'", f and f['t'].startswith('새로고침 완료! ') and f['next'] and f['c']=='rgb(74, 222, 128)', f)
    pg.wait_for_timeout(3800); check('b108: 완료 글자는 계속 보임(시각 포함)', pg.evaluate("getComputedStyle(document.querySelector('#syncDone')).opacity")=='1')
    mode['fail']=True; pg.evaluate("toastHide()"); pg.evaluate("syncAll()"); pg.wait_for_timeout(300)
    t=pg.inner_text('#toast'); check('실패: 하단 알림 없음(b112)', not pg.evaluate("document.querySelector('#toast').classList.contains('show')"), t)
    src=open(os.path.join(ROOT,'src','app.js'),encoding='utf-8').read()
    check('자동 병합(merged) 알림 toast 없음', 'GD_RES_MSG.merged:' not in src and "toast('☁ '+GD_RES_MSG.pulled)" in src)
    b.close()
finally: srv.kill()
print('FAILS:',fails); sys.exit(1 if fails else 0)
