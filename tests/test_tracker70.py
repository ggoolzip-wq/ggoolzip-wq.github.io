# b97: 보스 순위 동점 → 어려운 난이도 먼저 (익스트림 > 하드 = 카오스 > 노말 > 이지): 보스 득템왕 · 보스 별 누적 획득 아이템 · 보스 처치(bossKills)
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _legacy
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8895
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':'a1','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
def pc(items,bosses): return {'id':'c1','name':'c1','meso':1,'count':1,'bosses':bosses,'bvals':[1]*len(bosses),'items':{k:1 for k in items}}
# 같은 보스(대적자) 이지/노말/하드/익스트림 각각 1회 득템 + 카링 카오스… 대신 같은 횟수로 맞춤
H=[{'week':'2026-09-07','perChar':[pc(['adversary|g_faith'],['최초의 대적자(이지)'])]},
   {'week':'2026-09-14','perChar':[pc(['adversary|g_faith'],['최초의 대적자(노말)'])]},
   {'week':'2026-09-21','perChar':[pc(['adversary|g_faith'],['최초의 대적자(익스트림)'])]},
   {'week':'2026-09-28','perChar':[pc(['adversary|g_faith'],['최초의 대적자(하드)'])]}]
ST={'version':5,'theme':'dark','activeId':'c1','startWeek':'2026-09-07','history':H,'monthHistory':[],'worldOrder':[],'characters':[ch('c1','캐릭')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':_legacy.LEGACY_KEY,'main':True}]}}
SHOT=os.environ.get('SHOT'); BEFORE=bool(SHOT and 'before' in SHOT)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900},device_scale_factor=2); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("tab='loot'; render()"); pg.wait_for_timeout(300)
    if SHOT: pg.locator('#bossLootKing').screenshot(path=SHOT)
    if not BEFORE:
      rows=pg.evaluate("[...document.querySelectorAll('#bossLootKing tbody tr:not(.rkpad)')].map(r=>r.cells[1].innerText.trim())")
      want=['익스트림','하드','노말','이지']
      check('보스 득템왕: tie → 익스트림, 하드, 노말, 이지', [next((w for w in want if '('+w+')' in x),'') for x in rows]==want, rows)
      bl=pg.evaluate("[...document.querySelectorAll('.bossloot .blrow .blb')].map(e=>e.innerText.trim())")
      check('보스 별 누적 획득 아이템: same boss → 익스트림, 하드, 노말, 이지', [next((w for w in want if w in x),'') for x in bl]==want, bl)
      check('diffRank: hard == chaos, extreme first', pg.evaluate("[diffRank('extreme'),diffRank('하드'),diffRank('chaos'),diffRank('노말'),diffRank('easy'),diffRank('?')]")==[0,1,1,2,3,9])
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
