# test_b267: 게이지 오른쪽 = 'N% 진행중'(7세그먼트, 내림 정수 — 100% 는 다 잡았을 때만), 게이지 왼쪽 밑 작은 X/Y.
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
  return g?{cls:g.className,lab:(g.querySelector('.rpg-xy')||g.querySelector('.seg7')).textContent||g.querySelector('.seg7').getAttribute('aria-label'),pc:g.querySelector('.rpg-num .seg7').getAttribute('aria-label'),ing:g.querySelector('.rpg-num').textContent,pct:+g.dataset.pct,col:getComputedStyle(g.querySelector('.rpg-num')).color}:null; }"""
def shot(pg,name):
    if not SD: return
    os.makedirs(SD,exist_ok=True); pg.mouse.move(5,5); pg.wait_for_timeout(400); pg.locator('.revpanel').first.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
    ks=pg.evaluate(SETUP,1)
    for k,cls in [(3,'red'),(7,'org'),(11,'sky'),(12,'gold')]:
        r=pg.evaluate(SETW,[ks,[k]]); shot(pg,f'{cls}_{k}of12')
        if not NOCHK:
            want={3:'25%',7:'58%',11:'91%',12:'100%'}[k]
            check(f'{k}/12 → {want} 진행중 · 작은 {k}/12', r and r['pc']==want and r['ing'].endswith('진행중') and r['lab']==f'{k}/12', r)
    if not NOCHK:
        pg.evaluate(SETUP,12); r=pg.evaluate(SETW,[ks,[12]*11+[11]]); check('143/144 = 99% (100% 아님)', r['pc']=='99%' and 'g-sky' in r['cls'] and r['lab']=='143/144', r)
        r=pg.evaluate(SETW,[ks,[0]*12]); check('0/144 = 0%', r['pc']=='0%' and r['lab']=='0/144', r)
        pg.evaluate(SETUP,1); pg.evaluate(SETW,[ks,[7]])
        L=pg.evaluate("""(()=>{const g=document.querySelector('.rp-gauge'),b=g.querySelector('.rpg-bar').getBoundingClientRect(),x=g.querySelector('.rpg-xy').getBoundingClientRect(),n=g.querySelector('.rpg-num .seg7').getBoundingClientRect();
          return {xyLeft:x.left-b.left,xyBelow:x.top-b.bottom,xyFs:parseFloat(getComputedStyle(g.querySelector('.rpg-xy')).fontSize),numH:n.height,numRight:n.left>=b.right}})()""")
        check('X/Y = 게이지 왼쪽 끝 바로 밑, 더 작은 글씨', abs(L['xyLeft'])<1 and 0<=L['xyBelow']<6 and L['xyFs']<12, L)
        check('% 숫자 글씨 조금 작게(22→17px), 게이지 오른쪽', L['numH']==17 and L['numRight'], L)
        check('색 구간 유지(7/12 주황)', 'g-org' in pg.evaluate("document.querySelector('.rp-gauge').className"))
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
