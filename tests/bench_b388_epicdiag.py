# b388: 진단 생성 실측 — (1) 감지 없는 영상/감지 영상에서 ecDiag* 호출 횟수 vs ecTick 횟수, (2) 함수별 1회 소요시간(headless Chromium, performance.now), (3) 기록 크기. 기존 CPU 프로파일 표와 별개의 미시 측정.
import os, sys, tempfile, shutil, subprocess, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr','fonts']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
for f in ['beam720.webm','flash_synth.webm']: shutil.copy(os.path.join(ROOT,'tests','fixtures','b352',f),site)
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
WRAP="""()=>{ window.CNT={tick:0,hit:0,commit:0,frames:0,out:0,ms:{hit:[],commit:[],frames:[],out:[]}}; const w=(n,k)=>{ const f=window[n]; window[n]=function(...a){ CNT[k]++; const t=performance.now(); try{ return f.apply(this,a); } finally{ CNT.ms[k].push(performance.now()-t); } }; };
  const tk=window.ecTick; window.ecTick=function(){ CNT.tick++; return tk(); }; w('ecDiagHit','hit'); w('ecDiagCommit','commit'); w('ecDiagFrames','frames'); w('ecDiagOut','out'); }"""
PLAY="""async(src)=>{ const v=document.createElement('video'); v.muted=true; v.src=src; v.playsInline=true; v.style.cssText='position:fixed;left:-9999px;width:320px'; document.body.appendChild(v); await v.play(); ARX.testSrc=v; window._v=v; return true; }"""
res={}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':1400,'height':900}); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate("ARX.video=null")
    res['build']=pg.evaluate("document.documentElement.dataset.build")
    pg.evaluate("()=>{ ARX.det={cid:'',boss:'lucid',diff:'hard',src:''}; ARX.mapSt={boss:'lucid',kind:'r',diff:'hard',t:Date.now()}; setInterval(()=>{ if(ARX.mapSt) ARX.mapSt.t=Date.now(); },1000); }")
    pg.evaluate(WRAP)
    pg.evaluate(PLAY,'flash_synth.webm'); pg.wait_for_function("_v.ended||_v.currentTime>5.5",timeout=20000)
    res['noBeam_flash']=pg.evaluate("({tick:CNT.tick,hit:CNT.hit,commit:CNT.commit,frames:CNT.frames,out:CNT.out,saved:EC.saved||0,dur:_v.currentTime})")
    pg.evaluate("()=>{ _v.pause(); ARX.testSrc=null; }"); pg.wait_for_timeout(300); pg.evaluate("()=>{ CNT.tick=CNT.hit=CNT.commit=CNT.frames=CNT.out=0; for(const k in CNT.ms) CNT.ms[k]=[]; }")
    pg.evaluate(PLAY,'beam720.webm'); t0=time.time()
    while time.time()-t0<35 and not pg.evaluate("EC.saved"): pg.wait_for_timeout(200)
    res['beam']=pg.evaluate("({tick:CNT.tick,hit:CNT.hit,commit:CNT.commit,frames:CNT.frames,out:CNT.out,saved:EC.saved||0,ms:Object.fromEntries(Object.entries(CNT.ms).map(([k,a])=>[k,a.map(x=>+x.toFixed(3))]))})")
    res['savedMeta']=pg.evaluate("ecList().then(L=>{const m=L[0];return {dgChars:JSON.stringify(m.dg).length,fullMetaChars:JSON.stringify(ecMetaOut(m)).length,lg:m.dg.lg.length}})")
    pg.evaluate("()=>{ _v.pause(); ARX.testSrc=null; }")
    # 미시 반복: 최악 입력(EC.log 45개 → lg 40개, 120프레임)으로 각 함수 2000회
    res['micro']=pg.evaluate("""()=>{ const now=performance.now()+1e6; EC.log=Array.from({length:45},(_,i)=>({t:now-1480+i*33,sc:0.612,ss:0.734,m:47.3}));
      const v={arSnap:1}, one=Array.from({length:120},(_,i)=>({t:now-1000+i*33.3})), N=2000, r={};
      const T=(k,f)=>{ for(let i=0;i<50;i++) f(); const a=performance.now(); for(let i=0;i<N;i++) f(); r[k]=+((performance.now()-a)/N*1000).toFixed(2); };
      let h,c,fr,o; T('hit_us',()=>{h=ecDiagHit(now,v,1280,720)}); const hit={t:now-30,sc:.8,kind:'shift',dg:h};
      T('commit_us',()=>{c=ecDiagCommit(now+40,hit,now-30)}); T('frames_us',()=>{fr=ecDiagFrames(one,now-30)}); T('out_us',()=>{o=ecDiagOut(c,fr)});
      r.dgChars=JSON.stringify(o).length; r.lg=o.lg.length; r.N=N; return r; }""")
    b.close()
finally:
  srv.terminate(); shutil.rmtree(site,ignore_errors=True)
print(json.dumps(res,ensure_ascii=False)); 
out=os.environ.get('B388_BENCH_OUT'); 
if out: open(out,'w').write(json.dumps(res,ensure_ascii=False,indent=1))
