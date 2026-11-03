# test_b365 (t680): 캘린더 월 전체 머리 — 결정석(아이콘) 합계 / 아이템 N개 금액 / 합계 줄, API 키 지운 캐릭터 제외, 다크·라이트.
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
    pg=b.new_page(viewport={'width':1600,'height':1150},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(300)
    pg.locator('[data-calmv="-1"]').click(); pg.wait_for_timeout(200); pg.evaluate("calSel='M:'+calMon; renderCal()"); pg.wait_for_timeout(300)
    shot=os.environ.get('B365_SHOT','b365_month')
    pg.locator('#calDet .caldh').screenshot(path=os.path.join(OUT,shot+'.png'))
    if not os.environ.get('B365_SHOTONLY'):
      r=pg.evaluate("""()=>{ const ids=activeIds(), R=calRecs(calLoad()).filter(r=>r.day.startsWith(calMon)); const cm=R.filter(r=>!r.k).reduce((a,r)=>a+r.m,0), im=R.filter(r=>r.k).reduce((a,r)=>a+r.m,0), n=R.filter(r=>r.k).reduce((a,r)=>a+r.n,0);
        const q=s=>{const e=document.querySelector('#calDet .calmb .'+s); return e?e.textContent.replace(/[ ≈]/g,''):null;};
        return {exp:['결정석'+calEok(cm),'아이템'+n+'개'+calEok(im),'합계'+calEok(cm+im)], got:[q('calmb-c'),q('calmb-i'),q('calmb-t')], icon:!!document.querySelector('#calDet .calmb .calmb-c img,#calDet .calmb .calmb-c svg'), foreign:R.some(r=>!ids.has(r.id)), hasC1:S.characters.some(c=>c.id==='c1'&&!ids.has('c1'))}; }""")
      check('월 전체: 결정석·아이템 N개 금액·합계 3줄', r['exp']==r['got'], r)
      check('결정석 줄 아이콘', r['icon'], r)
      check('API 키 지운 캐릭터 제외', not r['foreign'] and r['hasC1'], r)
      pg.evaluate("document.documentElement.dataset.theme='light'"); pg.wait_for_timeout(200)
      col=pg.evaluate("getComputedStyle(document.querySelector('#calDet .calmb-t b')).color")
      check('라이트 테마 색 적용', col not in ('rgb(255, 215, 122)',), col)
      pg.locator('#calDet .caldh').screenshot(path=os.path.join(OUT,shot+'_light.png'))
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
