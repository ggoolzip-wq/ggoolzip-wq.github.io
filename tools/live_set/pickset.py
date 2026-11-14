"""회귀 세트 고르기 (원모님 상시 규칙 t574): 최신 20개(seq 큰 순) + 증명 아이템 영상.
LIVE_ALL=1 이면 전부, LIVE_ONLY=a,b 이면 그것만."""
import os, json
from pathlib import Path
H = Path(__file__).parent
def pick(T):
  if os.environ.get('LIVE_ONLY'): return [t for t in T if t['id'] in os.environ['LIVE_ONLY'].split(',')]
  if os.environ.get('LIVE_ALL'): return list(T)
  C = json.load(open(H / 'select.json', encoding='utf-8'))
  n = int(os.environ.get('LIVE_LATEST', C.get('latest', 20))); P = set(C.get('proof', []))
  new = {t['id'] for t in sorted(T, key=lambda t: t.get('seq', 0))[-n:]}
  prf = {t['id'] for t in T if P & (set(t.get('items', {})) | set(t.get('proof', [])))}
  return [t for t in T if t['id'] in new | prf]
if __name__ == '__main__':
  T = json.load(open(os.environ.get('LIVE_TRUTH', H / 'truth.json'), encoding='utf-8')); S = pick(T)
  print(len(S), ','.join(t['id'] for t in S))
