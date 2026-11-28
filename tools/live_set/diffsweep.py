#!/usr/bin/env python3
"""t707u 회귀 규칙: 과거 영상은 보스별로 1개만 무작위로 골라, 그 영상으로 그 보스의 모든 난이도 기준(드롭 테이블)을 돌린다.
사용: python3 diffsweep.py OUT_DIR [--seed N] [--root REPO] [--viddir DIR]
  - 보스별 1개 무작위(시드 기록, noReward 영상 제외) → 난이도마다 run_set.py 를 LIVE_FORCE_DIFF=<난이도> 로 순차 실행(병렬 금지: 부하로 결과 흔들림)
  - 판정: 기록된 아이템이 화면 정답(truth.items)에 없는 것 = 오기록(FAIL). 영상 본래 난이도 실행은 score.py 전체 항목(PASS/FAIL)도 함께.
  - 결과: OUT_DIR/sweep.json, OUT_DIR/sweep.txt (보스·영상·난이도·결과 표)"""
import os, sys, re, json, random, subprocess, argparse
from pathlib import Path
H = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--seed', type=int, default=None); ap.add_argument('--root', default=str(H.parent.parent))
ap.add_argument('--viddir', default='/workspace/reward_live_set/vids'); ap.add_argument('--only', default='')
A = ap.parse_args(); OUT = Path(A.out); OUT.mkdir(parents=True, exist_ok=True)
seed = A.seed if A.seed is not None else random.randrange(1 << 30)
T = json.load(open(H / 'truth.json', encoding='utf-8'))
app = open(Path(A.root) / 'src' / 'app.js', encoding='utf-8').read()
DIFFS = {m.group(1): re.findall(r"'(\w+)'", m.group(2)) for m in re.finditer(r"\{id:'(\w+)',name:'[^']*',type:'\w+',diffs:\[([^\]]*)\]", app)}
rng = random.Random(seed); pick = {}
for b in sorted({t['boss'] for t in T if not t.get('noReward')}):
  if A.only and b not in A.only.split(','): continue
  pick[b] = rng.choice(sorted([t for t in T if t['boss'] == b and not t.get('noReward')], key=lambda t: t['id']))
plan = {}
for b, t in pick.items():
  for d in DIFFS.get(b, [t['diff']]): plan.setdefault(d, []).append(t['id'])
env0 = dict(os.environ, LIVE_ROOT=A.root, LIVE_VIDDIR=A.viddir, LIVE_SPEC=str(H / 'truth.json'),
            LIVE_CHARS=os.environ.get('LIVE_CHARS', '["림강혼망","2터래플","터래플","zetking","린벨자","랑트킹","트딕이","Drcancel","허슬미러"]'))
rows = []
for d, ids in plan.items():
  o = OUT / d; env = dict(env0, LIVE_ONLY=','.join(ids), LIVE_FORCE_DIFF=d, LIVE_OUT=str(o))
  print('RUN', d, ids, flush=True)
  with open(str(o) + '.log', 'w') as lg: subprocess.run([sys.executable, str(H / 'run_set.py')], env=env, cwd=A.root, stdout=lg, stderr=subprocess.STDOUT)
  subprocess.run([sys.executable, str(H / 'score.py'), str(o)], env=dict(env, LIVE_ONLY=','.join(ids)), cwd=A.root, stdout=open(str(o) + '.score', 'w'), stderr=subprocess.STDOUT)
  for i in ids:
    t = next(x for x in T if x['id'] == i); p = o / i / 'summary.json'
    if not p.exists(): rows.append({'boss': t['boss'], 'id': i, 'vdiff': t['diff'], 'diff': d, 'ok': False, 'why': '결과 없음'}); continue
    s = json.load(open(p)); rec = [x['k'] for x in s.get('runRec') or []]
    want = dict(t.get('items') or {}); extra = []
    for k in rec:
      if want.get(k, 0) > 0: want[k] -= 1
      else: extra.append(k)
    sc = json.load(open(o / 'score.json')).get(i, {}) if (o / 'score.json').exists() else {}
    full = (sc.get('ok') if d == t['diff'] else None)
    rows.append({'boss': t['boss'], 'id': i, 'vdiff': t['diff'], 'diff': d, 'rec': rec, 'wrong': extra, 'ok': not extra and full is not False, 'full': full, 'fail': [k for k, v in (sc.get('c') or {}).items() if not v] if full is False else []})
rows.sort(key=lambda r: (r['boss'], r['diff']))
json.dump({'seed': seed, 'pick': {b: t['id'] for b, t in pick.items()}, 'rows': rows}, open(OUT / 'sweep.json', 'w'), ensure_ascii=False, indent=1)
KD = {'easy': '이지', 'normal': '노말', 'hard': '하드', 'chaos': '카오스', 'extreme': '익스트림'}
with open(OUT / 'sweep.txt', 'w') as f:
  f.write(f'시드 {seed}\n보스 | 영상(본래 난이도) | 기준 난이도 | 기록 | 오기록 | 결과\n')
  for r in rows:
    f.write(f"{r['boss']} | {r['id']}({KD.get(r['vdiff'], r['vdiff'])}) | {KD.get(r['diff'], r['diff'])} | {','.join(r.get('rec') or []) or '-'} | {','.join(r.get('wrong') or []) or '0'} | {'통과' if r['ok'] else '실패 ' + ','.join(r.get('fail') or []) + (r.get('why') or '')}\n")
  f.write(f"오기록 합계 {sum(len(r.get('wrong') or []) for r in rows)}, 통과 {sum(r['ok'] for r in rows)}/{len(rows)}\n")
print(open(OUT / 'sweep.txt').read())
