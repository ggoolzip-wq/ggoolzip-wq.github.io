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
const AR_DEF={on:true, fps:3, ocrEvery:3000, ocrTimeout:6000, logFps:6, stickySec:600,
  item:{x:0,y:.2,w:1,h:.76},      // 바닥·공중 아이콘 찾는 영역 (b287: 화면 전체 폭 — 왼쪽 끝 상자도)
  banner:{x:.25,y:.15,w:.5,h:.17}, // b288: 위쪽 '남은 시간' 타이머 상자(y<.145)가 불멸의 유산으로 오인식돼 제외  // 가운데 획득 배너 (아이콘)
  log:{x:.68,y:.55,w:.32,h:.33},  // 오른쪽 아래 획득 로그 (OCR, 1순위)
  map:{x:0,y:0,w:.2,h:.08},       // 왼쪽 위 미니맵 제목 '지역 맵이름 <난이도>' (b285: 미니맵 펼친 배치는 제목이 두 줄로 아래에 있음)
  name:{x:0,y:.957,w:.2,h:.026},  // 왼쪽 아래 상태바 'Lv.285 캐릭터' (이름표는 파티원도 있어서 안 씀)
  iconPx:0,       // 바닥 아이콘 템플릿 크기(px) 0 = 자동 (b287: 1080 높이에서 71px ±6% — 실제 화면 13장으로 맞춤)
  groundThr:.75,  // b287: 바닥 아이콘 기준 (정답 .79~.94 / 엉뚱한 곳 ≤ .66)
  groundSad:45,   // b287: 색 차이(평균 절대값) 상한 — 실제 화면 13장: 정답 24~39 / 닮은 바닥·이펙트 47~146 (가려진 경우 ×1.4)
  air:true,       // b287: 공중(회전·눌림) 아이템도 — b289: 보상 상자 깨진 직후 위로 튀어 오른 아이템(바닥 떨어지기 전 ~1초)은 '공중 감시'가 따로 맡음
  airFps:6,       // (b292: 평소 값 — 보상 맵이거나 상자 깬 직후엔 airBurstFps)
  airBurstFps:30, // b292: 보상 맵에 있거나 상자 깬 직후(airBurstSec 초) 공중 띠를 이 fps 로 뜸 — 밀린 프레임은 버리고 최신 것만
  airBurstSec:4,  // b292: 상자 깬 순간(공중 후보·바닥 영역 변화) 뒤 몇 초 동안 full-rate
  airMaxH:720,    // b292: 공중 띠를 이 높이(화면 기준) 이하로 줄여 떠서 Worker 로 (1080p → 0.67배, 0 = 원본)
  itemBurstFps:10, // b292: 같은 구간 바닥 찾기 최대 횟수/초 (이전 것 끝나야 — 밀리면 건너뜀)
  airStale:200,   // b292: 전체 검사 안 한 띠 프레임이 최신보다 이만큼(ms) 오래되면 버림(큐에 안 쌓음)       // b289: 공중 감시 — 초당 이만큼 위쪽 띠를 떠서 큐(최신 것 위주) → Worker 매칭 (예전: 3fps 중 바닥 찾기 2회/초 → 1초 공중 구간에 1~2번만 봄)
  airBand:{x:0,y:.08,w:1,h:.64}, // b293: 바닥 바로 위(y .72)까지 확장 — 20개 영상 실측: 아이템이 y≈.46 에서 생성돼 바닥 .75 로 떨어짐. b289: 공중 아이템이 날아다니는 띠 (v01·v07·v11 실제: 1080 높이 기준 y 150~560)
  airStep:10,     // b289: 회전 간격(도) — 45도 간격이면 사이 각도에서 점수 .45~.6 으로 떨어져 놓침 (10도: v11 백옥 공중 프레임 13장 중 6장 ≥ .78, 15도: 4장)
  airCand:.7,     // b289: 전체 검사에서 이 이상이면 '후보' → 보관해 둔 앞뒤 프레임을 그 근처만 다시 봄 (기록은 airThr·airSad 넘은 것만)
  airKeep:10,     // b289: 보관할 띠 프레임 수 (airFps 6 → 약 1.7초)
  airWin:1.2,     // b289: 후보 앞뒤 몇 초까지 다시 볼지
  airThr:.76,     // b289: 공중 기준 (v01·v07·v11 백옥 .78~.89 / 엉뚱한 곳·다른 아이콘 ≤ .7)
  airSad:40,      // b289: 공중 색 차이 상한 (정답 24~37, 빗나간 각도 ≥ 40)
  itemFps:2,      // b287: 바닥·공중 찾기 최대 횟수/초 (화면이 바뀐 때만, Worker 에서)
  prev:1,         // b287: 미리보기 갱신 횟수/초 (0 = 숨김)
  bannerPx:0,     // 배너 아이콘 템플릿 크기(px) 0 = 자동 (1080 높이에서 46px — 실제 화면 13장으로 맞춤)
  margin:.04,     // 1등 아이콘이 2등보다 이만큼 높아야 인정
  ds:4,           // 대략 찾기 축소 배율
  thr:.84,        // 아이콘 일치 점수 (NCC, -1~1) 기준 — 실제 배너: 정답 .88 / 닮은 상자 .80 / 배너 없음 < .5
  confirm:2,      // 연속 프레임 수
  bannerThr:.7,   // b286: 배너 순간 감시(바뀐 프레임만) 기준 — 보상이 한꺼번에 오면 배너 하나가 1프레임(33ms)만 보임 (v01 백옥 .76)
  watchFps:30,    // b286: 배너 변화 감시 횟수/초 (작은 축소본 비교만, 바뀐 프레임만 아이콘 매칭)
  dedupSec:120,   // 같은 아이템 다시 기록 막는 시간
  nameThr:.5, mapAlias:{}, cid:'', boss:''};
/* b291 (사용자 규칙): 보스 보상 맵 18개만 읽음 — 미니맵이 이 맵 이름(+ <난이도>)일 때만 보스를 정하고 아이템을 인식.
   입구·전투 맵·마을 등 다른 맵은 전부 무시 (보스 안 바꿈, 기록 안 함). 근거: /workspace/b287/boss_maps.md */
const AR_REWARD=[['고요해진함선','lotus'],['세계수정상','damien'],['고요한제단','slime'],['악몽의시계탑','lucid'],['바스러지는빛','will'],['공허의눈','dusk'],
  ['욕망의제단','jinhilla'],['끝에가까운곳','dunkel'],['존재하지않는공간','blackmage'],['왕궁메인홀','seren'],['카로테마천루','kalos'],['의지가증명된자리','adversary'],
  ['빛을되찾은사계','kaling'],['잠든환상','star'],['솔라툼의유산','bellona'],['해방된나무정상','limbo'],['폭풍이사그라든여명','baldrix'],['적막한용광로','jupiter']];
const AR_BMAP=[["코어 입구","lotus","w"],["경계하는 코어","lotus","b"],["해방된 코어","lotus","b"],["폭주하는 함선","lotus","b"],["고요해진 함선","lotus","r"],["세계수 정상으로 가는 길","damien","w"],["세계수 정상","damien","br"],["가디언 엔젤 슬라임의 제단","slime","w"],["라무라무 신전","slime","b"],["고요한 제단","slime","r"],["악몽의 시계탑","lucid","brw"],["몽환의 숲","lucid","b"],["무너지는 시계탑","lucid","b"],["거울에 비친 빛의 신좌","will","w"],["회절의 회랑","will","b"],["깊은 거울","will","b"],["바스러지는 빛","will","br"],["공허의 눈 앞","dusk","w"],["공허의 눈","dusk","br"],["욕망의 제단 입구","jinhilla","w"],["욕망의 제단","jinhilla","br"],["끝에 가까운 곳 앞","dunkel","w"],["끝에 가까운 곳","dunkel","br"],["거인의 심장","blackmage","rw"],["어둠의 신전","blackmage","b"],["어둠의 왕좌","blackmage","b"],["시작과 끝의 경계","blackmage","b"],["존재하지 않는 공간","blackmage","b"],["왕궁 메인홀","seren","brw"],["세계의 경계","seren","b"],["마천루","kalos","w"],["카로테 마천루","kalos","br"],["격전의 마천루","kalos","b"],["의지가 시작되는 곳","adversary","w"],["물러서지 않는 용기","adversary","b"],["진실을 꿰뚫는 지혜","adversary","b"],["전설로 거듭나는 운명","adversary","b"],["의지가 증명된 자리","adversary","r"],["사계가 머무는 누각","kaling","w"],["침공 저지","kaling","b"],["생기를 잃은 봄","kaling","b"],["빛을 잃은 여름","kaling","b"],["색을 잃은 가을","kaling","b"],["참혹의 겨울","kaling","b"],["죽음을 두른 사계","kaling","b"],["빛을 되찾은 사계","kaling","r"],["현혹의 신전","star","w"],["찬란한 연회장","star","b"],["환영이 벗겨진 폐허","star","b"],["잠든 환상","star","r"],["추방자의 협곡","bellona","w"],["테네아 신전","bellona","b"],["저주받은 테네아 신전","bellona","b"],["솔라툼의 유산","bellona","r"],["눈물이 스며든 신전","limbo","w"],["재현된 진리의 공간","limbo","b"],["재현된 사념의 공간","limbo","b"],["림보의 무의식","limbo","b"],["해방된 나무 정상","limbo","r"],["밤과 환영의 성소","baldrix","w"],["침묵당한 성전","baldrix","b"],["섭리를 벗어난 성당","baldrix","b"],["적의에 물든 성소","baldrix","b"],["격동하는 마력의 서편","baldrix","b"],["격동하는 마력의 중심","baldrix","b"],["격동하는 마력의 동편","baldrix","b"],["백야로 물든 설원","baldrix","b"],["폭풍이 사그라든 여명","baldrix","r"],["질서와 혼돈의 굴레","jupiter","w"],["균형과 질서의 영역","jupiter","b"],["적막한 용광로","jupiter","r"]]; /* t538: [맵 이름(지역·<난이도> 뺌), 보스, 종류 b=전투 r=보상 w=대기] — /workspace/bossmaps/boss_maps.json 에서 생성 */
const AR_DIFFW=[['익스트림','extreme'],['카오스','chaos'],['노멀','normal'],['노말','normal'],['하드','hard'],['이지','easy']];
const ARX={logPrev:[], lastLog:0, logText:'', logBusy:false, counted:[], cfg:null, stream:null, video:null, timer:0, busy:false, ocr:null, ocrP:null, lastOcr:0, mapText:'', nameText:'',
  det:{cid:'',boss:'',diff:'',src:''}, hits:{}, recent:{}, recentVia:{}, log:[], tpl:null, tplKey:'', lastScore:[]};
try{ ARX.cfg=Object.assign({},AR_DEF,JSON.parse(localStorage.getItem(AR_KEY)||'{}')); }catch(e){ ARX.cfg=Object.assign({},AR_DEF); }
if(!ARX.cfg.v288){ ARX.cfg.v288=1; const b=ARX.cfg.banner; if(b&&b.y===.1&&b.h===.2) ARX.cfg.banner=Object.assign({},AR_DEF.banner); }
/* b297ui: 영역은 항상 고정값 — 저장된 사용자 영역 무시 */
for(const k of ['log','banner','item','map','name','airBand']) ARX.cfg[k]=Object.assign({},AR_DEF[k]);
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
/* t538: 표(AR_BMAP)로 맵 이름 → {boss,diff,kind:'b'|'r'|'w'|'br'…,name}. 난이도는 줄 끝 <노멀> 같은 꺾쇠, 없으면 같은 판에서 마지막으로 읽은 난이도 */
function arTagDiff(L,b){ const t=arNorm(L); if(!/[<>]/.test(L)) return ''; for(const [w,k] of AR_DIFFW) if(t.includes(w)&&(!b||b.diffs.includes(k))) return k;
  const m=L.match(/<\s*([^<>]{1,6})\s*>?\s*$/)||L.match(/<\s*([^<>]{1,6})\s*>/); if(!m) return ''; let best=null; for(const [w,k] of AR_DIFFW){ if(b&&!b.diffs.includes(k)) continue; const s=arSimJ(m[1],w); if(s>=.6&&(!best||s>best.s)) best={k,s}; } return best?best.k:''; }
/* t558: 대기맵 지역명이 전투·보상맵과 다른 보스 (루시드: '꿈의 도시 레헬른' vs '레헬른') */
const AR_WREG={lucid:'꿈의도시레헬른'};
function arDetectBMap(text){ let best=null;
  for(const line of String(text||'').split('\n')){ const L=line.trim(); if(!L) continue; const nm=arNorm(L.replace(/<[^<>]*>?\s*$/,'').split(/[:：]/).pop()); if(nm.length<2) continue;
    for(const [n,id,k] of AR_BMAP){ const w=arNorm(n), sc=nm===w?2:Math.max(arSim(nm,w)>=1&&nm.length<=w.length+3?1:0,arSimJ(nm,w)>=.85?arSimJ(nm,w):0); if(!sc) continue;
      if(!best||sc>best.sc||(sc===best.sc&&w.length>best.w.length)) best={sc,w,id,k,L,reg:arNorm((L.split(/[:：]/).length>1?L.split(/[:：]/)[0]:''))}; } }
  if(!best) return null; const b=findBoss(best.id); if(!b) return null; let diff=arTagDiff(best.L,b);
  const R=ARX.runDiff; if(diff) ARX.runDiff={boss:best.id,diff}; else if(R&&R.boss===best.id) diff=R.diff;
  let kind=best.k; const WR=AR_WREG[best.id]; if(WR&&kind.length>1&&kind.includes('w')&&best.reg) kind=best.reg===WR?'w':kind.replace('w','')||kind; /* t558: 대기맵과 이름이 같은 전투·보상맵은 지역명으로 구분 */
  return {boss:best.id,diff,kind,sc:best.sc,name:best.w,src:kind.includes('r')?'보상 맵':kind.includes('b')?'전투 맵':'대기 맵'}; }
function arDetectBoss(text){ if(!arNorm(text)) return null; { const T=arDetectBMap(text); if(T&&T.kind.includes('r')) return T; if(T&&T.sc>=2&&T.kind==='w') return null; } /* t558: 표에 정확히 있는 비보상 맵(대기·준비 '…입구 <하드>')은 옛 보상 규칙으로 넘기지 않음 */ /* t538: 보스(기록용)는 보상 맵만. 대기·전투는 arMapState */
  for(const line of String(text).split('\n')){ const L=line.trim(), t=arNorm(L); if(!t||!/[<>]/.test(L)) continue; // 보상 맵 제목줄엔 항상 <난이도>
    if(/(입\s*구|앞)\s*$/.test(L.replace(/<[^<>]*>?\s*$/,'').trim())) continue; /* t558: '입구 <하드>' 도 대기 */
    const diffOf=b=>{ for(const [w,k] of AR_DIFFW) if(t.includes(w)&&b.diffs.includes(k)) return k; // '<미지>'(이지)·'<노말>' 같은 OCR 변형 → 괄호 안을 자모로 비교
      const m=L.match(/<\s*([^<>]{1,6})\s*>?\s*$/)||L.match(/<\s*([^<>]{1,6})\s*>/); if(!m) return ''; let best=null;
      for(const [w,k] of AR_DIFFW){ if(!b.diffs.includes(k)) continue; const s=arSimJ(m[1],w); if(s>=.6&&(!best||s>best.s)) best={k,s}; } return best?best.k:''; };
    for(const [k,v] of Object.entries(ARX.cfg.mapAlias||{})) if(arSim(t,k)>=.8){ return {boss:v.boss,diff:v.diff,src:'맵 등록'}; }
    for(const [m,id] of AR_REWARD) if(arSim(t,m)>=.8||arSimJ(t,m)>=.85){ const b=findBoss(id); if(b) return {boss:id,diff:diffOf(b),src:'보상 맵'}; } }
  return null; }
function arDetectChar(text){ const lat=arLatChar(text); if(lat) return lat; const L=String(text||'').split('\n').find(l=>/[가-힣]{2}/.test(l))||''; const hn=x=>(x.match(/[가-힣]/g)||[]).length, tok=L.trim().split(/\s+/).filter(x=>hn(x)).reduce((a,x)=>hn(x)>=hn(a)&&hn(x)>=Math.min(2,hn(a)+1)?x:a,''); // b285: 이름 뒤 잡티 한 글자('뇨')보다 글자 많은 토큰
  const pre=tok.match(/^[^가-힣]*/)[0], hg=tok.replace(/[^가-힣]/g,''); ARX.nameRead=tok; if(hg.length<1) return '';
  // 상태바 글꼴에서 앞 숫자('2터래플'의 2)는 OCR 이 '<'·'6'·'ㅇ' 등으로 읽음 → 한글 부분은 자모 비교, 앞 기호 유무는 '숫자로 시작하는 이름'과 맞춰 봄
  let best=null, sec=null; for(const c of S.characters){ const cp=(c.name.match(/^[^가-힣]*/)||[''])[0], ch=c.name.replace(/[^가-힣]/g,''); if(!ch) continue;
    const j0=arSimJ(hg,ch), jl=hg.length===ch.length?.9*arSim(arLoose(hg),arLoose(ch)):0, j=Math.max(j0,jl); if(j<ARX.cfg.nameThr) continue; let s=j; s+=(!!cp===!!pre)?.15:-.15; if(cp&&pre&&pre.includes(cp)) s+=.1;
    const e={c,s,loose:jl>j0}; if(!best||s>best.s){ sec=best; best=e; } else if(!sec||s>sec.s) sec=e; }
  if(best&&best.loose&&sec&&best.s-sec.s<.15) return ''; // b294: 느슨한 비교로만 맞으면 2등과 확실히 차이 날 때만
  return best?best.c.id:''; }
/* b294: 상태바 글꼴에서 OCR 이 거센소리↔예사소리(트↔드, 딕↔틱), 받침, ㅇ↔ㄴ 을 자주 헷갈림 → 같은 글자 수일 때 이걸 묶어서 한 번 더 비교 (드티니·드특니 → 트딕이) */
function arLoose(s){ const M={'\u1110':'\u1103','\u110F':'\u1100','\u1111':'\u1107','\u110E':'\u110C','\u110B':'\u1102'}; return [...arJamo(s)].filter(x=>!(x>='\u11A8'&&x<='\u11C2')).map(x=>M[x]||x).join(''); }
/* b285: 영문 닉네임 (예: Drcancel) — 한글이 없는 캐릭터만, 'Lv.285' 뒤 영문 토큰을 소문자로 비교 (OCR 이 l↔I/1, rn↔m 헷갈림) */
function arLatChar(text){ const fx=x=>String(x||'').toLowerCase().replace(/[1|!]/g,'l').replace(/0/g,'o').replace(/rn/g,'m').replace(/[^a-z]/g,'');
  const toks=String(text||'').split(/\s+/).map(fx).filter(x=>x.length>=3&&!/^lv/.test(x)); if(!toks.length) return ''; let best=null;
  for(const c of S.characters){ if(/[가-힣]/.test(c.name)) continue; const n=fx(c.name); if(n.length<2) continue;
    for(const t of toks){ const s=arSim(t,n); if(s>=.7&&(!best||s>best.s)) best={c,s}; } } return best?best.c.id:''; }
/* 지금 기록 대상 (인식 우선, 실패하면 수동 선택) */
function arTarget(){ if(arLive()&&!ARX.det.cid) return null; /* t551: 화면 공유 중 인식된 캐릭터가 목록에 없으면(또는 아직 모르면) 기록 대상 없음 — 이전·수동 캐릭터로 넘어가지 않음 */
  const c=S.characters.find(x=>x.id===(ARX.det.cid||ARX.cfg.cid))||activeChar(); if(!c) return null;
  const bid=ARX.det.boss||ARX.cfg.boss; const b=bid?findBoss(bid):null; return {c,b,diff:b?((ARX.det.boss===b.id&&ARX.det.diff)||c.bosses?.[b.id]?.diff||b.diffs[0]):''}; }
function arCandidates(withE){ const t=arTarget(); if(!t) return [];
  const list=t.b?[[t.b,t.diff]]:BOSSES.filter(b=>t.c.bosses?.[b.id]?.enabled).flatMap(b=>t.c.bosses[b.id].diff?[[b,t.c.bosses[b.id].diff]]:b.diffs.map(d=>[b,d])); // b285: 난이도 안 정한 보스는 모든 난이도
  const out=[]; for(const [b,d] of list) for(const k of dropsFor(b,d)) if(ITEM_ICONS[k]) out.push({k,b,info:false}); // b288 사용자 규칙: 대시보드 드롭 표에서 수익 기록되는 것만 (앱솔·아케인 상자·에테르넬 조각 등 정보용은 아예 안 찾음)
  return out; }

/* b295: 해상도·창 모드 — 게임 UI '최적 비율'은 정수 배율(1080p 이하 1배, 1440p·2732x1536·4K 2배). UI 영역(이름·로그·맵·배너)은
 * 화면 모서리에 UI 픽셀 × 배율로 붙여 계산(화면 비율 아님). 월드 영역(바닥·공중)은 게임 화면 비율. 게임 화면 = 스트림 안 검은 테두리·창 제목줄 뺀 곳. */
const AR_RES=[[800,600],[1024,768],[1280,720],[1280,960],[1366,768],[1600,900],[1680,1050],[1920,1080],[1920,1200],[2560,1080],[2560,1440],[2732,1536],[3440,1440],[3840,2160]];
const AR_UI={ // 1배(UI px) 기준, 1920x1080 최적 비율 실측(b284~b294 화면 비율을 UI px 로 옮김). a=붙는 모서리
  name:{a:'bl',l:0,b:46,w:384,h:28}, log:{a:'br',r:0,b:356+130,w:614,h:356}, map:{a:'tl',l:0,t:0,w:384,h:86}, banner:{a:'tc',t:162,w:960,h:184} };
function arUiScale(gw,gh){ const o=+ARX.cfg.uiScale||0; if(o>0) return o; const P=ARX.prof; if(P&&P.gw===gw&&P.gh===gh) return P.s; return gh>=1400?2:1; }
/* t523: 해상도 프로필 5종 (사용자 기준 스크린샷 20장 실측). s=UI 배율(1920 최적 = 1). 기본 비율 = 1366x768 화면을 통째로 키운 것.
 * 고정 영역(px, 게임 화면 기준): inv=인벤토리 메소, sto=창고 메소, stoInv=창고 열었을 때 옆 인벤토리 메소. 텍스트·닉네임은 AR_UI×s, 상자(월드)는 화면 높이 비율 */
const AR_PROF=[
  {id:'1366',w:1366,h:768,s:1,lab:'1366 x 768',inv:[550,538,272,26],sto:[635,582,200,30],stoInv:[877,582,218,30]},
  {id:'1920o',w:1920,h:1080,s:1,lab:'1920 x 1080(최적 비율)',inv:[728,674,272,26],sto:[830,728,200,30],stoInv:[1072,728,218,30]},
  {id:'1920b',w:1920,h:1080,s:1.40625,lab:'1920 x 1080(기본 비율)',inv:[773,757,382,37],sto:[776,804,281,42],stoInv:[1118,804,306,42]},
  {id:'2560b',w:2560,h:1440,s:1.875,lab:'2560 x 1440(기본 비율)',inv:[1031,1009,510,49],sto:[1037,1073,375,56],stoInv:[1491,1073,408,56]},
  {id:'2560o',w:2560,h:1440,s:2,lab:'2560 x 1440(최적 비율)',inv:[100,1012,544,52],sto:[1020,1096,400,60],stoInv:[1504,1096,436,60]}];
const AR_LVTPL='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAYCAAAAAC6zXDVAAACW0lEQVQoFWXBSY9MURgG4Pc759x7q25N3apVIWLYlBpiWIgYYk6ERhohSC+wEbEgISGGBRYkxJBYCCLCgq2QIBaN8BMs/AAJCaV1tRruufecT8vpTfM81ICjfpRi6GxPAIwJlCgx807q06et1MCk7JhQOugp/MXQ5Z/6yP4Xp/qnUR1Oacu9QBlKJAAGwIiz+w6cG8nEVIez9Oz2AGQEA4wJXjuTVFc8a7KkOpzateVlnQu2vfnmz1v+KBUpjjIdI3yeT3U4iy+sKfb82bde3smdn3FIBTSWb+fbstO4QnU4C89sLnMbN/MH048/Hy9DF1o+ydaqE2mqw1lyZm0xTb09245Nv3rj1axm4HPHx9rh0nuqw2lcXD1g/PTM61fKw4d+pRE0s7a94bh3/zHV4Cy4uHFOV3ud52/7CkcKUV7LOCyeKz94WKYanEWnN5R9Ynt07sC726VuEFHw/fCO95fzlmpwKpcGvZRq5dfvzV17PTC91Pyi5K7Buy+LCdXg1E9++8XZe1+LV+VQWu4bevFEqN07R1rjIVXhTFsnlOiN/Eht4qcFtWrlxw863LIrySCmKhw/0jFEQNL0kn4bU6QyRscdoVNUxaROBsamxvs0+10BjjySsIKjDC2A4xkrYg828lSSiEBxLIygnukbpwocK6Oc5d+hihOZ1+0oMGE3SVFuNEUVOGQjH8KkY04oFio0MUsP7Sg0VIHDJDUp2ZHChqP5WAtfS5uE1kiqMEmryWP8ixkgAFS1IDAJg/8x/qJlZC0JsoSpGAQwg0D9CrGVMBJTMQTAzBJ/AFRD8y/NHqJpAAAAAElFTkSuQmCC'; // 1배 'Lv.' 글자+레벨 바 (34x24, 05번 스크린샷)
function arLvTpl(){ if(ARX.lvT) return ARX.lvT; return ARX.lvT=new Promise(res=>{ const im=new Image(); im.onload=()=>res(im); im.onerror=()=>res(null); im.src=AR_LVTPL; }); }
function arGray(g,w,h){ const d=g.getImageData(0,0,w,h).data, o=new Float32Array(w*h); for(let i=0;i<w*h;i++) o[i]=d[i*4]*.299+d[i*4+1]*.587+d[i*4+2]*.114; return o; }
/* 왼쪽 아래 'Lv.' 바를 배율 후보마다 키워 맞춰 본 최고 점수 (NCC) */
function arLvScore(src,G,im,s){ const tw=Math.max(4,Math.round(34*s)), th=Math.max(4,Math.round(24*s)), rw=Math.round(80*s), rh=Math.round(60*s);
  const tc=document.createElement('canvas'); tc.width=tw; tc.height=th; const tg=tc.getContext('2d',{willReadFrequently:true}); tg.drawImage(im,0,0,tw,th); const T=arGray(tg,tw,th);
  const rc=document.createElement('canvas'); rc.width=rw; rc.height=rh; const rg=rc.getContext('2d',{willReadFrequently:true}); rg.drawImage(src,G.gx,G.gy+G.gh-rh,rw,rh,0,0,rw,rh); const I=arGray(rg,rw,rh);
  let tm=0; for(const v of T) tm+=v; tm/=T.length; let tt=0; for(let i=0;i<T.length;i++){ T[i]-=tm; tt+=T[i]*T[i]; } let best=-1; const N=T.length;
  for(let y=0;y+th<=rh;y++) for(let x=0;x+tw<=rw;x++){ let a=0,b=0,c=0; for(let j=0;j<th;j++){ const r=(y+j)*rw+x, q=j*tw; for(let i=0;i<tw;i++){ const v=I[r+i]; a+=T[q+i]*v; b+=v; c+=v*v; } }
    const vv=c-b*b/N; if(vv>1e-6){ const n=a/Math.sqrt(vv*tt); if(n>best) best=n; } } return best; }
/* 화면 공유 영상에서 프로필 고르기: 같은 해상도면 UI 크기(Lv 바)로 기본/최적 구분, 모르는 해상도는 가장 가까운 프로필 배율로 + '(추정)' */
async function arProfDetect(src){ const sw=src?.videoWidth||src?.width, sh=src?.videoHeight||src?.height; if(!sw||!sh) return null; const im=await arLvTpl(); if(!im) return null;
  ARX.geo=null; const keep=ARX.prof; ARX.prof=null; const G=arGeom(sw,sh); ARX.prof=keep; const exact=AR_PROF.filter(p=>p.w===G.gw&&p.h===G.gh);
  const near=t=>{ let n=null,bd=1e9; for(const p of AR_PROF){ if(p.id==='1366'?(t==='o'&&G.gw>1400):p.id.slice(-1)!==t) continue; /* 1366 창고 위치는 화면이 좁아 다르게 붙음 → 큰 최적 화면은 1920 기준 */ const d=Math.abs(p.h-G.gh)+Math.abs(p.w-G.gw)*.5; if(d<bd){ bd=d; n=p; } } return n; };
  const cand=exact.length?exact.map(p=>({p,s:p.s,t:p.id==='1366'?'':p.id.slice(-1)})):[{p:near('o'),s:G.gh>=1400?2:1,t:'o'},{p:near('b'),s:+(G.gh/768).toFixed(5),t:'b'}];
  let best=null; for(const c of cand){ const sc=arLvScore(src,G,im,c.s); if(!best||sc>best.sc) best={...c,sc}; }
  if(!best||(best.sc<.55&&cand.length>1)) return null; const est=!exact.length, P=best.p;
  const lab=est?`${G.gw} x ${G.gh}(${best.t==='b'?'기본 비율':'최적 비율'})(추정)`:P.lab;
  ARX.prof={id:P.id,base:P,s:best.s,gw:G.gw,gh:G.gh,est,lab,score:+best.sc.toFixed(3)}; ARX.geo=null; return ARX.prof; }
/* 프로필 고정 영역 → 스트림 비율 rect. 추정이면 가까운 프로필의 화면 가운데 기준 UI px × 배율 */
function arProfR(k,src){ const sw=src?.videoWidth||src?.width||1920, sh=src?.videoHeight||src?.height||1080, G=arGeom(sw,sh); let P=ARX.prof, base=P?.base;
  if(!base){ base=AR_PROF.find(p=>p.w===G.gw&&p.h===G.gh&&p.s===G.s)||AR_PROF[1]; P={s:G.s}; } const a=base[k]; if(!a) return null; let [x,y,w,h]=a;
  if(base.w!==G.gw||base.h!==G.gh||base.s!==P.s){ const k2=P.s/base.s; x=G.gw/2+(x-base.w/2)*k2; y=G.gh/2+(y-base.h/2)*k2; w*=k2; h*=k2; }
  x+=G.gx; y+=G.gy; return {x:x/sw,y:y/sh,w:Math.min(w,sw-x)/sw,h:Math.min(h,sh-y)/sh}; }
function arProfLab(){ const P=ARX.prof; return P?P.lab:''; }
function arSnapRes(w,h){ let best=null,bd=1e9; for(const [W,H] of AR_RES){ const d=Math.abs(W-w)+Math.abs(H-h); if(d<bd){ bd=d; best=[W,H]; } } return bd<=Math.max(8,.012*(w+h))?best:null; }
function arGameRect(sw,sh,bbox){ // bbox = 검은 테두리 뺀 내용 상자(px) 또는 null
  let x=0,y=0,w=sw,h=sh; if(bbox&&bbox.w>sw*.3&&bbox.h>sh*.3&&(bbox.w<sw-24||bbox.h<sh-24)){ const S=arSnapRes(bbox.w,bbox.h); if(S) return {x:bbox.x+Math.round((bbox.w-S[0])/2),y:bbox.y+Math.round((bbox.h-S[1])/2),w:S[0],h:S[1]}; } // 큰 화면 가운데 검은 테두리(창·작은 해상도 전체화면)
  if(AR_RES.some(([W,H])=>W===sw&&H===sh)) return {x,y,w,h};
  for(const [W,H] of AR_RES) if(W<=sw&&H<=sh&&sw-W<=20&&sh-H>0&&sh-H<=64) return {x:Math.floor((sw-W)/2),y:sh-H-Math.floor((sw-W)/2),w:W,h:H}; // 창 캡처: 제목줄(위)·얇은 테두리
  if(bbox&&bbox.w>sw*.3&&bbox.h>sh*.3&&(bbox.w<sw-4||bbox.h<sh-4)){ const S=arSnapRes(bbox.w,bbox.h); if(S){ x=bbox.x+Math.round((bbox.w-S[0])/2); y=bbox.y+Math.round((bbox.h-S[1])/2); w=S[0]; h=S[1]; } } // 알려진 해상도로 맞을 때만 (어두운 맵 가장자리를 테두리로 착각 방지)
  return {x,y,w,h}; }
function arBBox(src){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return null; const W=192,H=Math.max(2,Math.round(192*sh/sw));
  const c=ARX.bbc||(ARX.bbc=document.createElement('canvas')); c.width=W; c.height=H; const g=c.getContext('2d',{willReadFrequently:true}); g.drawImage(src,0,0,W,H); const d=g.getImageData(0,0,W,H).data;
  const lit=(i)=>d[i]+d[i+1]+d[i+2]>36; let x0=W,x1=-1,y0=H,y1=-1;
  for(let y=0;y<H;y++){ let n=0; for(let x=0;x<W;x++) if(lit((y*W+x)*4)) n++; if(n>W*.02){ if(y<y0)y0=y; y1=y; } }
  for(let x=0;x<W;x++){ let n=0; for(let y=0;y<H;y++) if(lit((y*W+x)*4)) n++; if(n>H*.02){ if(x<x0)x0=x; x1=x; } }
  if(x1<0||y1<0) return null; const kx=sw/W, ky=sh/H; return {x:Math.round(x0*kx),y:Math.round(y0*ky),w:Math.round((x1-x0+1)*kx),h:Math.round((y1-y0+1)*ky)}; }
function arGeom(sw,sh){ const G=ARX.geo; if(G&&G.sw===sw&&G.sh===sh&&G.bb===ARX.bbKey) return G; const R=arGameRect(sw,sh,ARX.bbox||null), s=arUiScale(R.w,R.h);
  return ARX.geo={sw,sh,bb:ARX.bbKey,...R,gx:R.x,gy:R.y,gw:R.w,gh:R.h,s}; }
/* 영역(스트림 비율 rect). 사용자가 바꾼 영역(기본값과 다름)은 게임 화면 비율 그대로, 기본값이면 UI 모서리 기준 */
function arR(k,src){ if(k==='inv'||k==='sto'||k==='stoInv') return arProfR(k,src); const sw=src?.videoWidth||src?.width||1920, sh=src?.videoHeight||src?.height||1080, G=arGeom(sw,sh), c=ARX.cfg[k], d=AR_DEF[k], U=AR_UI[k];
  const same=c&&d&&c.x===d.x&&c.y===d.y&&c.w===d.w&&c.h===d.h; let x,y,w,h;
  if(U&&same&&!ARX.cfg.uiProp){ const s=G.s; w=Math.min(G.gw,U.w*s); h=Math.min(G.gh,U.h*s);
    x=U.a==='bl'||U.a==='tl'?G.gx+U.l*s:U.a==='br'?G.gx+G.gw-U.r*s-w:G.gx+(G.gw-w)/2; y=U.a==='tl'||U.a==='tc'?G.gy+U.t*s:G.gy+G.gh-U.b*s; if(U.a==='br') y=G.gy+G.gh-U.b*s; }
  else { x=G.gx+c.x*G.gw; y=G.gy+c.y*G.gh; w=c.w*G.gw; h=c.h*G.gh; }
  x=Math.max(0,x); y=Math.max(0,y); return {x:x/sw,y:y/sh,w:Math.min(w,sw-x)/sw,h:Math.min(h,sh-y)/sh}; }
const arGH=(src,sh)=>{ const sw=src?.videoWidth||src?.width; return sw?arGeom(sw,sh).gh:sh; };
const arUS=(src,sh)=>{ const sw=src?.videoWidth||src?.width; return sw?arGeom(sw,sh).s:1; };
const arIconPx=(sh,reg,src)=>reg==='banner'?(ARX.cfg.bannerPx>0?ARX.cfg.bannerPx:Math.max(16,Math.round(46*(src?arUS(src,sh):sh/1080)))):(ARX.cfg.iconPx>0?ARX.cfg.iconPx:Math.max(12,Math.round(arGH(src,sh)*36/1080))); // b295: 배너=UI(46px×배율), 바닥=월드(게임 높이 비율)
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
/* b291: 소울 조각 로그로 보스를 정하던 것(b285) 제거 — 보스는 보상 맵 이름으로만 정함 */
function arSoulHint(line){}
/* 로그 텍스트 한 번 처리 (테스트도 바로 부름) → 새로 센 [{k,n,line}] */
function arLogStep(text){ const cur=arLogLines(text), add=arLogDiff(ARX.logPrev,cur); ARX.logPrev=cur; ARX.logText=text; const out=[];
  for(const line of add){ arSoulHint(line); const it=arLogItem(line); if(!it) continue; out.push({...it,line}); ARX.counted.push({k:it.k,n:it.n,line,t:Date.now()}); if(ARX.counted.length>200) ARX.counted.shift(); if(ARX.cfg.on) arRecord(it.k,it.s,'로그',it.n); }
  return out; }
/* 아이콘 템플릿 (px 크기로 줄인 RGBA) */
async function arTemplates(keys,px){ px=px||32; const sig=px+'|'+keys.join(','); ARX.tplC=ARX.tplC||{}; if(ARX.tplC[sig]) return ARX.tplC[sig]; const T={};
  await Promise.all(keys.map(k=>new Promise(res=>{ const im=new Image(); im.onload=()=>{ const cv=document.createElement('canvas'); cv.width=cv.height=px; const x=cv.getContext('2d',{willReadFrequently:true}); x.drawImage(im,0,0,px,px); T[k]=x.getImageData(0,0,px,px).data; res(); }; im.onerror=res; im.src=ITEM_ICONS[k]; })));
  ARX.tplC[sig]=T; return T; }
/* ===== b287: 매칭 코어 — 순수 함수라 Web Worker 안에서도 그대로 돎 (화면 공유 미리보기 끊김 해결: 무거운 계산은 전부 Worker) ===== */
function arDown(d,w,h,f){ const W=Math.floor(w/f),H=Math.floor(h/f),o=new Float32Array(W*H*4); for(let y=0;y<H;y++) for(let x=0;x<W;x++){ let r=0,g=0,b=0,a=0;
  for(let j=0;j<f;j++) for(let i=0;i<f;i++){ const p=((y*f+j)*w+x*f+i)*4, al=d[p+3]/255; r+=d[p]*al; g+=d[p+1]*al; b+=d[p+2]*al; a+=al; }
  const q=(y*W+x)*4; o[q]=a?r/a:0; o[q+1]=a?g/a:0; o[q+2]=a?b/a:0; o[q+3]=a/(f*f); } return {d:o,w:W,h:H}; }
/* 정규화 상호상관(NCC) — 배너가 반투명하게 떠오르거나 밝기가 달라도 모양·색 대비로 맞춤 (-1~1). sel=부분(가림 대비 4등분) */
function arPrepIdx(T,sel){ const idx=[],v=[]; for(let y=0;y<T.h;y++) for(let x=0;x<T.w;x++){ if(sel&&!sel(x,y)) continue; const t=(y*T.w+x)*4; if(T.d[t+3]<.8) continue; idx.push(y,x); v.push(T.d[t],T.d[t+1],T.d[t+2]); }
  const m=v.reduce((a,b)=>a+b,0)/(v.length||1); let n=0; const z=Float32Array.from(v,q=>q-m); for(const q of z) n+=q*q; return {idx,z,n:Math.sqrt(n)||1}; }
function arPrep(T){ if(T.idx) return T; Object.assign(T,arPrepIdx(T)); return T; }
function arScoreP(F,P,ox,oy){ const I=P.idx,Z=P.z,N=Z.length; if(!N) return 0; const D=F.d, w=F.w; let sf=0,sff=0,sfz=0; // 메모리 할당 없이 한 번에 (b287: 프레임마다 수만 번 불림)
  for(let i=0,j=0;i<I.length;i+=2,j+=3){ const f=((oy+I[i])*w+ox+I[i+1])*4, a=D[f], b=D[f+1], c=D[f+2]; sf+=a+b+c; sff+=a*a+b*b+c*c; sfz+=a*Z[j]+b*Z[j+1]+c*Z[j+2]; }
  const den=sff-sf*sf/N; return den>1e-6?sfz/(Math.sqrt(den)*P.n):0; } // Z 합이 0 이라 Σ(f-m)z = Σfz
/* 색 차이(평균 절대값) — 바닥 아이템은 불투명하게 그려져서 정답이면 작음. 스킬 이펙트처럼 모양만 닮은 곳은 큼 */
function arSad(F,T,ox,oy){ let s=0,n=0; for(let y=0;y<T.h;y++) for(let x=0;x<T.w;x++){ const t=(y*T.w+x)*4; if(T.d[t+3]<.8) continue; const f=((oy+y)*F.w+ox+x)*4; s+=Math.abs(F.d[f]-T.d[t])+Math.abs(F.d[f+1]-T.d[t+1])+Math.abs(F.d[f+2]-T.d[t+2]); n+=3; } return n?s/n:255; }
function arScore(F,T,ox,oy){ return arScoreP(F,arPrep(T),ox,oy); }
/* 회전(공중에서 빙글빙글) · 세로 눌림(튀어 오를 때) 템플릿 */
function arXform(src,px,ang,sq){ if(!ang&&sq===1) return {d:src,w:px,h:px}; const a=ang*Math.PI/180, c=Math.cos(a), s=Math.sin(a);
  const W=Math.ceil(Math.abs(c)*px+Math.abs(s)*px*sq), H=Math.ceil(Math.abs(s)*px+Math.abs(c)*px*sq), o=new Uint8ClampedArray(W*H*4);
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){ const dx=x+.5-W/2, dy=y+.5-H/2, u=c*dx+s*dy+px/2, v=(-s*dx+c*dy)/sq+px/2, sx=Math.floor(u), sy=Math.floor(v);
    if(sx<0||sy<0||sx>=px||sy>=px) continue; const p=(sy*px+sx)*4, q=(y*W+x)*4; o[q]=src[p]; o[q+1]=src[p+1]; o[q+2]=src[p+2]; o[q+3]=src[p+3]; } return {d:o,w:W,h:H}; }
const AR_XC=typeof WeakMap!=='undefined'?new WeakMap():null;
function arXcache(src,px,ang,sq,f){ let M=AR_XC&&AR_XC.get(src); if(!M&&AR_XC){ M=new Map(); AR_XC.set(src,M); } const key=px+'|'+ang+'|'+sq+'|'+f; let X=M&&M.get(key); if(X) return X;
  const tv=arXform(src,px,ang,sq), Tf={d:Float32Array.from(tv.d,(v,i)=>i%4===3?v/255:v),w:tv.w,h:tv.h}, Tc=arDown(tv.d,tv.w,tv.h,f); X={Tf,Tc,Pc:arPrepIdx(Tc)}; M&&M.set(key,X); return X; }
/* J={img:{data,width,height}, keys, T:{px:{k:RGBA}}, pxs:[..], thr, margin, ds, f, angles, sq, tiles, multi}
   → {hits:[{k,score,x,y,w,h,ang,sq,occ}], scores:[[k,best]]}  (multi=바닥/공중: 여러 개·여러 종류, 아니면 배너: 1등만) */
function arMatchCore(J,TS){ const img=J.img, pxs=J.pxs||[J.px], angs=J.angles||[0], sqs=J.sq||[1], W=img.width, H=img.height;
  const pmin=Math.min(...pxs), f=J.f||Math.max(1,Math.min(J.ds|0||4,Math.round(pmin/10))); // 작은 아이콘은 덜 줄여서 대략 찾기가 놓치지 않게
  const Fc=arDown(img.data,W,H,f), Ff={d:(()=>{ const S=img.data, o=new Float32Array(S.length); for(let i=0;i<S.length;i+=4){ o[i]=S[i]; o[i+1]=S[i+1]; o[i+2]=S[i+2]; o[i+3]=1; } return o; })(),w:W,h:H}, all=[], scores=[];
  for(const k of J.keys){ const V=[];
    for(const px of pxs){ const src=TS?.[px]?.[k]; if(!src) continue;
      for(const ang of angs) for(const sq of sqs){ if(ang&&sq!==1) continue; const X=arXcache(src,px,ang,sq,f), Tf=X.Tf, Tc=X.Tc; // b289: 회전 템플릿 캐시 (공중 감시: 24각 × 초당 여러 번)
        if(Tc.w>Fc.w||Tc.h>Fc.h||Tf.w>W||Tf.h>H) continue; const Pc=X.Pc; let top=[];
        for(let y=0;y+Tc.h<=Fc.h;y++) for(let x=0;x+Tc.w<=Fc.w;x++){ const s=arScoreP(Fc,Pc,x,y); if(top.length<6||s>top[top.length-1][0]){ top.push([s,x,y]); top.sort((a,b)=>b[0]-a[0]); if(top.length>6) top.pop(); } }
        for(const t of top) V.push({s:t[0],cx:t[1],cy:t[2],Tf,ang,sq,px}); } }
    V.sort((a,b)=>b.s-a.s); const ref=[];
    for(const v of V.slice(0,J.multi?8:6)){ const P=v.Tf.P||(v.Tf.P=arPrepIdx(v.Tf)); let best=null; const tryAt=(x,y)=>{ if(x<0||y<0||x+v.Tf.w>W||y+v.Tf.h>H) return; const s=arScoreP(Ff,P,x,y); if(!best||s>best.s) best={s,x,y}; };
      if(J.multi&&f>2){ for(let y=v.cy*f-f;y<=v.cy*f+f;y+=2) for(let x=v.cx*f-f;x<=v.cx*f+f;x+=2) tryAt(x,y); if(best){ const b0=best; for(let y=b0.y-1;y<=b0.y+1;y++) for(let x=b0.x-1;x<=b0.x+1;x++) tryAt(x,y); } }
      else for(let y=Math.max(0,v.cy*f-f);y<=Math.min(H-v.Tf.h,v.cy*f+f);y++) for(let x=Math.max(0,v.cx*f-f);x<=Math.min(W-v.Tf.w,v.cx*f+f);x++) tryAt(x,y);
      if(!best) continue; let score=best.s, occ=false;
      if(J.tiles&&score<J.thr&&score>=J.thr-.15){ const hw=v.Tf.w/2, hh=v.Tf.h/2, q=[[0,0],[1,0],[0,1],[1,1]].map(([a,b])=>arScoreP(Ff,arPrepIdx(v.Tf,(x,y)=>(x>=hw)===!!a&&(y>=hh)===!!b),best.x,best.y)).sort((a,b)=>b-a);
        const o=(q[0]+q[1]+q[2])/3*.97; if(o>score&&q[2]>=J.thr){ score=o; occ=true; } } // 다른 아이템·캐릭터에 일부 가려져도 4등분 중 3칸이 맞으면 (b287: 영상에서 하늘·기둥 오인식 → 3칸 모두 기준 이상, 색 차이 완화 없음)
      const sad=J.sad?arSad(Ff,v.Tf,best.x,best.y):0; if(J.sad&&sad>J.sad) score=Math.min(score,J.thr-.01);
      ref.push({k,score,x:best.x,y:best.y,w:v.Tf.w,h:v.Tf.h,ang:v.ang,sq:v.sq,px:v.px,occ,sad:+sad.toFixed(1)}); }
    ref.sort((a,b)=>b.score-a.score); const keep=[]; for(const r of ref) if(!keep.some(o=>Math.abs(o.x-r.x)<r.w*.6&&Math.abs(o.y-r.y)<r.h*.6)) keep.push(r);
    scores.push([k,keep[0]?+keep[0].score.toFixed(3):0]); all.push(...(J.multi?keep:keep.slice(0,1))); }
  all.sort((a,b)=>b.score-a.score);
  if(!J.multi){ const s2=scores.map(x=>x[1]).sort((a,b)=>b-a); const h=all[0]; return {hits:h&&h.score>=J.thr&&(h.score-(s2[1]||0)>=J.margin||(J.groups||[]).some(g=>g.includes(h.k)&&all.slice(1).every(o=>o.score<h.score-J.margin||g.includes(o.k))))?[arVariant(Ff,TS,h,J)]:[],scores}; }
  // 바닥/공중: 같은 자리에 닮은 아이콘(무기/방어구 상자)이 있으면 1등이 2등보다 margin 이상일 때만
  const hits=[]; for(const h of all){ if(h.score<J.thr) continue; const near=all.filter(o=>o!==h&&Math.abs(o.x-h.x)<h.w*.6&&Math.abs(o.y-h.y)<h.h*.6);
    if(near.some(o=>o.score>h.score)) continue; const grp=(J.groups||[]).find(g=>g.includes(h.k)); if(near.some(o=>o.k!==h.k&&!(grp&&grp.includes(o.k))&&h.score-o.score<J.margin)) continue; hits.push(arVariant(Ff,TS,h,J)); }
  return {hits,scores}; }
/* b288: 기록 가능한 아이템 전체 (모든 보스·난이도의 드롭 표 ∩ 아이콘) — 템플릿은 이 안에서만 */
function arRecordable(){ if(ARX.recSet) return ARX.recSet; const S0=new Set(); for(const b of BOSSES) for(const d of b.diffs||[]) for(const k of dropsFor(b,d)) if(ITEM_ICONS[k]) S0.add(k); return ARX.recSet=S0; }
/* b288: 모양은 같고 색·문양만 다른 아이콘 묶음 (아이콘 96개 전부 비교: 모양 NCC ≥ .8·알파 IoU ≥ .93) — 1등 모양 찾은 뒤 묶음 안에서 색으로 다시 고름 */
const AR_VAR=[['h_face','h_eye','h_belt','h_ear','h_pocket','h_pendant'],['mc_b','mc_s','mc_g'],['ab_w','ab_a'],['ar_w','ar_a'],['r_green','r_red'],['r_white','r_life'],
  ['b_adv','b_bellona','b_kaling','b_baldrix','b_kalos','b_limbo'],['ipc','ipcm'],['se3','se4'],['twilight','papmark']];
/* 색 단계: 같은 자리에서 묶음의 각 아이콘과 (밝기 맞춘) 색 차이 + 색상(hue) 히스토그램 거리 → 1등이 2등보다 확실히 작을 때만 그 아이콘, 아니면 amb(직접 고르기) */
function arVarDist(Ff,T,ox,oy){ let s=0,n=0,fs=[0,0,0],ts=[0,0,0]; const hf=new Float32Array(12),ht=new Float32Array(12);
  for(let y=0;y<T.h;y++) for(let x=0;x<T.w;x++){ const t=(y*T.w+x)*4; if(T.d[t+3]<.8) continue; const f=((oy+y)*Ff.w+ox+x)*4; for(let c=0;c<3;c++){ fs[c]+=Ff.d[f+c]; ts[c]+=T.d[t+c]; } n++; }
  if(!n) return 999; const g=[0,1,2].map(c=>fs[c]>1?ts[c]/fs[c]:1), G=(g[0]+g[1]+g[2])/3; // 밝기만 맞춤 (색 비율은 그대로)
  const hue=(r,gg,b,H)=>{ const mx=Math.max(r,gg,b), mn=Math.min(r,gg,b); if(mx-mn<24) return; let h=mx===r?(gg-b)/(mx-mn):mx===gg?2+(b-r)/(mx-mn):4+(r-gg)/(mx-mn); h=(h*2+12)%12; H[h|0]+=1; };
  for(let y=0;y<T.h;y++) for(let x=0;x<T.w;x++){ const t=(y*T.w+x)*4; if(T.d[t+3]<.8) continue; const f=((oy+y)*Ff.w+ox+x)*4; const a=Ff.d[f]*G,b=Ff.d[f+1]*G,c=Ff.d[f+2]*G;
    s+=Math.abs(a-T.d[t])+Math.abs(b-T.d[t+1])+Math.abs(c-T.d[t+2]); hue(a,b,c,hf); hue(T.d[t],T.d[t+1],T.d[t+2],ht); }
  let sf=0,st=0; for(let i=0;i<12;i++){ sf+=hf[i]; st+=ht[i]; } let hd=0; for(let i=0;i<12;i++) hd+=Math.abs(hf[i]/(sf||1)-ht[i]/(st||1));
  return s/(3*n)+20*hd; } // 평균 색 차이(0~255) + 색상 분포 차이(0~2 → ×20)
function arVariant(Ff,TS,h,J){ const grp=(J.groups||[]).find(g=>g.includes(h.k)); if(!grp||!h.px) return h; const d=[];
  for(const m of grp){ const src=TS?.[h.px]?.[m]; if(!src) continue; const tv=arXform(src,h.px,h.ang||0,h.sq||1); d.push([m,arVarDist(Ff,{d:Float32Array.from(tv.d,(v,i)=>i%4===3?v/255:v),w:tv.w,h:tv.h},h.x,h.y)]); }
  if(d.length<2) return h; d.sort((a,b)=>a[1]-b[1]); h.vd=d.slice(0,3).map(x=>[x[0],+x[1].toFixed(1)]);
  if(d[1][1]-d[0][1]<Math.max(J.varAbs??3,(J.varRel??.12)*d[1][1])){ h.amb=d.slice(0,2).map(x=>x[0]).filter((x,i,a)=>a.indexOf(x)===i); return h; } // 확실하지 않음 → 직접 고르기
  if(d[0][0]!==h.k){ h.from=h.k; h.k=d[0][0]; } return h; }
/* Worker: 위 함수들 그대로 넣어서 Blob 으로 띄움. 화면은 ImageBitmap(영역만 잘라서)으로 넘김 */
function arWorker(){ if(ARX.wk!==undefined) return ARX.wk; ARX.wk=null; if(ARX.wkOff||ARX.cfg.worker===false||typeof Worker==='undefined'||typeof OffscreenCanvas==='undefined') return null;
  try{ const src='const AR_XC=new WeakMap();\n'+[arDown,arPrepIdx,arScoreP,arSad,arXform,arXcache,arVarDist,arVariant,arMatchCore].map(f=>f.toString()).join('\n')+`
const TC={}; onmessage=e=>{ const J=e.data; try{ if(J.T) TC[J.sig]=J.T; if(J.bmp){ const oc=new OffscreenCanvas(J.bmp.width,J.bmp.height), g=oc.getContext('2d',{willReadFrequently:true}); g.drawImage(J.bmp,0,0); J.img=g.getImageData(0,0,oc.width,oc.height); J.bmp.close(); J.bmp=null; }
  const t0=performance.now(), r=arMatchCore(J,TC[J.sig]); r.ms=performance.now()-t0; r.id=J.id; postMessage(r); }catch(err){ postMessage({id:J.id,err:String(err),hits:[],scores:[]}); } };`;
    const w=new Worker(URL.createObjectURL(new Blob([src],{type:'text/javascript'}))); ARX.wkP={}; ARX.wkSig=new Set(); ARX.wkId=0;
    w.onmessage=e=>{ const r=e.data, cb=ARX.wkP[r.id]; delete ARX.wkP[r.id]; cb&&cb(r); }; w.onerror=()=>{ ARX.wk=null; for(const cb of Object.values(ARX.wkP)) cb({hits:[],scores:[],err:'worker'}); ARX.wkP={}; }; ARX.wk=w; }catch(e){ ARX.wk=null; } return ARX.wk; }
/* 영역 잘라 넘길 것: Worker 있으면 ImageBitmap(메인 스레드에서 픽셀 안 읽음), 없으면 ImageData */
async function arGrab(src,r){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height, x=Math.round(r.x*sw), y=Math.round(r.y*sh), w=Math.max(1,Math.min(sw-x,Math.round(r.w*sw))), h=Math.max(1,Math.min(sh-y,Math.round(r.h*sh)));
  if(arWorker()&&typeof createImageBitmap==='function'){ try{ return {bmp:await createImageBitmap(src,x,y,w,h),ox:x,oy:y,w,h}; }catch(e){} }
  const cv=arCrop(src,sw,sh,r,1); return {img:cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,cv.width,cv.height),ox:x,oy:y,w:cv.width,h:cv.height}; }
async function arMatchRun(G,keys,pxs,opt){ const rec=arRecordable(), groups=AR_VAR.filter(g=>g.some(k=>keys.includes(k))).map(g=>g.filter(k=>ITEM_ICONS[k]&&rec.has(k))), tk=[...new Set([...keys,...groups.flat()])];
  const TS={}; for(const px of pxs) TS[px]=await arTemplates(tk,px); const sig=pxs.join(',')+'|'+tk.join(',');
  const J=Object.assign({keys,pxs,groups,thr:ARX.cfg.thr,margin:ARX.cfg.margin,ds:ARX.cfg.ds},opt), w=arWorker(), t0=performance.now();
  if(w&&(G.bmp||G.img)){ J.id=++ARX.wkId; J.sig=sig; if(!ARX.wkSig.has(sig)){ J.T=TS; ARX.wkSig.add(sig); } if(G.bmp) J.bmp=G.bmp; else J.img=G.img;
    const r=await new Promise(res=>{ ARX.wkP[J.id]=res; try{ w.postMessage(J,G.bmp?[G.bmp]:[]); }catch(e){ delete ARX.wkP[J.id]; res({err:String(e)}); return; } setTimeout(()=>{ if(ARX.wkP[J.id]){ delete ARX.wkP[J.id]; res({err:'timeout'}); } },8000); }); if(!r.err) return r; ARX.wkSig.delete(sig);
    ARX.wkFail=(ARX.wkFail||0)+1; if(ARX.wkFail>=2||r.err==='worker'){ try{ w.terminate(); }catch(e){} ARX.wk=null; ARX.wkOff=r.err; } if(G.bmp) return {hits:[],scores:[],ms:0}; } // b288: Worker 실패 → 메인 스레드(b286 방식)로
  let img=G.img; if(!img&&G.bmp){ const cv=document.createElement('canvas'); cv.width=G.bmp.width; cv.height=G.bmp.height; const g=cv.getContext('2d',{willReadFrequently:true}); g.drawImage(G.bmp,0,0); img=g.getImageData(0,0,cv.width,cv.height); }
  J.img=img; const r=arMatchCore(J,TS); r.ms=performance.now()-t0; return r; }
/* 영역 이미지(ImageData)에서 아이콘 찾기 → [{k,score,x,y}] (배너: 1등만) */
async function arFindIcons(img,px,thr,opt){ const C=arCandidates(); if(!C.length) return []; const keys=[...new Set(C.map(c=>c.k))], G=img&&img.data?{img}:img;
  const r=await arMatchRun(G,keys,opt?.pxs||[px],Object.assign({thr:thr??ARX.cfg.thr},opt||{})); ARX.lastScore=r.scores; ARX.lastMs=r.ms; return r.hits; }
/* b287: 바닥·공중 아이템 — 파티 격파는 자동으로 안 주워져 바닥에 깔림. 바닥 아이콘은 인벤토리 아이콘보다 ~1.11배 (1080p 에서 64→71px, 상자류 67px).
   공중(튀어 오를 때)은 회전·세로 눌림. 프레임 사이 추적해서 같은 자리면 1번, 배너·로그와는 arRecord 에서 중복 제거 */
function arGroundPx(sh){ const b=ARX.cfg.iconPx>0?ARX.cfg.iconPx:Math.round(sh*71/1080); return [Math.round(b*.94),b,Math.round(b*1.06)]; }
async function arItemScan(src){ const C=arCandidates(true); if(!C.length) return []; const sh=src.videoHeight||src.height, keys=[...new Set(C.map(c=>c.k))], G=await arGrab(src,arR('item',src)), pxs=arGroundPx(arGH(src,sh));
  const opt={multi:true,tiles:true,sad:ARX.cfg.groundSad,thr:ARX.cfg.groundThr,f:Math.max(2,Math.round(pxs[1]/9)),angles:[0],sq:[1],pxs}; // b289: 공중(회전)은 arAirScan 으로 옮김
  const r0=await arMatchRun(G,keys,pxs,opt); const hits=[...r0.hits];
  ARX.lastScore=r0.scores; ARX.itemMs=r0.ms||0; return hits.map(h=>Object.assign(h,{x:h.x+G.ox,y:h.y+G.oy})); }
/* b289: 공중 아이템 — 보상 상자를 부순 순간 아이템들이 한 줄로 위로 튀어 올라 빙글빙글 돌다 0.4~1초 뒤 바닥에 떨어짐(솔로는 곧 자동 줍기라 바닥엔 거의 안 보임).
   놓친 이유(영상 20개 프레임 단위로 확인): ① 3fps·바닥 찾기 2회/초 → 공중 구간에 1~2번만 봄, 연속 2번 확인을 못 채움 ② 회전 45도 간격 → 사이 각도에서 .45~.6
   ③ 공중 회전 단계가 보스 모를 때 모든 아이콘으로 돌아 엉뚱한 아이콘이 이김. 그래서: 위쪽 띠를 airFps 로 떠서 최근 airKeep 장 보관 → 최신 것 전체 검사(회전 airStep 도) →
   후보(airCand 이상)가 보이면 보관해 둔 앞뒤 프레임을 그 자리 근처만 다시 검사 → 기준(airThr·airSad) 넘는 것만 추적, 같은 아이템 2번 보이면 1번 기록 */
function arAirAngles(){ const st=Math.max(5,+ARX.cfg.airStep||10), a=[]; for(let x=0;x<360;x+=st) a.push(x); return a; }
async function arAirScan(G,sh,ox,oy,thr){ const C=arCandidates(true); if(!C.length){ G.bmp&&G.bmp.close&&G.bmp.close(); return []; } const keys=[...new Set(C.map(c=>c.k))], px=arGroundPx(sh)[1];
  const r=await arMatchRun(G,keys,[px],{multi:true,tiles:true,sad:thr<ARX.cfg.airThr?999:ARX.cfg.airSad,thr:thr??ARX.cfg.airThr,f:Math.max(2,Math.round(px/9)),angles:arAirAngles(),sq:[1]});
  ARX.airScore=r.scores; ARX.airMs=r.ms||0; return r.hits.map(h=>Object.assign(h,{x:h.x+ox,y:h.y+oy,air:true,ok:h.score>=ARX.cfg.airThr&&h.sad<=ARX.cfg.airSad})); }
async function arAirCrop(e,x,y,w,h){ x=Math.max(0,Math.round(x)); y=Math.max(0,Math.round(y)); w=Math.round(Math.min(w,e.w-x)); h=Math.round(Math.min(h,e.h-y)); if(w<8||h<8) return null;
  if(e.bmp) return {bmp:await createImageBitmap(e.bmp,x,y,w,h)};
  const S=e.img.data, o=new Uint8ClampedArray(w*h*4); for(let j=0;j<h;j++) o.set(S.subarray(((y+j)*e.w+x)*4,((y+j)*e.w+x+w)*4),j*w*4); return {img:{data:o,width:w,height:h}}; }
/* 매 프레임 불림 — airFps 간격으로 띠를 떠서 보관(최근 airKeep 장) → arAirPump */
/* b292: 지금 full-rate 구간인지 (보상 맵에 있거나 상자 깬 직후 airBurstSec 초) */
function arHot(at){ const c=ARX.cfg; return !!(c.airBurstFps>0&&(ARX.det?.src==='보상 맵'||ARX.det?.src==='보상 상자'||(at??Date.now())<(ARX.burstUntil||0))); }
function arBurst(at){ ARX.burstUntil=Math.max(ARX.burstUntil||0,(at??Date.now())+(ARX.cfg.airBurstSec||0)*1000); }
function arAirWatch(src,now,at){ if(!ARX.cfg.air||!(ARX.cfg.airFps>0)) return false; now=now??performance.now(); const hot=ARX.airHot=arHot(at), fps=hot?Math.max(ARX.cfg.airFps,ARX.cfg.airBurstFps):ARX.cfg.airFps;
  if(now-(ARX.airT||0)<1000/fps-2) return false;
  const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return false; ARX.airT=now; const r=arR('airBand',src), pf=arPf();
  const x=Math.round(r.x*sw), y=Math.round(r.y*sh), w=Math.min(sw-x,Math.round(r.w*sw)), h=Math.min(sh-y,Math.round(r.h*sh)), k=ARX.cfg.airMaxH>0?Math.min(1,ARX.cfg.airMaxH/sh):1; // b292: 줄여서 뜸
  const e={sh:Math.round(sh*k),osh:sh,k,x:Math.round(x*k),y:Math.round(y*k),w:Math.round(w*k),h:Math.round(h*k),t:src.currentTime??null,at:at??Date.now(),done:false,loc:[]};
  if(typeof createImageBitmap==='function'&&ARX.cfg.worker!==false) e.bmpP=(k<1?createImageBitmap(src,x,y,w,h,{resizeWidth:e.w,resizeHeight:e.h,resizeQuality:'medium'}):createImageBitmap(src,x,y,w,h)).then(b=>e.bmp=b).catch(()=>null);
  else { const cv=document.createElement('canvas'); cv.width=e.w; cv.height=e.h; const g=cv.getContext('2d',{willReadFrequently:true}); g.imageSmoothingEnabled=true; g.drawImage(src,x,y,w,h,0,0,e.w,e.h); e.img=g.getImageData(0,0,e.w,e.h); }
  arAirPush(e); pf.airCap=(pf.airCap||0)+1; return arAirPump(); }
function arAirPush(e){ const B=ARX.abuf=ARX.abuf||[]; B.push(e); while(B.length>Math.max(2,ARX.cfg.airKeep|0||10)){ const o=B.shift(); if(!o.done) arPf().airDrop=(arPf().airDrop||0)+1; if(o.bmpP) o.bmpP.then(()=>{ if(!o.busy) o.bmp&&o.bmp.close(); }); } }
async function arAirPump(){ if(ARX.apBusy) return ARX.apP; ARX.apBusy=true; ARX.apP=(async()=>{ try{ while(await arAirStep()); } finally{ ARX.apBusy=false; } })(); return ARX.apP; }
/* 한 건 처리 (없으면 false) — 테스트는 이걸 직접 불러 처리 시간을 흉내 냄 */
async function arAirStep(){ { const B=ARX.abuf||[], pf=arPf();
      // 1) 후보 근처 다시 보기(보관해 둔 앞뒤 프레임) 2) 아직 안 본 최신 프레임 전체
      let job=null; for(const L of ARX.alocs||[]){ const e=B.find(e=>!e.loc.includes(L.id)&&Math.abs(e.at-L.at)<=ARX.cfg.airWin*1000); if(e){ job={e,L}; break; } }
      if(!job){ const nt=B.length?B[B.length-1].at:0; ARX.alocs=(ARX.alocs||[]).filter(L=>nt-L.at<3000); const e=[...B].reverse().find(e=>!e.done); if(!e) return false; job={e};
        for(const o of B) if(o!==e&&!o.done&&e.at-o.at>=(ARX.cfg.airStale||0)){ o.done=true; pf.airDrop=(pf.airDrop||0)+1; } } // b292: 밀린 옛 프레임은 전체 검사 안 하고 버림(후보 근처 다시 보기용으로만 보관)
      const e=job.e; e.busy=true; if(e.bmpP) await e.bmpP; if(!e.bmp&&!e.img){ e.done=true; e.loc.push(job.L?.id); e.busy=false; return true; }
      let hits=[];
      const K=e.k||1, OS=e.osh||e.sh, un=hs=>hs.map(h=>Object.assign(h,{x:Math.round(h.x/K),y:Math.round(h.y/K),w:Math.round(h.w/K),h:Math.round(h.h/K)})); // b292: 줄인 좌표 → 원래 화면 좌표
      if(job.L){ e.loc.push(job.L.id); const R=job.L.r*K, lx=job.L.x*K, ly=job.L.y*K; const G=await arAirCrop(e,lx-e.x-R,ly-e.y-R,2*R,2*R);
        if(G) hits=un((await arAirScan(G,e.sh,e.x+Math.max(0,Math.round(lx-e.x-R)),e.y+Math.max(0,Math.round(ly-e.y-R)),ARX.cfg.airThr)).filter(h=>h.k===job.L.k)); pf.airLoc=(pf.airLoc||0)+1; }
      else { e.done=true; const G=await arAirCrop(e,0,0,e.w,e.h); hits=G?un(await arAirScan(G,e.sh,e.x,e.y,ARX.cfg.airCand)):[]; pf.air=(pf.air||0)+1; pf.airMs=(pf.airMs||0)+(ARX.airMs||0); if(hits.length) arBurst(e.at);
        for(const h of hits) if(!(ARX.alocs||[]).some(L=>L.k===h.k&&Math.abs(L.at-e.at)<1500&&Math.hypot(L.x-h.x-h.w/2,L.y-h.y-h.h/2)<300*OS/1080)){ // 후보 → 이 자리 근처를 앞뒤 프레임에서
          ARX.alocs=(ARX.alocs||[]).concat([{id:(ARX.alocId=(ARX.alocId||0)+1),k:h.k,x:h.x+h.w/2,y:h.y+h.h/2,r:Math.round(300*OS/1080),at:e.at}]); e.loc.push(ARX.alocId); } }
      e.busy=false; const ok=hits.filter(h=>h.ok);
      if(ok.length){ ARX.airLog=(ARX.airLog||[]).concat([{t:e.t,loc:!!job.L,hits:ok.map(h=>[h.k,+h.score.toFixed(3),h.x,h.y,h.w,h.h,h.ang,h.sad])}]).slice(-300); for(const h of ok) (ARX.found=ARX.found||[]).push([h.k,'공중',+h.score.toFixed(3)]); }
      // b289: 공중은 0.4초뿐일 때가 있어 — 전체 훑기 후보(airCand)+근처 확인(airThr) 두 번 보인 걸로 친다
      if(job.L&&ok.length&&!job.L.seed){ job.L.seed=true; const h=ok[0]; arTrack([Object.assign({},h,{air:true})],OS,Math.min(e.at,job.L.at)); }
      arTrack(ok.map(h=>Object.assign({},h,{air:true})),OS,e.at); return true; } }
/* 추적: 같은 아이템이 비슷한 자리(바닥 80px·공중 250px, 1080p 기준)에 2.5초 안에 다시 보이면 같은 것 → confirm 번 보이면 1번 기록 */
function arTrack(hits,sh,now){ now=now||Date.now(); const k1=sh/1080; ARX.tracks=(ARX.tracks||[]).filter(t=>now-t.t<5000); const rec=[];
  for(const h of hits){ const R=(h.air?250:80)*k1; let t=ARX.tracks.find(t=>t.k===h.k&&now-t.t<2500&&Math.hypot(t.x-h.x,t.y-h.y)<R);
    if(!t){ t={k:h.k,x:h.x,y:h.y,t:now,n:0,done:false,air:!!h.air}; ARX.tracks.push(t); } t.x=h.x; t.y=h.y; t.t=now; t.n++; t.s=Math.max(t.s||0,h.score);
    if(!t.done&&t.n>=ARX.cfg.confirm){ t.done=true; rec.push(t); if(ARX.cfg.on) arPick(Object.assign({},h,{score:t.s}),h.air?'공중':'바닥'); } }
  return rec; }
/* OCR (연결할 때만 ./ocr/ 에서 불러옴, 다른 곳으로 보내지 않음) */
/* b296: 이름·미니맵 감시 전용 두 번째 워커 — 로그 OCR(초당 6번) 뒤에 줄 서지 않게 */
function arOcrFLoad(){ if(ARX.ocrFP) return ARX.ocrFP; ARX.ocrFP=arOcrLoad().then(()=>window.Tesseract?Tesseract.createWorker('kor',1,{workerPath:new URL('ocr/worker.min.js',location.href).href,corePath:new URL('ocr/',location.href).href,langPath:new URL('ocr',location.href).href,gzip:false,workerBlobURL:false}):null)
  .then(w=>ARX.ocrF=w).catch(e=>{ ARX.ocrFP=null; }); return ARX.ocrFP; }
function arOcrLoad(){ if(ARX.ocrP) return ARX.ocrP; ARX.ocrP=new Promise((res,rej)=>{ if(window.Tesseract) return res(); const s=document.createElement('script'); s.src='ocr/tesseract.min.js'; s.onload=res; s.onerror=rej; document.head.appendChild(s); })
  .then(()=>Tesseract.createWorker('kor',1,{workerPath:new URL('ocr/worker.min.js',location.href).href,corePath:new URL('ocr/',location.href).href,langPath:new URL('ocr',location.href).href,gzip:false,workerBlobURL:false}))
  .then(w=>ARX.ocr=w).catch(e=>{ ARX.ocrP=null; ARX.ocrErr=String(e); }); return ARX.ocrP; }
function arCrop(src,sw,sh,r,scale=1){ const cv=document.createElement('canvas'); const x=Math.round(r.x*sw),y=Math.round(r.y*sh),w=Math.max(1,Math.round(r.w*sw)),h=Math.max(1,Math.round(r.h*sh));
  cv.width=w*scale; cv.height=h*scale; const g=cv.getContext('2d',{willReadFrequently:true}); g.imageSmoothingEnabled=scale>1; g.drawImage(src,x,y,w,h,0,0,w*scale,h*scale); return cv; }
async function arOcr(cv,thr=150,fast){ await arOcrLoad(); if(fast) await arOcrFLoad(); const KW=fast&&ARX.ocrF?'ocrF':'ocr'; if(!ARX[KW]) return ''; const g=cv.getContext('2d',{willReadFrequently:true}), im=g.getImageData(0,0,cv.width,cv.height), d=im.data;
  for(let i=0;i<d.length;i+=4){ const v=Math.max(d[i],d[i+1],d[i+2]); const o=v>thr?0:255; d[i]=d[i+1]=d[i+2]=o; } g.putImageData(im,0,0); // 밝은 글자 → 흰 바탕 검은 글자
  const pc=document.createElement('canvas'); pc.width=cv.width+24; pc.height=cv.height+24; const pg=pc.getContext('2d'); pg.fillStyle='#fff'; pg.fillRect(0,0,pc.width,pc.height); pg.drawImage(cv,12,12); // 흰 여백 (tesseract 가 가장자리 글자를 덜 놓침)
  const w=ARX[KW], T=+ARX.cfg.ocrTimeout||6000; let to; // b296: tesseract 가 응답 안 하면(멈춤) 끝없이 기다리지 않음 → 시간 초과 시 워커를 버리고 다음에 새로 띄움
  try{ const r=await Promise.race([w.recognize(pc),new Promise((_,rej)=>{ to=setTimeout(()=>rej(new Error('ocr timeout')),T); })]); return (r?.data?.text||'').trim(); }
  catch(e){ if(String(e).includes('ocr timeout')&&ARX[KW]===w){ ARX.ocrHang=(ARX.ocrHang||0)+1; ARX[KW]=null; if(KW==='ocr') ARX.ocrP=null; else ARX.ocrFP=null; setTimeout(()=>{ try{ w.terminate?.(); }catch(_){} },50); } return ''; /* 멈춤은 빈 결과로 (다음에 새 워커) */ } finally{ clearTimeout(to); } }
/* 한 프레임 처리 (src = video 또는 canvas) — 테스트도 이걸 바로 부름 */
async function arLogFrame(src){ if(ARX.logBusy) return; ARX.logBusy=true; try{ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return;
    return arLogStep(await arOcr(arCrop(src,sw,sh,arR('log',src),arSc(sh,2,src)),170)); } finally{ ARX.logBusy=false; } }
const arSc=(sh,k,src)=>Math.max(1,Math.min(4,Math.round(k/(src?arUS(src,sh):sh/1080)))); // b295: UI 배율 기준 (2배 UI = 글자도 2배 → 덜 키움)  // 작은 화면일수록 더 키워서 OCR
function arFrame(src,force){ return arFrame2(src,force); }
async function arFrame2(src,force){ if(ARX.busy) return; ARX.busy=true; try{ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return;
    if(force||Date.now()-ARX.lastOcr>ARX.cfg.ocrEvery){ ARX.lastOcr=Date.now();
      if(force||!ARX.nTimer){ ARX.mapText=await arOcr(arCrop(src,sw,sh,arR('map',src),arSc(sh,3,src))); arLockCheck(src,ARX.mapText); arMapState(ARX.mapText,Date.now()); } /* b296: 연결 중엔 arMapWatch 가 0.2초마다 따로 봄 */ if(force||!ARX.nTimer) ARX.nameText=await arOcr(arCrop(src,sw,sh,arR('name',src),arSc(sh,3,src))); /* b294: 연결 중엔 arNameWatch 가 0.2초마다 따로 봄 */
      const b=ARX.nTimer&&!force?null:arDetectBoss(ARX.mapText), cid=ARX.nTimer&&!force?'':arDetectChar(ARX.nameText), now=Date.now(), stale=now-(ARX.detT||0)>ARX.cfg.stickySec*1000;
      // b285: 화면이 번쩍이거나 컷신이라 못 읽은 프레임은 직전 인식을 유지 (stickySec 지나면 비움)
      if(b) arMapHit(b,now); else if(stale&&!ARX.lock&&!(ARX.nTimer&&!force)&&arNorm(ARX.mapText||'').length>=2){ /* t556: 못 읽음이면 유지 */ if(arBoxNeed()) ARX.mapDet=null; else { ARX.det.boss=''; ARX.det.diff=''; ARX.det.src=''; } }
      if(cid){ ARX.det.cid=cid; ARX.cidT=now; } else if(!(ARX.nTimer&&!force)&&arUnkName(ARX.nameText)) ARX.det.cid=""; /* t552 */ }
    const found=[], seen=new Set(); ARX.found=[]; ARX.scores=ARX.scores||{};
    if(!(ARX.stream&&ARX.cfg.watchFps>0)){ // 배너는 연결 중엔 배너 순간 감시(매 프레임)가 맡음 — 여기선 테스트·감시 없음일 때만
      const cv=arCrop(src,sw,sh,arR('banner',src),1), img=cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,cv.width,cv.height);
      const hs=await arFindIcons(img,arIconPx(sh,'banner')); ARX.scores.banner=ARX.lastScore; for(const h of hs){ h.reg='banner'; found.push(h); ARX.found.push([h.k,'banner',+h.score.toFixed(3)]); } }
    for(const h of found){ seen.add(h.k); ARX.hits[h.k]=(ARX.hits[h.k]||0)+1; if(ARX.hits[h.k]>=ARX.cfg.confirm&&ARX.cfg.on) arPick(h,'배너'); }
    for(const k of Object.keys(ARX.hits)) if(!seen.has(k)) delete ARX.hits[k];
    if(force!=='noitem'){ await arBoxStep(src,force); if(arBoxOk()) await arItemStep(src,sh); } /* b300: 상자 보이기 전엔 아이템 안 찾음 */
    arLivePaint(); } finally{ ARX.busy=false; } }
/* b287: 바닥·공중 — 아이템 영역이 바뀐 프레임만, itemFps 이하, 이전 것이 끝나야 (밀리면 건너뛰고 '건너뜀'에 셈) */
async function arItemStep(src,sh,now){ const pf=arPf(), r=arR('item',src); now=now||Date.now();
  const sm=ARX.ism||(ARX.ism=document.createElement('canvas')); sm.width=48; sm.height=24; const g=sm.getContext('2d',{willReadFrequently:true}), sw=src.videoWidth||src.width; g.drawImage(src,r.x*sw,r.y*sh,r.w*sw,r.h*sh,0,0,48,24);
  const d=g.getImageData(0,0,48,24).data, p=ARX.iprev; let diff=0; if(p) for(let i=0;i<d.length;i+=4) diff+=Math.abs(d[i]-p[i])+Math.abs(d[i+1]-p[i+1])+Math.abs(d[i+2]-p[i+2]);
  const changed=!p||diff/(48*24*3)>=1.5; if(p&&diff/(48*24*3)>=6) arBurst(now); // b292: 바닥 영역이 크게 바뀜(상자 깨짐 등) → full-rate if(!changed&&now-(ARX.itemT||0)<3000&&!(ARX.tracks||[]).some(t=>!t.done&&now-t.t<2500)) return []; /* 확인 중인 아이템이 있으면 화면이 그대로여도 다시 봄 */ ARX.iprev=Uint8ClampedArray.from(d);
  if(ARX.itemBusy||now-(ARX.itemT||0)<1000/Math.max(.2,arHot(now)?Math.max(ARX.cfg.itemFps,ARX.cfg.itemBurstFps||0):ARX.cfg.itemFps)){ pf.iskip++; return []; } ARX.itemBusy=true; ARX.itemT=now;
  try{ const hits=await arItemScan(src); pf.items++; ARX.itemHits=hits; if(hits.length) ARX.itemLog=(ARX.itemLog||[]).concat([{t:src.currentTime??null,at:now,hits:hits.map(h=>[h.k,+h.score.toFixed(3),h.x,h.y,h.w,h.h,h.ang,h.sq,h.occ?1:0])}]).slice(-300); for(const h of hits) ARX.found.push([h.k,h.air?'공중':'바닥',+h.score.toFixed(3)]); arTrack(hits,sh); return hits; } finally{ ARX.itemBusy=false; } }
function arPf(){ return ARX.pf||(ARX.pf={t0:performance.now(),frames:0,watched:0,missed:0,bannerMs:0,banners:0,items:0,iskip:0,last:null}); }
/* b286: 배너 순간 감시 — 매 프레임 배너 영역을 아주 작게 줄여 이전 프레임과 비교, 바뀐 프레임만 잘라 큐에 넣고 차례로 아이콘 매칭 (1프레임만 떠도 셈, 바쁠 때도 안 버림) */
function arBannerWatch(src,meta){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return false; const r=arR('banner',src), pf=arPf(), t0=performance.now();
  if(meta&&meta.presentedFrames){ if(pf.lastPF&&meta.presentedFrames>pf.lastPF+1) pf.missed+=meta.presentedFrames-pf.lastPF-1; pf.lastPF=meta.presentedFrames; } pf.watched++;
  const sm=ARX.bsm||(ARX.bsm=document.createElement('canvas')); sm.width=64; sm.height=16; const g=sm.getContext('2d',{willReadFrequently:true}); g.drawImage(src,r.x*sw,r.y*sh,r.w*sw,r.h*sh,0,0,64,16);
  const d=g.getImageData(0,0,64,16).data, p=ARX.bprev; let diff=0; if(p) for(let i=0;i<d.length;i+=4) diff+=Math.abs(d[i]-p[i])+Math.abs(d[i+1]-p[i+1])+Math.abs(d[i+2]-p[i+2]);
  ARX.bprev=Uint8ClampedArray.from(d); pf.watchMs=(pf.watchMs||0)+performance.now()-t0; if(p&&diff/(64*16*3)<4) return false;
  // 바뀐 프레임: 배너 영역만 지금 바로 떠 둠 (ImageBitmap — 메인 스레드에서 픽셀 안 읽음) → 큐 → Worker 에서 아이콘 매칭
  ARX.bq=ARX.bq||[]; const px=arIconPx(sh,'banner',src), x=Math.round(r.x*sw), y=Math.round(r.y*sh), w=Math.round(r.w*sw), h=Math.round(r.h*sh);
  const item=(arWorker()&&typeof createImageBitmap==='function')?{bmpP:createImageBitmap(src,x,y,w,h).catch(()=>null),px}:{img:arCrop(src,sw,sh,r,1).getContext('2d',{willReadFrequently:true}).getImageData(0,0,w,h),px};
  ARX.bq.push(item); if(ARX.bq.length>40){ const o=ARX.bq.shift(); pf.bdrop=(pf.bdrop||0)+1; o.bmpP&&o.bmpP.then(b=>b&&b.close()); }
  return arBannerPump(); }
async function arBannerPump(){ if(ARX.bpBusy) return ARX.bpP; ARX.bpBusy=true; ARX.bpP=(async()=>{ try{ while(ARX.bq&&ARX.bq.length){ const q=ARX.bq.shift(), pf=arPf();
    const G=q.bmpP?{bmp:await q.bmpP}:{img:q.img}; if(!G.bmp&&!G.img) continue; const C=arCandidates(); if(!C.length){ G.bmp&&G.bmp.close(); continue; }
    const r=await arMatchRun(G,[...new Set(C.map(c=>c.k))],[q.px],{thr:ARX.cfg.bannerThr}); pf.banners++; pf.bannerMs+=r.ms||0; ARX.lastScore=r.scores;
    for(const h of r.hits){ ARX.bannerHits=(ARX.bannerHits||[]).concat([[h.k,+h.score.toFixed(3)]]).slice(-20); if(ARX.cfg.on) arPick(h,'배너 순간'); } } } finally{ ARX.bpBusy=false; } })(); return ARX.bpP; }
/* b300 (사용자 규칙 t504u): 보상 맵에서 현재 보스의 원본 보상 상자(WZ Mob 원본 · 일부 영상 크롭)가 보이면 그때부터 아이템 기록. 상자 전엔 어떤 아이템도 기록 안 함.
   1/8 크기로 거칠게 찾고(색 3채널 마스크 NCC = OpenCV TM_CCOEFF_NORMED+mask) 상위 3곳을 1/4 크기에서 다시 맞춤. 템플릿 = 1080p 화면 크기의 1/4 (src/boxicons.json). */
const AR_BOX=/*__BOX_ICONS__*/{};
function arBoxNeed(){ return ARX.cfg.boxGate!==false&&Object.keys(AR_BOX).length>0; } // t522: 상자 템플릿이 있으면 보스=상자
function arBoxOk(){ if(!arBoxNeed()) return true; const L=ARX.lock; if(L&&L.boss===ARX.det.boss) return true; /* t537: 맵 이름 고정 중엔 시간 제한 없음 */ const B=ARX.box; if(B&&Date.now()-B.t>=(ARX.cfg.boxHoldSec||180)*1000){ ARX.box=null; if(ARX.det.src==='보상 상자'){ ARX.det.boss=''; ARX.det.diff=''; ARX.det.src=''; } return false; } return !!(B&&B.boss===ARX.det.boss); }
function arBoxTpl(k,D){ const c=ARX.boxT||(ARX.boxT={}), id=k+'/'+D; if(c[id]) return c[id]; const a=AR_BOX[k]; return c[id]=new Promise(res=>{ const im=new Image(); im.onload=()=>{ const w=Math.max(4,Math.round(im.width*4/D)), h=Math.max(4,Math.round(im.height*4/D)), cv=document.createElement('canvas'); cv.width=w; cv.height=h; const g=cv.getContext('2d',{willReadFrequently:true}); g.drawImage(im,0,0,w,h); const d=g.getImageData(0,0,w,h).data;
  const idx=[]; for(let i=0;i<w*h;i++) if(d[i*4+3]>200) idx.push(i); const n=idx.length; const m=[0,0,0]; for(const i of idx) for(let ch=0;ch<3;ch++) m[ch]+=d[i*4+ch]; for(let ch=0;ch<3;ch++) m[ch]/=n||1;
  const t=new Float32Array(n*3); let tt=0; idx.forEach((i,j)=>{ for(let ch=0;ch<3;ch++){ const v=d[i*4+ch]-m[ch]; t[j*3+ch]=v; tt+=v*v; } }); res({w,h,n,t,tt,ox:Int32Array.from(idx.map(i=>i%w)),oy:Int32Array.from(idx.map(i=>(i/w)|0))}); }; im.onerror=()=>res(null); im.src=a.u; }); }
function arNcc(I,W,H,T,x0,x1,y0,y1){ const out=[]; for(let y=Math.max(0,y0);y<=Math.min(H-T.h,y1);y++) for(let x=Math.max(0,x0);x<=Math.min(W-T.w,x1);x++){ let st=0, s0=0,s1=0,s2=0,q=0;
    for(let j=0;j<T.n;j++){ const p=((y+T.oy[j])*W+x+T.ox[j])*4, a=I[p], b=I[p+1], c=I[p+2]; st+=T.t[j*3]*a+T.t[j*3+1]*b+T.t[j*3+2]*c; s0+=a; s1+=b; s2+=c; q+=a*a+b*b+c*c; }
    const vi=q-(s0*s0+s1*s1+s2*s2)/T.n, den=Math.sqrt(Math.max(0,vi)*T.tt); out.push([den>1e-6?st/den:0,x,y]); } return out; }
function arBoxGrab(src,D){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height, r=arR('item',src), k=1080/arGH(src,sh)/D, cv=document.createElement('canvas'); cv.width=Math.round(r.w*sw*k); cv.height=Math.round(r.h*sh*k);
  const g=cv.getContext('2d',{willReadFrequently:true}); g.imageSmoothingQuality='high'; g.drawImage(src,r.x*sw,r.y*sh,r.w*sw,r.h*sh,0,0,cv.width,cv.height); return {d:g.getImageData(0,0,cv.width,cv.height).data,w:cv.width,h:cv.height}; }
async function arBoxScore(src,k){ const T8=await arBoxTpl(k,8), T4=await arBoxTpl(k,4); if(!T8||!T4) return 0; const G8=arBoxGrab(src,8), G4=arBoxGrab(src,4);
  const r=arNcc(G8.d,G8.w,G8.h,T8,0,1e9,0,1e9).sort((a,b)=>b[0]-a[0]), top=[]; for(const c of r){ if(c[0]<.4||top.length>=3) break; if(top.every(t=>Math.abs(t[1]-c[1])>2||Math.abs(t[2]-c[2])>2)) top.push(c); }
  let best=0; for(const [,x,y] of top) for(const c of arNcc(G4.d,G4.w,G4.h,T4,2*x-3,2*x+3,2*y-3,2*y+3)) best=Math.max(best,c[0]); return best; }
const AR_BOX_REW_MS=200; /* t547 */
function arRewMap(now){ const M=ARX.mapSt; return M&&M.kind.includes('r')&&now-(M.t||0)<8000?M:null; }
async function arBoxStep(src,force){ if(!arBoxNeed()) return; if(arBoxOk()){ const B=ARX.box, n=Date.now(); /* t537: 상자는 봤는데 그때 맵 이름이 없었으면 상자가 보이는 동안 다시 확인 */
    if(B&&!ARX.lock&&ARX.mapDet&&ARX.mapDet.boss===B.boss&&(force||n-(ARX.boxScanT||0)>=1000/(ARX.cfg.boxFps||2))){ ARX.boxScanT=n; if(await arBoxScore(src,B.key)>=AR_BOX[B.key].thr) arLockTry(src,B.boss,n); } return; } const now=Date.now(), RM=arRewMap(now), RK=RM?Object.keys(AR_BOX).filter(k=>(AR_BOX[k].boss||k)===RM.boss):[]; /* t547: 보상 맵이면 그 보스 상자만 0.2초마다, 다른 맵은 1초마다 돌아가며 */
  if(!force&&now-(ARX.boxScanT||0)<(RK.length?AR_BOX_REW_MS:1000/(ARX.cfg.boxFps||1))-5) return; if(ARX.boxBusy) return; ARX.boxScanT=now; ARX.boxBusy=true; try{
  const K=RK.length?RK:Object.keys(AR_BOX), R=force||RK.length?1:Math.max(1,ARX.cfg.boxRounds||3), per=Math.ceil(K.length/R), st=(ARX.boxRR||0)%R; ARX.boxRR=st+1; // 한 번에 1/R 씩 돌아가며 (상자는 몇 초 이상 보임)
  let best=null; for(const k of K.slice(st*per,st*per+per)){ const sc=await arBoxScore(src,k); if(sc>=AR_BOX[k].thr&&(!best||sc-AR_BOX[k].thr>best.sc-AR_BOX[best.k].thr)) best={k,sc}; }
  ARX.boxLast=best?[best.k,+best.sc.toFixed(3)]:null; if(!best) return;
  arBoxHit(best,now); } finally{ ARX.boxBusy=false; } }
function arBoxHit(best,now){
  const boss=AR_BOX[best.k].boss||best.k, b=findBoss(boss), m=ARX.mapDet&&ARX.mapDet.boss===boss&&ARX.mapDet.diff?ARX.mapDet.diff:'';
  ARX.box={boss,key:best.k,t:now,score:best.sc}; ARX.det.boss=boss; ARX.det.diff=m; ARX.det.diffSrc=m?'맵 이름':'캐릭터 설정'; ARX.det.src='보상 상자'; ARX.detT=now; arClrFinish(boss,m||ARX.det.diff,now); arLockTry(src,boss,now);
  arLog(`보상 상자 감지: ${b?.name||boss} (${best.sc.toFixed(2)}) → 현재 보스로 정하고 아이템 기록 시작${m?' · 난이도 '+({easy:'이지',normal:'노멀',hard:'하드',chaos:'카오스',extreme:'익스트림'}[m]||m)+' (맵 이름)':' · 난이도는 캐릭터 설정'}`); }
function arRecord(item,score,via='',n=1){ if(!ARX.det.boss) return; if(!arBoxOk()){ if(!ARX.noBoxT||Date.now()-ARX.noBoxT>5000){ ARX.noBoxT=Date.now(); arLog(`보상 상자 확인 전이라 기록 안 함: ${ITEMS[item]?.n||item} [${via}]`); } return; } /* b300 */ /* b291: 보상 맵에서 보스를 읽었을 때만 기록 */ const t=arTarget(); if(!t) return; const C=arCandidates(true).filter(c=>c.k===item); if(!C.length) return;
  const b=C.find(c=>t.c.weekly?.[c.b.id]===false)?.b||C[0].b, key=b.id+'|'+item, now=Date.now();
  if(ARX.recent[key]&&now-ARX.recent[key]<ARX.cfg.dedupSec*1000){ if(via) ARX.recentVia[key]=(ARX.recentVia[key]||'')+'+'+via; return; } ARX.recent[key]=now; ARX.recentVia[key]=via;
  if(C.find(c=>c.b===b)?.info){ arLog(`획득 감지(정보 칩, 기록 안 함): ${ITEMS[item]?.n} · ${b.name}${n>1?' ×'+n:''} [${via}]`); ARX.infoSeen=(ARX.infoSeen||[]).concat(key); arPanelPaint(); return; }
  if((+dropMap(t.c,b.type)[key]||0)>=1){ arLog(`이미 기록됨: ${ITEMS[item]?.n} · ${b.name}`); return; } // 다시 누르면 취소되는 수동 칩과 달리 건드리지 않음
  if(S.activeId!==t.c.id){ S.activeId=t.c.id; render(); }
  changeDrop(key,+1); (ARX.runRec=ARX.runRec||[]).unshift({k:item,b:b.name,c:t.c.name,t:new Date().toTimeString().slice(0,5)}); ARX.runRec.length=Math.min(ARX.runRec.length,30); arLog(`자동 기록: ${ITEMS[item]?.n} · ${b.name}${n>1?' ×'+n:''} [${via} ${(+score).toFixed(2)}]`); arToast(item,b,key,t.c.id); }
/* b288: 색까지 봤는데도 닮은 두 아이콘 중 확실하지 않으면 자동 기록 안 하고 '직접 고르기' 칩 */
function arPick(h,via){ if(!ARX.det?.boss){ if(!ARX.noBossT||Date.now()-ARX.noBossT>5000){ ARX.noBossT=Date.now(); arLog(`보스 확인 전이라 기록 안 함: ${ITEMS[h.k]?.n||h.k} [${via}]`); } return; } // b288: 보스 모를 땐 모든 보스 아이콘 후보 → UI·글자 오인식
  if(!h.amb||h.amb.length<2) return arRecord(h.k,h.score,via); const C=arCandidates(), am=h.amb.filter(k=>C.some(c=>c.k===k)); if(am.length===1) return arRecord(am[0],h.score,via+' 색');
  if(!am.length) return; const key=am.join('/'); if((ARX.amb||[]).some(a=>a.key===key&&Date.now()-a.t<ARX.cfg.dedupSec*1000)) return;
  ARX.amb=[{key,ks:am,via,score:h.score,t:Date.now()}].concat(ARX.amb||[]).slice(0,5); arLog(`닮은 아이템 — 직접 고르기: ${am.map(k=>ITEMS[k]?.n).join(' / ')} [${via}]`); arPanelPaint(); }
function arLog(s){ ARX.log.unshift(new Date().toTimeString().slice(0,8)+' '+s); ARX.log.length=Math.min(ARX.log.length,20); }
function arToast(item,b,key,cid){ let el=$('#arToast'); if(!el){ el=document.createElement('div'); el.id='arToast'; el.className='ar-toast'; el.setAttribute('role','status'); document.body.appendChild(el); }
  el.innerHTML=`<span>${itemIcon(item)}</span><span>자동 기록: <b>${esc(ITEMS[item]?.n||item)}</b> · ${esc(b.name)}</span><button type="button" class="ar-undo">취소</button>`; el.classList.add('show');
  el.querySelector('.ar-undo').onclick=()=>{ const c=S.characters.find(x=>x.id===cid); if(typeof closeRing==='function'&&ringPending?.key===key) closeRing(); else if(c&&(+dropMap(c,b.type)[key]||0)>=1){ if(S.activeId!==cid){ S.activeId=cid; } changeDrop(key,-1); } arLog('취소: '+(ITEMS[item]?.n||item)); el.classList.remove('show'); arPanelPaint(); };
  clearTimeout(arToast._t); arToast._t=setTimeout(()=>el.classList.remove('show'),8000); }
/* 연결 / 끊기 */
/* b288: 연결 — 클릭 바로 getDisplayMedia (await 전에 호출해야 크롬이 선택 창을 띄움). 끊긴 스트림이 남아 있으면 정리하고 다시, 실패하면 이유를 패널에 */
/* t551: 'Lv.285 이름'처럼 이름이 읽혔는지 (빈 글자·잡음은 아님) */
function arUnkName(t){ const m=String(t||'').match(/lv\.?\s*\d{2,3}\s*([가-힣A-Za-z0-9]{2,})/i); return !!m; }
function arLive(){ const t=ARX.stream?.getVideoTracks?.()[0]; return !!(ARX.stream&&ARX.video&&(!t||t.readyState==='live')); }
async function arConnect(){ if(arLive()) return arPanel(true); if(ARX.stream||ARX.video){ try{ arDisconnect(); }catch(e){ ARX.stream=null; ARX.video=null; } }
  const md=navigator.mediaDevices; if(!md?.getDisplayMedia){ ARX.connErr='이 브라우저는 화면 공유를 지원하지 않아요 (PC 크롬·엣지 권장, https 주소).'; arPanel(true); return; }
  ARX.connErr=''; let fr=Math.max(+ARX.cfg.fps||0,+ARX.cfg.watchFps||0); if(!(fr>0)) fr=30; let p;
  try{ p=md.getDisplayMedia({video:{frameRate:{ideal:fr}},audio:false}); }catch(e){ p=Promise.reject(e); }
  try{ arOcrLoad(); }catch(e){} // b294: 화면 고르는 동안 OCR 모델 미리 불러옴
  try{ ARX.stream=await p; }catch(e){ ARX.stream=null;
    if(e&&(e.name==='OverconstrainedError'||e.name==='TypeError')){ try{ ARX.stream=await md.getDisplayMedia({video:true,audio:false}); }catch(e2){ e=e2; } }
    if(!ARX.stream){ ARX.connErr=e?.name==='NotAllowedError'?'화면 공유가 취소됐거나 브라우저·윈도우 설정에서 막혀 있어요. (다시 눌러 주세요)':`화면 공유 실패: ${e?.name||''} ${e?.message||e}`; console.warn('[화면 공유]',e); arPanel(true); return; } }
  try{ const v=document.createElement('video'); v.muted=true; v.playsInline=true; v.style.cssText='position:fixed;left:-9999px;top:0;width:2px;height:2px;opacity:0;pointer-events:none'; document.body.appendChild(v); v.srcObject=ARX.stream; v.play().catch(()=>{});
    ARX.stream.getVideoTracks()[0]?.addEventListener('ended',arDisconnect); arStart(v); }
  catch(e){ console.warn('[분석 시작 실패 → 메인 스레드로]',e); try{ ARX.wkOff=String(e); try{ ARX.wk?.terminate(); }catch(_){ } ARX.wk=null; arStart(ARX.video||document.querySelector('video[style*="-9999px"]')); }catch(e2){ ARX.connErr='분석 시작 실패: '+(e2?.message||e2); try{ arDisconnect(); }catch(_){ } arPanel(true); } } }
/* b294: 상태바 이름 빠른 감시 — 0.2초마다 이름 영역 축소본(96x12)만 비교, 바뀌었거나(캐릭터 접속·변경) 아직 못 읽었으면 바로 OCR 1번.
   예전: 맵+이름 OCR 을 3초(ocrEvery)마다 한 번, 보스·아이템 처리 뒤에 → 접속 후 이름 인식까지 7~9초 */
/* t520u: 보유 메소 — 프로필 고정 영역(인벤 'inv' / 창고 열림 'sto'+'stoInv')에서 읽음. 닉네임 → 메소 → 닉네임 순서, 앞뒤 닉네임이 같을 때만 저장 */
function arMesoParse(t){ let s=String(t||'').replace(/[Oo○◯]/g,'0').replace(/[Il!]/g,'1').replace(/[역얻억엌먹]/g,'억').replace(/[민많안믄맨반]/g,'만').replace(/[죠즈]/g,'조').replace(/[^0-9조억만]/g,'');
  const m=s.match(/^(?:(\d{1,4})조)?(?:(\d{1,4})억)?(?:(\d{1,4})만)?(\d{1,4})?$/); if(!s||!m||!/\d/.test(s)) return null;
  return (+m[1]||0)*1e12+(+m[2]||0)*1e8+(+m[3]||0)*1e4+(+m[4]||0); }
function arMesoPanel(src,k){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height, r=arR(k,src); if(!sw||!sh||!r) return false; const cv=arCrop(src,sw,sh,{x:r.x+r.w*.18,y:r.y+r.h*.15,w:r.w*(k==='inv'?.5:.8),h:r.h*.7});
  const d=cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,cv.width,cv.height).data; let wh=0,dk=0,n=d.length/4; for(let i=0;i<d.length;i+=4){ const lo=Math.min(d[i],d[i+1],d[i+2]), hi=Math.max(d[i],d[i+1],d[i+2]); if(lo>205) wh++; else if(hi<120) dk++; }
  return wh/n>.55&&(k==='sto'||dk/n>.01); } // 흰 바탕 + 어두운 숫자 = 메소 칸
async function arMesoRead1(src,k,sc,thr){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height, r=arR(k,src); const cv=arCrop(src,sw,sh,{x:r.x+r.w*.17,y:r.y,w:r.w*(k==='inv'?.53:.79),h:r.h},sc);
  const g=cv.getContext('2d',{willReadFrequently:true}), im=g.getImageData(0,0,cv.width,cv.height), d=im.data; for(let i=0;i<d.length;i+=4){ d[i]=255-d[i]; d[i+1]=255-d[i+1]; d[i+2]=255-d[i+2]; } g.putImageData(im,0,0); // 어두운 글자 → 밝게 (arOcr 는 밝은 글자용)
  const t=await arMesoOcr(cv,thr); return {t,v:arMesoParse(t)}; }
/* 배율 3·4 두 번 읽어 같을 때만 인정 (다르면 배율 2로 한 번 더 → 두 번 나온 값) */
async function arMesoRead(src,k){ const thr=+ARX.cfg.mesoThr||100, sl=ARX.cfg.mesoSc?[+ARX.cfg.mesoSc]:[3,4,2], got=[]; let t='';
  let n=0; for(const sc of sl){ const r=await arMesoRead1(src,k,sc,thr); n++; t=t||r.t; if(r.v==null) continue; if(got.includes(r.v)||sl.length===1) return {t:r.t,v:r.v,hi:n===2&&got.length===1}; got.push(r.v); } /* t554 hi: 배율 3·4 가 처음부터 모든 자리 일치 = 신뢰도 높음 */
  return {t,v:null}; }
/* 메소 전용 워커: 숫자·조억만만 허용(한 줄) → '억'을 '먹', '만'을 '반'으로 읽는 일 줄임 */
function arMesoWLoad(){ if(ARX.ocrMP) return ARX.ocrMP; ARX.ocrMP=arOcrLoad().then(()=>window.Tesseract?Tesseract.createWorker('kor',1,{workerPath:new URL('ocr/worker.min.js',location.href).href,corePath:new URL('ocr/',location.href).href,langPath:new URL('ocr',location.href).href,gzip:false,workerBlobURL:false}):null)
  .then(async w=>{ if(w) await w.setParameters({tessedit_char_whitelist:'0123456789조억만 ',tessedit_pageseg_mode:'7'}); return ARX.ocrM=w; }).catch(e=>{ ARX.ocrMP=null; }); return ARX.ocrMP; }
async function arMesoOcr(cv,thr){ await arMesoWLoad(); if(!ARX.ocrM) return arOcr(cv,thr,1); const k=ARX.ocrF; ARX.ocrF=ARX.ocrM; try{ return await arOcr(cv,thr,1); } finally{ ARX.ocrF=k; } }
async function arMesoNow(src){ const cid0=ARX.det.cid; if(!cid0) return {why:'nocid'}; const stoOpen=arMesoPanel(src,'sto')&&arMesoPanel(src,'stoInv'), invOpen=!stoOpen&&arMesoPanel(src,'inv'); if(!stoOpen&&!invOpen) return {why:'closed'};
  const a=await arMesoRead(src,stoOpen?'stoInv':'inv'), b=stoOpen?await arMesoRead(src,'sto'):null; if(a.v==null) return {why:'ocr',t:a.t};
  const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height, nt=await arOcr(arCrop(src,sw,sh,arR('name',src),arSc(sh,3,src)),150,1), cid1=(ARX.nameOf||arDetectChar)(nt); /* nameOf: 테스트용 */
  if(cid1!==cid0||ARX.det.cid!==cid0) return {why:'name',cid0,cid1}; // 메소 읽는 동안 캐릭터가 바뀌었으면 버림
  const res={cid:cid0,inv:a.v,sto:b&&b.v!=null?b.v:null,src:stoOpen?'storage':'inventory'};
  /* t554/t555: 단일 판독 즉시 확정 — 판독 신뢰도(배율 3·4 가 전 자리 일치)만 봄. 직전값 대비 급증 상한은 안 둠(결정석 판매로 한 번에 50억+ 가능).
   * 신뢰도 낮은 판독만 다음 판독과 같으면 확정. (t550 '3번 연속 같은 값'은 사냥 중 메소가 계속 변하면 영영 저장 안 돼서 폐기) */
  const hi=a.hi&&(!b||b.hi), VK=cid0+'|'+res.inv+'|'+res.sto+'|'+res.src, Q=ARX.mesoSus;
  if(!hi){ if(Q&&Q.k===VK){ ARX.mesoSus=null; res.why2='recheck'; } else { ARX.mesoSus={k:VK}; return {...res,why:'suspect'}; } } else ARX.mesoSus=null;
  arMesoSave(cid0,res.inv,res.sto,Date.now()); return res; }
/* t554: 서버 호출 폭증 방지 — 값이 바뀌었을 때만, 최소 1분 간격으로 저장(그 사이 값은 보류했다가 다음 틱/연결 끊김 때 저장) */
function arMesoSave(cid,inv,sto,now){ ARX.mesoPend={cid,inv,sto}; arMesoFlush(now); }
function arMesoFlush(now,force){ const q=ARX.mesoPend; if(!q) return; if(!force&&ARX.mesoSaveT&&now-ARX.mesoSaveT<(+ARX.cfg.mesoSaveMs||60000)) return; ARX.mesoPend=null;
  if(typeof saveMeso==='function'&&saveMeso(q.cid,q.inv,q.sto)){ ARX.mesoSaveT=now; arLog(`보유 메소 저장: ${(S.characters.find(c=>c.id===q.cid)||{}).name||''} ${fmtMesoFull(q.inv)}${q.sto!=null?` · 창고 ${fmtMesoFull(q.sto)}`:''}`); } }
function arMesoTick(src,now){ arMesoFlush(now); if(ARX.mesoBusy||now-(ARX.mesoT||0)<(+ARX.cfg.mesoEvery||1000)) return; ARX.mesoT=now; ARX.mesoBusy=true; arMesoNow(src).then(r=>{ ARX.mesoLast=r; }).catch(()=>{}).finally(()=>{ ARX.mesoBusy=false; }); }
function arNameWatch(src){ if(!src) return; const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return; const r=arR('name',src), now=Date.now(); if(!ARX.bbT||now-ARX.bbT>3000){ ARX.bbT=now; const b=arBBox(src); const k=b?[b.x,b.y,b.w,b.h].map(v=>Math.round(v/16)).join(','):''; if(k!==ARX.bbKey){ ARX.bbox=b; ARX.bbKey=k; ARX.profT=0; } }
  if(!ARX.profBusy&&(!ARX.profT||now-ARX.profT>(ARX.prof?15000:3000))){ ARX.profT=now; ARX.profBusy=true; const was=ARX.prof?.lab; arProfDetect(src).then(P=>{ ARX.profBusy=false; if(P&&P.lab!==was){ arLog(`해상도 프로필: ${P.lab} (UI 배율 ${P.s}, 일치 ${P.score})`); try{ arPanel(); }catch(e){} } }).catch(()=>{ ARX.profBusy=false; }); }
  const sm=ARX.nsm||(ARX.nsm=document.createElement('canvas')); sm.width=96; sm.height=12; const g=sm.getContext('2d',{willReadFrequently:true}); g.drawImage(src,r.x*sw,r.y*sh,r.w*sw,r.h*sh,0,0,96,12);
  const d=g.getImageData(0,0,96,12).data, p=ARX.nprev; let diff=0; if(p) for(let i=0;i<d.length;i+=4) diff+=Math.abs(d[i]-p[i])+Math.abs(d[i+1]-p[i+1])+Math.abs(d[i+2]-p[i+2]);
  const changed=!p||diff/(96*12*3)>=3; ARX.nprev=Uint8ClampedArray.from(d); if(changed){ ARX.nChgT=now; ARX.nameOk=false; }
  const need=(!ARX.nameOk&&now-(ARX.nChgT||0)<4000)||(!ARX.det.cid&&now-(ARX.nOcrT||0)>1000)||now-(ARX.nOcrT||0)>ARX.cfg.ocrEvery;
  if(ARX.nameBusy&&now-(ARX.nOcrT||0)>(+ARX.cfg.ocrTimeout||6000)+2000) ARX.nameBusy=false; /* b296: 바쁨 표시가 안 풀리면 강제로 풂 */ if(!ARX.ocr){ if(!ARX.ocrP) try{ arOcrLoad(); }catch(e){} return; } /* b296: 워커가 죽었으면 다시 띄움 */
  try{ arClrTick(src,now); }catch(e){}
  arMesoTick(src,now); /* t520u: 인벤·창고 창이 열려 있으면 보유 메소 읽기 */
  if(!need||ARX.nameBusy) return; ARX.nameBusy=true; ARX.nOcrT=now; const cv=arCrop(src,sw,sh,r,arSc(sh,[3,4,2][(ARX.nTry=(ARX.nTry||0)+1)%3],src)); /* 못 읽으면 다음 번엔 다른 배율 */
  return arOcr(cv,150,1).then(arNameRes).catch(()=>{}).finally(()=>{ ARX.nameBusy=false; }); }
/* t551/t552: 상태바 OCR 결과 처리 — 목록 캐릭터면 대상, 이름은 읽혔는데 목록에 없으면 '-', 못 읽으면(검은 화면 등) 직전 유지 */
function arNameRes(t){ ARX.nameText=t; const cid=arDetectChar(t), n2=Date.now(); if(cid){ ARX.nameOk=true; ARX.cidT=n2; ARX.unkName=0; if(cid!==ARX.det.cid){ ARX.det.cid=cid; ARX.nameMs=n2-(ARX.nChgT||n2); arLivePaint(); } }
    else if(arUnkName(t)&&(ARX.nChgT||0)>(ARX.cidT||0)){ if(ARX.det.cid){ ARX.det.cid=''; arLivePaint(); } ARX.unkName=1; } /* t551: 상태바가 바뀌었고 이름은 읽혔는데 목록에 없음 → 바로 '-' */ /* t552: 검은 화면·못 읽음이면 직전 캐릭터 유지 */ /* b296: 상태바가 안 바뀌었으면 마지막 확인 이름 유지 */ }
/* b296: 미니맵 제목 감시 — 0.2초마다 작게 떠서 바뀌면 바로 OCR (예전: 3초마다 + 바닥 찾기 끝난 뒤라 보스 바뀌는 데 3~10초).
   보상 맵이면 보스 바로 바꿈. 다른 맵 제목이 2번 연속 읽히면(맵 옮김) 이전 보스를 비움 → 다음 보상 맵에서 새 보스. */
/* t522: 맵 이름 인식 결과 반영 — 상자 게이트가 켜져 있으면 보스는 안 바꾸고 난이도 보조(mapDet)만, 다른 보스 보상 맵이면 상자 해제. 바뀌었으면 true */
/* t529~t531: 보스 클리어 시간 — 위 가운데 '남은시간' 타이머(7세그먼트 숫자)를 보일 때마다 읽어 입장 시각 = 지금 − (제한 − 남은). 제한은 AR_CLR_LIM 또는 첫 읽은 값을 분 단위로 올림.
 * 계속 줄어드는 값만, 갑자기 늘면(클리어 시 5:00 리셋) 그 뒤는 무시. 여러 번 읽은 입장 시각의 중앙값. 끝 = 그 보스 보상 상자 감지.
 * 상자 전 타이머를 한 번도 못 읽었으면 보스 맵 이름 인식 시각을 시작으로 쓰고 (추정) 표시. PRACTICE MODE 면 기록 안 함, 상자 없이 맵을 나가면 버림. */
const AR_CLR_LIM={}; /* 'bossId|diff' → 초 (모르면 첫 읽은 값 올림) */
const AR_SEG={'1110111':0,'0010010':1,'1011101':2,'1011011':3,'0111010':4,'1101011':5,'1101111':6,'1010010':7,'1110010':7,'1111111':8,'1111011':9};
/* 게임 화면 위 가운데 560×220(UI 배율 1 기준)을 1배로 줄여 읽음 → {m,s,sec} 또는 null */
function arClrParse(d,W,H){ const N=W*H, Y=new Uint8Array(N), L=new Uint8Array(N);
  for(let i=0;i<N;i++){ const r=d[i*4],g=d[i*4+1],b=d[i*4+2]; Y[i]=(r>125&&g>75&&r-b>45)?1:0; L[i]=(Y[i]||(r+g+b)/3>130)?1:0; }
  const rc=new Int32Array(H); for(let y=0;y<H;y++){ let c=0; for(let x=0;x<W;x++) c+=Y[y*W+x]; rc[y]=c; }
  const fr=(y0,y1,x0,x1)=>{ let n=0,c=0; for(let y=y0;y<Math.max(y1,y0+1);y++) for(let x=x0;x<Math.max(x1,x0+1);x++){ n++; c+=L[y*W+x]; } return n&&c/n>.3?1:0; };
  for(let y0=6;y0<H-36;y0++){ if(rc[y0]<2||rc[y0-1]>=2) continue;
    const cs=[]; for(let x=0;x<W;x++){ let c=0; for(let y=y0;y<y0+36;y++) c+=Y[y*W+x]; if(c>=2) cs.push(x); } if(!cs.length) continue;
    const runs=[]; let st=cs[0],pv=cs[0]; for(const c of cs.slice(1)){ if(c>pv+3){ runs.push([st,pv]); st=c; } pv=c; } runs.push([st,pv]);
    if(runs.length<3||runs.length>4) continue; const dg=[]; let bad=false;
    for(const [c0,c1] of runs){ const w=c1-c0+1; if(w>34){ bad=true; break; }
      if(w<8){ dg.push(fr(y0-6,y0-1,Math.max(0,c1-20),c1-6)?7:1); continue; } /* 좁으면 1 (7은 위 가로줄이 흰색이라 노란 칸이 좁음) */
      const X=(a,b)=>[c0+Math.floor(a*w),c0+Math.floor(b*w)];
      const k=[fr(y0-6,y0-1,...X(.3,.7)),fr(y0+1,y0+10,...X(0,.25)),fr(y0+1,y0+10,...X(.75,1)),fr(y0+13,y0+18,...X(.3,.7)),fr(y0+20,y0+29,...X(0,.25)),fr(y0+20,y0+29,...X(.75,1)),fr(y0+31,y0+35,...X(.3,.7))].join('');
      if(AR_SEG[k]==null){ bad=true; break; } dg.push(AR_SEG[k]); }
    if(bad) continue; const n=runs.length, g1=runs[n-2][0]-runs[n-3][1], g2=runs[n-1][0]-runs[n-2][1];
    if(g1<30||g2>27||dg[n-2]>5) continue; /* 분↔초 사이엔 '분' 글자(≈43px), 초 두 자리는 붙어 있음 */
    const m=n===4?dg[0]*10+dg[1]:dg[0], s=dg[n-2]*10+dg[n-1]; return {m,s,sec:m*60+s}; }
  return null; }
function arClrCanvas(src){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return null; const G=arGeom(sw,sh), s=G.s||1, W=560, H=220;
  const cv=ARX.clrCv||(ARX.clrCv=document.createElement('canvas')); cv.width=W; cv.height=H; const g=cv.getContext('2d',{willReadFrequently:true});
  g.drawImage(src,G.gx+(G.gw-W*s)/2,G.gy,W*s,H*s,0,0,W,H); return cv; }
function arClrRead(src){ const cv=arClrCanvas(src); if(!cv) return null; return arClrParse(cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,cv.width,cv.height).data,cv.width,cv.height); }
function arClrNew(now){ return ARX.clr={boss:'',diff:'',reads:[],mapT:0,practice:false,jump:0,up:0,lim:0,t0:now}; }
function arClrTick(src,now){ if(!src||ARX.cfg.clrOff) return; if(now-(ARX.clrT||0)<1000) return; ARX.clrT=now;
  const r=arClrRead(src); ARX.clrLast=r; if(!r) return; ARX.clrSeen=now; if(ARX.clrHold) return; /* 상자 뒤(5:00 리셋 타이머)는 맵 나갈 때까지 무시 */
  const C=ARX.clr||arClrNew(now); if(C.jump) return; const last=C.reads[C.reads.length-1];
  if(!C.lim&&!last) C.lim=Math.ceil((r.sec+1)/60)*60; const lim=C.lim; let ok, up;
  if(C.reads.length>=3){ const st=arMedian(C.reads.map(x=>x.t-(lim-x.rem)*1000)), ex=lim-(now-st)/1000; ok=Math.abs(r.sec-ex)<=3; up=r.sec>ex+10; } /* 잘못 읽은 값 하나는 버림 */
  else { ok=!last||r.sec<=last.rem; up=!!last&&r.sec>last.rem+10; }
  if(ok){ C.up=0; C.reads.push({t:now,rem:r.sec}); }
  else if(up&&++C.up>=2){ C.jump=now; arLog(`남은시간이 갑자기 늘어남 (${r.m}:${String(r.s).padStart(2,'0')}) → 클리어 신호, 이후 값 무시`); return; }
  if(!C.practice&&!ARX.clrPBusy&&now-(ARX.clrPT||0)>5000&&typeof arOcr==='function'&&ARX.ocr){ ARX.clrPT=now; ARX.clrPBusy=true; const cv=document.createElement('canvas'), s0=ARX.clrCv; cv.width=s0.width*2; cv.height=s0.height*2; cv.getContext('2d').drawImage(s0,0,0,cv.width,cv.height);
    arOcr(cv,150,1).then(t=>{ if(/PRACT[I1l]CE|MODE\s*PRA/i.test(t||'')&&ARX.clr===C){ C.practice=true; arLog('PRACTICE MODE — 클리어 시간 기록 안 함'); } }).catch(()=>{}).finally(()=>{ ARX.clrPBusy=false; }); } }
function arClrMap(b,now){ if(!b||!b.boss||ARX.clrHold) return; const C=ARX.clr||arClrNew(now); if(!C.mapT) C.mapT=now; if(!C.boss) C.boss=b.boss; if(b.diff) C.diff=b.diff; }
function arClrLeave(now){ if(ARX.clrSeen&&now-ARX.clrSeen<3000) return; /* 타이머가 아직 보이면 같은 보스 맵 */ if(ARX.clr&&!ARX.clrHold) arLog('보상 상자 없이 맵을 나감 — 클리어 시간 버림'); ARX.clr=null; ARX.clrHold=false; }
const arMedian=a=>{ const b=[...a].sort((x,y)=>x-y), n=b.length; return n%2?b[(n-1)/2]:(b[n/2-1]+b[n/2])/2; };
function arClrFinish(boss,diff,now){ const C=ARX.clr; ARX.clr=null; ARX.clrHold=true; if(!C) return null; if(C.practice){ arLog('PRACTICE MODE 라 클리어 시간 기록 안 함'); return null; }
  if(arLive()&&!ARX.det.cid){ arLog('캐릭터 목록에 없는 캐릭터라 클리어 시간 기록 안 함'); return null; } /* t551 */
  if(C.boss&&C.boss!==boss&&!C.reads.length) return null; diff=diff||C.diff||''; let start, est=false;
  if(C.reads.length){ const lim=AR_CLR_LIM[boss+'|'+diff]||C.lim||Math.ceil((C.reads[0].rem+1)/60)*60; start=arMedian(C.reads.map(x=>x.t-(lim-x.rem)*1000)); }
  else if(C.mapT){ start=C.mapT; est=true; } else return null;
  const sec=Math.round((now-start)/1000); if(!(sec>0&&sec<4*3600)) return null; const b=findBoss(boss), id=b?.id||boss;
  if(!diff){ const c=S.characters?.find(x=>x.id===ARX.det.cid); diff=c?.bosses?.[id]?.diff||b?.diffs?.[0]||''; }
  S.clears=S.clears||{}; S.clears[id+'|'+diff]={sec,at:now,est,n:C.reads.length}; try{ save(); }catch(e){} try{ if(typeof render==='function') render(); }catch(e){}
  arLog(`클리어 시간: ${b?.name||boss} ${diff} ${Math.floor(sec/60)}분 ${sec%60}초${est?' (추정 · 맵 이름 기준)':` (남은시간 ${C.reads.length}번 읽음)`}`); return S.clears[id+'|'+diff]; }
/* t537: 보스 확정 = 미니맵 맵 이름 + 보상 상자가 동시에 보일 때. 그때의 맵 이름 글자(정규화)와 글자 픽셀 지문을 저장하고,
 * 맵 이름이 그대로면 상자가 안 보여도 계속 인식·기록. 글자가 한 자라도 달라지고 픽셀 지문도 달라지면 즉시 중단
 * (글자만 다르고 픽셀이 같으면 OCR 흔들림으로 보고 무시, 픽셀만 다르면 바로 다시 읽어 확인). */
const AR_LOCK_DIST=.02;
function arMapKey(t){ return String(t||'').replace(/\s+/g,'').trim(); }
function arMapHash(src){ const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return null; const r=arR('map',src), W=Math.max(48,Math.min(480,Math.round(r.w*sw))), H=Math.max(8,Math.round(W*r.h*sh/(r.w*sw)));
  const cv=ARX.mhc||(ARX.mhc=document.createElement('canvas')); cv.width=W; cv.height=H; const g=cv.getContext('2d',{willReadFrequently:true}); g.drawImage(src,r.x*sw,r.y*sh,r.w*sw,r.h*sh,0,0,W,H);
  const d=g.getImageData(0,0,W,H).data, m=new Uint8Array(W*H); for(let i=0;i<W*H;i++) m[i]=(d[i*4]+d[i*4+1]+d[i*4+2])/3>170?1:0; m.W=W; m.H=H; return m; }
/* 글자 픽셀 지문 차이 = 다른 픽셀 / 글자 픽셀 합집합 (같은 화면이면 0 근처, 받침·모음 하나만 바뀌어도 수 %) */
function arHashDist(a,b){ if(!a||!b||a.length!==b.length) return 1; let x=0,o=0; for(let i=0;i<a.length;i++){ if(a[i]!==b[i]) x++; if(a[i]|b[i]) o++; } return o?x/o:0; }
function arLockTry(src,boss,now){ const M=ARX.mapDet, k=arMapKey(ARX.mapText);
  if(!M||M.boss!==boss||!k||now-(M.t||0)>Math.max(3000,(ARX.cfg.ocrEvery||0)+2000)) return false; /* 맵 이름이 지금 안 보이면 확정 안 함 */
  ARX.lock={boss,diff:ARX.det.diff,text:k,hash:arMapHash(src),t:now}; arLog(`보스 확정(맵 이름+상자): "${k}" — 맵 이름이 바뀔 때까지 유지`); return true; }
function arLockStop(why){ if(!ARX.lock) return; arLog(`맵 이름 바뀜 → 보스 인식 중단 (${why})`); ARX.lock=null; ARX.box=null; ARX.mapDet=null; ARX.det.boss=''; ARX.det.diff=''; ARX.det.src=''; arClrLeave(Date.now()+1e7); try{ arLivePaint(); }catch(e){} }
/* OCR 결과와 현재 프레임으로 고정 검사. 'stop'|'keep'|'jitter'|'' */
function arLockCheck(src,text){ const L=ARX.lock; if(!L) return ''; const k=arMapKey(text), dist=arHashDist(arMapHash(src),L.hash);
  if(!k) return dist>AR_LOCK_DIST*3?(arLockStop('맵 이름 사라짐'),'stop'):'keep'; /* 못 읽은 프레임: 픽셀도 크게 다를 때만 */
  if(k===L.text) return 'keep'; if(dist<=AR_LOCK_DIST) return 'jitter'; arLockStop(`"${L.text}" → "${k}"`); return 'stop'; }
/* t538/t541: 표로 읽은 맵 상태 (보스 기록과 별개). 대기 맵 = 진행 중 클리어 시간 버림·(고정 아니면) 상자 해제, 전투 맵 진입 = 클리어 시간 시작 */
function arMapState(text,now){ const T=arDetectBMap(text); if(!T){ if(arNorm(text).length>=2&&(ARX.mOffN=(ARX.mOffN||0)+1)>=2){ ARX.mapSt=null; if(ARX.det.boss||ARX.lock){ ARX.lock=null; ARX.box=null; ARX.mapDet=null; ARX.det.boss=''; ARX.det.diff=''; ARX.det.src=''; } ARX.mapOff=now; } return null; } ARX.mOffN=0; /* t556 (무관한 맵 2번 연속이면, 잡음 1번은 무시): 맵 이름을 실제로 읽었는데 보스와 무관 → 현재 보스 '-'. 검은 화면·못 읽음(글자 <2)은 직전 상태 유지 */ ARX.mapSt={...T,t:now};
  if(T.kind==='w'){ if(ARX.clr) arClrLeave(now+1e7); if(!ARX.lock&&ARX.box){ ARX.box=null; ARX.mapDet=null; ARX.det.boss=''; ARX.det.diff=''; ARX.det.src=''; } }
  else if(T.kind.includes('b')&&!T.kind.includes('r')) arClrMap(T,now); return T; }
/* '현재 보스' 상태: rew=보상 인식 중(상자/고정), run=진행 중, wait=대기 중 */
function arBossState(){ if(ARX.det.boss&&(!arBoxNeed()||(ARX.box&&arBoxOk()))) return 'rew'; const M=ARX.mapSt; if(!M) return ''; return M.kind.includes('w')?'wait':'run'; } /* t558: 대기맵과 이름이 같은 맵(세렌 왕궁 메인홀·검마 거인의 심장)은 상자 보이기 전까지 대기 중 */
function arMapHit(b,now){ const o=ARX.det.boss+'|'+ARX.det.diff;
  if(!b.kind||b.kind.includes('b')) arClrMap(b,now);
  if(arBoxNeed()){ ARX.mapDet={...b,t:now}; const B=ARX.box; if(ARX.lock){ if(b.diff&&b.boss===ARX.lock.boss){ ARX.det.diff=b.diff; ARX.det.diffSrc='맵 이름'; } } else if(B&&B.boss!==b.boss){ ARX.box=null; ARX.det.boss=''; ARX.det.diff=''; ARX.det.src=''; } else if(B&&b.diff){ ARX.det.diff=b.diff; ARX.det.diffSrc='맵 이름'; } }
  else { const keep=b.boss===ARX.det.boss?ARX.det.diff:''; ARX.det.boss=b.boss; ARX.det.diff=b.diff||keep; ARX.det.src=b.src; ARX.detT=now; }
  return o!==ARX.det.boss+'|'+ARX.det.diff; }
function arMapWatch(src){ if(!src) return; const sw=src.videoWidth||src.width, sh=src.videoHeight||src.height; if(!sw||!sh) return; const r=arR('map',src), now=Date.now();
  const sm=ARX.msm||(ARX.msm=document.createElement('canvas')); sm.width=96; sm.height=16; const g=sm.getContext('2d',{willReadFrequently:true}); g.drawImage(src,r.x*sw,r.y*sh,r.w*sw,r.h*sh,0,0,96,16);
  const d=g.getImageData(0,0,96,16).data, p=ARX.mprev; let diff=0; if(p) for(let i=0;i<d.length;i+=4) diff+=Math.abs(d[i]-p[i])+Math.abs(d[i+1]-p[i+1])+Math.abs(d[i+2]-p[i+2]);
  if(!p||diff/(96*16*3)>=3){ ARX.mChgT=now; ARX.mapOk=false; } if(ARX.lock&&now-(ARX.lhT||0)>=200){ ARX.lhT=now; if(arHashDist(arMapHash(src),ARX.lock.hash)>AR_LOCK_DIST){ ARX.mapOk=false; ARX.mChgT=now; } } /* t537 */ ARX.mprev=Uint8ClampedArray.from(d);
  if(ARX.mapBusy&&now-(ARX.mOcrT||0)>(+ARX.cfg.ocrTimeout||6000)+2000) ARX.mapBusy=false;
  if(!ARX.ocr){ if(!ARX.ocrP) try{ arOcrLoad(); }catch(e){} return; }
  const need=(!ARX.mapOk&&now-(ARX.mChgT||0)<6000)||now-(ARX.mOcrT||0)>ARX.cfg.ocrEvery; if(!need||ARX.mapBusy) return;
  ARX.mapBusy=true; ARX.mOcrT=now; const cv=arCrop(src,sw,sh,r,arSc(sh,3,src));
  return arOcr(cv,150,1).then(t=>{ ARX.mapText=t; try{ arMapState(t,Date.now()); }catch(e){} if(ARX.lock){ const r=arLockCheck(src,t); if(r){ if(r!=='stop'){ ARX.mapOk=true; ARX.mOther=0; const b=arDetectBoss(t); if(b) arMapHit(b,Date.now()); } return; } } const b=arDetectBoss(t), n2=Date.now();
    if(b){ ARX.mapOk=true; ARX.mOther=0; const ch=arMapHit(b,n2); if(ch){ ARX.mapMs=n2-(ARX.mChgT||n2); arLivePaint(); } }
    else if(arNorm(t).length>=2){ ARX.mapOk=++ARX.mOther>=2; if(ARX.mOther>=2){ ARX.mapDet=null; arClrLeave(Date.now()); if(ARX.det.boss){ ARX.box=null; ARX.det.boss=''; ARX.det.diff=''; ARX.det.src=''; arLivePaint(); } } /* t522: 보상 맵 나가면 상자도 해제 */ } }).catch(()=>{}).finally(()=>{ ARX.mapBusy=false; }); }
/* b287: 연결된 영상 분석 시작 (테스트는 <video src=mp4> 로 바로 부름). 메인 스레드엔 64x16 배너 비교만 매 프레임 — 나머지는 바뀐 프레임만·예산 안에서·Worker */
function arStart(v){ ARX.video=v; ARX.lastOcr=0; ARX.pf=null; arPf(); try{ arOcrLoad(); }catch(e){ ARX.ocrErr=true; } try{ arWorker(); }catch(e){ ARX.wk=null; ARX.wkOff=String(e); }
  ARX.nprev=null; ARX.nameOk=false; clearInterval(ARX.nTimer); ARX.mprev=null; ARX.mOther=0; ARX.nTimer=setInterval(()=>{ if(ARX.video){ arNameWatch(ARX.video); arMapWatch(ARX.video); } },200);
  ARX.timer=setInterval(()=>{ if(ARX.video) arFrame(ARX.video); },Math.round(1000/Math.max(.5,ARX.cfg.fps)));
  if(ARX.cfg.watchFps>0){ if(v.requestVideoFrameCallback){ const loop=(now,meta)=>{ if(ARX.video!==v) return; arPf().frames++; arBannerWatch(v,meta); arAirWatch(v); if(ARX.airHot&&!ARX.itemBusy){ const sh=v.videoHeight; if(sh) arItemStep(v,sh); } v.requestVideoFrameCallback(loop); }; v.requestVideoFrameCallback(loop); } else ARX.wTimer=setInterval(()=>{ if(ARX.video){ arBannerWatch(ARX.video); arAirWatch(ARX.video); } },Math.round(1000/ARX.cfg.watchFps)); }
  ARX.boxTimer=setInterval(()=>{ if(ARX.video&&!ARX.boxBusy&&arRewMap(Date.now())&&!arBoxOk()) arBoxStep(ARX.video,false).catch(()=>{}); },AR_BOX_REW_MS); /* t547: 보상 맵에선 프레임(1/fps)과 별도로 0.2초 */
  ARX.logTimer=setInterval(()=>{ if(ARX.ocr&&ARX.video) arLogFrame(ARX.video); },Math.round(1000/Math.max(1,ARX.cfg.logFps)));
  ARX.pfTimer=setInterval(()=>{ try{ arPerfPaint(); }catch(e){} },1000); arBtnPaint(); arPanel(true); }
function arDisconnect(){ try{ arMesoFlush(Date.now(),true); }catch(e){} clearInterval(ARX.nTimer); ARX.nTimer=0; clearInterval(ARX.pfTimer); clearInterval(ARX.logTimer); clearInterval(ARX.wTimer); clearInterval(ARX.boxTimer); ARX.bq=[]; (ARX.abuf||[]).forEach(e=>e.bmp&&e.bmp.close()); ARX.abuf=[]; ARX.alocs=[]; ARX.airT=0; ARX.bprev=null; ARX.logPrev=[]; clearInterval(ARX.timer); ARX.timer=0; ARX.stream?.getTracks().forEach(t=>t.stop()); ARX.stream=null; ARX.video?.remove(); ARX.video=null; ARX.tracks=[]; ARX.iprev=null; ARX.hits={}; ARX.det={cid:'',boss:'',diff:'',src:''}; ARX.box=null; arBtnPaint(); arPanelPaint(); }
function arBtnPaint(){ const b=$('#tabs [data-tab="auto"]'); if(b) b.classList.toggle('arlive',!!ARX.stream); arPanelPaint(); } // b294: 헤더 버튼 대신 탭에 초록 점
/* 패널: 상태 · 인식 결과 · 수동 선택 · 영역 맞추기(미리보기 드래그) · OCR 미리보기 */
let arRegionSel='item';
/* b294: 패널 = '보스 득템 자동 기록' 탭 내용 (예전 오른쪽 위 작은 떠 있는 패널 대신). 탭이 아닐 땐 그리지 않음 */
function renderAuto(){ const v=$('#view'); v.innerHTML='<div id="arPanel" class="ar-dash"></div>'; ARX.liveSig=''; arPanelBind(v.firstChild); arPanelPaint(); }
function arPanel(open){ if(open&&typeof tab!=='undefined'&&tab!=='auto'&&typeof render==='function'){ tab='auto'; render(); return; } arPanelPaint(); }
function arPanelBind(p){ {
    p.addEventListener('click',e=>{ const a=e.target.closest('[data-ar]')?.dataset.ar; if(!a) return;
      if(a==='guide') return; if(a==='roi'){ ARX.cfg.roi=!ARX.cfg.roi; arSave(); } else if(a==='stop') arDisconnect(); else if(a==='connect') arConnect(); else if(a.startsWith('pick:')){ const [,i,k]=a.split(':'), A=(ARX.amb||[])[+i]; if(A){ ARX.amb.splice(+i,1); arRecord(k,A.score,A.via+' 직접 고름'); arPanelPaint(); } }
      else if(a==='bindmap'){ const t=arNorm(ARX.mapText), bid=ARX.cfg.boss; if(t&&bid){ ARX.cfg.mapAlias[t]={boss:bid,diff:''}; arSave(); arLog(`맵 등록: ${ARX.mapText} → ${findBoss(bid)?.name}`); } }
      else if(a==='reset'){ const keep=ARX.cfg.mapAlias; ARX.cfg=Object.assign({},AR_DEF,{mapAlias:keep}); arSave(); }
      arPanelPaint(); });
    p.addEventListener('change',e=>{ const n=e.target.name; if(!n) return; if(n==='on') ARX.cfg.on=e.target.checked; else if(n==='prevOn') ARX.cfg.prev=e.target.checked?(ARX.cfg.prev||1):0; else if(n==='air') ARX.cfg.air=e.target.checked; else if(n==='cid'||n==='boss') ARX.cfg[n]=e.target.value; else ARX.cfg[n]=+e.target.value; arSave(); arPanelPaint(); });
    }
  }
function arPanelPaint(){ const p=$('#arPanel'); if(!p||p.hidden) return; const c=ARX.cfg, t=arTarget(), on=arLive(), dn=k=>({log:'획득 로그',banner:'획득 배너',item:'바닥 아이콘',map:'맵 이름',name:'상태바 이름'})[k];
  const detC=S.characters.find(x=>x.id===ARX.det.cid), bst=arBossState(), detB=(ARX.det.boss&&findBoss(ARX.det.boss))||(bst&&bst!=='rew'&&ARX.mapSt&&findBoss(ARX.mapSt.boss)), detD=ARX.det.boss?ARX.det.diff:(ARX.mapSt?.diff||''), mapN=(AR_REWARD.find(m=>m[1]===ARX.det.boss)||[''])[0], acc=detC&&typeof accOf==='function'?accOf(detC):null;
  if(!p.querySelector('.ar-g')){ p.innerHTML=`<div class="ar-sbar"></div><div class="ar-g">
    <div class="card ar-c ar-cchar"><h2>캐릭터 정보</h2><div class="ar-b"></div></div>
    <div class="card ar-c ar-cboss"><h2>현재 보스</h2><div class="ar-b"></div></div>
    <div class="card ar-c ar-clive"><h2>라이브 화면 <span class="hspace"></span><button type="button" class="btn sm ar-roib" data-ar="roi"></button><span class="ar-prof"></span></h2><div class="ar-vw"><video class="ar-vid" muted playsinline autoplay></video><canvas class="ar-prev" width="1280" height="720"></canvas><div class="ar-vnone">연결하면 게임 화면이 여기에 보여요</div></div><div class="ar-b ar-regs"></div></div>
    <div class="card ar-c ar-crec"><h2>현재까지 기록</h2><div class="ar-b"></div></div>
    <div class="card ar-c ar-cset" hidden><div class="ar-b"></div></div></div>`; }
  const q=s=>p.querySelector(s), vid=q('.ar-vid'); if(vid){ const ss=on?ARX.stream:null; if(vid.srcObject!==ss){ vid.srcObject=ss; if(ss) vid.play().catch(()=>{}); } q('.ar-vw').classList.toggle('on',!!ss||!!ARX.testSrc); }
  q('.ar-sbar').innerHTML=`<span class="ar-st ${on?'on':''}">${on?'● 연결됨':'○ 끊김'}</span><span class="hspace"></span>
    <label class="ar-sw"><input type="checkbox" name="on" ${c.on?'checked':''}> 자동 기록</label>${on?'<button type="button" class="btn" data-ar="stop">연결 끊기</button>':'<button type="button" class="btn primary" data-ar="guide">연결</button>'}${ARX.connErr?`<div class="ar-err" role="alert">${esc(ARX.connErr)}</div>`:''}`;
  q('.ar-cchar .ar-b').innerHTML=detC?`<div class="ar-who">${typeof avatar==='function'?avatar(detC):''}<div><div class="ar-big">${esc(detC.name)}</div><div class="muted">Lv.${esc(detC.level||'-')} ${esc(detC.job||'')}${acc?.name?' · '+esc(acc.name):''}${detC.world?' · '+esc(detC.world):''}</div></div></div>`
    :`<div class="ar-big dim">${on&&!ARX.unkName?'인식 중…':'-'}</div>`;
  q('.ar-cboss .ar-b').innerHTML=(bst?`<div class="ar-bst ${bst}"><i class="ar-dot"></i>${{wait:'대기 중',run:'진행 중',rew:'보상 인식 중'}[bst]}</div>`:'')+(detB?`<div class="ar-big ar-bline">${typeof bossIcon==='function'?bossIcon(detB):''}<span class="ar-bn">${esc(detB.name)}</span>${detD?' '+(typeof diffImg==='function'?diffImg(detD):esc(D[detD])):''}</div>`
    :`<div class="ar-big dim">-</div>`);
  arFitBoss();
  q('.ar-roib').textContent=c.roi?'영역 숨기기':'영역 보기'; { const pl=q('.ar-prof'); if(pl){ const L=arProfLab(); pl.textContent=L?L:(ARX.stream?'해상도 확인 중…':''); pl.title=L?'화면 공유 영상에서 자동 감지한 해상도·UI 비율':''; } } 
  const R=ARX.runRec||[]; q('.ar-crec .ar-b').innerHTML=`${(ARX.amb||[]).map((A,i)=>`<div class="ar-amb">닮은 아이템 — 직접 고르기 ${A.ks.map(k=>`<button type="button" class="chipb" data-ar="pick:${i}:${k}">${ITEM_ICONS[k]?`<img src="${ITEM_ICONS[k]}" alt="">`:''}${esc(ITEMS[k]?.n||k)}</button>`).join('')}</div>`).join('')}
    ${R.length?`<ul class="ar-recl">${R.map(r=>`<li>${ITEM_ICONS[r.k]?`<img src="${ITEM_ICONS[r.k]}" alt="">`:''}<span><b>${esc(ITEMS[r.k]?.n||r.k)}</b><small class="muted">${esc(r.b)} · ${esc(r.c)}</small></span><time>${r.t}</time></li>`).join('')}</ul>`:'<div class="muted">아직 기록 없음</div>'}`;
  q('.ar-cset .ar-b').innerHTML=`<details class="ar-dbg"><summary>수동 선택 · 조정 · 디버그</summary>
    <div class="ar-row"><select name="cid" aria-label="수동 캐릭터"><option value="">(수동) 캐릭터: 현재 선택</option>${S.characters.map(x=>`<option value="${esc(x.id)}" ${x.id===c.cid?'selected':''}>${esc(x.name)}</option>`).join('')}</select>
    <select name="boss" aria-label="수동 보스"><option value="">(수동) 보스: 자동</option>${BOSSES.filter(b=>DROPS[b.id]||Object.values(RING_DROPS).some(m=>m[b.id])).map(b=>`<option value="${b.id}" ${b.id===c.boss?'selected':''}>${esc(b.name)}</option>`).join('')}</select></div>
    <div class="ar-grid">${[['thr','아이콘 일치 기준',.5,1,.01],['groundThr','바닥 아이콘 기준',.5,1,.01],['itemFps','바닥 찾기(회/초)',.2,5,.2],['iconPx','아이콘 크기(px, 0=자동)',0,64,1],['logFps','로그 읽기(회/초)',1,6,1],['ds','대략 찾기 축소',1,8,1],['confirm','연속 프레임',1,5,1],['fps','초당 프레임',1,4,1],['dedupSec','중복 막기(초)',10,600,10]].map(([n,l,a,b,s])=>`<label>${l}<input type="number" name="${n}" min="${a}" max="${b}" step="${s}" value="${c[n]}"></label>`).join('')}</div>
    <label class="ar-sw"><input type="checkbox" name="air" ${c.air?'checked':''}> 공중 아이템(회전)도 찾기</label>
    <div>맵 OCR: <code>${esc(ARX.mapText||'-')}</code> ${ARX.cfg.boss&&ARX.mapText?'<button type="button" class="btn sm" data-ar="bindmap">이 맵 = 선택한 보스로 등록</button>':''}</div>
    <div>로그 OCR: <code>${esc((ARX.logText||'-').slice(-200))}</code></div><div>이름 OCR: <code>${esc(ARX.nameText||'-')}</code></div>
    <div>아이콘 점수: <code>${ARX.lastScore.map(([k,s])=>`${esc(ITEMS[k]?.s||ITEMS[k]?.n||k)} ${s}`).join(' · ')||'-'}</code></div>
    <button type="button" class="btn sm" data-ar="reset">조정값 처음으로</button><ul class="ar-log">${ARX.log.slice(0,8).map(s=>`<li>${esc(s)}</li>`).join('')}</ul></details>
    ${ARX.ocrErr?'<p class="ar-err">글자 읽기(OCR) 불러오기 실패</p>':''}`;
  arPrev(); }
function arPrev(){ const cv=$('#arPanel .ar-prev'); if(!cv) return; const g=cv.getContext('2d'); g.clearRect(0,0,cv.width,cv.height); const src=ARX.stream?null:ARX.testSrc;
  if(src&&(src.videoWidth||src.width)) g.drawImage(src,0,0,cv.width,cv.height); if(!ARX.cfg.roi) return;
  const fs=Math.max(11,Math.round(cv.width/48)); g.font=`700 ${fs}px system-ui,sans-serif`; g.textBaseline='bottom';
  for(const [k,col,lb] of [['item','#ffb347','아이템 인식 영역'],['banner','#ffe066','획득 배너'],['log','#ff6bd0','획득 로그'],['map','#5ec8ff','미니맵 맵 이름'],['name','#7dff9a','닉네임'],['inv','#c0ff40','인벤토리 메소'],['sto','#40e0ff','창고 메소'],['stoInv','#40e0ff','창고 옆 인벤 메소']]){ const r=arR(k,ARX.video||ARX.testSrc), x=r.x*cv.width, y=r.y*cv.height, w=r.w*cv.width, h=r.h*cv.height; g.strokeStyle=col; g.lineWidth=2; g.strokeRect(x,y,w,h);
    const tw=g.measureText(lb).width+10, ly=y-fs-6<0?y+fs+6:y, lx=Math.min(Math.max(0,x),cv.width-tw); g.fillStyle='rgba(8,10,20,.82)'; g.fillRect(lx,ly-fs-6,tw,fs+6); g.fillStyle=col; g.fillText(lb,lx+5,ly-2); } }
/* b287: 분석 상태 — 분석 fps(배너 감시) · 놓친 프레임(영상 프레임 중 감시 못 한 것) · 바닥 찾기 횟수·건너뜀 · 1회 시간 */
function arPerfText(){ const f=ARX.pf; if(!f||!ARX.video) return '분석 fps - · 놓친 프레임 -'; const s=Math.max(.001,(performance.now()-f.t0)/1000), L=f.last||{watched:0,missed:0,t:f.t0}, ds=Math.max(.001,(performance.now()-L.t)/1000);
  const fps=(f.watched-L.watched)/ds; return `분석 fps <b>${fps.toFixed(0)}</b> · 놓친 프레임 <b>${f.missed}</b>${f.watched?` (${(100*f.missed/(f.watched+f.missed)).toFixed(1)}%)`:''} · 배너 매칭 ${f.banners}회${f.banners?` (${(f.bannerMs/f.banners).toFixed(0)}ms)`:''} · 바닥/공중 ${f.items}회${ARX.itemMs?` (${ARX.itemMs.toFixed(0)}ms)`:''}${f.iskip?` · 건너뜀 ${f.iskip}`:''} · 공중 ${f.air||0}회${f.air?` (${((f.airMs||0)/f.air).toFixed(0)}ms)`:''}${f.airDrop?` · 버린 프레임 ${f.airDrop}`:''}${ARX.airHot?' · <b>full-rate</b>':''}${ARX.wk?'':' · Worker 없음'}`; }
function arPerfPaint(){ const f=ARX.pf; const el=$('#arPanel .ar-perf'); if(el) el.innerHTML=arPerfText(); if(f) f.last={watched:f.watched,missed:f.missed,t:performance.now()}; }
/* 프레임마다 패널 전체를 다시 그리지 않음 (입력·스크롤 유지, 가벼움) — 인식 결과만 */
function arLivePaint(){ const p=$('#arPanel'); if(!p||p.hidden) return; const sig=JSON.stringify([ARX.det,ARX.log[0],ARX.ocrErr,(ARX.amb||[]).length,arLive()]); if(sig===ARX.liveSig) return; ARX.liveSig=sig;
  const open=p.querySelector('details.ar-dbg')?.open, foc=document.activeElement&&p.contains(document.activeElement); if(foc) return; arPanelPaint(); const d=p.querySelector('details.ar-dbg'); if(d&&open) d.open=true; }
/* b294: '보스 득템 자동 기록' 탭 → (연결 안 됐으면) 탭 바로 아래 안내 창 → '확인' 클릭 안에서 바로 getDisplayMedia (사용자 동작). 닫으면 연결 안 함. 이미 연결됐으면 다시 묻지 않음 */
function arGuide(){ if(arLive()) return; let m=$('#arGuide'); if(!m){ m=document.createElement('div'); m.id='arGuide'; m.className='ar-guide'; m.setAttribute('role','dialog'); m.setAttribute('aria-label','게임 화면 연결 안내'); document.body.appendChild(m);
    m.addEventListener('click',e=>{ if(e.target.closest('[data-arg="ok"]')){ m.hidden=true; arConnect(); } else if(e.target.closest('[data-arg="x"]')) m.hidden=true; }); }
  m.innerHTML=`<div class="ar-gh"><b>게임 화면 연결 전에</b><button type="button" class="ar-x" data-arg="x" aria-label="닫기">✕</button></div>
    <ul><li>오른쪽 아래 <b class="ar-pk">획득 로그</b>를 읽어야 하니 파티 목록 등으로 가리지 마세요.</li><li>캐릭터 능력치·장비창·인벤토리 등 <b class="ar-or">아이템 인식</b>을 방해하는 창은 띄우지 마세요.</li></ul>
    <div class="ar-gimg"><img src="data/ar_guide_07.webp" alt="예시: 분홍 = 획득 로그, 주황 = 아이템 떨어지는 곳" width="640" height="360"><img src="data/ar_guide_01.webp" alt="예시 2" width="640" height="360" loading="lazy"></div>
    <small class="muted">분홍 = 획득 로그 · 주황 = 아이템 떨어지는 곳</small><div class="ar-gf"><button type="button" class="btn primary" data-arg="ok">확인</button></div>`;
  const tb=$('#tabs [data-tab="auto"]')?.getBoundingClientRect(); m.hidden=false; if(tb){ const w=Math.min(560,innerWidth-24); m.style.width=w+'px'; m.style.top=Math.round(tb.bottom+8)+'px'; m.style.left=Math.round(Math.max(12,Math.min(innerWidth-w-12,tb.left+tb.width/2-w/2)))+'px'; } }
document.addEventListener('click',e=>{ if(e.target.closest('#tabs [data-tab="auto"]')||e.target.closest('#arPanel [data-ar="guide"]')){ if(!arLive()) setTimeout(arGuide,0); return; }
  const m=$('#arGuide'); if(m&&!m.hidden&&!m.contains(e.target)) m.hidden=true; });
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ const m=$('#arGuide'); if(m) m.hidden=true; } }); // b288: 위쪽 버튼 한 번에 화면 선택 창 (전엔 패널만 열고 패널의 버튼을 또 눌러야 했음)
window.arNameWatch=arNameWatch; window.arNameRes=arNameRes; window.arMesoFlush=arMesoFlush; window.arTarget=arTarget; window.arClrFinish=arClrFinish; window.arMapWatch=arMapWatch; window.arGuide=arGuide; window.renderAuto=renderAuto; window.AR=ARX; window.arFrame=arFrame; window.arBannerWatch=arBannerWatch; window.arLogFrame=arLogFrame; window.arLogStep=arLogStep; window.arStart=arStart; window.arItemScan=arItemScan; window.arTrack=arTrack; window.arMatchCore=arMatchCore; window.arDetectBoss=arDetectBoss; window.arLogItem=arLogItem; window.arOcrLoad=arOcrLoad; arBtnPaint();

/* b297ui: 현재 보스 1줄 고정 — 넘치면 글씨 크기 자동 축소(최소 .8rem) */
function arFitBoss(){requestAnimationFrame(arFitBoss0);arFitBoss0();}
let arFitRO=null;
function arFitBoss0(){const el=document.querySelector('#arPanel .ar-bline');if(!el)return;
  if(!arFitRO&&window.ResizeObserver){arFitRO=new ResizeObserver(()=>arFitBoss0());}
  if(arFitRO&&el.parentElement&&!el.parentElement._ro){el.parentElement._ro=1;arFitRO.observe(el.parentElement);}
  if(!el.clientWidth)return;el.style.fontSize='';
  let f=parseFloat(getComputedStyle(el).fontSize)||22;const min=12.8;
  while(el.scrollWidth>el.clientWidth+1&&f>min){f-=0.5;el.style.fontSize=f+'px';}}
window.addEventListener('resize',()=>{try{arFitBoss()}catch(e){}});
