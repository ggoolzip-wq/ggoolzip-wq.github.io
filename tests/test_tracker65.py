# b87: API 키 없음(보이는 캐릭터 0) → 모든 탭이 보스 현황과 같은 빈 화면. (원래 b83: 득템 분석 '보스 득템왕' — 득템왕과 에픽빔왕 사이, 보스(난이도)별 득템 횟수 순위, 1위 보스 아이콘, 1~3위 지역 색, 한 줄·가로 스크롤 없음, 숨은 캐릭터 제외
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8883
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name,acc): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
CASES={'empty':{'version':5,'characters':[],'history':[],'monthHistory':[],'settings':{'accounts':[]}},
       'keyless':{'version':5,'activeId':'c1','characters':[ch('c1','숨는캐','a1')],'history':[],'monthHistory':[],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'','main':True}],'guilds':[{'world':'스카니아','name':'X'}]}}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for nm,ST in CASES.items():
        pg=b.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
        tabs=pg.evaluate("TABS")
        for t in tabs:
            pg.evaluate(f"tab='{t}'; render()"); pg.wait_for_timeout(250)
            ok=pg.evaluate("(()=>{const v=document.querySelector('#view'); return v.children.length===1 && !!v.querySelector('.card.empty .big') && v.innerText.includes('캐릭터를 추가해 보세요') && !!v.querySelector('#importAccBtn')})()")
            check(f'{nm}/{t}: empty-state prompt only', ok, pg.inner_text('#view')[:120])
            if nm=='keyless' and t=='guild': pg.screenshot(path='/workspace/maple-boss-tracker/oct12y_b87_test_guild_empty.png')
            if nm=='empty' and t=='loot': pg.screenshot(path='/workspace/maple-boss-tracker/oct12y_b87_test_loot_empty.png')
        pg.click('#importAccBtn'); pg.wait_for_timeout(300)
        check(f'{nm}: button opens import modal', pg.evaluate("document.querySelector('#importModal').classList.contains('show')"))
        pg.close()
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
