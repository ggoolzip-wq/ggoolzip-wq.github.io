# b179: 수익 기록 창 가운데 정렬 + 오른쪽 위 라이트/다크 전환 (localStorage mapleBossTracker.theme, 기본 다크)
import os,sys,subprocess,time,urllib.request,socket
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); fails=[]
def check(n,c,d=''): print(('PASS ' if c else 'FAIL ')+n,'' if c else d); c or fails.append(n)
s=socket.socket(); s.bind(('127.0.0.1',0)); PORT=s.getsockname()[1]; s.close()
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
  try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
  except Exception: time.sleep(.1)
ch={'id':'c1','name':'용사','level':280,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'activeId':'c1','history':[],'monthHistory':[],'worldOrder':[],'characters':[ch],'settings':{'accounts':[]}}
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
  pg=b.new_page(viewport={'width':1280,'height':900})
  pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
  pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
  check('default dark',pg.evaluate("document.documentElement.dataset.theme")=='dark')
  pg.evaluate("askRev(activeChar(),findBoss('lucid'),'lucid|x','pitched_box',null)"); pg.wait_for_timeout(200)
  c=pg.evaluate("""(()=>{const m=document.querySelector('#revModal .modal').getBoundingClientRect(),mc=m.left+m.width/2;
    const cx=s=>{const r=document.querySelector(s).getBoundingClientRect();return Math.abs(r.left+r.width/2-mc)};
    return [cx('.rvbox .rvguide'),cx('.rvbox .rvrow1'),cx('.rvbox .rvrow2'),cx('.rvbox .rvin')]})()""")
  check('popup contents centered',all(v<12 for v in c),c)
  lay=pg.evaluate("""(()=>{const r=s=>document.querySelector('#revModal '+s).getBoundingClientRect();const o=r('.rvok'),n=r('.rvno'),c=r('.rvcancel');return [Math.abs(o.top-n.top),o.left<n.left,c.top>o.bottom-2]})()""")
  check('b181 row1 [기록하기][기록 없이 저장], row2 [취소]',lay[0]<4 and lay[1] and lay[2],lay)
  pg.set_viewport_size({'width':390,'height':800}); pg.wait_for_timeout(150)
  lay=pg.evaluate("""(()=>{const r=s=>document.querySelector('#revModal '+s).getBoundingClientRect();const o=r('.rvok'),n=r('.rvno');return Math.abs(o.top-n.top)})()""")
  check('b181 390 row1 stays one line',lay<4,lay); pg.set_viewport_size({'width':1280,'height':900}); pg.wait_for_timeout(150)
  tb=pg.evaluate("(()=>{const m=document.querySelector('#revModal .modal').getBoundingClientRect(),t=document.querySelector('#revModal .thbtn').getBoundingClientRect();return [m.right-t.right,t.top-m.top]})()")
  check('theme button top-right',tb[0]<20 and tb[1]<20,tb)
  pg.click('#revModal .thbtn'); pg.wait_for_timeout(150)
  check('click → light + saved, popup stays',pg.evaluate("[document.documentElement.dataset.theme,localStorage.getItem('mapleBossTracker.theme'),!!document.querySelector('#revModal')]")==['light','light',True])
  bg=pg.evaluate("getComputedStyle(document.querySelector('#revModal .modal')).backgroundColor")
  check('light popup bg white',bg=='rgb(255, 255, 255)',bg)
  pg.reload(); pg.wait_for_timeout(600)
  check('light persists after reload',pg.evaluate("document.documentElement.dataset.theme")=='light')
  pg.evaluate("askRev(activeChar(),findBoss('lucid'),'lucid|x','pitched_box',null)"); pg.wait_for_timeout(200); pg.click('#revModal .thbtn'); pg.wait_for_timeout(150)
  check('toggle back → dark',pg.evaluate("[document.documentElement.dataset.theme,localStorage.getItem('mapleBossTracker.theme')]")==['dark','dark'])
  b.close()
finally: srv.terminate()
print('FAILS',len(fails)); sys.exit(1 if fails else 0)
