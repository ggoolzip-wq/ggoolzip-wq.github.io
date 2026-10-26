# test_b273: '진행중' 의 '진' 잉크 위 끝 = '행' 잉크 위 끝 (화면 배율 DPR 1 · 1.25 · 1.5 · 2 · 3, 두 테마) — Windows 배율에서도 '진' 만 튀지 않음
# 글씨·크기는 진행중 전체와 같아야(진 span 도 Orbit 13.5px)
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
from PIL import Image
site=tempfile.mkdtemp(); shutil.copy(os.path.join(SRCR,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const W=BOSSES.filter(b=>b.type==='weekly').slice(0,12);
  S.characters=[{id:'c0',name:'zet',level:280,job:'히어로',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',
    bosses:Object.assign(Object.fromEntries(W.map(b=>[b.id,{enabled:true,diff:b.diffs[0],party:1}])),{blackmage:{enabled:true,diff:'hard',party:1}}),weekly:{},monthly:{},auto:{},drops:{},sync:{}}];
  S.activeId='c0'; W.slice(0,7).forEach(b=>S.characters[0].weekly[b.id]=true); save&&save(); render(); }"""
GLY="""sel=>{const g=document.querySelector('.revpanel '+sel), e=g.querySelector('.rpg-ing'), w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT), out=[]; let t;
  while(t=w.nextNode()) for(let i=0;i<t.length;i++){const r=document.createRange(); r.setStart(t,i); r.setEnd(t,i+1); const b=r.getBoundingClientRect(); out.push([t.data[i],b.left,b.right]);}
  const n=g.querySelector('.rpg-num').getBoundingClientRect(); const j=g.querySelector('.rpg-j');
  return {g:out,box:[n.left-3,n.top-5,n.right+3,n.bottom+5],font:[getComputedStyle(e).fontFamily,getComputedStyle(e).fontSize,j?getComputedStyle(j).fontFamily:null,j?getComputedStyle(j).fontSize:null]};}"""
NOGLOW='.rpg-num,.rpg-num *{filter:none!important;text-shadow:none!important}'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for dpr in [1,1.25,1.5,2,3]:
      for th in ['dark','light']:
        pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',device_scale_factor=dpr); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1200)
        pg.evaluate(SETUP); pg.evaluate("document.fonts.ready"); pg.evaluate(f"document.documentElement.dataset.theme='{th}'"); pg.add_style_tag(content=NOGLOW+(os.environ.get('JY') and ':root{--jy:'+os.environ['JY']+'}' or '')); pg.mouse.move(5,5); pg.wait_for_timeout(300)
        for sel in ['.rpg-w','.rpg-m']:
            R=pg.evaluate(GLY,sel); x0,y0,x1,y1=R['box']; fn=os.path.join(SD or tempfile.gettempdir(),f'{PFX}_zoom_dpr{dpr}_{th}_{sel[5:]}.png'); os.makedirs(os.path.dirname(fn),exist_ok=True)
            pg.screenshot(path=fn,clip=dict(x=x0,y=y0,width=x1-x0,height=y1-y0))
            im=Image.open(fn).convert('RGB'); W,H=im.size; px=im.load(); bg=px[1,1]; S=W/(x1-x0)
            tops={}
            for ch,a,c in R['g']:
                A,C=max(0,int((a-x0+.3)*S)),min(W,int((c-x0-.3)*S))
                ys=[y for y in range(H) if any(sum(abs(u-v) for u,v in zip(px[x,y],bg))>120 for x in range(A,C))]
                tops[ch]=ys[0] if ys else None
            if not SD: os.remove(fn)
            print(f'TOP dpr{dpr} {th} {sel}: 기기px {tops}')
            if '진' in tops:
                d=tops['진']-tops['행']
                check(f'dpr{dpr} {th} {sel}: 진 위 끝 = 행 위 끝 (차 {d} 기기px, 허용 0~+1)', 0<=d<=1, tops)
                check(f'dpr{dpr} {th} {sel}: 진 = 진행중과 같은 글씨·크기', R['font'][0]==R['font'][2] and R['font'][1]==R['font'][3], R['font'])
        pg.close()
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
