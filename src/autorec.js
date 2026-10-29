/* ===== b283: 게임 화면 연결 → 자동 기록 (뼈대) =====
 * 화면 공유(getDisplayMedia) 프레임을 브라우저 안에서만 분석 — 프레임은 어디에도 올리지 않음.
 *  · 아이템 = 드롭 표 아이템 아이콘(ITEM_ICONS) 템플릿 매칭 (바닥에 떨어진 아이콘 · 획득 알림 아이콘)
 *  · 보스·난이도 = 미니맵 맵 이름 OCR (tesseract.js + kor, ./ocr/ 에서 연결할 때만 불러옴)
 *  · 캐릭터 = 화면 캐릭터 이름 OCR → 등록된 캐릭터와 비슷한 이름
 *  · 인식 실패 시 패널의 수동 선택(캐릭터·보스) 사용
 * 기록은 수동 칩 누르기와 같은 changeDrop(key,+1) (같은 저장 키·시세 자동·합계). 이미 기록된 건 건드리지 않음.
 * 조정값은 전부 AR_DEF (localStorage 'mbt_autorec') — 실제 게임 화면을 받은 뒤 여기서 튜닝. */
const AR_KEY='mbt_autorec';
const AR_DEF={on:true, fps:3, ocrEvery:3000,
  item:{x:.15,y:.25,w:.7,h:.7},   // 아이콘 찾는 영역 (화면 비율)
  map:{x:0,y:0,w:.22,h:.06},      // 미니맵 맵 이름 영역
  name:{x:.35,y:.9,w:.3,h:.1},    // 캐릭터 이름(상태바/이름표) 영역
  iconPx:32,      // 게임 화면에서 아이콘 크기(px, 100% UI 기준 32)
  ds:4,           // 대략 찾기 축소 배율
  thr:.86,        // 아이콘 일치 점수(0~1) 기준
  confirm:2,      // 연속 프레임 수
  dedupSec:120,   // 같은 아이템 다시 기록 막는 시간
  nameThr:.6, mapAlias:{}, cid:'', boss:''};
const ARX={cfg:null, stream:null, video:null, timer:0, busy:false, ocr:null, ocrP:null, lastOcr:0, mapText:'', nameText:'',
  det:{cid:'',boss:'',diff:'',src:''}, hits:{}, recent:{}, log:[], tpl:null, tplKey:'', lastScore:[]};
try{ ARX.cfg=Object.assign({},AR_DEF,JSON.parse(localStorage.getItem(AR_KEY)||'{}')); }catch(e){ ARX.cfg=Object.assign({},AR_DEF); }
const arSave=()=>{ try{ localStorage.setItem(AR_KEY,JSON.stringify(ARX.cfg)); }catch(e){} };
const arNorm=s=>String(s||'').replace(/[^0-9a-zA-Z가-힣]/g,'');
function arLev(a,b){ const m=a.length,n=b.length; if(!m) return n; if(!n) return m; let p=[...Array(n+1).keys()];
  for(let i=1;i<=m;i++){ const q=[i]; for(let j=1;j<=n;j++) q[j]=Math.min(p[j]+1,q[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1)); p=q; } return p[n]; }
function arSim(text,word){ const t=arNorm(text), w=arNorm(word); if(!t||!w) return 0; if(t.includes(w)) return 1; let best=0;
  for(let L=Math.max(1,w.length-1);L<=w.length+1;L++) for(let i=0;i+L<=t.length;i++) best=Math.max(best,1-arLev(t.slice(i,i+L),w)/w.length);
  if(t.length<w.length) best=Math.max(best,1-arLev(t,w)/w.length); return best; }
/* 보스·난이도: 사용자가 묶은 맵 이름 → 보스 이름 들어 있음 → 난이도 글자 */
function arDetectBoss(text){ const t=arNorm(text); if(!t) return null;
  for(const [k,v] of Object.entries(ARX.cfg.mapAlias||{})) if(arSim(t,k)>=.8) return {boss:v.boss,diff:v.diff,src:'맵 등록'};
  let best=null; for(const b of BOSSES){ const s=arSim(t,b.name); if(s>=.75&&(!best||s>best.s||(s===best.s&&b.name.length>best.b.name.length))) best={b,s}; }
  if(!best) return null; let diff=''; for(const [k,v] of Object.entries(D)) if(t.includes(v)&&best.b.diffs.includes(k)) diff=k; if(!diff&&t.includes('노멀')&&best.b.diffs.includes('normal')) diff='normal';
  return {boss:best.b.id,diff,src:'맵 이름'}; }
function arDetectChar(text){ let best=null; for(const c of S.characters){ const s=arSim(text,c.name); if(s>=ARX.cfg.nameThr&&(!best||s>best.s)) best={c,s}; } return best?best.c.id:''; }
/* 지금 기록 대상 (인식 우선, 실패하면 수동 선택) */
function arTarget(){ const c=S.characters.find(x=>x.id===(ARX.det.cid||ARX.cfg.cid))||activeChar(); if(!c) return null;
  const bid=ARX.det.boss||ARX.cfg.boss; const b=bid?findBoss(bid):null; return {c,b,diff:b?(c.bosses?.[b.id]?.diff||ARX.det.diff||b.diffs[0]):''}; }
function arCandidates(){ const t=arTarget(); if(!t) return [];
  const list=t.b?[[t.b,t.diff]]:BOSSES.filter(b=>t.c.bosses?.[b.id]?.enabled).map(b=>[b,t.c.bosses[b.id].diff]);
  const out=[]; for(const [b,d] of list) for(const k of dropsFor(b,d)) if(ITEM_ICONS[k]) out.push({k,b}); return out; }
/* 아이콘 템플릿 (iconPx 크기로 줄인 RGBA + 알파 마스크) */
async function arTemplates(keys){ const px=ARX.cfg.iconPx, sig=px+'|'+keys.join(','); if(ARX.tplKey===sig) return ARX.tpl; const T={};
  await Promise.all(keys.map(k=>new Promise(res=>{ const im=new Image(); im.onload=()=>{ const cv=document.createElement('canvas'); cv.width=cv.height=px; const x=cv.getContext('2d',{willReadFrequently:true}); x.drawImage(im,0,0,px,px); T[k]=x.getImageData(0,0,px,px).data; res(); }; im.onerror=res; im.src=ITEM_ICONS[k]; })));
  ARX.tpl=T; ARX.tplKey=sig; return T; }
function arDown(d,w,h,f){ const W=Math.floor(w/f),H=Math.floor(h/f),o=new Float32Array(W*H*4); for(let y=0;y<H;y++) for(let x=0;x<W;x++){ let r=0,g=0,b=0,a=0;
  for(let j=0;j<f;j++) for(let i=0;i<f;i++){ const p=((y*f+j)*w+x*f+i)*4, al=d[p+3]/255; r+=d[p]*al; g+=d[p+1]*al; b+=d[p+2]*al; a+=al; }
  const q=(y*W+x)*4; o[q]=a?r/a:0; o[q+1]=a?g/a:0; o[q+2]=a?b/a:0; o[q+3]=a/(f*f); } return {d:o,w:W,h:H}; }
function arScore(F,T,ox,oy){ let s=0,n=0; for(let y=0;y<T.h;y++) for(let x=0;x<T.w;x++){ const t=(y*T.w+x)*4; if(T.d[t+3]<.8) continue; const f=((oy+y)*F.w+ox+x)*4;
  s+=Math.abs(F.d[f]-T.d[t])+Math.abs(F.d[f+1]-T.d[t+1])+Math.abs(F.d[f+2]-T.d[t+2]); n++; } return n?1-s/(n*765):0; }
/* 영역 이미지(ImageData)에서 아이콘 찾기 → [{k,score,x,y}] */
async function arFindIcons(img){ const C=arCandidates(); if(!C.length) return []; const keys=[...new Set(C.map(c=>c.k))], T=await arTemplates(keys), px=ARX.cfg.iconPx, f=Math.max(1,ARX.cfg.ds|0);
  const Fc=arDown(img.data,img.width,img.height,f), Ff={d:Float32Array.from(img.data,(v,i)=>i%4===3?1:v),w:img.width,h:img.height}, res=[]; ARX.lastScore=[];
  for(const k of keys){ if(!T[k]) continue; const Tc=arDown(T[k],px,px,f), Tf={d:Float32Array.from(T[k],(v,i)=>i%4===3?v/255:v),w:px,h:px}; let cand=[];
    for(let y=0;y+Tc.h<=Fc.h;y++) for(let x=0;x+Tc.w<=Fc.w;x++){ const s=arScore(Fc,Tc,x,y); if(s>ARX.cfg.thr-.08) cand.push([s,x,y]); }
    cand.sort((a,b)=>b[0]-a[0]); let best=null;
    for(const [,cx,cy] of cand.slice(0,4)) for(let y=Math.max(0,cy*f-f);y<=Math.min(img.height-px,cy*f+f);y++) for(let x=Math.max(0,cx*f-f);x<=Math.min(img.width-px,cx*f+f);x++){ const s=arScore(Ff,Tf,x,y); if(!best||s>best.score) best={k,score:s,x,y}; }
    ARX.lastScore.push([k,best?+best.score.toFixed(3):0]); if(best&&best.score>=ARX.cfg.thr) res.push(best); }
  return res.sort((a,b)=>b.score-a.score); }
/* OCR (연결할 때만 ./ocr/ 에서 불러옴, 다른 곳으로 보내지 않음) */
function arOcrLoad(){ if(ARX.ocrP) return ARX.ocrP; ARX.ocrP=new Promise((res,rej)=>{ if(window.Tesseract) return res(); const s=document.createElement('script'); s.src='ocr/tesseract.min.js'; s.onload=res; s.onerror=rej; document.head.appendChild(s); })
  .then(()=>Tesseract.createWorker('kor',1,{workerPath:new URL('ocr/worker.min.js',location.href).href,corePath:new URL('ocr/',location.href).href,langPath:new URL('ocr',location.href).href,gzip:false,workerBlobURL:false}))
  .then(w=>ARX.ocr=w).catch(e=>{ ARX.ocrP=null; ARX.ocrErr=String(e); }); return ARX.ocrP; }
function arCrop(src,sw,sh,r,scale=1){ const cv=document.createElement('canvas'); const x=Math.round(r.x*sw),y=Math.round(r.y*sh),w=Math.max(1,Math.round(r.w*sw)),h=Math.max(1,Math.round(r.h*sh));
  cv.width=w*scale; cv.height=h*scale; const g=cv.getContext('2d',{willReadFrequently:true}); g.imageSmoothingEnabled=scale>1; g.drawImage(src,x,y,w,h,0,0,w*scale,h*scale); return cv; }
async function arOcr(cv){ await arOcrLoad(); if(!ARX.ocr) return ''; const g=cv.getContext('2d',{willReadFrequently:true}), im=g.getImageData(0,0,cv.width,cv.height), d=im.data;
  for(let i=0;i<d.length;i+=4){ const v=Math.max(d[i],d[i+1],d[i+2]); const o=v>150?0:255; d[i]=d[i+1]=d[i+2]=o; } g.putImageData(im,0,0); // 밝은 글자 → 흰 바탕 검은 글자
  const r=await ARX.ocr.recognize(cv); return (r?.data?.text||'').trim(); }
/* 한 프레임 처리 (src = video 또는 canvas) — 테스트도 이걸 바로 부름 */
async function arFrame(src,force){ if(ARX.busy) return; ARX.busy=true; try{ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return;
    if(force||Date.now()-ARX.lastOcr>ARX.cfg.ocrEvery){ ARX.lastOcr=Date.now();
      ARX.mapText=await arOcr(arCrop(src,sw,sh,ARX.cfg.map,3)); ARX.nameText=await arOcr(arCrop(src,sw,sh,ARX.cfg.name,3));
      const b=arDetectBoss(ARX.mapText); ARX.det.boss=b?.boss||''; ARX.det.diff=b?.diff||''; ARX.det.src=b?.src||''; ARX.det.cid=arDetectChar(ARX.nameText); }
    const cv=arCrop(src,sw,sh,ARX.cfg.item,1), img=cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,cv.width,cv.height);
    const found=await arFindIcons(img), seen=new Set(), t=arTarget();
    for(const h of found){ seen.add(h.k); ARX.hits[h.k]=(ARX.hits[h.k]||0)+1; if(ARX.hits[h.k]>=ARX.cfg.confirm&&ARX.cfg.on) arRecord(h.k,h.score); }
    for(const k of Object.keys(ARX.hits)) if(!seen.has(k)) delete ARX.hits[k];
    arPanelPaint(); } finally{ ARX.busy=false; } }
function arRecord(item,score){ const t=arTarget(); if(!t) return; const C=arCandidates().filter(c=>c.k===item); if(!C.length) return;
  const b=C.find(c=>t.c.weekly?.[c.b.id]===false)?.b||C[0].b, key=b.id+'|'+item, now=Date.now();
  if(ARX.recent[key]&&now-ARX.recent[key]<ARX.cfg.dedupSec*1000) return; ARX.recent[key]=now;
  if((+dropMap(t.c,b.type)[key]||0)>=1){ arLog(`이미 기록됨: ${ITEMS[item]?.n} · ${b.name}`); return; } // 다시 누르면 취소되는 수동 칩과 달리 건드리지 않음
  if(S.activeId!==t.c.id){ S.activeId=t.c.id; render(); }
  changeDrop(key,+1); arLog(`자동 기록: ${ITEMS[item]?.n} · ${b.name} (${score.toFixed(2)})`); arToast(item,b,key,t.c.id); }
function arLog(s){ ARX.log.unshift(new Date().toTimeString().slice(0,8)+' '+s); ARX.log.length=Math.min(ARX.log.length,20); }
function arToast(item,b,key,cid){ let el=$('#arToast'); if(!el){ el=document.createElement('div'); el.id='arToast'; el.className='ar-toast'; el.setAttribute('role','status'); document.body.appendChild(el); }
  el.innerHTML=`<span>${itemIcon(item)}</span><span>자동 기록: <b>${esc(ITEMS[item]?.n||item)}</b> · ${esc(b.name)}</span><button type="button" class="ar-undo">취소</button>`; el.classList.add('show');
  el.querySelector('.ar-undo').onclick=()=>{ const c=S.characters.find(x=>x.id===cid); if(typeof closeRing==='function'&&ringPending?.key===key) closeRing(); else if(c&&(+dropMap(c,b.type)[key]||0)>=1){ if(S.activeId!==cid){ S.activeId=cid; } changeDrop(key,-1); } arLog('취소: '+(ITEMS[item]?.n||item)); el.classList.remove('show'); arPanelPaint(); };
  clearTimeout(arToast._t); arToast._t=setTimeout(()=>el.classList.remove('show'),8000); }
/* 연결 / 끊기 */
async function arConnect(){ if(ARX.stream) return arPanel(true);
  if(!navigator.mediaDevices?.getDisplayMedia){ alert('이 브라우저는 화면 공유를 지원하지 않아요 (PC 크롬·엣지 권장).'); return; }
  try{ ARX.stream=await navigator.mediaDevices.getDisplayMedia({video:{frameRate:{ideal:ARX.cfg.fps}},audio:false}); }catch(e){ ARX.stream=null; return; }
  const v=ARX.video=document.createElement('video'); v.muted=true; v.playsInline=true; v.style.cssText='position:fixed;left:-9999px;top:0;width:2px;height:2px;opacity:0;pointer-events:none'; document.body.appendChild(v); v.srcObject=ARX.stream; arOcrLoad(); v.play().catch(()=>{});
  ARX.stream.getVideoTracks()[0]?.addEventListener('ended',arDisconnect); ARX.lastOcr=0; arOcrLoad();
  ARX.timer=setInterval(()=>arFrame(ARX.video),Math.round(1000/Math.max(.5,ARX.cfg.fps))); arBtnPaint(); arPanel(true); }
function arDisconnect(){ clearInterval(ARX.timer); ARX.timer=0; ARX.stream?.getTracks().forEach(t=>t.stop()); ARX.stream=null; ARX.video?.remove(); ARX.video=null; ARX.hits={}; ARX.det={cid:'',boss:'',diff:'',src:''}; arBtnPaint(); arPanelPaint(); }
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
function arPanelPaint(){ const p=$('#arPanel'); if(!p||p.hidden) return; const c=ARX.cfg, t=arTarget(), on=!!ARX.stream, dn=k=>({item:'아이템 아이콘',map:'맵 이름',name:'캐릭터 이름'})[k];
  const detC=S.characters.find(x=>x.id===ARX.det.cid), detB=ARX.det.boss&&findBoss(ARX.det.boss);
  p.innerHTML=`<div class="ar-h"><b>게임 화면 자동 기록</b><span class="ar-st ${on?'on':''}">${on?'● 연결됨':'○ 연결 안 됨'}</span><button type="button" class="ar-x" data-ar="close" aria-label="닫기">✕</button></div>
  <div class="ar-row">${on?'<button type="button" class="btn" data-ar="stop">연결 종료</button>':'<button type="button" class="btn primary" data-ar="connect">게임 화면 연결</button>'}
    <label class="ar-sw"><input type="checkbox" name="on" ${c.on?'checked':''}> 자동 기록</label></div>
  <div class="ar-det">캐릭터: <b>${detC?esc(detC.name)+' <small>(이름 인식)</small>':'인식 실패 → '+esc(t?.c?.name||'-')}</b><br>보스: <b>${detB?esc(detB.name)+(ARX.det.diff?' '+D[ARX.det.diff]:'')+` <small>(${ARX.det.src})</small>`:'인식 실패 → '+(t?.b?esc(t.b.name):'캐릭터의 모든 보스')}</b>${ARX.ocrErr?`<br><span class="ar-err">OCR 불러오기 실패</span>`:''}</div>
  <div class="ar-row"><select name="cid" aria-label="수동 캐릭터"><option value="">(수동) 캐릭터: 현재 선택</option>${S.characters.map(x=>`<option value="${esc(x.id)}" ${x.id===c.cid?'selected':''}>${esc(x.name)}</option>`).join('')}</select>
    <select name="boss" aria-label="수동 보스"><option value="">(수동) 보스: 자동</option>${BOSSES.filter(b=>DROPS[b.id]||Object.values(RING_DROPS).some(m=>m[b.id])).map(b=>`<option value="${b.id}" ${b.id===c.boss?'selected':''}>${esc(b.name)}</option>`).join('')}</select></div>
  <div class="ar-row ar-regs">영역: ${['item','map','name'].map(k=>`<button type="button" class="btn sm ${arRegionSel===k?'primary':''}" data-ar="reg:${k}">${dn(k)}</button>`).join('')}<small>미리보기에서 드래그</small></div>
  <canvas class="ar-prev" width="320" height="180"></canvas>
  <details class="ar-dbg"><summary>조정 · 디버그</summary>
    <div class="ar-grid">${[['thr','아이콘 일치 기준',.5,1,.01],['iconPx','아이콘 크기(px)',16,64,1],['ds','대략 찾기 축소',1,8,1],['confirm','연속 프레임',1,5,1],['fps','초당 프레임',1,4,1],['dedupSec','중복 막기(초)',10,600,10]].map(([n,l,a,b,s])=>`<label>${l}<input type="number" name="${n}" min="${a}" max="${b}" step="${s}" value="${c[n]}"></label>`).join('')}</div>
    <div>맵 OCR: <code>${esc(ARX.mapText||'-')}</code> ${ARX.cfg.boss&&ARX.mapText?'<button type="button" class="btn sm" data-ar="bindmap">이 맵 = 선택한 보스로 등록</button>':''}</div>
    <div>이름 OCR: <code>${esc(ARX.nameText||'-')}</code></div>
    <div>아이콘 점수: <code>${ARX.lastScore.map(([k,s])=>`${esc(ITEMS[k]?.s||ITEMS[k]?.n||k)} ${s}`).join(' · ')||'-'}</code></div>
    <button type="button" class="btn sm" data-ar="reset">조정값 처음으로</button></details>
  <ul class="ar-log">${ARX.log.slice(0,6).map(s=>`<li>${esc(s)}</li>`).join('')}</ul>
  <p class="ar-note">화면은 이 브라우저 안에서만 분석하고 어디에도 보내지 않아요.</p>`;
  arPrev(); }
function arPrev(){ const cv=$('#arPanel .ar-prev'); if(!cv) return; const g=cv.getContext('2d'); g.fillStyle='#111'; g.fillRect(0,0,cv.width,cv.height); const src=ARX.video||ARX.testSrc;
  if(src&&(src.videoWidth||src.width)) g.drawImage(src,0,0,cv.width,cv.height);
  for(const [k,col] of [['item','#ffb347'],['map','#5ec8ff'],['name','#7dff9a']]){ const r=ARX.cfg[k]; g.strokeStyle=col; g.lineWidth=k===arRegionSel?2.5:1.2; g.strokeRect(r.x*cv.width,r.y*cv.height,r.w*cv.width,r.h*cv.height); } }
setInterval(()=>{ if(ARX.stream&&!$('#arPanel')?.hidden) arPrev(); },500);
document.addEventListener('click',e=>{ if(e.target.closest('#arBtn')) arPanel(true); });
window.AR=ARX; window.arFrame=arFrame; arBtnPaint();
