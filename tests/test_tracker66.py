import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8886=_tutil.free_port()
# b90: b89 취소 — 보스 득템왕 1~3위 굵기가 b89 이전 값인지 확인 (b83 데이터 재사용)
# was b83: 득템 분석 '보스 득템왕' — 득템왕과 에픽빔왕 사이, 보스(난이도)별 득템 횟수 순위, 1위 보스 아이콘, 1~3위 지역 색, 한 줄·가로 스크롤 없음, 숨은 캐릭터 제외
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8886
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}

def ch(id,name,acc): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
def pc(id,items,bosses): return {'id':id,'name':id,'meso':1,'count':1,'bosses':bosses,'bvals':[1]*len(bosses),'items':{k:1 for k in items}}
P1=pc('c1',['lucid|eye','lucid|belt','lucid|book','kalos|g_faith','jupiter|g_life','zakum|r_black'],['루시드(하드)','감시자 칼로스(카오스)','유피테르(하드)','자쿰(카오스)'])
P2=pc('c1',['blackmage|genesis','blackmage|mitra','jupiter|g_faith','jupiter|lcm'],['검은 마법사(익스트림)','유피테르(하드)'])
P3=pc('c2',['zakum|eye','zakum|belt','zakum|book','zakum|terror','zakum|sos'],['자쿰(카오스)'])
H=[{'week':'2026-09-28','perChar':[P1,P3]}]; M=[{'month':'2026-09','perChar':[P2]}]
ST={'version':5,'theme':'dark','activeId':'c1','startWeek':'2026-09-28','history':H,'monthHistory':M,'worldOrder':[],'characters':[ch('c1','보이는캐','a1'),ch('c2','숨는캐','a2')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True},{'id':'a2','label':'부','key':''}]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900},device_scale_factor=2); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("tab='loot'; render()"); pg.wait_for_timeout(300)
    W=pg.evaluate("[...document.querySelectorAll('#bossLootKing tbody tr:not(.rkpad)')].map(r=>{const e=r.querySelector('.bdn'),g=r.querySelector('[class*=rg-]'),d=r.querySelector('.bdn ~ .dlv, .dlv'),cs=getComputedStyle(e),ds=d?getComputedStyle(d):{};return [e.innerText,g?g.className:'',cs.fontWeight,cs.webkitTextStrokeWidth,d?d.innerText:'',ds.fontWeight,ds.webkitTextStrokeWidth]})")
    print('WEIGHTS',W)
    if os.environ.get('SHOT'): pg.locator('#bossLootKing').screenshot(path=os.environ['SHOT'])
    top=[x for x in W if x[1]]; rest=[x for x in W if not x[1]]
    exp=[['유피테르','spk rg-gr2','700','0px','(하드)','800','0px'],['루시드','spk rg-arc','700','0px','(하드)','800','0px'],['검은 마법사','spk rg-bm','700','0.5px','(익스트림)','900','0px']]
    check('b90: top3 weights/outlines back to pre-b89', sorted(top)==sorted(exp), top)
    check('rank 4+ unchanged', all(x[2]=='400' and x[5]=='800' and x[6]=='0px' for x in rest), rest)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
