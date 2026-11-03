# test_b340 (t646): 캘린더 탭·화면만 Paperlogy(woff2, swap), 다른 탭·화면은 그대로. MBT_SHOTDIR 에 calendar_font.png
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
for d in ['data','ocr','fonts']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]}; const mk=(id,n,acc)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:acc,image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},mdate:{},auto:{},drops:{},sync:{}});
  const T=s=>Date.parse(s+'+09:00');
  S.settings.accounts=[{id:'a1',key:''}]; const c0=mk('c0','트딕이',''), c1=mk('c1','지운캐','a1'), c2=mk('c2','부캐냥',''); S.characters=[c0,c1,c2];
  c0.weekly={lucid:true,will:true}; c0.wat={lucid:T('2026-10-30T21:10:00'),will:T('2026-11-02T22:40:00')}; c0.drops={'lucid|eye':1,'will|belt':1}; c0.drev={'lucid|eye':{m:31e8,a:31,p:1,i:'eye'}};
  c0.monthly={blackmage:S.period.week}; c0.mdate={blackmage:'2026-11-01'}; c0.mdrops={'blackmage|genesis':1};
  c2.weekly={seren:true}; c2.drops={'seren|book':1};  /* wat 없음 → 목요일 ≈ */
  c1.weekly={lucid:true}; c1.wat={lucid:T('2026-10-31T12:00:00')}; c1.drops={'lucid|cfe':1};
  S.history=[{week:'2026-10-15',perChar:[{id:'c0',name:'트딕이',bosses:['루시드(하드)','윌(하드)'],bvals:[5e8,6e8],items:{'lucid|terror':1}}]},
             {week:'2026-10-22',perChar:[{id:'c0',name:'트딕이',bosses:['선택받은 세렌(하드)'],bvals:[12e8],items:{'seren|sos':1},revs:{'seren|sos':{m:80e8,a:80,p:1,i:'sos'}}},{id:'c1',name:'지운캐',bosses:['루시드(하드)'],bvals:[5e8],items:{}}]}];
  S.monthHistory=[{month:'2026-10',perChar:[{id:'c0',name:'트딕이',bosses:['검은 마법사(하드)'],bvals:[90e8],mdates:['2026-10-11'],mweeks:['2026-10-08'],items:{'blackmage|genesis':1}}]}];
  S.activeId='c0'; save(); render(); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1150},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.wait_for_timeout(200)
    ff=lambda sel: pg.evaluate("s=>{const e=document.querySelector(s);return e?getComputedStyle(e).fontFamily:''}",sel)
    check('다른 탭 글꼴 그대로','Paperlogy' not in ff('#tabs [data-tab=boss]'),ff('#tabs [data-tab=boss]'))
    check('캘린더 탭 = Paperlogy',ff('#tabs [data-tab=cal]').startswith('"Paperlogy"') or ff('#tabs [data-tab=cal]').startswith('Paperlogy'),ff('#tabs [data-tab=cal]'))
    check('보스 화면은 Paperlogy 아님','Paperlogy' not in ff('#view'),ff('#view'))
    pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(300)
    pg.locator('[data-calmv="-1"]').click(); pg.locator('button.calsum').click(); pg.wait_for_timeout(300)
    for s_ in ('.calti','.calc .calm','button.calsum','.calchip','.calmr .calmrb'): check('캘린더 '+s_+' = Paperlogy','Paperlogy' in ff(s_),ff(s_))
    pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    ld=pg.evaluate("async()=>{ await Promise.all([400,600,700].map(w=>document.fonts.load(w+' 16px Paperlogy','캘린더'))); return [...document.fonts].filter(f=>f.family.replace(/\"/g,'')==='Paperlogy').map(f=>f.status); }")
    check('woff2 3개 굵기 불러옴',ld==['loaded']*3,ld)
    fr=pg.evaluate("()=>performance.getEntriesByType('resource').filter(r=>/Paperlogy.*woff2/.test(r.name)).map(r=>r.name.split('/').pop())")
    check('fonts/*.woff2 받음',len(fr)>=2,fr)
    css=pg.evaluate("()=>[...document.styleSheets].flatMap(s=>{try{return [...s.cssRules]}catch(e){return []}}).filter(r=>r.cssText.includes('Paperlogy')&&r.cssText.startsWith('@font-face')).map(r=>r.style.getPropertyValue('font-display'))")
    check('font-display: swap',css and all(x=='swap' for x in css),css)
    pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(150); pg.screenshot(path=os.path.join(OUT,'calendar_font.png'),full_page=True)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
