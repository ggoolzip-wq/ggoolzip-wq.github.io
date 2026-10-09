"""드롭 아이템 아이콘(32px) → src/itemicons.json  (사용법: python3 tools/build_items.py, Pillow 필요)"""
from PIL import Image
import base64,io,json,os
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'src','assets'))
SRC={ # key: file
 'lcm':'itemicons/1012632.png','tc':'itemicons_msw/Eqp_Total_Control.png','eye':'itemicons/1022278.png','belt':'itemicons/1132308.png',
 'book':'itemicons/2633926.png','terror':'itemicons/1113306.png','cfe':'itemicons/1032316.png','sos':'itemicons/1122430.png',
 'genesis':'itemicons/1182285.png','mitra':'itemicons/2633927.png','twilight':'itemicons/1012757.png','estella':'itemicons/1032330.png',
 'daybreak':'itemicons/1122443.png','gar':'itemicons/1113313.png',
 'whisper':'itemicons_msw/Eqp_Whisper_of_the_Source.png','oath':'itemicons_msw/Eqp_Oath_of_Death.png','bliss':'itemicons_msw/Eqp_Blissful_Nightmare.png',
 'sin':'itemicons_msw/Eqp_Original_Sin_of_Pride.png','spirit':'itemicons_msw/Eqp_Starving_Blood-Red_Vengeful_Spirit.png','legacy':'itemicons_msw/Eqp_Immortal_Legacy.png',
 'chaosbox':'itemicons_msw/Use_Chaos_Pitched_Accessory_Box.png',
 'h_face':'itemicons_msw/Use_Exceptional_Hammer_(Face_Acc).png','h_eye':'itemicons_msw/Use_Exceptional_Hammer_(Eye_Acc).png',
 'h_belt':'itemicons_msw/Use_Exceptional_Hammer_(Belt).png','h_ear':'itemicons_msw/Use_Exceptional_Hammer_(Earrings).png',
 'cfs':'itemicons/1012478.png','aquatic':'itemicons/1022231.png','zbelt':'itemicons/1132296.png','papmark':'itemicons/1022277.png',
 'wentus':'itemicons/1182087.png','shoulder':'itemicons/1152170.png',
 'r_green':'ringicons/2028407.png','r_red':'ringicons/2028408.png','r_black':'ringicons/2028409.png','r_white':'ringicons/2028410.png','r_life':'ringicons/Use_Life_Boss_Ring_Box.png',
 'ring_restraint':'ringicons/Eqp_Ring_of_Restraint.png','ring_continuous':'ringicons/Eqp_Continuous_Ring.png',
 'ipc':'ringicons/4001928.png',  # 강렬한 힘의 결정 (주간), item 4001928 (maplestory.io GMS 255 game data = maplestorywiki 'Etc Intense Power Crystal (Weekly)')
 # 연마석: 생명 2539001 (maplestory.io KMS 389), 신념 2539003 (maplestory.io GMS 270 'Grindstone of Faith' — KMS 데이터에 아직 없음)
 'g_life':'itemicons/2539001.png','g_faith':'itemicons/2539003.png',
 # 소울 에테르 1~4단계 (2026-09-17 추가, maplestory.io 미수록) — maple.ai.kr 소울웨폰 개편 글의 게임 아이콘 이미지를 잘라 배경 제거
 'se1':'itemicons/soul_ether_1.png','se2':'itemicons/soul_ether_2.png','se3':'itemicons/soul_ether_3.png','se4':'itemicons/soul_ether_4.png',
 'erda':'itemicons/2636421.png',
 # 에테르넬 방어구 교환 재료 (정보 칩): 칼로스·카링 = maplestory.io KMST 1170 (2636606/2634472/2636607/2635747), 림보 2638063·발드릭스 2639252 = maplestory.io GMS 270,
 # 대적자·흉성·벨로나·유피테르 = 나무위키 '에테르넬 세트' 문서의 게임 아이콘 파일(i.namu.wiki, 2026-10-10)
 'e_kalos_f':'itemicons/2636606.png','e_kalos':'itemicons/2634472.png','e_kaling_f':'itemicons/2636607.png','e_kaling':'itemicons/2635747.png',
 'e_limbo':'itemicons/2638063.png','e_baldrix':'itemicons/2639252.png',
 'e_adv_f':'itemicons/eternal_adv_f.png','e_adv':'itemicons/eternal_adv.png','e_star_f':'itemicons/eternal_star_f.png','e_star':'itemicons/eternal_star.png',
 'e_bellona':'itemicons/eternal_bellona.png','e_jupiter':'itemicons/eternal_jupiter.png'}  # 솔 에르다의 기운 2636421 (maplestory.io KMS 389) — 정보 표시 전용  # 강렬한 힘의 결정 (주간), item 4001928 (maplestory.io GMS 255 game data = maplestorywiki 'Etc Intense Power Crystal (Weekly)')
out={}; S=32
for k,f in SRC.items():
    im=Image.open(f).convert('RGBA'); bb=im.getbbox(); im=im.crop(bb) if bb else im
    w,h=im.size; sc=min(S/w,S/h,1.0) if max(w,h)<=S else S/max(w,h)
    if max(w,h)>S: im=im.resize((max(1,round(w*sc)),max(1,round(h*sc))),Image.LANCZOS)
    c=Image.new('RGBA',(S,S),(0,0,0,0)); c.alpha_composite(im,((S-im.width)//2,(S-im.height)//2))
    b=io.BytesIO(); c.save(b,'WEBP',lossless=True); l=b.getvalue()
    b2=io.BytesIO(); c.save(b2,'PNG',optimize=True); p=b2.getvalue()
    out[k]=('data:image/webp;base64,'+base64.b64encode(l).decode()) if len(l)<=len(p) else ('data:image/png;base64,'+base64.b64encode(p).decode())
json.dump(out,open('../itemicons.json','w'))
print(len(out),'items',sum(map(len,out.values())),'chars')
T=40; sh=Image.new('RGBA',(T*len(out),T),(40,40,48,255))
for i,v in enumerate(out.values()):
    sh.alpha_composite(Image.open(io.BytesIO(base64.b64decode(v.split(',')[1]))).convert('RGBA'),(i*T+4,4))
sh.convert('RGB').resize((T*len(out)*2,T*2),Image.NEAREST).save('/tmp/items_preview.png')
