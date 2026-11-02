# test_b336 (t641): 분석 캘린더 — 이미 있는 기록(지난 주 기록·이번 주 처치 시각 wat·검마 mdate·지난 달) 채우기, 날짜 없는 건 목요일 ≈, 중복 없음, 키 지운 캐릭터 제외. MBT_SHOTDIR 에 calendar_backfill.png
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
    pg=b.new_page(viewport={'width':1600,'height':1150},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(300)
    day=lambda d: pg.evaluate("d=>{ const x=calDay(calRecs(calLoad()),d); return {m:x.m,ap:x.ap,it:x.it,ia:x.ia,by:x.by.map(b=>b.name)}; }",d)
    x=day('2026-10-30'); lv=pg.evaluate("charRevenue(S.characters[0]).wlist.find(x=>x.slot==='lucid').value")
    check('이번 주 처치 시각(wat) → 그날, 판매금·아이템 포함',x['m']==lv+31e8 and x['it'].get('eye')==1 and not x['ap'],x)
    x=day('2026-11-02'); check('윌 처치일 11/2 정확',x['it'].get('belt')==1 and not x['ap'],x)
    x=day('2026-11-01'); check('검마 mdate → 11/1',x['it'].get('genesis')==1 and x['m']>0 and not x['ap'],x)
    x=day('2026-10-29'); check('시각 없는 처치 → 그 주 목요일 ≈',x['it'].get('book')==1 and x['ap'] and x['ia'].get('book')==1 and x['by']==['부캐냥'],x)
    x=day('2026-10-22'); check('지난 주 기록 → 목요일 ≈ (판매금 포함)',x['m']==92e8 and x['ap'] and x['it'].get('sos')==1,x)
    x=day('2026-10-15'); check('지난 주 2 → 목요일 ≈',x['m']==11e8 and x['it'].get('terror')==1,x)
    x=day('2026-10-11'); check('지난 달 검마 mdates → 정확',x['m']==90e8 and not x['ap'] and x['it'].get('genesis')==1,x)
    x=day('2026-10-31'); check('키 지운 캐릭터 제외',x['m']==0 and not x['it'],x)
    tot=pg.locator('.calsum').inner_text()
    for i in range(3): pg.evaluate("()=>{ save(); render(); }")
    pg.evaluate("()=>{ const c=S.characters[0]; c.drops['will|book']=1; save(); render(); }"); pg.wait_for_timeout(200)
    x=day('2026-11-02'); check('새 기록 = 처치일에 1번만 (차이 기록과 중복 없음)',x['it'].get('book')==1 and x['it'].get('belt')==1,x)
    n=pg.evaluate("()=>calRecs(calLoad()).filter(r=>r.k==='book'&&r.id==='c0').length"); check('같은 기록 1개',n==1,n)
    pg.locator('[data-calmv="-1"]').click(); pg.wait_for_timeout(200)
    t=pg.locator('[data-calday="2026-10-22"]').inner_text(); check('칸에 ≈ 표시','≈' in t,t)
    pg.locator('[data-calday="2026-10-22"]').click(); pg.wait_for_timeout(200)
    check('상세에 ≈','≈' in pg.locator('#calDet').inner_text())
    pg.locator('#view').screenshot(path=os.path.join(OUT,'calendar_backfill.png'))
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
