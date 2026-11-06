/* b352 (t657): '에픽빔 기록지' 탭 — 라이브 화면 공유에서 에픽빔(득템 화면 효과) 감지 → 첫 감지 프레임 -1초 ~ +3초(4초, b354) 클립을 이 브라우저 IndexedDB 에 저장 + 로그인(넥슨 키) 상태면 서버(R2)에 올림 — 다른 PC 에서 같은 키로 로그인하면 보임. 자동 삭제 없음.
   autorec.js 는 건드리지 않음: ARX.video(공유 화면)를 따로 0.1초마다 읽고, 자동 기록은 arSessAdd 를 감싸서(래핑) 받음. */
const EC_TPL=[[0,0,0,0,0,0,1,0,0,0,4,2,0,1,0,0,2,6,7,7,7,7,7,7,7,3,0,0,0,0,0,0,0,0,0,0,0,0,1,5,0,3,19,42,9,3,0,2,24,72,78,78,78,78,78,78,55,16,2,0,0,0,0,0,0,0,0,0,0,0,0,4,3,2,23,100,32,5,0,7,70,180,184,184,184,184,184,154,56,10,0,0,2,13,8,0,0,0,0,1,0,0,0,0,0,0,13,76,85,15,0,14,109,228,229,229,229,229,211,89,21,2,0,11,48,28,0,0,0,0,0,1,0,0,0,0,0,0,4,31,115,28,3,22,138,236,236,236,236,230,118,31,3,2,29,65,14,0,0,0,0,0,0,0,0,0,0,0,0,0,0,15,85,54,10,32,164,236,236,236,235,148,44,6,9,51,49,0,0,0,0,0,0,0,0,0,0,0,6,33,9,0,0,6,32,93,21,47,189,236,236,236,182,61,13,21,60,18,0,0,0,0,0,0,1,10,8,1,0,0,1,23,64,37,4,1,18,87,41,75,212,236,236,216,89,21,34,44,0,0,0,13,0,0,0,0,0,3,7,1,1,1,0,0,9,57,74,24,18,54,86,111,226,236,234,145,29,22,4,0,27,61,51,13,0,0,0,0,0,2,6,6,4,2,1,3,16,11,36,92,67,37,98,175,233,236,195,60,0,9,59,73,47,15,3,1,0,0,0,0,0,2,6,7,6,5,4,3,17,43,56,62,92,115,146,202,236,221,129,59,88,80,36,11,5,3,2,1,0,0,0,0,1,20,49,57,51,40,27,13,3,4,13,38,81,152,195,214,229,196,168,95,43,24,12,5,3,1,0,0,0,0,0,0,0,5,14,18,19,16,12,7,1,1,3,11,53,153,193,216,213,172,139,74,54,41,22,5,3,2,1,1,0,0,0,0,0,1,4,6,6,8,9,8,7,8,13,51,107,169,186,198,194,180,109,34,21,16,11,12,30,39,40,32,17,8,2,0,0,2,8,17,23,24,20,16,12,14,37,72,83,105,143,177,173,166,137,31,12,5,4,4,6,10,14,24,36,29,11,1,0,1,5,11,15,19,19,19,32,57,50,35,43,55,93,98,130,90,105,94,20,3,1,2,2,2,1,1,0,0,0,0,0,0,1,3,5,7,13,23,26,16,11,11,19,35,30,25,42,31,29,37,20,4,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,2,1,1,2,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[0,1,2,2,0,0,0,0,3,6,7,7,7,7,7,6,4,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,13,39,52,24,7,0,1,15,59,76,76,76,76,76,68,39,9,19,1,0,0,0,0,0,0,0,0,0,0,1,0,3,39,112,157,150,64,16,2,13,78,178,185,185,185,185,165,87,27,41,2,1,2,2,1,1,1,0,0,3,20,12,0,1,41,153,210,223,201,88,22,6,40,163,230,229,229,229,211,103,52,32,1,3,4,3,2,2,1,0,15,67,42,0,0,0,11,72,184,234,236,216,101,29,16,80,219,236,236,236,222,102,66,20,3,6,5,4,3,2,4,37,84,24,0,0,0,0,1,12,51,136,220,236,224,117,36,34,144,236,236,236,223,102,72,12,21,10,7,5,3,11,61,62,0,0,0,0,0,0,0,0,6,27,78,174,232,229,130,49,72,207,236,236,225,116,79,36,43,48,13,7,21,66,22,0,0,0,11,1,0,0,0,0,0,2,11,41,115,206,231,149,80,141,235,236,229,128,66,43,80,75,11,13,36,0,0,14,69,75,31,1,0,0,0,0,0,0,1,7,20,65,159,229,177,132,215,236,230,139,69,107,127,26,0,0,0,45,94,85,34,6,0,0,0,0,1,3,3,1,3,30,48,46,62,134,214,216,197,235,230,185,136,164,52,3,19,80,100,66,23,5,2,0,0,0,0,0,1,3,3,3,2,3,9,32,71,115,143,180,215,227,233,230,221,153,68,108,103,48,17,8,5,3,2,0,0,0,0,2,22,49,50,32,11,2,1,3,24,58,86,145,205,230,235,232,208,191,116,66,43,31,20,12,7,5,4,2,2,0,0,0,5,13,14,9,3,0,0,0,2,22,51,81,195,228,233,233,211,199,154,127,114,99,82,59,44,35,29,23,15,5,0,0,1,3,4,4,5,5,5,15,47,46,102,138,208,217,229,230,226,188,111,123,139,145,150,147,134,119,107,91,66,23,1,0,2,10,16,19,17,14,10,9,21,91,94,102,130,169,227,213,207,185,64,37,30,35,46,68,108,146,172,172,124,41,3,0,2,6,13,14,15,13,15,38,68,66,103,108,80,166,183,172,127,134,142,32,5,2,4,7,14,22,31,37,36,16,1,0,0,2,4,6,7,13,28,31,15,10,26,33,45,80,64,60,40,31,55,43,6,0,0,0,0,0,1,1,2,1,0,0,0,0,0,0,1,2,1,1,1,1,1,1,3,4,3,2,1,1,2,3,1,0,0,0,0,0,0,0,0,0,0],[0,1,3,5,6,6,7,7,7,6,3,3,4,0,0,0,0,0,2,1,0,0,0,0,0,0,0,0,0,0,0,0,1,12,40,60,69,73,76,77,77,77,55,28,49,13,1,1,1,6,24,2,0,0,1,1,1,0,0,0,0,0,1,0,3,39,113,158,174,180,183,185,185,185,171,83,110,41,7,2,3,21,50,2,5,7,2,1,1,1,1,0,4,25,15,0,5,58,157,210,223,227,229,229,229,229,229,157,105,87,16,3,7,51,39,2,7,4,4,3,2,2,2,17,80,53,0,0,5,65,172,223,234,236,236,236,236,236,236,216,109,111,24,9,14,67,24,9,11,13,11,4,3,5,41,97,30,0,0,0,5,68,176,227,236,236,236,236,236,236,236,236,166,121,41,30,36,78,35,41,47,82,30,5,11,61,66,0,0,0,0,1,5,69,178,228,236,236,236,236,236,236,236,236,220,135,88,70,98,83,56,63,114,82,12,6,34,17,0,0,0,42,29,2,5,69,178,228,236,236,236,236,236,236,236,236,236,192,150,115,118,62,65,106,122,23,5,0,0,0,27,102,124,72,16,1,5,69,178,228,236,236,236,236,236,236,236,236,236,230,196,181,138,144,152,174,62,6,0,0,67,125,125,90,97,89,39,3,4,50,132,184,216,233,236,236,236,236,236,236,236,236,226,225,192,182,199,88,15,22,99,135,130,116,122,138,144,131,56,5,5,69,175,210,198,187,186,191,210,227,236,236,236,236,234,232,214,213,164,78,136,169,151,158,170,190,212,231,228,177,68,5,5,67,174,224,234,236,236,235,226,219,221,230,234,236,236,235,235,223,206,184,209,220,229,229,224,217,208,200,185,137,50,4,5,63,166,218,230,233,235,235,232,229,227,223,223,234,236,236,235,230,213,160,163,147,132,109,91,78,56,44,38,26,9,0,3,42,106,132,129,123,129,101,88,89,120,167,185,208,220,231,232,233,163,64,33,56,12,7,5,4,3,9,13,9,3,0,0,8,21,26,29,26,18,17,57,106,108,64,89,117,166,228,234,223,202,103,56,11,5,1,1,1,1,9,34,35,15,1,0,2,5,8,9,8,7,11,44,67,25,26,36,66,145,197,208,144,130,158,41,7,7,1,0,0,0,0,0,0,1,0,0,0,1,3,3,5,13,32,34,27,32,23,22,26,56,85,94,64,20,61,65,10,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,1,1,0,1,1,0,1,3,4,5,4,2,1,4,3,0,0,0,0,0,0,0,0,0,0],[0,1,3,5,6,7,7,7,7,4,0,0,0,0,0,0,0,0,2,1,0,0,0,0,0,0,0,0,0,1,1,0,0,12,39,60,69,73,76,77,77,66,22,2,0,0,1,2,2,5,23,2,1,0,0,1,1,0,1,9,26,33,10,0,1,25,105,158,174,180,183,184,185,183,100,22,1,1,2,8,7,21,47,4,5,4,4,6,3,5,26,81,143,104,30,2,0,20,95,179,223,226,228,229,229,229,201,71,10,4,9,13,16,51,36,16,19,17,26,58,14,41,124,211,203,141,44,3,0,1,28,116,183,229,236,236,236,236,236,146,37,9,27,33,46,81,30,52,49,59,103,48,56,155,231,228,205,134,37,3,0,0,0,15,82,162,216,236,236,236,236,218,102,28,60,77,112,115,59,85,78,127,79,78,181,232,225,205,156,124,56,5,0,0,1,6,5,39,131,200,234,236,236,236,184,99,123,131,126,75,62,63,131,115,106,204,229,218,180,178,207,167,64,5,0,4,10,6,4,2,18,82,169,227,236,236,232,180,165,138,140,121,88,113,163,135,218,224,196,186,215,227,222,156,46,2,0,2,29,59,65,39,14,15,60,140,214,236,236,216,192,198,163,122,122,190,186,223,207,195,215,224,203,155,92,41,9,0,0,0,1,5,15,49,81,93,106,87,114,197,235,236,215,224,194,192,214,214,215,202,215,204,161,102,54,28,10,3,0,0,0,5,11,15,12,10,18,23,49,104,159,191,198,231,232,232,226,227,221,211,209,183,124,68,36,17,7,3,0,0,0,0,3,36,83,99,94,84,77,71,67,73,95,146,213,231,236,235,236,229,205,164,109,67,41,22,17,14,13,9,2,0,0,0,5,63,166,217,229,230,229,226,224,227,222,228,235,236,236,236,235,228,195,113,69,67,65,56,54,50,42,28,6,0,0,0,4,54,149,203,221,229,233,236,236,236,236,236,236,230,226,234,232,234,189,91,30,8,16,33,1,0,0,0,0,1,1,0,3,41,121,178,206,220,229,234,236,236,235,222,204,198,192,207,219,230,234,188,120,75,14,5,0,0,0,0,0,5,8,1,2,23,77,130,165,187,201,207,209,181,136,136,163,96,120,124,177,172,209,211,191,110,37,8,4,2,0,0,0,0,0,0,0,5,22,45,65,78,87,86,59,39,46,74,37,26,29,44,67,53,77,94,94,91,54,22,6,3,0,0,0,0,0,0,0,0,1,2,3,4,4,2,2,2,5,2,1,1,1,2,3,2,3,5,5,5,5,4,2,0,0,0,0,0,0,0],[0,1,3,5,5,3,5,7,4,1,0,0,1,5,1,0,0,0,0,0,0,0,0,0,1,3,4,1,2,3,1,0,0,7,37,59,69,54,36,64,68,23,4,2,9,51,23,7,7,9,7,1,8,8,8,11,31,50,22,31,54,38,10,1,1,12,47,138,174,178,125,104,174,109,29,10,14,101,78,36,31,37,24,17,28,27,33,60,125,63,81,154,155,104,31,2,0,10,24,66,174,226,224,153,151,207,81,32,24,92,121,63,72,90,29,48,44,48,69,138,89,117,209,222,203,138,34,1,0,0,1,13,54,152,232,229,150,181,172,70,51,67,144,106,112,122,25,53,46,65,121,99,139,225,235,227,170,50,0,0,0,0,0,0,8,38,120,222,226,148,202,126,87,85,148,130,104,85,38,39,48,103,109,163,231,233,207,108,0,0,13,2,0,1,0,0,1,7,33,97,206,222,154,195,125,143,155,109,79,89,45,41,87,124,181,234,225,158,41,17,76,113,59,5,3,32,50,25,10,10,23,50,92,185,220,187,180,156,154,112,113,118,57,83,147,198,231,194,96,50,106,179,219,176,66,5,3,31,86,125,121,92,70,70,72,90,168,220,208,170,167,143,193,132,99,170,215,219,152,96,139,200,232,235,215,145,45,2,2,32,99,126,128,125,126,129,111,91,107,163,223,210,199,200,219,170,184,222,202,161,179,217,223,194,152,107,64,32,7,0,0,9,19,30,42,71,95,100,120,134,97,139,193,230,219,228,233,215,221,206,210,204,167,116,72,44,25,12,5,1,0,0,2,27,77,103,106,104,102,104,106,121,137,143,155,210,234,236,235,230,220,179,116,73,42,21,10,4,3,8,11,10,4,0,2,29,76,102,111,119,124,133,148,157,184,186,190,213,225,235,236,220,186,132,105,83,66,52,42,37,37,52,61,47,18,1,1,22,66,105,131,150,167,183,183,182,187,188,199,224,224,228,232,213,150,88,99,122,140,152,163,170,171,166,152,108,37,3,3,39,119,169,174,158,137,125,135,174,212,222,185,155,201,171,207,209,166,80,47,26,19,24,33,43,52,63,70,55,24,2,1,15,41,56,74,105,139,173,201,197,151,116,77,129,113,75,151,133,149,88,85,37,13,3,1,1,2,3,5,4,2,0,0,2,10,30,54,71,86,88,71,39,32,25,30,60,24,22,57,38,64,45,27,41,23,8,2,0,0,0,0,0,0,0,0,0,1,2,3,4,4,2,1,1,1,1,3,1,1,1,3,2,2,4,1,1,2,2,0,0,0,0,0,0,0,0],[0,0,0,0,0,2,6,4,1,0,0,0,1,3,0,0,1,1,1,0,0,0,1,2,1,2,2,2,5,3,0,0,1,11,16,8,3,8,31,67,27,7,4,4,4,33,11,9,12,15,13,2,9,8,12,21,15,21,28,62,59,22,2,0,2,39,104,81,30,11,30,104,134,43,18,17,9,70,44,44,44,51,30,18,19,24,48,32,52,63,154,163,78,17,1,0,1,31,139,204,143,55,28,52,157,123,46,34,26,65,78,72,67,75,24,29,27,46,52,38,72,190,198,91,26,0,0,0,0,7,49,150,227,188,79,47,70,172,92,56,56,66,91,92,65,77,19,29,33,64,42,74,195,182,87,38,0,0,0,0,0,0,8,36,94,186,210,106,65,89,166,84,86,104,71,74,48,77,27,28,50,47,74,194,157,97,51,0,0,0,22,3,0,1,3,9,25,57,128,208,147,78,114,145,118,111,56,60,45,87,34,40,51,73,185,138,104,35,0,1,98,138,63,5,2,25,40,29,27,35,54,86,164,177,100,147,142,102,84,88,71,97,46,59,85,175,134,93,11,14,110,194,222,155,46,2,0,8,48,85,93,80,62,58,74,118,184,155,160,117,137,119,137,100,70,96,174,140,69,36,120,201,202,153,91,42,9,0,0,3,6,9,20,46,75,84,73,75,105,184,187,177,165,174,189,120,103,170,139,94,142,187,156,97,56,32,18,11,6,1,1,15,37,43,35,19,13,21,34,38,64,110,182,215,205,212,211,177,170,159,180,174,109,60,42,37,31,30,36,33,12,1,2,27,72,92,102,106,98,101,94,78,81,96,140,204,230,229,224,210,206,160,102,70,53,52,53,52,55,61,66,59,25,2,1,6,21,34,45,57,81,104,103,114,138,149,145,174,204,228,227,203,179,119,121,129,135,138,144,154,164,176,178,142,54,4,0,4,17,34,50,65,88,115,141,163,166,170,179,204,198,212,224,210,148,66,58,78,87,88,92,92,88,75,54,36,12,1,1,23,82,140,182,199,183,150,123,124,171,200,155,120,172,147,184,197,150,72,66,40,17,12,10,16,20,32,42,31,9,0,2,21,66,92,86,77,69,86,137,183,148,94,55,109,85,65,119,105,137,83,41,42,54,44,20,11,4,1,0,0,0,0,0,3,9,19,27,30,50,79,80,41,18,13,29,48,13,16,40,26,45,52,32,12,8,20,36,24,10,4,1,0,0,0,0,0,0,0,2,3,4,3,1,1,1,1,2,1,0,0,1,1,1,2,3,1,1,0,0,1,2,1,0,0,0,0]]; /* 사용자 GIF(에픽빔 2번째 모션) 3~8번 프레임 − 0번 프레임 밝기 차이, 32x18 */
const EC={buf:[],h:[],log:[],cur:null,cool:0,pend:null,ph:[],pl:[],lastPil:null,recs:[],page:0,busy:false,timer:0,cv:null,sm:null,db:null,last:null,
  cfg:{fps:8,H0:240,H:540,q:.75,maxBytes:800000,th:.66,strong:.8,minMean:12,hits:2,pre:1000,post:3000,linkBefore:30000,linkAfter:90000,cool:12000,gate:true,rewardOnly:true,pil:false,shift:true,sx:10,sy:4,sTh:.77,sN:2,pendMs:2000,pilTh:.88,pilWid:5,per:12}};
const EC_ICON=(document.querySelector('#tabs [data-tab=epic] img.ecico')||{}).src||'';
const EC_DIFF={easy:'이지',normal:'노말',hard:'하드',chaos:'카오스',extreme:'익스트림'};
function ecDb(){ if(EC.db) return EC.db; return EC.db=new Promise((ok,no)=>{ const r=indexedDB.open('mbtEpicClips',1); r.onupgradeneeded=()=>{ const d=r.result; d.createObjectStore('meta',{keyPath:'id'}); d.createObjectStore('frames',{keyPath:'id'}); }; r.onsuccess=()=>ok(r.result); r.onerror=()=>no(r.error); }); }
async function ecTx(st,mode,fn){ const d=await ecDb(); return new Promise((ok,no)=>{ const t=d.transaction(st,mode); let out; t.oncomplete=()=>ok(out); t.onerror=()=>no(t.error); out=fn(t); if(out&&'onsuccess' in out){ const q=out; q.onsuccess=()=>{ out=q.result; }; } }); }
const ecList=()=>ecTx(['meta'],'readonly',t=>t.objectStore('meta').getAll()).then(a=>(a||[]).sort((x,y)=>y.t0-x.t0));
const ecFrames=id=>ecTx(['frames'],'readonly',t=>t.objectStore('frames').get(id));
const ecPutMeta=m=>ecTx(['meta'],'readwrite',t=>{ t.objectStore('meta').put(m); });
/* 감지: 0.6~1.5초 전 프레임들의 최솟값(배경) 대비 밝아진 양 D(32x18) 을 GIF 템플릿과 NCC. 에픽빔은 화면 전체 효과(ScreenEff)라 위치 고정 → 템플릿 한 번 비교로 충분(아주 쌈) */
function ecNcc(D,T){ const n=D.length; let ma=0,mb=0; for(let i=0;i<n;i++){ ma+=D[i]; mb+=T[i]; } ma/=n; mb/=n; let ab=0,aa=0,bb=0; for(let i=0;i<n;i++){ const a=D[i]-ma, b=T[i]-mb; ab+=a*b; aa+=a*a; bb+=b*b; } return aa>0&&bb>0?ab/Math.sqrt(aa*bb):0; }
function ecDetect(t,g){ const C=EC.cfg; EC.h.push({t,g}); while(EC.h.length&&EC.h[0].t<t-2000) EC.h.shift();
  const old=EC.h.filter(x=>x.t>t-1500&&x.t<=t-600); if(!old.length) return null;
  const D=new Float32Array(g.length); let m=0; for(let i=0;i<g.length;i++){ let b=255; for(const o of old) if(o.g[i]<b) b=o.g[i]; const d=g[i]-b; D[i]=d>0?d:0; m+=D[i]; } m/=g.length;
  let sc=0, ss=0; if(m>=C.minMean){ for(const T of EC_TPL){ const s=ecNcc(D,T); if(s>sc) sc=s; } if(C.shift) ss=Math.max(sc,ecNccShift(D)); }
  EC.last={t,sc:+sc.toFixed(3),ss:+ss.toFixed(3),m:+m.toFixed(1)}; EC.log.push(EC.last); while(EC.log.length&&EC.log[0].t<t-1000) EC.log.shift();
  const hit=EC.log.filter(x=>x.t>t-600&&x.sc>=C.th); if(hit.length>=C.hits||hit.some(x=>x.sc>=C.strong)) return hit[0];
  if(C.shift){ const L=EC.log.slice(-C.sN); if(L.length===C.sN&&L.every(x=>x.ss>=C.sTh)&&L[C.sN-1].t-L[0].t<=600){ let k=EC.log.length-C.sN; while(k>0&&EC.log[k-1].ss>=.5&&EC.log[k-1].t>t-1000) k--; return {t:EC.log[k].t,sc:L[C.sN-1].ss,kind:'shift'}; } } return null; } /* 시작 시각 = 점수가 .5 넘기 시작한 프레임(빔 첫 줄기) */
/* b361 (t671): 에픽빔이 캐릭터 위치(화면 중앙 아님)에서 터지면 고정 위치 NCC 가 낮음(01M6E78K: 0.48) → 템플릿을 x ±sx, y ±sy 칸 옮겨(겹치는 부분만) NCC.
   흔들림 오감지를 막으려고 옮긴 점수는 더 엄하게: 연속 sN(2) 프레임(0.6초 안) 모두 ≥sTh(.77) — 메인 스레드가 바빠 프레임이 드문드문해도 잡히게. 레퍼런스 47개 오감지 0(게이트 없이). */
function ecNccShift(D){ const C=EC.cfg; let best=0; const a=new Float32Array(576), b=new Float32Array(576);
  for(const T of EC_TPL) for(let dy=-C.sy;dy<=C.sy;dy++) for(let dx=-C.sx;dx<=C.sx;dx++){ if(!dx&&!dy) continue; let n=0;
    for(let y=Math.max(0,dy);y<18+Math.min(0,dy);y++) for(let x=Math.max(0,dx);x<32+Math.min(0,dx);x++){ a[n]=D[y*32+x]; b[n]=T[(y-dy)*32+(x-dx)]; n++; }
    const s=ecNcc(a.subarray(0,n),b.subarray(0,n)); if(s>best) best=s; }
  return best; }
/* b361 (t671): 국소 세로 빛기둥(미트라 등 아이템 위 기둥형 에픽빔) 감지 — 240p 프레임에서 배경(0.6~1.5초 전 최솟값) 대비 새로 생긴 밝은·무채색 픽셀(g≥190, 채도≤70, D≥35) 중
   폭 ≤5px·양옆(±7~16px) 비어 있음·위쪽 80% 높이의 ≥88% 를 잇는 세로 줄이 3프레임 연속 같은 자리(±6px) → 감지. 레퍼런스 47개 오감지 0. */
function ecPilFeat(px,bg,W,H){ const R=Math.floor(H*.8), m=new Uint8Array(W*R), cs=new Int32Array(W);
  for(let y=0;y<R;y++) for(let x=0;x<W;x++){ const i=y*W+x, k=i*4, r=px[k], gg=px[k+1], b=px[k+2], gv=((r*3+gg*6+b)/10)|0, mx=Math.max(r,gg,b), mn=Math.min(r,gg,b);
    if(gv>=190&&mx-mn<=70&&gv-bg[i]>=35){ m[i]=1; cs[x]++; } }
  const ord=Array.from(cs.keys()).sort((a,b)=>cs[b]-cs[a]).slice(0,12); let best={sc:0,x:0,wid:0};
  for(const x of ord){ if(x<8||x>=W-8||!cs[x]) continue; let run=0,mr=0;
    for(let y=0;y<R;y++){ const o=y*W; if(m[o+x-1]||m[o+x]||m[o+x+1]){ run++; if(run>mr) mr=run; } else run=0; }
    let sm=0; for(let j=Math.max(0,x-16);j<Math.max(0,x-6);j++) sm=Math.max(sm,cs[j]); for(let j=x+7;j<Math.min(W,x+17);j++) sm=Math.max(sm,cs[j]);
    let wid=0; for(let j=Math.max(0,x-6);j<x+7&&j<W;j++) if(cs[j]>=.5*cs[x]) wid++;
    const sc=(sm<=.35*cs[x]&&wid<=EC.cfg.pilWid)?mr/R:0; if(sc>best.sc) best={sc,x,wid}; }
  return best; }
function ecPillar(t,px,W,H){ const C=EC.cfg, n=W*H, gy=new Uint8Array(n); for(let i=0;i<n;i++){ const k=i*4; gy[i]=((px[k]*3+px[k+1]*6+px[k+2])/10)|0; }
  if(!EC.ph.length||EC.ph[0].W!==W||EC.ph[0].H!==H){ EC.ph=[]; EC.pl=[]; }
  const old=EC.ph.filter(o=>o.t>t-1550&&o.t<=t-550); EC.ph.push({t,g:gy,W,H}); while(EC.ph.length&&EC.ph[0].t<t-1600) EC.ph.shift();
  if(!old.length) return null; const bg=new Uint8Array(n).fill(255); for(const o of old){ const a=o.g; for(let i=0;i<n;i++) if(a[i]<bg[i]) bg[i]=a[i]; }
  const b=ecPilFeat(px,bg,W,H); EC.lastPil={t,sc:+b.sc.toFixed(3),x:b.x,wid:b.wid}; EC.pl.push(EC.lastPil); while(EC.pl.length>3) EC.pl.shift();
  if(EC.pl.length<3||EC.pl.some(h=>h.sc<C.pilTh)) return null; const xs=EC.pl.map(h=>h.x); if(Math.max(...xs)-Math.min(...xs)>6) return null;
  return {t:EC.pl[0].t,sc:EC.pl[2].sc,kind:'pillar',x:EC.pl[2].x}; }
function ecRewardMap(now){ if(!EC.cfg.rewardOnly) return ARX.det.boss||''; const M=ARX.mapSt, d=now-(M&&M.t||0); return M&&M.kind.includes('r')&&d<8000&&M.boss===ARX.det.boss?M.boss:''; }
function ecCtx(now){ if(typeof ARX==='undefined'||!ARX.det||!ARX.det.boss) return null; if(!EC.cfg.gate) return {boss:ARX.det.boss,diff:ARX.det.diff||''};
  /* b382: '상자로 추정한 보상 상태'/'전투 맵 60초'는 영상 기록 근거가 아니다. 맵 그림·OCR이 실제 보상 맵인 순간에만 저장. */
  let rew=!!(ecRewardMap(now)); if(!EC.cfg.rewardOnly) rew=!!(ARX.rew&&ARX.rew.boss===ARX.det.boss);
  return rew?{boss:ARX.det.boss,diff:ARX.det.diff||(ARX.mapSt&&ARX.mapSt.diff)||''}:null; } /* b382: 실제 보상 맵 확정 전엔 저장 안 함 — 전투 스킬·밝은 UI 오감지 방지 */
function ecGrid(px,W,H){ const gr=new Float32Array(576), n=new Float32Array(576); for(let y=0;y<H;y++){ const cy=Math.min(17,(y*18/H)|0); for(let x=0;x<W;x++){ const k=(y*W+x)*4, c=cy*32+Math.min(31,(x*32/W)|0); gr[c]+=px[k]*.3+px[k+1]*.59+px[k+2]*.11; n[c]++; } }
  for(let i=0;i<576;i++) gr[i]/=n[i]||1; return gr; }
function ecTick(){ const v=typeof ARX!=='undefined'&&(ARX.video?(typeof arSrc==='function'?arSrc():ARX.video):ARX.testSrc); /* b366 */ if(!v||!(v.videoWidth||v.width)){ if(EC.buf.length){ EC.buf=[]; EC.h=[]; EC.log=[]; EC.ph=[]; EC.pl=[]; } return; }
  const C=EC.cfg, vw=v.videoWidth||v.width, vh=v.videoHeight||v.height, now=Date.now(), vt=+(v.currentTime||0);
  const H=Math.min(C.H,vh), W=Math.round(H*vw/vh), H0=Math.min(C.H0,vh), W0=Math.round(H0*vw/vh); if(!EC.cv){ EC.cv=document.createElement('canvas'); EC.sm=document.createElement('canvas'); EC.dc=document.createElement('canvas'); EC.dc.width=32; EC.dc.height=18; }
  const cv=EC.cv; if(cv.width!==W||cv.height!==H){ cv.width=W; cv.height=H; }
  const sm=EC.sm; if(sm.width!==W0||sm.height!==H0){ sm.width=W0; sm.height=H0; }
  const g=cv.getContext('2d'), sg=sm.getContext('2d'); try{ g.drawImage(v,0,0,W,H); sg.drawImage(v,0,0,W0,H0); }catch(e){ return; }
  /* b383: 감지 240p, 캡처 최대 540p 분리. 최종 해상도·품질·fps는 저장 직후 실제 용량으로 결정. */
  const f={t:now,vt,p:new Promise(r=>cv.toBlob(r,'image/webp',C.q))}; EC.buf.push(f);
  const img=sg.getImageData(0,0,W0,H0).data, gr=ecGrid(img,W0,H0); /* b361: 32x18 은 칸 평균(area) — drawImage 축소는 표본 추출이라 빔 점수가 흔들림(0.48 vs 0.64) */
  let hit=ecDetect(now,gr); if(C.pil){ let ph=null; try{ ph=ecPillar(now,img,W,H); }catch(e){} if(!hit&&ph) hit=ph; }
  if(hit&&!EC.cur&&now-EC.cool>C.cool&&!EC.pend) EC.pend=hit; if(EC.pend&&now-EC.pend.t>C.pendMs) EC.pend=null; /* b361: 보상 맵 인식이 빔보다 늦게(01M6E78K: 빔 8.9초, 보상 맵 8.86~9.1초) 되어도 2초 안이면 그 빔으로 */
  if(!EC.cur&&EC.pend&&now-EC.cool>C.cool){ const hit=EC.pend, ctx=ecCtx(now); if(ctx){ EC.pend=null; const h0=EC.buf.find(x=>x.t>=hit.t)||f; EC.cool=now; EC.cur={t0:h0.t,vt0:h0.vt,sc:hit.sc,kind:hit.kind||'beam',...ctx,w:W,h:H}; } }
  if(EC.cur&&now>=EC.cur.t0+C.post){ const c=EC.cur; EC.cur=null; ecSave(c,EC.buf.filter(x=>x.t>=c.t0-C.pre&&x.t<c.t0+C.post)); }
  const keep=EC.cur?EC.cur.t0-C.pre:EC.pend?EC.pend.t-C.pre:now-C.pre-400; while(EC.buf.length&&EC.buf[0].t<keep) EC.buf.shift(); }
function ecRecFor(c){ const L=EC.recs.filter(r=>r.bid===c.boss&&r.t>=c.t0-EC.cfg.linkBefore&&r.t<=c.t0+EC.cfg.linkAfter&&!r.used); L.sort((a,b)=>Math.abs(a.t-c.t0)-Math.abs(b.t-c.t0)); return L[0]||null; }
function ecLink(m,r){ r.used=1; Object.assign(m,{item:r.k,cid:r.cid||m.cid,cname:r.cname||m.cname,diff:r.diff||m.diff,recT:r.t}); }
async function ecSave(c,fr){ const C0=EC.cfg; let blobs=(await Promise.all(fr.map(x=>x.p))), ok=fr.map((x,i)=>[x,blobs[i]]).filter(x=>x[1]); if(!ok.length) return;
  /* b383: 빔·아이템 오버레이가 뜨는 가운데 영역을 크롭해 정적인 테두리는 버리고 글자 픽셀을 보존.
     저장한 파일 전체를 측정해 이전 4초 측정치보다 여유있는 800,000B를 최종 ECB1 예산으로 강제.
     같은 캡처라도 장면 복잡도가 다르므로 실패하면 화면·fps·품질을 내려 표면적인 설정만 믿지 않는다. */
  async function ecEncFit(list,frac,q,skip){ const to=list.filter((_,i)=>i%skip===0), cv=document.createElement('canvas');cv.width=Math.round(c.w*frac);cv.height=Math.round(c.h*frac);const g=cv.getContext('2d'),sx=(c.w-cv.width)/2,sy=(c.h-cv.height)/2,fs=[];
    for(const [f,b] of to){ const im=await createImageBitmap(b); g.drawImage(im,sx,sy,cv.width,cv.height,0,0,cv.width,cv.height); im.close(); const nb=await new Promise(ok=>cv.toBlob(ok,'image/webp',q));fs.push([f,nb]); }
    return{ts:fs.map(x=>x[0].t),vt:fs.map(x=>x[0].vt),blobs:fs.map(x=>x[1]),H:cv.height,W:cv.width,q,fps:+(C0.fps/skip).toFixed(2)}; }
  if(C0.maxBytes){ let fit=null, packed=Infinity, raw;
    outer: for(const frac of [.8,.7,.6,.5]) for(const skip of [1,2,3]) for(const q of [.6,.5,.4,.3]){ fit=await ecEncFit(ok,frac,q,skip);const F={ts:fit.ts,vt:fit.vt,f:fit.blobs};packed=(await ecPack(F)).size;if(packed<=C0.maxBytes) break outer; }
    if(packed>C0.maxBytes){fit=await ecEncFit(ok,.4,.2,6);raw={ts:fit.ts,vt:fit.vt,f:fit.blobs};packed=(await ecPack(raw)).size;} /* 복잡도 극한: 마지막 단계도 실제 ECB1 확인 */
    ok=fit.blobs.map((b,i)=>[{t:fit.ts[i],vt:fit.vt[i]},b]);raw={ts:ok.map(x=>x[0].t-c.t0),vt:fit.vt,f:fit.blobs};packed=(await ecPack(raw)).size;c.w=fit.W;c.h=fit.H;EC.lastFit={...fit,crop:+(fit.W/(c.w/fit.W)).toFixed(2),packed}; }
  blobs=ok.map(x=>x[1]);
  const id='ec'+c.t0, mid=ok.reduce((b,x,i)=>Math.abs(x[0].t-c.t0)<Math.abs(ok[b][0].t-c.t0)?i:b,0), pi=Math.min(ok.length-1,mid+3), poster=ok[pi][1];
  let cid='',cname=''; try{ const a=typeof activeChar==='function'?activeChar():null; if(ARX.det.cid){ const x=S.characters.find(z=>z.id===ARX.det.cid); if(x){ cid=x.id; cname=x.name; } } else if(a){ cid=a.id; cname=a.name; } }catch(e){}
  const m={id,t0:c.t0,vt0:c.vt0,boss:c.boss,diff:c.diff,item:'',cid,cname,sc:c.sc,w:c.w,h:c.h,n:ok.length,start:ok[0][0].t-c.t0,end:ok[ok.length-1][0].t-c.t0,vts:[ok[0][0].vt,ok[ok.length-1][0].vt],poster,pi,up:0,bytes:EC.lastFit&&EC.lastFit.packed||blobs.reduce((s,b)=>s+(b?b.size:0),0)};
  const r=ecRecFor(m); if(r) ecLink(m,r);
  await ecTx(['meta','frames'],'readwrite',t=>{ t.objectStore('meta').put(m); t.objectStore('frames').put({id,ts:ok.map(x=>x[0].t-c.t0),vt:ok.map(x=>x[0].vt),f:ok.map(x=>x[1])}); });
  try{ if(typeof arLog==='function') arLog(`에픽빔 감지 → ${Math.round((C0.pre+C0.post)/1000)}초 클립 저장 (${ok.length}프레임)`); }catch(e){}
  EC.saved=(EC.saved||0)+1; if(typeof tab!=='undefined'&&tab==='epic') renderEpic(); ecSync(); }
/* 자동 기록 연결: arSessAdd(아이템 키, 보스 이름, 캐릭터 이름) 를 감쌈 — 시간 창 안의 클립(같은 보스)에 붙임 */
function ecOnRec(k,bn,cn){ const now=Date.now(), b=(typeof BOSSES!=='undefined'?BOSSES:[]).find(x=>x.name===bn||x.id===bn), c=(S.characters||[]).find(x=>x.name===cn);
  const r={t:now,k,bid:b?b.id:(ARX.det&&ARX.det.boss)||'',diff:(ARX.det&&ARX.det.diff)||'',cid:c?c.id:'',cname:cn||''}; EC.recs.push(r); while(EC.recs.length>50) EC.recs.shift();
  ecList().then(async L=>{ const m=L.filter(x=>!x.item&&x.boss===r.bid&&now>=x.t0-EC.cfg.linkBefore&&now<=x.t0+EC.cfg.linkAfter).sort((a,b)=>Math.abs(a.t0-now)-Math.abs(b.t0-now))[0]; if(m){ ecLink(m,r); if(m.up===1) m.up=0; await ecPutMeta(m); if(tab==='epic') renderEpic(); ecSync(); } }).catch(()=>{}); }
(()=>{ const o=window.arSessAdd; if(typeof o==='function'&&!o.ecWrap){ const w=function(k,bn,cn){ const out=o.apply(this,arguments); try{ ecOnRec(k,bn,cn); }catch(e){} return out; }; w.ecWrap=1; window.arSessAdd=w; } })();

/* ---------- b354: 서버 저장 (Cloudflare R2 + D1, server/worker.js /api/epic/*) ----------
   계정 = 사이트 동기화와 같은 로그인(넥슨 API 키 → /api/login 세션 토큰 svTok()). 서버는 넥슨 계정 해시(acct_hash)로 묶음 → 다른 PC 에서 같은 키로 로그인하면 보임.
   이 PC IndexedDB 는 캐시·오프라인 보관(up:0 = 올릴 것). 다시 연결(online)·로그인·탭 열기·5분마다 올림. 서버에 R2 가 없으면(503 r2_off) 이 PC 저장만. 어디서도 자동 삭제 없음.
   묶음 형식(ECB1): 'ECB1' + u32le(헤더 길이) + 헤더 JSON {ts,vt,sz} + JPEG 들 이어붙임. 최대 2MB(서버 제한). */
const ECC={st:'',busy:false,again:false,last:0,tok:'',pull:0};
const EC_MAXUP=2*1024*1024;
const ecApi=()=>{ try{ return typeof SV_ON!=='undefined'&&SV_ON&&typeof svTok==='function'&&svTok()?SV_ON:''; }catch(e){ return ''; } };
function ecCloudTxt(){ return {ok:'',off:'💾 이 PC 에만 저장 (서버 클립 저장소 준비 중)',nolog:'💾 이 PC 에만 저장 — 로그인하면 서버에도 올려요',net:'💾 오프라인 — 다시 연결되면 올려요'}[ECC.st] ?? '💾 이 PC 에 저장'; } /* b356: 서버 저장(ok) 안내 문구 없앰 — 카드 ☁ 배지만 */
function ecBadge(m){ return m.remote&&!m.poster?'':(m.up===1?'<span class="ecup on" title="서버에 저장됨">☁</span>':m.up===-1?'<span class="ecup bad" title="너무 커서 이 PC 에만">💾</span>':'<span class="ecup" title="서버에 올릴 예정">⏳</span>'); }
async function ecPack(F){ const bufs=await Promise.all(F.f.map(b=>b.arrayBuffer())), hd=new TextEncoder().encode(JSON.stringify({ts:F.ts,vt:F.vt,sz:bufs.map(b=>b.byteLength)})), h=new Uint8Array(8);
  h.set([69,67,66,49]); new DataView(h.buffer).setUint32(4,hd.length,true); return new Blob([h,hd,...bufs],{type:'application/octet-stream'}); }
function ecUnpack(ab){ const u=new Uint8Array(ab); if(u[0]!==69||u[1]!==67||u[2]!==66||u[3]!==49) throw new Error('bad clip'); const n=new DataView(ab).getUint32(4,true), hd=JSON.parse(new TextDecoder().decode(u.subarray(8,8+n)));
  const old=hd.sz.every((z,i)=>{const o=8+n+hd.sz.slice(0,i).reduce((a,b)=>a+b,0); return u[o]===255&&u[o+1]===216;});
  let o=8+n; const f=hd.sz.map(z=>{ const b=new Blob([u.subarray(o,o+z)],{type:old?'image/jpeg':'image/webp'}); o+=z; return b; }); return {ts:hd.ts,vt:hd.vt,f}; }
/* b382: 기록지는 공통 avatar()를 그대로 사용하고(넥슨 초상화 유지), 실패한 img 만 빈 원 대신 닉네임 이니셜로. */
const ecAvatar=c=>{ const cc={...(c||{}),image:safeImg(c&&c.image)?c.image:''}, letter=esc((c&&c.name||'?').slice(0,1));
  return avatar(cc,'ecav').replace('onerror="this.remove()"','onerror="ecAvErr(this)"').replace('<img ','<img data-ecletter="'+letter+'" '); };
function ecAvErr(im){ const b=document.createElement('b'); b.className='ecfb'; b.textContent=im.dataset.ecletter||'?'; im.replaceWith(b); }
const ecMetaOut=m=>{ const {poster,up,remote,...r}=m; return r; };
async function ecReq(path,opt={}){ const api=ecApi(); if(!api) return {status:0}; let r; try{ r=await fetch(api+path,{...opt,headers:{...(opt.headers||{}),Authorization:'Bearer '+svTok()}}); }catch(e){ return {status:-1}; } return r; }
async function ecUpOne(m){ const F=await ecFrames(m.id); if(!F) return {status:404}; const b=await ecPack(F); if(b.size>EC_MAXUP) return {status:413};
  return ecReq('/api/epic/clip?id='+encodeURIComponent(m.id),{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Epic-Meta':encodeURIComponent(JSON.stringify(ecMetaOut(m)))},body:b}); }
async function ecFetch(m){ const r=await ecReq('/api/epic/clip/'+encodeURIComponent(m.id)); if(!r.ok) throw new Error('fetch '+r.status); const F=ecUnpack(await r.arrayBuffer());
  const poster=F.f[Math.min(F.f.length-1,m.pi!=null?m.pi:Math.round(F.f.length/2))]; const mm={...m,poster,up:1};
  await ecTx(['meta','frames'],'readwrite',t=>{ t.objectStore('meta').put(mm); t.objectStore('frames').put({id:m.id,...F}); }); return {id:m.id,...F}; }
async function ecPosters(L){ for(const m of L.slice(0,12)){ try{ await ecFetch(m); }catch(e){ return; } } if(L.length&&typeof tab!=='undefined'&&tab==='epic') renderEpic(); }
function ecSyncSoon(){ if(Date.now()-ECC.last>30000) ecSync(); }
async function ecSync(){ if(ECC.busy){ ECC.again=true; return; } const api=ecApi(), st0=ECC.st; ECC.last=Date.now(); ECC.tok=ecApi()?svTok():'';
  if(!api){ ECC.st='nolog'; if(st0!==ECC.st&&typeof tab!=='undefined'&&tab==='epic') renderEpic(); return; }
  ECC.busy=true; let ch=false;
  try{ let L=await ecList(); outer:{
    for(const m of L.filter(x=>!x.up&&!x.remote).sort((a,b)=>a.t0-b.t0)){ const r=await ecUpOne(m);
      if(r.status===503){ ECC.st='off'; break outer; } if(r.status===-1){ ECC.st='net'; break outer; } if(r.status===401||r.status===403||r.status===0){ ECC.st='nolog'; break outer; }
      if(r.status===429){ ECC.st='ok'; setTimeout(ecSync,60000); break; }
      if(r.ok||r.status===413||r.status===400){ m.up=r.ok?1:-1; await ecPutMeta(m); ch=true; } }
    // 서버 목록(12개씩) → 이 PC 에 없는 클립 메타 받아 둠 (영상은 볼 때·미리보기 때 받음)
    const have=new Set(L.map(x=>x.id));
    for(let pgn=0;pgn<200;pgn++){ const r=await ecReq(`/api/epic/clips?page=${pgn}&per=${EC.cfg.per}`); if(r.status===503){ ECC.st='off'; break outer; } if(r.status===-1){ ECC.st='net'; break outer; } if(!r.ok){ ECC.st='nolog'; break outer; }
      const b=await r.json(); let nw=0; for(const it of b.items||[]){ if(have.has(it.id)) continue; nw++; have.add(it.id); await ecPutMeta({...it,remote:1,up:1}); ch=true; }
      ECC.st='ok'; if(!nw&&pgn>0||(pgn+1)*b.per>=b.total) break; }
  } }catch(e){ console.warn('[에픽빔 서버]',e); }
  finally{ ECC.busy=false; }
  if((ch||st0!==ECC.st)&&typeof tab!=='undefined'&&tab==='epic') renderEpic();
  if(ECC.again){ ECC.again=false; setTimeout(ecSync,500); } }
addEventListener('online',()=>ecSync());
setInterval(()=>{ try{ const t=ecApi()?svTok():''; if(t!==ECC.tok||Date.now()-ECC.last>300000) ecSync(); }catch(e){} },5000); /* 로그인(토큰 바뀜) 감지 → 바로 올림 · 5분마다 */
/* 화면 */
const ecWhen=t=>{ const d=new Date(t); const p=n=>String(n).padStart(2,'0'); return `${d.getFullYear()}.${p(d.getMonth()+1)}.${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`; }; /* 사이트 시간대 = KST(브라우저) */
const EC_URL=new Map();
const ecUrl=(id,b)=>{ if(!EC_URL.has(id)) EC_URL.set(id,URL.createObjectURL(b)); return EC_URL.get(id); };
function ecCard(m,i){ const b=BOSSES.find(x=>x.id===m.boss), c=(S.characters||[]).find(x=>x.id===m.cid), it=m.item&&ITEMS[m.item];
  return `<button class="eccard" data-ecopen="${esc(m.id)}" type="button"><div class="ecthumb">${m.poster?`<img src="${ecUrl(m.id,m.poster)}" alt="">`:'<span class="ecload">불러오는 중…</span>'}<span class="ecplay">▶</span><span class="ecdur">${Math.max(1,Math.round(((m.end||0)-(m.start||0)+100)/1000))}s</span>${ecBadge(m)}</div>
  <div class="ectl"><div class="ecl1"><span>${esc(ecWhen(m.t0))}</span></div>
  <div class="ecl2"><i class="ecic">${b?bossIcon(b):'<span class="ecq">?</span>'}</i><span>${esc(b?b.name:m.boss)}${m.diff?` (${esc(EC_DIFF[m.diff]||m.diff)})`:''}</span></div>
  <div class="ecl3"><i class="ecic">${it?itemIcon(m.item):'<span class="ecq">?</span>'}</i><span>${it?esc(it.n):'아이템 확인 전'}</span></div>
  <div class="ecl4"><i class="ecic">${c?ecAvatar(c):'<span class="ecq">?</span>'}</i><span>${esc(c?c.name:(m.cname||'캐릭터 미확인'))}</span></div></div></button>`; }
async function renderEpic(){ const v=$('#view'); if(!v) return; let L=[]; ecSyncSoon(); try{ L=await ecList(); }catch(e){ v.innerHTML='<div class="card ecwrap"><p>이 브라우저는 IndexedDB 를 쓸 수 없어 에픽빔 클립을 저장할 수 없어요.</p></div>'; return; }
  if(typeof tab!=='undefined'&&tab!=='epic') return;
  const P=EC.cfg.per, np=Math.max(1,Math.ceil(L.length/P)); EC.page=Math.min(Math.max(0,EC.page),np-1); const pg=L.slice(EC.page*P,EC.page*P+P);
  const live=typeof arLive==='function'&&arLive();
  v.innerHTML=`<div class="card ecwrap"><div class="echd"><h2><img class="ecico" src="${EC_ICON}" alt="">에픽빔 기록지</h2><span class="ecsub">보상 맵에서 에픽빔이 뜨면 처음 보인 순간 1초 전부터 4초를 저장해요 · ${L.length}개</span>${ecCloudTxt()?`<span class="eccloud ${ECC.st}">${ecCloudTxt()}</span>`:''}<span class="ecst ${live?'on':''}">${live?'● 화면 공유 감시 중':'○ 자동 기록 탭에서 화면 공유를 연결하면 감시해요'}</span></div>
  ${L.length?`<div class="ecgrid">${pg.map(ecCard).join('')}</div>`:'<div class="ecempty">아직 저장된 에픽빔 영상이 없어요.</div>'}
  ${np>1?`<div class="ecpg">${Array.from({length:np},(_,i)=>`<button type="button" class="ecpb${i===EC.page?' on':''}" data-ecpg="${i}">${i+1}</button>`).join('')}</div>`:''}</div>`;
  ecPosters(pg.filter(m=>!m.poster&&m.remote)); }
async function ecOpen(id){ const m=(await ecList()).find(x=>x.id===id); let F=await ecFrames(id); if(m&&!F&&m.remote) F=await ecFetch(m).catch(()=>null); if(!m||!F) return; ecClose();
  const ov=document.createElement('div'); ov.id='ecModal'; ov.className='ecmodal'; ov.innerHTML=`<div class="ecbox"><button class="ecx" type="button" aria-label="닫기">✕</button><canvas width="${m.w}" height="${m.h}"></canvas><div class="ecbar"><i></i></div><div class="ecmeta">${ecCard(m).replace(/^<button[^>]*>/,'').replace(/<div class="ecthumb">[\s\S]*?<\/div>/,'').replace(/<\/button>$/,'')}<span class="ectime">${((F.ts[0]||0)/1000).toFixed(1)}s</span></div></div>`;
  document.body.appendChild(ov); const cv=ov.querySelector('canvas'), g=cv.getContext('2d'), bar=ov.querySelector('.ecbar i'), tl=ov.querySelector('.ectime');
  const imgs=await Promise.all(F.f.map(b=>createImageBitmap(b).catch(()=>null))); const T0=F.ts[0], dur=F.ts[F.ts.length-1]-T0+100; let st=performance.now(), k=-1;
  const loop=now=>{ if(!ov.isConnected){ imgs.forEach(x=>x&&x.close&&x.close()); return; } const e=(now-st)%dur; let j=0; while(j+1<F.ts.length&&F.ts[j+1]-T0<=e) j++; if(j!==k&&imgs[j]){ k=j; g.drawImage(imgs[j],0,0,cv.width,cv.height); bar.style.width=(e/dur*100).toFixed(1)+'%'; tl.textContent=((F.ts[j])/1000).toFixed(1)+'s'; } ov._f=j; requestAnimationFrame(loop); };
  requestAnimationFrame(loop); ov.addEventListener('click',e=>{ if(e.target===ov||e.target.closest('.ecx')) ecClose(); }); }
function ecClose(){ document.getElementById('ecModal')?.remove(); }
document.addEventListener('click',e=>{ const o=e.target.closest('[data-ecopen]'); if(o){ ecOpen(o.dataset.ecopen); return; } const p=e.target.closest('[data-ecpg]'); if(p){ EC.page=+p.dataset.ecpg; renderEpic(); } });
document.addEventListener('keydown',e=>{ if(e.key==='Escape') ecClose(); });
EC.timer=setInterval(()=>{ try{ ecTick(); }catch(e){ console.warn('[에픽빔]',e); } },Math.round(1000/EC.cfg.fps));
window.ecSave=ecSave; window.EC=EC; window.ECC=ECC; window.ecGrid=ecGrid; window.ecNcc=ecNcc; window.ecTick=ecTick; window.ecCtx=ecCtx; window.ecSync=ecSync; window.ecPack=ecPack; window.ecUnpack=ecUnpack; window.renderEpic=renderEpic; window.ecOnRec=ecOnRec; window.ecList=ecList; window.ecFrames=ecFrames;
try{ if(typeof tab!=='undefined'&&tab==='epic') render(); }catch(e){}
