# test_b249: 결과 글자 = '기록 금액 :'(노랑) + 금액(초록), 더 큰 글씨 — 전체 수정 창 + 수익 기록 팝업, 1280/390 · dark/light 에서 창 안에 들어가고 읽힘
# MBT_SHOTDIR=폴더 → after_ 사진
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SD=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
def state(theme):
    C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',3)},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
    return {'version':5,'theme':theme,'activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
FIND="b=>[...document.querySelectorAll(`[data-drop^=\"${b}|\"]`)].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))"
SEED="""([ks,kk,party])=>{const c=S.characters[0]; c.drops={[ks]:1}; c.drev={[ks]:{m:1e9,a:10,p:1,i:ks.split('|')[1]}};
 if(party){ c.drops[kk]=1; c.dmode={[kk]:'s'}; c.drev[kk]={m:Math.round(1e9/3),a:10,p:3,i:kk.split('|')[1]}; } save(); render(); }"""
# 글자 검사: 문구, 색(노랑 = R,G 높고 B 낮음 / 초록 = G 가장 큼), 크기 ≥13px(390: ≥12.5), 배경 대비, 창 안·가로 넘침 없음
INFO="""([sel,box])=>{const e=document.querySelector(sel); if(!e) return null; const l=e.querySelector('.rlab'),v=e.querySelector('.rval'),m=document.querySelector(box).getBoundingClientRect(),r=e.getBoundingClientRect();
 const rgb=x=>getComputedStyle(x).color.match(/\\d+/g).map(Number); let bg=null; for(let n=e;n&&!bg;n=n.parentElement){const c=getComputedStyle(n).backgroundColor.match(/[\\d.]+/g); if(c&&(c.length<4||+c[3]>.5)) bg=c.slice(0,3).map(Number);}
 const lum=c=>{const f=x=>(x/=255)<=.03928?x/12.92:((x+.055)/1.055)**2.4; return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2]);}, cr=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
 return {text:e.innerText.replace(/\\s+/g,' ').trim(),lab:rgb(l),val:rgb(v),fs:parseFloat(getComputedStyle(l).fontSize),crl:cr(rgb(l),bg),crv:cr(rgb(v),bg),fit:r.left>=m.left-1&&r.right<=m.right+1,ov:document.documentElement.scrollWidth>innerWidth}; }"""
def judge(tag,i,exp,vw):
    check(f'{tag} 문구', i and i['text']=='기록 금액 : '+exp, i and i['text'])
    if not i: return
    L,V=i['lab'],i['val']
    check(f'{tag} 노랑/초록', L[0]>140 and L[1]>90 and L[2]<L[1]*0.6 and V[1]>V[0]+40 and V[1]>V[2]+20, (L,V))
    check(f'{tag} 크기', i['fs']>=(12.5 if vw<480 else 13), i['fs'])
    check(f'{tag} 대비', i['crl']>=3 and i['crv']>=3, (i['crl'],i['crv']))
    check(f'{tag} 창 안·넘침 없음', i['fit'] and not i['ov'], i)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for theme in ['dark','light']:
      for vw,vh in [(1280,900),(390,844)]:
       for party in [True,False]:
        sx="party" if party else "solo"; tag=f'{theme} {vw} {sx}'; shot=SD and vw==1280 and theme=='dark'
        pg=b.new_page(viewport={'width':vw,'height':vh},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",state(theme)); pg.reload(); pg.wait_for_timeout(800)
        ks=pg.evaluate(FIND,'seren'); kk=pg.evaluate(FIND,'kaling'); pg.evaluate(SEED,[ks,kk,party]); pg.wait_for_timeout(200)
        pg.click('#revAllBtn'); pg.wait_for_selector('#revAllModal')
        pg.click('[data-rafee="s"][data-v="3"]')
        if party: pg.click('[data-rafee="d"][data-v="3"]')
        if shot: pg.locator('#revAllModal .modal').screenshot(path=f'{SD}/after_editall_{sx}.png')
        for k,exp in [(ks,970000000)]+([(kk,None)] if party else []):
            i=pg.evaluate("k=>revAllRows(S.characters[0]).findIndex(x=>x.key===k)",k)
            e=pg.evaluate(f"()=>meso({exp})") if exp else pg.evaluate(f"()=>meso(Math.round(revNet(revGrossOf(S.characters[0].drev['{k}']),3,3,3)))")
            judge(f'전체 수정 {tag} {k.split("|")[0]}',pg.evaluate(INFO,[f'[data-ram="{i}"]','#revAllModal .modal']),e,vw)
        pg.keyboard.press('Escape')
        pg.evaluate("()=>localStorage.removeItem('mapleBossTracker.revFee')")
        k=kk if party else ks; pg.evaluate("([k,b])=>askRev(S.characters[0],findBoss(b),k,k.split('|')[1],null)",[k,'kaling' if party else 'seren']); pg.wait_for_selector('#revModal')
        pg.fill('#rvAmt','10'); pg.click('[data-fee="s"][data-v="3"]')
        if party: pg.click('[data-fee="d"][data-v="3"]')
        if shot: pg.locator('#revModal .modal').screenshot(path=f'{SD}/after_popup_{sx}.png')
        judge(f'팝업 {tag}',pg.evaluate(INFO,['#rvRam','#revModal .modal']),pg.evaluate(f"()=>meso({316801347 if party else 970000000})"),vw)
        pg.close()
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
