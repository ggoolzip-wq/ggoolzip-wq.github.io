# (b269: X/Y 앞 '이번 주 결정석 진행도' 글자는 떼고 비교 · % = 소수 둘째 자리 내림 · 100% 면 '완료')
# (b267: X/Y = 게이지 왼쪽 밑 .rpg-xy, 오른쪽 = 'N% 진행중')
# test_b266: 이번 주 수익 총합 — 현황 게이지(주간 결정석 개수 X/Y, 7세그먼트), 색 구간, 날짜 문구에서 ' · 전체 캐릭터' 제거
# MBT_ROOT = 다른 빌드(변경 전 사진용, MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = before/after
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRCR=os.environ.get('MBT_ROOT') or ROOT
NOCHK=os.environ.get('MBT_NOCHECK')=='1'; SD=os.environ.get('MBT_SHOTDIR'); PFX=os.environ.get('MBT_SHOT','after')
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(SRCR,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""n=>{ const W=BOSSES.filter(b=>b.type==='weekly').slice(0,12);
  S.characters=Array.from({length:n},(_,i)=>({id:'c'+i,name:'zet'+i,level:280,job:'히어로',world:'스카니아',ocid:'',accId:'',isMain:!i,image:'',
    bosses:Object.fromEntries(W.map(b=>[b.id,{enabled:true,diff:b.diffs[0],party:1}])),weekly:{},monthly:{},auto:{},drops:{},sync:{}}));
  S.activeId='c0'; save&&save(); render(); return W.map(b=>b.id); }"""
SETW="""([ks,k])=>{ S.characters.forEach((c,i)=>{ c.weekly={}; ks.slice(0,k[i]).forEach(s=>c.weekly[s]=true); }); render(); const g=document.querySelector('.revpanel .rp-gauge');
  return g?{cls:g.className,lab:(g.querySelector('.rpg-xy')||g.querySelector('.seg7')).textContent.replace(/^[^0-9]+/,'')||g.querySelector('.seg7').getAttribute('aria-label'),pc:(g.querySelector('.rpg-num .tir-sr')||{}).textContent||(g.querySelector('.rpg-num .seg7')||{getAttribute:()=>null}).getAttribute('aria-label'),ing:(g.querySelector('.rpg-ing')||{}).textContent||'',pct:+g.dataset.pct,col:getComputedStyle(g.querySelector('.rpg-num')).color}:null; }"""
def shot(pg,name):
    if not SD: return
    os.makedirs(SD,exist_ok=True); pg.mouse.move(5,5); pg.wait_for_timeout(400); pg.locator('.revpanel').first.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
    ks=pg.evaluate(SETUP,12); r=pg.evaluate(SETW,[ks,[0]*12])
    shot(pg,'panel_0of144')
    if not NOCHK:
        sub=pg.evaluate("document.querySelector('.revpanel h2').nextElementSibling.innerText")
        check('날짜 문구 = 기간만', '전체 캐릭터' not in sub and '~' in sub, sub)
        check('12캐릭 x 12 = 0/144 빨강', r and r['lab']=='0/144' and 'g-red' in r['cls'], r)
        el=pg.evaluate("(()=>{const p=document.querySelector('.revpanel'), t=p.querySelector('.rp-total'), g=p.querySelector('.rp-gauge'), c=p.querySelector('.rp-cry'); return t.nextElementSibling===g && g.nextElementSibling===c; })()")
        check('게이지 위치 = 메소 총합과 주보 결정석 사이', el)
        r2=pg.evaluate(SETW,[ks,[12]*6+[0]*6]); check('6캐릭 다 잡음 = 72/144 주황(50%)', r2['lab']=='72/144' and 'g-org' in r2['cls'], r2)
        r3=pg.evaluate(SETW,[ks,[13]*12]); check('한도 넘게 체크해도 144/144 금색', r3['lab']=='144/144' and 'g-gold' in r3['cls'], r3)
    pg.evaluate(SETUP,1)
    T=[(3,'g-red','3/12'),(4,'g-org','4/12'),(7,'g-org','7/12'),(8,'g-sky','8/12'),(11,'g-sky','11/12'),(12,'g-gold','12/12')]
    for k,cls,lab in T:
        r=pg.evaluate(SETW,[ks,[k]])
        if k in (3,7,11,12): shot(pg,f'{cls[2:]}_{k}of12')
        check(f'{lab} → {cls}', r and r['lab']==lab and cls in r['cls'], r)
    if not NOCHK:
        # 경계: 32.99/33/65.99/66/99.99/100 → 같은 규칙 (weekGaugeData 의 분류식)
        cl=pg.evaluate("[[3299,10000],[33,100],[6599,10000],[66,100],[9999,10000],[1,1]].map(([d,t])=>{ const pct=d/t*100; return d>=t?'g-gold':pct>=66?'g-sky':pct>=33?'g-org':'g-red'; })")
        check('경계 32.99/33/65.99/66/99.99/100', cl==['g-red','g-org','g-org','g-sky','g-sky','g-gold'], cl)
        src=pg.evaluate("weekGaugeData.toString()"); check('분류식 = 이 식', "pct>=66?'g-sky':pct>=33?'g-org':'g-red'" in src and 'done>=total' in src)
        # 키 지운 계정 캐릭 제외
        pg.evaluate(SETUP,2); pg.evaluate("()=>{ S.settings.accounts=[{id:'A',name:'a',key:''}]; S.characters[1].accId='A'; render(); }")
        r=pg.evaluate(SETW,[ks,[3,12]]); check('API 키 지운 계정 캐릭터 제외 → 3/12', r and r['lab']=='3/12', r)
        pg.evaluate(SETUP,1); pg.evaluate("()=>{ S.theme='light'; S.settings.theme='light'; document.documentElement.dataset.theme='light'; }")
        for k,cls in [(3,'red'),(7,'org'),(11,'sky'),(12,'gold')]:
            r=pg.evaluate(SETW,[ks,[k]]); pg.evaluate("document.documentElement.dataset.theme='light'"); shot(pg,f'light_{cls}_{k}of12')
            check(f'라이트 테마 {cls} 색 적용', r and r['col'] not in ('rgb(0, 0, 0)',''), r)
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
