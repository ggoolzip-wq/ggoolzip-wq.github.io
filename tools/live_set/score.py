#!/usr/bin/env python3
"""전체 회귀 세트 채점: truth.json(화면 확인 정답) vs run_set.py 결과(OUT/<id>/summary.json).
사용: python3 score.py OUT_DIR [OUT_DIR2]  → 영상별 보스·난이도·닉·해상도·아이템 PASS/FAIL, 마지막 줄 합계.
배포 조건: 전부 PASS (아이템 오기록 0, 확인된 드롭은 기록)."""
import json,sys,os
from collections import Counter
from pathlib import Path
H=Path(__file__).resolve().parent
T=json.load(open(Path(os.environ.get('LIVE_TRUTH',H/'truth.json'))))
sys.path.insert(0,str(H)); from pickset import pick as _pick; T=_pick(T)  # t574: 최신 20개 + 증명 아이템 영상
BOSS={'최초의 대적자':'adversary','벨로나':'bellona','스우':'lotus','선택받은 세렌':'seren','카링':'kaling','가디언 엔젤 슬라임':'slime','윌':'will','감시자 칼로스':'kalos','진 힐라':'jinhilla','듄켈':'dunkel','더스크':'dusk','유피테르':'jupiter','데미안':'damien','루시드':'lucid','검은 마법사':'blackmage','림보':'limbo','발드릭스':'baldrix','찬란한 흉성':'star','파풀라투스':'papulatus','매그너스':'magnus','자쿰':'zakum'}  # b429: y15 데미안 등 이름 추가
DIFF={'이지':'easy','노멀':'normal','하드':'hard','카오스':'chaos','익스트림':'extreme'}
def score(out):
  R={}
  for t in T:
    p=Path(out)/t['id']/'summary.json'
    if not p.exists(): R[t['id']]={'ok':False,'why':'결과 없음'}; continue
    s=json.load(open(p)); d=s.get('final_det') or {}; m=s.get('final_map') or {}
    # 영상 끝에 다음 보스 대기맵으로 이동하는 경우가 많아 '마지막 맵'이 아니라 보상 상자를 감지한 때의 보스·난이도로 채점
    bx=[x[1] for x in (s.get('itemLog') or []) if '보상 상자 감지' in x[1]]; boss=diff=None
    if bx:
      L=bx[-1]; nm=L.split('보상 상자 감지:')[1].split('(')[0].strip(); boss=BOSS.get(nm,nm)
      import re; mm=re.search(r'난이도 (\S+)',L); diff=DIFF.get(mm.group(1),'') if mm else ''
      if not diff:  # 상자 순간 난이도 미정이면 arBossState가 같은 보스 맵 상태(mapSt)의 난이도로 채움 → 같은 보스 맵 읽기 중 가장 많은 난이도
        C=Counter(); [C.update({mp[3]:n}) for mp,n in (s.get('maps') or []) if mp[0]==boss and mp[3]]
        diff=C.most_common(1)[0][0] if C else ''
    if not bx:  # b430: 상자 못 봤어도 보상 맵 이름으로 보스·난이도가 정해져 기록되면(y18) 그 보상 맵 읽기 중 가장 많은 것으로 채점
      C=Counter(); [C.update({(mp[0],mp[3]):n}) for mp,n in (s.get('maps') or []) if 'r' in mp[2] and mp[3]]
      if C: boss,diff=C.most_common(1)[0][0]
    rec=Counter(x['k'] for x in (s.get('runRec') or []))
    want=Counter(t.get('items') or {})
    prof=(s.get('final_prof') or {}); res_ok=bool(prof.get('gw'))
    c={'boss':boss==t['boss'],'diff':diff==t['diff'],'name':(s.get('final_name') or '')==t['name'],'res':res_ok,
       'items':(rec==want) if t.get('itemsChecked') else not (rec-want)}
    R[t['id']]={'ok':all(c.values()),'c':c,'got':{'boss':boss,'diff':diff,'name':s.get('final_name'),'items':dict(rec),'box':s.get('first_box'),'map':s.get('first_map'),'res':f"{s.get('vw')}x{s.get('vh')}→{prof.get('lab')}"},'want':{k:t[k] for k in ('boss','diff','name','items')}}
  return R
if __name__=='__main__':
  outs=sys.argv[1:]; RS=[score(o) for o in outs]
  for t in T:
    row=[t['id']]
    for R in RS:
      r=R[t['id']]; row.append('PASS' if r['ok'] else 'FAIL '+(','.join(k for k,v in r.get('c',{}).items() if not v) or r.get('why','')))
    print(' | '.join(row))
  for o,R in zip(outs,RS): print(o,'PASS',sum(r['ok'] for r in R.values()),'/',len(R))
  json.dump(RS[-1],open(Path(outs[-1])/'score.json','w'),ensure_ascii=False,indent=1)
