# b96 (test 71): 캐릭터 정보(보스 현황 왼쪽 카드) — '프리미엄 PC방' 훈장 착용 캐릭터는 주간/월간 보스 칸 위에 경고 줄(훈장 아이콘 + 왼쪽 위 빨간 ! 삼각형). 다른 캐릭터는 없음
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _legacy
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8896
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name,medal=None): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':'a1','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{},**({'medal':medal} if medal else {})}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[ch('c1','훈장캐',{'bad':True,'where':['프리셋 2'],'at':1}),ch('c2','정상캐',{'bad':False,'where':[],'at':1})],
    'settings':{'accounts':[{'id':'a1','label':'본계정','key':_legacy.LEGACY_KEY}]}}
SHOT=os.environ.get('SHOT'); BEFORE=bool(SHOT and 'before' in SHOT)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':1000},device_scale_factor=2); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("tab='boss'; render()"); pg.wait_for_timeout(200)
    card=pg.locator('.bosslay .grid>.card').first
    if SHOT: card.screenshot(path=SHOT)
    if not BEFORE:
      w=pg.locator('#view .medalrow')
      check('warning row shown for medal character', w.count()==1 and pg.inner_text('#view .medalrow .mdtxt').strip()=='프리미엄 PC방 훈장을 착용한 캐릭터 입니다.', w.inner_text() if w.count() else '')
      check('icon = medal image + red ! triangle at top-left', pg.evaluate("(()=>{const i=document.querySelector('.medalrow .mdico img'), t=document.querySelector('.medalrow .mdico .mdtri'); if(!i||!t) return false; const a=i.getBoundingClientRect(), b=t.getBoundingClientRect(); return i.src.startsWith('data:image') && b.left<=a.left+4 && b.top<=a.top+4 && t.textContent.includes('!')})()"))
      check('row is above 주간 보스 처치 stats', pg.evaluate("(()=>{const r=document.querySelector('.medalrow'), s=document.querySelector('#view .stats.s3'); return !!(r&&s) && (r.compareDocumentPosition(s)&Node.DOCUMENT_POSITION_FOLLOWING) && r.getBoundingClientRect().bottom<=s.getBoundingClientRect().top+1})()"))
      check('slightly larger text', pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.medalrow .mdtxt')).fontSize) > parseFloat(getComputedStyle(document.body).fontSize)"))
      pg.click('.char[data-id="c2"]'); pg.wait_for_timeout(300)
      check('not shown for other characters', pg.locator('#view .medalrow').count()==0)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
