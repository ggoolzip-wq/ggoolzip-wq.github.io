#!/usr/bin/env python3
"""일퀘 현황 지역 아이콘: src/assets/dqicons/*.png → src/dqicons.json (Pillow 필요)
원본(출처): cer~car = 넥슨 Open API /character/symbol-equipment 의 symbol_icon (어센틱심볼),
tal/gear = maplestory.io GMS/270 item 1714000/1714001 (그랜드 어센틱심볼: 탈라하트/기어드락, JMS/444와 픽셀 동일),
mp = maplestory.io KMS/389 item 4001864 (몬스터파크 REBORN 무료 이용권),
xmp = maplestory.io KMS/389 NPC 9071000 '슈피겔만'(몬스터파크 맵 951000000에 있는 흰 호랑이 버전) 스프라이트에서 얼굴·모자만 잘라냄
      (원본 xmp_src_npc9071000.png, 잘라내기 (44,0)-(102,60), 왼쪽 아래 호랑이 털 제거).
투명 여백을 잘라 40px(화면 20px의 2배) 안으로 맞춤."""
import base64, io, json, os
from PIL import Image
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'src','assets','dqicons'); out={}
for k in ['cer','arcs','odium','dow','art','car','tal','gear','mp','xmp']:
    im=Image.open(os.path.join(SRC,k+'.png')).convert('RGBA'); bb=im.getchannel('A').point(lambda a:255 if a>24 else 0).getbbox()
    if bb: im=im.crop(bb)
    if max(im.size)>40: im.thumbnail((40,40),Image.LANCZOS)
    b=io.BytesIO(); im.save(b,'PNG',optimize=True); out[k]='data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
json.dump(out,open(os.path.join(ROOT,'src','dqicons.json'),'w'),separators=(',',':'))
print({k:len(v) for k,v in out.items()}, sum(map(len,out.values())))
