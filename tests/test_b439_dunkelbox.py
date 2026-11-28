"""b439 (t679u 듄켈 보상상자가 보이는데도 미인식): 전투·보상 공용 맵의 상자 확인(arBoxGate/arBoxStep) — 합성 시계(가짜 Date.now) 시험.
 듄켈 y19 실측 모양: 상자 온전히 .80~.86 이 0.21초 → 이어서 가림·선택 테두리로 .62~.69 가 0.3초(→ 사라짐).
 예전: 온전한 그림 2번 + 0.2초 이상 + 첫 후보는 0.25초 간격(지금 0.15초) → 검사 시점에 따라 놓침. 지금: 문턱-.1 이상 '이어짐'을 인정(이어짐이 끼면 3번 이상)·검사 간격 당김.
 A y19 모양을 상자가 나타나는 시각 12가지(0~275ms, 25ms 간격, 틱은 0.1초)로 흘려 → 전부 1번 진입
 B 한 틱(60ms) 번쩍임 → 진입 0 · 문턱 아래(.69)만 2초 → 0(이어짐 혼자는 후보가 못 됨) · 온전 1번 뒤 0.6초 끊기고 .69 → 0
 C 온전한 상자가 계속 보이는 일반 보상 → 1.6초 안 진입(안 늦춤)"""
import sys,os,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
H=Path(__file__).parent; ROOT=os.environ.get('LIVE_ROOT',str(H.parent))
JS="""async ()=>{ let T=1e12; const RD=Date.now; Date.now=()=>T; const R={};
  arLockTry=()=>{}; arClrFinish=()=>{}; arMapHash=()=>null; arLivePaint=()=>{}; arBoxMsgScan=async()=>null; arSceneScore=async()=>0;
  let cur=()=>0; arSrc=()=>({currentTime:T/1000}); ARX.burstWait=async ms=>{ T+=ms; }; arBoxScore=async(src,k)=>{ ARX.boxFootSc=0; return cur(); };
  const reset=()=>{ for(const k of ['rew','rwl','box','mapSt','mapPend','lock','boxCand','boxNear','rewOff','mapDet','clr','fight']) ARX[k]=null; ARX.det={boss:'',diff:'',src:'',cid:''}; ARX.boxScanT=0; ARX.boxAcc={}; ARX.boxBusy=false; ARX.geo=null; };
  const MT='끝에 가까운 곳 <하드>';
  async function run(ms,sc,ph=0,dt=100){ reset(); arMapState(MT,T); const t0=T; let ent=0,first=null,st0=false; for(let t=0;t<=ms;t+=dt){ T=Math.max(T,t0+t); cur=()=>sc(T-t0+ph); if(t%250===0) arMapState(MT,T); await arBoxStep(null,false); const st=arBossState()==='rew'; if(st!==st0){ if(st){ ent++; if(first===null) first=t/1000; } st0=st; } } return {ent,first,box:!!ARX.box}; }
  // 전투·보상 공용 맵이어야 엄격 확인 — 맵 표에서 shared(br) 인지
  reset(); arMapState(MT,T); R.shared=!!(ARX.mapSt&&arShared(ARX.mapSt)); R.kind=ARX.mapSt&&ARX.mapSt.kind;
  const y19=t=>t<500?.4:t<720?.82:t<1000?.68:t<1400?.3:.3;           // 상자 .82 0.22초 → .68 0.28초 → 사라짐
  R.A=[]; for(let ph=0;ph<300;ph+=25) R.A.push((await run(2500,y19,ph)).ent);  // 프레임은 0.1초마다(10fps 인식 틱), 상자가 나타나는 시각만 25ms씩 밀어 12가지
  R.B1=await run(2500,t=>t>=500&&t<560?.82:.3);
  R.B2=await run(2500,t=>t>=500?.69:.3);
  R.B3=await run(3000,t=>t>=500&&t<560?.82:(t>=1200&&t<1800?.69:.3));
    R.C=await run(3000,t=>t>=300?.95:.3);
  Date.now=RD; return R; }"""
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
try:
 with sync_playwright() as p:
  br=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox']);pg=br.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}')
  pg.wait_for_function("typeof arBoxStep==='function'"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  R=pg.evaluate(JS); print(json.dumps(R,ensure_ascii=False))
  check('0 듄켈 맵은 전투·보상 공용(엄격 확인) 맵',R['shared'],R['kind'])
  check('A y19 모양(상자 온전 .22초 + 이어짐 .28초)을 검사 시작 12가지로 → 전부 진입',all(x==1 for x in R['A']),R['A'])
  check('B1 한 틱 번쩍임 → 진입 0',R['B1']['ent']==0,R['B1'])
  check('B2 문턱 아래(.69)만 2초 → 진입 0',R['B2']['ent']==0,R['B2'])
  check('B3 온전 1번 뒤 0.6초 끊기고 .69 → 진입 0',R['B3']['ent']==0,R['B3'])
  check('C 온전한 상자가 계속 보이는 보상 → 1.6초 안 진입',R['C']['ent']==1 and R['C']['first']<=1.6,R['C'])
  check('페이지 오류 0',not errs,errs[:2])
  br.close()
finally: srv.terminate()
print('PASS b439 dunkelbox' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
