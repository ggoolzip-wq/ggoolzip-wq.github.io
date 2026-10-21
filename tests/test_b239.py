# test_b239: 보스 드롭 칩 가격 등급 테두리·채움 (1000억 오로라 · 100억 금빛 · 30억 초록 · 10억 보라, 반지 상자 = 하늘색 + 결과(리4/컨4) 가격 등급 채움)
# MBT_SHOTDIR=폴더 → 칩 줄 사진 (dark·light × 미기록·기록) · MBT_ROOT=다른 빌드(변경 전 사진만, 검사 안 함)
import os, sys, subprocess, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK=not os.environ.get('MBT_ROOT'); SD=os.environ.get('MBT_SHOTDIR'); PFX='after' if CHECK else 'before'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
E=100000000; T=int(time.time()*1000)
PR={'chaosbox':1500*E,'h_ear':200*E,'g_faith':50*E,'se1':15*E,'ring_r4':150*E,'ring_c4':40*E}
def ch(id,name,got,out):
  return {'id':id,'name':name,'level':285,'job':'히어로','world':'스카니아','image':'','bosses':{'kaling':{'enabled':True,'diff':'extreme','party':1},'seren':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':got,'dropOut':out,'sync':{}}
KA=['chaosbox','h_ear','g_faith','se1','r_life']
ST={'version':5,'theme':'dark','activeId':'c1','history':[],'settings':{'accounts':[]},
    'characters':[ch('c1','미기록캐',{},{}),ch('c2','기록캐',{f'kaling|{k}':1 for k in KA},{'kaling|r_life':['r4']}),ch('c3','컨4캐',{'kaling|r_life':1},{'kaling|r_life':['c4']}),ch('c4','꽝캐',{'kaling|r_life':1},{'kaling|r_life':['x']})]}
cls=lambda pg,k: pg.evaluate(f"(document.querySelector(\"[data-drop='kaling|{k}']\")||{{}}).className||''").split()
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1100,'height':900},device_scale_factor=2,locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html')
    pg.evaluate("([s,pr,t])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.itemPrices',JSON.stringify(Object.fromEntries(Object.entries(pr).map(([k,v])=>[k,{p:v,t}]))));localStorage.setItem('mapleBossTracker.tab','boss')}",[ST,PR,T]); pg.reload(); pg.wait_for_timeout(1200)
    def show(cid,th='dark'):
        pg.evaluate(f"S.theme='{th}'; document.documentElement.dataset.theme='{th}'; S.activeId='{cid}'; render()"); pg.wait_for_timeout(400)
    def shot(name):
        if not SD: return
        el=pg.locator("[data-drop='kaling|chaosbox']").first.locator("xpath=ancestor::div[contains(concat(' ',@class,' '),' drops ')][1]")
        el.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'))
    for th in ['dark','light']:
        for cid,nm in [('c1','unrec'),('c2','rec')]: show(cid,th); shot(f'{th}_{nm}')
    if CHECK:
        show('c1')
        check('1000억 = 오로라(움직임)', {'tz','t-aur','tza'}<=set(cls(pg,'chaosbox')), cls(pg,'chaosbox'))
        check('100억 = 금빛(움직임)', {'tz','t-gold','tza'}<=set(cls(pg,'h_ear')), cls(pg,'h_ear'))
        check('30억 = 초록(정지)', {'tz','t-grn'}<=set(cls(pg,'g_faith')) and 'tza' not in cls(pg,'g_faith'), cls(pg,'g_faith'))
        check('10억 = 보라', {'tz','t-pur'}<=set(cls(pg,'se1')), cls(pg,'se1'))
        check('반지 상자 = 하늘색, 미기록 채움 없음', {'tz','t-sky'}<=set(cls(pg,'r_life')) and not any(c.startswith('f-') for c in cls(pg,'r_life')), cls(pg,'r_life'))
        check('미기록 = 채움 클래스 없음', not any(c.startswith('f-') for k in KA for c in cls(pg,k)))
        check('10억 미만·시세 없음 = 그대로', pg.evaluate("[...document.querySelectorAll('[data-drop^=\"seren|\"]')].filter(e=>!isRing(e.dataset.drop.split('|')[1])).every(e=>!e.classList.contains('tz')) && document.querySelectorAll('[data-drop^=\"seren|\"]').length>0"))
        bd=pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|chaosbox']\")).animationName")
        check('움직이는 테두리 animation', bd and bd!='none', bd)
        show('c2')
        check('기록 = 같은 등급 채움', 'f-aur' in cls(pg,'chaosbox') and 'f-gold' in cls(pg,'h_ear') and 'f-grn' in cls(pg,'g_faith') and 'f-pur' in cls(pg,'se1'), [cls(pg,k) for k in KA])
        check('반지 상자 리4(150억) 기록 → 금빛 채움·하늘색 테두리', {'t-sky','f-gold','tza'}<=set(cls(pg,'r_life')), cls(pg,'r_life'))
        bg=pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|h_ear']\")).backgroundImage")
        check('기록 금빛 = 그라데이션 채움', bg.count('gradient')>=2, bg[:200])
        show('c3'); check('반지 상자 컨4(40억) → 초록 채움', 'f-grn' in cls(pg,'r_life') and 'tza' not in cls(pg,'r_life'), cls(pg,'r_life'))
        show('c4'); check('반지 상자 꽝 → 하늘색만', 't-sky' in cls(pg,'r_life') and not any(c.startswith('f-') for c in cls(pg,'r_life')), cls(pg,'r_life'))
        show('c2','light'); check('라이트: 기록 채움 유지(그라데이션)', pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|chaosbox']\")).backgroundImage").count('gradient')>=2)
        pg.emulate_media(reduced_motion='reduce'); show('c2')
        check('prefers-reduced-motion = 움직임 없음', pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|chaosbox']\")).animationName")=='none')
        check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
