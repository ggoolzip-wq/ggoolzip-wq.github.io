"""드롭 아이템 아이콘(t562: KMS WZ 원본 info/icon 그대로, 업스케일·재압축 없음, PNG 무손실) → src/itemicons.json  (사용법: python3 tools/build_items.py)
원본: src/assets/itemicons_wz/<아이템ID>.png — 박스 /workspace/wz(클라이언트 WZ 복사본)에서 wz_reader 0.0.26 으로 추출(_outlink → _Canvas 추적, 위컴알 방식).
  링크: 1022277(파풀라투스 마크)→1012627, 2633912(앱솔 무기 상자)→2630291, 2633914(아케인 무기 상자)→2630133.
아이템ID 없는 UI 키(meso·blink·emo_*·dif_*)는 기존 itemicons.json 값 그대로 보존. 대시보드 표시와 자동 기록 인식 템플릿(autorec.js arTpl)이 모두 이 ITEM_ICONS 를 씀."""
import base64,json,os
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'src'))
IDS={
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
 'mc_b':2730034, 'mc_g':2711033, 'mc_s':2711032,  # t619: 메멘토 브론즈 에디셔널·골드·실버 큐브(200제) WZ 원본 info/icon — 영상 B 공중 큐브와 같은 모양(자물쇠 배지 포함, 회전해서 왼쪽 아래로 보였던 것)
 }
old=json.load(open('itemicons.json'))
out={}
for k,i in IDS.items(): out[k]='data:image/png;base64,'+base64.b64encode(open('assets/itemicons_wz/%d.png'%i,'rb').read()).decode()
for k,v in old.items():
    if k not in out: out[k]=v
json.dump(out,open('itemicons.json','w'))
print(len(out),'icons',len(IDS),'from WZ')
