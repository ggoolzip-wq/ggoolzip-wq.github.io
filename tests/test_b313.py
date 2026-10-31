#!/usr/bin/env python3
"""t565/t567: 메소 칸을 화면 전체에서 찾기(창 위치가 달라도) + 자동 기록 탭 실시간 갱신(버튼 없이)."""
import os, sys, json, base64, shutil, subprocess, tempfile
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures'); OUT=os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
du=lambda f:'data:image/png;base64,'+base64.b64encode(open(f,'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
pm=json.load(open(os.path.join(FX,'t523','meta.json'))); mm=json.load(open(os.path.join(FX,'t520','meta.json')))
V={3:22564195389,4:22564195389,7:22564211971,8:22564211971,11:22564231214,12:22564231214,15:22564245632,16:22564245632,19:22564257269,20:22564257269}
COMP="""async ([w,h,bl,cr])=>{ const ld=u=>new Promise(r=>{ const im=new Image(); im.onload=()=>r(im); im.src=u; });
  const cv=document.createElement('canvas'); cv.width=w; cv.height=h; const g=cv.getContext('2d'); g.fillStyle='#000'; g.fillRect(0,0,w,h);
  const b=await ld(bl); g.drawImage(b,0,h-b.height); for(const [u,x,y] of cr) g.drawImage(await ld(u),x,y); return cv; }"""
READ="""async a=>{ const cv=await ("+COMP+")(a); const A=window.AR; A.bbox=null;A.bbKey='';A.prof=null;A.geo=null; if(!a[4]) A.mesoLoc=null; A.mesoLocT=0; await arProfDetect(cv); await arMesoTpl(); const t0=performance.now(); arMesoLocate(cv); const ms=performance.now()-t0;
  const so=arMesoPanel(cv,'sto')&&arMesoPanel(cv,'stoInv'), io=!so&&arMesoPanel(cv,'inv'); const o={so,io,ms:Math.round(ms),prof:A.prof&&A.prof.id,loc:A.mesoLoc&&{inv:A.mesoLoc.inv&&A.mesoLoc.inv.sc,sto:A.mesoLoc.stoInv&&A.mesoLoc.stoInv.sc}};
  if(so){ o.inv=(await arMesoRead(cv,'stoInv')).v; o.sto=(await arMesoRead(cv,'sto')).v; } else if(io) o.inv=(await arMesoRead(cv,'inv')).v; return o; }""".replace('"+COMP+"',COMP)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    # 1) 20장 × 창 위치 3가지(원래 자리 + 두 곳으로 옮김) — 5개 프로필 모두
    SH=[(0,0),(-1,-1),(1,-1)]; mx=0
    for n in range(1,21):
      w,h=pm[str(n)]; base=mm[str(n)]
      for si,(sx,sy) in enumerate(SH):
        xs=[x for f,x,y in base]; ys=[y for f,x,y in base]; from PIL import Image; x0,y0=min(xs),min(ys); x1=max(x+Image.open(os.path.join(FX,'t520',f)).width for f,x,y in base)
        dx=0 if sx==0 else (-(x0-40) if sx<0 else (w-40-x1)); dy=0 if sy==0 else -(y0-int(h*.25))
        cr=[[du(os.path.join(FX,'t520',f)),x+dx,y+dy] for f,x,y in base]
        r=pg.evaluate(READ,[w,h,du(os.path.join(FX,'t523','bl%02d.png'%n)),cr,0]); mx=max(mx,r['ms'])
        if n in V: ok=r['inv']==V[n] and (r['so']==(n%2==0)) and (r.get('sto')==0 if n%2==0 else True)
        else: ok=not r['so'] and not r['io']
        check(f'{n:02d}번 {w}x{h} 위치{si} ({dx:+d},{dy:+d}) '+('창고' if n in V and n%2==0 else '인벤' if n in V else '창 닫힘'),ok,r)
    check(f'전체 찾기 1회 시간 ≤ 400ms (최대 {mx}ms)',mx<=400,mx)
    # 2) 창 옮기면 다시 찾고, 닫히면 안 읽고, 같은 자리면 다시 찾지 않음
    w,h=pm['7']; base=mm['7']; bl=du(os.path.join(FX,'t523','bl07.png'))
    mk=lambda dx,dy,on=True:[w,h,bl,[[du(os.path.join(FX,'t520',f)),x+dx,y+dy] for f,x,y in base] if on else [],1]
    pg.evaluate("async a=>{ window._c1=await ("+COMP+")(a); }",mk(0,0)[:4]); pg.evaluate("async a=>{ window._c2=await ("+COMP+")(a); }",mk(-500,-300)[:4]); pg.evaluate("async a=>{ window._c3=await ("+COMP+")(a); }",mk(0,0,False)[:4])
    r=pg.evaluate("""async()=>{ const A=window.AR; A.bbox=null;A.bbKey='';A.prof=null;A.geo=null;A.mesoLoc=null;A.mesoLocT=0; await arProfDetect(_c1); await arMesoTpl(); let n=0; const F=window.arMesoFind; 
      const L1=arMesoLocate(_c1,1000), x1=L1.inv&&L1.inv.x; const L1b=arMesoLocate(_c1,1500); const same=L1b===L1;
      const L2=arMesoLocate(_c2,4000), x2=L2.inv&&L2.inv.x, v2=(await arMesoRead(_c2,'inv')).v;
      const L3=arMesoLocate(_c3,7000), p3=arMesoPanel(_c3,'inv'); const L4=arMesoLocate(_c3,7500); return {x1,same,x2,v2,inv3:L3.inv,p3,thr:L4===L3}; }""")
    check('같은 자리면 다시 찾지 않음(1초 판독마다 전체 찾기 안 함)',r['same'],r)
    check('창 옮기면 새 위치 찾아 읽음',r['x1'] and r['x2'] and abs(r['x1']-r['x2'])>.1 and r['v2']==V[7],r)
    check('창 닫히면 메소 칸 없음 → 읽지 않음',r['inv3'] is None and not r['p3'],r)
    check('없을 때 다시 찾기는 2초 간격(느린 주기)',r['thr'],r)
    # 3) 자동 기록 탭: 버튼 없이 0.2초 안에 표시 갱신
    pg.evaluate("""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs[0]}; const mk=(id,name)=>({id,name,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}});
      S.characters=[mk('c0','트딕이'),mk('c1','부캐하나')]; S.activeId='c0'; save(); S.tab='auto'; renderAuto(); }""")
    pg.wait_for_timeout(400)
    T=lambda s:pg.evaluate("s=>(document.querySelector(s)||{}).textContent||''",s)
    def step(js,sel,want,name):
      pg.evaluate(js); pg.wait_for_timeout(300); t=T(sel); check('버튼 없이 자동 갱신: '+name,want in t,t)
    B=pg.evaluate("BOSSES.find(b=>b.id==='jinhilla'||b.id==='seren')?.id||BOSSES[0].id"); BN=pg.evaluate(f"findBoss('{B}').name")
    step("ARX.det.cid='c1'",'.ar-cchar','부캐하나','캐릭터 정보')
    step(f"ARX.mapSt={{boss:'{B}',diff:'',kind:'w'}}; ARX.det.boss='{B}'",'.ar-cboss','-','보상 맵 아님 → -  (t603: 대기/진행 상태 없음)')
    check("t603: 대기 중/진행 중 표시 없음",'대기 중' not in T('.ar-cboss') and '진행 중' not in T('.ar-cboss'),T('.ar-cboss'))
    step(f"ARX.rew={{boss:'{B}',diff:'',hash:null}}",'.ar-cboss','보상 인식 중','보상 맵 인식(보상 인식 중)')
    check('버튼 없이 자동 갱신: 보스 이름',BN in T('.ar-cboss'),T('.ar-cboss'))
    step("ARX.runRec=[{k:Object.keys(ITEMS)[0],b:'보스',c:'부캐하나',t:'12:34'}]",'.ar-crec',pg.evaluate("ITEMS[Object.keys(ITEMS)[0]].n"),'기록 목록')
    step("ARX.amb=[{ks:Object.keys(ITEMS).slice(0,2),score:.8,via:'t'}]",'.ar-crec','직접 고르기','닮은 아이템 칩')
    step("ARX.prof={id:'1920o',lab:'1920 x 1080(최적 비율)',s:1,base:AR_PROF[1]}",'.ar-prof','1920 x 1080','해상도 표시')
    step("ARX.connErr='테스트 오류'",'.ar-sbar','테스트 오류','연결 상태줄')
    step("ARX.mesoLast={cid:'c1',inv:22564195389,sto:null}",'.ar-cchar','225억 6419만 5389','보유 메소')
    step("arLog('로그 줄 테스트')",'.ar-cset','로그 줄 테스트','디버그 로그')
    # 포커스 있는 입력은 덮어쓰지 않음 + 열린 디버그 유지
    pg.evaluate("document.querySelector('.ar-cset details').open=true; document.querySelector('.ar-cset').hidden=false"); pg.focus(".ar-cset select[name=cid]")
    pg.evaluate("arLog('또 한 줄')"); pg.wait_for_timeout(300)
    check('입력에 포커스 있으면 설정 칸은 안 덮어씀(포커스 유지)',pg.evaluate("document.activeElement&&document.activeElement.name==='cid'"))
    pg.evaluate("document.activeElement.blur()"); pg.wait_for_timeout(300)
    check('포커스 빠지면 갱신 + 열린 디버그 그대로',pg.evaluate("document.querySelector('.ar-cset details').open&&document.querySelector('.ar-cset').textContent.includes('또 한 줄')"))
    pg.evaluate("ARX.clr=null"); pg.wait_for_timeout(300); n0=pg.evaluate("window._n=0; const o=document.querySelector('.ar-cboss .ar-b'); new MutationObserver(()=>window._n++).observe(o,{childList:true,subtree:true}); 0"); pg.wait_for_timeout(1000)
    check('안 바뀌면 DOM 안 건드림(1초 동안 변경 0)',pg.evaluate("window._n")==0,pg.evaluate("window._n"))
    for th in ['dark','light']:
      pg.evaluate(f"document.documentElement.dataset.theme='{th}'"); pg.wait_for_timeout(300); pg.screenshot(path=os.path.join(OUT,f'b313_live_{th}.png'))
    b.close()
finally:
  srv.kill()
check('페이지 오류 없음',not errs,errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
