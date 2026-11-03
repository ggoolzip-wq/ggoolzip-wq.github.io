# test_b357 (t660): 득템 축하 연출(에픽빔+불꽃+꽃가루) 끊김 회귀 테스트
# 원인이던 것: 큰 스프라이트(4608x2756) 메인 스레드 재디코드, CSS mask 매 프레임, 뒤 카드 backdrop 블러 매 프레임, 화면 전체 arc/save/restore
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
FT="""async(thr)=>{ const ft=[]; let vis=-1, last=0, on=true; await new Promise(r=>requestAnimationFrame(n=>{last=n;r()}));
 const lp=n=>{ ft.push(n-last); last=n; if(vis<0&&document.querySelector('#congrats.show')) vis=ft.length; if(on) requestAnimationFrame(lp); }; requestAnimationFrame(lp);
 celebrate(null,'r_white',BOSSES[0]); const st={on:document.body.classList.contains('cg-on')};
 await new Promise(r=>setTimeout(r,1000)); const c=document.querySelector('#congrats .cg-beam');
 st.baked=c.classList.contains('baked'); st.cw=c.width; st.mask=getComputedStyle(c).maskImage||getComputedStyle(c).webkitMaskImage; st.bd=getComputedStyle(document.querySelector('.card')).backdropFilter;
 await new Promise(r=>setTimeout(r,1100)); on=false; st.fxN=celebrate.fxN; endCelebrate(); st.off=!document.body.classList.contains('cg-on'); st.bd2=getComputedStyle(document.querySelector('.card')).backdropFilter;
 const a=ft.slice(vis); st.n=a.length; st.max=Math.max(...a); st.over50=a.filter(x=>x>50).length; st.over33=a.filter(x=>x>34).length; return st; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox','--headless=new'])
    pg=b.new_page(viewport={'width':1600,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e))); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_function("beamBake.fr&&beamBake.fr.length===16",timeout=15000)
    m=pg.evaluate("()=>({w:beamBake.fr[0].width,h:beamBake.fr[0].height,busy:beamBake.busy})")
    check('빛줄기 16장 미리 구움(화면 크기 576x344, dpr1)', m['w']==576 and m['h']==344, m)
    # CSS 연출 키프레임은 transform/opacity 만
    kf=pg.evaluate("""()=>{const o={}; for(const s of document.styleSheets){ let r; try{r=s.cssRules}catch(e){continue} for(const x of r) if(x.type===7&&['cgpop','cgfade','ib'].includes(x.name)) for(const k of x.cssRules) for(const pr of k.style) o[pr]=1; } return Object.keys(o);}""")
    check('축하 키프레임 = transform/opacity 만', kf and set(kf)<={'transform','opacity'}, kf)
    for thr in (1,4):
      cdp=pg.context.new_cdp_session(pg); cdp.send('Emulation.setCPUThrottlingRate',{'rate':thr}); pg.wait_for_timeout(300)
      best=None
      for k in range(3):  # 다른 작업이 CPU 를 쓰면 흔들림 → 3번 중 가장 좋은 것
        st=pg.evaluate(FT,thr); print(thr,st)
        if best is None or st['max']<best['max']: best=st
        pg.wait_for_timeout(400)
      st=best
      check(f'x{thr} 연출 중 cg-on·카드 블러 끔, 끝나면 복구', st['on'] and st['bd']=='none' and st['off'] and st['bd2']!='none', st)
      check(f'x{thr} 빛줄기 = 구운 프레임(마스크 없음)', st['baked'] and st['cw']==576 and st['mask'] in ('none',None,''), st)
      check(f'x{thr} 불꽃 입자 ≤ 600', 0<st['fxN']<=600, st['fxN'])
      check(f'x{thr} 프레임 수 충분(≥{60 if thr==1 else 10})', st['n']>=(60 if thr==1 else 10), st['n'])
      check(f'x{thr} 보인 뒤 가장 긴 프레임 < {100 if thr==1 else 400}ms (전: 300~1200ms)', st['max']<(100 if thr==1 else 400), st['max'])  # x4: 예전 첫 프레임 디코드 1000ms+ (CPU 바쁠 땐 x4 프레임이 원래 흔들림)
      if thr==1: check('x1 50ms 넘는 프레임 ≤ 1', st['over50']<=1, st['over50'])
      cdp.send('Emulation.setCPUThrottlingRate',{'rate':1})
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
