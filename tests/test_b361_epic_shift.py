# test_b361 (t671): 위치가 옮겨진 에픽빔(캐릭터 위치에서 터짐) — shifted NCC; 그리고 (기본 꺼짐) 국소 세로 빛기둥 에픽빔(미트라형) 감지 — 합성 240p 프레임으로 ecPillar: 좁고 긴 새 흰 기둥 3프레임 → 감지, 넓은 기둥·짧은 기둥·색깔 기둥·원래 있던 기둥·화면 전체 섬광 → 미감지.
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr','fonts']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
RUN="""(sp)=>{ const W=426,H=240, cv=document.createElement('canvas'); cv.width=W; cv.height=H; const g=cv.getContext('2d',{willReadFrequently:true});
  EC.ph=[]; EC.pl=[]; let hit=null, t=1e6, mx=0;
  for(let i=0;i<40;i++){ g.fillStyle='#3a4a5a'; g.fillRect(0,0,W,H); g.fillStyle='#806040'; g.fillRect(0,170,W,70); for(let k=0;k<30;k++){ g.fillStyle=`rgb(${(k*37)%200},${(k*91)%200},${(k*53)%200})`; g.fillRect((k*53+i*3)%W,(k*29)%H,12,12); }
    const on=i>=20&&i<30;
    if(sp.static||on){ g.fillStyle=sp.col||'#fafafa'; if(sp.flash) g.fillRect(0,0,W,H); else g.fillRect(sp.x,sp.y0,sp.w,sp.h); }
    const r=ecPillar(t,g.getImageData(0,0,W,H).data,W,H); if(EC.lastPil) mx=Math.max(mx,EC.lastPil.sc); if(r&&!hit) hit={i,x:r.x,sc:r.sc,kind:r.kind}; t+=100; }
  return {hit,mx}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(600)
    check('config', pg.evaluate("EC.cfg.pil===false&&EC.cfg.shift===true&&EC.cfg.sTh===.77&&EC.cfg.sN===2&&EC.cfg.pilTh===.88"))
    r=pg.evaluate("""()=>{ const T=EC_TPL[0], D=new Float32Array(576); for(let y=0;y<18;y++) for(let x=0;x<32;x++){ const sx=x-7, sy=y-2; D[y*32+x]=(sx>=0&&sx<32&&sy>=0&&sy<18)?T[sy*32+sx]:0; }
      return {sc:Math.max(...EC_TPL.map(t=>ecNcc(D,t))), ss:ecNccShift(D)}; }""")
    check('beam template shifted (+7,+2) → fixed NCC low, shifted NCC ≥.95', r['sc']<.7 and r['ss']>=.95, r)
    r=pg.evaluate("""()=>{ EC.log=[]; EC.h=[]; const mk=(t,ss)=>EC.log.push({t,sc:.3,ss,m:30}); mk(0,.55); mk(100,.8); mk(200,.78);
      const a=ecDetect(300,new Float32Array(576)); return true; }""")
    r=pg.evaluate("""()=>{ const T=EC_TPL[0], D=new Float32Array(576); for(let y=0;y<18;y++) for(let x=0;x<32;x++){ const sx=x-7, sy=y-2; D[y*32+x]=(sx>=0&&sx<32&&sy>=0&&sy<18)?T[sy*32+sx]:0; }
      EC.h=[]; EC.log=[]; const z=new Float32Array(576).fill(20); const out=[]; for(let i=0;i<14;i++) out.push(!!ecDetect(i*100,z)); for(let i=14;i<16;i++){ const g=new Float32Array(576); for(let k=0;k<576;k++) g[k]=20+D[k]; out.push(ecDetect(i*100,g)); } return {r:out.slice(14), ss:EC.last.ss, sc:EC.last.sc}; }""")
    # b391 (t477): 감지 기준이 '정지 모양 2회' → '사용자 GIF 모션 진행' 으로 바뀜. 옮겨진 정지 템플릿 2프레임은 이제 감지하면 안 됨(의도된 변경).
    check('b391: off-center 정지 템플릿 2프레임 → 모션 아님(미감지), shift 점수는 그대로 계산', r['r'][0] is None and r['r'][1] is None and r['ss']>=.95, r)
    r=pg.evaluate("""()=>{ EC.h=[]; EC.log=[]; EC.mo=[]; EC.lastG=null; const z=()=>{ const g=new Float32Array(576); for(let k=0;k<576;k++) g[k]=20+(k%7)*.3; return g; }; let hit=null;
      for(let i=0;i<16;i++) ecDetect(i*100,z());
      for(let i=0;i<14&&!hit;i++){ const t=1600+i*100, k=Math.floor(i*100/60); if(k<1||k>13){ ecDetect(t,z()); continue; } const T=EC_MOT[k-1], g=z();
        for(let y=0;y<18;y++) for(let x=0;x<32;x++){ const sx=x-6, sy=y-2; if(sx>=0&&sx<32&&sy>=0&&sy<18) g[y*32+x]+=T[sy*32+sx]; } hit=ecDetect(t,g); }
      return hit; }""")
    check('b391: 옮겨진(+6,+2) GIF 모션 진행 → 같은 위치에서 감지(kind motion)', bool(r) and r.get('kind')=='motion' and r['mo']['off']!='0,0', r)
    r=pg.evaluate("()=>{ EC.cfg.mo=false; EC.h=[]; EC.log=[]; const T=EC_TPL[0], D=new Float32Array(576); for(let y=0;y<18;y++) for(let x=0;x<32;x++){ const sx=x-7, sy=y-2; D[y*32+x]=(sx>=0&&sx<32&&sy>=0&&sy<18)?T[sy*32+sx]:0; } const z=new Float32Array(576).fill(20); for(let i=0;i<14;i++) ecDetect(i*100,z); const out=[]; for(let i=14;i<16;i++){ const g=new Float32Array(576); for(let k=0;k<576;k++) g[k]=20+D[k]; out.push(ecDetect(i*100,g)); } EC.cfg.mo=true; return out; }")
    check('mo:false(되돌림 설정)에서는 예전 shift 규칙 그대로', r[0] is None and r[1] and r[1].get('kind')=='shift', r)
    pg.evaluate("EC.cfg.pil=true")
    r=pg.evaluate(RUN,{'x':90,'y0':0,'w':3,'h':200})
    check('narrow tall new pillar → detected after 3 frames', bool(r['hit']) and r['hit']['i']==22 and abs(r['hit']['x']-91)<=2 and r['hit']['kind']=='pillar', r)
    for name,sp in [('wide pillar (24px)',{'x':90,'y0':0,'w':24,'h':200}),('short pillar (40%)',{'x':90,'y0':60,'w':3,'h':80}),
                    ('colored pillar',{'x':90,'y0':0,'w':3,'h':200,'col':'#ff4040'}),('static pillar (in background)',{'x':90,'y0':0,'w':3,'h':200,'static':1}),
                    ('full-screen flash',{'flash':1,'x':0,'y0':0,'w':0,'h':0}),('edge column',{'x':421,'y0':0,'w':3,'h':200})]:
        r=pg.evaluate(RUN,sp); check(name+' → not detected', not r['hit'], r)
    b.close()
finally:
    srv.terminate(); shutil.rmtree(site,ignore_errors=True)
check('no page errors', not errs, errs)
print('RESULT', 'FAIL' if fails else 'PASS', fails); sys.exit(1 if fails else 0)
