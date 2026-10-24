# test_b264: 에리온의 조각 개수 = 나무위키(아스트라 보조무기 2.1.2.2) — 카링 EX 480·벨로나 H 90 칩 추가, 림보/발드릭스 EX 는 '?' 라 없음.
# (b263 틀 재사용) 영롱한 달빛 포션(moon, WZ 2023136) = 익스트림 6보스(세렌·칼로스·대적자·카링·림보·발드릭스) 드롭표 기록 가능 칩. 이름 말풍선, 64px 아이콘, 가격순 정렬, 시세 없음 → 수동 입력.
# MBT_ROOT = 다른 빌드(변경 전 사진용, MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = before/after
import os, sys, tempfile, shutil, subprocess, base64, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRCR=os.environ.get('MBT_ROOT') or ROOT
NOCHK=os.environ.get('MBT_NOCHECK')=='1'; SD=os.environ.get('MBT_SHOTDIR'); PFX=os.environ.get('MBT_SHOT','after')
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(SRCR,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
BS={'kaling':'extreme','bellona':'hard'}
C={'id':'c0','name':'zetking','level':295,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{k:{'enabled':True,'diff':v,'party':1} for k,v in BS.items()},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
def clip(pg,sel,name,up=60):
    if not SD: return
    os.makedirs(SD,exist_ok=True); x,y,w,h=pg.locator(sel).first.evaluate("e=>{const r=(e.closest('.boss,.bcard,.brow')||e.parentElement.parentElement).getBoundingClientRect();return [r.x,r.y,r.width,r.height]}")
    pg.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'),clip={'x':max(0,x-10),'y':max(0,y-up),'width':min(1600,w+20),'height':min(700,h+up+20)})
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1500)
    sel='.drop.erion'
    def row(bid): return pg.evaluate("id=>{const r=[...document.querySelectorAll('.drop[data-drop^=\"'+id+'|\"]')][0]; const d=r&&r.parentElement.querySelector('.drop.erion'); return d?d.getAttribute('aria-label'):null}",bid)
    if SD:
        for bid in ['kaling','bellona']:
            s2=f'.drop[data-drop^="{bid}|"]'; pg.locator(s2).first.scroll_into_view_if_needed(); pg.mouse.move(5,5); pg.wait_for_timeout(200); clip(pg,s2,bid+'_drops',10)
    if NOCHK: b.close(); raise SystemExit
    M=pg.evaluate("()=>ERION")
    W={'seren':{'extreme':30},'kalos':{'extreme':180},'adversary':{'hard':30,'extreme':240},'kaling':{'hard':60,'extreme':480},'star':{'hard':90},'bellona':{'hard':90},'limbo':{'hard':60},'baldrix':{'hard':120},'jupiter':{'normal':45,'hard':360}}
    check('ERION = 나무위키 표', M==W, M)
    check('카링 익스 칩 480', row('kaling')=='에리온의 조각 480개', row('kaling'))
    check('벨로나 하드 칩 90', row('bellona')=='에리온의 조각 90개', row('bellona'))
    check('림보·발드릭스 익스 없음', pg.evaluate("[erionFor(findBoss('limbo'),'extreme'),erionFor(findBoss('baldrix'),'extreme')]")==[0,0])
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
