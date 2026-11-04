# test_b368 (t682): 상시 규칙 네온 버튼 .neonBtn — b367 캘린더 버튼 전부 네온(테두리 글로·hover 떠오름·상시 애니메이션 없음), 라이트 가독성.
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
SD=os.environ.get('B367_SHOTDIR') or OUT
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}});
  const c0=mk('c0','트딕이'), c1=mk('c1','부캐냥'); S.characters=[c0,c1];
  c0.bosses={lucid:{enabled:true,party:2,diff:'hard'},will:{enabled:true,party:1,diff:'hard'},seren:{enabled:true,party:3,diff:'hard'},dusk:{enabled:false,party:2,diff:'chaos'}};
  c1.bosses={will:{enabled:true,party:1,diff:'normal'}}; S.activeId='c0'; save(); render(); }"""
SD=os.environ.get('B368_SHOTDIR') or OUT
NEON="""(sel)=>[...document.querySelectorAll(sel)].map(e=>{ const c=getComputedStyle(e); return {neon:e.classList.contains('neonBtn'), sh:c.boxShadow, an:c.animationName, bc:c.borderColor, col:c.color, bg:c.backgroundColor}; })"""
def allneon(pg,sel,name):
    r=pg.evaluate(NEON,sel); ok=bool(r) and all(x['neon'] and 'rgba' in x['sh'] and x['an']=='none' for x in r)
    check(name+' 네온(글로·상시 애니메이션 없음)', ok, r[:2])
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':1100},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(300)
    day=pg.evaluate("dayId(Date.now())"); pg.locator(f'[data-calday="{day}"]').click(); pg.wait_for_timeout(200)
    pg.click('[data-calmemo]'); pg.fill('.calmt','메모'); pg.click('[data-calmsave]'); pg.click('[data-calmemo]')
    c=pg.evaluate(NEON,'#calDet .calnbt'); check('+메모 초록 / +보스 선홍', c[0]['col']=='rgb(62, 224, 138)' and c[1]['col']=='rgb(255, 59, 107)', c)
    allneon(pg,'#calDet .calnbt,#calDet [data-calmsave],#calDet [data-calmcancel],#calDet .calndel','상세 버튼')
    t0=pg.evaluate("getComputedStyle(document.querySelector('[data-calboss]')).transform"); pg.hover('[data-calboss]'); pg.wait_for_timeout(300)
    h=pg.evaluate("(()=>{const c=getComputedStyle(document.querySelector('[data-calboss]')); return [c.transform,c.boxShadow]})()")
    check('hover = 살짝 떠오름 + 글로 강해짐', t0=='none' and h[0]!='none' and '28px' in h[1], h)
    pg.locator('#calDet').screenshot(path=os.path.join(SD,'detail_buttons_after.png'))
    pg.click('[data-calmcancel]'); pg.click('[data-calboss]'); pg.click('[data-calbc="c0"]'); pg.wait_for_timeout(100)
    allneon(pg,'#calBossModal .calbc,#calBossModal .calbi,#calBossModal .calbcls','모달 캐릭터·보스·닫기')
    pg.click('[data-calbs="lucid"]'); pg.wait_for_timeout(100)
    allneon(pg,'#calBossModal [data-calbsave],#calBossModal .calbab [data-calbx]','모달 저장/취소')
    pg.mouse.move(5,5); pg.wait_for_timeout(250); pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'modal_after.png'))
    pg.click('[data-calbsave]'); pg.click('#calBossModal .calbcls'); pg.wait_for_timeout(100)
    pg.evaluate("document.documentElement.dataset.theme='light'"); pg.wait_for_timeout(200)
    r=pg.evaluate(NEON,'#calDet .calnbt')
    def lum(s):
        import re; v=[float(x) for x in re.findall(r'[\d.]+',s.replace('srgb',''))[:3]]; v=[x*255 for x in v] if 'srgb' in s else v; return 0.2126*v[0]+0.7152*v[1]+0.0722*v[2]
    check('라이트: 글자 어둡게(가독성)', all(lum(x['col'])<140 for x in r), r)
    pg.locator('#calDet').screenshot(path=os.path.join(SD,'light_after.png'))
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
