#!/usr/bin/env python3
"""b429: 드롭 그림 템플릿 만들기 -> src/dropsprites.json

인벤 아이콘(ITEM_ICONS)과 실제 바닥/공중에 떨어진 그림이 다른 아이템은 아이콘 맞춤 점수가 낮다
(생명의 연마석: 아이콘 0.47~0.58, 반짝이·후광 23% + 판 크기 1.2배). 그래서 실제 영상 한 장면에서
아이템 판 모양(다각형)만 잘라 1080 기준 84px 칸 가운데에 놓은 템플릿을 만든다.

SPEC   : 영상에서 직접 자르는 아이템 (video, 초, 자르는 기준점, 다각형, 영상 높이)
DERIVE : 같은 모양·다른 색 아이템 — 아이콘 두 장의 색 차이를 드롭 그림 위치로 옮겨 입힘
         (생명↔신념 연마석처럼 모양이 같은 짝; 색 구분 판정 arVarDist 가 그대로 쓰임)
사용:  python3 tools/build_dropsprites.py <영상 폴더(tools/live_set vids)>
"""
import sys, os, json, base64, subprocess, tempfile
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
VIDS = sys.argv[1] if len(sys.argv) > 1 else '/workspace/reward_live_set/vids'
CELL = 84  # AR_WZREF 40px 칸 = 화면 높이 1080 에서 84px (arGroundPx)

SPEC = [
  # w01 (최초의 대적자 노멀, 린벨자 1376x776): 11.567초 바닥에 떨어진 생명의 연마석, 다른 아이템에 안 가린 장면
  dict(k='g_life', video='w01.mp4', t=11.3 + 4 / 15, y0=488, x0=955, poly=[[17, 16], [52, 28], [59, 57], [37, 53], [24, 45]]),
]
DERIVE = [
  # (새 키, 기준 키, 아이콘 3점(기준 아이콘 좌표) -> 드롭 그림 3점(84칸 좌표))
  dict(k='g_faith', base='g_life', src=[[5, 5.6], [24.6, 11], [29.6, 26.9]], dst=[[10, 11], [61, 27], [72, 70]]),
]

def icons():
  s = open(os.path.join(ROOT, 'src', 'itemicons.json'), encoding='utf-8').read() if os.path.exists(os.path.join(ROOT, 'src', 'itemicons.json')) else None
  return json.loads(s) if s else {}

def dec(uri):
  b = base64.b64decode(uri.split(',', 1)[1]); return cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_UNCHANGED)

def enc(img):
  return 'data:image/png;base64,' + base64.b64encode(cv2.imencode('.png', img)[1].tobytes()).decode()

def frame(video, t):
  with tempfile.TemporaryDirectory() as d:
    o = os.path.join(d, 'f.png')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.3f' % t, '-i', os.path.join(VIDS, video), '-frames:v', '1', o], check=True)
    return cv2.imread(o)

def cut(f, y0, x0, poly):
  sh = f.shape[0]; P = np.array(poly, np.int32); xa, ya = P.min(0) - 3; x1, y1 = P.max(0) + 3
  c = f[y0 + ya:y0 + y1, x0 + xa:x0 + x1].copy(); m = np.zeros(c.shape[:2], np.uint8); cv2.fillPoly(m, [P - [xa, ya]], 255)
  m = cv2.dilate(m, np.ones((3, 3), np.uint8))
  s = 1080 / sh; c = cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC); m = cv2.resize(m, (c.shape[1], c.shape[0]))
  m = np.where(m >= 128, 255, 0).astype(np.uint8); ys, xs = np.nonzero(m)
  c = c[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
  h, w = m.shape; o = np.zeros((CELL, CELL, 4), np.uint8); oy, ox = (CELL - h) // 2, (CELL - w) // 2
  o[oy:oy + h, ox:ox + w, :3] = c; o[oy:oy + h, ox:ox + w, 3] = m; return o

def derive(S, L, F, src, dst):
  L = L.astype(np.float32); F = F.astype(np.float32)
  hh, ww = max(L.shape[0], F.shape[0]), max(L.shape[1], F.shape[1])
  pad = lambda x: np.pad(x, ((0, hh - x.shape[0]), (0, ww - x.shape[1]), (0, 0)))
  L, F = pad(L), pad(F)
  A = cv2.getAffineTransform(np.float32(src), np.float32(dst))
  wp = lambda x: cv2.warpAffine(x, A, (CELL, CELL))
  g1 = cv2.cvtColor(wp(L[..., :3]).astype(np.uint8), cv2.COLOR_BGR2GRAY); g2 = cv2.cvtColor(S[..., :3], cv2.COLOR_BGR2GRAY)
  W = np.eye(2, 3, dtype=np.float32)
  try:
    _, W = cv2.findTransformECC(g2, g1, W, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), (S[..., 3] > 0).astype(np.uint8), 5)
    A = (np.vstack([cv2.invertAffineTransform(W), [0, 0, 1]]) @ np.vstack([A, [0, 0, 1]]))[:2]
  except cv2.error:
    pass
  wl, wf = wp(L), wp(F); ok = (wl[..., 3] > 200) & (wf[..., 3] > 200)
  d = np.where(ok[..., None], wf[..., :3] - wl[..., :3], 0); w = ok.astype(np.float32)
  D = cv2.GaussianBlur(d, (0, 0), 2.0) / np.maximum(cv2.GaussianBlur(w, (0, 0), 2.0)[..., None], 1e-3)
  O = S.copy(); O[..., :3] = np.clip(S[..., :3].astype(np.float32) + D, 0, 255).astype(np.uint8); return O

def main():
  I = icons(); out = {}
  for sp in SPEC: out[sp['k']] = cut(frame(sp['video'], sp['t']), sp['y0'], sp['x0'], sp['poly'])
  for dv in DERIVE: out[dv['k']] = derive(out[dv['base']], dec(I[dv['base']]), dec(I[dv['k']]), dv['src'], dv['dst'])
  json.dump({k: enc(v) for k, v in out.items()}, open(os.path.join(ROOT, 'src', 'dropsprites.json'), 'w'), separators=(',', ':'))
  print('dropsprites:', {k: int((v[..., 3] > 0).sum()) for k, v in out.items()})

if __name__ == '__main__':
  main()
