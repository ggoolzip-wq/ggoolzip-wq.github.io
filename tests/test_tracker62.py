# b84: 길드 현황 '지하 수로' 카드 — 제목·수로 보스 아이콘, + 캐릭터 추가(다중 선택)·✕ 제거, 동기화 설정 저장. (원래 b83: 득템 분석 '보스 득템왕' — 득템왕과 에픽빔왕 사이, 보스(난이도)별 득템 횟수 순위, 1위 보스 아이콘, 1~3위 지역 색, 한 줄·가로 스크롤 없음, 숨은 캐릭터 제외
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8884
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name,acc,main=False): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'isMain':main,'ocid':'o'+id,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c1','history':[],'monthHistory':[],'worldOrder':[],'characters':[ch('c1','본캐릭','a1',True),ch('c2','부캐둘','a1'),ch('c3','부캐셋','a1'),ch('c4','숨는캐','a2')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True},{'id':'a2','label':'부','key':''}]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("tab='guild'; render()"); pg.wait_for_timeout(400)
    h2=pg.inner_text('#suroCard h2')
    check("title '지하 수로' (no 본캐)", '지하 수로' in h2 and '본캐' not in h2, h2)
    check('title icon = 수로 boss image', pg.evaluate("!!document.querySelector('#suroCard h2 img.suroico[src^=\"data:image\"]')"))
    names=lambda: pg.evaluate("[...document.querySelectorAll('#suroCard .grow .nm')].map(e=>e.innerText.trim())")
    check('migrated from 본캐 star', names()==['본캐릭'], names())
    pg.screenshot(path='/workspace/maple-boss-tracker/oct12v_b84_test_guild_before_add.png')
    pg.click('#suroAdd'); pg.wait_for_timeout(200)
    cands=pg.evaluate("[...document.querySelectorAll('#suroCard .surocand b')].map(e=>e.innerText)")
    check('picker lists visible, not-yet-added chars only', cands==['부캐둘','부캐셋'], cands)
    pg.screenshot(path='/workspace/maple-boss-tracker/oct12v_b84_test_guild_picker.png')
    pg.check('#suroCard .surocand input[value=c2]'); pg.check('#suroCard .surocand input[value=c3]'); pg.click('#suroOk'); pg.wait_for_timeout(300)
    check('multi-add', names()==['본캐릭','부캐둘','부캐셋'], names())
    pg.click('[data-surodel=c1]'); pg.wait_for_timeout(300)
    check('remove', names()==['부캐둘','부캐셋'], names())
    saved=pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).settings.suroChars")
    check('persisted in settings.suroChars', saved==['c2','c3'], saved)
    check('scores column shown per row', pg.evaluate("document.querySelectorAll('#suroCard .grow-r').length")==2)
    pg.screenshot(path='/workspace/maple-boss-tracker/oct12v_b84_test_guild_after.png')
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
