"""b431 (t576u·t577u, 모든 보스): 보상 맵에서만 인식 — 합성 시퀀스(가짜 시계 0.1초 틱, 맵 이름 0.5초마다).
모든 보스의 전투·대기 맵 이름(+오독 변형)을 30초씩 읽히고 상자 점수를 흉내:
 S1 전투/대기 전용 이름 + 약한 근거(발 부분 .80, 온전 .50 = y04 세계의 경계 실측) → 보상 진입 0, 상자 찾기 0회
 S2 전투/대기 전용 이름 + 가끔 강한 오감지(.95 한 틱) → 진입 0
 S3 전투·보상 공용 이름(세렌 왕궁 메인홀 1페이즈 등) + 이펙트처럼 끊기는 약한 근거(0.4초 켜짐/0.5초 꺼짐) → 진입 0
 S4 공용 이름 + 강한 오감지 한 틱씩(1.3초 간격) → 진입 0
 S5 공용 이름 실제 보상(온전한 상자 계속 / 가려진 상자=약한 근거 계속) → 1번 진입·유지, 깜빡임 0, 1.6초 안 (b440: 가려진 상자+남은 시간 못 읽음은 6.6초 안)
 S6 보상 전용 이름 실제 보상 → 1번 진입, 0.15초 안
 S7 세렌 실제 흐름: 세계의 경계(약한 근거 10초) → 왕궁 메인홀 보상(상자) → 진입 1번, 전투 중 0번
LIVE_ROOT 로 다른 빌드(예: b430)를 돌려 전후 비교 가능(B431_REPORT=경로 에 숫자 저장)."""
import sys,os,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
H=Path(__file__).parent
ROOT=os.environ.get('LIVE_ROOT',str(H.parent))
D=json.load(open(H/'fixtures/boss_maps.json',encoding='utf-8'))
import re as _re
_A=open(H.parent/'src/autorec.js',encoding='utf-8').read()
BK={n.replace(' ',''):k for n,_,k in json.loads(_re.search(r'const AR_BMAP=(\[\[.*?\]\]);',_A).group(1))}  # 인식기 표의 종류(b/r/w) = 정답 기준
def nm(x): return x.split('：')[-1].split('<')[0].strip()
battle=[];shared=[];rewonly=[];sharedR=[]
for b in D:
  R={}
  for v in (b.get('reward') or {}).values():
    s=v[0] if isinstance(v,list) else v
    if isinstance(s,str) and '：' in s: R[nm(s)]=s.replace('<난이도>','<하드>')
  pool=[v[0] for v in (b.get('waiting') or {}).values()]
  for p in b.get('phases',[]): pool+= [v[0] if isinstance(v,list) else v for v in p.get('maps',{}).values()]
  pool=[s for s in pool if isinstance(s,str) and '：' in s and len(nm(s))>=3]
  for s in pool+list(R.values()):
    k=BK.get(nm(s).replace(' ',''))
    if not k: continue
    if s in R.values() and k=='r': rewonly.append(s)
    elif 'r' in k:
      shared.append(s)
      if s in R.values(): sharedR.append(s)
    else: battle.append(s)
def uniq(L):
  o={}
  for s in L: o.setdefault(nm(s),s)
  return list(o.values())
for n0,id0,k0 in json.loads(_re.search(r'const AR_BMAP=(\[\[.*?\]\]);',_A).group(1)):
  if 'r' not in k0 and not any(nm(x)==n0 for x in battle): battle.append('：'+n0+' <하드>')
battle=uniq(battle);shared=uniq(shared);rewonly=uniq(rewonly);sharedR=uniq(sharedR)
VS={'ㅏ':'ㅓ','ㅓ':'ㅏ','ㅗ':'ㅜ','ㅜ':'ㅗ','ㅐ':'ㅔ','ㅔ':'ㅐ','ㅣ':'ㅡ','ㅡ':'ㅣ'}
J='ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
def vow(n,i):
  c=n[i];o=ord(c)-0xAC00
  if not(0<=o<11172): return n
  a,b,f=o//588,(o%588)//28,o%28
  if J[b] not in VS: return n
  return n[:i]+chr(0xAC00+a*588+J.index(VS[J[b]])*28+f)+n[i+1:]
def vars_(s):
  r,rest=s.split('：',1); n=nm(s); t=rest[len(n):].strip() or '<하드>'
  if not r: return [f'{n} {t}', f'{vow(n,0)} {t}', f'{vow(n,len(n)-1)} {t.replace("<","").replace(">","")}', f'{vow(vow(n,1),len(n)-2)} {t}']
  return [s, f'{r[1:]} {vow(n,0)} {t}', f'{vow(n,len(n)-1)} {t.replace("<","").replace(">","")}', f'{r}{vow(vow(n,1),len(n)-2)} {t}']
JS="""async (A)=>{ const {scen}=A; let T=1e12; const RD=Date.now; Date.now=()=>T; const res=[];
  arLockTry=()=>{}; arClrFinish=()=>{}; arMapHash=()=>null; arLivePaint=()=>{}; arBoxMsgScan=async()=>null; arSceneScore=async()=>0; arBoxMsgScan.x=1;
  let full=0, foot=0, scans=0; arBoxScore=async(src,k)=>{ scans++; ARX.boxFootSc=foot; return full; };
  const reset=()=>{ for(const k of ['rew','rwl','box','mapSt','mapPend','lock','boxCand','rewOff','mapDet','clr','mapText','runDiff']) ARX[k]=null; ARX.det={boss:'',diff:'',src:'',cid:''}; ARX.boxScanT=0; ARX.boxAcc={}; ARX.mOffN=0; ARX.rewFlips=0; ARX.boxBusy=false; };
  for(const sc of scen){ reset(); scans=0; let st0=false, ent=0, flips=0, first=null; const t0=T;
    for(let i=0;i<sc.n;i++){ T+=100; const ph=sc.ph(i)||{}; full=ph.full||0; foot=ph.foot||0;
      if(i%5===0&&ph.text) { try{ ARX.mapText=ph.text; arMapState(ph.text,T); }catch(e){ res.push({id:sc.id,err:String(e)}); break; } }
      try{ await arBoxStep(null,false); }catch(e){ res.push({id:sc.id,err:'box '+String(e)}); break; }
      const st=arBossState()==='rew'; if(st!==st0){ flips++; if(st){ ent++; if(first===null) first=(T-t0)/1000; } st0=st; } }
    res.push({id:sc.id,ent,flips,first,scans,boss:ARX.det.boss}); }
  Date.now=RD; return res; }"""
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[];rep={}
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
try:
 with sync_playwright() as p:
  br=p.chromium.launch(args=['--no-sandbox']);pg=br.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}')
  pg.wait_for_function("typeof arBoxStep==='function'")
  def run(specs):
    # specs: list of (id, n, [(fromTick,text,full,foot), ...]) → 단계 함수로 직렬화
    code="(A)=>{ const S=A.map(([id,n,P])=>({id,n,ph:i=>{ let o=null; for(const p of P) if(i>=p[0]) o={text:p[1],full:p[2],foot:p[3],blip:p[4],pat:p[5]}; if(o&&o.blip){ o={...o,full:(i%o.blip===0)?.95:o.full}; } if(o&&o.pat){ o={...o,foot:(i%o.pat<4)?o.foot:0}; } return o; }})); return ("+JS+")({scen:S}); }"
    return pg.evaluate(code,specs)
  S1=[(f'S1|{v}',300,[(0,v,.5,.8)]) for s in battle for v in vars_(s)]
  S2=[(f'S2|{v}',300,[(0,v,.5,.8,13)]) for s in battle for v in vars_(s)]
  S3=[(f'S3|{v}',300,[(0,v,.5,.8,0,9)]) for s in shared for v in vars_(s)]
  S4=[(f'S4|{v}',300,[(0,v,.3,.2,13)]) for s in shared for v in vars_(s)]
  S5=[(f'S5|{s}',100,[(0,s,.95,.9)]) for s in sharedR]+[(f'S5w|{s}',100,[(0,s,.5,.8)]) for s in sharedR]
  S6=[(f'S6|{s}',100,[(0,s,.95,.9)]) for s in rewonly]
  S7=[('S7|seren',250,[(0,'세계의 경계：세계의 경계 <하드>',.5,.8),(100,'',0,0),(120,'세르니움：왕궁 메인홀 <하드>',0,0),(140,'세르니움：왕궁 메인홀 <하드>',.95,.9)])]
  R={}
  for nmS,L in [('S1',S1),('S2',S2),('S3',S3),('S4',S4),('S5',S5),('S6',S6),('S7',S7)]:
    out=run(L); R[nmS]=out
    err=[o for o in out if o.get('err')]
    ent=sum(o.get('ent',0) for o in out); fl=sum(o.get('flips',0) for o in out); scans=sum(o.get('scans',0) for o in out)
    rep[nmS]={'cases':len(out),'entries':ent,'flips':fl,'scans':scans,'err':len(err)}
    print(nmS,rep[nmS], err[:2])
  ok=lambda k: rep[k]['err']==0
  check(f'S1 전투/대기 전용 이름 {len(S1)}줄 + 약한 근거: 보상 진입 0',ok('S1') and rep['S1']['entries']==0,rep['S1'])
  check('S1 전투/대기 전용 맵에서 상자 찾기 0회(무거운 처리 없음)',rep['S1']['scans']==0,rep['S1']['scans'])
  check(f'S2 전투/대기 전용 이름 + 강한 오감지 한 틱: 진입 0',ok('S2') and rep['S2']['entries']==0,rep['S2'])
  check(f'S3 공용 이름(전투 페이즈) {len(S3)}줄 + 끊기는 약한 근거: 진입 0',ok('S3') and rep['S3']['entries']==0,rep['S3'])
  check(f'S4 공용 이름 + 강한 오감지 1.3초 간격 한 틱: 진입 0',ok('S4') and rep['S4']['entries']==0,rep['S4'])
  s5=R['S5']; lim=lambda o: 1.6 if not o['id'].startswith('S5w') else 6.6  # b440: 가려진 상자(약한 근거)+남은 시간 못 읽음 → 체력바 없는 5초 확인 뒤 (남은 시간 4:xx 읽히면 1.6초 안 = test_b440 B4)
  check(f'S5 공용 이름 실제 보상 {len(s5)}개: 1번 진입·깜빡임 0·온전한 상자 1.6초 안/가려진 상자 6.6초 안',ok('S5') and all(o['ent']==1 and o['flips']==1 and o['first']<=lim(o) for o in s5),[(o['id'],o['ent'],o['flips'],o['first']) for o in s5 if not(o['ent']==1 and o['flips']==1 and o['first']<=lim(o))] or 'all ok')
  s6=R['S6']; check(f'S6 보상 전용 이름 {len(s6)}개: 1번 진입 0.15초 안',ok('S6') and all(o['ent']==1 and o['flips']==1 and o['first']<=.15 for o in s6),[(o['id'],o['ent'],o['first']) for o in s6 if not(o['ent']==1 and o['first']<=.15)] or 'all ok')
  s7=R['S7'][0]; check('S7 세렌: 세계의 경계 10초 진입 0 → 보상 맵 상자에서 1번 진입',s7.get('ent')==1 and s7.get('flips')==1 and s7.get('first',0)>=14,s7)
  rep['bosses']=len({nm(s) for s in battle+shared}) and len(D)
  br.close()
finally: srv.terminate()
if os.environ.get('B431_REPORT'): json.dump(rep,open(os.environ['B431_REPORT'],'w'),ensure_ascii=False,indent=1)
print('PASS b431 reward gate' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
