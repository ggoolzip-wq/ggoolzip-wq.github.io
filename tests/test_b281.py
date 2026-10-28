# test_b281: 게이지 카운팅 — 막대 0→목표, % 0.00→목표(둘째 자리 내림), X 0→목표, 같은 1.2초 ease-out. '완료'·금빛은 도착 뒤만. 같은 값 재렌더면 다시 안 돎. reduced-motion 이면 바로 최종
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
  S.activeId='c0'; W.slice(0,N).forEach(b=>S.characters[0].weekly[b.id]=true); S.characters[0].exp={rate:42.5,level:280}; save&&save(); render(); }"""
ST="""()=>[...document.querySelectorAll('.revpanel .rp-gauge')].map(g=>({k:g.classList[1],cls:g.className,an:g.dataset.ganim||'',w:parseFloat(g.querySelector('.rpg-bar i').style.width),p:g.querySelector('.rpg-t').textContent,i:g.querySelector('.rpg-ing').textContent,x:g.querySelector('.rpg-xy').textContent}))"""
def shot(pg,n):
    if SD: os.makedirs(SD,exist_ok=True); pg.locator('.revpanel .rp-gauge.rpg-w').locator('..').screenshot(path=os.path.join(SD,n))
A="""()=>({an:[...document.querySelectorAll('[data-gk]')].map(e=>e.dataset.gk+':'+(e.dataset.ganim||'')),
 w:(document.querySelector('.rp-gauge.rpg-w .rpg-t')||{}).textContent, e:(document.querySelector('.expl .gnum')||{}).textContent,
 wk:(document.querySelector('[data-gk^="wk:"] .gnum')||{}).textContent, mini:(document.querySelector('[data-gk^="mini:"] .gnum')||{}).textContent})"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate(SETUP,7); pg.wait_for_timeout(1600)
    pg.reload(); pg.wait_for_timeout(100); pg.evaluate("render()"); pg.wait_for_timeout(250); pg.evaluate("render()")
    m=pg.evaluate(A); check('부팅 재렌더 중에도 카운팅 이어짐', m['w']!='58.33%' and any(x.endswith(':run') for x in m['an']), m)
    pg.wait_for_timeout(1500); f=pg.evaluate(A)
    check('끝 값', f['w']=='58.33%' and f['e']=='42.50%' and f['wk']=='7', f)
    kinds={x.split(':')[0] for x in f['an']}; check('게이지 종류: rpg-w·rpg-m·exp·wk·mo·mini', {'rpg-w','exp','wk','mo','mini'}<=kinds, kinds)
    pg.click('[data-tab="total"]'); pg.wait_for_timeout(300); pg.click('[data-tab="boss"]'); pg.wait_for_timeout(250)
    t=pg.evaluate(A); check('탭 전환 후 다시 0부터 카운팅', t['w']!='58.33%' and any(x.endswith(':run') for x in t['an']), t)
    pg.wait_for_timeout(1500); check('탭 전환 끝 값', pg.evaluate(A)['w']=='58.33%')
    check('JS 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
