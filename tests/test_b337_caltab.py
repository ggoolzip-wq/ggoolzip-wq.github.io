# test_b337 (t642): 탭 이름 '캘린더', 노랑 네온 박스(다크·라이트), 다른 탭 색 그대로. MBT_SHOTDIR 에 tabs.png
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); PORT=s.getsockname()[1]; s.close()
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(.6)
fails=[];errs=[]
def check(n,ok,d=''):
  print(('PASS ' if ok else 'FAIL ')+n+(' — '+str(d) if d!='' else '')); ok or fails.append(n)
C="""t=>{const s=getComputedStyle(document.querySelector('#tabs [data-tab='+t+']'));return [s.getPropertyValue('--nb1').trim(),s.boxShadow]}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':900},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
    check('탭 이름 = 캘린더',pg.locator('#tabs [data-tab=cal]').inner_text()=='캘린더')
    check('분석 캘린더 문구 없음','분석 캘린더' not in pg.locator('body').inner_text())
    for th,y in (('dark','#ffd23c'),('light','#e0a800')):
      pg.evaluate("t=>document.documentElement.setAttribute('data-theme',t)",th); pg.wait_for_timeout(150)
      c=pg.evaluate(C,'cal'); a=pg.evaluate(C,'auto'); l=pg.evaluate(C,'loot')
      check(th+': 캘린더 노랑',c[0]==y,c); check(th+': 자동 기록 빨강 그대로',a[0] in('#ff4d5e','#e0203a'),a); check(th+': 다른 탭은 노랑 아님',l[0]!=y,l)
    pg.evaluate("()=>document.documentElement.setAttribute('data-theme','dark')"); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(300)
    pg.locator('#tabs').screenshot(path=os.path.join(OUT,'tabs.png'))
    pg.evaluate("()=>document.documentElement.setAttribute('data-theme','light')"); pg.wait_for_timeout(200)
    pg.locator('#tabs').screenshot(path=os.path.join(OUT,'tabs_light.png'))
    b.close()
finally: srv.terminate()
check('페이지 오류 없음',not errs,errs)
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
