# test_b371 (t686): 파티 보스 모달 — 보스명·난이도 겹침/글자별 줄바꿈 없음, 긴 클리어 라벨은 다음 줄로 전부 표시, 공통 보스 없는 캐릭터 비활성.
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SD=os.environ.get('B371_SHOTDIR') or OUT
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}});
  const N=['트덕이','zetking','린벨자','랑트킹','테레사아','부캐냥이'], cs=N.map((n,i)=>{const c=mk('c'+i,n); c.bosses={lotus:{enabled:true,party:2,diff:'extreme'},star:{enabled:true,party:2,diff:'normal'}}; return c;});
  const c6=mk('c6','루시드만'); c6.bosses={lucid:{enabled:true,party:2,diff:'hard'}};
  const c7=mk('c7','섞임'); c7.bosses={lucid:{enabled:true,party:2,diff:'hard'},lotus:{enabled:true,party:2,diff:'extreme'},blackmage:{enabled:true,party:2,diff:'hard'}};
  S.characters=[...cs,c6,c7];
  S.history=[{week:'2026-10-15',perChar:N.map((n,i)=>({id:'c'+i,name:n,bosses:['스우(익스트림)','찬란한 흉성(노말)'],bvals:[1e8]}))}];
  S.activeId='c0'; save(); render(); }"""
GEO="""()=>[...document.querySelectorAll('#calBossModal .calbi')].map(e=>{const r=e.getBoundingClientRect(),n=e.querySelector('.calbin').getBoundingClientRect(),d=e.querySelector('.dbadge').getBoundingClientRect(),l=e.querySelector('.calbclr');const lr=l&&l.getBoundingClientRect();
  return {s:e.dataset.calbs,nh:n.height,nr:n.right,dl:d.left,lab:l?l.textContent:'',lh:lr?lr.height:0,lin:lr?(lr.right<=r.right+0.5&&lr.left>=r.left-0.5&&l.scrollWidth<=l.clientWidth+1):true,below:lr?lr.top>=n.bottom-1:false}})"""
DIS="[...document.querySelectorAll('#calBossModal .calbc')].map(e=>e.dataset.calbc+(e.disabled?'X':''))"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1000,'height':900},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(200)
    pg.evaluate("calBM={day:'2026-10-21',cids:['c0']}; calBossRender()"); pg.wait_for_timeout(100)
    g=pg.evaluate(GEO); check('1명: 라벨 한 줄, 이름 한 줄', all(x['nh']<30 and x['lh']<24 and x['lin'] for x in g), g)
    pg.evaluate("calBM={day:'2026-10-21',cids:['c0','c1','c2','c3','c4','c5']}; calBossRender()"); pg.wait_for_timeout(150)
    g=pg.evaluate(GEO)
    check('여러 명: 보스명 한 줄(글자별 줄바꿈 없음)', all(x['nh']<30 for x in g), g)
    check('여러 명: 난이도 배지가 이름과 안 겹침', all(x['nr']<=x['dl']+0.5 for x in g), g)
    check('여러 명: 긴 라벨 전체 표시(잘림 없음) + 닉네임 전부', all(x['lin'] and x['lab'].endswith('(트덕이, zetking, 린벨자, 랑트킹, 테레사아, 부캐냥이)') for x in g), g)
    check('여러 명: 라벨은 이름 아래 다음 줄로', all(x['below'] for x in g), g)
    pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'after_many.png'))
    SR="""(a)=>{ calBM={day:a[0],cids:a[1]}; calBossRender(); return Object.fromEntries([...document.querySelectorAll('#calBossModal .calbi')].map(e=>[e.dataset.calbs,(e.disabled?'X':'O')+(e.querySelector('.calbclr')?e.querySelector('.calbclr').textContent:'')])); }"""
    pg.evaluate("""()=>{ S.calNotes={'2026-10-16':{m:{},b:{s1:{cids:['c7'],ns:['섞임'],slot:'lucid',boss:'lucid',d:'normal',p:2,h:21,mi:30,at:1},s2:{cids:['c0','c7'],ns:['트덕이','섞임'],slot:'lotus',boss:'lotus',d:'extreme',p:2,h:9,mi:5,at:2}}},
      '2026-10-02':{m:{},b:{s3:{cid:'c7',n:'섞임',slot:'blackmage',boss:'blackmage',d:'hard',p:2,h:22,mi:0,at:3}}}}; save(); }""")
    r=pg.evaluate(SR,['2026-10-21',['c7']])
    check('같은 보스 주에 일정 있음(난이도 달라도) → 비활성 + 누가·언제', r.get('lucid')=='X·이번 주 일정 등록됨 (섞임, 10/16 21:30)' and r.get('lotus','').startswith('X·이번 주 일정 등록됨 (섞임, 10/16 09:05)'), r)
    check('검은 마법사: 같은 달 일정 → 비활성', r.get('blackmage')=='X·이번 달 일정 등록됨 (섞임, 10/02 22:00)', r)
    r=pg.evaluate(SR,['2026-10-22',['c7']]); check('다음 보스 주(목) → 다시 활성', r.get('lucid')=='O' and r.get('lotus')=='O' and r.get('blackmage','').startswith('X'), r)
    r=pg.evaluate(SR,['2026-11-02',['c7']]); check('다음 달 → 검은 마법사 활성', r.get('blackmage')=='O', r)
    r=pg.evaluate(SR,['2026-10-21',['c0','c7']]); check('클리어가 일정보다 우선', r.get('lotus')=='X·이번 주 클리어 완료 (트덕이)', r)
    pg.evaluate(SR,['2026-10-21',['c7']]); pg.wait_for_timeout(100)
    pg.locator('#calBossModal .modal').screenshot(path=os.path.join(os.environ.get('B371_SHOTDIR2') or SD,'scheduled_disabled.png'))
    pg.evaluate("()=>{ delete S.calNotes['2026-10-16'].b.s1; save(); }")
    r=pg.evaluate(SR,['2026-10-21',['c7']]); check('일정 삭제 → 다시 활성', r.get('lucid')=='O', r)
    pg.evaluate("()=>{ S.calNotes={}; save(); }")
    pg.evaluate("calBM={day:dayId(Date.now()),cids:[]}; calBossRender()")
    check('선택 없음: 전부 활성', pg.evaluate(DIS)==['c0','c1','c2','c3','c4','c5','c6','c7'], pg.evaluate(DIS))
    pg.click('[data-calbc="c0"]'); d=pg.evaluate(DIS)
    check('c0 선택 → 공통 보스 없는 루시드만 비활성', d==['c0','c1','c2','c3','c4','c5','c6X','c7'], d)
    pg.click('[data-calbc="c6"]',force=True); check('비활성 클릭 안 됨', pg.evaluate("calBM.cids")==['c0'])
    pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'disabled_chars.png'))
    pg.click('[data-calbc="c7"]'); d=pg.evaluate(DIS)
    check('c0+c7(공통 스우) → 루시드만 여전히 비활성', d==['c0','c1','c2','c3','c4','c5','c6X','c7'], d)
    pg.click('[data-calbc="c0"]'); d=pg.evaluate(DIS)
    check('c0 해제(c7만) → 루시드만 다시 활성', d==['c0','c1','c2','c3','c4','c5','c6','c7'], d)
    pg.click('[data-calbc="c7"]'); pg.click('[data-calbc="c6"]'); d=pg.evaluate(DIS)
    check('루시드만 선택 → 스우·흉성만 가진 캐릭터 비활성', d==['c0X','c1X','c2X','c3X','c4X','c5X','c6','c7'], d)
    st=pg.evaluate("(()=>{const e=document.querySelector('[data-calbc=c0]');return [e.classList.contains('neonBtn'),getComputedStyle(e).cursor,e.getAttribute('aria-disabled')]})()")
    check('비활성 캐릭터 = 네온 회색, not-allowed', st==[True,'not-allowed','true'], st)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
