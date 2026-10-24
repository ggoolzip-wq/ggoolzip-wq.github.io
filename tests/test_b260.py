# test_b260: 에테르넬 장신망 상자(b_sjm) — 벨로나·림보·발드릭스·유피테르 장갑/신발/망토 상자 하나로, 기록 가능, 아이템 시세 = maple.ai.kr 에테르넬 장갑·신발·망토 평균(Worker maiMap)
# MBT_ROOT = 다른 빌드(변경 전 사진용, 검사 생략은 MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = 파일 이름 앞말(before/after)
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRCR=os.environ.get('MBT_ROOT') or ROOT
NOCHK=os.environ.get('MBT_NOCHECK')=='1'; SD=os.environ.get('MBT_SHOTDIR'); PFX=os.environ.get('MBT_SHOT','after')
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not NOCHK:
    from mai_node import mai_map, mai_unmatched, mai_keys
    it={'에테르넬 장갑':{'main':18.41},'에테르넬 신발':{'main':19.1},'에테르넬 망토':{'main':18.62},'에테르넬 모자':{'main':3.0}}
    m=mai_map(it,123); check('Worker maiMap: b_sjm = 장갑·신발·망토 평균(18.71억)', m.get('b_sjm')=={'p':1871000000,'t':123}, m)
    m2=mai_map({'에테르넬 장갑':{'main':18.41},'에테르넬 신발':{'main':19.1}},1); check('셋 중 하나라도 없으면 b_sjm 안 바꿈', 'b_sjm' not in m2, m2)
    m3=mai_map({'에테르넬 장갑':{'main':18.41},'에테르넬 신발':{'main':0},'에테르넬 망토':{'main':18.62}},1); check('0 값이면 b_sjm 안 바꿈', 'b_sjm' not in m3, m3)
    um=mai_unmatched(it); check('장갑·신발·망토 = 매칭됨(unmatched 에 없음)', '에테르넬 장갑' not in um and '에테르넬 모자' in um, um)
    check('MAI_KEYS 에 b_sjm(자동 갱신 missing 목록)', 'b_sjm' in mai_keys())
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(SRCR,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
BS={'limbo':'extreme','baldrix':'hard','bellona':'hard','jupiter':'hard'}
C={'id':'c0','name':'zetking','level':295,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{k:{'enabled':True,'diff':v,'party':1} for k,v in BS.items()},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
T=1761300000000
def shot(pg,sel,name):
    if not SD: return
    os.makedirs(SD,exist_ok=True); bx=pg.locator(sel).first.evaluate("e=>{const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}")
    x,y,w,h=bx; pg.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'),clip={'x':max(0,x-10),'y':max(0,y-10),'width':min(1600,w+20),'height':min(1400,h+20)})
def shot2(pg,sel,name):
    os.makedirs(SD,exist_ok=True); bx=pg.locator(sel).first.evaluate("e=>{const r=(e.closest('.boss,.bcard,.brow,tr,li')||e.parentElement.parentElement).getBoundingClientRect();return [r.x,r.y,r.width,r.height]}")
    x,y,w,h=bx; pg.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'),clip={'x':max(0,x-10),'y':max(0,y-10),'width':min(1600,w+20),'height':min(600,h+20)})
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("([s,t])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.itemPrices',JSON.stringify({b_sjm:{p:1871000000,t},whisper:{p:2500000000,t}}))}",[ST,T]); pg.reload(); pg.wait_for_timeout(1500)
    r=pg.evaluate("""()=>{const f=id=>BOSSES.find(b=>b.id===id), D2=(id,d)=>dropsFor(f(id),d);
      return {n:ITEMS.b_sjm&&ITEMS.b_sjm.n, lh:D2('limbo','hard'),le:D2('limbo','extreme'),ln:D2('limbo','normal'),bh:D2('baldrix','hard'),be:D2('baldrix','extreme'),
        eh:D2('bellona','hard'),en:D2('bellona','normal'),jh:D2('jupiter','hard'),jn:D2('jupiter','normal'),
        old:BOSSES.flatMap(b=>b.diffs.flatMap(d=>dropsFor(b,d))).filter(k=>['b_limbo','b_baldrix','b_bellona','b_jupiter'].includes(k)),
        rev:revItems().filter(k=>k==='b_sjm').length, ap:admPriceOf('b_sjm'), cnt:Object.values(ITEMS).filter(o=>o.n==='에테르넬 장신망 상자').length}}""")
    if not NOCHK:
        check('이름 = 에테르넬 장신망 상자 (항목 1개)', r['n']=='에테르넬 장신망 상자' and r['cnt']==1, r['n'])
        check('b261: 드롭표 = 보스별 원래 상자(림보 H·EX, 발드릭스 H·EX, 벨로나 H, 유피테르 H), b_sjm 은 드롭표에 없음', all(x in r[k] for k,x in [('lh','b_limbo'),('le','b_limbo'),('bh','b_baldrix'),('be','b_baldrix'),('eh','b_bellona'),('jh','b_jupiter')]) and not any('b_sjm' in r[k] for k in ['lh','le','bh','be','eh','jh']), r)
        check('노멀(림보·벨로나·유피테르) 엔 상자 없음', not any(x in r[k] for k in ['ln','en','jn'] for x in ['b_limbo','b_bellona','b_jupiter']))
        check('아이템 시세 목록에 1번', r['rev']==1, r['rev'])
        check('시세 자동 채움 값 = 공용 시세', r['ap'] and r['ap']['p']==1871000000, r['ap'])
        ch=pg.evaluate("()=>[...document.querySelectorAll('.drop[data-drop$=\"|b_limbo\"]')].map(x=>x.dataset.drop+' '+x.className+' '+x.innerText)")
        check('b261: 보스 카드에 욕망 상자 기록 칩(정보 칩 아님)', ch and not any('ibox' in c for c in ch), ch)
        ico=pg.evaluate("()=>{const d=document.createElement('div');d.innerHTML=itemIcon('b_sjm');const i=d.querySelector('img');return i?i.src.slice(0,22):d.innerHTML.slice(0,80)}")
        check('WZ 아이콘(2638066) 사용', ico.startswith('data:image'), ico)
    pg.evaluate("()=>{pcKind='item';repaintPrices();}"); pg.wait_for_timeout(300)
    pr=pg.evaluate("()=>{const r=document.querySelector('.pricecard .pc-row[data-pit=b_sjm]');return r?r.innerText:null}")
    if not NOCHK: check('아이템 가격 표: 에테르넬 장신망 상자 18.71억', pr and '장신망' in pr and '18억 7,100만' in pr.replace('\n',' ') or (pr and '18.71' in pr), pr)
    if SD:
        el=pg.locator('.pricecard').first; el.scroll_into_view_if_needed(); pg.evaluate("()=>{const r=document.querySelector('.pricecard .pc-row[data-pit=b_sjm]'), l=document.querySelector('.pricecard .pc-list'); if(r&&l) l.scrollTop=r.offsetTop-l.offsetTop-l.clientHeight/2;}"); pg.wait_for_timeout(200); shot(pg,'.pricecard','pricecard')
        lb=pg.locator('.drop[data-drop^="limbo|b_"]').first
        try: lb.scroll_into_view_if_needed(); pg.wait_for_timeout(200); shot2(pg,'.drop[data-drop^="limbo|b_"]','limbo_drops')
        except Exception as e: print('shot limbo skip',e)
    pg.evaluate("askRev(S.characters[0],findBoss('limbo'),'limbo|b_limbo','b_limbo',()=>{})"); pg.wait_for_timeout(300)
    v=pg.evaluate("()=>{const i=document.getElementById('rvAmt');return i?i.value:null}")
    if not NOCHK: check('기록 창 금액 자동 채움 = 18.71 억', v=='18.71', v)
    if SD and v is not None: shot(pg,'#revModal .modal','record')
    if not NOCHK: check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
    srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
print('FAILED:',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
