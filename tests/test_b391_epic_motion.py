# test_b391 (t477): 에픽빔 = 사용자 첨부 GIF(16프레임×60ms) '모션' 일 때만 저장. 실제 ecDetect 에 32x18 grid 를 넣어 판정 확인.
# 양성: GIF 순서대로 진행(관측 100ms·위상 0~90ms, 속도 0.5~2배, 33ms 관측, 같은 비트맵 반복 공급). 음성: 정지 한 장·두 장 교체·역순·반복·밝기 페이드·섬광·화면 전환.
# 확정 지연 중 프리롤 보존(ecKeepFrom), 해상도 전환/입력 끊김 때 후보 초기화, mo:false 예전 판정, 비용. 사용자 영상·넥슨·로그인 없음(합성 grid 만).
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr','fonts']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
LIB="""()=>{ let seed=7; const rnd=()=>{ seed=(seed*1103515245+12345)%2147483648; return seed/2147483648; };
  const BG=new Float32Array(576).map((_,i)=>25+((i*37)%29)+((i>>5)%7)*3);
  window.T_frame=(k,opt={})=>{ const g=new Float32Array(576), a=opt.a??1, add=opt.add||0; for(let i=0;i<576;i++){ let v=BG[i]+add+(rnd()-.5)*2; if(k>0) v+=a*EC_MOT[k-1][i]; g[i]=Math.min(255,v); } return g; };
  window.T_run=(seq,opt={})=>{ /* seq(t)→{k,a,add} | null ; 관측 step ms, 위상 ph */ EC.h=[];EC.log=[];EC.mo=[];EC.lastG=null; const st=opt.step||100, hits=[]; let pin=null, last=null, nObs=0, kmax=-1e9, first=null;
    for(let t=opt.ph||0;t<(opt.dur||3200);t+=st){ const s=seq(t); const g=s&&s.same&&last?last:T_frame(s?s.k:0,s||{}); last=g; if(first!==null&&!hits.length) kmax=Math.max(kmax,ecKeepFrom(t)); const r=ecDetect(t,g); if(EC.mo.length&&!EC.last.dup&&EC.mo[EC.mo.length-1].t===t) nObs++;
      const kf=ecKeepFrom(t); if(pin===null&&EC.mo.some(q=>(q.sc.get(q.off)||{}).s>=EC.cfg.th)) pin={t,kf,first:EC.mo.find(q=>(q.sc.get(q.off)||{}).s>=EC.cfg.th).t};
      if(first===null&&pin) first=pin.first; if(r){ hits.push({...r,at:t,keep:kf,moAfter:EC.mo.length}); } }
    return {hits,pin,nObs,kmax}; };
  window.T_gif=(start,speed=1,order=null)=>t=>{ if(t<start) return null; const i=Math.floor((t-start)/(60/speed)); const o=order||[...Array(16).keys()]; if(i>=o.length) return null; const k=o[i]; return k>=1&&k<=13?{k}:{k:0}; };
  window.T_hold=(start,list)=>t=>{ let u=t-start; if(u<0) return null; for(const [k,ms] of list){ if(u<ms) return {k}; u-=ms; } return null; };
  return true; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda r:r.continue_() if r.request.url.startswith(f'http://127.0.0.1:{PORT}') else r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(700); pg.evaluate("clearInterval(EC.timer)"); pg.evaluate(LIB)
    c=pg.evaluate("({b:document.documentElement.dataset.build,n:EC_MOT.length,l:EC_MOT.every(t=>t.length===576),cfg:EC.cfg})")
    check('build b398(b391 모션 유지) · GIF 13단계 템플릿',c['b']=='b398' and c['n']==13 and c['l'],c['b'])
    cf=c['cfg']; check('기존 문턱·빈도·규격 유지 + 모션 설정',all(cf[k]==v for k,v in dict(fps=30,H0=240,H=720,th=.66,minMean=12,pre=1000,post=3000,cool=12000,gate=True,rewardOnly=True,pendMs=2000,shift=True,mo=True,moWin=1200).items()),cf)
    # EC_TPL 이 같은 GIF #3..#8 에서 나온 것인지
    r=pg.evaluate("EC_TPL.map((T,j)=>+ecNcc(EC_MOT[j+2],T).toFixed(4))"); check('EC_TPL ≈ 새 GIF #3..#8 (NCC ≥ .99)',min(r)>=.99,r)
    # 양성: 위상 0~90ms
    R=pg.evaluate("[0,10,20,30,40,50,60,70,80,90].map(ph=>T_run(T_gif(1600),{ph}))")
    ok=[len(x['hits'])==1 and x['hits'][0]['kind']=='motion' and 1600<=x['hits'][0]['t']<=1860 for x in R]
    check('GIF 순서 진행 → 위상 10개 모두 1회 감지, 시작 시각 = 첫 모션 관측(GIF 시작 +260ms 이내 — #0·#1 은 가는 줄기라 밝기 문턱 미만)',all(ok),[(x['hits'][0]['t'],x['hits'][0]['mo']) if x['hits'] else None for x in R])
    check('확정은 모션 진행 뒤(쇠퇴 단계) — 앞 단계만 보고 저장 안 함',all(x['hits'][0]['at']-x['hits'][0]['t']>=150 for x in R if x['hits']),[x['hits'][0]['at']-x['hits'][0]['t'] for x in R if x['hits']])
    check('확정 지연 중 프리롤 고정: ecKeepFrom ≤ 시작-1000ms',all(x['pin'] and x['kmax']<=x['hits'][0]['t']-1000 for x in R),[(x['kmax'],x['hits'][0]['t']) for x in R][:4])
    check('확정 직후 모션 후보 비움(같은 모션 재확정 방지)',all(x['hits'][0]['moAfter']==0 for x in R))
    for sp in (.5,.75,1.5,2.0):
        R=pg.evaluate(f"[0,25,50,75].map(ph=>T_run(T_gif(1600,{sp}),{{ph,dur:4200}}))"); check(f'속도 {sp}배 → 감지',all(len(x['hits'])==1 for x in R),[len(x['hits']) for x in R])
    R=pg.evaluate("[0,11,22].map(ph=>T_run(T_gif(1600),{ph,step:33}))"); check('33ms 관측(30fps) → 1회만',all(len(x['hits'])==1 for x in R),[len(x['hits']) for x in R])
    # 같은 비트맵 반복 공급: 단계마다 같은 객체 2번 → 새 관측 수는 고유 비트맵만
    R=pg.evaluate("T_run(t=>{ const s=T_gif(1600)(t- (t%200>=100?100:0)); return s&&(t%200>=100)?{...s,same:true}:s; })")
    check('같은 비트맵 재사용은 모션 관측으로 안 셈(감지는 실제 바뀐 프레임으로만)',R['nObs']<=8,R)
    # 음성
    neg={'정지 한 장 #3':"T_hold(1600,[[3,1500]])",'정지 한 장 #6':"T_hold(1600,[[6,1500]])",'정지 한 장 #10':"T_hold(1600,[[10,1500]])",
         '두 장 교체 #3→#10':"T_hold(1600,[[3,300],[10,300]])",'두 장 교체 #2→#9':"T_hold(1600,[[2,300],[9,300]])",'역순 재생':"T_gif(1600,1,[...Array(16).keys()].reverse())",
         '정점 반복 #6×10':"T_gif(1600,1,Array(10).fill(6))",'앞 단계 반복 #3-5':"T_gif(1600,1,[3,4,5,3,4,5,3,4,5,3,4,5])",'쇠퇴 단계 먼저 → 앞 단계(블록 역순)':"T_gif(1600,1,[9,10,11,12,2,3,4,5])",
         '같은 비트맵 정지(묵은 #4 계속)':"t=>t>=1600&&t<2600?{k:4,same:t>1600}:null",
         '밝기 페이드(전체 균일)':"t=>{ const u=(t-1600)/900; return u>=0&&u<=1?{k:0,add:Math.sin(Math.PI*u)*120}:null; }",'섬광 200ms':"t=>t>=1600&&t<1800?{k:0,add:180}:null",
         '화면 전환(밝은 장면으로 유지)':"t=>t>=1600?{k:0,add:60}:null",'정점 단계만 #5→#6':"T_hold(1600,[[5,150],[6,150]])"}
    for n,js in neg.items():
        R=pg.evaluate(f"[0,30,60,90].map(ph=>T_run({js},{{ph}}).hits.length)"); check('음성: '+n,sum(R)==0,R)
    R=pg.evaluate("[0,30,60,90].map(ph=>T_run(T_hold(1600,[[3,150],[6,150],[10,150]]),{ph}).hits.length)")
    print('INFO 알려진 한계 — 세 장 정지 #3→#6→#10(각150ms) 순서 제시는 감지됨:',R)
    # 입력 정체성 초기화: 같은 해상도 소스 교체 / 스트림 교체 / null 못 본 stop→start(세대) / 해상도 전환 / 입력 끊김. 비트맵이 매 tick 바뀌는 것과 혼동 금지(같은 소스 유지 땐 초기화 0)
    SW="""(kind)=>{ const mk=(w,h)=>{ const c=document.createElement('canvas'); c.width=w; c.height=h; c.getContext('2d').fillRect(0,0,w,h); return c; };
      const o=window.ecDetect; window.ecDetect=()=>null; ARX.video=null; ARX.stream=null; ARX.startGen=5; let A=mk(640,360); ARX.testSrc=A; ecTick(); const r0=EC.srcResets||0;
      const seed=()=>{ EC.mo=[{t:Date.now(),m:30,D:new Float32Array(576),sc:new Map([['0,0',{k:3,s:.9}]]),k:3,s:.9,off:'0,0'}]; EC.lastG=new Float32Array(576); EC.h=[{t:Date.now(),g:new Float32Array(576)}];
        EC.pend={t:Date.now()-100,sc:.9,kind:'motion'}; EC.cur={t0:Date.now()-200,w:640,h:360,boss:'x'}; const fr=new VideoFrame(mk(640,360),{timestamp:1}); ECV.frames.push({t:Date.now(),f:fr}); return fr; };
      ecTick(); ecTick(); const same=(EC.srcResets||0)-r0; const fr=seed();
      if(kind==='elem') ARX.testSrc=mk(640,360); else if(kind==='stream') ARX.stream={id:'s2'}; else if(kind==='gen') ARX.startGen=7; else if(kind==='res') A.height=300; else if(kind==='none'){}
      ecTick(); let closed=false; try{ fr.clone().close(); }catch(e){ closed=true; }
      const out={same,reset:(EC.srcResets||0)-r0-same,mo:EC.mo.length,lastG:EC.lastG===null,h:EC.h.length,pend:EC.pend,cur:EC.cur,frames:ECV.frames.length,closed}; window.ecDetect=o; EC.mo=[];EC.pend=null;EC.cur=null;ECV.frames.forEach(x=>x.f.close());ECV.frames=[]; ARX.testSrc=null; ARX.stream=null; ecTick(); return out; }"""
    for kind,name in (('elem','같은 해상도 영상 소스 교체'),('stream','같은 요소·해상도에서 스트림 교체'),('gen','null 을 못 본 stop→start(연결 세대 증가, 같은 요소)'),('res','해상도 전환')):
        r=pg.evaluate(SW,kind)
        check('입력 교체 초기화: '+name+' → 배경·모션 후보·대기·저장 대기·소유 프레임(close) 비움',r['same']==0 and r['reset']==1 and r['mo']==0 and r['lastG'] and r['pend'] is None and r['cur'] is None and r['closed'] and r['frames']<=1,r)
    r=pg.evaluate(SW,'none'); check('같은 소스 유지(비트맵만 매 tick 새로) → 초기화 안 함, 후보·대기·클립 유지',r['same']==0 and r['reset']==0 and r['mo']==1 and r['pend'] and r['cur'] and not r['closed'],r)
    r=pg.evaluate("""()=>{ const mk=()=>{ const c=document.createElement('canvas'); c.width=640; c.height=360; return c; }; const o=window.ecDetect, oa=window.arSrc; window.ecDetect=()=>null;
      ARX.testSrc=null; ARX.stream={id:'live'}; ARX.startGen=9; ARX.video=mk(); window.arSrc=()=>{ const b=mk(); b.arSnap=1; return b; }; /* 실제 arSrc 처럼 매 tick 새 비트맵 객체 */
      ecTick(); const r0=EC.srcResets||0; EC.mo=[{t:Date.now(),m:30,D:new Float32Array(576),sc:new Map(),k:3,s:.9,off:'0,0'}]; EC.pend={t:Date.now(),sc:.9};
      for(let i=0;i<5;i++) ecTick(); const out={resets:(EC.srcResets||0)-r0,mo:EC.mo.length,pend:!!EC.pend};
      window.arSrc=oa; window.ecDetect=o; EC.mo=[]; EC.pend=null; ARX.video=null; ARX.stream=null; ecTick(); return out; }""")
    check('라이브 경로: 같은 ARX.video·스트림·세대에서 arSrc 비트맵 객체만 매 tick 바뀜 → 초기화 0',r['resets']==0 and r['mo']==1 and r['pend'],r)
    r=pg.evaluate("""()=>{ const c=document.createElement('canvas'); c.width=640;c.height=360; ARX.video=null; ARX.testSrc=c; ecTick(); EC.mo=[{t:1,m:30,D:new Float32Array(576),sc:new Map(),k:3,s:.9,off:'0,0'}]; EC.buf.push({t:Date.now()}); ARX.testSrc=null; ecTick(); return {mo:EC.mo.length,lastG:EC.lastG,src:EC.src}; }""")
    check('입력 끊김 → 모션 후보 초기화',r['mo']==0 and r['lastG'] is None and r['src'] is None,r)
    # 혼합 방지 끝단: 소스 A 의 앞·정점 단계 뒤 소스 교체 → 소스 B 의 쇠퇴 단계만으로는 확정 안 됨 (대조: 교체 없으면 확정)
    MIX="""(sw)=>{ const mk=()=>{ const c=document.createElement('canvas'); c.width=640;c.height=360; return c; }; ARX.video=null; ARX.stream=null; ARX.testSrc=mk(); const o=window.ecDetect; window.ecDetect=()=>null; ecTick(); window.ecDetect=o;
      EC.h=[];EC.log=[];EC.mo=[];EC.lastG=null; const f=T_gif(1600); let hit=null;
      for(let t=0;t<3200&&!hit;t+=100){ if(t===2000){ window.ecDetect=()=>null; if(sw) ARX.testSrc=mk(); ecTick(); window.ecDetect=o; if(sw){ for(let u=600;u<=1500;u+=100) ecDetect(t-1600+u-1000+400, T_frame(0)); } } const s=f(t); const r=ecDetect(t,T_frame(s?s.k:0,s||{})); if(r) hit=r; }
      ARX.testSrc=null; window.ecDetect=()=>null; ecTick(); window.ecDetect=o; return hit; }"""
    r0=pg.evaluate(MIX,False); r1=pg.evaluate(MIX,True)
    check('대조: 같은 소스 유지 → 그 모션 확정',bool(r0) and r0.get('kind')=='motion',r0)
    check('소스 교체 뒤 새 소스 쇠퇴 단계만 → 예전 소스 앞·정점과 합쳐 확정 안 함',r1 is None,r1)
    # mo:false 예전 판정(설정으로만): 정지 #3 두 번 hit 이면 예전처럼 감지
    r=pg.evaluate("()=>{ EC.cfg.mo=false; const x=T_run(T_hold(1600,[[3,1500]])).hits.length; EC.cfg.mo=true; return x; }"); check('mo:false 는 예전 정지 판정 그대로(되돌림 경로)',r>=1,r)
    # 비용: 새 판정 vs 예전 판정(같은 입력)
    r=pg.evaluate("""()=>{ const go=mo=>{ EC.cfg.mo=mo; let tot=0,n=0,mx=0; for(let rep=0;rep<15;rep++){ EC.h=[];EC.log=[];EC.mo=[];EC.lastG=null; for(let t=0;t<3200;t+=33){ const s=T_gif(1600)(t), g=T_frame(s?s.k:0,s||{}); const a=performance.now(); ecDetect(t,g); const d=performance.now()-a; tot+=d; n++; if(d>mx) mx=d; } } EC.cfg.mo=true; return {mean:+(tot/n*1000).toFixed(1),max:+mx.toFixed(2)}; };
      go(false); go(true); return {old:go(false),neu:go(true)}; }""")
    print('INFO ecDetect µs/호출(평균) 예전',r['old'],'새',r['neu'])
    check('추가 비용 제한: 평균 ≤ 예전×2 + 150µs',r['neu']['mean']<=r['old']['mean']*2+150,r)
    check('JS 오류 없음',not errs,errs)
    b.close()
finally:
    srv.terminate()
print('RESULT','OK' if not fails else 'FAIL '+','.join(fails)); sys.exit(1 if fails else 0)
