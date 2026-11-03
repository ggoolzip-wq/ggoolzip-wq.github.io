# test_b362 (t677): 에픽빔 기록지 클립 카드 4줄 제목 정렬 — 아이콘 칸 고정폭, 2~4줄 글자 x 동일(±1px), 세로 가운데, 긴 글자 말줄임.
# 스크린샷: MBT_SHOTDIR(기본 tests/out) 에 b362_card.png, b362_card_light.png
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.environ.get('B362_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOT=os.environ.get('B362_SHOT','b362_card')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr','fonts']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},mdate:{},auto:{},drops:{},sync:{}});
  S.characters=[mk('c0','아주아주아주긴닉네임테스트용캐릭터이름말줄임확인용입니다')]; S.activeId='c0'; save(); render();
  const b=BOSSES.find(x=>x.id==='lucid'); const item=dropsFor(b,'hard').find(k=>ITEM_ICONS[k]);
  const it=ITEMS[item]; it.n=it.n+' 아주 긴 아이템 이름 말줄임 확인용 텍스트';
  b.name=b.name+' 아주 아주 긴 보스 이름 말줄임 확인용 텍스트';
  const m={id:'t1',t0:Date.UTC(2026,10,3,12,34,56),boss:'lucid',diff:'hard',item,cid:'c0',start:-1000,end:2900,up:1,remote:false,poster:null};
  const v=document.querySelector('#view'); v.innerHTML='<div class="card ecwrap" style="width:340px"><div class="ecgrid" style="grid-template-columns:1fr">'+ecCard(m,0)+'</div></div>'; return item; }"""
MEAS="""()=>{ const c=document.querySelector('.eccard'), t=c.querySelector('.ectl'); const r=e=>e.getBoundingClientRect();
  const rows=[...t.children].slice(0,4).map(d=>{ const s=d.querySelector(':scope>span:last-child')||d, ic=d.children.length>1?d.children[0]:null;
    const rs=r(s), ri=ic?r(ic):null; return {x:rs.left, ell:s.scrollWidth>s.clientWidth+1, h:rs.height, cy:rs.top+rs.height/2, icx:ri&&ri.left, icw:ri&&ri.width, ich:ri&&ri.height, icy:ri&&(ri.top+ri.height/2), row:r(d).height}; });
  return {rows, tl:r(t).left+parseFloat(getComputedStyle(t).paddingLeft), d1:(()=>{const g=document.createRange(); g.selectNodeContents(t.children[0]); return g.getBoundingClientRect().left;})()}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for theme in ['dark','light']:
      pg=b.new_page(viewport={'width':900,'height':700},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul',device_scale_factor=2); pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.route('https://open.api.nexon.com/**',lambda r:r.abort()); pg.route('**/*workers.dev/**',lambda r:r.abort())
      pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
      pg.evaluate("t=>document.documentElement.setAttribute('data-theme',t)",theme)
      pg.evaluate(SETUP); pg.wait_for_timeout(400)
      pg.evaluate("()=>{ for(const e of document.querySelectorAll('body *')){ const c=getComputedStyle(e); if(c.position==='fixed'&&e.offsetWidth>=innerWidth*.9&&e.offsetHeight>=innerHeight*.9) e.style.display='none'; } }")
      M=pg.evaluate(MEAS); R=M['rows']; print(theme,M)
      pg.locator('.eccard').first.screenshot(path=os.path.join(OUT,SHOT+('' if theme=='dark' else '_light')+'.png'))
      if theme=='dark':
        xs=[r['x'] for r in R[1:]]
        check('2~4줄 글자 왼쪽 x 동일(±1px)',max(xs)-min(xs)<=1,xs)
        check('아이콘 칸 같은 크기·같은 x',len({(round(r['icw']),round(r['ich']),round(r['icx'])) for r in R[1:]})==1,[(r['icx'],r['icw'],r['ich']) for r in R[1:]])
        check('날짜 줄 = 아이콘 칸 왼쪽 끝',abs(M['d1']-R[1]['icx'])<=1,(M['d1'],R[1]['icx']))
        check('아이콘·글자 세로 가운데(±1px)',all(abs(r['cy']-r['icy'])<=1 for r in R[1:]),[(r['cy'],r['icy']) for r in R[1:]])
        check('줄 높이 일정',len({round(r['row']) for r in R[1:]})==1,[r['row'] for r in R])
        check('긴 글자 한 줄 말줄임',all(r['ell'] and r['h']<30 for r in R[1:]),[(r['ell'],r['h']) for r in R[1:]])
      pg.close()
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.kill()
print('FAILS',fails) if fails else print('ALL PASS')
sys.exit(1 if fails else 0)
