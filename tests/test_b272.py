# test_b272: 게이지 글자 — 실제 그려진 폰트(CDP)=Orbit 웹폰트만 · 숫자/한글 같은 크기 · 글자별 span/이동 없음 · 한글 글자별 잉크 고름 · 막대 끝 바로 옆 6px · 한 줄
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

OB={"진":(-106,778),"행":(-134,762),"중":(-133,735),"완":(-60,821),"료":(-20,697)}  # Orbit-Regular 글자 잉크 yMin,yMax (1000 단위) · b277: 진 개별 이동 없음 · b276: 완 = 1px-.02em 올림 반영(13.5px 기준 54 단위)
GLY="""sel=>{const g=document.querySelector('.revpanel '+sel), w=document.createTreeWalker(g.querySelector('.rpg-ing'),NodeFilter.SHOW_TEXT), out=[]; let t;
  while(t=w.nextNode()) for(let i=0;i<t.length;i++){const r=document.createRange(); r.setStart(t,i); r.setEnd(t,i+1); const b=r.getBoundingClientRect(); out.push([t.data[i],b.left,b.right,b.top,b.bottom]);} return out;}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',device_scale_factor=3); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
    ks=pg.evaluate(SETUP,1); pg.evaluate("document.fonts.ready")
    cdp=pg.context.new_cdp_session(pg); cdp.send('DOM.enable'); cdp.send('CSS.enable')
    for k,m,name in [([7],[0],'7of12'),([12],[1],'complete')]:
        pg.evaluate(SET,[ks,k,m]); pg.wait_for_timeout(300)
        root=cdp.send('DOM.getDocument',{'depth':-1})['root']['nodeId']
        for sel in ['.rpg-w','.rpg-m']:
            for part in ['.rpg-t','.rpg-ing']:
                nid=cdp.send('DOM.querySelector',{'nodeId':root,'selector':f'.revpanel {sel} .rpg-num {part}'})['nodeId']
                F=cdp.send('CSS.getPlatformFontsForNode',{'nodeId':nid})['fonts']
                check(f'{name} {sel} {part}: 실제 그려진 폰트 = Orbit 웹폰트만 (대체 폰트 없음)', F and all(f['familyName']=='Orbit' and not f['isCustomFont']==False for f in F), F)
        G=pg.evaluate("""(()=>{const r=[];document.querySelectorAll('.revpanel .rp-gauge').forEach(g=>{const bar=g.querySelector('.rpg-bar').getBoundingClientRect(),t=g.querySelector('.rpg-num .rpg-t'),i=g.querySelector('.rpg-ing'),tb=t.getBoundingClientRect(),ib=i.getBoundingClientRect(),gb=g.getBoundingClientRect();
          r.push({gap:tb.left-bar.right,fsT:parseFloat(getComputedStyle(t).fontSize),fsI:parseFloat(getComputedStyle(i).fontSize),oneLine:Math.abs(tb.top-ib.top)<3&&i.getClientRects().length===1,spans:g.querySelectorAll('.rpg-num span span:not(.rpg-j)').length,tail:gb.right-ib.right,bar:bar.width});});return r;})()""")
        check(f'{name}: 막대 끝 → 숫자 사이 6px (빈 칸 없음)', all(abs(x['gap']-6)<0.6 for x in G), G)
        check(f'{name}: 숫자·진행중/완료 같은 글자 크기', all(abs(x['fsT']-x['fsI'])<0.01 for x in G), G)
        check(f'{name}: 한 줄 · 글자별 span 없음(b273: 진 만 예외)', all(x['oneLine'] and x['spans']==0 for x in G), G)
        check(f'{name}: 글자 뒤 남는 칸 ≤ 숫자 한 칸(9px)', all(-0.5<=x['tail']<=9 for x in G), G)
    pg.add_style_tag(content=NOGLOW)
    for th in ['dark','light']:
        for k,m,name in [([7],[0],'7of12'),([12],[1],'complete')]:
            pg.evaluate(SET,[ks,k,m]); pg.evaluate(f"document.documentElement.dataset.theme='{th}'"); pg.mouse.move(5,5); pg.wait_for_timeout(300)
            for sel in ['.rpg-w','.rpg-m']:
                r=pg.evaluate(INFO,sel); fn=os.path.join(tempfile.gettempdir(),'b272g.png'); ink(pg,r,fn)
                tops=[];bots=[];chs=[]
                for ch,x0,x1,_,_ in pg.evaluate(GLY,sel):
                    chs.append(ch)
                    r2=dict(r); r2['dx']=[x0+.3,x1-.3]; r2['kx']=None; I,_=ink(pg,r2,fn)
                    tops.append(I[0]); bots.append(I[1])
                print(f'GLYPH {th} {name} {sel}: tops {tops} bots {bots}')
                # 글자별 잉크 = Orbit 글자 디자인(같은 기준선) 그대로 ±.7px — 글자별 이동/다른 폰트면 어긋남
                fs=13.5; et=[-OB[c][1]*fs/1000 for c in chs]; eb=[-OB[c][0]*fs/1000 for c in chs]
                dt=[(tops[i]-tops[0])-(et[i]-et[0]) for i in range(len(chs))]; db=[(bots[i]-bots[0])-(eb[i]-eb[0]) for i in range(len(chs))]
                check(f'[{th}] {name} {sel} 한글 글자별 잉크 = 같은 기준선(Orbit 디자인대로 ±.7px, 한 글자만 튀지 않음)', all(abs(v)<=.7 for v in dt+db), [chs,tops,bots,dt,db])
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
