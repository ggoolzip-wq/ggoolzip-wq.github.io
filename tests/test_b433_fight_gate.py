"""b433 (t579 z01·z05, 모든 보스): 전투 신호(보스 체력바) → 전투·보상 이름 공용 맵에서 보상 진입 막기.
 A 실제 화면(박스 영상, 없으면 건너뜀): 체력바 있는 전투 프레임(1920·1376 창 테두리) 전부 감지, 보상 화면 프레임 감지 0,
   맵 이동 검은 화면 감지 · 보통 화면 검은 화면 오감지 0.
 B 합성 흐름(가짜 시계): 공용 맵 + 전투 잠금 + 약한 근거 3초 → 진입 0 / 검은 화면 뒤 → 1번 진입 /
   보상 래치 중 체력바 1초 넘게 → 해제 / 잠금 없는 공용 맵 실제 보상 → 그대로 1.6초 안 진입 (정상 진입 안 늦춤)."""
import sys,os,subprocess,json,base64,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
H=Path(__file__).parent; ROOT=os.environ.get('LIVE_ROOT',str(H.parent))
VD=Path(os.environ.get('LIVE_VIDDIR','/workspace/reward_live_set/vids'))
POS=[('z01',1.5),('z01',15),('z01',24),('z03',3),('z04',4),('z05',1),('z05',6.9),('z02',5),('n1',0.5),('y03',1),('x02',1),('v03',1)]
DARK=[('z02',15.5),('z03',14.35),('z04',12.9),('z05',17.5)]
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(f)]).decode())
def grab(f,t):
  o=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(f),'-frames:v','1','-q:v','3','-f','image2pipe','-vcodec','mjpeg','-'],capture_output=True).stdout
  return 'data:image/jpeg;base64,'+base64.b64encode(o).decode() if o else None
def lum(f,t):  # 테스트 쪽 독립 밝기(16×9 평균) — 영상 끝 실제 검은 화면(맵 나감)은 '보통 화면'에서 뺌
  o=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(f),'-frames:v','1','-vf','scale=16:9,format=gray','-f','rawvideo','-'],capture_output=True).stdout
  return sum(o)/max(1,len(o))
frames=[]
if VD.exists():
  REW={'z02':[20,25],'z03':[18,24],'z04':[17,22],'z05':[20,26]}
  for v in sorted(VD.glob('*.mp4')):
    id=v.stem
    if id=='z01': continue
    ts=REW.get(id) or [round(dur(v)*.6,2),round(dur(v)-.6,2)]
    for t in ts: frames.append(('neg',id,t))
  for id,t in POS: frames.append(('pos',id,t))
  for id,t in DARK: frames.append(('dark',id,t))
JSA="""async (L)=>{ const out=[]; for(const [kind,id,t,url] of L){ const b=await (await fetch(url)).blob(); const bm=await createImageBitmap(b); ARX.geo=null;
  const hp=arHpBarScan(bm), dk=arDarkScan(bm); out.push([kind,id,t,!!hp,dk,bm.width]); bm.close(); } return out; }"""
JSB="""async (url)=>{ let T=1e12; const RD=Date.now; Date.now=()=>T; const R={};
  arLockTry=()=>{}; arClrFinish=()=>{}; arMapHash=()=>null; arLivePaint=()=>{}; arBoxMsgScan=async()=>null; arSceneScore=async()=>0;
  let full=0, foot=0; arBoxScore=async(src,k)=>{ ARX.boxFootSc=foot; return full; };
  const bat=await createImageBitmap(await (await fetch(url)).blob()); const dark=document.createElement('canvas'); dark.width=1920; dark.height=1080; dark.getContext('2d').fillRect(0,0,1920,1080);
  const reset=()=>{ for(const k of ['rew','rwl','box','mapSt','mapPend','lock','boxCand','rewOff','mapDet','clr','fight']) ARX[k]=null; ARX.det={boss:'',diff:'',src:'',cid:''}; ARX.boxScanT=0; ARX.boxAcc={}; ARX.boxBusy=false; ARX.fightBarT=0; ARX.geo=null; };
  const MT='세르니움：왕궁 메인홀 <하드>';
  async function run(n,fn){ let ent=0,st0=false,first=null; const t0=T; for(let i=0;i<n;i++){ T+=100; const o=fn(i)||{}; full=o.full||0; foot=o.foot||0; if(i%5===0) arMapState(MT,T); if(o.src) arFightWatch(o.src); await arBoxStep(null,false); const st=arBossState()==='rew'; if(st!==st0){ if(st){ ent++; if(first===null) first=(T-t0)/1000; } st0=st; } } return {ent,first,st:st0}; }
  reset(); arMapState(MT,T);
  // B1 전투 프레임(체력바) 0.5초 + 약한 근거 3초 → 진입 0
  R.b1=await run(35,i=>i<5?{src:bat,foot:.8,full:.5}:{foot:.8,full:.5}); R.b1.fight=!!(ARX.fight&&ARX.fight.n>=2);
  // B2 검은 화면(맵 이동) → 잠금 풀림 → 실제 보상(가려진 상자=약한 근거) 진입 1번
  R.b2=await run(30,i=>i<3?{src:dark}:{foot:.8,full:.5}); R.b2.fight=!!ARX.fight;
  // B3 보상 래치 중 체력바 1.2초 → 해제
  R.b3=await run(15,i=>({src:bat})); R.b3.rew=arBossState()==='rew';
  // B4 잠금 없는 공용 맵 실제 보상 → 1.6초 안 (b431과 같음)
  reset(); arMapState(MT,T); R.b4=await run(30,i=>({full:.95,foot:.9}));
  Date.now=RD; return R; }"""
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
try:
 with sync_playwright() as p:
  br=p.chromium.launch(args=['--no-sandbox']);pg=br.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}')
  pg.wait_for_function("typeof arHpBarScan==='function'")
  if frames:
    L=[]; LUM={}
    for k,id,t in frames:
      u=grab(VD/f'{id}.mp4',t)
      if u: L.append([k,id,t,u]); LUM[(id,t)]=lum(VD/f'{id}.mp4',t)
    out=[]
    for i in range(0,len(L),20): out+=pg.evaluate(JSA,L[i:i+20])
    pos=[o for o in out if o[0]=='pos']; neg=[o for o in out if o[0]=='neg']; dk=[o for o in out if o[0]=='dark']
    check(f'A1 체력바 전투 프레임 {len(pos)}장 전부 감지(1920·1376)',all(o[3] for o in pos),[o[:3] for o in pos if not o[3]] or 'all')
    check(f'A2 보상 화면 {len(neg)}장(영상 {len({o[1] for o in neg})}개) 체력바 오감지 0',not any(o[3] for o in neg),[o[:3] for o in neg if o[3]] or 0)
    check(f'A3 맵 이동 검은 화면 {len(dk)}장 감지',all(o[4] for o in dk),[o[:3] for o in dk if not o[4]] or 'all')
    nm_=[o for o in pos+neg if LUM.get((o[1],o[2]),0)>=40]; blk=[o for o in neg if LUM.get((o[1],o[2]),99)<5]  # 완전 검은 화면만 (y04 14.85 = 흐려진 컷신 화면, 평균 6: 맵 이동 아님)
    check(f'A4 보통 화면(밝기 40 이상) {len(nm_)}장 검은 화면 오감지 0',not any(o[4] for o in nm_),[o[:3] for o in nm_ if o[4]] or 0)
    check(f'A5 영상 끝 실제 검은 화면 {len(blk)}장 감지',all(o[4] for o in blk),[o[:3] for o in blk if not o[4]] or 'all')
  else: print('SKIP A (영상 없음)')
  u=grab(VD/'z01.mp4',1.5) if (VD/'z01.mp4').exists() else None
  if u:
    R=pg.evaluate(JSB,u); print(json.dumps(R,ensure_ascii=False))
    check('B1 전투 잠금 중 약한 근거 3초 → 보상 진입 0',R['b1']['fight'] and R['b1']['ent']==0,R['b1'])
    check('B2 맵 이동 검은 화면 뒤 실제 보상 → 1번 진입, 잠금 풀림',R['b2']['ent']==1 and not R['b2']['fight'],R['b2'])
    check('B3 보상 래치 중 체력바 1초 넘게 → 보상 인식 해제',not R['b3']['rew'],R['b3'])
    check('B4 잠금 없는 공용 맵 실제 보상 → 1.6초 안 진입(안 늦춤)',R['b4']['ent']==1 and R['b4']['first']<=1.6,R['b4'])
  else: print('SKIP B (z01 없음)')
  br.close()
finally: srv.terminate()
print('PASS b433 fight gate' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
