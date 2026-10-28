# test_b278: 게이지 카운팅 — 막대 0→목표, % 0.00→목표(둘째 자리 내림), X 0→목표, 같은 1.2초 ease-out. '완료'·금빛은 도착 뒤만. 같은 값 재렌더면 다시 안 돎. reduced-motion 이면 바로 최종
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SD=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""N=>{ const W=BOSSES.filter(b=>b.type==='weekly').slice(0,12);
  S.characters=[{id:'c0',name:'zet',level:280,job:'히어로',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',
    bosses:Object.assign(Object.fromEntries(W.map(b=>[b.id,{enabled:true,diff:b.diffs[0],party:1}])),{blackmage:{enabled:true,diff:'hard',party:1}}),weekly:{},monthly:{},auto:{},drops:{},sync:{}}];
  S.activeId='c0'; W.slice(0,N).forEach(b=>S.characters[0].weekly[b.id]=true); if(N>=12) S.characters[0].monthly.blackmage=S.period.week; save&&save(); render(); }"""
ST="""()=>[...document.querySelectorAll('.revpanel .rp-gauge')].map(g=>({k:g.classList[1],cls:g.className,an:g.dataset.ganim||'',w:parseFloat(g.querySelector('.rpg-bar i').style.width),p:g.querySelector('.rpg-t').textContent,i:g.querySelector('.rpg-ing').textContent,x:g.querySelector('.rpg-xy').textContent}))"""
def shot(pg,n):
    if SD: os.makedirs(SD,exist_ok=True); pg.locator('.revpanel .rp-gauge.rpg-w').locator('..').screenshot(path=os.path.join(SD,n))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate(SETUP,7); pg.wait_for_timeout(250); m=pg.evaluate(ST); shot(pg,'mid_gauge_7of12.png')
    w=[g for g in m if g['k']=='rpg-w'][0]
    check('7/12 중간: 카운팅 중(막대·%·X 가 목표보다 작음)', w['an']=='run' and 0<w['w']<58.34 and float(w['p'][:-1])<58.33 and w['x'].endswith('/12') and int(w['x'].split()[-1].split('/')[0])<7, w)
    check('중간 % 둘째 자리 형식', len(w['p'].split('.')[1])==3, w['p'])
    pg.wait_for_timeout(1400); f=pg.evaluate(ST); w=[g for g in f if g['k']=='rpg-w'][0]; shot(pg,'final_gauge_7of12.png')
    check('7/12 끝: 58.33% · 7/12 · 진행중 · 주황', w['an']=='done' and w['p']=='58.33%' and w['x'].endswith('7/12') and w['i']=='진행중' and 'g-org' in w['cls'] and abs(w['w']-58.33)<.01, w)
    pg.evaluate("render()"); pg.wait_for_timeout(200); r=pg.evaluate(ST); check('같은 값 재렌더 = 다시 안 돎', all(g['an']=='' and g['p'] in ('58.33%','0.00%') for g in r), r)
    pg.evaluate(SETUP,12); seen=set(); gold_early=False
    for _ in range(30):
        s=[g for g in pg.evaluate(ST) if g['k']=='rpg-w'][0]
        if s['an']=='run':
            seen.update(c for c in ('g-org','g-sky','g-gold') if c in s['cls'])
            if 'g-gold' in s['cls'] or s['i']!='진행중' or s['p']=='100.00%': gold_early=True
        pg.wait_for_timeout(50)
    check('7→12: 이전 값에서 올라가며 주황→하늘, 금빛·완료·100.00% 는 도착 뒤만', 'g-sky' in seen and not gold_early, (seen,gold_early))
    pg.wait_for_timeout(800); f=pg.evaluate(ST); shot(pg,'final_gauge_complete.png')
    check('끝: 둘 다 100.00% 완료 + 금/빨강 빛', all(g['p']=='100.00%' and g['i']=='완료' and g['an']=='done' for g in f) and 'g-gold' in f[0]['cls'] and 'g-mred' in f[1]['cls'], f)
    pg.close()
    ctx=b.new_context(viewport={'width':1600,'height':1000},locale='ko-KR',reduced_motion='reduce'); pg=ctx.new_page(); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate(SETUP,7); pg.wait_for_timeout(150); w=[g for g in pg.evaluate(ST) if g['k']=='rpg-w'][0]
    check('b281 reduced-motion(Windows 애니메이션 효과 끔)에도 카운팅', w['an']=='run' and w['p']!='58.33%', w)
    b.close()
finally: srv.terminate()
check('JS 오류 없음', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
