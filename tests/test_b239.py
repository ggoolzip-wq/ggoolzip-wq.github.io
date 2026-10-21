# test_b239 (+b240: 금빛 반짝·체크 표시 등급 색·채움 더 밝게·실제로 움직임): 보스 드롭 칩 가격 등급 테두리·채움 (1000억 오로라 · 100억 금빛 · 30억 초록 · 10억 보라, 반지 상자 = 하늘색 + 결과(리4/컨4) 가격 등급 채움)
# MBT_SHOTDIR=폴더 → 칩 줄 사진 (dark·light × 미기록·기록) · MBT_ROOT=다른 빌드(변경 전 사진만, 검사 안 함)
import os, sys, subprocess, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK=not os.environ.get('MBT_ROOT'); SD=os.environ.get('MBT_SHOTDIR'); PFX='after' if CHECK else 'before'; LUNREC=os.environ.get('MBT_LIGHT_UNREC','1')!='0'
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
    'characters':[ch('c1','미기록캐',{},{}),ch('c2','기록캐',{f'kaling|{k}':1 for k in KA},{'kaling|r_life':['r4']}),ch('c3','컨4캐',{'kaling|r_life':1},{'kaling|r_life':['c4']}),ch('c5','싼리4캐',{'kaling|r_life':1},{'kaling|r_life':['r4']}),ch('c4','꽝캐',{'kaling|r_life':1},{'kaling|r_life':['x']})]}
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
        sr=pg.locator("[data-drop^='seren|']").first.locator("xpath=ancestor::div[contains(concat(' ',@class,' '),' drops ')][1]")
        if sr.count(): sr.screenshot(path=os.path.join(SD,f'{PFX}_{name}_under10.png'))
    pg.evaluate("(()=>{const ch=S.characters.find(c=>c.id==='c2'); const e=[...document.querySelectorAll('[data-drop^=\"seren|\"]')]; S.activeId='c2'; render(); [...document.querySelectorAll('[data-drop^=\"seren|\"]')].slice(0,2).forEach(x=>{ if(!isRing(x.dataset.drop.split('|')[1])) ch.drops[x.dataset.drop]=1; }); save(); render();})()")
    for th in ['dark','light']:
        for cid,nm in [('c1','unrec'),('c2','rec')]:
            if th=='light' and nm=='unrec' and not LUNREC: continue
            show(cid,th); shot(f'{th}_{nm}')
    if CHECK:
        show('c1')
        check('1000억 = 오로라(움직임)', {'tz','t-aur','tza'}<=set(cls(pg,'chaosbox')), cls(pg,'chaosbox'))
        check('100억 = 금빛(움직임)', {'tz','t-gold','tza'}<=set(cls(pg,'h_ear')), cls(pg,'h_ear'))
        check('b240: 50억 = 보라(초록 없음)', {'tz','t-pur'}<=set(cls(pg,'g_faith')) and 'tza' not in cls(pg,'g_faith') and 't-grn' not in cls(pg,'g_faith'), cls(pg,'g_faith'))
        check('10억 = 보라', {'tz','t-pur'}<=set(cls(pg,'se1')), cls(pg,'se1'))
        check('반지 상자 = 하늘색, 미기록 채움 없음', {'tz','t-sky'}<=set(cls(pg,'r_life')) and not any(c.startswith('f-') for c in cls(pg,'r_life')), cls(pg,'r_life'))
        check('미기록 = 채움 클래스 없음', not any(c.startswith('f-') for k in KA for c in cls(pg,k)))
        check('b240: 10억 미만·시세 없음 = 하늘색', pg.evaluate("[...document.querySelectorAll('[data-drop^=\"seren|\"]')].every(e=>e.classList.contains('t-sky')) && document.querySelectorAll('[data-drop^=\"seren|\"]').length>0"))
        bd=pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|chaosbox']\")).animationName")
        check('움직이는 테두리 animation', bd and bd!='none', bd)
        show('c2')
        check('기록 = 같은 등급 채움', 'f-aur' in cls(pg,'chaosbox') and 'f-gold' in cls(pg,'h_ear') and 'f-pur' in cls(pg,'g_faith') and 'f-pur' in cls(pg,'se1'), [cls(pg,k) for k in KA])
        check('반지 상자 리4(150억) 기록 → 금빛 채움·하늘색 테두리', {'t-sky','f-gold','tza'}<=set(cls(pg,'r_life')), cls(pg,'r_life'))
        bg=pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|h_ear']\")).backgroundImage")
        check('기록 금빛 = 그라데이션 채움', bg.count('gradient')>=2, bg[:200])
        pos=lambda k: pg.evaluate(f"getComputedStyle(document.querySelector(\"[data-drop='kaling|{k}']\")).backgroundPosition")
        for th in ['dark','light']:
            show('c2',th); p1={k:pos(k) for k in ['chaosbox','h_ear','g_faith']}; pg.wait_for_timeout(900); p2={k:pos(k) for k in ['chaosbox','h_ear','g_faith']}
            check(f'b240 {th}: 기록 칩 반짝임이 실제로 움직임(배경 위치 바뀜)', all(p1[k]!=p2[k] for k in p1), (p1,p2))
        show('c2')
        ck=lambda k: pg.evaluate(f"getComputedStyle(document.querySelector(\"[data-drop='kaling|{k}']\"),'::after').backgroundImage")
        cks={k:ck(k) for k in KA}
        check('b240: 체크 표시 = 등급 색 (오로라·금·보라·반지(금 채움) 각자)', '9b5cff' in cks['se1'] and '9b5cff' in cks['g_faith'] and 'fff3b0' in cks['h_ear'] and 'b061ff' in cks['chaosbox'] and 'fff3b0' in cks['r_life'], {k:v[60:140] for k,v in cks.items()})
        check('b240: 오로라 체크 = 움직임', pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|chaosbox']\"),'::after').animationName")!='none')
        check('b240: 10억 미만 기록 = 하늘색 채움·체크', pg.evaluate("(()=>{const l=[...document.querySelectorAll('[data-drop^=\"seren|\"].got')].filter(f=>!isRing(f.dataset.drop.split('|')[1])); return l.length>0&&l.every(f=>f.classList.contains('f-sky')&&getComputedStyle(f,'::after').backgroundImage.includes('39b6f5'));})()"))
        check('b240: 초록 등급 없음', pg.evaluate("document.querySelectorAll('.t-grn,.f-grn').length")==0)
        show('c3'); check('반지 상자 컨4(40억) → 보라 채움', 'f-pur' in cls(pg,'r_life') and 'tza' not in cls(pg,'r_life'), cls(pg,'r_life'))
        pg.evaluate("(()=>{const P=JSON.parse(localStorage.getItem('mapleBossTracker.itemPrices')); P.ring_r4.p=5e8; localStorage.setItem('mapleBossTracker.itemPrices',JSON.stringify(P));})()")
        show('c5'); check('b240: 반지 상자 결과 10억 미만 → 하늘색 채움', {'t-sky','f-sky'}<=set(cls(pg,'r_life')), cls(pg,'r_life'))
        pg.evaluate("(()=>{const P=JSON.parse(localStorage.getItem('mapleBossTracker.itemPrices')); P.ring_r4.p=150e8; localStorage.setItem('mapleBossTracker.itemPrices',JSON.stringify(P));})()")
        show('c4'); check('반지 상자 꽝 → 하늘색만', 't-sky' in cls(pg,'r_life') and not any(c.startswith('f-') for c in cls(pg,'r_life')), cls(pg,'r_life'))
        check('b240: 반지 상자 채움 없음 → 하늘색 체크', '39b6f5' in pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|r_life']\"),'::after').backgroundImage"))
        show('c2','light'); check('라이트: 기록 채움 유지(그라데이션)', pg.evaluate("getComputedStyle(document.querySelector(\"[data-drop='kaling|chaosbox']\")).backgroundImage").count('gradient')>=2)
        pg.emulate_media(reduced_motion='reduce'); show('c2')
        check('prefers-reduced-motion = 움직임 없음(칩·체크·초록 반짝)', pg.evaluate("['chaosbox','g_faith'].every(k=>getComputedStyle(document.querySelector(`[data-drop='kaling|${k}']`)).animationName==='none')&&getComputedStyle(document.querySelector(\"[data-drop='kaling|chaosbox']\"),'::after').animationName==='none'"))
        check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
