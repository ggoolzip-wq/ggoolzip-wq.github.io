"""b440 (pt702u, 전투·보상 이름 공용 9보스): 체력바 없는 전투(시작 직후·체력바 공백)에서 보상 맵 오인식 막기.
 A 실제 화면(박스 영상, 없으면 건너뜀): '남은 시간' 읽기 — 보상 화면(영상마다 2장)은 5:02 넘게 읽힘 0,
   전투 화면(z01 세렌·z04 듄켈·z05 윌·z03 진힐라 체력바 있는 구간)은 5:02 이하로 읽힘 0 + 절반 넘게 읽힘.
 B 합성 흐름(가짜 시계, arTimerScan 흉내): B1 전투 시간(18분)+체력바 없음+약한 근거 10초 → 진입 0 /
   B2 체력바 잠금 → 검은 화면(연출) → 체력바 없음 10초(18분) → 0 / B3 남은 시간 못 읽음 → 5초 전엔 0, 7초 안 진입 /
   B4 보상 시간(4:50)+약한 근거 → 1.6초 안 진입(안 늦춤) / B5 온전한 상자 4:50 → 1.6초 안 · 18분(1초 읽은 뒤) → 0 /
   B6 처치(18분→4:57) 뒤 검은 화면 전 → 0, 검은 화면 뒤 → 진입 / B7 fightGate=false → 예전처럼 진입."""
import sys,os,subprocess,json,base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
H=Path(__file__).parent; ROOT=os.environ.get('LIVE_ROOT',str(H.parent))
VD=Path(os.environ.get('LIVE_VIDDIR','/workspace/reward_live_set/vids'))
FIGHT=[('z01',t) for t in (1,3,7,11,15,19,23,27)]+[('z04',t) for t in (1,3,5,7,9)]+[('z05',t) for t in (1,3,5,7,9,11)]+[('z03',t) for t in (1,3,5,7)]
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(f)]).decode())
def grab(f,t):
  o=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(f),'-frames:v','1','-f','image2pipe','-vcodec','png','-'],capture_output=True).stdout
  return 'data:image/png;base64,'+base64.b64encode(o).decode() if o else None
frames=[]
if VD.exists():
  REW={'z02':[20,25],'z03':[18,24],'z04':[17,22],'z05':[20,26]}
  for v in sorted(VD.glob('*.mp4')):
    id=v.stem
    if id=='z01' or id.startswith('s0'): continue
    ts=REW.get(id) or [round(dur(v)*.6,2),round(dur(v)-.6,2)]
    for t in ts: frames.append(('rew',id,t))
  for id,t in FIGHT: frames.append(('fight',id,t))
JSA="""async (L)=>{ const out=[]; for(const [kind,id,t,url] of L){ const b=await (await fetch(url)).blob(); const bm=await createImageBitmap(b); ARX.geo=null;
  const r=arTimerScan(bm); out.push([kind,id,t,r?r.sec:null]); bm.close(); } return out; }"""
JSB="""async (url)=>{ let T=1e12; const RD=Date.now; Date.now=()=>T; const R={};
  arLockTry=()=>{}; arClrFinish=()=>{}; arMapHash=()=>null; arLivePaint=()=>{}; arBoxMsgScan=async()=>null; arSceneScore=async()=>0;
  let full=0, foot=0, tm=null, hp=false, dk=false; arBoxScore=async(src,k)=>{ ARX.boxFootSc=foot; return full; };
  arTimerScan=()=>tm==null?null:{sec:tm,DH:40}; arHpBarScan=()=>hp?{T:1}:null; arDarkScan=()=>dk;
  const reset=()=>{ for(const k of ['rew','rwl','box','mapSt','mapPend','lock','boxCand','rewOff','mapDet','clr','fight','fq','tmLast']) ARX[k]=null; ARX.tmFight=0; ARX.tmRew=0; ARX.tmKill=0; ARX.tmT=0; ARX.det={boss:'',diff:'',src:'',cid:''}; ARX.boxScanT=0; ARX.boxAcc={}; ARX.boxBusy=false; ARX.fightBarT=0; ARX.geo=null; ARX.cfg.fightGate=true; };
  const MT='세르니움：왕궁 메인홀 <하드>', SRC={width:1920,height:1080};
  async function run(n,fn){ let ent=0,st0=false,first=null; const t0=T; for(let i=0;i<n;i++){ T+=100; const o=fn(i)||{}; full=o.full||0; foot=o.foot||0; tm=o.tm===undefined?null:o.tm; hp=!!o.hp; dk=!!o.dk; if(i%5===0) arMapState(MT,T); arFightWatch(SRC); await arBoxStep(null,false); const st=arBossState()==='rew'; if(st!==st0){ if(st){ ent++; if(first===null) first=(T-t0)/1000; } st0=st; } } return {ent,first,st:st0}; }
  const sec=(s0,i)=>s0-Math.floor(i/10);
  reset(); arMapState(MT,T); R.b1=await run(100,i=>({tm:sec(1100,i),foot:.8,full:.5}));
  reset(); arMapState(MT,T); R.b2=await run(110,i=>i<10?{hp:true,tm:sec(1100,i),foot:.8,full:.5}:i<14?{dk:true}:{tm:sec(1090,i),foot:.8,full:.5});
  reset(); arMapState(MT,T); R.b3=await run(70,i=>({foot:.8,full:.5}));
  reset(); arMapState(MT,T); R.b4=await run(30,i=>({tm:sec(290,i),foot:.8,full:.5}));
  reset(); arMapState(MT,T); R.b5a=await run(30,i=>({tm:sec(290,i),full:.95,foot:.9}));
  reset(); arMapState(MT,T); R.b5b=await run(60,i=>i<10?{tm:sec(1100,i)}:{tm:sec(1100,i),full:.95,foot:.9}); /* 남은 시간을 1초 읽은 뒤 */
  reset(); arMapState(MT,T); R.b6a=await run(100,i=>i<20?{tm:sec(1100,i)}:{tm:sec(297,i),foot:.8,full:.5}); R.b6b=await run(40,i=>i<4?{dk:true}:{tm:sec(290,i),foot:.8,full:.5});
  reset(); ARX.cfg.fightGate=false; arMapState(MT,T); R.b7=await run(30,i=>({tm:sec(1100,i),foot:.8,full:.5})); ARX.cfg.fightGate=true;
  Date.now=RD; return R; }"""
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
try:
 with sync_playwright() as p:
  br=p.chromium.launch(args=['--no-sandbox']);pg=br.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}')
  pg.wait_for_function("typeof arTimerScan==='function'")
  if frames and not os.environ.get('SKIP_A'):
    L=[[k,id,t,grab(VD/f'{id}.mp4',t)] for k,id,t in frames]; L=[x for x in L if x[3]]
    out=[]
    for i in range(0,len(L),10): out+=pg.evaluate(JSA,L[i:i+10])
    rw=[o for o in out if o[0]=='rew']; fi=[o for o in out if o[0]=='fight']
    rr=[o for o in rw if o[3] is not None]; fr=[o for o in fi if o[3] is not None]
    check(f'A1 보상 화면 {len(rw)}장(영상 {len({o[1] for o in rw})}개) 5:02 넘게 읽힘 0 (읽음 {len(rr)}장)',not any(o[3]>302 for o in rr),[o[:4] for o in rr if o[3]>302] or 0)
    check(f'A2 전투 화면 {len(fi)}장 5:02 이하로 읽힘 0, 절반 넘게 읽음 ({len(fr)}장)',not any(o[3]<=302 for o in fr) and len(fr)*2>len(fi),[o[:4] for o in fi if o[3] is None or o[3]<=302])
  else: print('SKIP A')
  R=pg.evaluate(JSB,''); print(json.dumps(R,ensure_ascii=False))
  check('B1 전투 시간(18분)·체력바 없음·약한 근거 10초 → 진입 0',R['b1']['ent']==0,R['b1'])
  check('B2 체력바 잠금 → 검은 화면 → 체력바 없음 10초(18분) → 진입 0',R['b2']['ent']==0,R['b2'])
  check('B3 남은 시간 못 읽음 → 5초 전 진입 0, 7초 안 진입',R['b3']['ent']==1 and 5<=R['b3']['first']<=7,R['b3'])
  check('B4 보상 시간(4:50)+약한 근거 → 1.6초 안 진입',R['b4']['ent']==1 and R['b4']['first']<=1.6,R['b4'])
  check('B5 온전한 상자: 4:50 → 1.6초 안 / 18분 → 0',R['b5a']['ent']==1 and R['b5a']['first']<=1.6 and R['b5b']['ent']==0,[R['b5a'],R['b5b']])
  check('B6 처치(18분→4:57) 뒤 검은 화면 전 0, 검은 화면 뒤 진입',R['b6a']['ent']==0 and R['b6b']['ent']==1,[R['b6a'],R['b6b']])
  check('B7 fightGate=false → 예전처럼 진입',R['b7']['ent']==1,R['b7'])
  br.close()
finally: srv.terminate()
print('PASS b440 timer gate' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
