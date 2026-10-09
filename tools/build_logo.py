#!/usr/bin/env python3
"""주황버섯(몹 1210102) 로고/파비콘 생성 → logo.json(16/32/64px data URI) + favicon.png(64) + apple-touch-icon.png(180)
원본: https://maplestory.io/api/KMS/389/mob/1210102/icon  (assets/orange_mushroom_1210102.png)
사용법: python3 build_logo.py <원본png> <logo.json 경로> <사이트 루트 폴더>   (Pillow 필요)"""
import base64, io, json, os, sys
from PIL import Image
src, out_json, site = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(src).convert('RGBA'); im = im.crop(im.getbbox())
S = max(im.size) + 2; sq = Image.new('RGBA', (S, S), (0, 0, 0, 0)); sq.alpha_composite(im, ((S - im.width) // 2, (S - im.height) // 2))
def png(img):
    b = io.BytesIO(); img.save(b, 'PNG', optimize=True); return b.getvalue()
out = {}
for n in (16, 32, 64):
    r = sq.resize((n, n), Image.LANCZOS); out[f's{n}'] = 'data:image/png;base64,' + base64.b64encode(png(r)).decode()
    if n == 64: r.save(os.path.join(site, 'favicon.png'))
bg = Image.new('RGBA', (180, 180), (255, 244, 230, 255)); bg.alpha_composite(sq.resize((150, 150), Image.LANCZOS), (15, 15)); bg.save(os.path.join(site, 'apple-touch-icon.png'))
out['s180'] = ''  # apple-touch-icon 은 파일로 제공
json.dump(out, open(out_json, 'w'))
print('ok', {k: len(v) for k, v in out.items()})
