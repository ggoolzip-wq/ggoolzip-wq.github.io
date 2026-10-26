# (b271: 게이지 글자 = 주보 결정석과 같은 글씨체 · 숫자/진행중 잉크 위·아래 ±1px · 라벨 13px)
# test_b270: 두 게이지 막대 폭 = 글자 상관없이 항상 같음(0/58.33/99.99/100) · '진행중/완료' 실제 잉크(스샷 픽셀) 위·아래 끝 = 숫자 잉크 ±1px, 두 테마
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
    bosses:Object.assign(Object.fromEntries(W.map(b=>[b.id,{enabled:true,diff:b.diffs[0],party:1}])),{blackmage:{enabled:true,diff:'hard',party:1}}),weekly:{},monthly:{},auto:{},drops:{},sync:{}}));
  S.activeId='c0'; save&&save(); render(); return W.map(b=>b.id); }"""
SET="""([ks,k,m])=>{ S.characters.forEach((c,i)=>{ c.weekly={}; ks.slice(0,k[i]).forEach(s=>c.weekly[s]=true); c.monthly={}; if(m[i]) c.monthly.blackmage=S.period.week; }); render();
  const f=g=>g?{cls:g.className,xy:g.querySelector('.rpg-xy').textContent,pc:g.querySelector('.rpg-num .rpg-t').textContent,ing:g.querySelector('.rpg-ing').textContent,
     kfont:getComputedStyle(g.querySelector('.rpg-ing')).fontFamily,col:getComputedStyle(g.querySelector('.rpg-num')).color,flt:getComputedStyle(g.querySelector('.rpg-num')).filter,
     dH:g.querySelector('.rpg-num .rpg-t').getBoundingClientRect().height,dB:g.querySelector('.rpg-num .rpg-t').getBoundingClientRect().bottom,
     kB:g.querySelector('.rpg-ing').getBoundingClientRect().bottom,kH:g.querySelector('.rpg-ing').getBoundingClientRect().height}:null;
  return {w:f(document.querySelector('.revpanel .rp-gauge.rpg-w')),m:f(document.querySelector('.revpanel .rp-gauge.rpg-m')),order:(()=>{const w=document.querySelector('.revpanel .rpg-w');return !!w&&w.nextElementSibling===document.querySelector('.revpanel .rpg-m')})(),
    sh:document.scrollingElement.scrollHeight}; }"""
from PIL import Image
def shot(pg,name,clip=None):
    if not SD: return
    os.makedirs(SD,exist_ok=True); pg.mouse.move(5,5); pg.wait_for_timeout(400)
    if clip: pg.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'),clip=clip)
    else: pg.locator('.revpanel').first.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'))
INFO="""sel=>{const g=document.querySelector('.revpanel '+sel); if(!g) return null; const q=s=>g.querySelector(s), n=q('.rpg-num').getBoundingClientRect(), d=q('.rpg-num .rpg-t').getBoundingClientRect(), ks=[...g.querySelectorAll('.rpg-ing')], k0=ks.length?ks[0].getBoundingClientRect():null, k1=ks.length?ks[ks.length-1].getBoundingClientRect():null;
  return {n:[n.left-4,n.top-6,n.right+4,n.bottom+6],dx:[d.left,d.right],kx:k0?[k0.left,k1.right]:null,bar:q('.rpg-bar').getBoundingClientRect().width}}"""
NOGLOW='.rpg-num,.rpg-num *{filter:none!important;text-shadow:none!important}'
def ink(pg,r,fn):
    S=3; pg.screenshot(path=fn,clip=dict(x=r['n'][0],y=r['n'][1],width=r['n'][2]-r['n'][0],height=r['n'][3]-r['n'][1]))
    im=Image.open(fn).convert('RGB'); W,H=im.size; px=im.load(); bg=px[1,1]
    def rows(x0,x1):
        a,b=max(0,int((x0-r['n'][0])*S)),min(W,int((x1-r['n'][0])*S)); ys=[y for y in range(H) if any(sum(abs(u-v) for u,v in zip(px[x,y],bg))>120 for x in range(a,b))]
        return (ys[0]/S,(ys[-1]+1)/S) if ys else None
    return rows(*r['dx']), (rows(*r['kx']) if r['kx'] else None)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',device_scale_factor=3); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
    ks=pg.evaluate(SETUP,1)
    # 전체 게이지 사진: 7/12 · 다 잡음 (어두운 테마, 글로우 그대로)
    for k,m,name in [([7],[0],'7of12'),([12],[1],'complete')]:
        pg.evaluate(SET,[ks,k,m]); shot(pg,f'gauge_{name}')
    if not NOCHK:
        # 막대 폭: 주간 0/58.33/99.99/100 · 검마 0/100 — 모두 같아야
        W=[]
        for d,t in [(0,12),(7,12),(9999,10000),(12,12)]:
            W.append(pg.evaluate("([d,t])=>{ const g=weekGaugeData; window.weekGaugeData=()=>({done:d,total:t,pct:d/t*100,cls:d>=t?'g-gold':'g-org'}); render(); window.weekGaugeData=g; return document.querySelector('.revpanel .rpg-w .rpg-bar').getBoundingClientRect().width }",[d,t]))
        for m in ([0],[1]): pg.evaluate(SET,[ks,[0],m]); W.append(pg.evaluate("document.querySelector('.revpanel .rpg-m .rpg-bar').getBoundingClientRect().width"))
        check('막대 폭 항상 같음(주간 0/58.33/99.99/100, 검마 0/100)', max(W)-min(W)<0.01 and W[0]>150, W)
        ov=pg.evaluate("(()=>{ const r=[]; document.querySelectorAll('.revpanel .rpg-num').forEach(n=>{ const c=[...n.children].reduce((a,e)=>a+e.getBoundingClientRect().width,0); r.push([c,n.clientWidth]); }); return r; })()")
        check('글자가 고정 칸 안에 들어감', all(c<=w for c,w in ov), ov)
    if not NOCHK:
        F=pg.evaluate("(()=>{const s=e=>{const c=getComputedStyle(e);return [c.fontFamily,c.fontWeight,c.fontStyle]};const l=document.querySelector('.revpanel .rp-cry .rplb');return [s(l),...[...document.querySelectorAll('.revpanel .rpg-num .tsmn')].map(s)]})()")
        check('b271: NN.NN%·진행중 = 주보 결정석과 같은 글씨체/굵기/모양', len(F)>=3 and all(x==F[0] for x in F), F)
        X=pg.evaluate("[...document.querySelectorAll('.revpanel .rpg-xy')].map(e=>[parseFloat(getComputedStyle(e).fontSize),e.scrollWidth<=e.parentElement.clientWidth+1])")
        check('b271: 작은 라벨 ≥12.5px · 한 줄에 들어감', X and all(f>=12.5 and ok for f,ok in X), X)
    pg.add_style_tag(content=NOGLOW)
    for th in ['dark','light']:
        pg.evaluate(f"document.documentElement.dataset.theme='{th}'")
        for k,m,name in [([7],[0],'7of12'),([12],[1],'complete')]:
            pg.evaluate(SET,[ks,k,m]); pg.evaluate(f"document.documentElement.dataset.theme='{th}'"); pg.mouse.move(5,5); pg.wait_for_timeout(300)
            for sel in ['.rpg-w','.rpg-m']:
                r=pg.evaluate(INFO,sel); fn=os.path.join(SD or tempfile.gettempdir(),f'{PFX}_zoom3x_{th}_{name}_{sel[5:]}.png'); os.makedirs(os.path.dirname(fn),exist_ok=True)
                D,K=ink(pg,r,fn)
                if not SD: os.remove(fn)
                print(f'INK {th} {name} {sel}: digit {D} hangul {K}' + (f' dTop {K[0]-D[0]:+.2f} dBot {K[1]-D[1]:+.2f}' if D and K else ''))
                check(f'[{th}] {name} {sel} 진행중/완료 잉크 위·아래 = 숫자 ±1px', D and K and abs(K[0]-D[0])<=1 and abs(K[1]-D[1])<=1, [D,K])
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
