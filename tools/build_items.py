"""드롭 아이템 아이콘(b259: KMS WZ 원본 → b254 파이프라인 ESPCN x2 + 언샵 = 64px, 화면 32px) → src/itemicons.json  (사용법: python3 tools/build_items.py, Pillow·opencv 필요)"""
from PIL import Image
import base64,io,json,os
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'src','assets'))
# b259: 아이콘 전부 KMS 클라이언트 WZ 원본(C:\Nexon\Maple\Data, PKG2 분할 형식) info/icon 을 _outlink → _Canvas 로 풀어 뽑음(위컴알과 같은 방식, wz_reader 0.0.26).
#   아이템 ID = 같은 클라이언트 String.wz(Eqp/Consume/Etc) 의 이름과 일치하는 것. 메소 주머니(9000003)만 KMS String 에 없어 옛 파일 유지.
SRC={k:'itemicons/kms/%d.png'%i for k,i in {
 'lcm':1012632, 'tc':1672095, 'eye':1022278, 'belt':1132308, 'book':2633926, 'terror':1113306,
 'cfe':1032316, 'sos':1122430, 'genesis':1182285, 'mitra':2633927, 'twilight':1012757, 'estella':1032330,
 'daybreak':1122443, 'gar':1113313, 'whisper':1113341, 'oath':1122447, 'bliss':1113360, 'sin':1012911,
 'spirit':1022397, 'legacy':1143471, 'chaosbox':2830338, 'h_face':2644205, 'h_eye':2644206, 'h_belt':2644204,
 'h_ear':2644207, 'cfs':1012478, 'aquatic':1022231, 'zbelt':1132296, 'papmark':1022277, 'wentus':1182087,
 'shoulder':1152170, 'r_green':2028407, 'r_red':2028408, 'r_black':2028409, 'r_white':2028410, 'r_life':2028430,
 'ring_restraint':1113098, 'ring_continuous':1113329, 'ipcm':4001929, 'ipc':4001928, 'symsel':2437750, 'g_life':2539001,
 'g_faith':2539003, 'se1':2539020, 'se2':2539021, 'se3':2539022, 'se4':2539023, 'erda':2636421,
 'e_kalos_f':2636606, 'e_kalos':2634472, 'e_kaling_f':2636607, 'e_kaling':2635747, 'e_limbo':2638063, 'e_baldrix':2639252,
 'e_adv_f':2830305, 'e_adv':2830304, 'e_star_f':2831408, 'e_star':2831103, 'e_bellona':2832967, 'e_jupiter':2831104,
 'b_kalos':2638064, 'b_adv':2830306, 'b_kaling':2638065, 'b_star':2831105, 'b_limbo':2638066, 'b_sjm':2638066, 'b_baldrix':2639253,
 'b_bellona':2832969, 'b_jupiter':2831106, 'h_pocket':2644209, 'h_pendant':2644210, 'erion':4009615, 'ab_w':2633912,
 'ab_a':2633913, 'ar_w':2633914, 'ar_a':2633915, 'pcmedal':1142145, 'guildbless':2432290, 'moon':2023136,
 }.items()}
SRC['meso']='ringicons/9000003.png'
import cv2, numpy as np
_SR=cv2.dnn_superres.DnnSuperResImpl_create(); _SR.readModel(os.path.join(os.path.dirname(os.path.abspath(__file__)),'models','ESPCN_x2.pb')); _SR.setModel('espcn',2)
def up2(c):
    """RGBA 32px → 64px: RGB = ESPCN x2(투명 부분은 이웃 색으로 채워 테두리 번짐 방지) + 언샵, 알파 = 바이큐빅 + 살짝 대비."""
    a=np.array(c); rgb=a[...,:3].astype(np.float32); al=a[...,3].astype(np.float32)/255
    m=(al>0.02).astype(np.float32); fill=rgb*m[...,None]; w=m.copy()
    for _ in range(6):
        k=lambda x: cv2.blur(x,(3,3))
        nf=k(fill); nw=k(w); upd=(w==0)&(nw>0)
        fill[upd]=nf[upd]/nw[upd][...,None]; w[upd]=1
    big=_SR.upsample(np.clip(fill,0,255).astype(np.uint8)[...,::-1])[...,::-1].astype(np.float32)
    bl=cv2.GaussianBlur(big,(0,0),1.0); big=np.clip(big+0.6*(big-bl),0,255)
    A=cv2.resize(al,(al.shape[1]*2,al.shape[0]*2),interpolation=cv2.INTER_CUBIC); A=np.clip((A-0.5)*1.15+0.5,0,1)
    return Image.fromarray(np.dstack([big,A*255]).astype(np.uint8),'RGBA')
def enc(c):
    b=io.BytesIO(); c.save(b,'WEBP',quality=92,method=6,alpha_quality=100); l=b.getvalue()
    return 'data:image/webp;base64,'+base64.b64encode(l).decode()
old=json.load(open('../itemicons.json')) if os.path.exists('../itemicons.json') else {}
out={}; S=32
for k,f in SRC.items():
    im=Image.open(f).convert('RGBA'); bb=im.getbbox(); im=im.crop(bb) if bb else im
    w,h=im.size; sc=min(S/w,S/h,1.0) if max(w,h)<=S else S/max(w,h)
    if max(w,h)>S: im=im.resize((max(1,round(w*sc)),max(1,round(h*sc))),Image.LANCZOS)
    c=Image.new('RGBA',(S,S),(0,0,0,0)); c.alpha_composite(im,((S-im.width)//2,(S-im.height)//2))
    out[k]=enc(up2(c))
# 수동 추가 키(blink·emo·dif·mc·guildbless·pcmedal 등) 보존: 32px 이하 아이템 아이콘만 64px 로 올림(이모지·난이도 배지·UI 는 그대로)
for k,v in old.items():
    if k in out: continue
    im=Image.open(io.BytesIO(base64.b64decode(v.split(',')[1]))).convert('RGBA')
    out[k]=enc(up2(im)) if (max(im.size)<=32 and not k.startswith(('emo_','dif_','mc_'))) else v
json.dump(out,open('../itemicons.json','w'))
print(len(out),'items',sum(map(len,out.values())),'chars')
T=40; sh=Image.new('RGBA',(T*len(out),T),(40,40,48,255))
for i,v in enumerate(out.values()):
    sh.alpha_composite(Image.open(io.BytesIO(base64.b64decode(v.split(',')[1]))).convert('RGBA'),(i*T+4,4))
sh.convert('RGB').resize((T*len(out)*2,T*2),Image.NEAREST).save('/tmp/items_preview.png')
