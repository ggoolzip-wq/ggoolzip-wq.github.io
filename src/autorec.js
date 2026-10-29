/* ===== b283: 게임 화면 연결 → 자동 기록 (뼈대) =====
 * 화면 공유(getDisplayMedia) 프레임을 브라우저 안에서만 분석 — 프레임은 어디에도 올리지 않음.
 *  · 아이템 = 드롭 표 아이템 아이콘(ITEM_ICONS) 템플릿 매칭 (바닥에 떨어진 아이콘 · 획득 알림 아이콘)
 *  · 보스·난이도 = 미니맵 맵 이름 OCR (tesseract.js + kor, ./ocr/ 에서 연결할 때만 불러옴)
 *  · 캐릭터 = 화면 캐릭터 이름 OCR → 등록된 캐릭터와 비슷한 이름
 *  · 인식 실패 시 패널의 수동 선택(캐릭터·보스) 사용
 * 기록은 수동 칩 누르기와 같은 changeDrop(key,+1) (같은 저장 키·시세 자동·합계). 이미 기록된 건 건드리지 않음.
 * 조정값은 전부 AR_DEF (localStorage 'mbt_autorec') — 실제 게임 화면을 받은 뒤 여기서 튜닝. */
const AR_KEY='mbt_autorec';
/* b284: 실제 화면(1920x1080, 13장) 기준으로 튜닝. 영역은 전부 화면 비율이라 해상도와 무관.
 *  1순위 = 오른쪽 아래 획득 로그 OCR ('<아이템>.. 아이템을 N 개 얻었습니다') — 자주(logFps) 잘라 읽고, 이전 프레임 줄과 맞춰 새 줄만 1번씩 셈.
 *  2순위 = 가운데 획득 배너('<아이템>를 획득했습니다.') 아이콘 매칭 + 바닥 아이콘 — 로그와 같은 아이템이면 dedup 으로 한 번만. */
const AR_DEF={on:true, fps:3, ocrEvery:3000, logFps:6, stickySec:600,
  item:{x:.15,y:.25,w:.7,h:.7},   // 바닥 아이콘 찾는 영역 (화면 비율)
  banner:{x:.25,y:.1,w:.5,h:.2},  // 가운데 획득 배너 (아이콘)
  log:{x:.68,y:.55,w:.32,h:.33},  // 오른쪽 아래 획득 로그 (OCR, 1순위)
  map:{x:0,y:0,w:.2,h:.08},       // 왼쪽 위 미니맵 제목 '지역 맵이름 <난이도>' (b285: 미니맵 펼친 배치는 제목이 두 줄로 아래에 있음)
  name:{x:0,y:.957,w:.2,h:.026},  // 왼쪽 아래 상태바 'Lv.285 캐릭터' (이름표는 파티원도 있어서 안 씀)
  iconPx:0,       // 바닥 아이콘 템플릿 크기(px) 0 = 자동 (1080 높이에서 36px, 미검증)
  bannerPx:0,     // 배너 아이콘 템플릿 크기(px) 0 = 자동 (1080 높이에서 46px — 실제 화면 13장으로 맞춤)
  margin:.04,     // 1등 아이콘이 2등보다 이만큼 높아야 인정
  ds:4,           // 대략 찾기 축소 배율
  thr:.84,        // 아이콘 일치 점수 (NCC, -1~1) 기준 — 실제 배너: 정답 .88 / 닮은 상자 .80 / 배너 없음 < .5
  confirm:2,      // 연속 프레임 수
  bannerThr:.7,   // b286: 배너 순간 감시(바뀐 프레임만) 기준 — 보상이 한꺼번에 오면 배너 하나가 1프레임(33ms)만 보임 (v01 백옥 .76)
  watchFps:30,    // b286: 배너 변화 감시 횟수/초 (작은 축소본 비교만, 바뀐 프레임만 아이콘 매칭)
  dedupSec:120,   // 같은 아이템 다시 기록 막는 시간
  nameThr:.5, mapAlias:{}, cid:'', boss:''};
/* 맵 이름 → 보스 (미니맵 제목에 보스 이름이 없는 맵). 난이도는 제목 끝 <노멀>/<하드>/<익스트림>... 에서 읽음 */
const AR_MAPS=[['잠든환상','star'],['고요해진함선','lotus'],['흉성','star'],
  // b285: 실제 영상 미니맵 제목 (지역 + 맵). 둘 중 하나만 읽혀도 되게 두 단어씩
  ['증명의전장','adversary'],['의지가증명된','adversary'],['고통의미궁','jinhilla'],['욕망의제단','jinhilla'],['끝에가까운곳','dunkel'],
  ['카로테마천루','kalos'],['문브릿지','dusk'],['공허의눈','dusk'],['라무라무','slime'],['고요한제단','slime'],['솔라툼골짜기','bellona'],['솔라툼의유산','bellona'],
  ['세르니움왕궁','seren'],['왕궁메인홀','seren'],['도원경','kaling'],['빛을되찾은사계','kaling'],['에스페라','will'],['바스러지는빛','will'],
  ['타락한세계수','damien'],['세계수정상','damien'],['레헬른','lucid'],['악몽의시계탑','lucid'],['블랙헤븐','lotus']];
const AR_DIFFW=[['익스트림','extreme'],['카오스','chaos'],['노멀','normal'],['노말','normal'],['하드','hard'],['이지','easy']];
const ARX={logPrev:[], lastLog:0, logText:'', logBusy:false, counted:[], cfg:null, stream:null, video:null, timer:0, busy:false, ocr:null, ocrP:null, lastOcr:0, mapText:'', nameText:'',
  det:{cid:'',boss:'',diff:'',src:''}, hits:{}, recent:{}, recentVia:{}, log:[], tpl:null, tplKey:'', lastScore:[]};
try{ ARX.cfg=Object.assign({},AR_DEF,JSON.parse(localStorage.getItem(AR_KEY)||'{}')); }catch(e){ ARX.cfg=Object.assign({},AR_DEF); }
if(!ARX.cfg.v285){ ARX.cfg.v285=1; const m=ARX.cfg.map; if(m&&m.h===.045&&!m.y) m.h=AR_DEF.map.h; if(ARX.cfg.logFps===4) ARX.cfg.logFps=AR_DEF.logFps; } // b285: 예전 기본값 저장된 경우만 새 기본값으로
const arSave=()=>{ try{ localStorage.setItem(AR_KEY,JSON.stringify(ARX.cfg)); }catch(e){} };
const arNorm=s=>String(s||'').replace(/[^0-9a-zA-Z가-힣\u1100-\u11FF]/g,'');
function arLev(a,b){ const m=a.length,n=b.length; if(!m) return n; if(!n) return m; let p=[...Array(n+1).keys()];
  for(let i=1;i<=m;i++){ const q=[i]; for(let j=1;j<=n;j++) q[j]=Math.min(p[j]+1,q[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1)); p=q; } return p[n]; }
/* 한글을 자모로 풀어서 비교 (OCR 이 '터→더', '솔→플' 처럼 획 하나 틀리는 걸 부분 점수로) */
function arJamo(s){ let o=''; for(const ch of String(s||'')){ const c=ch.charCodeAt(0)-0xAC00; if(c>=0&&c<11172){ o+=String.fromCharCode(0x1100+Math.floor(c/588),0x1161+Math.floor(c%588/28)); if(c%28) o+=String.fromCharCode(0x11A7+c%28); } else o+=ch; } return o; }
function arSimJ(text,word){ return arSim(arJamo(arNorm(text)),arJamo(arNorm(word))); }
function arSim(text,word){ const t=arNorm(text), w=arNorm(word); if(!t||!w) return 0; if(t.includes(w)) return 1; let best=0;
  for(let L=Math.max(1,w.length-1);L<=w.length+1;L++) for(let i=0;i+L<=t.length;i++) best=Math.max(best,1-arLev(t.slice(i,i+L),w)/w.length);
  if(t.length<w.length) best=Math.max(best,1-arLev(t,w)/w.length); return best; }
/* 보스·난이도: 사용자가 묶은 맵 이름 → 보스 이름 들어 있음 → 난이도 글자 */
function arDetectBoss(text){ const t=arNorm(text); if(!t) return null;
  for(const [k,v] of Object.entries(ARX.cfg.mapAlias||{})) if(arSim(t,k)>=.8) return {boss:v.boss,diff:v.diff,src:'맵 등록'};
  const diffOf=b=>{ for(const [w,k] of AR_DIFFW) if(t.includes(w)&&b.diffs.includes(k)) return k; // b285: '<미지>'(이지)·'<노말>' 같은 OCR 변형 → 괄호 안을 자모로 비교
    const m=String(text).match(/<\s*([^<>]{1,6})\s*>?\s*$/m)||String(text).match(/<\s*([^<>]{1,6})\s*>/); if(!m) return ''; let best=null;
    for(const [w,k] of AR_DIFFW){ if(!b.diffs.includes(k)) continue; const s=arSimJ(m[1],w); if(s>=.6&&(!best||s>best.s)) best={k,s}; } return best?best.k:''; };
  for(const [m,id] of AR_MAPS) if(arSim(t,m)>=.8||(m.length>=3&&arSimJ(t,m)>=.85)){ const b=findBoss(id); if(b) return {boss:id,diff:diffOf(b),src:'맵 이름'}; }
  let best=null; for(const b of BOSSES){ const s=arSim(t,b.name); if(s>=.75&&(!best||s>best.s||(s===best.s&&b.name.length>best.b.name.length))) best={b,s}; }
  if(!best) return null; let diff=''; for(const [k,v] of Object.entries(D)) if(t.includes(v)&&best.b.diffs.includes(k)) diff=k; if(!diff&&t.includes('노멀')&&best.b.diffs.includes('normal')) diff='normal';
  return {boss:best.b.id,diff,src:'맵 이름'}; }
function arDetectChar(text){ const lat=arLatChar(text); if(lat) return lat; const L=String(text||'').split('\n').find(l=>/[가-힣]{2}/.test(l))||''; const hn=x=>(x.match(/[가-힣]/g)||[]).length, tok=L.trim().split(/\s+/).filter(x=>hn(x)).reduce((a,x)=>hn(x)>=hn(a)&&hn(x)>=Math.min(2,hn(a)+1)?x:a,''); // b285: 이름 뒤 잡티 한 글자('뇨')보다 글자 많은 토큰
  const pre=tok.match(/^[^가-힣]*/)[0], hg=tok.replace(/[^가-힣]/g,''); ARX.nameRead=tok; if(hg.length<1) return '';
  // 상태바 글꼴에서 앞 숫자('2터래플'의 2)는 OCR 이 '<'·'6'·'ㅇ' 등으로 읽음 → 한글 부분은 자모 비교, 앞 기호 유무는 '숫자로 시작하는 이름'과 맞춰 봄
  let best=null; for(const c of S.characters){ const cp=(c.name.match(/^[^가-힣]*/)||[''])[0], ch=c.name.replace(/[^가-힣]/g,''); if(!ch) continue;
    const j=arSimJ(hg,ch); if(j<ARX.cfg.nameThr) continue; let s=j; s+=(!!cp===!!pre)?.15:-.15; if(cp&&pre&&pre.includes(cp)) s+=.1;
    if(!best||s>best.s) best={c,s}; } return best?best.c.id:''; }
/* b285: 영문 닉네임 (예: Drcancel) — 한글이 없는 캐릭터만, 'Lv.285' 뒤 영문 토큰을 소문자로 비교 (OCR 이 l↔I/1, rn↔m 헷갈림) */
function arLatChar(text){ const fx=x=>String(x||'').toLowerCase().replace(/[1|!]/g,'l').replace(/0/g,'o').replace(/rn/g,'m').replace(/[^a-z]/g,'');
  const toks=String(text||'').split(/\s+/).map(fx).filter(x=>x.length>=3&&!/^lv/.test(x)); if(!toks.length) return ''; let best=null;
  for(const c of S.characters){ if(/[가-힣]/.test(c.name)) continue; const n=fx(c.name); if(n.length<2) continue;
    for(const t of toks){ const s=arSim(t,n); if(s>=.7&&(!best||s>best.s)) best={c,s}; } } return best?best.c.id:''; }
/* 지금 기록 대상 (인식 우선, 실패하면 수동 선택) */
function arTarget(){ const c=S.characters.find(x=>x.id===(ARX.det.cid||ARX.cfg.cid))||activeChar(); if(!c) return null;
  const bid=ARX.det.boss||ARX.cfg.boss; const b=bid?findBoss(bid):null; return {c,b,diff:b?((ARX.det.boss===b.id&&ARX.det.diff)||c.bosses?.[b.id]?.diff||b.diffs[0]):''}; }
function arCandidates(){ const t=arTarget(); if(!t) return [];
  const list=t.b?[[t.b,t.diff]]:BOSSES.filter(b=>t.c.bosses?.[b.id]?.enabled).flatMap(b=>t.c.bosses[b.id].diff?[[b,t.c.bosses[b.id].diff]]:b.diffs.map(d=>[b,d])); // b285: 난이도 안 정한 보스는 모든 난이도
  const out=[]; for(const [b,d] of list) for(const k of [...dropsFor(b,d),...infoBoxFor(b,d)]) if(ITEM_ICONS[k]) out.push({k,b,info:!dropsFor(b,d).includes(k)}); return out; }
const arIconPx=(sh,reg)=>reg==='banner'?(ARX.cfg.bannerPx>0?ARX.cfg.bannerPx:Math.max(16,Math.round(sh*46/1080))):(ARX.cfg.iconPx>0?ARX.cfg.iconPx:Math.max(12,Math.round(sh*36/1080)));
/* 획득 로그 한 줄 → {k,n} (이름은 '앱솔랩스 방어구..' 처럼 잘려 있어 앞부분으로 맞춤) */
function arLogItem(line){ const L=String(line||''); if(!/[템탬팀플].{0,4}[\d|Il]+\s*[개거]|얻었|얼었|획득|습니|슬니|있슬|었슬|줍니|니다|\(\s*[소기조][비타]|\)\s*$/.test(L)) return null; const q=+(L.match(/(\d+)\s*개/)||[])[1]||1;
  let name=L.split(/\.\s?\.|…|[,.]\s*[가-힣]?[미이비]?[이디]?[템탬팀]|[아마바미][이미디][템탬팀][을흘플즐글를]|을\s*획득|를\s*획득/)[0]; const pm=L.match(/\(([^()]*)\)\s*$/); if(/^\s*\S+\s*아이템을\s*얻었/.test(L)&&pm) name=pm[1]; // '소비 아이템을 얻었습니다 (이름)'
  const nn=arNorm(name); if(nn.length<2) return null; let best=null;
  for(const c of arCandidates()){ const full=arNorm(ITEMS[c.k]?.n), cut=full.slice(0,nn.length); const jn=arJamo(nn), jc=arJamo(full).slice(0,jn.length); const s=Math.max(arSim(nn,full), nn.length>=3?1-arLev(nn,cut)/nn.length:0, nn.length>=3?1-arLev(jn,jc)/jn.length:0); if(s>=.72&&(!best||s>best.s)) best={k:c.k,s}; }
  return best?{k:best.k,n:q,s:best.s}:null; }
/* 새 줄만 고르기: 줄은 아래로 쌓이고 위에서 사라짐 → 이전 줄 목록의 꼬리 = 이번 목록의 머리 인 가장 긴 겹침을 찾고 나머지만 새 줄 */
const arLineEq=(a,b)=>{ const x=arNorm(a),y=arNorm(b); return x===y||(x.length>4&&y.length>4&&1-arLev(x,y)/Math.max(x.length,y.length)>=.85); };
function arLogDiff(prev,cur){ for(let i=0;i<=prev.length;i++){ const tail=prev.slice(i); if(tail.length>cur.length) continue; if(tail.every((l,j)=>arLineEq(l,cur[j]))) return cur.slice(tail.length); } return cur.slice(); }
function arLogLines(text){ return String(text||'').split(/\n+/).map(x=>x.trim()).filter(x=>arNorm(x).length>=4); }
/* b285: '소비 아이템을 얻었습니다 (벨로나의 소울 조각)' → 맵 이름을 못 읽었을 때 보스 힌트 (난이도는 모름) */
function arSoulHint(line){ const m=String(line).match(/\(([^()]{2,})의\s*소/); if(!m||ARX.det.boss) return; let best=null;
  for(const b of BOSSES) for(const n of [b.name,...(b.aliases||[])]){ const s=arSimJ(m[1],n); if(s>=.75&&(!best||s>best.s)) best={b,s}; }
  if(best){ ARX.det.boss=best.b.id; ARX.det.diff=''; ARX.det.src='소울 조각'; ARX.detT=Date.now(); } }
/* 로그 텍스트 한 번 처리 (테스트도 바로 부름) → 새로 센 [{k,n,line}] */
function arLogStep(text){ const cur=arLogLines(text), add=arLogDiff(ARX.logPrev,cur); ARX.logPrev=cur; ARX.logText=text; const out=[];
  for(const line of add){ arSoulHint(line); const it=arLogItem(line); if(!it) continue; out.push({...it,line}); ARX.counted.push({k:it.k,n:it.n,line,t:Date.now()}); if(ARX.counted.length>200) ARX.counted.shift(); if(ARX.cfg.on) arRecord(it.k,it.s,'로그',it.n); }
  return out; }
/* 아이콘 템플릿 (iconPx 크기로 줄인 RGBA + 알파 마스크) */
async function arTemplates(keys,px){ px=px||32; const sig=px+'|'+keys.join(','); ARX.tplC=ARX.tplC||{}; if(ARX.tplC[sig]) return ARX.tplC[sig]; const T={};
  await Promise.all(keys.map(k=>new Promise(res=>{ const im=new Image(); im.onload=()=>{ const cv=document.createElement('canvas'); cv.width=cv.height=px; const x=cv.getContext('2d',{willReadFrequently:true}); x.drawImage(im,0,0,px,px); T[k]=x.getImageData(0,0,px,px).data; res(); }; im.onerror=res; im.src=ITEM_ICONS[k]; })));
  ARX.tplC[sig]=T; return T; }
function arDown(d,w,h,f){ const W=Math.floor(w/f),H=Math.floor(h/f),o=new Float32Array(W*H*4); for(let y=0;y<H;y++) for(let x=0;x<W;x++){ let r=0,g=0,b=0,a=0;
  for(let j=0;j<f;j++) for(let i=0;i<f;i++){ const p=((y*f+j)*w+x*f+i)*4, al=d[p+3]/255; r+=d[p]*al; g+=d[p+1]*al; b+=d[p+2]*al; a+=al; }
  const q=(y*W+x)*4; o[q]=a?r/a:0; o[q+1]=a?g/a:0; o[q+2]=a?b/a:0; o[q+3]=a/(f*f); } return {d:o,w:W,h:H}; }
/* b284: 정규화 상호상관(NCC) — 배너가 반투명하게 떠오르거나 밝기가 달라도 모양·색 대비로 맞춤 (-1~1) */
function arPrep(T){ if(T.idx) return T; const idx=[],v=[]; for(let y=0;y<T.h;y++) for(let x=0;x<T.w;x++){ const t=(y*T.w+x)*4; if(T.d[t+3]<.8) continue; idx.push(y,x); v.push(T.d[t],T.d[t+1],T.d[t+2]); }
  const m=v.reduce((a,b)=>a+b,0)/(v.length||1); let n=0; const z=Float32Array.from(v,q=>q-m); for(const q of z) n+=q*q; T.idx=idx; T.z=z; T.n=Math.sqrt(n)||1; return T; }
function arScore(F,T,ox,oy){ arPrep(T); const I=T.idx,Z=T.z,N=Z.length; let sf=0; const fv=new Float32Array(N);
  for(let i=0,j=0;i<I.length;i+=2){ const f=((oy+I[i])*F.w+ox+I[i+1])*4; fv[j++]=F.d[f]; fv[j++]=F.d[f+1]; fv[j++]=F.d[f+2]; }
  for(let j=0;j<N;j++) sf+=fv[j]; const m=sf/(N||1); let num=0,den=0; for(let j=0;j<N;j++){ const q=fv[j]-m; num+=q*Z[j]; den+=q*q; } return den?num/(Math.sqrt(den)*T.n):0; }
/* 영역 이미지(ImageData)에서 아이콘 찾기 → [{k,score,x,y}] */
async function arFindIcons(img,px,thr){ thr=thr??ARX.cfg.thr; const C=arCandidates(); if(!C.length) return []; const keys=[...new Set(C.map(c=>c.k))], T=await arTemplates(keys,px), f=Math.max(1,Math.min(ARX.cfg.ds|0,Math.round(px/10))); // b284: 작은 아이콘은 덜 줄여서 대략 찾기가 놓치지 않게
  const Fc=arDown(img.data,img.width,img.height,f), Ff={d:Float32Array.from(img.data,(v,i)=>i%4===3?1:v),w:img.width,h:img.height}, res=[]; ARX.lastScore=[];
  for(const k of keys){ if(!T[k]) continue; const Tc=arDown(T[k],px,px,f), Tf={d:Float32Array.from(T[k],(v,i)=>i%4===3?v/255:v),w:px,h:px}; let cand=[];
    for(let y=0;y+Tc.h<=Fc.h;y++) for(let x=0;x+Tc.w<=Fc.w;x++){ const s=arScore(Fc,Tc,x,y); cand.push([s,x,y]); }
    cand.sort((a,b)=>b[0]-a[0]); let best=null;
    for(const [,cx,cy] of cand.slice(0,6)) for(let y=Math.max(0,cy*f-f);y<=Math.min(img.height-px,cy*f+f);y++) for(let x=Math.max(0,cx*f-f);x<=Math.min(img.width-px,cx*f+f);x++){ const s=arScore(Ff,Tf,x,y); if(!best||s>best.score) best={k,score:s,x,y}; }
    ARX.lastScore.push([k,best?+best.score.toFixed(3):0]); if(best&&best.score>=thr) res.push(best); }
  res.sort((a,b)=>b.score-a.score); const all=ARX.lastScore.map(x=>x[1]).sort((a,b)=>b-a);
  // 비슷한 상자(무기/방어구)처럼 닮은 아이콘: 1등이 2등보다 margin 이상 높을 때만
  return res.filter((h,i)=>i===0&&h.score-(all[1]||0)>=ARX.cfg.margin); }
/* OCR (연결할 때만 ./ocr/ 에서 불러옴, 다른 곳으로 보내지 않음) */
function arOcrLoad(){ if(ARX.ocrP) return ARX.ocrP; ARX.ocrP=new Promise((res,rej)=>{ if(window.Tesseract) return res(); const s=document.createElement('script'); s.src='ocr/tesseract.min.js'; s.onload=res; s.onerror=rej; document.head.appendChild(s); })
  .then(()=>Tesseract.createWorker('kor',1,{workerPath:new URL('ocr/worker.min.js',location.href).href,corePath:new URL('ocr/',location.href).href,langPath:new URL('ocr',location.href).href,gzip:false,workerBlobURL:false}))
  .then(w=>ARX.ocr=w).catch(e=>{ ARX.ocrP=null; ARX.ocrErr=String(e); }); return ARX.ocrP; }
function arCrop(src,sw,sh,r,scale=1){ const cv=document.createElement('canvas'); const x=Math.round(r.x*sw),y=Math.round(r.y*sh),w=Math.max(1,Math.round(r.w*sw)),h=Math.max(1,Math.round(r.h*sh));
  cv.width=w*scale; cv.height=h*scale; const g=cv.getContext('2d',{willReadFrequently:true}); g.imageSmoothingEnabled=scale>1; g.drawImage(src,x,y,w,h,0,0,w*scale,h*scale); return cv; }
async function arOcr(cv,thr=150){ await arOcrLoad(); if(!ARX.ocr) return ''; const g=cv.getContext('2d',{willReadFrequently:true}), im=g.getImageData(0,0,cv.width,cv.height), d=im.data;
  for(let i=0;i<d.length;i+=4){ const v=Math.max(d[i],d[i+1],d[i+2]); const o=v>thr?0:255; d[i]=d[i+1]=d[i+2]=o; } g.putImageData(im,0,0); // 밝은 글자 → 흰 바탕 검은 글자
  const pc=document.createElement('canvas'); pc.width=cv.width+24; pc.height=cv.height+24; const pg=pc.getContext('2d'); pg.fillStyle='#fff'; pg.fillRect(0,0,pc.width,pc.height); pg.drawImage(cv,12,12); // 흰 여백 (tesseract 가 가장자리 글자를 덜 놓침)
  const r=await ARX.ocr.recognize(pc); return (r?.data?.text||'').trim(); }
/* 한 프레임 처리 (src = video 또는 canvas) — 테스트도 이걸 바로 부름 */
async function arLogFrame(src){ if(ARX.logBusy) return; ARX.logBusy=true; try{ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return;
    return arLogStep(await arOcr(arCrop(src,sw,sh,ARX.cfg.log,arSc(sh,2)),170)); } finally{ ARX.logBusy=false; } }
const arSc=(sh,k)=>Math.max(1,Math.min(4,Math.round(k*1080/sh)));  // 작은 화면일수록 더 키워서 OCR
function arFrame(src,force){ return arFrame2(src,force); }
async function arFrame2(src,force){ if(ARX.busy) return; ARX.busy=true; try{ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return;
    if(force||Date.now()-ARX.lastOcr>ARX.cfg.ocrEvery){ ARX.lastOcr=Date.now();
      ARX.mapText=await arOcr(arCrop(src,sw,sh,ARX.cfg.map,arSc(sh,3))); ARX.nameText=await arOcr(arCrop(src,sw,sh,ARX.cfg.name,arSc(sh,3)));
      const b=arDetectBoss(ARX.mapText), cid=arDetectChar(ARX.nameText), now=Date.now(), stale=now-(ARX.detT||0)>ARX.cfg.stickySec*1000;
      // b285: 화면이 번쩍이거나 컷신이라 못 읽은 프레임은 직전 인식을 유지 (stickySec 지나면 비움)
      if(b){ const keep=b.boss===ARX.det.boss?ARX.det.diff:''; ARX.det.boss=b.boss; ARX.det.diff=b.diff||keep; ARX.det.src=b.src; ARX.detT=now; }
      else if(stale){ ARX.det.boss=''; ARX.det.diff=''; ARX.det.src=''; }
      if(cid){ ARX.det.cid=cid; ARX.cidT=now; } else if(now-(ARX.cidT||0)>ARX.cfg.stickySec*1000) ARX.det.cid=''; }
    const found=[], seen=new Set(); ARX.found=[]; ARX.scores={};
    for(const reg of ['banner','item']){ const cv=arCrop(src,sw,sh,ARX.cfg[reg],1), img=cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,cv.width,cv.height);
      const hs=await arFindIcons(img,arIconPx(sh,reg)); ARX.scores[reg]=ARX.lastScore; for(const h of hs) if(!found.some(f=>f.k===h.k)){ h.reg=reg; found.push(h); ARX.found.push([h.k,reg,+h.score.toFixed(3)]); } }
    for(const h of found){ seen.add(h.k); ARX.hits[h.k]=(ARX.hits[h.k]||0)+1; if(ARX.hits[h.k]>=ARX.cfg.confirm&&ARX.cfg.on) arRecord(h.k,h.score,h.reg==='banner'?'배너':'바닥'); }
    for(const k of Object.keys(ARX.hits)) if(!seen.has(k)) delete ARX.hits[k];
    arPanelPaint(); } finally{ ARX.busy=false; } }
/* b286: 배너 순간 감시 — 매 프레임 배너 영역을 아주 작게 줄여 이전 프레임과 비교, 바뀐 프레임만 잘라 큐에 넣고 차례로 아이콘 매칭 (1프레임만 떠도 셈, 바쁠 때도 안 버림) */
function arBannerWatch(src){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return false; const r=ARX.cfg.banner;
  const sm=ARX.bsm||(ARX.bsm=document.createElement('canvas')); sm.width=64; sm.height=16; const g=sm.getContext('2d',{willReadFrequently:true}); g.drawImage(src,r.x*sw,r.y*sh,r.w*sw,r.h*sh,0,0,64,16);
  const d=g.getImageData(0,0,64,16).data, p=ARX.bprev; let diff=0; if(p) for(let i=0;i<d.length;i+=4) diff+=Math.abs(d[i]-p[i])+Math.abs(d[i+1]-p[i+1])+Math.abs(d[i+2]-p[i+2]);
  ARX.bprev=Uint8ClampedArray.from(d); if(p&&diff/(64*16*3)<4) return false;
  const cv=arCrop(src,sw,sh,r,1); ARX.bq=ARX.bq||[]; ARX.bq.push({img:cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,cv.width,cv.height),px:arIconPx(sh,'banner')}); if(ARX.bq.length>40) ARX.bq.shift();
  return arBannerPump(); }
async function arBannerPump(){ if(ARX.bpBusy) return ARX.bpP; ARX.bpBusy=true; ARX.bpP=(async()=>{ try{ while(ARX.bq&&ARX.bq.length){ const q=ARX.bq.shift();
    for(const h of await arFindIcons(q.img,q.px,ARX.cfg.bannerThr)){ ARX.bannerHits=(ARX.bannerHits||[]).concat([[h.k,+h.score.toFixed(3)]]).slice(-20); if(ARX.cfg.on) arRecord(h.k,h.score,'배너 순간'); } } } finally{ ARX.bpBusy=false; } })(); return ARX.bpP; }
function arRecord(item,score,via='',n=1){ const t=arTarget(); if(!t) return; const C=arCandidates().filter(c=>c.k===item); if(!C.length) return;
  const b=C.find(c=>t.c.weekly?.[c.b.id]===false)?.b||C[0].b, key=b.id+'|'+item, now=Date.now();
  if(ARX.recent[key]&&now-ARX.recent[key]<ARX.cfg.dedupSec*1000){ if(via) ARX.recentVia[key]=(ARX.recentVia[key]||'')+'+'+via; return; } ARX.recent[key]=now; ARX.recentVia[key]=via;
  if(C.find(c=>c.b===b)?.info){ arLog(`획득 감지(정보 칩, 기록 안 함): ${ITEMS[item]?.n} · ${b.name}${n>1?' ×'+n:''} [${via}]`); ARX.infoSeen=(ARX.infoSeen||[]).concat(key); arPanelPaint(); return; }
  if((+dropMap(t.c,b.type)[key]||0)>=1){ arLog(`이미 기록됨: ${ITEMS[item]?.n} · ${b.name}`); return; } // 다시 누르면 취소되는 수동 칩과 달리 건드리지 않음
  if(S.activeId!==t.c.id){ S.activeId=t.c.id; render(); }
  changeDrop(key,+1); arLog(`자동 기록: ${ITEMS[item]?.n} · ${b.name}${n>1?' ×'+n:''} [${via} ${(+score).toFixed(2)}]`); arToast(item,b,key,t.c.id); }
function arLog(s){ ARX.log.unshift(new Date().toTimeString().slice(0,8)+' '+s); ARX.log.length=Math.min(ARX.log.length,20); }
function arToast(item,b,key,cid){ let el=$('#arToast'); if(!el){ el=document.createElement('div'); el.id='arToast'; el.className='ar-toast'; el.setAttribute('role','status'); document.body.appendChild(el); }
  el.innerHTML=`<span>${itemIcon(item)}</span><span>자동 기록: <b>${esc(ITEMS[item]?.n||item)}</b> · ${esc(b.name)}</span><button type="button" class="ar-undo">취소</button>`; el.classList.add('show');
  el.querySelector('.ar-undo').onclick=()=>{ const c=S.characters.find(x=>x.id===cid); if(typeof closeRing==='function'&&ringPending?.key===key) closeRing(); else if(c&&(+dropMap(c,b.type)[key]||0)>=1){ if(S.activeId!==cid){ S.activeId=cid; } changeDrop(key,-1); } arLog('취소: '+(ITEMS[item]?.n||item)); el.classList.remove('show'); arPanelPaint(); };
  clearTimeout(arToast._t); arToast._t=setTimeout(()=>el.classList.remove('show'),8000); }
/* 연결 / 끊기 */
async function arConnect(){ if(ARX.stream) return arPanel(true);
  if(!navigator.mediaDevices?.getDisplayMedia){ alert('이 브라우저는 화면 공유를 지원하지 않아요 (PC 크롬·엣지 권장).'); return; }
  try{ ARX.stream=await navigator.mediaDevices.getDisplayMedia({video:{frameRate:{ideal:Math.max(ARX.cfg.fps,ARX.cfg.watchFps||0)}},audio:false}); }catch(e){ ARX.stream=null; return; }
  const v=ARX.video=document.createElement('video'); v.muted=true; v.playsInline=true; v.style.cssText='position:fixed;left:-9999px;top:0;width:2px;height:2px;opacity:0;pointer-events:none'; document.body.appendChild(v); v.srcObject=ARX.stream; arOcrLoad(); v.play().catch(()=>{});
  ARX.stream.getVideoTracks()[0]?.addEventListener('ended',arDisconnect); ARX.lastOcr=0; arOcrLoad();
  ARX.timer=setInterval(()=>arFrame(ARX.video),Math.round(1000/Math.max(.5,ARX.cfg.fps)));
  if(ARX.cfg.watchFps>0){ if(v.requestVideoFrameCallback){ const loop=()=>{ if(ARX.video!==v) return; arBannerWatch(v); v.requestVideoFrameCallback(loop); }; v.requestVideoFrameCallback(loop); } else ARX.wTimer=setInterval(()=>ARX.video&&arBannerWatch(ARX.video),Math.round(1000/ARX.cfg.watchFps)); }
  ARX.logTimer=setInterval(()=>{ if(ARX.ocr) arLogFrame(ARX.video); },Math.round(1000/Math.max(1,ARX.cfg.logFps))); arBtnPaint(); arPanel(true); }
function arDisconnect(){ clearInterval(ARX.logTimer); clearInterval(ARX.wTimer); ARX.bq=[]; ARX.bprev=null; ARX.logPrev=[]; clearInterval(ARX.timer); ARX.timer=0; ARX.stream?.getTracks().forEach(t=>t.stop()); ARX.stream=null; ARX.video?.remove(); ARX.video=null; ARX.hits={}; ARX.det={cid:'',boss:'',diff:'',src:''}; arBtnPaint(); arPanelPaint(); }
function arBtnPaint(){ const b=$('#arBtn'); if(!b) return; b.classList.toggle('on',!!ARX.stream); b.innerHTML=ARX.stream?'<span class="ar-dot"></span>게임 화면 연결됨':'🎮 게임 화면 연결'; }
/* 패널: 상태 · 인식 결과 · 수동 선택 · 영역 맞추기(미리보기 드래그) · OCR 미리보기 */
let arRegionSel='item';
function arPanel(open){ let p=$('#arPanel'); if(!p){ p=document.createElement('div'); p.id='arPanel'; p.className='ar-panel'; p.hidden=true; document.body.appendChild(p);
    p.addEventListener('click',e=>{ const a=e.target.closest('[data-ar]')?.dataset.ar; if(!a) return;
      if(a==='close') p.hidden=true; else if(a==='stop') arDisconnect(); else if(a==='connect') arConnect();
      else if(a==='bindmap'){ const t=arNorm(ARX.mapText), bid=ARX.cfg.boss; if(t&&bid){ ARX.cfg.mapAlias[t]={boss:bid,diff:''}; arSave(); arLog(`맵 등록: ${ARX.mapText} → ${findBoss(bid)?.name}`); } }
      else if(a.startsWith('reg:')){ arRegionSel=a.slice(4); } else if(a==='reset'){ const keep=ARX.cfg.mapAlias; ARX.cfg=Object.assign({},AR_DEF,{mapAlias:keep}); arSave(); }
      arPanelPaint(); });
    p.addEventListener('change',e=>{ const n=e.target.name; if(!n) return; if(n==='on') ARX.cfg.on=e.target.checked; else if(n==='cid'||n==='boss') ARX.cfg[n]=e.target.value; else ARX.cfg[n]=+e.target.value; arSave(); arPanelPaint(); });
    p.addEventListener('pointerdown',e=>{ const cv=e.target.closest('.ar-prev'); if(!cv) return; const R=cv.getBoundingClientRect(), x0=(e.clientX-R.left)/R.width, y0=(e.clientY-R.top)/R.height;
      const mv=ev=>{ const x1=Math.min(1,Math.max(0,(ev.clientX-R.left)/R.width)), y1=Math.min(1,Math.max(0,(ev.clientY-R.top)/R.height)); ARX.cfg[arRegionSel]={x:Math.min(x0,x1),y:Math.min(y0,y1),w:Math.max(.01,Math.abs(x1-x0)),h:Math.max(.01,Math.abs(y1-y0))}; arPrev(); };
      const up=()=>{ removeEventListener('pointermove',mv); removeEventListener('pointerup',up); arSave(); arPanelPaint(); }; addEventListener('pointermove',mv); addEventListener('pointerup',up); }); }
  if(open) p.hidden=false; arPanelPaint(); }
function arPanelPaint(){ const p=$('#arPanel'); if(!p||p.hidden) return; const c=ARX.cfg, t=arTarget(), on=!!ARX.stream, dn=k=>({log:'획득 로그',banner:'획득 배너',item:'바닥 아이콘',map:'맵 이름',name:'상태바 이름'})[k];
  const detC=S.characters.find(x=>x.id===ARX.det.cid), detB=ARX.det.boss&&findBoss(ARX.det.boss);
  p.innerHTML=`<div class="ar-h"><b>게임 화면 자동 기록</b><span class="ar-st ${on?'on':''}">${on?'● 연결됨':'○ 연결 안 됨'}</span><button type="button" class="ar-x" data-ar="close" aria-label="닫기">✕</button></div>
  <div class="ar-row">${on?'<button type="button" class="btn" data-ar="stop">연결 종료</button>':'<button type="button" class="btn primary" data-ar="connect">게임 화면 연결</button>'}
    <label class="ar-sw"><input type="checkbox" name="on" ${c.on?'checked':''}> 자동 기록</label></div>
  <div class="ar-det">캐릭터: <b>${detC?esc(detC.name)+' <small>(이름 인식)</small>':'인식 실패 → '+esc(t?.c?.name||'-')}</b><br>보스: <b>${detB?esc(detB.name)+(ARX.det.diff?' '+D[ARX.det.diff]:'')+` <small>(${ARX.det.src})</small>`:'인식 실패 → '+(t?.b?esc(t.b.name):'캐릭터의 모든 보스')}</b>${ARX.ocrErr?`<br><span class="ar-err">OCR 불러오기 실패</span>`:''}</div>
  <div class="ar-row"><select name="cid" aria-label="수동 캐릭터"><option value="">(수동) 캐릭터: 현재 선택</option>${S.characters.map(x=>`<option value="${esc(x.id)}" ${x.id===c.cid?'selected':''}>${esc(x.name)}</option>`).join('')}</select>
    <select name="boss" aria-label="수동 보스"><option value="">(수동) 보스: 자동</option>${BOSSES.filter(b=>DROPS[b.id]||Object.values(RING_DROPS).some(m=>m[b.id])).map(b=>`<option value="${b.id}" ${b.id===c.boss?'selected':''}>${esc(b.name)}</option>`).join('')}</select></div>
  <div class="ar-row ar-regs">영역: ${['log','banner','item','map','name'].map(k=>`<button type="button" class="btn sm ${arRegionSel===k?'primary':''}" data-ar="reg:${k}">${dn(k)}</button>`).join('')}<small>미리보기에서 드래그</small></div>
  <canvas class="ar-prev" width="320" height="180"></canvas>
  <details class="ar-dbg"><summary>조정 · 디버그</summary>
    <div class="ar-grid">${[['thr','아이콘 일치 기준',.5,1,.01],['iconPx','아이콘 크기(px, 0=자동)',0,64,1],['logFps','로그 읽기(회/초)',1,6,1],['ds','대략 찾기 축소',1,8,1],['confirm','연속 프레임',1,5,1],['fps','초당 프레임',1,4,1],['dedupSec','중복 막기(초)',10,600,10]].map(([n,l,a,b,s])=>`<label>${l}<input type="number" name="${n}" min="${a}" max="${b}" step="${s}" value="${c[n]}"></label>`).join('')}</div>
    <div>맵 OCR: <code>${esc(ARX.mapText||'-')}</code> ${ARX.cfg.boss&&ARX.mapText?'<button type="button" class="btn sm" data-ar="bindmap">이 맵 = 선택한 보스로 등록</button>':''}</div>
    <div>로그 OCR: <code>${esc((ARX.logText||'-').slice(-200))}</code></div>
    <div>이름 OCR: <code>${esc(ARX.nameText||'-')}</code></div>
    <div>아이콘 점수: <code>${ARX.lastScore.map(([k,s])=>`${esc(ITEMS[k]?.s||ITEMS[k]?.n||k)} ${s}`).join(' · ')||'-'}</code></div>
    <button type="button" class="btn sm" data-ar="reset">조정값 처음으로</button></details>
  <ul class="ar-log">${ARX.log.slice(0,6).map(s=>`<li>${esc(s)}</li>`).join('')}</ul>
  <p class="ar-note">화면은 이 브라우저 안에서만 분석하고 어디에도 보내지 않아요.</p>`;
  arPrev(); }
function arPrev(){ const cv=$('#arPanel .ar-prev'); if(!cv) return; const g=cv.getContext('2d'); g.fillStyle='#111'; g.fillRect(0,0,cv.width,cv.height); const src=ARX.video||ARX.testSrc;
  if(src&&(src.videoWidth||src.width)) g.drawImage(src,0,0,cv.width,cv.height);
  for(const [k,col] of [['log','#ff6bd0'],['banner','#ffe066'],['item','#ffb347'],['map','#5ec8ff'],['name','#7dff9a']]){ const r=ARX.cfg[k]; g.strokeStyle=col; g.lineWidth=k===arRegionSel?2.5:1.2; g.strokeRect(r.x*cv.width,r.y*cv.height,r.w*cv.width,r.h*cv.height); } }
setInterval(()=>{ if(ARX.stream&&!$('#arPanel')?.hidden) arPrev(); },500);
document.addEventListener('click',e=>{ if(e.target.closest('#arBtn')) arPanel(true); });
window.AR=ARX; window.arFrame=arFrame; window.arBannerWatch=arBannerWatch; window.arLogFrame=arLogFrame; window.arLogStep=arLogStep; window.arLogItem=arLogItem; window.arOcrLoad=arOcrLoad; arBtnPaint();
