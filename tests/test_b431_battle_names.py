"""b431 (t576u·t577u): 모든 보스 전투·대기 맵 이름(+OCR 오독 변형)이 보상 맵으로 판정되는 일 0회.
tests/fixtures/boss_maps.json 의 모든 보스 대기·페이즈 맵 이름 중 보상 맵 이름과 다른 것(=보상 아님)을 모아
자모 변형(모음·자음 혼동, 받침 빠짐, 글자 빠짐, 지역명 빠짐/붙음, 난이도 꼬리 변형, 잡글)으로 arDetectBMap 에 넣고
결과가 보상 맵(kind 에 r)이면 실패. 같은 이름을 전투·보상이 함께 쓰는 맵(세렌 왕궁 메인홀 등)은 이름만으로 구분 불가 → test_b431_reward_gate(상자 근거) 가 맡음."""
import sys,subprocess,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
H=Path(__file__).parent
D=json.load(open(H/'fixtures/boss_maps.json',encoding='utf-8'))
import re as _re
_A=open(H.parent/'src/autorec.js',encoding='utf-8').read()
BK={n.replace(' ',''):k for n,_,k in json.loads(_re.search(r'const AR_BMAP=(\[\[.*?\]\]);',_A).group(1))}  # 인식기 표의 종류(b/r/w) = 정답 기준
def nm(x): return x.split('：')[-1].split('<')[0].strip()
def reg(x): return x.split('：')[0].strip() if '：' in x else ''
def tag(x): return x[x.index('<'):].strip() if '<' in x else ''
src=[]  # (전체 이름, 보스)
for b in D:
  R=set()
  rw=b.get('reward') or {}
  for v in rw.values():
    s=v[0] if isinstance(v,list) else v
    if isinstance(s,str) and '：' in s: R.add(nm(s))
  pool=[]
  for v in (b.get('waiting') or {}).values(): pool.append(v[0])
  for p in b.get('phases',[]):
    for v in p.get('maps',{}).values(): pool.append(v[0] if isinstance(v,list) else v)
  for s in pool:
    if isinstance(s,str) and '：' in s and len(nm(s))>=3 and nm(s) not in R and 'r' not in BK.get(nm(s).replace(' ',''),'r'): src.append((s,b['boss']))
for n0,id0,k0 in json.loads(_re.search(r'const AR_BMAP=(\[\[.*?\]\]);',_A).group(1)):
  if 'r' not in k0 and not any(nm(x)==n0 for x,_ in src): src.append((n0+' <하드>',id0))  # 표에만 있는 전투 맵(대적자·카링·벨로나·림보·발드릭스 페이즈)
src=sorted(set(src))
CHO='ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'; JUNG='ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
VS={'ㅏ':'ㅓ','ㅓ':'ㅏ','ㅗ':'ㅜ','ㅜ':'ㅗ','ㅐ':'ㅔ','ㅔ':'ㅐ','ㅣ':'ㅡ','ㅡ':'ㅣ','ㅕ':'ㅓ','ㅚ':'ㅗ','ㅢ':'ㅣ'}
CS={'ㄱ':'ㄲ','ㄲ':'ㄱ','ㅇ':'ㅁ','ㅁ':'ㅇ','ㄹ':'ㄷ','ㄷ':'ㄹ','ㅌ':'ㄹ','ㅂ':'ㅃ','ㅅ':'ㅆ','ㅈ':'ㅊ','ㅎ':'ㅇ','ㄴ':'ㄹ','ㅊ':'ㅈ','ㅋ':'ㄱ','ㅍ':'ㅂ'}
def dec(c):
  o=ord(c)-0xAC00
  return (o//588,(o%588)//28,o%28) if 0<=o<11172 else None
def com(a,b,c): return chr(0xAC00+a*588+b*28+c)
def variants(s):
  n=nm(s); r=reg(s); t=tag(s) or '<하드>'; out=set(); drops=set()
  bases=[n]
  for i,ch in enumerate(n):
    d=dec(ch)
    if not d: continue
    a,b,c=d
    v=JUNG[b]
    if v in VS: bases.append(n[:i]+com(a,JUNG.index(VS[v]),c)+n[i+1:])
    if CHO[a] in CS: bases.append(n[:i]+com(CHO.index(CS[CHO[a]]),b,c)+n[i+1:])
    if c: bases.append(n[:i]+com(a,b,0)+n[i+1:])
    if ch!=' ': drops.add((n[:i]+n[i+1:]).strip()); bases.append((n[:i]+n[i+1:]).strip())
  # 두 글자 동시 오독(모음+자음)
  rnd=random.Random(sum(map(ord,n)))  # 실행마다 같은 변형
  for _ in range(6):
    x=list(n)
    for i in rnd.sample(range(len(x)),min(2,len(x))):
      d=dec(x[i])
      if d and JUNG[d[1]] in VS: x[i]=com(d[0],JUNG.index(VS[JUNG[d[1]]]),d[2])
      elif d and CHO[d[0]] in CS: x[i]=com(CHO.index(CS[CHO[d[0]]]),d[1],d[2])
    bases.append(''.join(x))
  tails=[t,t.replace('<','').replace('>',''),'<하프>','<노딸>','<카모스>','','   비호',' :011[']
  for bb in bases:
    if len(bb.replace(' ',''))<2: continue
    for tl in tails:
      dr=bb in drops
      out.add((f'{bb} {tl}'.strip(),dr,''))
      if r: out.add((f'{r}：{bb} {tl}'.strip(),dr,'')); out.add((f'{r}{bb} {tl}'.strip(),dr,r)); out.add((f'{r[1:]} {bb} {tl}'.strip(),dr,r[1:]))
  return sorted(out)
RN={n.replace(' ','') for n,k in [(a,BK[a.replace(' ','')]) for a in [x for x in BK]] if 'r' in k}
def ambiguous(v,s):
  # 이름만으로는 구분 불가: (1) 대기/전투 이름이 보상 가능 이름을 품고(앞/뒤 꼬리) 글자가 빠진 변형 (2) 지역명이 ':' 없이 붙어 보상 가능 이름과 같아진 줄
  t,dr,rg=v; n0=nm(s).replace(' ','')
  rel=[w for w in RN if w!=n0 and (w in n0 or n0 in w)]
  if dr and rel: return True
  if rg and any((rg+nm(s)).replace(' ','').endswith(w) or w in (rg+nm(s)).replace(' ','') for w in rel+list(RN) if len(w)>=4 and (w in (rg+nm(s)).replace(' ',''))): return True
  return False
ALL=[(v,s,b) for s,b in src for v in variants(s)]
cases=[(v[0],s,b) for v,s,b in ALL if not ambiguous(v,s)]
amb=len(ALL)-len(cases)
port=_tutil.free_port();import os
srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=os.environ.get('LIVE_ROOT',str(H.parent)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[]
try:
 with sync_playwright() as p:
  br=p.chromium.launch(args=['--no-sandbox']);pg=br.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}')
  res=pg.evaluate("""C=>C.map(t=>{ ARX.runDiff=null; ARX.mapSt=null; ARX.rew=null; ARX.rwl=null; let d=null; try{ d=arDetectBMap(t); }catch(e){ return ['ERR',String(e)]; } return d?[d.boss,d.kind,d.name]:null; })""",[c[0] for c in cases])
  br.close()
finally: srv.terminate()
n_none=0; n_ok=0
for (t,s,b),r in zip(cases,res):
  if r is None: n_none+=1; continue
  if r[0]=='ERR' or 'r' in r[1]: bad.append((t,s,r))
  else: n_ok+=1
print(f'보스 {len(set(b for _,b in src))}명 · 비보상 맵 이름 {len(src)}개 · 변형 {len(cases)}줄(이름만으론 구분 불가 {amb}줄은 상자 연속 확인 test_b431_reward_gate S3·S4 가 맡음) → 전투/대기로 판정 {n_ok}, 미판정 {n_none}, 보상 맵 오판정 {len(bad)}')
import collections
G=collections.Counter((x[1],x[2][2] if x[2] and x[2][0]!='ERR' else str(x[2])) for x in bad)
for (a,b2),v in G.most_common(30): print(f'  FAIL {v}줄: {a} → {b2} 예: '+next(x[0] for x in bad if x[1]==a))
print('PASS b431 battle names' if not bad else f'FAIL b431 battle names ({len(bad)})'); sys.exit(1 if bad else 0)
