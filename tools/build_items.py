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
 'ipc':'ringicons/4001928.png'}  # 강렬한 힘의 결정 (주간), item 4001928 (maplestory.io GMS 255 game data = maplestorywiki 'Etc Intense Power Crystal (Weekly)')
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
