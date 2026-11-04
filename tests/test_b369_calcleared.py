# test_b369 (t683): 보스 일정 모달 — 대상 날짜의 보스 주(목~수)·달에 이미 클리어한 보스 회색·비활성 + 이번 주/달 클리어 완료.
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
SD=os.environ.get('B369_SHOTDIR') or OUT
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}});
  const c0=mk('c0','트딕이'); S.characters=[c0];
  c0.bosses={lotus:{enabled:true,party:2,diff:'extreme'},star:{enabled:true,party:2,diff:'normal'},blackmage:{enabled:true,party:3,diff:'hard'}};
  S.history=(S.history||[]).filter(h=>h.week!=='2026-10-15'); S.history.push({week:'2026-10-15',perChar:[{id:'c0',name:'트딕이',bosses:['찬란한 흉성(노말)'],bvals:[1e8]}]});
  S.activeId='c0'; save(); render(); }"""
ROWS="""(day)=>{ calBM={day,cid:'c0'}; calBossRender(); return Object.fromEntries([...document.querySelectorAll('#calBossModal .calbi')].map(e=>[e.dataset.calbs,(e.disabled?'X':'O')+(e.querySelector('.calbcl')?e.querySelector('.calbcl').textContent:'')])); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':1000},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(200)
    # 지난 주 기록: 2026-10-16(금) 흉성 노말 클리어 → 다음 수요일 10-21 = 흉성만 비활성, 다음 목요일 10-22 = 둘 다 가능
    r=pg.evaluate(ROWS,'2026-10-21'); check('금 클리어 → 그 주 수요일: 흉성 비활성·스우 가능', r.get('star')=='X·이번 주 클리어 완료' and r.get('lotus')=='O', r)
    r=pg.evaluate(ROWS,'2026-10-22'); check('다음 목요일(리셋) → 둘 다 가능', r.get('star')=='O' and r.get('lotus')=='O', r)
    r=pg.evaluate(ROWS,'2026-10-15'); check('목요일(주 시작)도 같은 주', r.get('star')=='X·이번 주 클리어 완료', r)
    # 이번 주(c.weekly) + 이번 달 검은 마법사(c.monthly)
    info=pg.evaluate("""()=>{ const c=S.characters[0]; c.weekly={star:true}; c.monthly={blackmage:S.period.week}; save();
      const w=S.period.week, t=Date.parse(w+'T12:00:00+09:00'), d=n=>dayId(t+n*864e5), [Y,M]=S.period.month.split('-').map(Number), nm=M===12?`${Y+1}-01-01`:`${Y}-${pad(M+1)}-01`;
      return {wed:d(6), thu:d(7), nm, mday:S.period.month+'-'+(dayId(Date.now()).slice(8))}; }""")
    r=pg.evaluate(ROWS,info['wed']); check('이번 주 수요일: 흉성 비활성', r.get('star')=='X·이번 주 클리어 완료' and r.get('lotus')=='O', r)
    r=pg.evaluate(ROWS,info['thu']); check('다음 주 목요일: 흉성 가능', r.get('star')=='O', r)
    r=pg.evaluate(ROWS,info['mday']); check('검은 마법사: 이번 달 클리어 → 비활성', r.get('blackmage')=='X·이번 달 클리어 완료', r)
    r=pg.evaluate(ROWS,info['nm']); check('검은 마법사: 다음 달 → 가능', r.get('blackmage')=='O', r)
    pg.evaluate(ROWS,info['wed']); pg.click('#calBossModal [data-calbs="star"]',force=True); pg.wait_for_timeout(100)
    check('비활성 보스 클릭해도 시간 선택 안 열림', pg.locator('#calBossModal .calbh').count()==0)
    col=pg.evaluate("getComputedStyle(document.querySelector('#calBossModal .calbcl')).color"); check('클리어 완료 글자 밝은 초록', col=='rgb(77, 255, 154)', col)
    pg.mouse.move(5,5); pg.wait_for_timeout(250); pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'modal_cleared.png'))
    pg.click('#calBossModal [data-calbs="lotus"]'); check('클리어 안 한 보스는 선택 가능', pg.locator('#calBossModal .calbh').count()==1)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
