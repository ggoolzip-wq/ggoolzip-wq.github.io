# test_b338 (t643): '이번 달 합계' 버튼 → 아래 상세 칸에 이 달 전체(아이템·합계·캐릭터별 + 날짜별 묶음), 다시 누르면 닫힘, 날짜 누르면 그 날로. MBT_SHOTDIR 에 month_list.png
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
    pg.locator('[data-calmv="-1"]').click(); pg.wait_for_timeout(200)
    bt=pg.locator('button.calsum'); check('이번 달 합계 = 버튼',bt.count()==1)
    sumt=bt.inner_text(); bt.click(); pg.wait_for_timeout(200)
    d=pg.locator('#calDet'); t=d.inner_text()
    check('같은 상세 칸에 10월 전체',d.count()==1 and '10월 전체' in t,t[:80])
    x=pg.evaluate("()=>calDay(calRecs(calLoad()),d=>d.startsWith('2026-10'))")
    import re
    check('달 합계 = 버튼 합계',('%s'%pg.evaluate("m=>calEok(m)",x['m'])) in t and pg.evaluate("m=>calEok(m)",x['m']) in sumt,(x['m'],sumt))
    check('아이템 목록·캐릭터별',d.locator('.caldi').count()>=4 and d.locator('.caldcr').count()>=2)
    ch=d.locator('.calchip'); chips=[ch.nth(i).inner_text() for i in range(ch.count())]
    check('기록 있는 날짜 칩만, 날짜 순',[c.split()[0] for c in chips]==['10/11','10/15','10/22','10/29','10/30'],chips)
    check('기본 = 최근 날짜 선택',d.locator('.calchip.on').inner_text().startswith('10/30') and d.locator('.calml').count()==1)
    check('목록은 한 날짜만',d.locator('.calmgh').count()==1)
    d.locator('[data-calmd="2026-10-22"]').click(); pg.wait_for_timeout(200); d=pg.locator('#calDet')
    check('칩 누르면 그 날 목록',d.locator('.calchip.on').inner_text().startswith('10/22') and '10월 22일' in d.locator('.calml').inner_text())
    r22=d.locator('.calml').inner_text(); check('항목에 보스·캐릭터·금액·≈',all(k in r22 for k in ('고통의 근원','선택받은 세렌','트딕이','≈')),r22)
    xs=pg.evaluate("()=>[...document.querySelectorAll('.calml .calmr')].map(r=>[...r.children].map(c=>Math.round(c.getBoundingClientRect().left)))")
    check('열 왼쪽 위치 모든 줄 같음',all(x==xs[0] for x in xs),xs)
    ali=pg.evaluate("()=>[...document.querySelector('.calml .calmr:not(.calmrh)').children].map(c=>getComputedStyle(c).textAlign)")
    check('금액만 오른쪽 정렬',ali[1:5]==['left']*4 and ali[5]=='right',ali)
    pg.locator('[data-calmd="2026-10-15"]').click(); pg.wait_for_timeout(150)
    xs2=pg.evaluate("()=>[...document.querySelectorAll('.calml .calmr')].map(r=>[...r.children].map(c=>Math.round(c.getBoundingClientRect().left)))")
    check('다른 날짜도 같은 열',xs2[0]==xs[0],(xs2[0],xs[0]))
    pg.locator('[data-calmd="2026-10-22"]').click(); pg.wait_for_timeout(150)
    check('키 지운 캐릭터 없음','지운캐' not in t)
    pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(150); pg.screenshot(path=os.path.join(os.environ.get('MBT_SHOT2') or OUT,'month_v2.png' if os.environ.get('MBT_SHOT2') else 'month_list.png'),full_page=True)
    pg.locator('[data-calday="2026-10-15"]').click(); pg.wait_for_timeout(200)
    check('날짜 누르면 그 날로',pg.locator('#calDet b').first.inner_text()=='10월 15일' and not pg.locator('.calml:not(.calml-day)').count())
    pg.locator('button.calsum').click(); pg.wait_for_timeout(150); pg.locator('button.calsum').click(); pg.wait_for_timeout(150)
    check('다시 누르면 닫힘',pg.locator('#calDet').count()==0)
    pg.locator('button.calsum').click(); pg.locator('[data-calmd="2026-10-11"]').click(); pg.wait_for_timeout(150); pg.locator('#calDet .calmgh').first.click(); pg.wait_for_timeout(150)
    check('묶음 날짜 누르면 그 날',pg.locator('#calDet b').first.inner_text()=='10월 11일')
    pg.evaluate("()=>document.documentElement.setAttribute('data-theme','light')"); pg.wait_for_timeout(150)
    check('라이트에서 노랑 테두리',pg.evaluate("()=>getComputedStyle(document.querySelector('button.calsum')).borderTopColor")=='rgb(224, 168, 0)')
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
