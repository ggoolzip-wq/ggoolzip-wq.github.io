'use strict';
/* b223: 새로고침(그리고 새로 들어옴·뒤로/앞으로 다시 불러옴)하면 페이지 맨 위에서 시작 — 바로(애니메이션 없음). 브라우저 스크롤 복원 끔(manual),
 * 시작·첫 그리기·load·첫 동기화 끝 때 다시 맨 위. 사용자가 먼저 스크롤·클릭·키를 누르면 그 뒤로는 안 건드림(TOP_PIN 끝). bfcache 복원(persisted)은 그대로 둠 */
let TOP_PIN=true;
function pageTop(force){ if(!TOP_PIN&&!force) return; try{ window.scrollTo({top:0,left:0,behavior:'instant'}); }catch(e){ window.scrollTo(0,0); }
  const se=document.scrollingElement; if(se&&se.scrollTop) se.scrollTop=0; }
try{ if('scrollRestoration' in history) history.scrollRestoration='manual'; }catch(e){}
pageTop();
['wheel','touchstart','keydown','mousedown'].forEach(ev=>window.addEventListener(ev,()=>{ TOP_PIN=false; },{capture:true,passive:true,once:true}));
window.addEventListener('scroll',()=>{ if(TOP_PIN&&(scrollY>0||scrollX>0)&&document.readyState==='complete') TOP_PIN=false; },{passive:true}); // 스크롤바 끌기·코드 스크롤 = 사용자 위치 존중
window.addEventListener('load',()=>{ pageTop(); requestAnimationFrame(()=>pageTop()); setTimeout(()=>{ pageTop(); },400); setTimeout(()=>{ TOP_PIN=false; },8000); });
/* =====================================================================
 *  구글 드라이브 동기화용 OAuth 클라이언트 ID (Google Cloud 콘솔 > Google 인증 플랫폼 > 클라이언트 에서 만든 '웹 애플리케이션' ID)
 *  예: '1234567890-abcdefg.apps.googleusercontent.com'  — 비워 두면 동기화 기능만 '준비 중'으로 표시되고 나머지는 그대로 동작합니다.
 * ===================================================================== */
const GOOGLE_CLIENT_ID = '463037848804-2ut2277bsc2cf4vpf4qb0rl7hlt9ur8c.apps.googleusercontent.com';
/* =====================================================================
 *  설정 상수 (처치 한도 등은 고정값)
 * ===================================================================== */
const CONFIG = {
  STORAGE_KEY: 'mapleBossTracker.v1',
  WEEKLY_BOSS_LIMIT: 12,           // 캐릭터당 주간 보스 처치 제한 (KMS, 작성 시점 기준)
  MONTHLY_BOSS_LIMIT: 1,           // 캐릭터당 월간 보스(검은 마법사) 처치 제한
  MAX_PARTY: 6,
  TZ_OFFSET_HOURS: 9,              // KST
  WEEKLY_RESET_DAY: 4,             // 0=일 ... 4=목 (목요일 00:00 KST)
  API_BASE: 'https://open.api.nexon.com',
  API_DELAY_MS: 250,              // (b107 전) 모든 호출 사이 250ms 간격 — 지금은 아래 키별 초당 제한으로 대체
  API_RATE_N: 4, API_RATE_WIN_MS: 1100 // b112: 5→4 (넥슨 서버 쪽 1초 창에 6건이 몰려 초당 429 나던 것 방지). b107: 키마다 1.1초 안에 최대 5건 시작 (넥슨 개발 단계 키 공식 한도 초당 5건 + 여유). 키가 다르면 동시에
  // (AUTO_SYNC_MIN: 15분마다 자동 동기화 — 2026-10-10 제거. 이제 페이지를 열 때 1회 + 🔄 버튼만)
};

/* 결정석 가격 (단위: 메소)
 * - 공식: 2026-09-17 업데이트 안내 '보스 리워드 개편' 표에 적힌 값 그대로 (검은 마법사는 2026-10-01부터 적용)
 *   https://maplestory.nexon.com/News/Update/813
 * - 공식 표에 없는 8개(kalos/adversary/kaling_extreme, star/limbo/baldrix/bellona/jupiter_hard)는 커뮤니티 추정값. 출처 설명은 README 참고.
 * 사이트의 prices.json(공식 패치 노트, 매일 자동 갱신)으로 덮어써집니다. 직접 수정 기능은 없습니다. */
/* 이전 버전 기본값(설정에 그대로 저장돼 있으면 새 기본값으로 교체) */
const OLD_DEFAULT_PRICES = {kaling_normal:576000000, star_normal:593000000, will_easy:16150000, damien_normal:8760000};
const PRICE_CONFIG = {
  'zakum_chaos':4040000, 'pierre_chaos':4080000, 'vonbon_chaos':4070000, 'queen_chaos':4070000, 'vellum_chaos':4640000,
  'magnus_hard':4280000, 'papulatus_chaos':6550000,
  'lotus_normal':8350000, 'lotus_hard':48900000, 'lotus_extreme':545000000,
  'damien_normal':8750000, 'damien_hard':46400000,
  'slime_normal':12700000, 'slime_chaos':71300000,
  'lucid_easy':14900000, 'lucid_normal':17800000, 'lucid_hard':59700000,
  'will_easy':16100000, 'will_normal':20500000, 'will_hard':73200000,
  'dusk_normal':22000000, 'dusk_chaos':66300000,
  'jinhilla_normal':67600000, 'jinhilla_hard':100000000,
  'dunkel_normal':23700000, 'dunkel_hard':89600000,
  'seren_normal':167000000, 'seren_hard':302000000, 'seren_extreme':1840000000,
  'kalos_easy':238000000, 'kalos_normal':479000000, 'kalos_chaos':1230000000, 'kalos_extreme':4104000000,
  'adversary_easy':261000000, 'adversary_normal':532000000, 'adversary_hard':1390000000, 'adversary_extreme':4712000000,
  'kaling_easy':320000000, 'kaling_normal':593000000, 'kaling_hard':1560000000, 'kaling_extreme':4845000000,
  'star_normal':576000000, 'star_hard':2678000000,
  'limbo_normal':995000000, 'limbo_hard':2385000000,
  'baldrix_normal':1320000000, 'baldrix_hard':3078000000,
  // b252: 익스트림 림보·발드릭스 — 공식 미발표, 사용자 승인 커뮤니티 값 (namu.wiki '강렬한 힘의 결정' + matsu1207.tistory.com/757).
  //   내장값 우선 — 공식 공지 가격이 다르면 boss_auto 가 conflicts 로 기록만 함.
  'limbo_extreme':7500000000, 'baldrix_extreme':9600000000,
  'bellona_easy':396000000, 'bellona_normal':824000000, 'bellona_hard':2950000000,
  'jupiter_normal':1560000000, 'jupiter_hard':5387000000,
  // 월간
  'blackmage_hard':465000000, 'blackmage_extreme':5680000000
};

const D = {easy:'이지',normal:'노말',hard:'하드',chaos:'카오스',extreme:'익스트림'};
// b53: '(난이도)' 굵은 색 글자 — 모든 화면 공통 (캐릭터 정보의 보스 드롭 표는 예외로 예전 표기 유지)
const dlvHtml = d => D[d]?`<span class="dlv dlv-${d}">(${D[d]})</span>`:'';
/* 보스 프리셋. aliases: 넥슨 스케줄러 API 보스명과 매칭할 때 쓰는 이름(공백 무시) */
const BOSSES = [
  {id:'zakum',name:'자쿰',type:'weekly',diffs:['chaos']},
  {id:'pierre',name:'피에르',type:'weekly',diffs:['chaos']},
  {id:'vonbon',name:'반반',type:'weekly',diffs:['chaos']},
  {id:'queen',name:'블러디퀸',type:'weekly',diffs:['chaos']},
  {id:'vellum',name:'벨룸',type:'weekly',diffs:['chaos']},
  {id:'magnus',name:'매그너스',type:'weekly',diffs:['hard']},
  {id:'papulatus',name:'파풀라투스',type:'weekly',diffs:['chaos']},
  {id:'lotus',name:'스우',type:'weekly',diffs:['normal','hard','extreme']},
  {id:'damien',name:'데미안',type:'weekly',diffs:['normal','hard']},
  {id:'slime',name:'가디언 엔젤 슬라임',type:'weekly',diffs:['normal','chaos'],aliases:['가엔슬']},
  {id:'lucid',name:'루시드',type:'weekly',diffs:['easy','normal','hard']},
  {id:'will',name:'윌',type:'weekly',diffs:['easy','normal','hard']},
  {id:'dusk',name:'더스크',type:'weekly',diffs:['normal','chaos'],aliases:['주시자더스크']},
  {id:'jinhilla',name:'진 힐라',type:'weekly',diffs:['normal','hard']},
  {id:'dunkel',name:'듄켈',type:'weekly',diffs:['normal','hard'],aliases:['친위대장듄켈']},
  {id:'seren',name:'선택받은 세렌',type:'weekly',diffs:['normal','hard','extreme'],aliases:['세렌']},
  {id:'kalos',name:'감시자 칼로스',type:'weekly',diffs:['easy','normal','chaos','extreme'],aliases:['칼로스']},
  {id:'adversary',name:'최초의 대적자',type:'weekly',diffs:['easy','normal','hard','extreme'],aliases:['대적자']},
  {id:'kaling',name:'카링',type:'weekly',diffs:['easy','normal','hard','extreme']},
  {id:'star',name:'찬란한 흉성',type:'weekly',diffs:['normal','hard'],aliases:['흉성']},
  {id:'limbo',name:'림보',type:'weekly',diffs:['normal','hard','extreme']},
  {id:'baldrix',name:'발드릭스',type:'weekly',diffs:['normal','hard','extreme']},
  {id:'bellona',name:'벨로나',type:'weekly',diffs:['easy','normal','hard']},
  {id:'jupiter',name:'유피테르',type:'weekly',diffs:['normal','hard']},
  {id:'blackmage',name:'검은 마법사',type:'monthly',diffs:['hard','extreme'],aliases:['검마']}
];
const TYPE_LABEL = {weekly:'주간 보스',monthly:'월간 보스'};
/* 보스 아이콘 = 게임 보스 스케줄러 목록의 보스 아이콘(= UI.wz MobGage 초상화, 원본 25~27px; 출처 MapleStory Wiki 'Mobicon_*.png', 스우 = 1페이즈 파란 눈).
 * b117: 사용자 고른 ④ = 최근접 4배 + 진한 외곽선 + 선명·대비 보정(/workspace/upscale5/mk.py m_outline 그대로) WebP(q92) base64. 없으면 글자 아이콘. */
const BOSS_ICONS = /*__BOSS_ICONS__*/{};
function bossIcon(b){
  const src=BOSS_ICONS[b.id];
  if(src) return `<img class="bicon" src="${src}" alt="" aria-hidden="true">`;
  let h=0; for(const ch of b.id) h=(h*31+ch.charCodeAt(0))%360;
  return `<span class="bicon fb" style="--h:${h}" aria-hidden="true">${esc(b.name.replace(/^(선택받은|감시자|최초의|찬란한)\s*/,'').slice(0,1))}</span>`;
}
/* b115: 보스 초상화 + 왼쪽 위 난이도 네모(E/N/H/C/X). fr = HP바 초상화 테두리(전체 수정·득템왕·메소왕·보스 목록), 이번 주 수익·가격 표는 테두리 없음 */
const bossPic=(b,d,fr=true)=>`<span class="bpic${fr?' bfr':''}">${bossIcon(b)}${diffBadge(d)}</span>`;
const priceKey = (b,diff) => b.id+'_'+diff;

/* 주요 희귀 드롭 (KMS). 출처: 나무위키 '칠흑의 보스 세트' / '여명의 보스 세트' / '광휘의 보스 세트' / '보스 장신구 세트' 문서의
 * 'BOSS REWARD' 표와 각 아이템의 '○○(난이도) 처치 시 드롭' 문구 (2026-10-09 열람). 확인되지 않은 보스(루타비스 등)는 비워 둠.
 * - 블랙 하트는 2025-08-21 패치로 더 이상 드롭되지 않아 제외.
 * 아이콘: maplestory.io (KMS/KMST WZ) 및 MapleStory Wiki(maplestorywiki.net) 'Eqp/Use *.png' 를 32px로 내장. */
const ITEM_ICONS = /*__ITEM_ICONS__*/{};
const ITEMS = {
  lcm:{n:'루즈 컨트롤 머신 마크',set:'칠흑'}, tc:{n:'컴플리트 언더컨트롤',set:'칠흑'}, eye:{n:'마력이 깃든 안대',set:'칠흑'},
  belt:{n:'몽환의 벨트',set:'칠흑'}, book:{n:'저주받은 마도서 선택 상자',set:'칠흑'}, terror:{n:'거대한 공포',set:'칠흑'},
  cfe:{n:'커맨더 포스 이어링',set:'칠흑'}, sos:{n:'고통의 근원',set:'칠흑'}, genesis:{n:'창세의 뱃지',set:'칠흑'},
  mitra:{n:'미트라의 분노 선택 상자',set:'칠흑'}, chaosbox:{n:'혼돈의 칠흑 장신구 상자',set:'칠흑',note:'칠흑 장신구 7종 중 1개 (무작위)'},
  twilight:{n:'트와일라이트 마크',set:'여명'}, estella:{n:'에스텔라 이어링',set:'여명'}, daybreak:{n:'데이브레이크 펜던트',set:'여명'}, gar:{n:'가디언 엔젤 링',set:'여명'},
  whisper:{n:'근원의 속삭임',set:'광휘'}, oath:{n:'죽음의 맹세',set:'광휘'}, bliss:{n:'황홀한 악몽',set:'광휘'},
  sin:{n:'오만의 원죄',set:'광휘'}, spirit:{n:'굶주리는 핏빛 원혼',set:'광휘'}, legacy:{n:'불멸의 유산',set:'광휘'},
  h_face:{n:'익셉셔널 해머 (얼굴장식)',set:'해머'}, h_eye:{n:'익셉셔널 해머 (눈장식)',set:'해머'}, h_belt:{n:'익셉셔널 해머 (벨트)',set:'해머'}, h_ear:{n:'익셉셔널 해머 (귀고리)',set:'해머'},
  moon:{n:'영롱한 달빛 포션',set:'포션'}, // b263: 익스트림 6보스(세렌·칼로스·대적자·카링·림보·발드릭스) 기록 가능 칩, WZ 2023136, 시세 출처 없음(maple.ai.kr 없음) → 수동 입력
  h_pocket:{n:'익셉셔널 해머 (포켓)',set:'해머'}, h_pendant:{n:'익셉셔널 해머 (펜던트)',set:'해머'}, // b252: 공지 815 아이템명 (KMST V1207 id 2644209/2644210) · b254: 아이콘 = 나무위키 림보/발드릭스 문서 게임 아이콘
  // b254: 정보 칩 전용(기록 안 함) — 앱솔랩스/아케인셰이드 무기·방어구 상자 (maplestory.io KMS 389 2633912~2633915)
  ab_w:{n:'앱솔랩스 무기 상자',set:'정보'}, ab_a:{n:'앱솔랩스 방어구 상자',set:'정보'}, ar_w:{n:'아케인셰이드 무기 상자',set:'정보'}, ar_a:{n:'아케인셰이드 방어구 상자',set:'정보'},
  cfs:{n:'응축된 힘의 결정석',set:'보장'}, aquatic:{n:'아쿠아틱 레터 눈장식',set:'보장'}, zbelt:{n:'분노한 자쿰의 벨트',set:'보장'},
  papmark:{n:'파풀라투스 마크',set:'보장'}, wentus:{n:'크리스탈 웬투스 뱃지',set:'보장'}, shoulder:{n:'로얄 블랙메탈 숄더',set:'보장'},
  // 연마석 (특수 스킬 반지 레벨 상승 재료) — 나무위키 각 보스 문서 '보상' · peak.nexon.com/post/1277 · mitemprice.kr (2026-10-10 열람)
  g_life:{n:'생명의 연마석',s:'생명 연마석',set:'연마석'}, g_faith:{n:'신념의 연마석',s:'신념 연마석',set:'연마석'},
  // 소울 에테르 (2026-09-17 소울웨폰 개편으로 추가) — 나무위키 '소울웨폰' · maple.ai.kr 소울웨폰 개편 글
  se1:{n:'1단계 소울 에테르',s:'소울 에테르 1',set:'에테르'}, se2:{n:'2단계 소울 에테르',s:'소울 에테르 2',set:'에테르'},
  se3:{n:'3단계 소울 에테르',s:'소울 에테르 3',set:'에테르'}, se4:{n:'4단계 소울 에테르',s:'소울 에테르 4',set:'에테르'},
  // 특수 스킬 반지 상자 (낮은 확률) — 녹옥(1~3Lv) · 홍옥(1~4Lv) · 흑옥(1~4Lv) · 백옥(3~4Lv) · 생명(3~4Lv, 생명의 연마석 포함)
  r_green:{n:'녹옥의 보스 반지 상자',s:'녹옥 반지 상자',set:'반지',note:'1~3레벨 특수 스킬 반지'},
  r_red:{n:'홍옥의 보스 반지 상자',s:'홍옥 반지 상자',set:'반지',note:'1~4레벨 특수 스킬 반지'},
  // b229: 홍옥 반지 상자에서 나온 리4·컨4 (홍옥 상자 자체는 기록 안 함, 드롭 칩 없음 — 보스 줄 끝 '홍옥 반지 상자로 리4/컨4…' 버튼으로만). 아이콘 = 홍옥 상자 + 반지
  hong_r4:{n:'리스트레인트 링 4레벨 (홍옥 반지 상자)',s:'홍옥 리4',set:'홍옥'}, hong_c4:{n:'컨티뉴어스 링 4레벨 (홍옥 반지 상자)',s:'홍옥 컨4',set:'홍옥'},
  r_black:{n:'흑옥의 보스 반지 상자',s:'흑옥 반지 상자',set:'반지',note:'1~4레벨 특수 스킬 반지'},
  r_white:{n:'백옥의 보스 반지 상자',s:'백옥 반지 상자',set:'반지',note:'3~4레벨 특수 스킬 반지'},
  r_life:{n:'생명의 보스 반지 상자',s:'생명 반지 상자',set:'반지',note:'3~4레벨 특수 스킬 반지 또는 생명의 연마석'},
  // b253: 로이드·소울 조각·에테르넬 방어구 상자 — 나무위키 각 보스 문서 '보상'(2026-10-23 열람) + matsu1207.tistory.com/937(2026-10-16 수정) 두 출처 일치분만.
  //   교환 불가·시세 출처 없음 → 가격 미표시(정렬 맨 뒤, 반지 상자 앞). 아이콘 미확보 → 기본 글자 아이콘. 못 가진 아이템 목록에서는 제외(MISS_SKIP_SET).
  b_kalos:{n:'의지의 에테르넬 방어구 상자',s:'의지의 방어구 상자',set:'방어구'},
  b_adv:{n:'고대의 에테르넬 방어구 상자',s:'고대의 방어구 상자',set:'방어구'},
  b_kaling:{n:'흉수의 에테르넬 방어구 상자',s:'흉수의 방어구 상자',set:'방어구'},
  b_star:{n:'환상의 에테르넬 방어구 상자',s:'환상의 방어구 상자',set:'방어구'},
  b_bellona:{n:'광기의 에테르넬 방어구 상자',s:'광기의 방어구 상자',set:'방어구'},
  b_limbo:{n:'욕망의 에테르넬 방어구 상자',s:'욕망의 방어구 상자',set:'방어구'},
  b_baldrix:{n:'맹세의 에테르넬 방어구 상자',s:'맹세의 방어구 상자',set:'방어구'},
  b_jupiter:{n:'갈망의 에테르넬 방어구 상자',s:'갈망의 방어구 상자',set:'방어구'},
  // b260: 에테르넬 장신망 상자 = 벨로나(광기)·림보(욕망)·발드릭스(맹세)·유피테르(갈망) 하드+ 장갑/신발/망토 상자를 하나로 — 기록 가능, 시세 = maple.ai.kr 에테르넬 장갑·신발·망토 평균(server/worker.js MAI_AVG)
  b_sjm:{n:'에테르넬 장신망 상자',set:'장신망'},
  // 에테르넬 방어구 교환 재료 — 확정 지급, 정보 칩 전용(클릭·기록·수익 없음). ETERNAL 참고
  e_kalos_f:{n:'남겨진 칼로스의 의지 조각',set:'에테르넬'}, e_kalos:{n:'남겨진 칼로스의 의지',set:'에테르넬'},
  e_adv_f:{n:'이어진 고대의 결의 조각',set:'에테르넬'}, e_adv:{n:'이어진 고대의 결의',set:'에테르넬'},
  e_kaling_f:{n:'뒤엉킨 흉수의 고리 조각',set:'에테르넬'}, e_kaling:{n:'뒤엉킨 흉수의 고리',set:'에테르넬'},
  e_star_f:{n:'황홀한 환상의 단편 조각',set:'에테르넬'}, e_star:{n:'황홀한 환상의 단편',set:'에테르넬'},
  e_bellona:{n:'저주받은 원혼의 잔재',set:'에테르넬'}, e_limbo:{n:'왜곡된 욕망의 결정',set:'에테르넬'},
  e_baldrix:{n:'영원한 충성의 흔적',set:'에테르넬'}, e_jupiter:{n:'뒤틀린 갈망의 편린',set:'에테르넬'}
};
// b261: 드롭표 = 보스별 원래 상자(광기·욕망·맹세·갈망, 이름·아이콘·기록 키 그대로) — 시세만 b_sjm(장갑·신발·망토 평균) 공용. 시세 목록엔 b_sjm 1줄
const SJM_BOX={bellona:'b_bellona',limbo:'b_limbo',baldrix:'b_baldrix',jupiter:'b_jupiter'}, SJM_KEYS=new Set(Object.values(SJM_BOX));
/* b261: b260 때 b_sjm 으로 저장된 기록 → 그 기록 보스의 상자 키로 옮김(키 '보스|b_sjm…' + 값 i:'b_sjm'). 보스를 모르면 그대로(장신망 상자로 표시) */
function sjmMigrate(o,d=0){ if(!o||typeof o!=='object'||d>8) return; if(Array.isArray(o)){ o.forEach(x=>sjmMigrate(x,d+1)); return; }
  for(const k of Object.keys(o)){ const m=/^([a-z0-9_]+)\|b_sjm(#.*)?$/.exec(k), bx=m&&SJM_BOX[m[1]], v=o[k];
    if(bx){ const nk=`${m[1]}|${bx}${m[2]||''}`; if(v&&typeof v==='object'&&v.i==='b_sjm') v.i=bx; if(!(nk in o)) o[nk]=v; else if(typeof v==='number'&&typeof o[nk]==='number') o[nk]+=v; delete o[k]; }
    else sjmMigrate(v,d+1); } }
/* 마우스 올림/터치 툴팁에 쓰는 구성품 (2026-10-10).
 * 반지 상자: 넥슨 공식 확률 공개 maplestory.nexon.com/Guide/OtherProbability/bossRingBox/ringBox{Green,Red,Black,White,Life}Jade (2026-10-10 열람)
 *   — 레벨 확률(lv) · 반지별 획득 확률(r = 리스트레인트, c = 컨티뉴어스, %). 4레벨 확률 = 반지 확률 × 4레벨 확률 (반지 종류와 레벨은 따로 정해짐).
 * 혼돈의 칠흑 장신구 상자: 나무위키 '칠흑의 보스 세트' 5.11 (2025-08-21 추가, 미트라·컴플리트 언더컨트롤·창세의 뱃지 제외). */
const RING_TOP=['리스트레인트 링','컨티뉴어스 링','웨폰퍼프-S/I/L/D 링 (4종)','얼티메이덤 링','리스크테이커 링','링 오브 썸','크리데미지 링','크라이시스-HM 링'];
const RING_ALL=[...RING_TOP,'버든리프트 링','오버패스 링','레벨퍼프-S/I/L/D 링 (4종)','헬스컷 링','크리디펜스 링','리밋 링','듀라빌리티 링','리커버디펜스 링','실드스와프 링','마나컷 링','크라이시스-H 링','크라이시스-M 링','크리쉬프트 링','스탠스쉬프트 링','리커버스탠스 링','스위프트 링','리플렉티브 링'];
const BOX_INFO={
  r_green:{lv:'1~3레벨',p:'1레벨 50% · 2레벨 41% · 3레벨 9%',lv4:0,r:2.11268,c:2.11268,n:31,rings:RING_ALL},
  r_red:{lv:'1~4레벨',p:'1레벨 40% · 2레벨 30% · 3레벨 20% · 4레벨 10%',lv4:.10,r:6.92308,c:6.92308,n:31,rings:RING_ALL},
  r_black:{lv:'1~4레벨',p:'1레벨 25% · 2레벨 25% · 3레벨 30% · 4레벨 20%',lv4:.20,r:12.5,c:12.5,n:11,rings:RING_TOP},
  r_white:{lv:'3~4레벨',p:'3레벨 65% · 4레벨 35%',lv4:.35,r:14.28571,c:14.28571,n:11,rings:RING_TOP},
  r_life:{lv:'3~4레벨',p:'3레벨 30% · 4레벨 70%',lv4:.70,r:14.51613,c:14.51613,n:9,rings:RING_TOP.filter(r=>!/얼티메이덤|크라이시스/.test(r)),extra:'또는 생명의 연마석 (14.51613%)'}
};
const fmtPct=v=>v>0?(Math.round(v*100)/100).toFixed(2)+'%':'없음';
// 리스트레인트 링 4레벨(r4) / 컨티뉴어스 링 4레벨(c4) 확률 (%) — 반지 결과 버튼 r4/c4 와 같은 기준
const ring4=k=>{ const b=BOX_INFO[k]; return b?{r4:b.r*b.lv4,c4:b.c*b.lv4,gl:RING_GL[k]||0}:null; };
const RING_GL={r_life:14.51613}; // b122: 생명 상자 → 생명의 연마석 공식 확률(%) (BOX_INFO.r_life.extra)
const CHAOS_BOX=['루즈 컨트롤 머신 마크 (얼굴장식)','마력이 깃든 안대 (눈장식)','몽환의 벨트 (벨트)','저주받은 마도서 선택 상자 (포켓)','거대한 공포 (반지)','커맨더 포스 이어링 (귀고리)','고통의 근원 (펜던트)'];
/* 드롭 칩 툴팁 (2026-10-10 사용자 요청): 반지 상자(녹옥 제외)·혼돈의 칠흑 장신구 상자·에테르넬 칩에만. 그 외 칩(에르다 포함)은 툴팁·title 없음.
 * 반지 상자 = 이름 + '리4: x%' + '컨4: y%' 만 / 칠흑 상자 = 이름 + 구성품. 난이도·'클릭: 획득 +1' 같은 안내 줄 없음. */
function itemTip(k){
  const it=ITEMS[k]; if(!it) return '';
  if(k==='moon') return it.n; // b263: 이름 말풍선
  if(k==='chaosbox') return `${it.n}\n칠흑 장신구 7종 중 1개 (무작위)\n${CHAOS_BOX.map(x=>'· '+x).join('\n')}`;
  const r=BOX_INFO[k]&&BOX_INFO[k].lv4>0?ring4(k):null; // 녹옥(4레벨 없음): 툴팁 없음
  return r?`${it.n}\n리4: ${fmtPct(r.r4)}\n컨4: ${fmtPct(r.c4)}`:'';
}
// 보스별 반지 상자 (정심심 블로그 2026-09-04 정리 · 나무위키 '특수 스킬 반지' · maple.ai.kr 보스 보상과 대조)
const RING_DROPS = {
  r_green:{lotus:['normal'],damien:['normal'],slime:['normal'],lucid:['easy','normal'],will:['easy','normal'],dusk:['normal'],dunkel:['normal']},
  r_red:{lotus:['hard'],damien:['hard'],lucid:['hard'],will:['hard'],jinhilla:['normal']},
  r_black:{dusk:['chaos'],dunkel:['hard'],slime:['chaos'],jinhilla:['hard'],seren:['normal']},
  r_white:{lotus:['extreme'],blackmage:['hard','extreme'],seren:['hard','extreme'],kalos:['easy','normal'],kaling:['easy','normal'],adversary:['easy','normal'],star:['normal'],bellona:['easy','normal']},
  r_life:{kalos:['chaos','extreme'],kaling:['hard','extreme'],limbo:['normal','hard','extreme'],baldrix:['normal','hard','extreme'],adversary:['hard','extreme'],star:['hard'],jupiter:['normal','hard'],bellona:['hard']}
};
const SET_LABEL = {'반지':'특수 스킬 반지 상자 (낮은 확률)','광휘':'광휘의 보스 세트','칠흑':'칠흑의 보스 세트','여명':'여명의 보스 세트','보장':'보스 장신구 세트','해머':'익셉셔널 강화 재료','연마석':'연마석 (특수 스킬 반지 강화 재료)','에테르':'소울 에테르 (소울웨폰 재료)','방어구':'에테르넬 방어구 상자','장신망':'에테르넬 장신망 상자 (장갑·신발·망토)','포션':'소비 아이템'};
const MISS_SKIP_SET=new Set(['방어구','정보']); // b253 · b254: 로이드·소울 삭제, 정보 칩(앱솔/아케인 상자) 제외
// 보스별 [아이템, 드롭 난이도들] — 해당 난이도를 선택했을 때만 표시
const DROPS = {
  // 2026-10-10: 보스 장신구 세트(파풀라투스 마크 제외)·여명의 보스 세트는 드롭 표에서 뺌 (ITEMS 는 남겨 예전 기록은 그대로 표시)
  papulatus:[['papmark',['chaos']]],
  lotus:[['lcm',['hard','extreme']],['tc',['extreme']]],
  damien:[['eye',['hard']]],
  lucid:[['belt',['hard']]],
  will:[['book',['hard']]],
  dusk:[['terror',['chaos']]],
  jinhilla:[['sos',['hard']]],
  dunkel:[['cfe',['hard']]],
  seren:[['mitra',['hard','extreme']],['h_face',['extreme']],['moon',['extreme']]],
  kalos:[['h_eye',['extreme']],['g_life',['normal','chaos','extreme']],['moon',['extreme']]],
  adversary:[['legacy',['hard','extreme']],['g_life',['normal','hard','extreme']],['se1',['normal','hard','extreme']],['moon',['extreme']]],
  kaling:[['chaosbox',['normal','hard','extreme']],['h_ear',['extreme']],['g_life',['normal']],['g_faith',['hard','extreme']],['se1',['normal','hard','extreme']],['moon',['extreme']]],
  star:[['bliss',['hard']],['chaosbox',['normal','hard']],['g_life',['normal']],['g_faith',['hard']],['se2',['normal','hard']]], // b262: b_star(환상의 상자) → INFOBOX 정보 칩
  // b252: 익스트림 — 공지 815(1.2.420)·인벤 322439/322167: 익림 → 익셉셔널 해머 (포켓), 익발 → 익셉셔널 해머 (펜던트). 시세 출처 없음 → 가격 미표시라 맨 뒤(반지 상자 앞).
  //   하드 공통 보상 이월은 namu.wiki 림보/발드릭스 보상 + matsu1207.tistory.com/937 두 출처 일치.
  limbo:[['whisper',['hard','extreme']],['chaosbox',['normal','hard','extreme']],['g_faith',['normal','hard','extreme']],['se3',['normal','hard','extreme']],['h_pocket',['extreme']],['b_limbo',['hard', 'extreme']],['moon',['extreme']]],
  baldrix:[['oath',['hard','extreme']],['chaosbox',['normal','hard','extreme']],['g_faith',['normal','hard','extreme']],['se3',['normal','hard','extreme']],['h_pendant',['extreme']],['b_baldrix',['hard', 'extreme']],['moon',['extreme']]],
  bellona:[['spirit',['hard']],['chaosbox',['normal','hard']],['g_life',['normal']],['g_faith',['hard']],['se2',['normal','hard']],['b_bellona',['hard']]],
  jupiter:[['sin',['hard']],['chaosbox',['normal','hard']],['g_faith',['normal','hard']],['se4',['normal','hard']],['b_jupiter',['hard']]],
  blackmage:[['genesis',['hard','extreme']],['h_belt',['extreme']]]
};
// 2026-10-10: 보스 장신구 세트(파풀라투스 마크 제외)·여명 세트 = 드롭 표 끝에 회색 칩(누를 수 없음, 기록 안 함)
const DROPS_OFF = {zakum:[['cfs',['chaos']],['aquatic',['chaos']],['zbelt',['chaos']]], magnus:[['wentus',['hard']],['shoulder',['hard']]],
  slime:[['gar',['normal','chaos']]], lucid:[['twilight',['normal','hard']]], will:[['twilight',['normal','hard']]], dusk:[['estella',['normal','chaos']]],
  jinhilla:[['daybreak',['normal','hard']]], dunkel:[['estella',['normal','hard']]], seren:[['daybreak',['normal','hard','extreme']]]};
const RING_OFF = new Set(['r_green','r_red']); // b53: 녹옥 반지 상자 = 회색 칩(누를 수 없음, 못 가진 아이템 목록에서도 제외)
const dropsOff = (b,diff) => [...(DROPS_OFF[b.id]||[]).filter(([,ds])=>ds.includes(diff)).map(([k])=>k),
  ...Object.entries(RING_DROPS).filter(([k,m])=>RING_OFF.has(k)&&(m[b.id]||[]).includes(diff)).map(([k])=>k)];
const dropsFor = (b,diff) => [...(DROPS[b.id]||[]).filter(([,ds])=>ds.includes(diff)).map(([k])=>k),
  ...Object.entries(RING_DROPS).filter(([k,m])=>!RING_OFF.has(k)&&(m[b.id]||[]).includes(diff)).map(([k])=>k)];
const DROP_MAX = 99; // (예전: 3개 넘으면 +N 묶음) — 이제 묶지 않고 모두 표시
/* 확정 지급 솔 에르다의 기운 개수 (정보 표시 전용: 클릭·집계·수익 기록 없음).
 * 출처: 나무위키 각 보스 문서 '보상' 표 (namu.moe 미러, 2026-10-10 열람) — 하드 스우부터 지급. 발드릭스·유피테르는 mitemprice.kr 과 대조. */
const ERDA = {
  lotus:{hard:50,extreme:280}, damien:{hard:50}, lucid:{hard:50}, will:{hard:50}, jinhilla:{normal:70,hard:120},
  slime:{chaos:70}, dusk:{chaos:100}, dunkel:{hard:120}, seren:{normal:150,hard:220,extreme:560}, blackmage:{hard:300,extreme:600},
  kalos:{easy:200,normal:250,chaos:400,extreme:700}, adversary:{easy:200,normal:280,hard:450,extreme:750},
  kaling:{easy:200,normal:300,hard:500,extreme:800}, star:{normal:290,hard:590}, limbo:{normal:400,hard:600},
  baldrix:{normal:450,hard:650}, bellona:{easy:200,normal:290,hard:590}, jupiter:{normal:450,hard:750}
};
const erdaFor = (b,diff) => +(ERDA[b?.id]?.[diff])||0;
/* b253: 확정 지급 에리온의 조각 개수 (정보 표시 전용: 클릭·집계·수익 기록 없음, 에르다 칩 옆).
 * 출처 두 곳 일치분만: 나무위키 각 보스 문서 '보상'(2026-10-23 열람) · matsu1207.tistory.com/937 (2026-10-16 수정).
 * 미추가(출처 불일치/단일): 익스트림 카링(나무 480 · matsu 400), 하드 벨로나(matsu 100 단독), 익스트림 림보·발드릭스(두 곳 모두 '?'). */
// b264: 나무위키 아스트라 보조무기(2.1.2.2) 기준 — 카링 EX 480·벨로나 H 90 추가. 림보/발드릭스 EX = 나무위키 '?' → 생략
const ERION = { seren:{extreme:30}, kalos:{extreme:180}, adversary:{hard:30,extreme:240}, kaling:{hard:60,extreme:480}, star:{hard:90}, bellona:{hard:90},
  limbo:{hard:60}, baldrix:{hard:120}, jupiter:{normal:45,hard:360} };
const erionFor = (b,diff) => +(ERION[b?.id]?.[diff])||0;
/* b254: 기록하지 않는 상자 정보 칩 (에리온의 조각 칩 바로 뒤, 에리온이 없는 보스도 같은 자리). 아이콘만 + aria-label · b258: data-tip = 아이템 이름(여명 장신구 off 칩과 같은 말풍선).
 * 에테르넬 방어구 상자: 칼로스·최초의 대적자·카링·흉성(b262)은 기록 안 함(정보), 림보·발드릭스·벨로나·유피테르는 DROPS 에서 기록 그대로.
 * 앱솔랩스 상자: 하드 스우·하드 데미안 (나무위키 '앱솔랩스 세트' + 메이플 보스 보상표 matsu937). 익스트림 스우 = 보상표 '하드 이상'.
 * 아케인셰이드 상자: 하드 루시드·하드 윌·카오스 더스크·노멀/하드 진 힐라·하드 듄켈·하드/익스트림 검은 마법사 (나무위키 '아케인셰이드 세트' + 보상표). */
const AB=['ab_w','ab_a'], AR=['ar_w','ar_a'];
const INFOBOX = { kalos:{chaos:['b_kalos'],extreme:['b_kalos']}, adversary:{hard:['b_adv'],extreme:['b_adv']}, kaling:{hard:['b_kaling'],extreme:['b_kaling']}, star:{hard:['b_star']}, /* b262: 흉성 하드 상자 = 정보 칩 */
  lotus:{hard:AB,extreme:AB}, damien:{hard:AB}, lucid:{hard:AR}, will:{hard:AR}, dusk:{chaos:AR}, jinhilla:{normal:AR,hard:AR}, dunkel:{hard:AR}, blackmage:{hard:AR,extreme:AR} };
const infoBoxFor = (b,diff) => INFOBOX[b?.id]?.[diff]||[];
/* 확정 지급 에테르넬 방어구 교환 재료 (정보 표시 전용: 클릭·집계·수익 기록 없음). [아이템 키, 개수]
 * 출처: 나무위키 '에테르넬 세트' 3. 획득처 표 (namu.moe 미러, 2026-10-10 열람) — 칼로스·대적자·카링·흉성 = 단체 보상, 벨로나·림보·발드릭스·유피테르 = 개인 보상.
 * 이지/노멀의 '○○ 조각'(파편) 2개 = 상위 재료 1개, 상위 재료 10개 = 에테르넬 방어구 1개(부위 선택). 아이콘: maplestory.io(KMST 1170·GMS 270) / 나무위키 파일. */
const E_UP={e_kalos_f:'e_kalos',e_adv_f:'e_adv',e_kaling_f:'e_kaling',e_star_f:'e_star'};
const E_PART={e_kalos:'모자·상의·하의·어깨장식',e_adv:'모자·상의·하의·어깨장식',e_kaling:'모자·상의·하의·어깨장식',e_star:'모자·상의·하의·어깨장식',
  e_bellona:'장갑·신발·망토',e_limbo:'장갑·신발·망토',e_baldrix:'장갑·신발·망토',e_jupiter:'장갑·신발·망토'};
const ETERNAL = {
  kalos:{normal:['e_kalos_f',3],chaos:['e_kalos',5],extreme:['e_kalos',14]},
  adversary:{normal:['e_adv_f',4],hard:['e_adv',6],extreme:['e_adv',16]},
  kaling:{easy:['e_kaling_f',1],normal:['e_kaling_f',5],hard:['e_kaling',7],extreme:['e_kaling',18]},
  star:{normal:['e_star_f',6],hard:['e_star',18]},
  bellona:{normal:['e_bellona',1],hard:['e_bellona',2]}, limbo:{normal:['e_limbo',1],hard:['e_limbo',2],extreme:['e_limbo',5]},
  baldrix:{normal:['e_baldrix',1],hard:['e_baldrix',2]}, jupiter:{normal:['e_jupiter',1],hard:['e_jupiter',2]}  // b252: 발드릭스 익스트림 개수는 matsu937(5개) 단일 출처라 미추가 (namu '?개'); 림보 익스트림 5개는 namu+matsu937 일치
};
const eternalFor = (b,diff) => { const v=ETERNAL[b?.id]?.[diff]; return v?{k:v[0],n:v[1]}:null; };
/* 확정 지급 메멘토 큐브 개수 (정보 표시 전용: 클릭·집계·수익 기록 없음). b=메멘토 수상한 에디셔널(브론즈 에디셔널) 큐브, s=메멘토 실버 큐브, g=메멘토 골드 큐브
 * 단일 기준(b125, 사용자 지정): matsu1207.tistory.com/1173 '보스별 메멘토 큐브 획득량 정리' (수정일 2026-09-14, 보스 리워드 개편 반영; 2026-10-14 재열람).
 * 그 표에 없는 보스·난이도(자쿰, 상위 난이도 등)와 'ㅡ' 칸은 칩 없음.
 * 아이콘(b124): 메멘토 큐브 전용 게임 아이콘 — 아이템 ID 2730034(메멘토 수상한(브론즈) 에디셔널 큐브 200제)·2711032(메멘토 실버 큐브 200제)·2711033(메멘토 골드 큐브 200제),
 *   maplestorywiki.net 'Use Memento … Cube.png' (게임 파일 추출본). 일반 큐브 아이콘 쓰지 말 것. */
const MEMENTO_N={b:'메멘토 수상한 에디셔널 큐브',s:'메멘토 실버 큐브',g:'메멘토 골드 큐브'};
const MEMENTO = {
  magnus:{hard:{b:1}}, pierre:{chaos:{b:1}}, vonbon:{chaos:{b:1}}, queen:{chaos:{b:1}}, vellum:{chaos:{b:1}}, papulatus:{chaos:{b:1}},
  lotus:{normal:{b:3},hard:{b:6}}, damien:{normal:{b:3},hard:{b:6}}, slime:{normal:{b:3},chaos:{b:8,s:1}},
  lucid:{easy:{b:3},normal:{b:5},hard:{b:8,s:1}}, will:{easy:{b:3},normal:{b:5},hard:{b:8,s:1}},
  dusk:{normal:{b:5},chaos:{b:8,s:1}}, dunkel:{normal:{b:5},hard:{b:8,s:1}}, jinhilla:{normal:{b:5},hard:{b:8,s:1}},
  seren:{normal:{b:5,s:2},hard:{b:8,g:2}}, kalos:{easy:{b:8,g:2},normal:{g:3}}, adversary:{easy:{b:8,g:2},normal:{g:3}},
  kaling:{easy:{b:8,g:2},normal:{g:3}}, star:{normal:{g:3}}, bellona:{easy:{g:2}}, blackmage:{hard:{b:24,s:8}}
};
const mementoFor = (b,diff) => MEMENTO[b?.id]?.[diff]||null;
const mementoHtml = m => m?['b','s','g'].filter(t=>m[t]).map(t=>`<span class="drop erda memc mc-${t}" aria-label="${esc(MEMENTO_N[t])} ${m[t]}개">${ITEM_ICONS['mc_'+t]?`<img src="${ITEM_ICONS['mc_'+t]}" alt="" aria-hidden="true">`:`<span class="ifb" aria-hidden="true">${'수실골'['bsg'.indexOf(t)]}</span>`}<b class="ecnt">${m[t]}</b></span>`).join(''):'';
function eternalTip(k,n,diff){
  const up=E_UP[k], main=up||k, it=ITEMS[k], party=['e_bellona','e_limbo','e_baldrix','e_jupiter'].includes(main)?'개인보상':'단체보상';
  return `${it.n} ${n}개 (${party})\n`+(up?`2개 → ${ITEMS[up].n} 1개로 교환\n${ITEMS[up].n} 10개 → `:`10개 → `)+`에테르넬 ${E_PART[main]} 중 1개 선택`;
}
const isHong = k => /^hong_(r4|c4)$/.test(String(k||'').replace(/^x:/,'').replace(/@[wl]$/,'').split('#')[0]);
const hnCls = k => isHong(k)?' vh':''; // b229: 홍옥 리4/컨4 = 아이콘 2개 + xN (이름은 화면에서 숨김, 말풍선·읽기 프로그램용으로만)
function itemIcon(k){
  if(k==='hong_r4'||k==='hong_c4') return `<span class="hongico">${itemIcon('r_red')}${miniIcon(k==='hong_r4'?'ring_restraint':'ring_continuous')}</span>`;
  const it=ITEMS[k], src=ITEM_ICONS[k];
  return src?`<img src="${src}" alt="" width="32" height="32" aria-hidden="true">`:`<span class="ifb" aria-hidden="true">${esc((it?.n||'?').slice(0,1))}</span>`;
}
/* b239: 드롭 칩 가격 등급 (공용 시세 admPriceOf = 수익 기록 칸과 같은 값). 테두리 t-*, 기록하면 같은 등급 채움 f-*, 움직이는 등급 tza.
 * ≥1000억 aur(오로라) · ≥100억 gold(금빛) · ≥10억 pur(보라) · b240: 10억 미만/시세 없음 = 하늘색(sky, 반지 상자와 같음; 초록 등급 삭제).
 * 반지 상자 칩 = 항상 하늘색 테두리(t-sky), 기록하면 결과(리4·컨4) 중 비싼 쪽 가격 등급으로 채움(꽝·미기록 결과 = 채움 없음). 홍옥 반지 상자 버튼(rredBtn)은 예전 그대로(옆 칩과 같은 모양 규칙 zosu-b234 유지). */
const priceTier = p => !(+p>0)?'':p>=1e11?'aur':p>=1e10?'gold':p>=1e9?'pur':''; // b240: 초록 등급 삭제
const tierP = k => +(admPriceOf(priceId(k))?.p)||0;
function tierCls(bd,fill){ if(!bd&&!fill) return ''; const anim=/aur|gold/.test(bd+' '+fill); return ` tz${bd?' t-'+bd:''}${fill?' f-'+fill:''}${anim?' tza':''}`; }
function dropTierCls(c,b,k,got){
  if(isRing(k)){ const outs=(got&&c?(outMap(c,b.type)[b.id+'|'+k]||[]):[]).filter(o=>o==='r4'||o==='c4'); const p=Math.max(0,...outs.map(o=>tierP('ring:'+o))); return tierCls('sky',outs.length?(priceTier(p)||'sky'):''); } // b240: 결과 10억 미만 = 하늘색 채움, 꽝·미기록 = 채움 없음
  const t=priceTier(tierP(k))||'sky'; return tierCls(t,got?t:''); } // b240: 10억 미만·시세 없음 = 하늘색
// b246: 드롭 칩 정렬 가격 = 테두리 등급과 같은 시세(tierP). 반지 상자 = 리4·컨4 확률(ring4, BOX_INFO) × 리4/컨4 시세 기댓값
const dropSortP = k => { if(isRing(k)){ const p=ring4(k); return p?(p.r4/100)*tierP('ring:r4')+(p.c4/100)*tierP('ring:c4'):0; } return tierP(k); };
// b255: 드롭 칩 그룹 = 에르다(이름에 '에르다') 0 → 큐브(이름에 '큐브') 1 → 나머지 2, 그룹 안은 비싼 순(나머지 안에서 반지 상자 맨 끝 b247 유지)
const dropGrp = k => { const n=(ITEMS[k]?.n||'')+' '+(ITEMS[k]?.s||''); return /에르다/.test(n)?0:/큐브/.test(n)?1:2; };
const dropOpen=new Set(); // '+N'을 눌러 펼친 보스 행
function dropsHtml(b,diff,c){
  const ks=dropsFor(b,diff), off=dropsOff(b,diff), en=erdaFor(b,diff); if(!ks.length&&!off.length&&!en&&!erionFor(b,diff)&&!eternalFor(b,diff)&&!mementoFor(b,diff)&&!infoBoxFor(b,diff).length) return '';
  const et=eternalFor(b,diff);
  const eo=erionFor(b,diff);
  const erda=(en?`<span class="drop erda" aria-label="솔 에르다의 기운 ${en}개">${itemIcon('erda')}<b class="ecnt">${en}</b></span>`:'')
    +mementoHtml(mementoFor(b,diff)) // b255: 큐브 정보 칩 = 에르다 다음
    +(et?`<span class="drop erda eter" data-tip="${esc(eternalTip(et.k,et.n,diff))}" aria-label="${esc(ITEMS[et.k].n)} ${et.n}개">${itemIcon(et.k)}<b class="ecnt">${et.n}</b></span>`:'')
    +(eo?`<span class="drop erda erion" data-tip="에리온의 조각" aria-label="에리온의 조각 ${eo}개">${ITEM_ICONS.erion?itemIcon('erion'):'<span class="ifb" aria-hidden="true">에</span>'}<b class="ecnt">${eo}</b></span>`:'')
    +infoBoxFor(b,diff).map(k=>`<span class="drop erda ibox" data-tip="${esc(ITEMS[k].n)}" aria-label="${esc(ITEMS[k].n)} (기록하지 않음)">${itemIcon(k)}</span>`).join('');
  const cnt=k=>c?dropCount(c,b,k):0;
  const chip=k=>{const it=ITEMS[k], n=cnt(k);
    return `<span class="drop s-${it.set} ${n?'got':''}${dropTierCls(c,b,k,n>0)}" ${c?`data-drop="${b.id}|${k}" role="button" tabindex="0"`:''}${(t=>t?` data-tip="${esc(t)}"`:'')(itemTip(k))}>${itemIcon(k)}<span class="dn">${esc(it.s||it.n)}</span></span>`;};
  // 2026-10-10 사용자 요청: 아이템을 '+N' 묶음 칩으로 합치지 않음 — 생명/신념 연마석, 소울 에테르 1~4단계, 반지 상자 모두 각자 칩(각자 아이콘·클릭 +1), 넘치면 다음 줄로
  const shown=ks.map((k,i)=>[k,i,dropSortP(k)]).sort((a,b)=>dropGrp(a[0])-dropGrp(b[0])||(isRing(a[0])-isRing(b[0]))||b[2]-a[2]||a[1]-b[1]).map(a=>a[0]); // b246: 비싼 순(시세 없음 = 뒤, 같으면 원래 순서) · b247: 반지 상자는 항상 맨 끝(상자끼리는 기댓값 순)
  // 아래 줄: 이 보스에서 획득한 아이템 (모든 화면과 같은 형식: 이름(N인 분배) ×개수 결과)
  const mine=c?(d=>({items:Object.fromEntries(Object.entries(d.items).filter(([k])=>k.split('|')[0]===b.id)),outcomes:d.outcomes}))(charDrops(c,b.type)):null;
  const ringLine=mine?itemsInline(mine.items,{outs:mine.outcomes}):'';
  /* b213: 누를 수 없는 칩(기록 안 함) = 모멘텀 큐브(정보 아이콘) 바로 다음, 원래 색 · b214: 솔 에르다·모멘텀 큐브처럼 아이콘만(이름·개수 없음, 말풍선 = 이름) */
  return `<div class="drops open" aria-label="주요 희귀 드롭">${erda}${off.filter(k=>!(k==='r_red'&&c&&b.type==='weekly')).map(k=>`<span class="drop erda off" aria-disabled="true" data-tip="${esc(ITEMS[k].n)}" aria-label="${esc(ITEMS[k].n)} (기록하지 않음)">${itemIcon(k)}</span>`).join('')}${shown.map(chip).join('')}${c&&b.type==='weekly'&&(RING_DROPS.r_red?.[b.id]||[]).includes(diff)?rredBtn(b,c):''}</div>${ringLine?`<div class="ringouts">${ringLine}</div>`:''}`;
}
/* b229: 홍옥 반지 상자로 리4/컨4 — 보스 줄 끝 버튼 → 창(리4/컨4 고르기 + 판매금 + 저장/취소).
 * 저장 = c.drops['보스|hong_r4|hong_c4']=1 (홍옥 상자 r_red 는 기록 안 함 → 상자 수·반지 상자 줄·반상 상위·기댓값 그대로) + c.drev 같은 키 {m,a,p:1,i:'hong_r4'}.
 * 일반 아이템 기록과 같아서 '이번주 획득 아이템' 금액·xN(+1)·주간 기록·득템왕·보스 득템왕·보스 별 누적·주별 득템·판매 누적 수익에 그대로, 일반 반지 상자 리4/컨4 와는 따로 줄.
 * 다시 누르면 취소(드롭 칩처럼). 보스당 이번 주 1번. 분배 없음(입력 = 내 몫) */
const RRED_TXT='홍옥 반지 상자'; /* zosu-hong: 버튼 = 홍옥 상자 아이콘 + 이름 (예전 '…먹었을 경우 클릭'), 옆 아이콘만 칩(r_red off) 삭제 */
const rredGot = (c,slot) => ['hong_r4','hong_c4'].find(k=>+(c?.drops||{})[slot+'|'+k]>0)||'';
function rredBtn(b,c){ const k=rredGot(c,b.id), r=k&&(c.drev||{})[b.id+'|'+k];
  return `<button type="button" class="drop rredbtn${k?' got':''}${tierCls('sky',k?'sky':'')}" data-rred="${b.id}"${k?` data-tip="${esc(`${k==='hong_r4'?'리4':'컨4'}${r&&+r.m>0?` · 판매금 ${meso(+r.m)}`:''} — 다시 누르면 취소`)}"`:''} aria-label="홍옥 반지 상자로 리4/컨4를 먹었을 경우 기록"><span class="rrbico" aria-hidden="true">${itemIcon('r_red')}</span><span class="rrbt">${RRED_TXT}</span></button>`; }
function openRred(slot){
  const c=activeChar(), b=findBoss(slot); if(!c||!b) return; pendStart();
  const had=rredGot(c,slot); if(had){ for(const k of ['hong_r4','hong_c4']){ delete c.drops[slot+'|'+k]; if(c.drev) delete c.drev[slot+'|'+k]; } if(c.drev&&!Object.keys(c.drev).length) delete c.drev; save(); render(); return; } // 기록된 것 다시 누름 = 취소
  document.querySelector('#rredModal')?.remove(); let pick='r4';
  const el=document.createElement('div'); el.id='rredModal'; el.className='modal-bg show'; el.setAttribute('role','dialog'); el.setAttribute('aria-modal','true'); el.setAttribute('aria-labelledby','rrTitle');
  el.innerHTML=`<div class="modal rvbox rrbox"><h3 class="rvh" id="rrTitle"><span class="rrico">${miniIcon('ring_restraint')}${miniIcon('ring_continuous')}</span>홍옥 반지 상자로 리4/컨4를 먹었을 경우</h3>
    <div class="rrnote muted">(홍옥 반지 상자는 카운팅X, 리4/컨4 판매금은 아이템 메소에 편입됩니다)</div>
    <div class="rrpicks" role="radiogroup" aria-label="얻은 반지"><button type="button" class="rrpick on" data-rrpick="r4" role="radio" aria-checked="true" title="${esc(OUT_NAME.r4)}">${miniIcon('ring_restraint')}<span>리4</span></button><button type="button" class="rrpick" data-rrpick="c4" role="radio" aria-checked="false" title="${esc(OUT_NAME.c4)}">${miniIcon('ring_continuous')}<span>컨4</span></button></div>
    <div class="rrbody"><label class="rvin"><input id="rrAmt" type="number" inputmode="decimal" min="0" step="0.01" placeholder="0" aria-label="판매금 (억 메소)"><span>억 메소</span></label>
    <span class="rrbtns"><button class="btn rvok" data-rr="ok">저장</button><button class="btn ghost" data-rr="cancel">취소</button></span></div><div class="rverr" id="rrErr" role="alert"></div></div>`;
  document.body.appendChild(el);
  const close=()=>{ el.remove(); document.removeEventListener('keydown',kd,true); };
  const cancel=()=>{ close(); if(pend&&pendSig(S)===pendSig(pend.base)) pend=null; render(); };
  const ok=()=>{ const v=parseFloat(String($('#rrAmt').value).replace(',','.')); if(!(v>0)||v>100000){ $('#rrErr').textContent='금액을 입력해주세요.'; markEmpty($('#rrAmt')); $('#rrAmt').focus(); return; }
    const cc=S.characters.find(x=>x.id===c.id)||c, key=slot+'|hong_'+pick; dropMap(cc,'weekly')[key]=1; (cc.drev||(cc.drev={}))[key]={m:Math.round(v*1e8),a:Math.round(v*1e4)/1e4,p:1,i:'hong_'+pick}; save(); close(); render(); };
  const kd=e=>{ if(e.key==='Escape'){ e.preventDefault(); e.stopPropagation(); cancel(); } else if(e.key==='Enter'&&e.target.id==='rrAmt'){ e.preventDefault(); ok(); } };
  document.addEventListener('keydown',kd,true);
  el.onclick=e=>{ if(e.target===el) return cancel(); const pk=e.target.closest('[data-rrpick]'); if(pk){ pick=pk.dataset.rrpick; el.querySelectorAll('[data-rrpick]').forEach(x=>{ const on=x===pk; x.classList.toggle('on',on); x.setAttribute('aria-checked',on?'true':'false'); }); return; }
    const t=e.target.closest('[data-rr]'); if(t) t.dataset.rr==='ok'?ok():cancel(); };
  setTimeout(()=>$('#rrAmt')?.focus(),30);
}
/* 파티(2인 이상) 드롭: 블빵승리 / 블빵패배 / 분배 고르기 (결정석 수익은 항상 1/n — 이 선택은 아이템 기록만 바꿈)
 * c.dmode / c.mdmode = {'보스|아이템': 'w'(블빵승리)|'l'(블빵패배)|'s'(분배)} — 없으면 예전 기록(분배와 같게 표시) */
const modeMap = (c,type) => type==='monthly' ? (c.mdmode||(c.mdmode={})) : (c.dmode||(c.dmode={}));
function askBbang(c,b,key,apply,cel,disp){
  const pty=curParty(c,b.id);
  const done=m=>{ apply(); const mm=modeMap(c,b.type); if(m) mm[key]=m; else delete mm[key]; save(); render(); if(m!=='l'&&cel) cel(); };
  if(pty<=1) return done('');
  document.querySelector('#bbModal')?.remove();
  const el=document.createElement('div'); el.id='bbModal'; el.className='modal-bg show cbmodal'; el.setAttribute('role','dialog'); el.setAttribute('aria-modal','true');
  const ik=key.split('|')[1], d=disp||{ico:itemIcon(ik), name:ITEMS[ik]?.n||''}; // 반지 상자·칠흑: 고른 결과/장신구
  el.innerHTML=`<div class="modal cbbox bbbox"><div class="bbico">${d.ico}</div><div class="bbname">${esc(d.name)}</div><div class="cblist">
    <button class="cbopt" data-bb="w">${miniIcon('blink')}<span>블빵승리</span></button>
    <button class="cbopt" data-bb="l"><span class="gray">${miniIcon('blink')}</span><span>블빵패배</span></button>
    <button class="cbopt" data-bb="s">${miniIcon('meso')}<span>분배</span></button></div><button class="btn ghost cbcancel" data-bb="">취소</button></div>`;
  document.body.appendChild(el);
  el.onclick=e=>{ const t=e.target.closest('[data-bb]'); if(!t&&e.target!==el) return; el.remove(); const m=t?t.dataset.bb:'';
    if(!m){ if(pend&&pendSig(S)===pendSig(pend.base)) pend=null; render(); return; }
    done(m); };
}
/* b62-8: 아이템 판매 수익 기록 — 축하 메시지가 나오는 모든 드롭(반지 상자 꽝·블빵패배 제외) 바로 전에 '수익을 기록할까요?'
 * c.drev / c.mdrev = {'보스|아이템': {m: 내 몫 메소(분배면 ÷인원), a: 입력한 억, p: 나눈 인원, i: 실제 아이템 키(반지 결과 'ring:r4'·칠흑 'cb:…' 포함)}}
 * 획득 기록(보스·아이템당 기간 1번)마다 따로 저장 → 주간/월간 기록(perChar.revs)으로 넘어감. 제목 아래 안내 문구대로 사용자가 경매장 최저가 시세를 매번 직접 입력. */
/* b244: 수수료 — 판매 P, 판매 수수료 s → 실수령 Q=P(1-s). N명 분배(분배 수수료 d): 분배자 몫 x, 다른 사람에게 y 보내면 y(1-d) 받음,
 * x=y(1-d), x+(N-1)y=Q → 1인 실수령 = Q(1-d)/(N-d) (메이플로드 보스 분배금 계산기와 같은 식). 1인이면 Q. 마지막 선택 기억(기본 0%). */
const revNet=(p,n,s,d)=>{ const q=p*(1-(s||0)/100); if(!(n>1)) return q; const f=(d||0)/100; return q*(1-f)/(n-f); };
const REVFEE_K='mapleBossTracker.revFee';
function revFeeGet(){ try{ const o=JSON.parse(localStorage.getItem(REVFEE_K)||'{}'); const ok=v=>[0,3,5].includes(v)?v:0; return {s:ok(o.s),d:ok(o.d)}; }catch(e){ return {s:0,d:0}; } }
function revFeeSet(o){ try{ localStorage.setItem(REVFEE_K,JSON.stringify({s:o.s,d:o.d})); }catch(e){} }
const fmtEokP=m=>{ const e=m/1e8; return (e>=100?e.toFixed(1):e>=1?e.toFixed(3):e.toFixed(4)).replace(/\.?0+$/,'')+'억 메소'; };
/* b249: 결과 글자 = '기록 금액 :'(노랑) + 금액(초록) */
const ramHtml=m=>m>0?`<span class="rlab">기록 금액 :</span> <b class="rval">${meso(m)}</b>`:'';
const revMap = (c,type) => type==='monthly' ? (c.mdrev||(c.mdrev={})) : (c.drev||(c.drev={}));
function askRev(c,b,key,ik,cel){
  const pty=curParty(c,b.id), md=modeMap(c,b.type)[key]||'', div=pty>1&&md!=='w'&&md!=='n'?pty:1; // 분배(예전 기록 포함) = ÷인원, 1인·블빵승리 = 전부
  document.querySelector('#revModal')?.remove();
  const fs=revFeeGet(), feeRow=(k,lab)=>`<div class="rvfrow" data-frow="${k}"><span class="rvflab">${lab} :</span>${[0,3,5].map(v=>`<button type="button" class="rvfbtn${fs[k]===v?' on':''}" data-fee="${k}" data-v="${v}" aria-pressed="${fs[k]===v}">${v}%</button>`).join('')}</div>`;
  const feeHtml=`<div class="rvfee">${feeRow('s','판매 수수료')}${div>1?feeRow('d','분배 수수료'):''}<div class="rvprev" id="rvPrev"></div></div>`; // b244: 1인 = 판매만, 2인 이상 분배 = 판매+분배
  const ap=admPriceOf(ik); // b104: 관리자만 — maple.ai.kr 시세로 미리 채움 (수정 가능)
  const el=document.createElement('div'); el.id='revModal'; el.className='modal-bg show'; el.setAttribute('role','dialog'); el.setAttribute('aria-modal','true'); el.setAttribute('aria-labelledby','rvTitle');
  el.innerHTML=`<div class="modal rvbox"><h3 class="rvh" id="rvTitle"><span class="rvico">${lootIco(ik)}</span>수익을 기록할까요?</h3><div class="rvguide muted" id="rvGuide">${ap?`가격 확인 : ${kstStamp(ap.t)}`:'이 아이템의 경매장 최저가 시세를 적어주세요.'}</div>${ap?priceSrcHtml('rvguide rvsrc muted'):''}${div>1?`<div class="rvname muted">${div}인 분배 · 수수료 반영 1인 실수령</div>`:''}
    <div class="rvbody"><div class="rvleft"><div class="rvamtrow"><small class="ram rvram" id="rvRam" aria-live="polite"></small><label class="rvin"><input id="rvAmt" type="number" inputmode="decimal" min="0" step="0.01" placeholder="0" aria-label="판매 금액 (억 메소)"${ap?` value="${Math.round(ap.p/1e4)/1e4}"`:''}><span>억 메소</span></label></div>${feeHtml}<span class="rvbtns rvrow1"><button class="btn rvok" data-rv="ok">기록하기</button><button class="btn plain rvno" data-rv="no">기록 없이 저장</button></span><span class="rvbtns rvrow2"><button class="btn ghost rvcancel" data-rv="cancel">취소</button></span></div></div><div class="rverr" id="rvErr" role="alert"></div></div>`;
  document.body.appendChild(el);
  let closed=false; const fin=()=>{ if(closed) return; closed=true; el.remove(); document.removeEventListener('keydown',kd,true); if(cel) cel(); };
  const ok=()=>{ const v=parseFloat(String($('#rvAmt').value).replace(',','.')); if(!(v>0)||v>100000){ $('#rvErr').textContent='금액을 입력해주세요.'; markEmpty($('#rvAmt')); $('#rvAmt').focus(); return; }
    const cc=S.characters.find(x=>x.id===c.id)||c; const ds=div>1?fs.d:0; revMap(cc,b.type)[key]={m:Math.round(revNet(v*1e8,div,fs.s,ds)),a:Math.round(v*1e4)/1e4,p:div,i:ik,fs:fs.s,fd:ds}; revFeeSet(fs); save(); render(); fin(); };
  // b109: 오른쪽 [기록하기](주황) = 금액 기록 / [기록 없이 저장](예전 '아니오') = 획득은 남기고 수익 기록 없이 축하 / [취소](예전 '취소하기') = 아래 undo
  // zosu-ui: [취소하기] = 이 창을 띄운 아이템 선택 자체를 되돌림(획득·블빵/분배·반지/칠흑 결과·수익 기록 삭제, 축하 없음) — changeDrop 의 취소와 같은 정리
  const undo=()=>{ if(closed) return; closed=true; el.remove(); document.removeEventListener('keydown',kd,true);
    const cc=S.characters.find(x=>x.id===c.id)||c, t=b.type; delete dropMap(cc,t)[key]; delete modeMap(cc,t)[key]; delete outMap(cc,t)[key];
    const rk=t==='monthly'?'mdrev':'drev', rm=cc[rk]; if(rm){ delete rm[key]; if(!Object.keys(rm).length) delete cc[rk]; }
    if(pend&&pendSig(S)===pendSig(pend.base)) pend=null; save(); render(); };
  const prev=()=>{ const v=parseFloat(String($('#rvAmt').value).replace(',','.')), pv=$('#rvPrev'), rr=$('#rvRam'); if(rr) rr.innerHTML=v>0&&v<=100000?ramHtml(Math.round(revNet(v*1e8,div,fs.s,div>1?fs.d:0))):''; /* b248: 입력 = 판매가 그대로, 왼쪽 작은 글자 = 수수료 반영 결과 */ if(pv) pv.innerHTML=v>0&&v<=100000?`기록 금액 : <b>${fmtEokP(revNet(v*1e8,div,fs.s,div>1?fs.d:0))}</b>${div>1?' (1인)':''}`:''; };
  $('#rvAmt').addEventListener('input',prev); prev();
  const kd=e=>{ if(e.key==='Escape'){ e.preventDefault(); e.stopPropagation(); fin(); } else if(e.key==='Enter'&&e.target.id==='rvAmt'){ e.preventDefault(); ok(); } };
  document.addEventListener('keydown',kd,true);
  el.onclick=e=>{ if(e.target===el) return undo(); const f=e.target.closest('[data-fee]'); if(f){ fs[f.dataset.fee]=+f.dataset.v; el.querySelectorAll(`[data-fee="${f.dataset.fee}"]`).forEach(x=>{const on=x===f; x.classList.toggle('on',on); x.setAttribute('aria-pressed',on);}); prev(); return; } const t=e.target.closest('[data-rv]'); if(t) return t.dataset.rv==='ok'?ok():t.dataset.rv==='cancel'?undo():fin(); }; // b110: 바깥(배경) 클릭 = [취소] (체크 되돌림)
  setTimeout(()=>{ const i=$('#rvAmt'); if(i){ i.focus(); if(ap) i.select(); } },30);
}
/* b110: 아이템 이름 옆에 그 아이템을 준 보스 아이콘 = 공통 bossIcon() (보스 아이콘을 바꾸면 여기도 같이 바뀜)
 * b109: '수익 기록 전체 수정' — 이 캐릭터가 이번 주/이번 달 체크한 아이템 전부(수익 기록 안 한 것 포함, 블빵패배·반지 상자 꽝 제외 = 수익이 없음)를
 * 한 창에서 고침. 금액 = 억 메소, **내 몫(분배 후 실제 합산 값)** 을 보여 주고 그대로 저장(b110 — 예전엔 총액을 보여 주고 다시 ÷인원). 빈 칸 = 그 아이템 수익 기록 없음(지움). [전체 수정] = 바로 확정(저장 대기·[저장] 없이) →
 * c.drev/c.mdrev 가 이번 주 수익·수익 분석·득템 분석·주간 기록 넘김에 모두 쓰이므로 모든 표에 반영. 지난 주(history) 기록은 건드리지 않음 */
/* b247: 기록 값 m 에서 원래 판매가 P 되돌리기 — b244 식의 역(기록에 남은 p·fs·fd, 예전 기록은 수수료 0 = a 그대로) */
const revGross=(m,n,s,d)=>{ const f=(d||0)/100, q=n>1?m*(n-f)/(1-f):m; return q/(1-(s||0)/100); };
// a(입력한 억 = 판매가, b110 전체 수정도 총액) 가 기록 m 과 맞으면 a 그대로(반올림 손실 없음), 아니면 m 에서 역산
const revGrossOf=r=>{ const m=+r.m, n=+r.p||1, s=+r.fs||0, d=n>1?+r.fd||0:0, a=+r.a*1e8; return a>0&&Math.abs(revNet(a,n,s,d)-m)<2e4?a:revGross(m,n,s,d); };
function revAllRows(c){ const rows=[];
  for(const t of ['weekly','monthly']) for(const [key,n] of Object.entries(dropMap(c,t)||{})){ if(!(+n>0)) continue;
    const [slot,it]=key.split('|'), b=findBoss(slot); if(!b||!ITEMS[it]) continue; const md=modeMap(c,t)[key]||'', outs=outMap(c,t)[key]||[], last=outs[outs.length-1];
    if(md==='l'||last==='x') continue;
    const r=revMap(c,t)[key], ik=r?.i||(last==='r4'||last==='c4'?'ring:'+last:last==='gl'?'g_life':/^cb:/.test(last||'')?last:it);
    const pty=curParty(c,slot), div=pty>1&&md!=='w'&&md!=='n'?pty:1; rows.push({t,key,b,ik,div,m:r&&+r.m>0?+r.m:0,fs:+r?.fs||0,fd:div>1?+r?.fd||0:0,g:r&&+r.m>0?revGrossOf(r):0}); const x=rows[rows.length-1]; x.a=x.g>0?String(Math.round(x.g/1e4)/1e4):''; } // b248: 칸 = 판매가(총액, a 없으면 revGrossOf 역산), 왼쪽 = 결과 m · b110: 칸 = 내 몫(분배 후, 실제로 합산되는 값) 억 단위
  return rows; }
/* b112: 같은 보스 기록(주간/월간·보스)끼리 묶음 — 보스 초상화 1번 + 그 보스 아이템 줄들. 입력 번호(i)는 rows 순서 그대로 */
function raGroups(c,rows){ const G=[]; rows.forEach((x,i)=>{ let g=G.find(y=>y.t===x.t&&y.b===x.b); if(!g) G.push(g={t:x.t,b:x.b,d:c.bosses?.[x.b.id]?.diff||'',items:[]}); g.items.push([x,i]); }); return G; }
// b112: 보스 아이콘 왼쪽 위 난이도 배지 — 이지 E 파랑 · 노말 N 연두 · 하드 H 빨강 · 카오스 C 검정 · 익스트림 X 보라(사용자 미지정 → 다른 색)
const DIFF_BADGE={easy:'E',normal:'N',hard:'H',chaos:'C',extreme:'EX'}; /* b115: 익스트림 = 검정 네모 + 빨간 EX */
const diffBadge=d=>DIFF_BADGE[d]?`<span class="dbadge db-${d}" data-d="${DIFF_BADGE[d]}" aria-hidden="true"></span>`:''; /* b115: 글자는 ::before (본문 글자에 안 섞이게) */
function openRevAll(){
  const c=activeChar(); if(!c) return; document.querySelector('#revAllModal')?.remove(); const rows=revAllRows(c);
  const el=document.createElement('div'); el.id='revAllModal'; el.className='modal-bg show'; el.setAttribute('role','dialog'); el.setAttribute('aria-modal','true'); el.setAttribute('aria-labelledby','raTitle');
  el.innerHTML=`<div class="modal rabox"><h3 id="raTitle">수익 기록 전체 수정</h3>
    <div class="raicons">${rows.filter((x,i)=>rows.findIndex(y=>icoId(y.ik)===icoId(x.ik))===i).map(x=>`<span class="raic" title="${esc(lootName(x.ik))}">${lootIco(x.ik)}</span>`).join('')||'<span class="muted">이번 주·이번 달 체크한 아이템이 없습니다.</span>'}</div>
    ${rows.some(x=>x.m>0)?(()=>{ const rec=rows.filter(x=>x.m>0), cm=k=>{ const v=rec.map(x=>x[k]); return v.every(y=>y===v[0])?v[0]:-1; }, sp=rec.some(x=>x.div>1), cs=cm('fs'), cd=sp?cm('fd'):-1;
      const fr=(k,lab,cv)=>`<div class="rvfrow" data-rafrow="${k}"><span class="rvflab">${lab} :</span>${[0,3,5].map(v=>`<button type="button" class="rvfbtn${cv===v?' on':''}" data-rafee="${k}" data-v="${v}" aria-pressed="${cv===v}">${v}%</button>`).join('')}</div>`;
      return `<div class="rvfee rafee" aria-label="수수료 전체 적용"><div class="rafh muted">수수료 전체 적용</div>${fr('s','판매 수수료',cs)}${sp?fr('d','분배 수수료',cd):''}</div>`; })():'' /* b247: 기록 전부 1인(분배 없음) = 판매만 */}
    <div class="ralist">${raGroups(c,rows).map(g=>`<div class="ragrp"><span class="rabi" data-boss="${g.b.id}" title="${esc(g.b.name)}${g.d?' '+esc(D[g.d]||''):''}">${bossPic(g.b,g.d)}</span><div class="ragi">${g.items.map(([x,i])=>`<div class="rarow"><span class="raic">${lootIco(x.ik)}</span><span class="raname">${isHong(x.ik)?`<span class="vh">${esc(lootName(x.ik))}</span><b class="lx">x1</b>`:esc(lootName(x.ik))}${x.div>1?` <small class="muted">(${x.div}인 분배)</small>`:''}<small class="ram" data-ram="${i}">${ramHtml(x.m)}</small></span><label class="rvin rain"><input type="number" inputmode="decimal" min="0" step="0.01" placeholder="0" data-ra="${i}" value="${x.a}" aria-label="${esc(lootName(x.ik))} 판매 금액 (억 메소)"><span>억 메소</span></label></div>`).join('')}</div></div>`).join('')}</div>
    <div class="rverr" id="raErr" role="alert"></div>
    <div class="rabtns">${rows.length?'<button class="btn raok" data-rab="ok">전체 수정</button><button class="btn ghost" data-rab="cancel">취소</button>':'<button class="btn raok" data-rab="close">확인</button>' /* b206: 체크한 아이템 없음 → [확인] 하나, 누르면 닫기만 */}</div></div>`;
  document.body.appendChild(el);
  const close=()=>{ el.remove(); document.removeEventListener('keydown',kd,true); };
  // b248: 오른쪽 칸 = 판매가(그대로), 수수료 버튼·입력 = 왼쪽 결과 글자만 다시 계산
  const rf=rows.map(x=>({s:x.fs,d:x.fd})), fee={s:-1,d:-1}; el.querySelectorAll('[data-rafee].on').forEach(b=>{ fee[b.dataset.rafee]=+b.dataset.v; });
  const gOf=i=>{ const inp=el.querySelector(`[data-ra="${i}"]`), raw=String(inp?.value??'').trim(), v=parseFloat(raw.replace(',','.')); return raw===rows[i].a&&rows[i].g>0?rows[i].g:v>0&&v<=100000?v*1e8:0; };
  const mOf=i=>{ const g=gOf(i), x=rows[i]; return g>0?Math.round(revNet(g,x.div,rf[i].s,x.div>1?rf[i].d:0)):0; };
  const showM=i=>{ const o=el.querySelector(`[data-ram="${i}"]`); if(o) o.innerHTML=ramHtml(mOf(i)); };
  const feeAll=(k,v)=>{ fee[k]=v; el.querySelectorAll(`[data-rafee="${k}"]`).forEach(b=>{ const on=+b.dataset.v===v; b.classList.toggle('on',on); b.setAttribute('aria-pressed',on); });
    rows.forEach((x,i)=>{ if(k==='d'&&!(x.div>1)) return; rf[i][k]=v; showM(i); }); };
  const ok=()=>{ const vals=[]; for(const inp of el.querySelectorAll('[data-ra]')){ const s=String(inp.value).trim().replace(',','.'), v=s===''?0:parseFloat(s);
      if(!(v>=0)||v>100000){ $('#raErr').textContent='금액을 확인해주세요.'; markEmpty(inp); inp.focus(); return; } vals[+inp.dataset.ra]=v; } // b112: 보스별 묶음이라 화면 순서 ≠ rows 순서 → 번호로
    // b110: 입력 = 내 몫 그대로 저장(다시 나누지 않음). 안 바꾼 칸은 원래 값 그대로(반올림 손실 없음)
    const raw=[]; el.querySelectorAll('[data-ra]').forEach(i=>{ raw[+i.dataset.ra]=String(i.value).trim(); });
    const apply=cc=>{ if(!cc) return; rows.forEach((x,i)=>{ const v=vals[i], rm=revMap(cc,x.t);
      const s=rf[i].s, d=x.div>1?rf[i].d:0; if(raw[i]===x.a&&x.m>0&&s===x.fs&&d===x.fd) return; // 안 바꾼 줄 = 그대로
      const g=raw[i]===x.a&&x.g>0?x.g:v*1e8; // b248: 판매가 a + fs/fd + 결과 m 저장
      if(v>0) rm[x.key]={m:Math.round(revNet(g,x.div,s,d)),a:Math.round(g/1e4)/1e4,p:x.div,i:x.ik,fs:s,fd:d}; else delete rm[x.key];
      const rk=x.t==='monthly'?'mdrev':'drev'; if(cc[rk]&&!Object.keys(cc[rk]).length) delete cc[rk]; }); };
    apply(S.characters.find(x=>x.id===c.id)); if(pend) apply(pend.base?.characters?.find(x=>x.id===c.id)); // 저장 대기 중인 다른 변경과 섞이지 않게 기준 상태에도 같이
    save(); try{ svPushBg(); }catch(e){} close(); render(); };
  const kd=e=>{ if(e.key==='Escape'){ e.preventDefault(); e.stopPropagation(); close(); } else if(e.key==='Enter'&&e.target.dataset?.ra!=null){ e.preventDefault(); ok(); } };
  document.addEventListener('keydown',kd,true);
  el.addEventListener('input',e=>{ const i=e.target.dataset?.ra; if(i==null) return; showM(+i); });
  el.onclick=e=>{ if(e.target===el) return close(); const f=e.target.closest('[data-rafee]'); if(f) return feeAll(f.dataset.rafee,+f.dataset.v); const t=e.target.closest('[data-rab]'); if(t) t.dataset.rab==='ok'&&rows.length?ok():close(); }; // b110: 바깥 클릭 = [취소]
  setTimeout(()=>(el.querySelector('[data-ra]')||el.querySelector('[data-rab]'))?.focus(),30);
}
function changeDrop(key, delta){
  const c=activeChar(); if(!c) return; const [slot,item]=key.split('|'); const b=findBoss(slot); if(!b||!ITEMS[item]) return;
  if(delta>0 && (+dropMap(c,b.type)[key]||0)>=1) delta=-1; // 보스·아이템당 기간에 1번만: 이미 획득 → 다시 누르면 취소
  pendStart();
  if(delta>0 && item==='chaosbox'){ openChaos(key); return; } // 칠흑 장신구 상자: 어떤 장신구인지 고른 뒤 +1
  if(delta>0 && isRing(item)){ openRing(key); return; } // 반지 상자는 결과를 고른 뒤 +1
  const m=dropMap(c,b.type);
  if(delta>0){ askBbang(c,b,key,()=>{ m[key]=1; },()=>askRev(c,b,key,item,()=>celebrate(null,item,b))); return; }
  const n=0; delete m[key]; delete modeMap(c,b.type)[key]; { const rm=c[b.type==='monthly'?'mdrev':'drev']; if(rm){ delete rm[key]; if(!Object.keys(rm).length) delete c[b.type==='monthly'?'mdrev':'drev']; } } // 빈 {} 를 남기면 [취소]/[저장] 비교가 어긋남
  if(delta<0 && hasOut(item)){ const om=outMap(c,b.type); const l=om[key]; if(l&&l.length) l.pop(); if(!n||(l&&!l.length)) delete om[key]; } // 가장 최근 획득(결과 포함) 취소
  save(); render();
  // (선택/취소 알림 문구 없음 — 2026-10-10)
}
/* 반지 상자 결과 선택 모달 (닫기 = 기록 안 함) */
let ringPending=null;
function openRing(key){
  const c=activeChar(); const [slot,item]=key.split('|'); const b=findBoss(slot); if(!c||!b) return;
  ringPending={cid:c.id,key};
  const diff=c.bosses[slot]?.diff;
  $('#ringBoxIcon').innerHTML=itemIcon(item); $('#ringTitle').textContent=`${ITEMS[item].n} 획득!`;
  const pty=curParty(c,slot);
  $('#ringSub').innerHTML=`${esc(c.name)} · ${esc(b.name)}${diff?` ${dlvHtml(diff)}`:''}${pty>1?` · ${pty}인 분배`:''} — 상자에서 무엇이 나왔나요?`;
  { const g=document.querySelector('#ringModal [data-ring="gl"]'); if(g) g.hidden=item!=='r_life'; const xb=document.querySelector('#ringModal [data-ring="x"] b'); if(xb) xb.textContent=item==='r_life'?'셋 다 못 먹었어요':'둘 다 못 먹었어요'; }
  $('#ringModal').classList.add('show'); setTimeout(()=>document.querySelector('#ringModal [data-ring="r4"]')?.focus(),30);
}
function closeRing(){ ringPending=null; $('#ringModal').classList.remove('show'); if(pend&&pendSig(S)===pendSig(pend.base)){ pend=null; render(); } } // b110: 닫기(✕·바깥·Esc) = 취소 — 바뀐 게 없으면 저장 대기도 풂
function chooseRing(o){
  const p=ringPending; if(!p||!(o in OUT_LABEL)) return; closeRing();
  const c=S.characters.find(x=>x.id===p.cid); if(!c) return; const [slot,item]=p.key.split('|'); const b=findBoss(slot);
  pendStart(); const m=dropMap(c,b.type);
  if(o==='x'){ m[p.key]=1; const om=outMap(c,b.type); (om[p.key]||(om[p.key]=[])).push('x'); modeMap(c,b.type)[p.key]='n'; save(); render(); return; } // 꽝: 블빵 창 없이 1인처럼 (라벨 없음)
  m[p.key]=1; (outMap(c,b.type)[p.key]||(outMap(c,b.type)[p.key]=[])).push(o); if(curParty(c,b.id)>1) modeMap(c,b.type)[p.key]='s'; save(); render(); // 반지 상자: 블빵 창 없이 항상 분배
  askRev(c,b,p.key,o==='gl'?'g_life':'ring:'+o,()=>{ if(o==='gl') celebrate(null,'g_life',b); else celebrate(o,null,b); }); return;
  askBbang(c,b,p.key,()=>{},()=>{},
    o==='gl'?{ico:itemIcon('g_life'),name:ITEMS.g_life.n}:o==='x'?{ico:itemIcon(item),name:ITEMS[item].n+' · 꽝'}:{ico:outIcon(o),name:OUT_NAME[o]});
}
/* 축하 연출: 캔버스 불꽃놀이 + 꽃가루 (~2.6초, 외부 라이브러리 없음) */
// 아이콘 불꽃: 같은 아이콘 수십 개가 가운데서 사방으로 (CSS transform, 약 2초 후 제거, 모션 줄이기 존중)
function iconBurst(src){
  document.querySelector('#iconBurst')?.remove(); if(!src||matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const box=document.createElement('div'); box.id='iconBurst'; box.setAttribute('aria-hidden','true');
  const N=42; let h='';
  for(let i=0;i<N;i++){ const a=Math.PI*2*(i/N)+Math.random()*.3, d=160+Math.random()*320, x=Math.cos(a)*d, y=Math.sin(a)*d+60, r=(Math.random()*2-1)*540, sc=.6+Math.random()*.8, dl=(i%3)*90;
    h+=`<img src="${src}" style="--x:${x.toFixed(0)}px;--y:${y.toFixed(0)}px;--r:${r.toFixed(0)}deg;--s:${sc.toFixed(2)};animation-delay:${dl}ms">`; }
  box.innerHTML=h; document.body.appendChild(box); setTimeout(()=>box.remove(),2100);
}
// 이모지: 글꼴에 컬러 이모지가 없는 PC(예: PC방 윈도우)에서도 보이게 Twemoji 이미지(CC-BY 4.0)로, alt 에 글자
const CG_EMOJI=[['😚','1f61a'],['😙','1f619'],['😊','1f60a'],['😘','1f618'],['🥳','1f973']];
const cgEmoji = () => { const [ch,cp]=CG_EMOJI[Math.random()*CG_EMOJI.length|0]; return `<img class="cg-emo" src="${ITEM_ICONS['emo_'+cp]}" alt="${ch}" data-emo="${ch}" draggable="false">`; };
/* b246: 에픽 빛줄기 = 4x4 스프라이트(1152x689 프레임 16장, ESPCN x2 업스케일+언샤프) 를 캔버스에 69ms 마다 — 창이 열릴 때마다 0번 프레임부터(animated WebP 는 캐시되면 중간부터 재생됨). 페이지 로드 때 미리 받아 디코드 */
const BEAM={src:'epicbeam_sprite.webp',w:1152,h:689,cols:4,n:16,ms:69};
const beamImg=new Image(); beamImg.src=BEAM.src; beamImg.decode?.().catch(()=>{});
function beamDraw(cv,f){ const g=cv.getContext('2d'); g.clearRect(0,0,BEAM.w,BEAM.h); if(beamImg.complete&&beamImg.naturalWidth) g.drawImage(beamImg,(f%BEAM.cols)*BEAM.w,(f/BEAM.cols|0)*BEAM.h,BEAM.w,BEAM.h,0,0,BEAM.w,BEAM.h); celebrate.beamFrame=f; }
function beamPlay(cv){ if(!cv) return; const id=(beamPlay._id=(beamPlay._id||0)+1);
  if(matchMedia('(prefers-reduced-motion: reduce)').matches){ celebrate.beamFrame=-1; return; }
  const t0=performance.now(); beamDraw(cv,0); let last=0;
  const tick=now=>{ if(id!==beamPlay._id||!celebrate.running||!cv.isConnected) return; const f=Math.max(0,Math.floor((now-t0)/BEAM.ms))%BEAM.n; if(f!==last){ last=f; beamDraw(cv,f); } requestAnimationFrame(tick); };
  if(!beamImg.complete) beamImg.addEventListener('load',()=>{ if(id===beamPlay._id) beamDraw(cv,last); },{once:true});
  requestAnimationFrame(tick); }
function celebrate(o,item,boss){
  const cv=$('#fx'), msg=$('#congrats');
  msg.innerHTML=`<div class="cg-in"><span class="cg-ico"><canvas class="cg-beam" width="1152" height="689" aria-hidden="true"></canvas>${item?itemIcon(item):o==='r4'?miniIcon('ring_restraint'):miniIcon('ring_continuous')}</span><div class="cg-big">${boss?`<span class="cg-boss">${bossIcon(boss)}</span>`:''}<span class="cg-t">축하드립니다!</span></div><div class="cg-sub">${item?ITEMS[item].n:OUT_NAME[o]} 획득</div></div>`;
  beamPlay(msg.querySelector('.cg-beam'));
  const img=null; iconBurst(ITEM_ICONS[item||(o==='r4'?'ring_restraint':'ring_continuous')]);
  msg.classList.add('show'); cv.classList.add('show'); celebrate.running=true;
  clearTimeout(celebrate._t); celebrate._t=setTimeout(endCelebrate,2200);
  if(matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const dpr=Math.min(2,devicePixelRatio||1), W=innerWidth, H=innerHeight; cv.width=W*dpr; cv.height=H*dpr; const g=cv.getContext('2d'); g.setTransform(dpr,0,0,dpr,0,0);
  const P=[], COL=['#ff5a5f','#ffb400','#4ecdc4','#a66cff','#ffe66d','#ff8fab','#7bdff2','#9be84a'];
  const burst=(x,y)=>{ const n=70, col=COL[Math.random()*COL.length|0]; for(let i=0;i<n;i++){ const a=Math.PI*2*i/n, v=2+Math.random()*4; P.push({x,y,vx:Math.cos(a)*v,vy:Math.sin(a)*v,life:1,dec:.012+Math.random()*.012,r:2+Math.random()*1.5,col:Math.random()<.3?COL[Math.random()*COL.length|0]:col,k:'s'}); }};
  for(let i=0;i<90;i++) P.push({x:Math.random()*W,y:-20-Math.random()*H*.5,vx:(Math.random()-.5)*2,vy:2+Math.random()*3,life:1,dec:.004,r:4+Math.random()*4,col:COL[i%COL.length],k:'c',rot:Math.random()*6,vr:(Math.random()-.5)*.3});
  const t0=performance.now(); let nb=0;
  const step=now=>{ if(!celebrate.running) return; const t=now-t0;
    while(nb<6 && t>nb*320){ burst(W*(.18+Math.random()*.64), H*(.15+Math.random()*.35)); nb++; }
    g.clearRect(0,0,W,H);
    for(const q of P){ if(q.life<=0) continue; q.x+=q.vx; q.y+=q.vy; q.life-=q.dec;
      if(q.k==='i'){ q.vx*=.985; q.vy=q.vy*.985+.05; q.rot+=q.vr; g.globalAlpha=Math.max(0,q.life); g.save(); g.translate(q.x,q.y); g.rotate(q.rot); if(img.complete) g.drawImage(img,-q.r/2,-q.r/2,q.r,q.r); g.restore(); }
      else if(q.k==='s'){ q.vx*=.985; q.vy=q.vy*.985+.06; g.globalAlpha=Math.max(0,q.life); g.fillStyle=q.col; g.beginPath(); g.arc(q.x,q.y,q.r,0,7); g.fill(); }
      else { q.vy+=.02; q.rot+=q.vr; g.globalAlpha=Math.max(0,Math.min(1,q.life*1.5)); g.save(); g.translate(q.x,q.y); g.rotate(q.rot); g.fillStyle=q.col; g.fillRect(-q.r/2,-q.r/4,q.r,q.r/2); g.restore(); } }
    g.globalAlpha=1; if(t<2600) requestAnimationFrame(step); };
  requestAnimationFrame(step);
}
function endCelebrate(){ celebrate.running=false; $('#congrats').classList.remove('show'); const cv=$('#fx'); cv.classList.remove('show'); cv.getContext('2d').clearRect(0,0,cv.width,cv.height); }
const findBoss = (slot) => BOSSES.find(b=>b.id===slot);
const JOBS = ['히어로','팔라딘','다크나이트','아크메이지(불,독)','아크메이지(썬,콜)','비숍','보우마스터','신궁','패스파인더','나이트로드','섀도어','듀얼블레이드','바이퍼','캡틴','캐논마스터','소울마스터','플레임위자드','윈드브레이커','나이트워커','스트라이커','미하일','아란','에반','루미너스','메르세데스','팬텀','은월','블래스터','배틀메이지','와일드헌터','메카닉','제논','데몬슬레이어','데몬어벤져','카이저','카인','카데나','엔젤릭버스터','아델','일리움','칼리','아크','라라','호영','렌','제로','키네시스'];
const WORLDS = ['스카니아','베라','루나','제니스','크로아','유니온','엘리시움','이노시스','레드','오로라','아케인','노바','에오스','핼리오스','챌린저스'];

/* =====================================================================
 *  시간/리셋 계산 (KST)
 * ===================================================================== */
const KST_MS = CONFIG.TZ_OFFSET_HOURS*3600e3;
const kst = (t=Date.now()) => new Date(t + KST_MS);
const kstDay = () => kst().toISOString().slice(0,10); // b60: 월간 보스 클리어 날짜 (KST)
const pad = n => String(n).padStart(2,'0');
function dayId(t){const d=kst(t);return `${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}-${pad(d.getUTCDate())}`}
function monthId(t){const d=kst(t);return `${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}`}
function weekStartMs(t=Date.now()){
  const d=kst(t); const back=(d.getUTCDay()-CONFIG.WEEKLY_RESET_DAY+7)%7;
  return Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate()-back) - KST_MS;
}
function weekId(t){return dayId(weekStartMs(t))}
function fmtWeek(wid){
  const s=Date.parse(wid+'T00:00:00+09:00'); const e=s+6*864e5;
  const a=kst(s),b=kst(e); return `${a.getUTCMonth()+1}/${a.getUTCDate()} ~ ${b.getUTCMonth()+1}/${b.getUTCDate()}`;
}
function hm(t){const d=kst(t);return `${d.getUTCMonth()+1}/${d.getUTCDate()} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`}
function untilText(ms){const h=Math.floor(ms/3600e3),m=Math.floor(ms%3600e3/60e3);const d=Math.floor(h/24);return d>0?`${d}일 ${h%24}시간`:`${h}시간 ${m}분`}

/* =====================================================================
 *  상태
 * ===================================================================== */
function defaultSettings(){
  return {weeklyLimit:CONFIG.WEEKLY_BOSS_LIMIT, monthlyLimit:CONFIG.MONTHLY_BOSS_LIMIT,
    prices:{}, accounts:[], autoEnable:true, lastSync:0};
}
// 일퀘 현황 표시 설정: off{항목:1}=전체 숨김, charOff{캐릭터:{항목:1}}=캐릭터별 숨김, hide{캐릭터:1}=카드 숨김
function defaultDq(){ return {off:{}, charOff:{}, hide:{}}; }
function defaultState(){
  return {version:5, theme:null, activeId:null, characters:[], worldOrder:[], history:[], monthHistory:[], startWeek:weekId(), settings:defaultSettings(), dq:defaultDq(),
    period:{week:weekId(), day:dayId(), month:monthId()}};
}
/* character: {id,name,job,level,world,ocid,image,isMain, bosses:{slot:{enabled,diff,party}},
 *   weekly:{slot:true}, monthly:{slot:weekId}, auto:{slot:true}, sync:{at,ok,msg,clear,limit,unmatched,imgAt}} */
let S;
// 저장된 상태 객체를 현재 형식으로 정리 (load·드라이브 병합 공용; obj 를 직접 고치므로 복사본을 넘길 것)
function normState(obj){
  const keep=S;
  try{
    S=Object.assign(defaultState(),obj&&typeof obj==='object'?obj:{});
    S.settings=Object.assign(defaultSettings(),S.settings||{});
    migrate();
    S.settings.prices={}; delete S.settings.priceSource; // 가격 수동 수정 기능 제거: 가격은 공식 prices.json 자동 갱신 값만 사용
    delete S.settings.driveKeys; // 예전 '키도 드라이브에 저장' 선택 항목 (이제 항상 저장)
    delete S.settings.apiMode;
    delete S.settings.autoSync; // 예전 '열려 있으면 15분마다 자동 동기화' 설정 (2026-10-10 제거 — 페이지를 열 때마다 자동 동기화로 대체)
    // ↑ 예전 연결 방식(로컬 프록시) 설정 — 이제 항상 open.api.nexon.com 직접 호출
    S.settings.weeklyLimit=CONFIG.WEEKLY_BOSS_LIMIT; S.settings.monthlyLimit=CONFIG.MONTHLY_BOSS_LIMIT; // 처치 한도는 고정값 (설정 화면 제거)
    delete S.settings.worldLimit; // 월드 결정석 판매 한도 기능 제거 (수익 = 클리어한 보스 합계, 상한 없음)
    sjmMigrate(S.characters); sjmMigrate(S.history); sjmMigrate(S.monthHistory); // b261
    S.characters.forEach(normChar);
    S.dq=Object.assign(defaultDq(),S.dq&&typeof S.dq==='object'?S.dq:{}); ['off','charOff','hide'].forEach(k=>{ if(!S.dq[k]||typeof S.dq[k]!=='object') S.dq[k]={}; }); // b111: 일퀘 현황 탭 복원
    if(typeof S.updatedAt!=='number') S.updatedAt=0;
    return S;
  } finally { S=keep; }
}
function load(){
  let o=null;
  try{ const raw=localStorage.getItem(CONFIG.STORAGE_KEY); o=raw?JSON.parse(raw):null; }catch(e){ console.warn(e); }
  S=normState(o);
  lastBody=bodyOf(); lastSig=contentSig(S);
}
function migrate(){
  if((S.version||1)<2){
    // v1 → v2: 일일 보스 삭제, 캐릭터 결정석 14개 → 주간 보스 12개, 월드 180 → 90
    S.characters.forEach(c=>{ delete c.daily; delete c.dailyWeek; for(const k of Object.keys(c.bosses||{})) if(k.startsWith('d_')) delete c.bosses[k]; });
    for(const k of Object.keys(S.settings.prices)) if(k.startsWith('d_')) delete S.settings.prices[k];
    delete S.settings.charLimit;
    S.version=2;
  }
  if(S.version<3){
    // v2 → v3: 사용자 지정 순서 도입. 기존 화면 순서(본캐 → 레벨순)를 그대로 저장 순서로 고정
    S.characters.sort((a,b)=>(b.isMain?1:0)-(a.isMain?1:0) || (Number(b.level)||0)-(Number(a.level)||0));
    S.worldOrder=[]; S.version=3;
  }
  if(S.version<4){
    // v3 → v4: 2026-06 패치로 일일 보스가 된 힐라(하드)·핑크빈(카오스)·시그너스(노멀), 삭제된 시그너스(이지)를 주간 목록에서 제거.
    // 2026-09-17 공식 가격 반영: 이전 기본값이 설정에 '그대로' 저장돼 있으면 지움(사용자가 직접 바꾼 값은 유지).
    const gone=['hilla','pinkbean','cygnus'];
    S.characters.forEach(c=>{ for(const k of gone){ ['bosses','weekly','monthly','auto'].forEach(f=>{ if(c[f]) delete c[f][k]; }); } });
    const P=S.settings.prices||{};
    for(const k of Object.keys(P)){ if(gone.some(g=>k.startsWith(g+'_'))) delete P[k]; else if(OLD_DEFAULT_PRICES[k]===P[k]) delete P[k]; }
    S.version=4;
  }
  if(S.version<5){
    // v4 → v5: 주간 수익에서 월간 보스(검은 마법사) 분리. 지난 주 기록에 섞여 있던 검은 마법사 수익을 빼서 '주간 보스만'으로 정리
    const bm=findBoss('blackmage'), rd=Object.fromEntries(Object.entries(D).map(([k,v])=>[v,k]));
    (S.history||[]).forEach(h=>{ if(h.weeklyOnly) return; let minus=0, cnt=0;
      (h.perChar||[]).forEach(pc=>{ let m=0; pc.bosses=(pc.bosses||[]).filter(t=>{ const x=/^검은 마법사\((.+?)\)(?:\/(\d+)인)?$/.exec(t); if(!x) return true;
        const d=rd[x[1]]; if(d&&bm.diffs.includes(d)) m+=Math.floor(price(bm,d)/Math.max(1,+x[2]||1)); cnt++; return false; });
        if(m){ pc.meso=Math.max(0,(pc.meso||0)-m); minus+=m; } if(pc.count!=null) pc.count=pc.bosses.length; });
      h.total=Math.max(0,(h.total||0)-minus); if(cnt){ h.cleared=Math.max(0,(h.cleared||0)-cnt); if(h.crystals!=null) h.crystals=Math.max(0,h.crystals-cnt); } h.weeklyOnly=true; });
    S.version=5;
  }
  if(!Array.isArray(S.monthHistory)) S.monthHistory=[];
  if(!Array.isArray(S.missW)) S.missW=[]; if(!Array.isArray(S.missM)) S.missM=[];
  // 총 수익 집계 시작 주: 가장 오래된 기록 주(없으면 이번 주). 한 번 정하면 저장되어 유지
  { const ws=(S.history||[]).map(h=>h.week).filter(Boolean).sort(); const first=ws[0]||S.period?.week||weekId();
    if(!S.startWeek || first<S.startWeek) S.startWeek=first; }
  if(!Array.isArray(S.worldOrder)) S.worldOrder=[];
  // 단일 API 키 → 여러 넥슨 계정(계정마다 라벨 + 키). 기존 키는 '본계정'이 됨
  if(!Array.isArray(S.settings.accounts)) S.settings.accounts=[];
  for(const a of S.settings.accounts) if(a&&(a.bk||a.bkLabel)){ delete a.bk; delete a.bkLabel; } // b74: 예비 API 키 기능 삭제 — 저장된 예비 키는 버림 (금고에서도 다음 동기화 때 빠짐)
  if(S.settings.apiKey){
    const k=String(S.settings.apiKey).trim();
    if(k && !S.settings.accounts.some(a=>a.key===k)) S.settings.accounts.unshift({id:uid(),label:S.settings.accounts.length?'계정'+(S.settings.accounts.length+1):'본계정',key:k});
    delete S.settings.apiKey;
  }
}
/* 보스·난이도별 최대 파티 인원 (기본 CONFIG.MAX_PARTY=6). 익스트림 스우 2인 · 최초의 대적자/찬란한 흉성/벨로나/림보/발드릭스/유피테르 3인 */
const PARTY_MAX = { lotus:{extreme:2}, adversary:3, star:3, bellona:3, limbo:3, baldrix:3, jupiter:3 };
const partyMax = (b,diff) => { const v=PARTY_MAX[b?.id??b]; const n=typeof v==='object'?v?.[diff]:v; return Math.max(1,Math.min(CONFIG.MAX_PARTY,+n||CONFIG.MAX_PARTY)); };
/* =====================================================================
 *  b251: 새 보스·새 난이도 자동 추가 (scripts/boss_auto.py 가 공식 공지에서 찾아 data/bosses_auto.json 에 기록, Actions 가 커밋)
 *  - 빌드 때 그 파일을 AUTO_BOSSES 로 넣고, 접속하면 ./data/bosses_auto.json 을 다시 받아 합침 (이 브라우저에 보관)
 *  - 더하기만 함: 없는 난이도·보스만 추가, 가격·파티 인원·드롭은 내장 값이 없을 때만. 내장 데이터가 항상 우선
 * ===================================================================== */
const AUTO_BOSSES=/*__AUTO_BOSSES__*/{};
const AUTO_KEY='mapleBossTracker.autoBosses';
const DIFF_ORDER=['easy','normal','hard','chaos','extreme'];
function applyAutoBosses(j){
  if(!j||!Array.isArray(j.bosses)) return false; let ch=false;
  for(const e of j.bosses){ if(!e||typeof e.name!=='string'||!e.diffs||typeof e.diffs!=='object') continue;
    const n=normName(e.name);
    let b=BOSSES.find(x=>x.id===e.id)||BOSSES.find(x=>[x.name,...(x.aliases||[])].map(normName).includes(n));
    if(!b){ if(!/^auto_[0-9a-f]{8}$/.test(String(e.id))) continue;
      b={id:e.id,name:e.name.slice(0,20),type:e.type==='monthly'?'monthly':'weekly',diffs:[],auto:true};
      const i=b.type==='weekly'?BOSSES.findIndex(x=>x.type==='monthly'):-1; if(i<0) BOSSES.push(b); else BOSSES.splice(i,0,b); ch=true; }
    for(const [d,v] of Object.entries(e.diffs)){ if(!DIFF_ORDER.includes(d)||!v) continue;
      if(!b.diffs.includes(d)){ b.diffs.push(d); b.diffs.sort((x,y)=>DIFF_ORDER.indexOf(x)-DIFF_ORDER.indexOf(y)); (b.autoDiffs=b.autoDiffs||[]).push(d); ch=true; }
      const k=priceKey(b,d), p=Math.round(+v.price);
      if(!(k in PRICE_CONFIG) && p>=1e5 && p<=5e10){ PRICE_CONFIG[k]=p; ch=true; }
      else if(k in BUILTIN_PRICE_LOCK && p>0 && p!==BUILTIN_PRICE_LOCK[k]) noteConflict(k,p,v.src&&v.src.url);
      const pm=+v.partyMax; if(pm>=1&&pm<=6&&PARTY_MAX[b.id]==null){ PARTY_MAX[b.id]={[d]:pm}; ch=true; }
      else if(pm>=1&&pm<=6&&typeof PARTY_MAX[b.id]==='object'&&PARTY_MAX[b.id][d]==null){ PARTY_MAX[b.id][d]=pm; ch=true; }
      for(const nm of (Array.isArray(v.drops)?v.drops:[])){ if(typeof nm!=='string'||!nm||nm.length>30) continue;
        let key=Object.keys(ITEMS).find(x=>ITEMS[x].n===nm);
        if(!key){ key='auto_'+[...nm].reduce((h,c)=>(h*31+c.charCodeAt(0))>>>0,7).toString(16); ITEMS[key]={n:nm,set:'기타',auto:true}; }
        const L=DROPS[b.id]=DROPS[b.id]||[]; const r=L.find(x=>x[0]===key);
        if(!r){ L.push([key,[d]]); ch=true; } else if(!r[1].includes(d)){ r[1].push(d); ch=true; } }
    }
  }
  return ch;
}
let autoSig='';
function fetchAutoBosses(){
  if(!/^https?:$/.test(location.protocol)) return;
  fetch(`./data/bosses_auto.json?t=${Math.floor(Date.now()/300000)}`,{cache:'no-cache'}).then(r=>r.ok?r.json():null).then(j=>{
    if(!j||!Array.isArray(j.bosses)) return; const sig=JSON.stringify(j); if(sig===autoSig) return; autoSig=sig;
    try{ localStorage.setItem(AUTO_KEY,sig); }catch(e){}
    if(applyAutoBosses(j)){ try{ const c=JSON.parse(localStorage.getItem(PRICES_CACHE_KEY)||'null'); if(c) applyOfficialPrices(prMerge(c,srvPr())); }catch(e){} render(); }
  }).catch(()=>{});
}
/* 저장된 파티 인원이 한도를 넘으면 한도로 낮춤 (나머지는 그대로) */
function clampParty(c,slot){ const cfg=c?.bosses?.[slot]; if(!cfg) return; const b=findBoss(slot); if(!b) return; const m=partyMax(b,cfg.diff||b.diffs[0]); if((parseInt(cfg.party)||1)>m) cfg.party=m; }
let dropClampN=0; // 2026-10-10: 보스·아이템당 기간 1개로 — 예전 2개 이상 기록을 1로 줄인 수 (콘솔 보고)
function clampDropMap(m,om){ for(const k of Object.keys(m||{})) if(k.includes('|')&&(+m[k]||0)>1){ m[k]=1; dropClampN++; if(om&&Array.isArray(om[k])&&om[k].length>1) om[k]=om[k].slice(-1); } }
function normChar(c){ ['bosses','weekly','monthly','mdate','auto','sync','drops','mdrops','dropOut','mdropOut'].forEach(k=>c[k]=c[k]||{}); clampDropMap(c.drops,c.dropOut); clampDropMap(c.mdrops,c.mdropOut); delete c.dropParty; delete c.mdropParty; c.world=c.world||''; Object.values(c.bosses).forEach(cfg=>{ if(cfg&&typeof cfg==='object') cfg.party=Math.max(1,parseInt(cfg.party)||1); }); Object.keys(c.bosses).forEach(s=>clampParty(c,s)); } // party 는 항상 숫자 (없음/'1' 문자열이면 취소·저장 비교가 어긋났음)
// updatedAt: 데이터 내용이 '실제로' 바뀐 시각 (구글 드라이브 동기화에서 어느 쪽이 최신인지 비교)
// — 기기마다 다른 값·자동으로 계속 바뀌는 값(테마, 선택한 캐릭터, 날짜(period), 마지막 동기화 시각, 캐릭터 sync/이미지/EXP, 계정 상태)은
//   contentSig 에서 빠지므로 updatedAt 을 바꾸지 않고 드라이브 저장도 하지 않음 (2026-10-10: 이것 때문에 '어느 데이터를 쓸까요?'가 반복됐음)
let lastBody=null, lastSig=null, render0Dirty=false;
function bodyOf(){ const u=S.updatedAt; S.updatedAt=0; const b=JSON.stringify(S); S.updatedAt=u; return b; }
/* 보스 목록 [취소]/[저장]: 파티 인원 변경·드롭 클릭은 '대기 중' — 저장 전에는 수익 기록(수익 패널·캐릭터 목록·기록 탭)과 저장소에 반영 안 됨.
 * 첫 변경 직전 상태(pend.base)를 복사해 두고, 취소 = 되돌림 / 저장 = 확정(+서버 모드면 서버 저장). 나중 버튼도 pendSave() 만 부르면 됨. */
let pend=null;
// 비교용 정규화: 파티 인원 숫자화(없음·'1' → 1), 0개 드롭·빈 결과 목록 제거
function pendSig(x){ const d=JSON.parse(JSON.stringify(x)); (d.characters||[]).forEach(c=>{ normChar(c);
  for(const m of [c.drops,c.mdrops]) for(const k of Object.keys(m)) if(!(+m[k]>0)) delete m[k];
  for(const m of [c.dropOut,c.mdropOut,c.chaosOut,c.mchaosOut]) for(const k of Object.keys(m||{})) if(!Array.isArray(m[k])||!m[k].length) delete m[k];
  for(const f of ['dmode','mdmode']) if(c[f]){ for(const k of Object.keys(c[f])) if(!(+(c[f==='dmode'?'drops':'mdrops']||{})[k]>0)) delete c[f][k]; if(!Object.keys(c[f]).length) delete c[f]; } }); return contentSig(d); }
function pendStart(){ if(!pend){ pend={base:JSON.parse(JSON.stringify(S))}; } }
const COMMITTED=fn=>{ if(!pend) return fn(); const live=S; pend.base.activeId=live.activeId; S=pend.base; try{ return fn(); } finally{ S=live; } };
const cRev=c=>COMMITTED(()=>charRevenue(S.characters.find(x=>x.id===c.id)||c));
function pendCancel(quiet){ if(!pend) return; const keepId=S.activeId; S=pend.base; S.activeId=keepId; pend=null; save(); render(); if(!quiet) toast('변경사항을 취소했습니다'); }
let pendDoneAt=0; // b75: 보스 목록 [저장] → 취소 버튼 왼쪽에 초록 '저장이 완료되었습니다.' (하단 알림 없음)
// b81: [저장] = 즉시 (이 PC 에 확정·화면·'저장이 완료되었습니다.' 바로). 서버 저장은 뒤에서(svPushBg) — 기다리지 않음, 실패하면 다시 시도 후 헤더 '⚠ 저장 안 됨'
let svPushing=false; // 뒤에서 서버 저장 중(재시도 포함) — 이동안 [저장]/[취소]는 꺼 둠
function svPushBg(n=0){ if(!(SV_ON&&svTok()&&gdMeta.on)) return; clearTimeout(svPushBg._t); svPushing=true;
  const end=()=>{ svPushing=false; if(tab==='boss') render(); else gdRender(); };
  gdPush({manual:false}).then(ok=>{ gdRender(); if(ok&&!gdLocalDirty()) return end(); end(); if(n<3&&gd.state!=='conflict'&&svTok()) svPushBg._t=setTimeout(()=>{ if(gdLocalDirty()&&!svPushing) svPushBg(n+1); },1500*(n+1)); }).catch(end); } // 실패하면 버튼은 다시 켜고(경고 표시) 뒤에서 몇 번 더 시도
async function pendSave(){ if(!pend&&!svUnsaved()) return; pend=null; save(); pendDoneAt=Date.now(); svPushBg(); render();
  clearTimeout(pendSave._t); pendSave._t=setTimeout(()=>{ pendDoneAt=0; document.querySelectorAll('.pdone').forEach(e=>e.remove()); },3000); }
/* b75: 저장 안 한 보스 목록 변경이 있으면 탭 이동·다른 캐릭터 선택 전에 묻기 (그 캐릭터 사진 + 문구, 예=저장 후 이동 / 아니오=버리고 이동 / 바깥 클릭=머무름) */
function pendGuard(go){ if(!pend) return go(); const c=activeChar();
  svAsk('지금까지의 변경사항을 저장하시겠습니까?',[['yes','예'],['no','아니오']],c?`<div class="pgav">${avatar(c,'pgavi')}<div class="pgname">${esc(c.name||'')}</div></div>`:'').then(async k=>{ if(k==='yes'){ await pendSave(); go(); } else if(k==='no'){ pendCancel(true); go(); } }); }
function pendAsk(){ svAsk('변경사항을 취소하시겠습니까?',[['yes','예'],['no','아니오']]).then(k=>{ if(k==='yes') pendCancel(); }); }
function save(){
  if(pend){ if(pendSig(S)===pendSig(pend.base)) pend=null; else return; } // 대기 중: 저장소에 쓰지 않음. 되돌려서 스냅샷과 같아지면 대기 해제(버튼 비활성)
  const sig=contentSig(S), changed=sig!==lastSig;
  if(changed){ S.updatedAt=Date.now(); lastSig=sig; }
  lastBody=bodyOf();
  localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(S));
  if(changed) gdChanged();
  if(typeof svKeysSoon==='function') svKeysSoon(); // b62: 서버 모드 — 키(부계정·예비)만 바뀐 것도 바로 금고에 (키는 내용 비교에서 빠져 있어 [저장]이 안 생김)
}
const price = (b,diff) => { const k=priceKey(b,diff); return (k in S.settings.prices)?S.settings.prices[k]:(PRICE_CONFIG[k]||0); };
const activeChar = () => { const c=S.characters.find(c=>c.id===S.activeId); return c&&charShown(c)?c:activeChars()[0]; };
const uid = () => Math.random().toString(36).slice(2,9)+Date.now().toString(36).slice(-4);
const worldOf = c => c.world || '월드 미지정';

/* ---------- 빠뜨린 보스메소 (수익 분석) ----------
 * S.missW=[{week,date:'YYYY.MM.DD'(초기화 날짜),n,meso,list:[{name,n,meso}],approx?}] / S.missM=[{month,date,...}]
 * 주간: 초기화(목 00:00) 직전 상태로 각 캐릭터의 '상위 12개 중 못 잡은 주간 보스'(예상 수익과 같은 규칙: 스케줄러 보스·파티 분배) 합계.
 * 월간: 초기화(1일 00:00) 직전 상태로 월간 보스(검은 마법사)를 못 잡은 캐릭터. 기간당 1개(중복 없음). 서버 키 없이 브라우저에서 계산 */
const ymdDot = id => String(id).replace(/-/g,'.');
const nextWeekId = w => dayId(Date.parse(w+'T00:00:00+09:00')+7*864e5);
const nextMonthId = m => { const [y,mm]=m.split('-').map(Number); return mm===12?`${y+1}-01`:`${y}-${pad(mm+1)}`; };
function missPack(list){ return {n:list.reduce((a,x)=>a+x.n,0), meso:list.reduce((a,x)=>a+x.meso,0), list}; }
function missNow(kind){ const list=[];
  S.characters.forEach(c=>{ const r=remainingWeekly(c), l=kind==='w'?r.list:r.mon; if(l.length) list.push({id:c.id,name:c.name,n:l.length,meso:l.reduce((a,x)=>a+x.value,0)}); }); // zosu-apikey: 전체 저장(id 포함), 화면에서 activeMiss 로 거름
  return missPack(list); }
function missRecord(kind,id,pk,extra){ const arr=kind==='w'?(S.missW||(S.missW=[])):(S.missM||(S.missM=[])), f=kind==='w'?'week':'month';
  if(!id||arr.some(x=>x[f]===id)) return false;
  arr.push({[f]:id, date:ymdDot(kind==='w'?nextWeekId(id):nextMonthId(id)+'-01'), ...pk, ...(extra||{})}); arr.sort((a,b)=>a[f]<b[f]?-1:1); return true; }
// 며칠/몇 주 안 열었을 때: 저장된 주간 기록(history: 캐릭터별 클리어 보스)으로 지난 주들을 채움 (보스 목록·가격은 지금 설정 기준이라 근사값)
function missBackfill(){ let n=0; const cur=weekId(), lim=S.settings.weeklyLimit;
  for(const h of S.history||[]){ if(!h.week||h.week>=cur||(S.missW||[]).some(x=>x.week===h.week)) continue; const list=[];
    for(const p of h.perChar||[]){ const c=S.characters.find(x=>x.id===p.id); if(!c) continue; // zosu-apikey: 숨은 캐릭터도 id 와 함께 저장, 화면에서 activeMiss 로 거름
      const top=expectedAll(c).slice(0,lim), got=new Set((p.bosses||[]).map(t=>String(t).split('(')[0]));
      const miss=top.filter(x=>!got.has(x.name)).slice(0,Math.max(0,top.length-(+p.count||0)));
      if(miss.length) list.push({id:c.id,name:p.name||c.name,n:miss.length,meso:miss.reduce((a,x)=>a+x.value,0)}); }
    if(missRecord('w',h.week,missPack(list),{approx:true})) n++; }
  return n; }
function missSync(){ if(typeof SV_ON!=='undefined'&&SV_ON&&!pend) setTimeout(()=>{ try{ if(svTok()&&gdMeta.on) svSaveNow(); }catch(e){} },1500); }
function missChart(rows, kind){
  if(!rows.length) return '<p class="muted">아직 기록이 없어요</p>';
  const n=rows.length, W=Math.max(640,90+n*80), Hh=236, pl=45, pr=45, pt=46, pb=34, /* b186: 위 오른쪽 총 누적 자리 */ max=Math.max(1,...rows.map(r=>r.meso));
  const X=i=>n===1?W/2:pl+(W-pl-pr)*i/(n-1), Y=v=>Hh-pb-(Hh-pb-pt)*v/max;
  const tip=r=>(r.list.length?`${r.date} · 손해 ${meso(r.meso)}\n`+r.list.map(x=>`${x.name}: ${x.n}개 · ${meso(x.meso)}`).join('\n')+`\n합계: ${r.n}개 · ${meso(r.meso)}`+(r.approx?'\n(주간 기록으로 채운 근사값)':''):`${r.date}\n손해 없음`);
  const u=++chartUid, c=kind==='m'?'#ff6b6b':'#f2c94c', c2=kind==='m'?'#ff9a8a':'#ffe08a', pts=rows.map((r,i)=>`${X(i).toFixed(1)},${Y(r.meso).toFixed(1)}`).join(' ');
  const grid=[.25,.5,.75,1].map(f=>`<line class="cg" x1="${pl-20}" x2="${W-pr+20}" y1="${Y(max*f).toFixed(1)}" y2="${Y(max*f).toFixed(1)}" stroke="url(#mcgr${u})"/>`).join('')+rows.map((r,i)=>`<line class="ctick" x1="${X(i).toFixed(1)}" x2="${X(i).toFixed(1)}" y1="${Hh-pb}" y2="${Hh-pb+5}"/>`).join('');
  return `<div class="chart scrollx misschart lux ${kind==='m'?'mm':'mw'}"><div class="ctot"><span>빠뜨린 보스메소 총 누적</span><b>${meso(rows.reduce((t,r)=>t+(+r.meso||0),0))}</b></div><svg viewBox="0 0 ${W} ${Hh}" style="width:${W}px;max-width:${W>640?'none':'100%'}" role="img" aria-label="빠뜨린 보스메소 그래프">
    <defs><linearGradient id="mcg${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c}" stop-opacity=".3"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></linearGradient>
    <linearGradient id="mcs${u}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${c}"/><stop offset="1" stop-color="${c2}"/></linearGradient>
    <linearGradient id="mcgr${u}" gradientUnits="userSpaceOnUse" x1="${pl-20}" y1="0" x2="${W-pr+20}" y2="0"><stop offset="0" stop-color="${c2}" stop-opacity=".1"/><stop offset=".5" stop-color="${c2}" stop-opacity=".34"/><stop offset="1" stop-color="${c2}" stop-opacity=".1"/></linearGradient>
    <linearGradient id="mcb${u}" gradientUnits="userSpaceOnUse" x1="${pl-20}" y1="0" x2="${W-pr+20}" y2="0"><stop offset="0" stop-color="${c}" stop-opacity=".15"/><stop offset=".5" stop-color="${c2}"/><stop offset="1" stop-color="${c}" stop-opacity=".15"/></linearGradient>
    <linearGradient id="mcbar${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c2}" stop-opacity=".5"/><stop offset=".4" stop-color="${c}" stop-opacity=".22"/><stop offset="1" stop-color="${c}" stop-opacity=".03"/></linearGradient>
    <filter id="mcf${u}" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    ${grid}<line class="cg cg0" x1="${pl-20}" x2="${W-pr+20}" y1="${Hh-pb}" y2="${Hh-pb}" stroke="url(#mcb${u})"/>
    ${n>1?`<polygon class="carea" fill="url(#mcg${u})" points="${X(0).toFixed(1)},${Hh-pb} ${pts} ${X(n-1).toFixed(1)},${Hh-pb}"/>`:''}
    <polyline class="cline" pathLength="1" fill="none" stroke="url(#mcs${u})" stroke-width="2.8" stroke-linejoin="round" stroke-linecap="round" filter="url(#mcf${u})" points="${pts}"/>
    ${rows.map((r,i)=>`<g class="mpt" data-tip="${esc(tip(r))}" style="--d:${(.15+i*.06).toFixed(2)}s;--c:${c}"><circle cx="${X(i).toFixed(1)}" cy="${Y(r.meso).toFixed(1)}" r="14" fill="transparent"/><rect class="cbar" x="${(X(i)-12).toFixed(1)}" y="${Y(r.meso).toFixed(1)}" width="24" height="${Math.max(0,Hh-pb-Y(r.meso)).toFixed(1)}" rx="5" fill="url(#mcbar${u})"/><circle class="mdot" cx="${X(i).toFixed(1)}" cy="${Y(r.meso).toFixed(1)}" r="4.5"/>
      <g class="cval cvd"><title>${r.meso?meso(r.meso):'0 메소'}</title>${tirSvg(r.meso?meso(r.meso).replace(/ .*/,''):'0',X(i),Y(r.meso)-12,12,kind==='m'?'tgold tred':'tgold')}</g>
      <text class="cxl" x="${X(i).toFixed(1)}" y="${Hh-pb+18}" text-anchor="middle" font-size="10">${r.date}</text></g>`).join('')}</svg></div>`;
}
let chartUid=0;
/* b139: 그래프 그려지는 애니메이션은 화면에 들어올 때 시작 (그 전엔 멈춤·숨김). 렌더로 새로 생긴 .chart.lux 를 MutationObserver 로 잡아 IntersectionObserver 에 등록 */
(()=>{ if(typeof document==='undefined') return; const inv=el=>{ el.classList.add('inview'); try{ tsvAnim(el); }catch(e){} };
  const io=typeof IntersectionObserver==='function'?new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting){ inv(e.target); io.unobserve(e.target); } }),{threshold:.25}):null;
  const scan=root=>(root.querySelectorAll?root.querySelectorAll('.chart.lux:not(.inview)'):[]).forEach(el=>io?io.observe(el):inv(el));
  const start=()=>{ scan(document); new MutationObserver(ms=>{ for(const m of ms) for(const n of m.addedNodes) if(n.nodeType===1){ if(n.matches?.('.chart.lux')) scan(n.parentNode); else scan(n); } }).observe(document.body,{childList:true,subtree:true}); };
  if(document.body) start(); else document.addEventListener('DOMContentLoaded',start); })();
const missIcon = '<span class="missic" aria-hidden="true">!</span>', missIconM = '<span class="missic red" aria-hidden="true">!</span>';
function missHtml(){ return `<div class="card"><h2>${missIcon} 지금까지 빠뜨린 보스메소는? (주간 Ver)</h2>${missChart((S.missW||[]).map(r=>activeMiss(r)),'w')}</div>
  <div class="card"><h2>${missIconM} 지금까지 빠뜨린 보스메소는? (월간 Ver)</h2>${missChart((S.missM||[]).map(r=>activeMiss(r)),'m')}</div>`; }

/* ---------- 리셋 처리 ---------- */
function resetCore(){
  const now={week:weekId(),day:dayId(),month:monthId()}; let changed=false; const msgs=[];
  if(S.period.week!==now.week){
    missRecord('w',S.period.week,missNow('w')); // 지난 주 빠뜨린 보스메소 (초기화 전 상태로 계산)
    const sum=weekSummary(S.period.week);
    if(sum.cleared>0 && !S.history.some(h=>h.week===S.period.week)) S.history.push(sum);
    S.history.sort((a,b)=>a.week<b.week?-1:1);
    S.characters.forEach(c=>{c.weekly={}; c.wat={}; c.drops={}; c.dropOut={}; delete c.dmode; delete c.drev; for(const k in c.auto) if(findBoss(k)?.type==='weekly') delete c.auto[k]; bossNextApply(c);}); // b241: 대기 중 스케줄러 변경 적용
    msgs.push('주간 보스가 초기화되었습니다 (지난 주 기록 저장됨)'); changed=true;
  }
  if(S.period.month!==now.month){
    missRecord('m',S.period.month,missNow('m'));
    const ms=monthSummary(S.period.month); if(ms.cleared>0 && !S.monthHistory.some(h=>h.month===ms.month)) S.monthHistory.push(ms);
    S.monthHistory.sort((a,b)=>a.month<b.month?-1:1);
    S.characters.forEach(c=>{c.monthly={}; c.mdate={}; c.mdrops={}; c.mdropOut={}; delete c.mdmode; delete c.mdrev; for(const k in c.auto) if(findBoss(k)?.type==='monthly') delete c.auto[k];}); msgs.push('월간 보스 초기화'); changed=true; }
  if(S.period.day!==now.day) changed=true;
  if(changed) S.period=now;
  return {changed,msgs};
}

/* b134: 2026-10-15 목 리셋 직후 b133 버그로 꺼진 등록 복구 (캐릭터마다 1번, c.b134 표시).
 *  근거 = 실제 기록만: 지난 주 주간 기록(S.history)의 그 캐릭터 처치 보스 '이름(난이도)'. 꺼져 있거나 없는 보스를 그 난이도로 다시 켬(파티 인원은 남은 값).
 *  지어낸 값 없음. 이후 이번 주 스케줄러 응답이 오면 그 목록이 우선(목록에 없으면 다시 꺼짐). */
function b134Restore(){ let n=0; const wk=S.period?.week; if(!wk) return 0;
  const last=(S.history||[]).filter(h=>h.week&&h.week<wk).sort((a,b)=>a.week<b.week?1:-1)[0]; if(!last) return 0;
  for(const c of S.characters||[]){ if(c.b134) continue; c.b134=1;
    const pc=(last.perChar||[]).find(p=>p.id===c.id); if(!pc) continue;
    for(const t of pc.bosses||[]){ const m=/^(.+?)\((.+?)\)/.exec(t); if(!m) continue; const b=BOSSES.find(x=>x.name===m[1]), d=DK[m[2]];
      if(!b||b.type!=='weekly'||!b.diffs.includes(d)) continue; const cfg=c.bosses[b.id];
      if(cfg?.enabled) continue; c.bosses[b.id]={enabled:true,diff:d,party:cfg?.party||1}; clampParty(c,b.id); n++; } }
  return n; }
function checkResets(){ const r=resetCore(); try{ if(syncGoneTick()) r.changed=true; }catch(e){ console.warn('syncGoneTick',e); } if(b134Restore()) r.changed=true; const bf=missBackfill(); if(r.changed||bf) missSync(); if(r.changed||bf){ save(); if(r.msgs.length) toast(r.msgs.join(' · ')); } return r.changed; }
// 다른 상태 객체(드라이브 데이터 등)도 지금 주·월로 넘김 (지난 주 체크 → 기록으로 보관 후 초기화) — 병합 전에 양쪽 기준을 맞춤
function rollPeriod(x){ const keep=S; try{ S=x; resetCore(); } finally{ S=keep; } return x; }

/* ---------- 클리어 수 / 수익 계산 ---------- */
const weeklyCount = c => Object.keys(c.weekly).filter(s=>findBoss(s)?.type==='weekly').length;
const monthlyCount = c => Object.keys(c.monthly).length;
/* 이번 주 클리어한 주간 보스 + 이번 달 클리어한 월간 보스. 주간 수익과 월간 수익은 따로 집계한다. */
function charCrystals(c){
  const list=[];
  for(const slot in c.bosses){
    const cfg=c.bosses[slot]; const b=findBoss(slot); if(!b||!cfg) continue;
    const ok = b.type==='weekly' ? !!c.weekly[slot] : !!c.monthly[slot];
    if(!ok) continue;
    const diff=cfg.diff, party=Math.max(1,Math.min(partyMax(b,diff),cfg.party||1));
    list.push({slot,name:b.name,type:b.type,diff,party,gross:price(b,diff),value:Math.floor(price(b,diff)/party),auto:!!c.auto[slot]});
  }
  list.sort((a,b)=>b.value-a.value);
  let w=0,m=0; list.forEach(x=>{ if(x.type==='weekly'){ x.counted = w < S.settings.weeklyLimit; w++; } else { x.counted = m < S.settings.monthlyLimit; m++; } });
  return list;
}
function charRevenue(c){ const l=charCrystals(c), sum=t=>l.filter(x=>x.type===t&&x.counted).reduce((s,x)=>s+x.value,0);
  return {list:l, wlist:l.filter(x=>x.type==='weekly'), mlist:l.filter(x=>x.type==='monthly'), weekly:weeklyCount(c), meso:sum('weekly'), monthMeso:sum('monthly')}; }
/* 아직 이번 주 주간 보스를 하나도 안 잡은 캐릭터용 '예상 주간 수익':
 * 이 캐릭터가 켜 둔(⚙ 보스 선택) 주간 보스를 지금 고른 난이도·파티 인원으로 모두 잡는다고 보고,
 * 실제 수익 계산(charCrystals)과 같은 규칙으로 1인당 결정석 가격이 높은 순 상위 12개(주간 처치 한도)를 합산. */
function expectedWeekly(c){
  const l=[];
  for(const b of BOSSES){ if(b.type!=='weekly') continue; const cfg=c.bosses[b.id]; if(!bossOn(c,b)) continue; /* b241 */
    const diff=b.diffs.includes(cfg.diff)?cfg.diff:b.diffs[0], party=curParty(c,b.id);
    l.push({slot:b.id,name:b.name,diff,party,value:Math.floor(price(b,diff)/party)}); }
  l.sort((a,b)=>b.value-a.value); const top=l.slice(0,S.settings.weeklyLimit);
  return {list:top, all:l.length, meso:top.reduce((s,x)=>s+x.value,0)};
}
// 이번 주 남은 예상 수익: 12칸 중 아직 안 채운 칸을, 켜 둔 주간 보스 중 아직 안 잡은 것의 1인당 가격 상위로 채움 (12개 다 잡으면 빈 목록)
function remainingWeekly(c){
  const lim=S.settings.weeklyLimit, done=weeklyCount(c), left=Math.max(0,lim-done);
  const l=expectedAll(c).filter(x=>!c.weekly[x.slot]).slice(0,left);
  // 월간 보스(스케줄러에 있는 것만): 이번 달 아직 안 잡았으면 더함
  const mon=BOSSES.filter(b=>b.type==='monthly'&&c.bosses[b.id]?.enabled&&!c.monthly[b.id]).map(b=>{ const cfg=c.bosses[b.id], diff=b.diffs.includes(cfg.diff)?cfg.diff:b.diffs[0], party=curParty(c,b.id); return {slot:b.id,name:b.name,diff,party,value:Math.floor(price(b,diff)/party),monthly:true}; });
  const wm=l.reduce((s,x)=>s+x.value,0), mm=mon.reduce((s,x)=>s+x.value,0);
  return {list:l, mon, done, left, meso:wm+mm};
}
function expectedAll(c){ const l=[];
  for(const b of BOSSES){ if(b.type!=='weekly') continue; const cfg=c.bosses[b.id]; if(!bossOn(c,b)) continue; /* b241 */
    const diff=b.diffs.includes(cfg.diff)?cfg.diff:b.diffs[0], party=curParty(c,b.id); l.push({slot:b.id,name:b.name,diff,party,value:Math.floor(price(b,diff)/party)}); }
  return l.sort((a,b)=>b.value-a.value); }
function allRevenue(list){ // b72: list 없으면 전체(기록 저장용), 화면의 '이번 주' 패널은 보이는 캐릭터만
  const per=(list||S.characters).map(c=>({c,r:charRevenue(c)}));
  let total=0, count=0, monthTotal=0, monthCount=0;
  per.forEach(p=>{ p.r.wlist.filter(x=>x.counted).forEach(x=>{ total+=x.value; count++; }); p.r.mlist.filter(x=>x.counted).forEach(x=>{ monthTotal+=x.value; monthCount++; }); });
  return {per, total, count, monthTotal, monthCount};
}
const bossTag = x => `${x.name}(${D[x.diff]})`+(x.party>1?`/${x.party}인`:'');
// 주간 기록: 주간 보스만 (월간 보스는 monthSummary 로 따로)
/* 희귀 드롭 획득 수량 (수익에는 넣지 않음): c.drops = {'보스|아이템': 개수} (이번 주), c.mdrops = 월간 보스용 (이번 달) */
const dropMap = (c,type) => type==='monthly' ? (c.mdrops||(c.mdrops={})) : (c.drops||(c.drops={}));
const dropCount = (c,b,item) => +(dropMap(c,b.type)[b.id+'|'+item]||0);
const cleanItems = m => Object.fromEntries(Object.entries(m||{}).filter(([,n])=>+n>0).map(([k,n])=>[k,+n]));
const itemSum = m => Object.values(m||{}).reduce((s,n)=>s+(+n||0),0);
/* 반지 상자 결과: c.dropOut / c.mdropOut = {'보스|반지상자': ['r4'|'c4'|'x', ...]} (획득 순서). 개수보다 결과가 적으면 그만큼 '미기록'(기능 도입 전 획득분) */
const RING_KEYS = new Set(['r_green','r_red','r_black','r_white','r_life']);
const isRing = k => RING_KEYS.has(k);
const outMap = (c,type) => type==='monthly' ? (c.mdropOut||(c.mdropOut={})) : (c.dropOut||(c.dropOut={}));
const cleanOut = m => Object.fromEntries(Object.entries(m||{}).filter(([,a])=>Array.isArray(a)&&a.length).map(([k,a])=>[k,a.filter(o=>o==='r4'||o==='c4'||o==='gl'||o==='x'||/^cb:\w+$/.test(o))]));
const OUT_LABEL = {r4:'리4', c4:'컨4', gl:'생명의 연마석', x:'꽝'}; // gl = 생명 반지 상자에서 나온 생명의 연마석
/* 파티 인원: 이번 주/이번 달의 획득 기록은 그 캐릭터의 해당 보스 '파티 인원' 설정을 따릅니다 (드롭다운을 바꾸면 이번 기간 기록 표시도 바뀜).
 * 주간/월간 초기화로 기록에 저장될 때 키에 인원이 고정됩니다: 'boss|item'(1인) / 'boss|item#N'(N인 분배) */
const curParty = (c,slot) => { const cfg=c?.bosses?.[slot], b=findBoss(slot); return Math.max(1, Math.min(b?partyMax(b,cfg?.diff||b.diffs[0]):CONFIG.MAX_PARTY, parseInt(cfg?.party)||1)); };
const MODE_TXT={w:'블빵승리',l:'블빵패배'};
const partyTxt = (p,m) => p>1 ? ` (${p}인 ${MODE_TXT[m]||'분배'})` : '';
const partyHtml = (p,m) => p>1 ? ` <span class="ptx ptx-${m||'s'}">(${p}인 ${MODE_TXT[m]||'분배'})</span>` : '';
// 'boss|item', 'boss|item#3', 'item', 'item#2' → {slot, it, party}
function parseIK(k){ const [a,pp]=String(k).split('#'); const mode=/^\d+([wl])$/.exec(pp||'')?.[1]||''; const i=a.indexOf('|'); return {slot:i>=0?a.slice(0,i):'', it:i>=0?a.slice(i+1):a, party:Math.max(1,parseInt(pp)||1), mode}; }
// 이번 기간 획득 기록 → 현재 파티 인원을 붙인 키
function charDrops(c,type){
  const m=type==='monthly'?c.mdrops:c.drops, om=type==='monthly'?c.mdropOut:c.dropOut, rm=(type==='monthly'?c.mdrev:c.drev)||{}, I={}, O={}, V={};
  for(const [k,n] of Object.entries(m||{})){ if(!(+n>0)) continue; const slot=k.split('|')[0], p=curParty(c,slot), md=p>1?((type==='monthly'?c.mdmode:c.dmode)||{})[k]:'', key=p>1&&md!=='n'?`${k}#${p}${md==='w'||md==='l'?md:''}`:k;
    I[key]=+n; const l=(om||{})[k]; if(Array.isArray(l)&&l.length) O[key]=l.filter(o=>o==='r4'||o==='c4'||o==='gl'||o==='x'||/^cb:\w+$/.test(o));
    const r=rm[k]; if(r&&+r.m>0) V[key]={m:+r.m,a:+r.a||0,p:+r.p||1,i:String(r.i||k.split('|')[1])}; }
  return {items:I, outcomes:O, revs:V};
}
const charAllDrops = c => { const w=charDrops(c,'weekly'), m=charDrops(c,'monthly'); return {items:{...w.items,...m.items}, outcomes:{...w.outcomes,...m.outcomes}, revs:{...w.revs,...m.revs}}; };
const CHAOS_PICK = ['lcm','eye','belt','book','terror','cfe','sos'];
const hasOut = it => isRing(it)||it==='chaosbox';
const chaosHtml = (outs,n) => { const l=(outs||[]).filter(o=>/^cb:/.test(o)).map(o=>o.slice(3)).filter(k=>ITEMS[k]);
  return l.map(k=>`<span class="cbx">${miniIcon('chaosbox')} - ${itemIcon(k)}<span class="dln">${esc(ITEMS[k].n)}</span></span>`).join('') + (n>l.length?`<span class="cbx muted">${miniIcon('chaosbox')} - 미기록 ${xN(n-l.length)}</span>`:''); };
function openChaos(key){
  const c=activeChar(); if(!c) return; document.querySelector('#chaosModal')?.remove();
  const el=document.createElement('div'); el.id='chaosModal'; el.className='modal-bg show cbmodal'; el.setAttribute('role','dialog'); el.setAttribute('aria-modal','true');
  el.innerHTML=`<div class="modal cbbox"><h3>어떤 장신구를 획득하셨나요?</h3><div class="cblist">${CHAOS_PICK.map(k=>`<button class="cbopt" data-cbpick="${k}">${itemIcon(k)}<span>${esc(ITEMS[k].n)}</span></button>`).join('')}</div><button class="btn ghost cbcancel" data-cbpick="">취소</button></div>`;
  document.body.appendChild(el);
  el.onclick=e=>{ const t=e.target.closest('[data-cbpick]'); if(!t&&e.target!==el) return; el.remove(); const k=t?t.dataset.cbpick:'';
    if(!k){ if(pend&&pendSig(S)===pendSig(pend.base)) pend=null; render(); return; }
    const cc=S.characters.find(x=>x.id===c.id); const b=findBoss(key.split('|')[0]); if(!cc||!b) return;
    pendStart(); askBbang(cc,b,key,()=>{ dropMap(cc,b.type)[key]=1; outMap(cc,b.type)[key]=['cb:'+k]; },()=>askRev(cc,b,key,'cb:'+k,()=>celebrate(null,k,b)),{ico:itemIcon(k),name:ITEMS[k].n}); };
}
const OUT_NAME = {r4:'리스트레인트 링 4레벨', c4:'컨티뉴어스 링 4레벨'};
const miniIcon = k => ITEM_ICONS[k] ? `<img class="ric" src="${ITEM_ICONS[k]}" alt="" width="32" height="32" aria-hidden="true">` : '';
const outIcon = o => o==='r4'?miniIcon('ring_restraint'):o==='c4'?miniIcon('ring_continuous'):o==='gl'?miniIcon('g_life'):'';
const xN = n => 'x'+n;
/* b221: 이번 주 수익 총합 줄 = 이름 칸(고정 너비) + 개수 칸 xN — 주보·검마 결정석·획득 아이템·반지 상자·남은 결정석 개수가 한 세로줄 */
const rpLbl = (lb,n,z) => `<span class="tsmn rplb">${esc(lb)}</span>${n>0||z?`<span class="tsmn rpx">${xN(n)}</span>`:''}`; // 개수 표기 공통: '리4 x1', '컨4 x3' (0개는 표시하지 않음 — b225: z 면 x0 도 표시)
/* b226: '이번주 획득 아이템' 개수 — 일반 아이템 = 개수, 반지 상자 = 결과가 리4(r4)·컨4(c4)·생명의 연마석(gl)인 것만 (꽝 x·미기록은 아래 '반지 상자' 줄에만). 판매 금액(drev 'ring:r4' 등)과 같은 기준 */
const itemCnt = (k,v,om) => { if(!(+v>0)) return 0; if(!isRing(parseIK(k).it)) return +v; const t=outTally((om||{})[k],v); return Math.min(+v,t.r4+t.c4+t.gl); };
function outTally(list, n){ const t={r4:0,c4:0,gl:0,x:0,un:0}; (list||[]).forEach(o=>{ if(o in t) t[o]++; }); t.un=Math.max(0,(+n||0)-(list||[]).length); return t; }
// 순서대로: '미기록 · 리4 · 꽝' / compact: '리4×2 · 꽝×3 · 미기록×1'
function outHtml(list, n, compact){
  list=list||[]; const t=outTally(list,n); const parts=[];
  if(compact){ for(const o of ['r4','c4','gl','x']) if(t[o]) parts.push(`<span class="ro ro-${o}">${outIcon(o)}${OUT_LABEL[o]} ${xN(t[o])}</span>`); }
  else { if(t.un) parts.push(`<span class="ro ro-un">미기록 ${xN(t.un)}</span>`); list.forEach(o=>parts.push(`<span class="ro ro-${o}">${outIcon(o)}${OUT_LABEL[o]}</span>`)); }
  if(compact&&t.un) parts.push(`<span class="ro ro-un">미기록 ${xN(t.un)}</span>`);
  return parts.length?`<span class="routs">${parts.join('<span class="rsep"> · </span>')}</span>`:'';
}
// 주간 기록: 주간 보스 결정석 수익 + 주간 보스 획득 아이템 (월간 보스는 monthSummary 로 따로)
function weekSummary(wid){
  const a=allRevenue();
  const perChar=a.per.map(p=>({id:p.c.id, name:p.c.name, job:p.c.job, world:p.c.world, meso:p.r.meso, count:p.r.wlist.length, bosses:p.r.wlist.map(bossTag), bvals:p.r.wlist.map(x=>x.counted?x.value:0), ...(sp=>({items:cleanItems(sp.items), outcomes:cleanOut(sp.outcomes), ...(Object.keys(sp.revs).length?{revs:sp.revs}:{})}))(charDrops(p.c,'weekly'))}));
  return {week:wid, weeklyOnly:true, total:a.total, cleared:a.per.reduce((s,p)=>s+p.r.wlist.length,0), crystals:a.count, items:perChar.reduce((s,p)=>s+itemSum(p.items),0), perChar};
}
function monthSummary(mid){
  const a=allRevenue();
  return {month:mid, total:a.monthTotal, cleared:a.per.reduce((s,p)=>s+p.r.mlist.length,0),
    perChar:a.per.filter(p=>p.r.mlist.length||itemSum(cleanItems(p.c.mdrops))).map(p=>({id:p.c.id, name:p.c.name, meso:p.r.monthMeso, bosses:p.r.mlist.map(bossTag), bvals:p.r.mlist.map(x=>x.counted?x.value:0), mweeks:p.r.mlist.map(x=>typeof p.c.monthly[x.slot]==='string'?p.c.monthly[x.slot]:''), mdates:p.r.mlist.map(x=>(p.c.mdate||{})[x.slot]||''), ...(sp=>({items:cleanItems(sp.items), outcomes:cleanOut(sp.outcomes), ...(Object.keys(sp.revs).length?{revs:sp.revs}:{})}))(charDrops(p.c,'monthly'))}))};
}
/* 획득 아이템 줄 (모든 화면 공통 형식): [아이콘] 아이템 이름 (N인 분배) ×개수 · 반지 상자는 결과 집계(리4·컨4·꽝·미기록)
 * byBoss: 보스별로 따로 (보스 이름 표시) / 기본: 아이템 + 인원별 합계 */
function dropLine(it, party, n, outs, boss, mode, diff, bp){ // b126: bp = 보스 객체 → 이름 앞에 bossPic(아이콘+난이도 배지, 이번 주 수익 주보 게이지 밑과 같은 크기)
  const dtx=diff&&D[diff]?` (${D[diff]})`:'', bh=boss?`<span class="dlb">${bp?bossPic(bp,diff,false):''}${esc(boss)}${dlvHtml(diff)?' '+dlvHtml(diff):''}</span>`:'';
  const I=ITEMS[it];
  if(it==='chaosbox') return `<span class="dl cbl">${bh}${chaosHtml(outs,n)}${partyHtml(party,mode)}</span>`;
  return `<span class="dl ${party>1?'pty':''}${mode?' md-'+mode:''}" title="${esc((boss?boss+dtx+' · ':'')+I.n+partyTxt(party,mode))} ${xN(n)}">${bh}<span class="dlt">${lootLabel(it,{cls:'dln',name:esc(I.n),extra:partyHtml(party,mode),n,n1:1,xc:'dlc'})}${isRing(it)?' '+outHtml(outs,n,true):''}</span>${it==='chaosbox'?chaosHtml(outs,n):''}</span>`;
}
// 슬롯 → 현재 설정 난이도(캐릭터) / 기록의 보스 태그 '이름(난이도)'(주간·월간 기록)
const cfgDiff = c => slot => { const b=findBoss(slot), d=c?.bosses?.[slot]?.diff; return b&&b.diffs.includes(d)?d:''; };
const tagDiff = (p,c) => slot => { const b=findBoss(slot); if(!b) return ''; for(const t of (p&&p.bosses)||[]){ const m=/^(.+?)\((.+?)\)/.exec(t); if(m&&m[1]===b.name&&DK[m[2]]) return DK[m[2]]; } return cfgDiff(c)(slot); };
function itemsInline(items, opts={}){
  const agg={}, outs={}, meta={};
  for(const [k,n] of Object.entries(items||{})){ const {slot,it,party,mode}=parseIK(k); if(!ITEMS[it]||!(+n>0)) continue;
    const a=(opts.byBoss?slot+'|':'')+it+'#'+party+mode; meta[a]={slot,it,party,mode};
    agg[a]=(agg[a]||0)+(+n); if(hasOut(it)) (outs[a]=outs[a]||[]).push(...((opts.outs||{})[k]||[]));
    const rv=(opts.revs||{})[k]; if(rv&&+rv.m>0) meta[a].rev=(meta[a].rev||0)+(+rv.m); }
  const bi=s=>{ const i=BOSSES.findIndex(b=>b.id===s); return i<0?999:i; }, ii=it=>Object.keys(ITEMS).indexOf(it);
  const ks=Object.keys(agg).sort((x,y)=>{ const X=meta[x], Y=meta[y]; return (opts.byBoss?bi(X.slot)-bi(Y.slot):0) || ii(X.it)-ii(Y.it) || X.party-Y.party || String(X.mode).localeCompare(String(Y.mode)); });
  if(!ks.length) return opts.empty??'';
  if(opts.bpic&&opts.byBoss){ // b131: 이번 주 수익 — 같은 보스·난이도끼리 묶음: 보스 아이콘·이름 1번, 아이템은 세로로, 합친 금액은 마지막 아이템 밑에 1번
    const G=[]; for(const a of ks){ const sl=meta[a].slot; let g=G[G.length-1]; if(!g||g.slot!==sl) G.push(g={slot:sl,ks:[],rev:0}); g.ks.push(a); g.rev+=meta[a].rev||0; }
    return `<span class="dls">${G.map(g=>{ const b=findBoss(g.slot), d=opts.diffOf?opts.diffOf(g.slot):'';
      const bh=`<span class="dlb">${b?bossPic(b,d,false):''}${esc(b?.name||'')}${dlvHtml(d)?' '+dlvHtml(d):''}</span>`;
      const rows=g.ks.map(a=>{ const {it,party,mode}=meta[a]; return dropLine(it,party,agg[a],outs[a],'',mode,'').replace('<span class="dl','<span class="dl dli'); }).join('');
      return `<span class="dl dlg">${bh}<span class="dlcol">${rows}${g.rev?`<span class="dlrev">${meso(g.rev)}</span>`:''}</span></span>`; }).join('')}</span>`;
  }
  return `<span class="dls">${ks.map(a=>{ const {slot,it,party,mode,rev}=meta[a]; const h=dropLine(it,party,agg[a],outs[a],opts.byBoss?(findBoss(slot)?.name||''):'',mode,opts.byBoss&&opts.diffOf?opts.diffOf(slot):'',opts.bpic&&opts.byBoss?findBoss(slot):null); if(rev&&opts.bpic&&h.includes('<span class="dlt">')){ // b128: 이번 주 수익 — 금액을 보스 초상화 밑이 아니라 아이템(아이콘·이름) 바로 밑에
      const i=h.lastIndexOf('</span>'); return h.replace('<span class="dlt">','<span class="dlcol"><span class="dlt">').slice(0,i+'<span class="dlcol">'.length)+`<span class="dlrev">${meso(rev)}</span></span>`+'</span>'; }
    return rev?`<span class="dlw">${h}<span class="dlrev">${meso(rev)}</span></span>`:h; }).join('')}</span>`;
}
const fmtMonth = m => { const [y,mm]=String(m).split('-'); return `${y}년 ${+mm}월`; };

/* =====================================================================
 *  넥슨 Open API
 *  - GET /maplestory/v1/character/list            : 계정 캐릭터 목록 (본인 API 키)
 *  - GET /maplestory/v1/id?character_name=         : ocid 조회
 *  - GET /maplestory/v1/character/basic?ocid=      : 기본 정보 (이미지, 월드, 레벨 등)
 *  - GET /maplestory/v1/scheduler/character-state?ocid= : 스케줄러 (보스 완료 여부, 자기 계정 캐릭터만)
 * ===================================================================== */
const API_ERR = {OPENAPI00001:'서버 내부 오류',OPENAPI00002:'권한이 없습니다',OPENAPI00003:'유효하지 않은 식별자(캐릭터)',OPENAPI00004:'파라미터 누락 또는 유효하지 않음',
  OPENAPI00005:'유효하지 않은 API 키입니다',OPENAPI00006:'유효하지 않은 게임 또는 API 경로',OPENAPI00007:'API 호출량 초과 — 잠시 후 다시 시도하세요',
  OPENAPI00009:'데이터 준비 중',OPENAPI00010:'게임 점검 중',OPENAPI00011:'API 점검 중'};
const sleep = ms => new Promise(r=>setTimeout(r,ms));
let lastCall=0; const keyCalls={}; // b107: 키별 최근 호출 시작 시각 (슬라이딩 창)
async function rateGate(key){ // 같은 키로 1.1초 안에 5건이 이미 시작됐으면 자리가 날 때까지 기다림 (동시 호출도 순서대로 자리 예약)
  const q=keyCalls[key]||(keyCalls[key]=[]);
  for(;;){ const now=Date.now(); while(q.length&&now-q[0]>=CONFIG.API_RATE_WIN_MS) q.shift();
    if(q.length<CONFIG.API_RATE_N){ q.push(now); lastCall=now; return; }
    await sleep(q[0]+CONFIG.API_RATE_WIN_MS-now+5); }
}
/* b107: 작업들을 동시에 최대 n개씩 실행 (호출 속도 자체는 rateGate가 키별로 지킴) */
async function pool(items,n,fn){ let i=0; const run=async()=>{ while(i<items.length){ const x=items[i++]; await fn(x); } };
  await Promise.all(Array.from({length:Math.min(n,items.length)},run)); }
/* ---------- 넥슨 계정(API 키) ----------
 * character/list · scheduler 는 '키 소유 계정'의 캐릭터만 조회되므로 캐릭터마다 소속 계정(accId)의 키를 사용 */
const accounts = () => S.settings.accounts;
const accById = id => accounts().find(a=>a.id===id);
/* b72: 키가 등록되지 않은 계정(계정 칸은 있는데 key 없음)의 캐릭터는 화면 어디에도 안 보임 — 데이터(보스·수익·순서)는 그대로 두고,
 * 그 계정 키를 다시 등록하면 그대로 다시 보임. 연결 = c.accId(계정 칸 id; 키를 다시 넣으면 keyRelink/svAfterLogin 이 같은 칸에 넣음).
 * 계정 연결이 없는(수동 추가) 캐릭터·없는 계정을 가리키는 캐릭터는 보임. 지난 기록(history·누적 수익)은 숨긴 캐릭터 것도 유지·합산. */
/* b102: 삭제한 부계정 = 계정 칸 자체를 지움(키·ah·이름 등 흔적 없음). 그 캐릭터 기록만 남기고 숨김 — 칸 id 는 S.settings.goneAccs 에만 (캐릭터 연결용) */
const goneAcc = id => (S.settings.goneAccs||[]).includes(id);
const charShown = c => { if(!c||!c.accId) return true; if(goneAcc(c.accId)) return false; const a=accById(c.accId); return !a||!!a.key; };
function accForget(list){ const ids=list.map(x=>x.id); S.settings.goneAccs=[...new Set([...(S.settings.goneAccs||[]),...ids])].slice(-200); S.settings.accounts=accounts().filter(x=>!ids.includes(x.id)); ids.forEach(id=>{ if(listCache[id]) delete listCache[id]; }); }
const vchars = () => S.characters.filter(charShown);
/* b235: 🔄 캐릭터 동기화 버튼을 30일 동안 안 누른 계정 → 기록 삭제 (본계정 포함, 관리자 제외). b234 의 '키 삭제 30일' 기준을 대체.
 * S.settings.syncAt = {계정 칸 id: 마지막으로 동기화가 끝난 시각(ms)} — 상태와 함께 동기화. b236: 🔄·열 때·F5·키 등록 등 끝난 syncAll 마다(syncPressMark) 동기화된 칸 = 지금.
 * 기록이 없는 칸(기존 데이터·새 칸) = 처음 본 때부터 셈(지금) → 배포 직후 바로 지워지는 계정 없음. (b236: 자동 동기화도 셈) 로그인·로그아웃·다른 기기 세션 자체는 타이머와 무관.
 * 키 삭제(부계정)·로그아웃(본계정)은 타이머를 시작/멈추지 않음. 키가 빠진 칸은 🔄 로 갱신되지 않으므로 계속 셈.
 * 같은 넥슨 계정에 새 키를 등록하면 keyRelink(b64·b219)가 같은 칸/새 칸으로 다시 연결 → 기록 그대로·합계에 다시 포함(syncAt 도 새 칸으로 이어감).
 * 30일(30×24시간)이 지나면 purgeChars: 그 칸 캐릭터와 지난 기록(history·monthHistory perChar, missW/missM list)을 지우고 합계 다시 계산.
 * 서버 모드: Worker 도 users.last_sync_at(POST /api/sync-press) 기준 30일 → 사용자 데이터 전부 삭제(syncGoneCron, 관리자 제외). */
const SYNC_GONE_MS = 30*864e5;
function syncAtMap(){ const m=S.settings.syncAt; if(m&&typeof m==='object'&&!Array.isArray(m)) return m; return (S.settings.syncAt={}); }
function syncPressMark(t=Date.now(),bad=new Set()){ const m=syncAtMap(); accounts().filter(a=>a.key&&!bad.has(a.id)).forEach(a=>{ m[a.id]=t; }); save(); // b236: 끝난 동기화마다(자동·F5·키 등록·🔄) — 동기화된(키 있고 오류 없는) 칸만
  try{ if(typeof SV_ON!=='undefined'&&SV_ON&&svTok()) svFetch('/api/sync-press',{method:'POST',body:{}}).catch(()=>{}); }catch(e){} }
function syncTimerMove(from,to){ const m=syncAtMap(); if(m[from]!=null&&from!==to){ m[to]=Math.max(+m[to]||0,+m[from]||0); } }
function purgeChars(ids){ // ids = Set(캐릭터 id). 캐릭터와 그 기록을 실제로 지움
  if(!ids.size) return false;
  const names=new Set(S.characters.filter(c=>ids.has(c.id)).map(c=>c.name));
  S.characters=S.characters.filter(c=>!ids.has(c.id));
  const left=new Set(S.characters.map(c=>c.name)), gone=x=>x&&(x.id?ids.has(x.id):(names.has(x.name)&&!left.has(x.name)));
  const fixRec=arr=>(arr||[]).flatMap(h=>{ const pc=h.perChar||[]; if(!pc.some(gone)) return [h];
    const k=pc.filter(x=>!gone(x)); if(!k.length) return [];
    const o={...h, perChar:k, total:k.reduce((x,p)=>x+(+p.meso||0),0), cleared:k.reduce((x,p)=>x+((p.bosses||[]).length||+p.count||0),0), items:k.reduce((x,p)=>x+itemSum(p.items),0)};
    if(h.crystals!=null) o.crystals=k.reduce((x,p)=>x+(p.bvals||[]).filter(v=>v>0).length,0); return [o]; });
  S.history=fixRec(S.history); S.monthHistory=fixRec(S.monthHistory);
  const hw=new Set(S.history.map(h=>h.week)), hm=new Set(S.monthHistory.map(h=>h.month));
  const fixMiss=(arr,f,has)=>(arr||[]).flatMap(r=>{ const l=r.list||[]; if(!l.some(gone)) return [r]; const k=l.filter(x=>!gone(x));
    if(!k.length&&!has.has(r[f])) return []; return [{...r, list:k, n:k.reduce((a,x)=>a+(+x.n||0),0), meso:k.reduce((a,x)=>a+(+x.meso||0),0)}]; });
  S.missW=fixMiss(S.missW,'week',hw); S.missM=fixMiss(S.missM,'month',hm);
  if(ids.has(S.activeId)) S.activeId=S.characters[0]?.id||null;
  if(S.dq) ['charOff','hide'].forEach(k=>{ const o=S.dq[k]; if(o) for(const x of Object.keys(o)) if(ids.has(x)||(names.has(x)&&!left.has(x))) delete o[x]; });
  return true; }
function syncGoneTick(now=Date.now()){ let ch=false;
  if(S.settings.keyGoneAt){ delete S.settings.keyGoneAt; ch=true; } // b234 예약은 버림 (b235 = 동기화 버튼 기준)
  try{ if(typeof svIsAdmin==='function'&&svIsAdmin()) return ch; }catch(e){} // 관리자 제외
  const m=syncAtMap(), used=new Set(S.characters.map(c=>c.accId).filter(Boolean));
  for(const id of used){
    if(!(+m[id]>0)){ m[id]=now; continue; } // 처음 셈 = 다음 저장 때 함께 저장(이것만으로 서버 저장 안 함)
    if(now-m[id]<SYNC_GONE_MS) continue;
    const ids=new Set(S.characters.filter(c=>c.accId===id).map(c=>c.id));
    if(purgeChars(ids)) console.info('b235: 30일 동안 캐릭터 동기화 안 한 계정 기록 삭제',ids.size);
    delete m[id]; S.settings.goneAccs=(S.settings.goneAccs||[]).filter(x=>x!==id); ch=true; }
  for(const id of Object.keys(m)) if(!used.has(id)&&!accById(id)) delete m[id]; // 캐릭터·칸 없는 id 정리
  return ch; }
/* b82 규칙: 모든 합계·표·차트(지금·앞으로의 모든 탭)는 '지금 보이는(키 등록된) 캐릭터'만 — visibleCharIds() / visHist().
 * 저장된 기록(S.history·monthHistory)은 지우지 않고 볼 때마다 캐릭터 id 로 걸러 합계를 다시 계산 → 키를 다시 넣으면 합계도 그대로 돌아옴.
 * (b72 의 '지난 기록은 숨긴 캐릭터 것도 합산' 결정을 대체. 지금 목록에 없는(삭제된) 캐릭터의 기록도 빠짐) */
const visibleCharIds = () => new Set(vchars().map(c=>c.id));
/* zosu-apikey: 공용 필터 헬퍼 — 새 탭·집계는 이것만 쓰면 키 삭제(키 없음·goneAccs) 캐릭터가 자동 제외. 저장 데이터는 안 지움(키 다시 넣으면 복귀).
 * activeChars() = 보이는 캐릭터 목록 · activeIds() = 그 id Set · activeRecords(h) = 기록 1개(perChar) 걸러 합계 다시 계산 · activeMiss(r) = 빠뜨린 보스메소 기록 1개 거름 */
const activeChars = () => vchars();
const activeIds = () => visibleCharIds();
const activeRecords = (h,ids=activeIds()) => visHist(h,ids);
function activeMiss(r,ids=activeIds()){ const list=r.list||[]; // 예전 기록은 id 없이 이름만 → 숨은 캐릭터 이름이고 보이는 캐릭터 중엔 없으면 제외
  const vis=new Set(S.characters.filter(c=>ids.has(c.id)).map(c=>c.name)), hid=new Set(S.characters.filter(c=>!ids.has(c.id)).map(c=>c.name));
  const keep=list.filter(x=>x&&(x.id?ids.has(x.id):!(hid.has(x.name)&&!vis.has(x.name))));
  if(keep.length===list.length) return r;
  return {...r, list:keep, n:keep.reduce((a,x)=>a+(+x.n||0),0), meso:keep.reduce((a,x)=>a+(+x.meso||0),0)}; }
function visHist(h,ids=visibleCharIds()){ const pc=(h.perChar||[]).filter(p=>p&&p.id&&ids.has(p.id));
  if(pc.length===(h.perChar||[]).length) return h;
  return {...h, perChar:pc, total:pc.reduce((x,p)=>x+(+p.meso||0),0), cleared:pc.reduce((x,p)=>x+((p.bosses||[]).length||+p.count||0),0),
    crystals:pc.reduce((x,p)=>x+(p.bvals||[]).filter(v=>v>0).length,0), items:pc.reduce((x,p)=>x+itemSum(p.items),0)}; }
const accOf = c => c && c.accId ? accById(c.accId) : null;
const hasApi = () => accounts().some(a=>a.key);
const anyKey = () => accounts().find(a=>a.key)?.key || '';
const needAssign = c => !!c.ocid && !accOf(c);
/* 응답: { account_list:[ { account_id, character_list:[ {ocid, character_name, world_name, character_class, character_level} ] } ] }
 * 한 넥슨 ID 아래 메이플 계정(account_id)이 여러 개일 수 있으므로 모든 account_list 항목을 합친다. */
const listCache={}; // accId → {all, accounts, at}
async function listAccount(a){
  const d=await nx('/maplestory/v1/character/list',{},a.key);
  const accs=Array.isArray(d?.account_list)?d.account_list:[];
  const seen=new Set(), all=[];
  accs.forEach((x,i)=>{ (Array.isArray(x?.character_list)?x.character_list:[]).forEach(ch=>{
    if(!ch) return; const name=String(ch.character_name||'').trim(); const id=String(ch.ocid||'');
    if(!id&&!name) return; const k=id||('n:'+name+'|'+ch.world_name); if(seen.has(k)) return; seen.add(k);
    all.push({ocid:id,character_name:name,world_name:String(ch.world_name||''),character_class:String(ch.character_class||''),character_level:Number(ch.character_level)||0,account_id:String(x?.account_id||''),accIdx:i});
  }); });
  listCache[a.id]={all,accounts:accs.length,at:Date.now(),key:a.key};
  a.status={ok:true,count:all.length,accounts:accs.length,at:Date.now(),msg:''};
  return all;
}
const flagOn = v => v===true || String(v).toLowerCase()==='true';
/* 오류 원인 안내 (공식 응답 코드표: openapi.nexon.com/ko/guide/request-api/) */
const API_HINT = {
  NETWORK:['인터넷 연결을 확인하세요.','회사·학교·PC방 네트워크나 광고 차단 같은 브라우저 확장 프로그램이 open.api.nexon.com 을 막고 있을 수 있습니다. 확장 프로그램을 끄거나 다른 네트워크에서 다시 시도해 보세요.'],
  OPENAPI00005:['키를 복사할 때 앞뒤 공백이나 일부 글자가 빠지지 않았는지 확인하세요.','넥슨 Open API → 내 애플리케이션 → 애플리케이션 상세에서 현재 키를 다시 복사하세요. 재발급했다면 이전 키는 더 이상 쓸 수 없습니다.'],
  OPENAPI00002:['이 키로 이 API를 호출할 권한이 없습니다. 애플리케이션 상세에서 키 상태와 사용 게임(메이플스토리)을 확인하고, 필요하면 키를 재발급하세요.'],
  OPENAPI00007:['호출량 초과입니다. 개발 단계(test_) 키는 초당 5회·하루 1,000회까지입니다. 잠시 후(또는 내일) 다시 시도하세요.'],
  OPENAPI00009:['넥슨 쪽 데이터가 준비 중입니다. 잠시 후 다시 시도하세요.'],
  OPENAPI00010:['게임 점검 중입니다. 점검이 끝난 뒤 다시 시도하세요.'],
  OPENAPI00011:['API 점검 중입니다. 잠시 후 다시 시도하세요.'],
  OPENAPI00001:['넥슨 서버 내부 오류입니다. 잠시 후 다시 시도하세요.'],
};
function errHtml(e, a){
  const hints=API_HINT[e.code]||(e.status===403?API_HINT.OPENAPI00002:e.status===429?API_HINT.OPENAPI00007:['잠시 후 다시 시도하고, 계속되면 아래 코드를 확인하세요.']);
  return `<b>⚠ '${esc(a?.label||'')}' 캐릭터 목록 조회 실패</b>
    <div class="errcode">HTTP ${e.status===0?'— (응답 없음)':esc(e.status??'?')} · ${esc(e.code||'코드 없음')}${API_ERR[e.code]?' · '+esc(API_ERR[e.code]):''}</div>
    ${e.apiMsg?`<div>서버 메시지: <code>${esc(e.apiMsg)}</code></div>`:(e.status===0?`<div>${esc(e.message)}</div>`:'')}
    <ul>${hints.map(h=>`<li>${esc(h)}</li>`).join('')}</ul>`;
}
function emptyHtml(a){
  return `<b>'${esc(a.label)}' 키로 조회한 계정 캐릭터가 0명입니다.</b> (API 호출은 정상 · HTTP 200)
    <ul><li><b>키를 발급한 넥슨 ID</b>와 게임 캐릭터가 있는 넥슨 ID가 같은지 확인하세요. 캐릭터 목록은 <b>키를 발급한 본인 계정</b>의 캐릭터만 내려줍니다.</li>
    <li>키가 <b>test_</b>(개발 단계)로 시작한다면 본인 계정 데이터가 비어 있다는 사용자 보고가 있습니다. 애플리케이션을 <b>서비스 단계(live_)</b> 키로 다시 발급해 보세요.</li>
    <li>방금 만든 캐릭터나 키는 반영까지 시간이 걸릴 수 있습니다(게임 데이터 평균 15분). 잠시 후 [다시 불러오기]를 눌러 보세요.</li>
</ul>`;
}
/* 소속 계정이 없는 캐릭터를 이 계정의 캐릭터 목록과 ocid(없으면 이름+월드)로 매칭해 배정 */
function assignFromList(a, all){
  let n=0;
  S.characters.forEach(c=>{
    if(c.accId && c.accId!==a.id) return;
    const m=all.find(x=>c.ocid?x.ocid===c.ocid:(x.character_name===c.name&&(!c.world||x.world_name===c.world)));
    if(!m) return;
    if(!c.accId){ c.accId=a.id; n++; }
    c.ocid=m.ocid; c.name=m.character_name; c.world=m.world_name; c.job=m.character_class; c.level=m.character_level;
  });
  return n;
}
async function testAccount(a, quiet){ // (조용한 확인용) — 화면에서는 openImport()가 목록과 오류를 직접 보여줌
  try{ const all=await listAccount(a); const n=assignFromList(a,all); save(); render();
    if(!quiet) toast(`✓ ${a.label} 연결 성공 — 계정 캐릭터 ${all.length}명`+(n?` · 기존 캐릭터 ${n}명 이 계정으로 연결`:''));
    return true;
  }catch(e){ a.status={ok:false,msg:e.message,at:Date.now()}; save(); render(); if(!quiet) toast(`${a.label} 연결 실패: ${e.message}`); return false; }
}
/* 예비 API 키 (2026-10-10): 계정마다 1개 (a.bk, 같은 넥슨 계정 키만). 기본 키가 호출량/한도 초과(HTTP 429 · OPENAPI00007)면
 * 같은 요청을 예비 키로 다시 보내고, 그날(KST) 끝까지 그 계정은 예비 키 사용. 키 값은 로그·화면에 남기지 않음 */
const BK_DAY_KEY='mapleBossTracker.bkDay';
const isQuotaErr = e => !!e && (e.status===429 || e.code==='OPENAPI00007' || /quota|한도/i.test(e.apiMsg||''));
const bkDays = () => { try{ return JSON.parse(localStorage.getItem(BK_DAY_KEY)||'{}')||{}; }catch(e){ return {}; } };
const bkOn = a => bkDays()[a.id]===dayId();
const bkSet = a => { const d=bkDays(); for(const k in d) if(d[k]!==dayId()) delete d[k]; d[a.id]=dayId(); localStorage.setItem(BK_DAY_KEY,JSON.stringify(d)); };
async function nx(path, params={}, keyArg){
  const key=(keyArg||'').trim(), a=key&&typeof S!=='undefined'?accounts().find(x=>x.bk&&x.key===key):null;
  if(a&&bkOn(a)) return nxRaw(path,params,a.bk);
  try{ return await nxRaw(path,params,key); }
  catch(e){ if(a&&isQuotaErr(e)){ bkSet(a); return nxRaw(path,params,a.bk); } throw e; }
}
/* 남은 호출 수(추정): 넥슨은 남은 양을 알려 주지 않으므로 이 브라우저에서 보낸 호출을 키별·KST 날짜별로 셈 (키는 해시로만 저장) */
const QUOTA_KEY='mapleBossTracker.callCount', DAILY_LIMIT=1000;
const keyTag = k => { let h=2166136261; for(const ch of String(k)) { h^=ch.codePointAt(0); h=Math.imul(h,16777619)>>>0; } return h.toString(36); };
const quotaGet = () => { try{ const q=JSON.parse(localStorage.getItem(QUOTA_KEY)||'null'); if(q&&q.day===dayId()) return q; }catch(e){} return {day:dayId(),c:{},x:{}}; };
const quotaBump = (k,over,sec) => { const q=quotaGet(), t=keyTag(k); q.c[t]=(q.c[t]||0)+1; if(over) q.x[t]=1; if(sec){ (q.s||(q.s={}))[t]=Date.now(); } try{ localStorage.setItem(QUOTA_KEY,JSON.stringify(q)); }catch(e){} };
const quotaOk = k => { const q=quotaGet(), t=keyTag(k); if(!q.x[t]&&!(q.s||{})[t]) return; delete q.x[t]; if(q.s) delete q.s[t]; try{ localStorage.setItem(QUOTA_KEY,JSON.stringify(q)); }catch(e){} };
const quotaOf = k => { const q=quotaGet(), t=keyTag(k); return {used:q.c[t]||0, over:!!q.x[t], sec:Date.now()-((q.s||{})[t]||0)<60e3}; };
const quotaHtml = (k,switched) => { if(!k) return ''; const {used,over}=quotaOf(k), left=Math.max(0,DAILY_LIMIT-used);
  const sec=!over&&quotaOf(k).sec; // b112: 초당 한도(잠깐) ≠ 오늘 한도
  return `<span class="quota${over?' over':''}${sec?' sec':''}" title="이 브라우저에서 오늘(KST) 이 키로 보낸 호출 수로 계산한 추정치">${sec?`초당 호출 제한 — 잠시 후 자동 재시도 · 남은 호출 약 ${left}/${DAILY_LIMIT}`:over?`호출 한도 도달${switched?' → 예비 키 사용 중':''}`:`남은 호출 약 ${left}/${DAILY_LIMIT}`}</span>`; };
async function nxRaw(path, params={}, keyArg, retried){
  const key=(keyArg||'').trim(); if(!key) throw new Error('API 키가 설정되지 않았습니다');
  await rateGate(key);
  const qs=new URLSearchParams(Object.entries(params).filter(([,v])=>v!=null&&v!=='')).toString();
  let res;
  try{ res=await fetch(CONFIG.API_BASE+path+(qs?'?'+qs:''),{headers:{'x-nxopen-api-key':key,'accept':'application/json'}}); }
  catch(e){ const err=new Error('네트워크 오류 — 인터넷 연결 또는 브라우저 확장 프로그램·네트워크의 차단 여부를 확인하세요.'); err.status=0; err.code='NETWORK'; throw err; }
  let body=null; try{ body=await res.json(); }catch(e){}
  const q429=res.status===429||body?.error?.name==='OPENAPI00007';
  /* b112: 429 는 초당 한도일 때가 대부분 → 1.2초 쉬고 1번 다시. 다시 보내도 429 일 때만 '오늘 한도 도달'(하루 표시·예비 키 전환) */
  if(q429&&!retried){ quotaBump(key,false,true); await sleep(1200); return nxRaw(path,params,keyArg,true); }
  quotaBump(key, q429);
  if(res.ok&&body&&!q429) quotaOk(key); /* b115: 호출 성공 = 한도 아님 → '호출 한도 도달'·초당 제한 표시 풂 */
  if(!res.ok || !body || typeof body!=='object'){
    const n=body?.error?.name||'', m=body?.error?.message||'';
    const err=new Error(`${API_ERR[n]||(res.ok?'응답을 해석할 수 없습니다':'요청 실패')} (HTTP ${res.status}${n?' · '+n:''})${m?' — '+m:''}`);
    err.code=n; err.status=res.status; err.apiMsg=m; err.path=path; throw err; }
  return body;
}
const normName = s => String(s||'').replace(/[\s()·:\[\]「」]/g,'').toLowerCase();
const DIFF_MAP = {easy:'easy','이지':'easy',normal:'normal','노말':'normal','노멀':'normal',hard:'hard','하드':'hard',chaos:'chaos','카오스':'chaos',extreme:'extreme','익스트림':'extreme'};
const normDiff = s => DIFF_MAP[String(s||'').trim().toLowerCase()] || null;
// 2026-06 패치로 일일 보스가 되었거나 삭제되어 추적하지 않는 보스 (부분 일치로 '진 힐라' 등에 잘못 붙지 않도록 먼저 걸러냄)
const RETIRED_BOSS_NAMES = ['힐라','핑크빈','시그너스','카오스핑크빈'].map(normName);
function matchBoss(apiName){
  const n=normName(apiName); if(!n) return null;
  if(RETIRED_BOSS_NAMES.includes(n)) return null;
  const names=b=>[b.name,...(b.aliases||[])].map(normName);
  let hit=BOSSES.find(b=>names(b).includes(n)); if(hit) return hit;
  let best=null,len=0;
  // API 이름이 프리셋 이름을 '포함'할 때만 부분 일치 (예: '주시자 더스크' → 더스크). 반대 방향('힐라' ⊂ '진힐라')은 허용하지 않음
  for(const b of BOSSES) for(const a of names(b)) if(a.length>len && a.length>=2 && n.includes(a)){best=b;len=a.length;}
  return best;
}
/* 시즌 한정 보스 (예: '시즌 보스 메이린') — 주간 보스 표에 없는 것이 정상이므로 매칭 실패로 표시하지 않음 */
const isSeasonBoss = n => /시즌|메이린/.test(String(n||''));
/* 스케줄러 응답을 캐릭터에 반영. 완료된 보스만 체크(수동 체크는 지우지 않음). */
/* b241: 주간 보스 12개(한도)를 이번 주에 다 잡은 캐릭터 = 스케줄러 등록 변경(새 보스·난이도)은 목 리셋 때 적용.
 * c.bossNext = {보스 id: {enabled, diff}} — 캐릭터 안이라 저장·서버/드라이브 동기화·다른 기기에 그대로. resetCore(주간 초기화, rollPeriod 포함)가 적용 후 지움.
 * 한도 미만이면 예전처럼 바로 적용(대기 중이던 것도 다음 applyScheduler 때 바로). */
const bossNextNote = c => { const l=Object.entries(c.bossNext||{}).map(([id,v])=>{ const b=findBoss(id); return b?`${b.name}${v?.enabled===false?' 빼기':v?.diff&&D[v.diff]?`(${D[v.diff]})`:''}`:''; }).filter(Boolean);
  return l.length?`<div class="bnext muted tiny" title="이번 주 주간 보스 ${S.settings.weeklyLimit}개를 다 잡아서 스케줄러 변경은 다음 주부터 적용">⏳ 스케줄러 변경 ${esc(l.join(', '))} — 목요일 초기화 때 적용</div>`:''; };
/* b241: 스케줄러 주간 보스 등록이 12개(한도)를 넘으면 어디서나 12개만 — 이번 주 처치한 보스는 항상 포함, 나머지는 1인당 결정석 가격 높은 순.
 * bossOn(c,b) = 켜져 있고(enabled) 주간이면 weeklyShown 안. 월간(검마)은 세지 않음. */
function weeklyShown(c){ const lim=S.settings.weeklyLimit;
  const l=BOSSES.filter(b=>b.type==='weekly'&&c.bosses?.[b.id]?.enabled).map(b=>{ const cfg=c.bosses[b.id], d=b.diffs.includes(cfg.diff)?cfg.diff:b.diffs[0]; return {id:b.id,done:!!c.weekly?.[b.id],v:Math.floor(price(b,d)/Math.max(1,Math.min(partyMax(b,d),cfg.party||1)))}; });
  if(l.length<=lim) return null; l.sort((a,b)=>(b.done-a.done)||(b.v-a.v)); return new Set(l.slice(0,lim).map(x=>x.id)); }
const weeklyOver = c => !!weeklyShown(c);
const bossOn = (c,b) => { if(!c.bosses?.[b.id]?.enabled) return false; if(b.type!=='weekly') return true; const s=weeklyShown(c); return !s||s.has(b.id); };
const weeklyFull = c => weeklyCount(c)>=S.settings.weeklyLimit;
function bossNextPut(c,b,v){ (c.bossNext||(c.bossNext={}))[b.id]=v; }
function bossNextApply(c){ const n=c.bossNext; if(!n) return 0; let k=0;
  for(const [id,v] of Object.entries(n)){ const b=findBoss(id); if(!b) continue; const cfg=c.bosses[id];
    const diff=b.diffs.includes(v?.diff)?v.diff:(cfg?.diff&&b.diffs.includes(cfg.diff)?cfg.diff:b.diffs[0]);
    c.bosses[id]={enabled:v?.enabled!==false,diff,party:cfg?.party||1}; try{ clampParty(c,id); }catch(e){} k++; }
  delete c.bossNext; return k; }
function applyScheduler(c, data){
  const d=String(data?.date||'').slice(0,10);
  const staleWeek = d && d < S.period.week, staleMonth = d && d.slice(0,7) < S.period.month;
  /* b242: 이번 주 응답이면 대기(bossNext)를 응답 기준으로 다시 계산. adds = 새로 등록된(안 켜진·안 잡은) 주간 보스, clrEdit = 이번 주 잡은 보스의 등록 해제·난이도 변경(→ 대기).
   *  잡은 보스를 건드렸거나(clrEdit) 12개 다 잡았으면(weeklyFull) 새 등록은 빈 칸(12 - 켜진 수)만큼 가격 높은 순으로 바로, 나머지는 대기. 아니면 예전처럼 전부 바로. */
  if(!staleWeek&&c.bossNext) delete c.bossNext; const adds=[], clrEdit={};
  const unmatched=[]; let checked=0;
  const isDone = r => flagOn(r.complete_flag) || flagOn(r.clear_flag); // 공식 스펙: complete_flag (일부 문서는 clear_flag 표기)
  const rows=(data?.boss_contents||[]).slice().sort((a,b)=>isDone(b)-isDone(a));
  const seen={}, regYes={}, regNo={}; // b136: 스케줄러 등록 목록(registration_flag) — 클리어 여부와 무관
  for(const r of rows){
    const cyc=String(r.cycle||'').toLowerCase();
    if(/daily|일일|일간/.test(cyc)) continue; // 일일 보스는 추적하지 않음
    const b=matchBoss(r.content_name), diff=normDiff(r.difficulty);
    if(!b && RETIRED_BOSS_NAMES.includes(normName(r.content_name))) continue; // 일일 보스로 바뀐 보스
    if(!b && isSeasonBoss(r.content_name)) continue; // 시즌 보스(메이린 등)는 추적 대상이 아님 — '매칭 안 된 보스'에서 제외
    if(!b || !diff || !b.diffs.includes(diff)){ unmatched.push(`${r.content_name}(${r.difficulty||'?'})`); continue; }
    if(seen[b.id]){ if(b.type==='weekly'&&!staleWeek&&c.weekly[b.id]&&flagOn(r.registration_flag)&&!isDone(r)&&diff!==c.bosses[b.id]?.diff) clrEdit[b.id]={enabled:true,diff}; continue; } // b242: 잡은 보스 난이도 변경 = 대기
    const done=isDone(r), reg=flagOn(r.registration_flag), hasReg=r.registration_flag!=null&&r.registration_flag!=='';
    if(reg) regYes[b.id]=b; else if(hasReg&&!done) regNo[b.id]=b;
    const cfg=c.bosses[b.id];
    if(done){
      // b133: 지난 주/달 완료로 남은 응답이면 이번 클리어로 치지 않음. 예전에 continue 만 해서 registration_flag 를
      //  못 보고 seen 에 안 넣음 → 목 리셋(c.weekly={}) 직후 동기화 때 '스케줄러에 없다'로 등록이 전부 꺼졌음.
      if((b.type==='weekly'&&staleWeek)||(b.type==='monthly'&&staleMonth)){
        if(reg){ seen[b.id]=true;
          if(b.type==='weekly'&&!c.weekly[b.id]&&weeklyFull(c)&&!(cfg?.enabled&&cfg.diff===diff)){ bossNextPut(c,b,{enabled:true,diff}); continue; } // b241
          c.bosses[b.id]={enabled:true,diff,party:cfg?.party||1}; clampParty(c,b.id); }
        continue;
      }
      seen[b.id]=true;
      if(b.type==='weekly'&&hasReg&&!reg) clrEdit[b.id]={enabled:false}; // b242: 잡은 보스를 스케줄러에서 뺌 = 이번 주는 그대로(클리어 표시), 목 리셋 때 끔
      c.bosses[b.id]={enabled:true,diff,party:cfg?.party||1}; clampParty(c,b.id);
      if(b.type==='weekly'){ if(!c.weekly[b.id]){ checked++; (c.wat||(c.wat={}))[b.id]=Date.now(); } c.weekly[b.id]=true; }
      else { if(!c.monthly[b.id]) checked++; c.monthly[b.id]=c.monthly[b.id]||S.period.week; (c.mdate||(c.mdate={}))[b.id]=(c.mdate||{})[b.id]||kstDay(); }
      c.auto[b.id]=true;
    } else if(reg){ // 스케줄러에 등록된 보스 = 이 캐릭터의 보스 (난이도도 API 값, 파티 인원은 유지)
      seen[b.id]=true;
      if(b.type==='weekly'&&!staleWeek&&!c.weekly[b.id]&&!cfg?.enabled){ adds.push({b,diff,cfg}); continue; } // b242: 새 등록은 아래에서 (빈 칸만큼 바로, 나머지 대기)
      if(b.type==='weekly'&&!staleWeek&&c.weekly[b.id]&&cfg?.enabled&&cfg.diff!==diff){ clrEdit[b.id]={enabled:true,diff}; continue; } // b242: 잡은 보스 난이도 변경 = 대기
      c.bosses[b.id]={enabled:true,diff,party:cfg?.party||1}; clampParty(c,b.id);
    }
  }
  // 보스 목록은 스케줄러만 따름: 매칭된 보스가 1개라도 있을 때만, 거기 없는 보스는 끔 (이번 주/달 이미 체크한 건 유지, 파티·드롭 기록은 남김).
  // b133: boss_contents 가 일일만 있거나 매칭 실패만 있으면 seen 이 비어 전부 끄던 것 방지 — 매칭된 게 있을 때만 끔.
  // b134: 이번 주 응답(date ≥ 이번 주 시작)일 때만 끔 — 접속 안 한 캐릭터의 지난 주 응답(stale)은 등록 판단 근거가 아님(등록은 그대로 둠)
  // b136: 동기화 때 등록이 전부 꺼지던 원인 — seen 에 '이번 달 클리어한 검마'(월간)만 있어도 registration_flag 가 안 온(clear_flag 만 온)
  //  안 잡은 주간 보스를 전부 껐음 (+ isDone(c,b) 가 응답 행용 isDone 에 가려져 '체크한 건 유지'도 안 됐음).
  //  사용자 규칙: 스케줄러 등록 보스는 항상 라인업에, 클리어 플래그는 클리어 표시만, 목 리셋은 클리어 표시만 지움.
  //  → 동기화는 등록을 켜기만 하고 절대 끄지 않음 (빼려면 사용자가 직접 끔). regYes/regNo 는 기록용.
  // b242: 예외 — 이번 주 응답에서 registration_flag 가 명시적으로 'false'(regNo)인 주간 보스는, 이번 주에 안 잡았고 같은 응답에 등록(true) 보스가 있을 때만 끔
  //  (스케줄러에서 안 잡은 보스를 다른 보스로 바꾼 경우 → 바로 적용. b136 의 '플래그 없음'은 regNo 에 안 들어가므로 그대로 안전). 난이도·파티 인원은 남김.
  // b250 버그 수정: 스케줄러 응답은 보스마다 난이도 줄이 전부 옴(등록 안 한 난이도 = 'false'). 예전엔 다른 난이도의 'false' 줄 하나만 있어도 regNo 에 들어가
  //  등록된 보스(예: 스우 익스트림 true, 노말/하드 false)를 끄거나(목 리셋 뒤 12개 → 몇 개만) 잡은 보스를 '빼기' 대기에 넣었음. 같은 보스의 어떤 난이도든 등록(true)이면 regNo 아님.
  for(const id of Object.keys(regYes)){ delete regNo[id]; if(clrEdit[id]&&clrEdit[id].enabled===false) delete clrEdit[id]; }
  if(!staleWeek&&Object.values(regYes).some(b=>b.type==='weekly')) for(const [id,b] of Object.entries(regNo)){
    if(b.type!=='weekly'||!c.bosses[id]?.enabled) continue; if(c.weekly[id]){ clrEdit[id]=clrEdit[id]||{enabled:false}; continue; } c.bosses[id].enabled=false; }
  if(!staleWeek){ // b242
    const hold=Object.keys(clrEdit).length>0||weeklyFull(c), val=a=>Math.floor(price(a.b,a.diff)/Math.max(1,Math.min(partyMax(a.b,a.diff),a.cfg?.party||1)));
    let free=hold?Math.max(0,S.settings.weeklyLimit-BOSSES.filter(x=>x.type==='weekly'&&c.bosses[x.id]?.enabled).length):Infinity;
    adds.sort((x,y)=>val(y)-val(x));
    for(const a of adds){ if(free>0){ c.bosses[a.b.id]={enabled:true,diff:a.diff,party:a.cfg?.party||1}; clampParty(c,a.b.id); free--; } else bossNextPut(c,a.b,{enabled:true,diff:a.diff}); }
    for(const [id,v] of Object.entries(clrEdit)) bossNextPut(c,findBoss(id),v);
  }
  c.sync=Object.assign(c.sync||{},{at:Date.now(),ok:true,msg:'',clear:data?.weekly_boss_clear_count,limit:data?.weekly_boss_clear_limit_count,unmatched,date:d});
  if(data?.character_level) c.level=data.character_level;
  if(data?.character_class) c.job=data.character_class;
  if(data?.world_name) c.world=data.world_name;
  return checked;
}
// character/basic 의 character_exp(int64, 현재 레벨 보유 경험치) / character_exp_rate(string, 예 "51.234") 저장
function expFrom(b,fallbackLevel){
  const r=parseFloat(b?.character_exp_rate); if(!isFinite(r)) return null;
  return {rate:Math.max(0,Math.min(100,r)), exp:Number(b.character_exp)||0, level:Number(b.character_level)||Number(fallbackLevel)||0, date:b.date||'', at:Date.now()};
}
async function fetchBasic(c,key){
  const b=await nx('/maplestory/v1/character/basic',{ocid:c.ocid},key);
  const e=expFrom(b,c.level); if(e) c.exp=e;
  if(b.character_image) c.image=b.character_image;
  if(b.world_name) c.world=b.world_name;
  if(b.character_class) c.job=b.character_class;
  if(b.character_level) c.level=b.character_level;
  c.guild=String(b.character_guild_name||''); c.guildAt=Date.now(); // b85: 길드 현황 '+ 길드 추가' 후보
  c.sync=Object.assign(c.sync||{},{imgAt:Date.now()});
}
/* b86: '프리미엄 PC방' 훈장 감지 — /character/item-equipment 의 item_equipment(현재) + item_equipment_preset_1~3 전부에서
 * item_equipment_slot(또는 part) '훈장' 아이템 이름에 '프리미엄 PC방'이 있으면 c.medal.bad. 동기화 때마다 갱신 (캐릭터당 1회 호출) */
const MEDAL_BAD='프리미엄 PC방';
/* b190: 보스 프리셋 = 프리셋 1~3 중 장비 총 옵션 점수가 가장 높은 것(빈 프리셋 제외, 모두 같으면 현재 preset_no).
 * 점수 = (보공%+방무%+데미지%+올스탯%)×10 + 공격력+마력 + 주스탯(STR/DEX/INT/LUK 중 가장 큰 합)÷10. 그 프리셋 훈장이 '프리미엄 PC방'이거나 비어 있으면 경고 */
const isMedal = i => i&&(i.item_equipment_slot==='훈장'||i.item_equipment_part==='훈장');
function presetScore(l){ let p=0, st={str:0,dex:0,int:0,luk:0}; for(const i of l){ const o=i?.item_total_option||{}, n=k=>parseFloat(o[k])||0;
    p+=(n('boss_damage')+n('ignore_monster_armor')+n('damage')+n('all_stat'))*10+n('attack_power')+n('magic_power'); for(const k in st) st[k]+=n(k); }
  return p+Math.max(...Object.values(st))/10; }
function medalFrom(e){
  const P=[1,2,3].map(k=>({k,l:Array.isArray(e?.[`item_equipment_preset_${k}`])?e[`item_equipment_preset_${k}`].filter(Boolean):[]})).filter(x=>x.l.length);
  P.forEach(x=>x.sc=presetScore(x.l));
  let boss=null; if(P.length){ const top=Math.max(...P.map(x=>x.sc)), best=P.filter(x=>x.sc===top); boss=best.length===1?best[0]:(best.find(x=>x.k===+e?.preset_no)||P.find(x=>x.k===+e?.preset_no)||best[0]); }
  if(!boss){ const cur=Array.isArray(e?.item_equipment)?e.item_equipment:[]; if(!cur.length) return {bad:false,where:[],at:Date.now()}; boss={k:+e?.preset_no||0,l:cur}; }
  const m=boss.l.find(isMedal), pc=!!m&&String(m.item_name||'').includes(MEDAL_BAD);
  const nm=boss.k?`보스 프리셋 ${boss.k}`:'현재 장비';
  return {v:2, bad:pc||!m, empty:!m, preset:boss.k, where:[nm+(m?'':' (훈장 없음)')], at:Date.now()};
}
const medalTip = c => c.medal?.empty?`${(c.medal.where||[]).join(', ')} — 훈장 칸 비어 있음`:`'${MEDAL_BAD}' 훈장 착용: ${(c.medal.where||[]).join(', ')}`;
async function fetchMedal(c,key){ c.medal=medalFrom(await nx('/maplestory/v1/character/item-equipment',{ocid:c.ocid},key)); }
const medalBand = c => c.medal?.bad&&charShown(c) ? `<div class="medalwarn" title="${esc(medalTip(c))}" aria-label="훈장 잘못 착용중"><span>훈장 잘못 착용중</span></div>` : '';
let syncing=false, syncBg=null;
/* zosu-testfix: b184 뒤 작업(basic·훈장)은 넣을 때의 키를 기억 → 그 사이 캐릭터가 지워졌거나(S.characters 에 없음) 계정 키가 바뀌거나 지워졌으면 요청 안 함
 * (예전엔 실행 시점의 a.key 를 읽어 지운 캐릭터 ocid 를 다른 키로 계속 조회했음) */
const bgJob=(c,a,fn)=>{ const k=a.key; return ()=>{ if(!S.characters.includes(c)||a.key!==k||!k) return; return fn(c,k); }; };
const SYNC_CONC=6, SYNC_LIST_TTL_MS=10*60e3, SYNC_BASIC_TTL_MS=10*60e3, SYNC_BASIC_LOAD_TTL_MS=60*60e3 /* b112: 페이지 열 때(자동)는 레벨·이미지 1시간, 🔄 는 10분 */, SYNC_MEDAL_TTL_MS=6*3600e3; // b107
const LOAD_SYNC_GAP_MS=3e3, LOAD_SYNC_KEY='mapleBossTracker.loadSyncAt';
/* b218: API 키를 등록한 직후 1번 자동 동기화 (🔄 버튼과 같은 syncAll). 보이는 캐릭터가 있을 때만(새 사용자는 캐릭터를 고른 뒤 doImport 가 동기화),
 *  이미 동기화 중이면 건너뜀, 마지막 동기화·열 때 동기화가 3초(LOAD_SYNC_GAP_MS) 안이면 건너뜀 → 새로고침 동기화와 겹치지 않음 */
let keySyncPend=null;
function keySync(){ if(syncing||!hasApi()||demoAllowed()||!vchars().length) return false;
  const last=Math.max(+S.settings.lastSync||0,+localStorage.getItem(LOAD_SYNC_KEY)||0); if(Date.now()-last<LOAD_SYNC_GAP_MS) return false;
  try{ localStorage.setItem(LOAD_SYNC_KEY,String(Date.now())); }catch(e){} syncAll({silent:true}); return true; } // 페이지 열 때 자동 동기화 최소 간격 (아래 loadSyncDue)
async function syncAll(opts={}){
  if(syncing) return; if(!hasApi()){ if(!opts.silent) toast('+ 추가에서 넥슨 API 키를 먼저 등록하세요'); return; }
  syncing=true; renderHeaderSync(); syncLabel('run'); let total=0, errs=0, assigned=0; const badAcc=new Set(), accMsgs=[], bgList=[];
  try{
    // b107: 계정들은 키가 달라 동시에 (같은 키는 rateGate가 초당 5건 이하로). 목록은 10분 안에 받았고 모든 캐릭터 ocid가 있으면 건너뜀
    const vc=vchars(), fresh=a=>{ const L=listCache[a.id]; return L&&L.key===a.key&&Date.now()-L.at<SYNC_LIST_TTL_MS&&!opts.full&&vc.every(c=>c.accId!==a.id||c.ocid); };
    let netErr=null;
    await Promise.all(accounts().filter(a=>a.key).map(async a=>{
      if(fresh(a)) return;
      if(!opts.full&&vc.some(c=>c.accId===a.id)&&vc.every(c=>c.accId!==a.id||c.ocid)){ bgList.push(a); return; } // b184: 캐릭터 ocid 가 다 있으면 목록(새 캐릭터 확인)은 뒤에서
      try{ assigned+=assignFromList(a, await listAccount(a)); }
      catch(e){ a.status={ok:false,msg:e.message,at:Date.now()}; badAcc.add(a.id); accMsgs.push(`${a.label}: ${e.message}`); if(/네트워크/.test(e.message)) netErr=e; }
    }));
    if(netErr) throw netErr;
    // 2) 캐릭터별 (b107: 스케줄러 먼저 = 보스 체크가 가장 빨리 보이게, 끝난 캐릭터부터 화면 갱신). basic은 10분, 훈장은 6시간 안에 받았으면 건너뜀
    const todo=[];
    for(const c of vchars()){ // b72: 키 없는 계정의 (숨긴) 캐릭터는 동기화 안 함
      const a=accOf(c);
      if(!a){ if(c.ocid){ errs++; c.sync=Object.assign(c.sync||{},{at:Date.now(),ok:false,msg:'넥슨 계정 미지정 — 등록된 어느 계정의 캐릭터 목록에도 없습니다. ✎ 편집에서 계정을 선택하거나 해당 계정의 API 키를 추가하세요.'}); } continue; }
      if(!a.key||badAcc.has(a.id)){ errs++; c.sync=Object.assign(c.sync||{},{at:Date.now(),ok:false,msg:`'${a.label}' 계정 API 키 오류: ${a.status?.msg||'API 키 미등록'}`}); continue; }
      todo.push([c,a]);
    }
    let netN=0; const lb=[], later=[]; if(syncBg) await syncBg; // 앞 동기화의 뒤 작업이 남았으면 끝난 뒤 시작
    let rt=0; const paint=()=>{ if(rt) return; rt=setTimeout(()=>{ rt=0; renderChars(); },120); };
    await pool(todo, SYNC_CONC, async([c,a])=>{
      if(!c.ocid){ try{ c.ocid=(await nx('/maplestory/v1/id',{character_name:c.name},a.key)).ocid; }catch(e){ c.sync={...c.sync,ok:false,msg:'ocid 조회 실패: '+e.message}; errs++; return; } }
      try{ total+=await schedApply(c,a,opts.full?null:lb,opts.full); paint(); } // fetchSched: 같은 응답으로 일퀘/길드 요약도 저장
      catch(e){ errs++; if(e.code==='NETWORK') netN++; const hint=/OPENAPI0000[234]/.test(e.code||'')?` — 스케줄러 조회 불가: '${a.label}' 계정의 캐릭터가 아니거나 2026-06-25 이후 접속 기록이 없을 수 있어요. 수동 체크는 계속 가능합니다.`:''; c.sync=Object.assign(c.sync||{},{at:Date.now(),ok:false,msg:e.message+hint}); }
      const now=Date.now();
      if(opts.full||!(now-(c.sync?.imgAt||0)<(opts.silent?SYNC_BASIC_LOAD_TTL_MS:SYNC_BASIC_TTL_MS))) later.push(bgJob(c,a,fetchBasic)); // 이미지·레벨·EXP
      if(opts.full||!c.medal||c.medal.v!==2||!(now-(c.medal.at||0)<SYNC_MEDAL_TTL_MS)) later.push(bgJob(c,a,fetchMedal)); // b86: 훈장(모든 프리셋)
    });
    clearTimeout(rt);
    if(todo.length&&netN===todo.length) throw new Error('네트워크 오류 — 인터넷 연결 또는 브라우저 확장 프로그램·네트워크의 차단 여부를 확인하세요.'); // b184: 목록을 뒤로 미뤄도 전부 네트워크 오류면 '새로고침 실패'
    /* b184: 보스 체크(스케줄러)가 끝나면 바로 '완료' — 되짚기·레벨/이미지·훈장은 뒤에서 이어서 (같은 rateGate = 4건/1.1초 그대로) */
    if(lb.length||later.length||bgList.length) syncBg=(async()=>{ let bt=0; const bp=()=>{ if(bt) return; bt=setTimeout(()=>{ bt=0; renderChars(); },150); };
      for(const a of bgList){ try{ if(assignFromList(a, await listAccount(a))) bp(); }catch(e){} }
      await pool(lb,SYNC_CONC,async([c,a])=>{ try{ if(await schedLookback(c,a)) bp(); }catch(e){} });
      await pool(later,SYNC_CONC,async f=>{ try{ await f(); bp(); }catch(e){} });
      clearTimeout(bt); save(); if(!syncing) render(); })().finally(()=>{ syncBg=null; });
    S.settings.lastSync=Date.now(); save(); try{ svSyncDone(); }catch(e){} // b229: 관리자 창 '최근 갱신'
    try{ syncPressMark(Date.now(),badAcc); }catch(e){} // b236: 성공한 동기화(자동 포함) = 30일 삭제 타이머 다시 시작 + /api/sync-press
    // zosu: 성공 알림(toast) 대신 🔄 버튼 옆 초록 글자 '새로고침 완료!' (몇 초 뒤 사라짐). 실패(일부 캐릭터·계정 오류)는 계속 알림
    if(errs||accMsgs.length) toast((errs?`일부 캐릭터 동기화 실패 ${errs}`:'')+(errs&&accMsgs.length?' · ':'')+(accMsgs.length?`계정 오류: ${accMsgs.join(', ')}`:''));
    syncLabel(errs||accMsgs.length?'part':'ok');
  }catch(e){ syncLabel('fail'); if(!opts.silent) toast('동기화 실패: '+e.message); save(); }
  finally{ syncing=false; render(); }
}

/* =====================================================================
 *  길드 현황(지하 수로) — 스케줄러(/scheduler/character-state) 재사용
 *  스케줄러 응답 요약을 localStorage(SCHED_KEY)에 캐릭터별로 보관 → 동기화·탭 자동 갱신이 같은 캐시를 씀.
 *  실측(2026-10-09) 이름: daily_contents '[일일 퀘스트] 세르니움 조사' … '[일일 퀘스트] 기어드락 크로노스의 잔재 수집',
 *  '몬스터파크'(contents, now/max=…/14), weekly_contents '[몬스터파크] 익스트림 몬스터파커에 도전해보겠나?'(주간 퀘스트, now/max=…/5),
 *  '[길드] 지하 수로' · '[길드] 플래그 레이스' · '[길드] 주간 미션 포인트'(now_count = 이번 주 점수).
 *  quest_state: "2" 완료, "1" 진행 중, "0" 기타(미수락·미해금).
 * ===================================================================== */
const DQ_TTL_MS = 10*60e3;      // 스케줄러 캐시 기본 수명 (길드 탭)
const GUILD_TTL_MS = 30*60e3;   // 길드 랭킹: 하루 1번(09:30경) 갱신 데이터라 30분 캐시
/* b85: 고정 길드('봉사활동') 삭제 → 사용자가 고른 길드들 S.settings.guilds=[{world,name}] (동기화됨). 랭킹 캐시는 길드별 */
const SCHED_KEY = 'mapleBossTracker.sched', GUILD_KEY = 'mapleBossTracker.guild2';
const gKey = g => g.world+'|'+g.name;
const guildList = () => Array.isArray(S.settings.guilds)?S.settings.guilds:[];
const lsGet = k => { try{ return JSON.parse(localStorage.getItem(k)||'null'); }catch(e){ return null; } };
const lsSet = (k,v) => { try{ localStorage.setItem(k,JSON.stringify(v)); }catch(e){} };
let schedC = lsGet(SCHED_KEY) || {};   // charId → {date, level, items{id:{st,now,max,reg,name}}, guild{suro,flag,mission}, at, ok, msg}
let guildC = lsGet(GUILD_KEY) || {};    // gKey → {date, t1, t2, at, ok, msg}
const GUILD_MARK_TTL=7*864e5;
const guildMarkHtml=G=>{ const m=guildC[gKey(G)]?.mark; return m?.src?`<img class="gmark" src="${esc(m.src)}" alt="" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'gmark gmark0',textContent:'🛡️'}))">`:'<span class="gmark gmark0">🛡️</span>'; };
let guildPick=false, guildCandBusy=false;
let dqBusy=false, guildBusy=false, apiPauseUntil=0; // dqBusy = 스케줄러 갱신 중 (b119: 일퀘 탭 삭제 후 길드 탭만 씀)

function schedSummary(d){
  const weekly=Array.isArray(d?.weekly_contents)?d.weekly_contents:[];
  const nm=r=>normName(r?.content_name);
  const g=k=>{ const r=weekly.find(x=>nm(x).includes(k)); return r?{now:Number(r.now_count)||0,max:Number(r.max_count)||0}:null; };
  return {date:String(d?.date||'').slice(0,10)||dayId(), level:Number(d?.character_level)||0,
    guild:{suro:g('지하수로')} /* 2026-10-10: 플래그·주간 미션 표시 삭제 (같은 스케줄러 응답이라 API 호출 수는 그대로) */, at:Date.now(), ok:true, msg:''};
}
function schedPut(c,d){ schedC[c.id]=schedSummary(d); lsSet(SCHED_KEY,schedC); }
function schedErr(c,e){ schedC[c.id]={...(schedC[c.id]||{}),errAt:Date.now(),ok:false,msg:e.message,code:e.code||''}; lsSet(SCHED_KEY,schedC); }
/* 스케줄러 1회 호출 = 보스 자동 체크(applyScheduler) + 일퀘/길드 요약 저장 (동기화와 같은 경로) */
/* b137: 실제 넥슨 응답 확인 — 목 리셋 후 이번 주에 아직 접속 안 한 캐릭터는 오늘 응답의 boss_contents 에 주간 보스 행이 아예 없음
 * (검은 마법사 bossMonthly 2행만; 접속한 캐릭터는 80행, 각 행 registration_flag/complete_flag "true"/"false").
 * 그래서 등록을 켤 근거가 없어 라인업이 빈 채로 남았음 → 주간 행이 없으면 date= 어제…7일 전 응답(스케줄러 등록 목록)으로 등록만 켬
 * (지난 주 날짜라 클리어로는 안 침 — applyScheduler 의 staleWeek). 아직 준비 안 된 날짜(OPENAPI00009)는 건너뜀. */
const hasWeeklyRows = d => (d?.boss_contents||[]).some(r=>/weekly/i.test(String(r.cycle||'')));
/* b184: 지난 날짜 되짚기(이번 주 기록 찾기, 최대 7번 호출) 결과는 캐릭터·KST 날짜별로 기억 → 같은 날 다시 🔄 해도 다시 안 부름.
 * lb 배열을 주면(🔄) 되짚기는 바로 하지 않고 lb 에 넣어 '완료' 표시 뒤 뒤에서 처리 */
const lbCache={};
async function schedLookback(c,a,force){ const day=dayId(), hit=lbCache[c.id];
  if(!force&&hit&&hit.day===day&&hit.ocid===c.ocid){ if(hit.p){ const keep=c.sync; const n=applyScheduler(c,hit.p); c.sync=keep; return n; } return 0; }
  let found=null;
  for(let k=1;k<=7;k++){
    let p; try{ p=await nx('/maplestory/v1/scheduler/character-state',{ocid:c.ocid,date:dayId(Date.now()-k*864e5)},a.key); }
    catch(e){ if(e.code==='OPENAPI00009'||e.code==='OPENAPI00004') continue; return 0; } // 다른 오류는 기억 안 함(다음에 다시)
    if(hasWeeklyRows(p)){ found=p; break; }
  }
  lbCache[c.id]={day,ocid:c.ocid,p:found};
  if(!found) return 0; const keep=c.sync; const n=applyScheduler(c,found); c.sync=keep; return n; }
async function schedApply(c,a,lb,force){
  const d=await fetchSched(c,a); let n=0;
  const need=(d?.boss_contents||[]).length && !hasWeeklyRows(d); // 응답 자체가 비면(오류·빈 객체) 건너뜀
  if(need&&!lb) n+=await schedLookback(c,a,force);
  n+=applyScheduler(c,d);
  if(need&&lb){ const h=lbCache[c.id]; if(h&&h.day===dayId()&&h.ocid===c.ocid) n+=await schedLookback(c,a); else lb.push([c,a]); }
  return n;
}
async function fetchSched(c,a){
  try{ const d=await nx('/maplestory/v1/scheduler/character-state',{ocid:c.ocid},a.key); schedPut(c,d); return d; }
  catch(e){ schedErr(c,e); throw e; }
}
const schedOk = c => !!(c.ocid && accOf(c)?.key);
const schedFresh = (c,ttl) => { const x=schedC[c.id]; const t=Math.max(x?.at||0,x?.errAt||0); return !!x && Date.now()-t<ttl && (!x.ok||x.date===dayId()); };
/* 열려 있는 탭에 필요한 캐릭터만, 오래된 것만(ttl) 순서대로 갱신. 동기화 중·호출량 초과 대기 중이면 건너뜀 */
async function refreshSched(chars, ttl=DQ_TTL_MS){
  if(dqBusy||syncing||Date.now()<apiPauseUntil) return;
  const todo=chars.filter(c=>schedOk(c)&&!schedFresh(c,ttl)); if(!todo.length) return;
  dqBusy=true; renderTabView(); let n=0;
  try{
    for(const c of todo){
      try{ n+=await schedApply(c,accOf(c)); }
      catch(e){ if(e.code==='OPENAPI00007'||e.status===429){ apiPauseUntil=Date.now()+DQ_TTL_MS; break; } if(e.code==='NETWORK') break; }
      renderTabView();
    }
    save();
    if(n) toast(`스케줄러 갱신 — 새로 체크된 보스 ${n}개`);
  } finally { dqBusy=false; renderChars(); renderTabView(); }
}
/* 길드 랭킹: 오늘 날짜(09:30 KST 이후) → 비었거나 준비 전이면 어제 */
async function refreshGuild(force){
  if(guildBusy||Date.now()<apiPauseUntil) return; const key=anyKey(); if(!key) return;
  const todo=guildList().filter(G=>{ const c=guildC[gKey(G)]; const ttl=c?.ok&&c.date===dayId()?3*GUILD_TTL_MS:GUILD_TTL_MS; return force||!c||Date.now()-(c.at||0)>=ttl; });
  if(!todo.length) return;
  guildBusy=true; renderTabView();
  const k=kst(), ready=k.getUTCHours()*60+k.getUTCMinutes()>=9*60+30;
  const days=(ready?[dayId()]:[]).concat(dayId(Date.now()-864e5));
  try{
    for(const G of todo){
      let got=null, lastErr=null, stop=false;
      for(const d of days){
        const rows={};
        try{
          for(const t of [2,1]){
            const r=await nx('/maplestory/v1/ranking/guild',{date:d,world_name:G.world,ranking_type:t,guild_name:G.name},key);
            rows[t]=(Array.isArray(r?.ranking)?r.ranking:[]).find(x=>x&&x.guild_name===G.name&&(!x.world_name||x.world_name===G.world))||null;
          }
        }catch(e){ lastErr=e; if(e.code==='OPENAPI00007'||e.status===429||e.code==='NETWORK'){ stop=true; break; } continue; }
        if(rows[1]||rows[2]){ got={date:d,t1:rows[1],t2:rows[2]}; break; }
      }
      const kk=gKey(G), prevMark=guildC[kk]?.mark;
      guildC[kk]=got?{...got,at:Date.now(),ok:true,msg:''}:{...(guildC[kk]||{}),at:Date.now(),ok:false,msg:lastErr?lastErr.message:`'${G.world}' 월드 랭킹에서 '${G.name}' 길드를 찾지 못했습니다`};
      if(prevMark) guildC[kk].mark=prevMark;
      // b99: 길드 마크 — guild/id → guild/basic. guild_mark_custom(base64) 우선, 없으면 guild_mark(URL). 7일 캐시
      if(!stop&&(!prevMark||Date.now()-(prevMark.at||0)>=GUILD_MARK_TTL)){
        try{
          const id=await nx('/maplestory/v1/guild/id',{guild_name:G.name,world_name:G.world},key);
          if(id?.oguild_id){ const gb=await nx('/maplestory/v1/guild/basic',{oguild_id:id.oguild_id},key);
            const cu=typeof gb?.guild_mark_custom==='string'&&gb.guild_mark_custom.trim(), mk=typeof gb?.guild_mark==='string'&&gb.guild_mark.trim();
            guildC[kk].mark={src:cu?(cu.startsWith('data:')?cu:'data:image/png;base64,'+cu):(mk&&/^https:\/\//.test(mk)?mk:''),at:Date.now()}; }
        }catch(e){ if(e.code==='OPENAPI00007'||e.status===429||e.code==='NETWORK') stop=true; }
      }
      lsSet(GUILD_KEY,guildC); renderTabView();
      if(stop) break;
    }
  } finally { guildBusy=false; renderTabView(); }
}
/* '+ 길드 추가' 후보: 보이는 캐릭터의 (월드, 길드). 길드 정보가 아직 없는 캐릭터는 character/basic으로 한 번 채움 */
async function fillGuildCands(){
  if(guildCandBusy) return; const todo=activeChars().filter(c=>c.guildAt==null&&c.ocid&&accOf(c)?.key); if(!todo.length) return;
  guildCandBusy=true; renderTabView();
  try{ for(const c of todo){ try{ await fetchBasic(c,accOf(c).key); }catch(e){ if(e.code==='OPENAPI00007'||e.status===429||e.code==='NETWORK') break; } } save(); }
  finally{ guildCandBusy=false; renderTabView(); }
}
function guildCands(){ const have=new Set(guildList().map(gKey)), m=new Map();
  for(const c of activeChars()) if(c.guild&&c.world){ const G={world:c.world,name:c.guild}, k=gKey(G); if(have.has(k)) continue; const e=m.get(k)||{...G,chars:[]}; e.chars.push(c.name); m.set(k,e); }
  return [...m.values()]; }
/* 60초 타이머·탭 열기·화면 복귀 시 호출: 열려 있는 탭만 갱신 */
/* b206: 왼쪽 캐릭터 목록에서 캐릭터 클릭 = 어느 탭에 있든(라이브 포함) 이번 주 보스 탭으로 — 탭 버튼과 같은 정리(디지털 숫자 다시 세기·마지막 탭 기억). 바뀌었으면 true */
/* b213: 탭 바꿀 때 = 페이지 + 탭 내용 안 스크롤 칸 맨 위로 (바로, 애니메이션 없음). 왼쪽 캐릭터 목록(#charList)은 그대로 */
function tabTop(){ const go=()=>{ try{ window.scrollTo({top:0,left:0,behavior:'instant'}); }catch(e){ window.scrollTo(0,0); }
    const se=document.scrollingElement; if(se&&se.scrollTop) se.scrollTop=0;
    const v=document.getElementById('view'); if(v){ if(v.scrollTop) v.scrollTop=0; v.querySelectorAll('*').forEach(el=>{ if(el.scrollTop) el.scrollTop=0; }); } };
  go(); requestAnimationFrame(go); }
function toBossTab(){ if(tab==='boss') return false; TIR_LAST.clear(); TSV_SEEN.clear(); tab='boss'; try{ localStorage.setItem(TAB_KEY,tab); }catch(e){} syncTabs(); return true; }
function tabTick(){
  if(document.hidden) return;
  if(tab==='guild'){ refreshGuild(); refreshSched(suroChars()); }
}
/* b84: '지하 수로' 카드 — 본캐(★) 대신 사용자가 고른 캐릭터들(S.settings.suroChars, 동기화됨). 처음엔 기존 본캐로 채움. 보이는 캐릭터만 */
const SURO_ICON='data:image/webp;base64,UklGRoQIAABXRUJQVlA4WAoAAAAQAAAAPwAAPwAAQUxQSGABAAABkLtt2/E+eePkZ9u2bds2a3fqH6DJk93J2NrJtm3b7vPcRZyja4+ImACJuTVBpSvfQfeP0wt7M4M8HLVKmcRS5Q6h3XthKD/euWBMWXKIu51cmE8IhZ1XxpSzYNbHAPDm+oGlg2n+DiphFqlCZecanD646T0YBjMzALzaOTEvxFklE0YJpVarkQuhdPaLymyeu/cZQDCaiQh4d3B2ZbSnvVpumND4phdFemq1gQXzNu598BMghmmZADq/ZmJJhJdBQuXTdujC1pao2MatDADEMD0TgE/X1k7WI4REZu9XsxvAkSlzLwJEDHMTA/iiS65UKpziZqx6TT+J7/0AwzKZCAqZkAiVV3i4f+SsD5++QifBcjnQ3Vmt9CrZsauu+jQYfzPDkudPKw8NKNgJzJ96jUmHpX89NbNyyU+i83uewlqfbTwGhvUy4fs3AGBrARj/nX7n/GewVV099cHKCP9SVlA4IP4GAADwGwCdASpAAEAAPlEejEQjoaEY+c7YOAUEtQBOmWDpE1jA3Pv7PPok2zHmA8230Pf531AP8z1DvPy+xd+6HpLYErubxNcpPqCO1Sl4Td8PxDycbuOAD8x/uHfR6k3f3oo78qgB+e/Vi/u/HF9U+wN+vfW/9GL9sVdGI+dWOxVWADkrYSttRL/UvXL65jY8/ZYzXztC0thNaGLqv1ziBb6FAurElmGThHTmSfLxtQ6Ww6eGE/6k0+//Mt/duLMVOlV+Kx1zRoiW+xLlrdIq937LcBNBnuQbqNH8not5AddR0DxfErGx6aKAAP7/2If5xBAbxARNuoYDOKQPwJDmMvJCVm96Aof4F1vRFpbDL31SLjtdTvt9UIkOFtZzUB/i5HT2IPqMLLdax4LLSj+HS2+GqPmjidr5n5T71ImMVSm2qysaj29+k7M2CbCRks1Y/Rw/vEaCzAH8+Pn2d+dXclCTjGCs31tHIWSKIRfcyBpte7ZajQ+IOjo11KObSg8F5X39hginLuqk3tMQlHADudzv5gzrW2tiQnAirpg4eLcjc6eRdqS8iqaOEmmQvyPxXPgT0gFsI5LOAtvFshjoVgN5bC/NM4j9vz8FRmVmD++3cXgbBVLnxtWk+0f3ZGz5+cr0UJMKB8OWLUdjUrygypDqiwt4w+DXVZBR7EHaKPRXbSz3b29MpubH9WmcGgYqD2TK8/PJsuL7iyJm9WDFPXHqKFrbAFevZIuvHx/FTksqzCl5LB7KF1s5tuTafRv55SPyclaQQ/SfSP2sT+cE5OrUpvQofPOghdTtD0lWU8Pc+a2B4JKd9jmDUUFzbtPDO/skXTKDUOZzmNopyOD819XTVVc8I+h3RpKhzFh7oBk5FohOCXVLaDhDtQnRTf8GJa0wed51Ow5qKqpD2t7G/F25wSqmsZ4bkURppJsPHubao0leteb6zL1D2eoJFQLuE6wf2N1JH0H0lDrHJJInsNw+cCXHxIC1E+/sbibkeelR8e+6znJl4fZjLj+z8t26e+u0bJrZ8z6wnx288YOgM12yDkwpkRVPwAmFATPQr5o+h5a+b5kLSqNo6/4Zk0xvpvROZqL2SEr+AjsVDHkV3tIIbXX+RHlgMxdMEA3/Z//dm27fEfbBG5+lBbJUVRUiN5xhZbhI4fx/T+J6/F6XbnhaeZzH5hQKSoqWm14ft0Ubs20c0lXr871jpc91KSrWkhk3HYuYE/Q47bMhWza2gpX4HSKtPZzsWCbf0/h004ABLE0thSAi1Fz7K7ZGH8lDwTSg10l23thPIASOEZ4LAqIMK0goRXEuvYBL3khqWT0yh/NULafJqqVM+XxC0xvxUNql/w0GftR6aFTRbksSUf3FM1YNXvheiLI1EZ1dJRCTdaQLJvDnLY5sL7VjVd2eh+z08be09YiVRODi9xv2zIqnyqiOOK7+85hIFbr72OLG5lGAnhlXP2pBv/2Qqj+d4Ds4d/ouHjQXh5Jb0+//8beHmzgkoQWc2RPK7qn4+ohIlQU//Gy/qNiRNLY2EgVrywaQU88KlGwTCxM0yH5Vorj2sl8y7fMAFTiW0wU8Ei7jmWKX02FA/G1kpLuqdHnqpB8qe+9pIVT//U5/ypfTdR7btU4AzEp3QJzRplQ+K9BMwc7Sd9OdSRr1wCGZd/f3g71UlacaMr2h8svJCHobI3yP60sKhYbTnjh2sW9EvB5EzPaMerBEXhJ/TrANKvyrUjea7fQ8ZfCtcCs9aOPsvg2l+KcX5Juyw7kBGq3w39ZpNcKpPEjXlJ30seWDSbbLXbCVwnPrh9cGSx9232HrgyQwkDL5PE05mZ8hcNz8y+E28skxUGKowo8f5UkJEhQ4N6oEzP0AO8z5FQddlHe0j1yCzLh4y4CVxk0fqBfGTP0xDCuvRQ7Sg/dshFh1eUmcdVQMG0CIwBZjFL3A2klSHShE+Yl/l7sq0Y+D3sl7NjKBqXJ5k5H71YEiOuKPOPhC5xNP9yHsFME2H6RRFMoMGYoHiZud31Mx59tUxDzjG4C5liXBI9AxoIN0FvhLYw9gl/xYDGGhq5bO18OG7GKQRMFFU2v1qh94EJx7CAo168rptS3yLtSBNxDW2jrnMRr95tYXa7Gy3nHThTl+xw3B0O4kV1JwJ0CGPm8TPGpIxDqx8VyroBW0GldvT9ePAvONNzWqryKBcUdzDznQn0Sd7B5dTdJYVhq02z881fJvnDIOvtqbYHrxsuDR5dqdeEXyCCBAciek2AWEnEJ5/4s3k4+rZJ1snnHKLxB5XFLBBIRvDhGYMLZrltwgsnQDSyFG4B9m8i086EGmPc5ZnH4Q2k9JZhxJ8rO0M7sKrHAM+OXmaXhnVCso0XU7OwnxRSFVWEc1pYo07Kc2KxcKxEAAAA=='; // 수로 보스 '아르카누스' (MapStory Fandom Wiki Mob_Arcanus.png, 얼굴 위주 잘라 64px)
let suroPick=false;
function suroIds(){ const st=S.settings; if(!Array.isArray(st.suroChars)) st.suroChars=S.characters.filter(c=>c.isMain).map(c=>c.id); return st.suroChars; }
const suroChars=()=>{ const ids=suroIds(); return activeChars().filter(c=>ids.includes(c.id)).sort((a,b)=>ids.indexOf(a.id)-ids.indexOf(b.id)); };
function renderTabView(){ if(!vchars().length) return; if(tab==='guild') renderGuild(); }
const hhmm = t => { const d=kst(t); return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`; };
const num = n => (Number(n)||0).toLocaleString('ko-KR');
/* ---------- b157: 신창섭 라이브 탭 ----------
   Worker cron(매 1분)이 유튜브 @MapleStoryKR /live 와 넥슨 라이브 channels/23 을 확인해 D1 에 저장 → 여기서는 /api/live 만 읽음(외부 요청 없음).
   b224: 페이지를 열 때(새로 들어옴·새로고침·다시 불러오는 뒤로/앞으로, bfcache 복원 포함) 1번만 조회 — 30초 재조회 없앰(사용자 결정, 서버 비용). 라이브 탭은 받아 둔 값 사용.
   영상은 자동재생 없음(썸네일 ▶ 누르면 재생). */
const LIVE_API='https://ggoolzip-sync.bossmaple.workers.dev/api/live';
let LIVE=null;
async function liveFetch(){ try{ const r=await fetch(LIVE_API); /* b224: 서버 Cache-Control max-age=15 → 15초 안 새로고침은 브라우저 캐시(요청 0) */ if(!r.ok) return; LIVE=await r.json(); }catch(e){ return; }
  srvPricesApply(LIVE&&LIVE.feed&&LIVE.feed.prices); // b193: Worker 가 1분 안에 읽은 새 공지 가격
  feedSrvApply(LIVE&&LIVE.feed); // b170: 같은 응답에 넥슨 공지 빠른 감시 결과 포함(추가 요청 없음)
  const on=!!(LIVE&&((LIVE.yt&&LIVE.yt.live)||(LIVE.nx&&LIVE.nx.live))), b=document.getElementById('liveBadge'); if(b){ const was=!b.hidden; b.hidden=!on; if(on&&!was) liveReveal(b); }
  if(tab==='live'&&!document.querySelector('#view .lvplay.playing')) renderLive(); }
/* b161: 모바일에서 탭 줄이 옆으로 넘쳐 '신창섭 라이브' 탭(+LIVE)이 화면 밖이면, 라이브가 켜질 때 한 번 탭 줄을 밀어 보이게 함 */
function liveReveal(b){ const n=b.closest('.tabs'); if(!n||n.scrollWidth<=n.clientWidth+1) return; const go=()=>{ const t=b.parentElement.getBoundingClientRect(), r=n.getBoundingClientRect(); if(t.right>r.right-2||t.left<r.left) n.scrollLeft=n.scrollWidth; }; go(); setTimeout(go,600); setTimeout(go,2000); document.fonts&&document.fonts.addEventListener("loadingdone",go,{once:true}); }
window.addEventListener('pageshow',e=>{ if(e.persisted) liveFetch(); }); // b224: bfcache 로 돌아온 페이지 = 스크립트가 다시 안 돌므로 여기서 1번
const lvDate=t=>{ const d=new Date(t+KST_MS); return `${d.getUTCMonth()+1}/${d.getUTCDate()} ${String(d.getUTCHours()).padStart(2,'0')}:${String(d.getUTCMinutes()).padStart(2,'0')}`; };
/* b161: 라이브 없을 때 영상 자리 — 핑크빈(메이플 몹 8820001 stand, 출처 maplestory.io 렌더, 사이트 내장) */
const PINKBEAN='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAG0AAABZCAYAAAA0E6rtAAAJzklEQVR42u2d63GzOhCGX3u+BnRKUEogJYgSSAm4BFMCLsGUYJWASrBKsEqIStD5wcUChLnaBpydYSYhvoAedvfVaiHAn63OdiPfZ2b4jCWYmWk8Fg/NnI9XJDyBhoZSfG3wSlDp+VbuVErjcPpexXkMPUCTnm9IOM9PVAHAWuCZOighJKSS0FpDQ4NRD4mIFg/u39A3HKKDcz8lDJ7HwEVkFgbPFMd3js8QQt69S6tVxvTB0M7xGQnnoISCiwQA4HkMACCVRMhiAEDyfngNzzpEBwQsLGFprUsv2zS0wrhIKgOglAIBgVDZlfwmeJV8dYgOFc86x2ccokN5ka3VRkGTUlSAAQCltAQH4NXwGl5VN6UVEq4QsLCMEJR6HyH5TZEbCjFSh9llSovZBAslzBQeVAgL2xjznJ5FCc0vpFO5jxC6XSFST+Y2qICFrQm+eB0lrIBn5jqJOqzOSJFHAeYFVriPkCi+7ZxWQChAdakxy8PyucNl1PdqlYsGrfF9EmWech2HHQ7r3lYXISGLV+Flo6EVIqQLFM8GYRKkuhFKMnCElF5mg6sfj9JVcFrfleLaVOOkeVpbTqvDKkFRYl3i5aU+HZwVHgtw9hTEBY5SrwLuI4RIer5BCOn0sBLWLe0R56bD00rjO+IlpEJg1OePtgDhIgHJX2d72lpEyKScRgmtgOMiqsLKB6YKxgJE8l/zMDcGHrE92ArVRegu4BUApZIIWIhEnEpwHzNPc3mYuaVVUJXRJTkU4gZXec10q8OzASolQUCga5GCy/WUtAaHx/PxWhaKlVZVYIQ4Yph2/K5nDZVfP0lnlaMeGRrXVVYA2HZ47AWs1YNIe6h8gkjQWkNq+VA5shVVR/aTgKWXx8BscK6fZ7LbJeysxnQBW4uXjYYmpciA0SkASDfgGcCtXd7PAu2URLhdwgxYHy+byHCIXePgI8D9e8m3vGjQCCW4xgG+o2zi755I6w+FVnjZJGD6qeAAlPCyqEtbvzWxym2blPz3XEbuobEtRLqAuSba9V8neqZdVC7s+yRyESXmGosVQSurHqRdFbYNehuwZ0GrfVY9VGqVVfp9wVcFbT/Yy9o8Sev79kZgRYh0C1P3/pQFQLMHckOSX9d+6DPIfYG9wch09Wsc29Kg6eaIt3lZZV8PYDOqzNLbnjCZt2GZXwPza3C7Ztsl61N5KrwhcfweHglxzKvIcJU4Nix6DOjRj+ISJG15DcCQ3GbMr8kLDRo8kaD5RaLy71RKgsvnVFn2g4E9JODaZgZGveyiWVCtkHoU4dFDePRAKYFU8qmdXvvR79QT3jdFeJBpYW+OHFZ4WZvooYRASA6Phk8ROOMm1zrv0dADy09z5LAx0GZePVAqHwJ6D7lJku2UUkKVy0/PyafTy1i6I63poZWSB3msDooF2ee05Ld6L0mXpSyAL7jpk4eUUoC6H4+SClqrl9Q5J4THTBlyIbD79rPtywfnsjuljQQmhMButys3IUQGcmKb95iQKYWCFBJSyFzMqJcVpvdT3syFxE90quz7iSJwIVohjw2JQgj4vl/Z7fv+HdxISGTE8pIsvcre9D1lP/lunL5y1Kked/5P/sd7rt3tso+cq8+xCIPl57q+yxhA8NElrRGy3xyDFFLJ+hp8DizLZ1Ilb5X8H2M9SlqGEgalJDzqQWkJbW3PFCDzCZEPtAuj+BECUglnK17uYU/xsiGetitCYeXgj8cyTBWbvX9WD0hT53cV+yeXvfrlxTJNXBiF0gJSJY0th/W0VYNJ4TFgXgPQ5XhEwGauBmgNxlgDUJqmYIy9bGXctm9egVPfFhgereQeUDpYdESnE+Ih3igF4DEwxipCpBQX9fsKKBk9V1uD7ccA0/Xk2zEo9v1j0emEOL0iOp1aX9MKrq4QBQc4H3w8rkl4DzFiTHqBTMTbob1EiDDmIeEcSil40OD+F7wcIJDd+hsGwcAS2hO9pyO/WaFxJdAoAVFeazhqswKK7WHxGMFShzbyeNZs47uxRlo8VVkqmUFT8mMgbWNyLQU+2TZfEdmacnxtRWTs4uMGe/FfBc2MKgATYm10rKv0WiHgQiAIg8Fyv7UCczzCP53stbXdzv8xJr3gminIXutuixIiPOEImGMdi9JpkJqTqGb9tQCp7ksgUmkEHxAaJ4XHxiB53nyg+oKkHqAVfP8H6SWezcs2DE29HlYLQCFluwDRes7ex0WEyNG1xzS9YPffV7MW+GLb7XYwvzdA9n/U0trvV+st+ZeYH9qA2V7Ge8AceG67nf8DL2S4Bs9pkZsDmls5SgnzeyvXtZYI7CQEgjje3NTh34CYgqJfpayKW+BeGSZdwOq9ID9JgvR2y0Kh5wFCfB40oRUYaKm47/ntTYORA6v36/8X5Y96si8iSue/bt4oSHpDCxhDlHCcOMdvEXLeaLr2hB0XrErHleeBSPkRnlbJZ/E5Rny5NPLYqxWkMWbQMWitM2/bCLRhBeN8PmaMqWzvsFHHQMgmHk/RHxqlqz9ZvYFzGAaNrGuhsWzTtj3LAa0QMmvywH3v+RnZgKfNW9JauKeRDS3n/0FbUWgs/rZhaOb3fN7U1VkCtPLaGvNZp6eV1YYV5bNHXraVqLJ/cPabSWNP8KS3dhtvqhtrCJyHyzGUwM+aajvrie/oNt53jMJq+iz0gwe8VKx4NMF4L3x7T/9+7it4aR7mVJB6dD6rAHtXT/++x4hkHrdQcI3HJnV5kdXB5fy7u8XcADDXIHw7MOBBlV9rfb87UiuAeNV9C/SuXiGy7Z8mWOfl328SMQCKtoK35rFe0CrghIQOKEheJX8nuDYYemCe6npNHdRSgHV9ubnld7gQQqA9D6C0AewVAIfkrIevlRJEyOZrinPIVaMLWA7r7cA6Pa0yEEIAYVg5YVJbn5oLYJcXdIXG1qjRAcwBqO8FvhhPq3gbkC/Ze54jHbwuXA4FVv5NqSa0GrC+c7MleFrv/4pLpCwXEm1Qz/C2sR63dWDFQZqYUERZi9Wuj7fVFxPf7WkPXyNVs32ulsOWFv56QQtA4BFSgHNaF7hnARxUmqqLklx4lFLe8fysOC+GP7holwutsDAMnQPwkyfnEp7W0IwtpnekIfnzkGjDugRheVH5yQkxoZDW+3j2aLLd6qB5hIC0gNBKld7Y1/PeUg3JgRWwzrXnQR6kaABbE7gGtEfgtFUCcsEDpdnK8MwAh6jDImf5PClDH4DyfB4BWwu44sCc4OyTtYHZZufByqSUZrftzgmxAk8pEGXdDVoTF7Fj4TbSCkGPx/qtBVpZZ2uD18fqQuYahgAINMkGdXLfYR1Ui8BwAZMDBM2aoFXgfbjt/obgz/7sz/5sdfY/8HGz0sPs1XQAAAAASUVORK5CYII=';
function lvPlayer(src,o){ if(src==='nx'&&!(o&&o.ok)) return `<div class="lvcol"><div class="lvhd">넥슨 라이브 · 메이플스토리<span class="lvoff">새 창</span></div>
    <a class="lvplay lvext" href="https://live.nexon.com/channels/23" target="_blank" rel="noopener" aria-label="넥슨 라이브 메이플스토리 채널 새 창에서 열기"><div class="lvblank">넥슨 라이브는 사이트에 넣을 수 없어 새 창에서 열려요</div><span class="lvbtn" aria-hidden="true">▶</span></a>
    <div class="lvt"></div><a class="lvlink" href="https://live.nexon.com/channels/23" target="_blank" rel="noopener">https://live.nexon.com/channels/23</a></div>`;
  const L=o&&o.live, th=o&&o.thumb, url=(o&&o.url)||(src==='yt'?'https://www.youtube.com/@MapleStoryKR/streams':'https://live.nexon.com/channels/23');
  const embed=src==='yt'?(L&&o.vid?`https://www.youtube-nocookie.com/embed/${encodeURIComponent(o.vid)}?autoplay=1&rel=0`:''):(L?url:'');
  return `<div class="lvcol"><div class="lvhd">${src==='yt'?'유튜브 · 메이플스토리 공식':'넥슨 라이브 · 메이플스토리'}${L?'<span class="livebadge">LIVE</span>':'<span class="lvoff">방송 없음</span>'}</div>
    <div class="lvplay" ${embed?`data-embed="${esc(embed)}" data-src="${src}" role="button" tabindex="0" aria-label="재생"`:''}>${!L?`<div class="lvblank lvnone"><img class="pinkbean" src="${PINKBEAN}" alt="핑크빈"><span>라이브 일정이 없습니다.</span></div>`:th?`<img src="${esc(th)}" alt="" loading="lazy">`:'<div class="lvblank">지금은 라이브 방송이 없어요</div>'}${embed?'<span class="lvbtn" aria-hidden="true">▶</span>':''}</div>
    <div class="lvt">${L&&o.title?esc(o.title):''}</div><a class="lvlink" href="${esc(url)}" target="_blank" rel="noopener">${esc(url)}</a></div>`; }
function renderLive(){ const v=document.getElementById('view'); const D=LIVE||{}, since=Date.parse('2026-10-15T00:00:00+09:00');
  const L=(D.list||[]).filter(x=>(x.start_at||x.first_seen)>=since);
  v.innerHTML=`<div class="lvwrap"><div class="lvgrid lvone">${lvPlayer('yt',D.yt)}${(()=>{ const u=(D.nx&&D.nx.ok&&D.nx.live&&D.nx.url)||'https://live.nexon.com/channels/23'; return `<a class="lvlink lvnx" href="${esc(u)}" target="_blank" rel="noopener">넥슨 라이브: ${esc(u)}</a>`; })()}</div>
    <div class="card lvlist"><h2>라이브 저장소</h2>${L.length?`<ul>${L.map(x=>`<li><span class="lvsrc ${x.src}">${x.src==='yt'?'유튜브':'넥슨'}</span>${x.status==='LIVE'?'<span class="livebadge">LIVE</span>':x.status==='RESERVE'?'<span class="lvoff">예정</span>':''}<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.title||x.url)}</a><span class="muted tiny">${lvDate(x.start_at||x.first_seen)}</span></li>`).join('')}</ul>`:'<p class="muted">아직 기록된 라이브가 없어요</p>'}</div></div>`; }
document.addEventListener('click',e=>{ const p=e.target.closest('.lvplay[data-embed]'); if(!p||p.classList.contains('playing')) return; p.classList.add('playing');
  p.innerHTML=`<iframe src="${esc(p.dataset.embed)}" title="라이브 영상" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>`; });
document.addEventListener('keydown',e=>{ if((e.key==='Enter'||e.key===' ')&&e.target.matches?.('.lvplay[data-embed]')){ e.preventDefault(); e.target.click(); } });
setTimeout(liveFetch,0); // b224: 페이지 열 때 1번 (재조회 없음)
function renderGuild(){
  const v=$('#view'), g=guildC, mains=suroChars();
  const tile=(lbl,ico,r)=>`<div class="gtile"><div class="gk">${ico} ${lbl}</div>${r?`<div class="gv">${num(r.guild_point)}<small>점</small></div><div class="grk"><b>${num(r.ranking)}</b>위</div>`:`<div class="gv dim">기록 없음</div><div class="grk muted">랭킹 미등록</div>`}</div>`;
  const gblock=G=>{ const g=guildC[gKey(G)], info=g?.t2||g?.t1;
  const body=!hasApi()?'<div class="note">넥슨 API 키를 등록하면 길드 랭킹을 불러옵니다. 사이드바 <b>+ 추가</b>에서 API 키를 등록하세요.</div>'
    : !g ? `<div class="muted">${guildBusy?'불러오는 중…':'잠시 후 불러옵니다…'}</div>`
    : `${info?`<div class="gmeta"><span class="glv">Lv.${esc(info.guild_level)}</span><span>마스터 <b>${esc(info.guild_master_name||'-')}</b></span></div>
       <div class="gtiles">${tile('지하 수로','🌊',g.t2)}${tile('플래그 레이스','🚩',g.t1)}</div>`:''}
       ${g.ok===false?`<div class="dqlock warnc">⚠ 길드 랭킹 조회 실패 — ${esc(g.msg||'')}</div>`:''}`;
  const sub=g?.date?`<span class="muted tiny">기준 ${esc(g.date)}${g.date!==dayId()?' (어제 · 오늘 랭킹 준비 전)':''}${guildBusy?' · 갱신 중…':g.at?` · 확인 ${hhmm(g.at)}`:''}</span>`:'';
  return `<div class="gblk"><div class="gblk-h">${guildMarkHtml(G)}<b>${esc(G.name)}</b> <span class="muted">${worldIcon(G.world)} ${esc(G.world)}</span><span class="hspace"></span>${sub}<button class="surodel" data-gdel="${esc(gKey(G))}" title="길드 제거" aria-label="${esc(G.name)} 제거">✕</button></div>${body}</div>`; };
  const gc=guildCands();
  const gpick=guildPick?`<div class="suropick">${gc.length?gc.map(G=>`<label class="surocand"><input type="checkbox" value="${esc(gKey(G))}"><span>${worldIcon(G.world)} <b>${esc(G.name)}</b> <span class="muted tiny">${esc(G.world)} · ${G.chars.map(esc).join(', ')}</span></span></label>`).join(''):`<div class="muted">${guildCandBusy?'캐릭터 길드 정보를 불러오는 중…':'추가할 수 있는 길드가 없습니다. (보이는 캐릭터가 가입한 길드만 추가할 수 있습니다)'}</div>`}
</div>`:'';
  const gbtns=guildPick?`<span class="pickbtns"><button class="btn sm plain" id="guildCancel">취소</button><button class="btn sm primary" id="guildOk"${gc.length?'':' disabled'}>추가</button></span>`:''; // b111: 취소/추가 = 버튼 왼쪽
  const gl=guildList();
  const row=c=>{ const x=schedC[c.id], gg=x?.guild||{}, has=x&&x.ok!==false;
    return `<div class="grow-r">${avatar(c)}<div class="grow"><div class="nm">${esc(c.name)}</div><div class="meta">Lv.${esc(c.level||'?')} · ${esc(c.job||'')}</div></div>
      ${!schedOk(c)?'<span class="muted tiny">API 키 미연결</span>':!x?`<span class="muted tiny">${dqBusy?'불러오는 중…':'대기 중…'}</span>`:!has?`<span class="warnc tiny" title="${esc(x.msg||'')}">⚠ 조회 실패</span>`
       :`<div class="gsc main"><span class="muted tiny">지하 수로</span><b>${gg.suro?num(gg.suro.now):'-'}</b></div>`}<button class="surodel" data-surodel="${esc(c.id)}" title="목록에서 제거" aria-label="${esc(c.name)} 제거">✕</button></div>`; };
  const cand=activeChars().filter(c=>!suroIds().includes(c.id));
  const pick=suroPick?`<div class="suropick">${cand.length?cand.map(c=>`<label class="surocand">${avatar(c)}<input type="checkbox" value="${esc(c.id)}"><span><b>${esc(c.name)}</b> <span class="muted tiny">Lv.${esc(c.level||'?')} · ${esc(c.job||'')}</span></span></label>`).join(''):'<div class="muted">추가할 수 있는 캐릭터가 없습니다.</div>'}
</div>`:'';
  const sbtns=suroPick?`<span class="pickbtns"><button class="btn sm plain" id="suroCancel">취소</button><button class="btn sm primary" id="suroOk"${cand.length?'':' disabled'}>추가</button></span>`:'';
  v.innerHTML=`<div class="grid"><div class="card gcard" id="guildCard"><h2><img class="gbless" src="${ITEM_ICONS.guildbless||''}" alt="" aria-hidden="true">길드 ${gbtns}<button class="btn sm" id="guildAdd">+ 길드 추가</button></h2>${gpick}${gl.length?gl.map(gblock).join(''):'<div class="muted">+ 길드 추가로 캐릭터가 가입한 길드를 고르세요.</div>'}</div>
    <div class="card" id="suroCard"><h2><img class="bicon suroico" src="${SURO_ICON}" alt="" aria-hidden="true"> 지하 수로 <span class="muted" style="font-weight:500">이번 주</span>${sbtns}<button class="btn sm" id="suroAdd">+ 캐릭터 추가</button></h2>${pick}
      ${mains.length?mains.map(row).join(''):'<div class="muted">+ 캐릭터 추가로 수로 점수를 볼 캐릭터를 고르세요.</div>'}
      <div class="muted tiny" style="margin-top:8px">캐릭터 점수는 메이플 스케줄러의 '[길드] 지하 수로' 점수(이번 주 누적, 목요일 초기화)입니다. 길드 순위·점수는 넥슨 길드 랭킹(하루 1번, 09:30경 갱신) 기준입니다.</div></div></div>`;
  const gcd=$('#guildCard');
  if(gcd){ gcd.querySelector('#guildAdd').onclick=()=>{ guildPick=!guildPick; renderGuild(); if(guildPick) fillGuildCands(); };
    const gx=gcd.querySelector('#guildCancel'); if(gx) gx.onclick=()=>{ guildPick=false; renderGuild(); };
    const go=gcd.querySelector('#guildOk'); if(go) go.onclick=()=>{ const ks=[...gcd.querySelectorAll('.suropick input:checked')].map(i=>i.value); if(!ks.length){ toast('추가할 길드를 선택해주세요.'); return; }
      if(!Array.isArray(S.settings.guilds)) S.settings.guilds=[]; for(const k of ks){ const i=k.indexOf('|'); S.settings.guilds.push({world:k.slice(0,i),name:k.slice(i+1)}); }
      guildPick=false; save(); renderGuild(); refreshGuild(); };
    gcd.querySelectorAll('[data-gdel]').forEach(b=>b.onclick=()=>{ S.settings.guilds=guildList().filter(G=>gKey(G)!==b.dataset.gdel); save(); renderGuild(); }); }
  const sc=$('#suroCard'); if(!sc) return;
  sc.querySelector('#suroAdd').onclick=()=>{ suroPick=!suroPick; renderGuild(); };
  const cc=sc.querySelector('#suroCancel'); if(cc) cc.onclick=()=>{ suroPick=false; renderGuild(); };
  const ok=sc.querySelector('#suroOk'); if(ok) ok.onclick=()=>{ const ids=[...sc.querySelectorAll('.suropick input:checked')].map(i=>i.value); if(!ids.length){ toast('추가할 캐릭터를 선택해주세요.'); return; }
    suroIds().push(...ids); suroPick=false; save(); renderGuild(); refreshSched(suroChars()); };
  sc.querySelectorAll('[data-surodel]').forEach(b=>b.onclick=()=>{ const ids=suroIds(), i=ids.indexOf(b.dataset.surodel); if(i>=0) ids.splice(i,1); save(); renderGuild(); });
}

/* =====================================================================
 *  유틸 / UI
 * ===================================================================== */
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
/* b141: 티르노그 디지털 액션 데미지 스킨(유닛) 골드(B안) 숫자 — 7세그먼트 SVG. 억/만 도 막대로 그린 글자. 정해진 4곳에만.
 *  진짜 글자는 .tir-sr 에(복사·화면 낭독·innerText), 그림은 aria-hidden. 그라데이션·글로우는 문서에 1번 넣는 #tirDefs 공유 */
const TIR_SEG={0:'abcdef',1:'bc',2:'abged',3:'abgcd',4:'fgbc',5:'afgcd',6:'afgedc',7:'abc',8:'abcdefg',9:'abcdfg'};
const tirH=(x1,x2,y,t)=>{ const c=t/2; return `M${x1},${y}L${x1+c},${y-c}L${x2-c},${y-c}L${x2},${y}L${x2-c},${y+c}L${x1+c},${y+c}Z`; };
const tirV=(x,y1,y2,t)=>{ const c=t/2; return `M${x},${y1}L${x+c},${y1+c}L${x+c},${y2-c}L${x},${y2}L${x-c},${y2-c}L${x-c},${y1+c}Z`; };
function tirDigit(ch,ox){ const w=46,h=78,t=7,c=3.5,g=2.5,m=h/2, on=TIR_SEG[ch]||'';
  const P={a:tirH(c+g,w-c-g,c,t),g:tirH(c+g,w-c-g,m,t),d:tirH(c+g,w-c-g,h-c,t),f:tirV(c,c+g,m-g,t),b:tirV(w-c,c+g,m-g,t),e:tirV(c,m+g,h-c-g,t),c:tirV(w-c,m+g,h-c-g,t)};
  return `<g transform="translate(${ox} 0)">${'abcdefg'.split('').filter(k=>ch!=='1'||on.includes(k)).map(k=>`<path d="${P[k]}" class="${on.includes(k)?'tl':'tg'}"/>`).join('')}</g>`; }
function tirDefs(){ if(document.getElementById('tirDefs')) return; const d=document.createElement('div'); d.innerHTML=`<svg id="tirDefs" width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <linearGradient id="tirV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd2b8"/><stop offset=".55" stop-color="#ff5a1f"/><stop offset="1" stop-color="#d9381e"/></linearGradient>
  <linearGradient id="tirY" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6c8"/><stop offset=".55" stop-color="#ffd700"/><stop offset="1" stop-color="#d4af37"/></linearGradient>
  <linearGradient id="tirP" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe0f2"/><stop offset=".5" stop-color="#ff7ac8"/><stop offset="1" stop-color="#ff2d9b"/></linearGradient>
  <pattern id="tirDotY" width="8" height="8" patternUnits="userSpaceOnUse"><rect x=".5" y=".5" width="7" height="7" rx=".8" fill="#ffe7a8"/></pattern>
  <pattern id="tirDotA" width="8" height="8" patternUnits="userSpaceOnUse"><rect x=".5" y=".5" width="7" height="7" rx=".8" fill="#e6cf9c"/></pattern>
  <pattern id="tirDotW" width="8" height="8" patternUnits="userSpaceOnUse"><rect x=".5" y=".5" width="7" height="7" rx=".8" fill="#fff1dc"/></pattern>
  <linearGradient id="tirYL" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a87a00"/><stop offset=".55" stop-color="#8a6200"/><stop offset="1" stop-color="#6b4800"/></linearGradient>
  <linearGradient id="tirVL" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d0401c"/><stop offset=".55" stop-color="#b8300f"/><stop offset="1" stop-color="#8f2408"/></linearGradient>
  <linearGradient id="tirPL" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c21c7c"/><stop offset=".5" stop-color="#a01264"/><stop offset="1" stop-color="#7d0e4e"/></linearGradient>
  <linearGradient id="tirGL" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d6fa6"/><stop offset=".5" stop-color="#0a5a8c"/><stop offset="1" stop-color="#084a75"/></linearGradient>
  <linearGradient id="tirG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e6ffff"/><stop offset=".5" stop-color="#9ffbff"/><stop offset="1" stop-color="#4fe6dc"/></linearGradient>
  <filter id="tirF" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur in="SourceAlpha" stdDeviation="3.5" result="b"/><feFlood flood-color="#28e6dc"/><feComposite in2="b" operator="in" result="gl"/><feMerge><feMergeNode in="gl"/><feMergeNode in="gl"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs></svg>`; document.body.appendChild(d.firstChild); }
/* b152: 디지털 한글 단위(조/억/만/메/소) — 획마다 이어진 세그먼트, 획과 획 사이만 끊김(7세그먼트 방식). 12×12 격자 [x1,y1,x2,y2] */
const HSEG={
 '조':[[2,1.4,10,1.4],[5.4,2.9,2.4,6.4],[6.6,2.9,9.6,6.4],[6,7.5,6,9.4],[1,10.8,11,10.8]],
 '소':[[5.3,1,2,6.2],[6.7,2.7,10,6.2],[6,7.5,6,9.4],[1,10.8,11,10.8]],
 '억':[[2.2,1,5.2,1],[6.4,2.1,6.4,4.9],[5.2,6,2.2,6],[1,4.9,1,2.1],[7.5,3.5,8.7,3.5],[9.8,.5,9.8,7.2],[1.6,8.9,9,8.9],[10.2,10,10.2,11.8]],
 '만':[[1.9,1.2,5.1,1.2],[1,2.2,1,5.2],[6,2.2,6,5.2],[1.9,6.2,5.1,6.2],[8.8,.5,8.8,7.2],[9.9,3.7,11.3,3.7],[1.9,8.3,1.9,10.5],[2.9,11.4,10.6,11.4]],
 '메':[[1.9,1.9,4.7,1.9],[1,2.9,1,9.1],[5.6,2.9,5.6,9.1],[1.9,10.1,4.7,10.1],[6.7,5.6,7.4,5.6],[8.4,1,8.4,11],[10.9,.5,10.9,11.5]]};
const hsegD=ch=>(HSEG[ch]||[]).map(([a,b,c,d])=>`M${a},${b}L${c},${d}`).join('');
/* b153: 점 무늬 픽셀 한글(그래프용) — 96px 글자 + 8단위 점 패턴(userSpace)을 scale로 축소, 바닥 yb 기준 */
const HDY={'억':72,'메':72,'만':70,'조':80,'소':80};
const HPIX={"기":[[0,0],[1,0],[2,0],[3,0],[4,0],[5,0],[9,0],[5,1],[9,1],[5,2],[9,2],[5,3],[9,3],[5,4],[9,4],[4,5],[9,5],[4,6],[9,6],[3,7],[9,7],[2,8],[9,8],[0,9],[1,9],[9,9],[9,10]],"록":[[0,6],[1,0],[1,2],[1,3],[1,4],[1,6],[1,8],[2,0],[2,2],[2,4],[2,6],[2,8],[3,0],[3,2],[3,4],[3,6],[3,8],[4,0],[4,2],[4,4],[4,6],[4,8],[5,0],[5,2],[5,4],[5,5],[5,6],[5,8],[6,0],[6,2],[6,4],[6,6],[6,8],[7,0],[7,2],[7,4],[7,6],[7,8],[8,0],[8,2],[8,4],[8,6],[8,8],[9,0],[9,1],[9,2],[9,4],[9,6],[9,8],[9,9],[9,10],[10,6]],"지":[[0,0],[0,9],[1,0],[1,7],[1,8],[2,0],[2,4],[2,5],[2,6],[3,0],[3,1],[3,2],[3,3],[4,0],[4,4],[4,5],[4,6],[5,0],[5,7],[5,8],[6,0],[6,9],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"조":[[0,9],[1,0],[1,5],[1,9],[2,0],[2,5],[2,9],[3,0],[3,4],[3,9],[4,0],[4,3],[4,9],[5,0],[5,1],[5,2],[5,6],[5,7],[5,8],[5,9],[6,0],[6,3],[6,9],[7,0],[7,4],[7,9],[8,0],[8,5],[8,9],[9,0],[9,5],[9,9],[10,9]],"억":[[0,2],[0,3],[1,1],[1,4],[1,7],[2,0],[2,5],[2,7],[3,0],[3,5],[3,7],[4,0],[4,5],[4,7],[5,1],[5,4],[5,7],[6,2],[6,3],[6,7],[7,2],[7,7],[8,2],[8,7],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,7],[9,8],[9,9],[9,10]],"만":[[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[1,0],[1,5],[1,7],[1,8],[1,9],[1,10],[2,0],[2,5],[2,10],[3,0],[3,5],[3,10],[4,0],[4,5],[4,10],[5,0],[5,1],[5,2],[5,3],[5,4],[5,5],[5,10],[6,10],[7,10],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,10],[10,3]],"메":[[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[0,8],[0,9],[1,0],[1,9],[2,0],[2,9],[3,0],[3,9],[4,0],[4,1],[4,2],[4,3],[4,4],[4,5],[4,6],[4,7],[4,8],[4,9],[5,4],[6,4],[7,0],[7,1],[7,2],[7,3],[7,4],[7,5],[7,6],[7,7],[7,8],[7,9],[7,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"소":[[0,9],[1,6],[1,9],[2,5],[2,9],[3,4],[3,9],[4,3],[4,9],[5,0],[5,1],[5,2],[5,6],[5,7],[5,8],[5,9],[6,3],[6,9],[7,4],[7,9],[8,5],[8,9],[9,6],[9,9],[10,9]],"개":[[0,0],[0,9],[1,0],[1,9],[2,0],[2,8],[3,0],[3,7],[4,0],[4,5],[4,6],[5,0],[5,1],[5,2],[5,3],[5,4],[7,0],[7,1],[7,2],[7,3],[7,4],[7,5],[7,6],[7,7],[7,8],[7,9],[7,10],[8,5],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"회":[[0,2],[0,9],[1,2],[1,5],[1,6],[1,9],[2,0],[2,2],[2,4],[2,7],[2,9],[3,0],[3,2],[3,4],[3,7],[3,8],[3,9],[4,0],[4,2],[4,4],[4,7],[4,9],[5,0],[5,2],[5,4],[5,7],[5,9],[6,2],[6,5],[6,6],[6,9],[7,2],[7,9],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"승":[[0,5],[1,3],[1,5],[1,8],[1,9],[2,3],[2,5],[2,7],[2,10],[3,2],[3,5],[3,7],[3,10],[4,2],[4,5],[4,7],[4,10],[5,0],[5,1],[5,5],[5,7],[5,10],[6,2],[6,5],[6,7],[6,10],[7,2],[7,5],[7,7],[7,10],[8,3],[8,5],[8,7],[8,10],[9,3],[9,5],[9,8],[9,9],[10,5]],"패":[[0,0],[0,9],[1,0],[1,1],[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[1,8],[1,9],[2,0],[2,9],[3,0],[3,9],[4,0],[4,1],[4,2],[4,3],[4,4],[4,5],[4,6],[4,7],[4,8],[4,9],[5,0],[5,9],[7,0],[7,1],[7,2],[7,3],[7,4],[7,5],[7,6],[7,7],[7,8],[7,9],[7,10],[8,5],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"인":[[0,2],[0,3],[1,1],[1,4],[1,7],[1,8],[1,9],[1,10],[2,0],[2,5],[2,10],[3,0],[3,5],[3,10],[4,0],[4,5],[4,10],[5,1],[5,4],[5,10],[6,2],[6,3],[6,10],[7,10],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,10]],"%":[[0,2],[0,7],[0,8],[1,1],[1,3],[1,6],[2,2],[2,4],[2,5],[2,7],[3,3],[3,6],[3,8],[4,1],[4,2],[4,7]],"(":[[1,3],[1,4],[1,5],[1,6],[2,1],[2,2],[2,7],[2,8],[3,0],[3,9]],")":[[1,0],[1,9],[2,1],[2,2],[2,7],[2,8],[3,3],[3,4],[3,5],[3,6]],"·":[[2,5]],"결":[[0,0],[0,4],[1,0],[1,4],[1,6],[1,8],[1,9],[1,10],[2,0],[2,4],[2,6],[2,8],[2,10],[3,0],[3,4],[3,6],[3,8],[3,10],[4,0],[4,3],[4,6],[4,8],[4,10],[5,0],[5,1],[5,2],[5,6],[5,8],[5,10],[6,6],[6,8],[6,10],[7,1],[7,3],[7,6],[7,8],[7,10],[8,1],[8,3],[8,6],[8,8],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,6],[9,7],[9,8],[9,10]],"균":[[0,4],[1,0],[1,4],[1,7],[1,8],[1,9],[1,10],[2,0],[2,4],[2,10],[3,0],[3,4],[3,5],[3,6],[3,7],[3,10],[4,0],[4,4],[4,10],[5,0],[5,4],[5,10],[6,0],[6,4],[6,10],[7,0],[7,4],[7,5],[7,6],[7,7],[7,10],[8,0],[8,4],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,10],[10,4]],"녹":[[0,5],[1,0],[1,1],[1,2],[1,3],[1,5],[1,7],[2,3],[2,5],[2,7],[3,3],[3,5],[3,7],[4,3],[4,5],[4,7],[5,3],[5,4],[5,5],[5,7],[6,3],[6,5],[6,7],[7,3],[7,5],[7,7],[8,3],[8,5],[8,7],[9,3],[9,5],[9,7],[9,8],[9,9],[9,10],[10,5]],"누":[[0,6],[1,0],[1,1],[1,2],[1,3],[1,4],[1,6],[2,4],[2,6],[3,4],[3,6],[4,4],[4,6],[5,4],[5,6],[5,7],[5,8],[5,9],[5,10],[6,4],[6,6],[7,4],[7,6],[8,4],[8,6],[9,4],[9,6],[10,6]],"매":[[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[0,8],[0,9],[1,0],[1,9],[2,0],[2,9],[3,0],[3,9],[4,0],[4,9],[5,0],[5,1],[5,2],[5,3],[5,4],[5,5],[5,6],[5,7],[5,8],[5,9],[7,0],[7,1],[7,2],[7,3],[7,4],[7,5],[7,6],[7,7],[7,8],[7,9],[7,10],[8,5],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"반":[[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[1,2],[1,5],[1,7],[1,8],[1,9],[1,10],[2,2],[2,5],[2,10],[3,2],[3,5],[3,10],[4,2],[4,5],[4,10],[5,0],[5,1],[5,2],[5,3],[5,4],[5,5],[5,10],[6,10],[7,10],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,10],[10,3]],"상":[[0,5],[1,4],[1,8],[1,9],[2,3],[2,7],[2,10],[3,0],[3,1],[3,2],[3,7],[3,10],[4,3],[4,7],[4,10],[5,4],[5,7],[5,10],[6,5],[6,7],[6,10],[7,7],[7,10],[8,7],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,8],[9,9],[10,2]],"석":[[0,5],[1,4],[1,7],[2,3],[2,7],[3,0],[3,1],[3,2],[3,7],[4,3],[4,7],[5,4],[5,7],[6,5],[6,7],[7,2],[7,7],[8,2],[8,7],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,7],[9,8],[9,9],[9,10]],"아":[[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[1,1],[1,8],[2,0],[2,9],[3,0],[3,9],[4,0],[4,9],[5,1],[5,8],[6,2],[6,3],[6,4],[6,5],[6,6],[6,7],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10],[10,5]],"옥":[[0,5],[1,1],[1,2],[1,5],[1,7],[2,0],[2,3],[2,5],[2,7],[3,0],[3,3],[3,5],[3,7],[4,0],[4,3],[4,5],[4,7],[5,0],[5,3],[5,4],[5,5],[5,7],[6,0],[6,3],[6,5],[6,7],[7,0],[7,3],[7,5],[7,7],[8,0],[8,3],[8,5],[8,7],[9,1],[9,2],[9,5],[9,7],[9,8],[9,9],[9,10],[10,5]],"외":[[0,2],[0,3],[0,9],[1,1],[1,4],[1,9],[2,0],[2,5],[2,9],[3,0],[3,5],[3,7],[3,8],[3,9],[4,0],[4,5],[4,9],[5,1],[5,4],[5,9],[6,2],[6,3],[6,9],[7,9],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"월":[[0,3],[1,1],[1,3],[1,6],[1,8],[1,9],[1,10],[2,0],[2,2],[2,3],[2,6],[2,8],[2,10],[3,0],[3,2],[3,3],[3,4],[3,5],[3,6],[3,8],[3,10],[4,0],[4,2],[4,3],[4,6],[4,8],[4,10],[5,0],[5,2],[5,3],[5,6],[5,8],[5,10],[6,1],[6,3],[6,6],[6,8],[6,10],[7,3],[7,4],[7,6],[7,8],[7,10],[8,4],[8,6],[8,8],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,10]],"위":[[0,6],[1,1],[1,2],[1,3],[1,6],[2,0],[2,4],[2,6],[3,0],[3,4],[3,6],[4,0],[4,4],[4,6],[4,7],[4,8],[4,9],[4,10],[5,0],[5,4],[5,6],[6,1],[6,2],[6,3],[6,6],[7,6],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"이":[[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[1,1],[1,8],[2,0],[2,9],[3,0],[3,9],[4,0],[4,9],[5,1],[5,8],[6,2],[6,3],[6,4],[6,5],[6,6],[6,7],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"적":[[0,0],[0,5],[1,0],[1,4],[1,7],[2,0],[2,3],[2,7],[3,0],[3,1],[3,2],[3,7],[4,0],[4,3],[4,7],[5,0],[5,4],[5,7],[6,0],[6,5],[6,7],[7,2],[7,7],[8,2],[8,7],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,7],[9,8],[9,9],[9,10]],"정":[[0,0],[0,5],[1,0],[1,4],[1,8],[1,9],[2,0],[2,3],[2,7],[2,10],[3,0],[3,1],[3,2],[3,7],[3,10],[4,0],[4,3],[4,7],[4,10],[5,0],[5,4],[5,7],[5,10],[6,0],[6,5],[6,7],[6,10],[7,2],[7,7],[7,10],[8,2],[8,7],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,8],[9,9]],"제":[[0,0],[0,7],[0,8],[0,9],[1,0],[1,4],[1,5],[1,6],[2,0],[2,1],[2,2],[2,3],[3,0],[3,4],[3,5],[3,6],[4,0],[4,7],[4,8],[4,9],[5,4],[6,4],[7,0],[7,1],[7,2],[7,3],[7,4],[7,5],[7,6],[7,7],[7,8],[7,9],[7,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10]],"주":[[0,6],[1,0],[1,4],[1,6],[2,0],[2,4],[2,6],[3,0],[3,3],[3,6],[4,0],[4,3],[4,6],[5,0],[5,1],[5,2],[5,6],[5,7],[5,8],[5,9],[5,10],[6,0],[6,3],[6,6],[7,0],[7,3],[7,6],[8,0],[8,4],[8,6],[9,0],[9,4],[9,6],[10,6]],"템":[[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[1,0],[1,2],[1,5],[1,7],[1,8],[1,9],[1,10],[2,0],[2,2],[2,5],[2,7],[2,10],[3,0],[3,2],[3,5],[3,7],[3,10],[4,0],[4,2],[4,5],[4,7],[4,10],[5,3],[5,7],[5,10],[6,3],[6,7],[6,10],[7,0],[7,1],[7,2],[7,3],[7,4],[7,5],[7,7],[7,10],[8,7],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,7],[9,8],[9,9],[9,10]],"판":[[0,0],[0,5],[1,0],[1,5],[1,7],[1,8],[1,9],[1,10],[2,0],[2,1],[2,2],[2,3],[2,4],[2,5],[2,10],[3,0],[3,5],[3,10],[4,0],[4,5],[4,10],[5,0],[5,1],[5,2],[5,3],[5,4],[5,5],[5,10],[6,0],[6,5],[6,10],[7,0],[7,5],[7,10],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,10],[10,3]],"평":[[0,0],[0,5],[1,0],[1,1],[1,2],[1,3],[1,4],[1,5],[1,8],[1,9],[2,0],[2,5],[2,7],[2,10],[3,0],[3,5],[3,7],[3,10],[4,0],[4,1],[4,2],[4,3],[4,4],[4,5],[4,7],[4,10],[5,0],[5,5],[5,7],[5,10],[6,0],[6,5],[6,7],[6,10],[7,1],[7,3],[7,7],[7,10],[8,1],[8,3],[8,7],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,8],[9,9]],"홍":[[0,1],[0,5],[1,1],[1,2],[1,5],[1,8],[1,9],[2,1],[2,3],[2,5],[2,7],[2,10],[3,1],[3,3],[3,5],[3,7],[3,10],[4,1],[4,3],[4,5],[4,7],[4,10],[5,0],[5,1],[5,3],[5,4],[5,5],[5,7],[5,10],[6,1],[6,3],[6,5],[6,7],[6,10],[7,1],[7,3],[7,5],[7,7],[7,10],[8,1],[8,3],[8,5],[8,7],[8,10],[9,1],[9,2],[9,5],[9,8],[9,9],[10,1],[10,5]],"검":[[0,0],[0,5],[1,0],[1,5],[1,7],[1,8],[1,9],[1,10],[2,0],[2,5],[2,7],[2,10],[3,0],[3,4],[3,7],[3,10],[4,0],[4,3],[4,7],[4,10],[5,0],[5,1],[5,2],[5,7],[5,10],[6,7],[6,10],[7,2],[7,7],[7,10],[8,2],[8,7],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,7],[9,8],[9,9],[9,10]],"득":[[0,5],[1,0],[1,1],[1,2],[1,3],[1,5],[1,7],[2,0],[2,3],[2,5],[2,7],[3,0],[3,3],[3,5],[3,7],[4,0],[4,3],[4,5],[4,7],[5,0],[5,3],[5,5],[5,7],[6,0],[6,3],[6,5],[6,7],[7,0],[7,3],[7,5],[7,7],[8,0],[8,3],[8,5],[8,7],[9,0],[9,3],[9,5],[9,7],[9,8],[9,9],[9,10],[10,5]],"마":[[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[0,8],[0,9],[1,0],[1,9],[2,0],[2,9],[3,0],[3,9],[4,0],[4,9],[5,0],[5,9],[6,0],[6,1],[6,2],[6,3],[6,4],[6,5],[6,6],[6,7],[6,8],[6,9],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9],[9,10],[10,5]],"번":[[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[1,2],[1,5],[1,7],[1,8],[1,9],[1,10],[2,2],[2,5],[2,10],[3,2],[3,5],[3,10],[4,2],[4,5],[4,10],[5,0],[5,1],[5,2],[5,3],[5,4],[5,5],[5,10],[6,10],[7,3],[7,10],[8,3],[8,10],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,10]],"보":[[0,9],[1,0],[1,1],[1,2],[1,3],[1,4],[1,5],[1,6],[1,9],[2,2],[2,6],[2,9],[3,2],[3,6],[3,9],[4,2],[4,6],[4,9],[5,2],[5,6],[5,7],[5,8],[5,9],[6,2],[6,6],[6,9],[7,2],[7,6],[7,9],[8,2],[8,6],[8,9],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,9],[10,9]],"획":[[0,1],[0,6],[1,1],[1,3],[1,6],[1,8],[2,1],[2,2],[2,4],[2,6],[2,8],[3,0],[3,1],[3,2],[3,4],[3,5],[3,6],[3,8],[4,1],[4,2],[4,4],[4,6],[4,8],[5,1],[5,2],[5,4],[5,6],[5,8],[6,1],[6,3],[6,6],[6,8],[7,1],[7,6],[7,8],[8,8],[9,0],[9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,8],[9,9],[9,10]]};
/* b154: 디지털 한글 단위 = Fusion Pixel 12px 비트맵을 숫자와 같은 좌표계(SVG)로 그림. 1칸 = 숫자 세그먼트 굵기 t(7), 11칸 = 숫자 높이(바닥 y=78).
   이어진 칸 사이를 2칸마다 끊어(HGAP) 1x 화면에서도 빈 점 틈이 보이게 함 */
const HGAP=3.6;
/* b155: 사이트 이름 로고를 디지털 픽셀(하늘색·글로우·5°)로 */
function logoDigital(){ const a=document.getElementById('logoHome'); if(!a||a.querySelector('.logo-d')) return; tirDefs();
  const T='메보기', w=T.length*92-8; const tn=[...a.childNodes].find(n=>n.nodeType===3&&n.textContent.trim()===T); if(!tn) return;
  const sp=document.createElement('span'); sp.className='logo-d'; sp.innerHTML=`<span class="tir-sr">${T}</span><svg class="tir-g logo-g" viewBox="-6 -6 ${w+12} 98" style="--tw:${((w+12)/98).toFixed(3)}" aria-hidden="true" focusable="false">${[...T].map((c,i)=>`<path class="tl tk" d="${hpixD(c,i*92)}"/>`).join('')}</svg>`;
  tn.replaceWith(sp); }
const HADV={'%':46,'(':40,')':40,'·':34}; /* b164: 반폭 글리프 전진폭 */
function hpixD(ch,ox,oy=1,c=7,g=HGAP,extra){ const P=extra?HPIX[ch].concat(extra):HPIX[ch]; if(!P) return ''; const on=new Set(P.map(([x,y])=>x+','+y)), h=g/2;
  return P.map(([x,y])=>{ let x0=x*c,x1=x0+c,y0=y*c,y1=y0+c;
    if(on.has((x-1)+','+y)&&x%2===0) x0+=h; if(on.has((x+1)+','+y)&&(x+1)%2===0) x1-=h;
    if(on.has(x+','+(y-1))&&y%2===0) y0+=h; if(on.has(x+','+(y+1))&&(y+1)%2===0) y1-=h;
    return `M${(ox+x0).toFixed(1)},${(oy+y0).toFixed(1)}H${(ox+x1).toFixed(1)}V${(oy+y1).toFixed(1)}H${(ox+x0).toFixed(1)}z`; }).join(''); }
const hdotG=(ch,x,yb,s,pat)=>`<g class="hdot" transform="translate(${(+x).toFixed(1)} ${(yb-78*s).toFixed(1)}) scale(${s.toFixed(4)})"><text x="0" y="${HDY[ch]||76}" style="font-size:96px" fill="url(#${pat})">${ch}</text></g>`;
const hsegSvg=ch=>`<svg class="hk" viewBox="0 0 12 12" aria-hidden="true" focusable="false"><path d="${hsegD(ch)}"/></svg>`;
/* 그래프 글자(축·값 라벨): 숫자는 text, 한글 단위는 세그먼트 path. anchor=end|middle, fs=글자 크기 */
function segLab(str,x,y,anchor,cls,fs=10){ const S=String(str), u=fs*.70*84/78, gap=fs*.12;
  const parts=[]; let buf=''; for(const ch of S){ if(HSEG[ch]){ if(buf) parts.push(['t',buf]); buf=''; parts.push(['k',ch]); } else buf+=ch; } if(buf) parts.push(['t',buf]);
  const tw=t=>[...t].reduce((a,c)=>a+(/[.,]/.test(c)?.32:c===' '?.3:.64)*fs,0);
  const W=parts.reduce((a,[k,v])=>a+(k==='t'?tw(v):u+gap),0); let cx=anchor==='end'?x-W:anchor==='middle'?x-W/2:x; let out='';
  for(const [k,v] of parts){ if(k==='t'){ out+=`<text class="${cls}" x="${cx.toFixed(1)}" y="${y}" text-anchor="start">${esc(v)}</text>`; cx+=tw(v); }
    else { { const k=fs*.70/78, d=hpixD(v,0,1,7,0), tf=`translate(${(cx+gap*.5).toFixed(1)} ${(+y-78*k).toFixed(1)}) scale(${k.toFixed(4)})`; out+=`<g transform="${tf}"><path class="hsk hsk-o" d="${d}" style="stroke-width:${(2.6/k).toFixed(1)}px"/><path class="hsk ${cls}-k" d="${d}" style="stroke-width:${(.5/k).toFixed(1)}px"/></g>`; } cx+=u+gap; } }
  return `<g class="seglab" aria-hidden="true">${out}</g>`; }
function tir(text,cls=''){ const T=String(text); let out='', x=0, parts='';
  const flush=()=>{ if(!parts&&!x) return; const W=Math.max(1,x-8); out+=`<svg class="tir-g" viewBox="-6 -6 ${W+12} 98" style="--tw:${((W+12)/98).toFixed(3)}" aria-hidden="true" focusable="false">${parts}</svg>`; parts=''; x=0; };
  for(const ch of T){ if(ch==='1'){ parts+=tirDigit(ch,x-20); x+=34; } else if(/[0-9]/.test(ch)){ parts+=tirDigit(ch,x); x+=54; } /* 1 은 좁게 */
    else if(HPIX[ch]){ parts+=`<path class="tl tk" d="${hpixD(ch,x+4,1,7,HGAP,ch==='억'?[[9,11]]:null)}"/>`; x+=HADV[ch]||92; } /* b158: 숫자 옆 '억'은 ㄱ 세로획 맨 아래 점 1개 추가 */
    else if(/[가-힣]/.test(ch)){ flush(); out+=`<span class="tir-k" data-k="${ch}" aria-hidden="true"></span>`; }
    else if(ch==='.'){ parts+=`<path class="tl" d="M${x+8},61h15v15h-15z"/>`; x+=33; } /* b211: 소수점 1.5배(10→15) · b212: 양옆 더 띄움(왼 8·오른 10, 전진폭 = 점 무늬 8 배수) */
    else if(ch===','){ parts+=`<path class="tl" d="M${x+2},64h10v10h-10zM${x+5},76h6l-5,9h-5z"/>`; x+=17; }
    else if(ch==='-'){ parts+=`<path class="tl" d="${tirH(x+2,x+40,39,7)}"/>`; x+=48; } else if(ch===' '){ flush(); out+='<span class="tir-sp" aria-hidden="true"></span>'; } }
  flush();
  return `<span class="tir ${cls}"${arguments[2]||''}><span class="tir-sr">${esc(T)}</span>${out}</span>`; }
/* b162: 디지털 숫자 카운팅 (0→최종값 1.2초 ease-out, 같은 포맷). 화면에 보일 때 시작(IntersectionObserver), 같은 자리(key) 값이 그대로면 재렌더해도 다시 안 돎(바뀌면 이전 값→새 값). 최종 폭으로 고정해 흔들림 없음. prefers-reduced-motion 이면 바로 최종값 */
const TIR_F={eok:fmtEokSafe, meso:n=>meso(n), cnt:n=>String(Math.round(n)), dec:n=>String(Math.round(n*10)/10), pct:n=>pctNum(n), tpct:n=>'상위 '+pctNum(n)};
const pctNum=v=>String(v>=0.1||v===0?(Math.round(v*10)/10):Number(v.toPrecision(1)));
/* b162: '상위 X%' — 글자 '상위'는 그대로, 숫자+% 만 디지털 */
const topPctT=(v,key)=>v==null?tir('-'):`<span class="tirv">${tirN(v,'tpct',key,'%')}</span>`;
/* b164: 작은 문구용 디지털 — 글씨체(계산기 숫자+점 한글)·점 무늬만, 색=원래 문구 색, 글로우·카운팅·확대 없음 */
const tsm=t=>`<span class="tsmn">${esc(String(t))}</span>`; /* b183: 작은 문구 = 사이트 기본 글씨체(디지털 아님) */ function fmtEokSafe(n){ return fmtEok(n); }
const TIR_LAST=new Map();
const tirN=(v,f,key,suf='')=>{ v=+v||0; return tir(TIR_F[f](v)+suf,'',` data-tv="${v}" data-tf="${f}" data-tk="${esc(key)}" data-ts="${esc(suf)}"`); };
const tirMeso = (n,key) => key?tirN(n,'meso',key):tir(meso(n));
function tirAnimOne(el){ if(el._tirDone) return; el._tirDone=1; const v=+el.dataset.tv, f=TIR_F[el.dataset.tf], suf=el.dataset.ts||'', k=el.dataset.tk;
  const from=TIR_LAST.has(k)?TIR_LAST.get(k):0; TIR_LAST.set(k,v); el.dataset.tdone='1';
  if(from===v||!f||(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)) return;
  const fin=el.innerHTML, w=el.getBoundingClientRect().width; el.style.display='inline-block'; el.style.minWidth=w+'px'; el.style.textAlign=getComputedStyle(el.parentElement).textAlign==='right'?'right':'left';
  const t0=performance.now(), D=1200, step=now=>{ if(!el.isConnected) return; const q=Math.min(1,(now-t0)/D), e=1-Math.pow(1-q,3);
    if(q>=1){ el.innerHTML=fin; el.style.minWidth=''; el.style.display=''; el.style.textAlign=''; el.dataset.tanim='done'; return; }
    const cur=from+(v-from)*e, c=/dec|pct|tpct/.test(el.dataset.tf)?cur:Math.abs(v)>=1e4?Math.round(cur/1e4)*1e4:Math.round(cur); const tmp=document.createElement('span'); tmp.innerHTML=tir(f(c)+suf); const sr=el.querySelector('.tir-sr'); el.replaceChildren(...(sr?[sr]:[]),...[...tmp.firstChild.childNodes].slice(1)); requestAnimationFrame(step); };
  el.dataset.tanim='run'; requestAnimationFrame(step); }
(()=>{ const io=typeof IntersectionObserver==='function'?new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting){ io.unobserve(e.target); tirAnimOne(e.target); } }),{threshold:.3}):null;
  const scan=()=>document.querySelectorAll('.tir[data-tv]:not([data-tobs])').forEach(el=>{ el.dataset.tobs='1'; const k=el.dataset.tk, v=+el.dataset.tv; if(TIR_LAST.has(k)&&TIR_LAST.get(k)===v){ el._tirDone=1; el.dataset.tdone='1'; return; } io?io.observe(el):tirAnimOne(el); });
  let qd=0; new MutationObserver(()=>{ if(qd) return; qd=1; requestAnimationFrame(()=>{ qd=0; scan(); }); }).observe(document.documentElement,{childList:true,subtree:true}); })();
/* b150: 그래프 값 라벨용 SVG 디지털 글자 (계산기4 골드 숫자 + Fusion Pixel 한글, 한글은 8단위 격자에 맞춘 점 무늬) — (cx, 바닥 y, 숫자 높이 h) */
function tirSvg(text,cx,yb,h,cls='tgold'){ const T=String(text), k=h/78, P=[]; let x=0;
  for(const ch of T){ if(ch==='1'){ P.push(tirDigit(ch,x-20)); x+=34; } else if(/[0-9]/.test(ch)){ P.push(tirDigit(ch,x)); x+=54; }
    else if(HPIX[ch]){ P.push(`<path class="tl tk" d="${hpixD(ch,x+4)}"/>`); x+=HADV[ch]||92; }
    else if(ch==='.'){ P.push(`<path class="tl" d="M${x+8},61h15v15h-15z"/>`); x+=33; } /* b211·b212: 소수점 1.5배 + 양옆 띄움 */
    else if(ch===','){ P.push(`<path class="tl" d="M${x+2},66h10v10h-10z"/>`); x+=17; } else if(ch===' '){ x+=24; } }
  const W=Math.max(1,x-6), tr=`translate(${(cx-W*k/2).toFixed(1)} ${(yb-78*k).toFixed(1)}) scale(${k.toFixed(4)}) skewX(-5)`; if(arguments[5]) return {tr,inner:P.join('')};
  return `<g class="tsv ${cls}" transform="${tr}" data-st="${esc(T)}" data-sa="${cx},${yb},${h}" aria-hidden="true">${P.join('')}</g>`; }
/* b173: 그래프 안 디지털 숫자도 0→최종값 카운팅 (그래프가 화면에 들어올 때). 같은 그래프·자리·값은 탭 전환/새로고침 전까지 다시 안 돎 */
const TSV_SEEN=new Set();
function tsvAnim(chart){ if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches) return; const sig=chart.className.replace(/\s*inview/,'');
  chart.querySelectorAll('g.tsv[data-st]').forEach((g,i)=>{ const T=g.dataset.st, key=sig+'|'+i+'|'+T; if(TSV_SEEN.has(key)) return; TSV_SEEN.add(key);
    const m=/^(-?[\d,]*\.?\d+)(.*)$/.exec(T); if(!m) return; const v=parseFloat(m[1].replace(/,/g,'')); if(!v) return;
    const dp=(m[1].split('.')[1]||'').length, cm=m[1].includes(','), [cx,yb,h]=g.dataset.sa.split(',').map(Number);
    const fmt=c=>dp?c.toFixed(dp):cm?Math.round(c).toLocaleString():String(Math.round(c));
    const set=t=>{ const r=tirSvg(t,cx,yb,h,'',1); g.setAttribute('transform',r.tr); g.innerHTML=r.inner; };
    const t0=performance.now(), D=1200; g.dataset.tanim='run'; set(fmt(0)+m[2]);
    const step=now=>{ if(!g.isConnected) return; const q=Math.min(1,(now-t0)/D); if(q>=1){ set(T); g.dataset.tanim='done'; return; } set(fmt(v*(1-Math.pow(1-q,3)))+m[2]); requestAnimationFrame(step); };
    requestAnimationFrame(step); }); }
/* b150: 1억 이상은 소수 둘째 자리 억(32.51억), 1조 이상은 조(1.23조) — 사이트 전체 공통 */
function fmtEok(n){ n=+n||0; const a=Math.abs(n); return a>=1e12?(n/1e12).toFixed(2)+'조':(n/1e8).toFixed(2)+'억'; }
function meso(n){
  n=Math.round(n||0); if(n===0) return '0 메소';
  if(Math.abs(n)>=1e8) return fmtEok(n)+' 메소';
  const eok=Math.floor(n/1e8), man=Math.floor(n%1e8/1e4), rest=n%1e4;
  let s=''; if(eok) s+=eok.toLocaleString()+'억 '; if(man) s+=man.toLocaleString()+'만'; if(!eok&&!man) s=rest.toLocaleString();
  return s.trim()+' 메소'; // b60: 금액에는 항상 '메소' 단위
}
/* b75 규칙: 칸을 비워서 경고가 나오면 그 칸 테두리를 빨갛게(.inerr) — 입력하면 바로 지움 */
function markEmpty(el,on=true){ if(el) el.classList.toggle('inerr',!!on); return el; }
document.addEventListener('input',e=>{ const t=e.target; if(t?.classList?.contains('inerr')&&String(t.value).trim()) t.classList.remove('inerr'); },true);
function toastHide(){ clearTimeout(toast._t); $('#toast')?.classList.remove('show'); }
function toast(msg){} /* b112: 하단 알림 전부 없앰 */
const safeImg = u => /^https:\/\/open\.api\.nexon\.com\//.test(u||'') ? u : '';
const avatar = (c,cls='') => `<div class="avatar ${cls}">${safeImg(c.image)?`<img src="${esc(c.image)}" alt="" loading="lazy" onerror="this.remove()">`:esc((c.name||'?').slice(0,1))}</div>`;
const TAB_KEY='mapleBossTracker.tab', TABS=['boss','total','loot','guild','live']; // 새로고침 후 마지막 탭 복원 (이 브라우저)
let tab='boss', /* b166: 새로고침하면 항상 '이번 주 보스' (저장된 마지막 탭·해시 무시) */ bossFilter='weekly', editMode=false;

const THEME_KEY='mapleBossTracker.theme'; // b179: 라이트/다크 선택 (이 브라우저, 기본 다크) — 사용자 요청으로 다크 전용 규칙 해제
function curTheme(){ try{ return localStorage.getItem(THEME_KEY)==='light'?'light':'dark'; }catch(e){ return 'dark'; } }
function applyTheme(){ document.documentElement.dataset.theme=curTheme(); }
function toggleTheme(){ const t=curTheme()==='light'?'dark':'light'; try{ localStorage.setItem(THEME_KEY,t); }catch(e){} applyTheme(); document.querySelectorAll('.thbtn').forEach(b=>{ b.textContent=t==='light'?'🌙':'☀️'; b.title=b.ariaLabel=t==='light'?'다크 모드로':'라이트 모드로'; }); }
applyTheme();
function paintThemeBtn(){ const t=curTheme(); document.querySelectorAll('.thbtn').forEach(b=>{ b.textContent=t==='light'?'🌙':'☀️'; b.title=t==='light'?'다크 모드로':'라이트 모드로'; b.setAttribute('aria-label',b.title); }); } // b182: 헤더 오른쪽 위 버튼
function orbitFont(){ if(document.getElementById('orbitCss')) return; const l=document.createElement('link'); l.id='orbitCss'; l.rel='stylesheet'; l.href='https://fonts.googleapis.com/css2?family=Orbit&display=swap'; document.head.appendChild(l); document.fonts&&document.fonts.addEventListener('loadingdone',()=>{ if(tab==='boss') fitPriceCard(); if(tab==='loot') fitMiss(); }); }
/* b187: 캐릭터를 바꿨을 때만 정보 카드·드롭 표 등장 애니메이션 (transform·opacity 만 → 자리 이동·클릭 지연 없음, 줄인 동작 설정이면 없음) */
let enterFor=null, enterT=0;
function charEnter(){ const id=S.activeId, v=$('#view'); if(enterFor===id) return; const first=enterFor===null; enterFor=id; if(first||!v) return;
  if(matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  /* b197: 칸 = 정보 카드의 각 줄·스탯 칸 + 드롭 표 툴바·보스 줄. 순번(--ei, 최대 14)으로 시차 */
  v.querySelectorAll('.bosslay>.grid>.card>:not(.stats):not(.boss-list),.bosslay>.grid .stats>.stat,.bosslay>.grid .boss-list>*').forEach((e,i)=>{ e.classList.add('cpop'); e.style.setProperty('--ei',Math.min(i,14)); });
  v.classList.remove('center'); void v.offsetWidth; v.classList.add('center'); clearTimeout(enterT); enterT=setTimeout(()=>v.classList.remove('center'),1000); }
function render(){ paintThemeBtn(); tirDefs(); logoDigital(); orbitFont(); document.body.dataset.curtab=tab; if(!TABS.includes(tab)) tab='boss'; syncTabs();
  renderChars(); renderHeaderSync(); if($('#importModal').classList.contains('show')) renderAccList();
  /* b87 규칙 10: 보이는 캐릭터가 없으면(API 키 미등록) 모든 탭 = 보스 현황과 같은 빈 화면(emptyView). 새 탭도 이 분기를 거침 */
  if(!vchars().length&&tab!=='live'){ $('#view').innerHTML=emptyView(); fitPriceCard(); renderResetInfo(); return; } /* b161: 라이브 탭은 캐릭터·로그인 없어도 보임 */
  ({boss:renderBoss,total:()=>COMMITTED(renderTotal),loot:()=>COMMITTED(renderLoot),guild:renderGuild,live:renderLive})[tab](); if(tab==='boss'){ fitPriceCard(); charEnter(); } if(tab==='loot') fitMiss(); renderResetInfo(); }
/* b108: 🔄 옆 상태 글자 — 동기화 중 '새로고침 중입니다..'(회색), 끝나면 초록 '새로고침 완료! HH:mm'(KST, 계속 표시),
 * 일부 캐릭터·계정 오류면 주황 '일부 실패 HH:mm', 전체 실패면 빨강 '새로고침 실패 HH:mm' (오류 알림 toast 는 예전 그대로). 페이지 열 때 동기화도 같음 */
let syncLbl=null; // {st:'run'|'ok'|'part'|'fail', at}
function syncLabel(st,at){ syncLbl={st,at:at||Date.now()}; paintSyncLabel(); }
function paintSyncLabel(){ const b=$('#syncBtn'); if(!b||!syncLbl||b.hidden) { $('#syncDone')?.remove(); return; }
  let f=$('#syncDone'); if(!f){ f=document.createElement('span'); f.id='syncDone'; f.setAttribute('role','status'); f.setAttribute('aria-live','polite'); }
  if(b.nextElementSibling!==f) b.after(f);
  const k=kst(syncLbl.at), t=pad(k.getUTCHours())+':'+pad(k.getUTCMinutes()), M={run:['새로고침 중입니다..','run'],ok:['새로고침 완료! '+t,''],part:['일부 실패 '+t,'part'],fail:['새로고침 실패 '+t,'fail']}[syncLbl.st];
  f.className='syncdone'+(M[1]?' '+M[1]:''); if(f.textContent!==M[0]) f.textContent=M[0]; }
function syncDoneFlash(){ syncLabel('ok'); }
/* 캐릭터 카드 제목 옆: 🔄 지금 동기화 아이콘 버튼 (API 키가 있을 때만, 넥슨 API 전용 — 구글 드라이브는 헤더 ☁ 버튼) */
const SYNC_SVG=`<svg class="rot" viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.34-5.66" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M20 4v5h-5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
function renderHeaderSync(){ if(!syncing&&TOP_PIN) pageTop(); /* b223: 첫 동기화 끝(아직 사용자가 안 움직였으면) 맨 위 유지 */
  const b=$('#syncBtn'); if(!b) return; const st=S.settings; b.hidden=!hasApi(); b.disabled=syncing;
  b.classList.toggle('busy',syncing); b.setAttribute('aria-busy',String(syncing));
  if(!b.querySelector('svg')) b.innerHTML=SYNC_SVG; // 아이콘만 (2026-10-10: 헤더 → 캐릭터 카드 제목 옆)
  b.title=syncing?'동기화 중…':`지금 동기화 (보스 클리어 자동 체크)\n마지막 동기화: ${st.lastSync?hm(st.lastSync)+' KST':'없음'}\n홈페이지에 들어올 때·새로고침할 때·API 키를 등록할 때 자동 (3초 안 중복은 건너뜀)`;
  b.setAttribute('aria-label',syncing?'동기화 중':`지금 동기화 — 마지막 ${st.lastSync?hm(st.lastSync):'없음'}`);
  paintSyncLabel();
}

/* ---------- 사용자 지정 순서 ----------
 * S.characters 배열 순서 = 월드 그룹 안에서의 표시 순서, S.worldOrder = 월드 그룹 순서.
 * 동기화·가져오기·본캐 지정은 이 순서를 바꾸지 않습니다(새 캐릭터는 맨 뒤에 추가). */
function worldGroups(){
  const groups=new Map();
  for(const w of S.worldOrder) groups.set(w,[]);
  for(const c of activeChars()){ const w=worldOf(c); if(!groups.has(w)) groups.set(w,[]); groups.get(w).push(c); }
  for(const [w,cs] of groups) if(!cs.length) groups.delete(w);
  return groups;
}
const orderedChars = () => [...worldGroups().values()].flat();
function moveCharTo(id, targetId, after){
  if(id===targetId) return false;
  const arr=S.characters, c=arr.find(x=>x.id===id), t=arr.find(x=>x.id===targetId);
  if(!c||!t||worldOf(c)!==worldOf(t)) return false;
  arr.splice(arr.indexOf(c),1); arr.splice(arr.indexOf(t)+(after?1:0),0,c);
  save(); return true;
}
function moveCharBy(id, dir){
  const c=S.characters.find(x=>x.id===id); if(!c) return;
  const same=vchars().filter(x=>worldOf(x)===worldOf(c)); const i=same.indexOf(c), j=i+dir;
  if(j<0||j>=same.length) return;
  moveCharTo(id, same[j].id, dir>0);
}
function moveWorldTo(w, target, after){
  if(w===target) return false;
  const order=[...worldGroups().keys()]; if(!order.includes(w)||!order.includes(target)) return false;
  order.splice(order.indexOf(w),1); order.splice(order.indexOf(target)+(after?1:0),0,w);
  S.worldOrder=order; save(); return true;
}
function moveWorldBy(w, dir){ const order=[...worldGroups().keys()], j=order.indexOf(w)+dir; if(j<0||j>=order.length) return; moveWorldTo(w, order[j], dir>0); }

// EXP 줄: API 데이터가 있고 레벨이 일치할 때만 표시 (수동 캐릭터/레벨 불일치 시 숨김)
function expLine(c){
  const e=c.exp; if(!e||!isFinite(e.rate)) return '';
  if(e.level&&c.level&&+e.level!==+c.level) return '';
  const p=Math.max(0,Math.min(100,+e.rate));
  const tip=`EXP ${p.toFixed(3)}%`+(e.exp?` (${Number(e.exp).toLocaleString()})`:'')+(e.date?` · 기준 ${String(e.date).slice(0,10)}`:'');
  return `<div class="expl" title="${esc(tip)}"><span class="expbar" role="progressbar" aria-label="경험치" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${p.toFixed(2)}"><i style="width:${p.toFixed(2)}%"></i></span><span class="exppct">${p.toFixed(2)}%</span></div>`;
}
/* 사이드바 카드: 이번 주 주간 보스 12/12면 반투명 검정 덮개 + '★ 이번 주 보스 완료'
 * (월간 보스를 선택해 두었는데 이번 달 아직 안 잡았으면 그 아래 줄에 빨간 (!) '검마 격파 필요' 추가). 마우스를 올리면 사라짐, 클릭은 통과 */
function monthlyPending(c){ return BOSSES.filter(b=>b.type==='monthly'&&c.bosses?.[b.id]?.enabled&&!c.monthly?.[b.id]); }
function doneOverlay(c,r){
  if(r.weekly<S.settings.weeklyLimit) return '';
  const pend=monthlyPending(c);
  const warn=pend.length?`<span class="dov-warn"><i class="dov-ex" aria-hidden="true">!</i>${pend.map(b=>esc(b.aliases?.[0]||b.name)).join('·')} 격파 필요</span>`:'';
  return `<div class="dov" aria-hidden="true"><div class="dov-t"><span class="dov-ok"><b class="dov-star">★</b> 이번 주 보스 완료</span>${warn}</div></div>`;
}
/* 사이드바 캐릭터 정렬 보기: 'base' = 기본순(저장된 순서) / 'undone' = 보스 미완료순(이번 주 12/12 안 된 캐릭터 먼저, 각 무리 안은 기본순 유지).
 * 보기 방식만 바꾸고 저장된 순서는 건드리지 않음. 기기별 표시 설정이라 localStorage(드라이브 동기화 안 함). */
const CHAR_SORT_KEY='mapleBossTracker.charSort';
const CSORTS=['base','undone','gm']; // gm = 검마 정렬순: 이번 달 검은 마법사 안 잡은 캐릭터 먼저 (각 무리 안은 기본순)
let charSort=(()=>{ try{ const v=localStorage.getItem(CHAR_SORT_KEY); return CSORTS.includes(v)?v:'base'; }catch(e){ return 'base'; } })();
const gmDone = c => !!c.monthly?.blackmage;
const sortedChars = cs => charSort==='gm' ? [...cs.filter(c=>!gmDone(c)), ...cs.filter(gmDone)] : charSort!=='undone' ? cs : [...cs.filter(c=>weeklyCount(c)<S.settings.weeklyLimit), ...cs.filter(c=>weeklyCount(c)>=S.settings.weeklyLimit)];
function setCharSort(v){ charSort=CSORTS.includes(v)?v:'base'; try{ localStorage.setItem(CHAR_SORT_KEY,charSort); }catch(e){} render(); }
/* 캐릭터 목록: 8명까지 보이고 넘으면 목록 안에서 스크롤 (페이지는 안 늘어남).
 * 데스크톱에서 화면이 낮아 8줄 + 소식 카드 최소 높이가 안 들어가면 들어가는 만큼만(최소 4줄) 보여 줌 → 사이드바 때문에 페이지가 길어지지 않음. */
const CHAR_ROWS=8, CHAR_ROWS_MIN=4, SIDE_FEED_MIN=31*2+70+12; // 소식 카드 최소 높이(feedFit 의 minH) + 카드 간격
function fitCharList(){ // 2026-10-10: 스크롤 대신 페이지(8명) — 높이 제한 없음
  { const el=$('#charList'); if(el){ el.style.maxHeight=''; el.classList.remove('scroll'); } return; }
  const el=$('#charList'); if(!el) return; const cs=[...el.querySelectorAll('.char[data-id]')], st=el.scrollTop;
  el.style.maxHeight=''; el.classList.remove('scroll');
  let n=CHAR_ROWS;
  if(cs.length>CHAR_ROWS_MIN && !matchMedia('(max-width:820px)').matches){
    const aside=el.closest('.side-sticky'), card=el.closest('.card');
    if(aside&&card){
      const A=aside.getBoundingClientRect(), relTop=el.getBoundingClientRect().top-A.top, padB=card.getBoundingClientRect().bottom-el.getBoundingClientRect().bottom;
      const stick=parseFloat(getComputedStyle(aside).top)||0, docTop=A.top+scrollY;
      const foot=$('.foot'), main=aside.parentElement, below=parseFloat(getComputedStyle(main).paddingBottom)+(foot?foot.offsetHeight:0);
      const room=Math.min(innerHeight-stick-16, innerHeight-docTop-below)-relTop-padB-SIDE_FEED_MIN; // 목록이 쓸 수 있는 높이
      const top=el.getBoundingClientRect().top;
      while(n>CHAR_ROWS_MIN && cs[n-1] && cs[n-1].getBoundingClientRect().bottom-top>room) n--;
    }
  }
  if(cs.length<=n) return;
  const top=el.getBoundingClientRect().top, b=cs[n-1].getBoundingClientRect().bottom;
  el.style.maxHeight=Math.ceil(b-top+2)+'px'; el.classList.add('scroll'); el.scrollTop=st;
  const on=el.querySelector('.char.on'); if(on){ const r=on.getBoundingClientRect(), R=el.getBoundingClientRect(); if(r.top<R.top||r.bottom>R.bottom) el.scrollTop+=r.top-R.top-4; }
}
addEventListener('resize',()=>{ fitCharList(); });
/* 공식 월드 아이콘 (tools/build_worlds.py → src/worldicons.json). 없는 월드는 아이콘 없이 이름만. */
const WORLD_ICONS = /*__WORLD_ICONS__*/{};
function worldIcon(w){ w=String(w||''); const k=WORLD_ICONS[w]?w:['챌린저스','버닝'].find(p=>w.startsWith(p)&&WORLD_ICONS[p]);
  return k?`<img class="wico" src="${WORLD_ICONS[k]}" alt="" aria-hidden="true">`:''; }
/* 월드 탭: 사이드바 캐릭터 카드에 '[아이콘]스카니아 (3) ㅣ [아이콘]루나 (2)' — 고른 월드의 캐릭터만 표시. 선택은 기기별 localStorage. */
const WORLD_TAB_KEY='mapleBossTracker.worldTab';
let worldTab=(()=>{ try{ return localStorage.getItem(WORLD_TAB_KEY)||''; }catch(e){ return ''; } })();
let seenActive=null, dndEndAt=0;
function setWorldTab(w){ worldTab=w; try{ localStorage.setItem(WORLD_TAB_KEY,w); }catch(e){} render(); }
const CHAR_PER_PAGE=8; let charPage=1, charPageKey='';
function renderChars(){
  if(dnd) return; // 드래그 중에는 다시 그리지 않음
  const el=$('#charList'), tabsEl=$('#worldTabs');
  const fixed=charSort!=='base'; // 미완료순 보기에서는 순서 바꾸기(드래그·▲▼) 잠금 — 기본순에서만
  el.classList.toggle('sorted',fixed);
  if(!vchars().length){ if(tabsEl) tabsEl.innerHTML=''; if($('#charPager')) $('#charPager').hidden=true; el.innerHTML='<div class="muted" style="padding:8px 2px">아직 캐릭터가 없습니다.<br><b>+ 추가</b> 또는 아래 <b>넥슨 API</b>로 불러오세요.</div>'; fitCharList(); return; }
  const groups=worldGroups(); const worlds=[...groups.keys()];
  // 다른 곳(수익 요약 등)에서 다른 월드 캐릭터를 고르면 그 월드 탭으로
  const act=activeChar();
  if(seenActive===null) seenActive=S.activeId;
  else if(S.activeId!==seenActive){ seenActive=S.activeId; if(act&&worldOf(act)!==worldTab){ worldTab=worldOf(act); try{ localStorage.setItem(WORLD_TAB_KEY,worldTab); }catch(e){} } }
  if(!groups.has(worldTab)) worldTab=(act&&groups.has(worldOf(act)))?worldOf(act):worlds[0];
  const multi=worlds.length>1;
  const sortCtl=`<span class="charsort" role="group" aria-label="캐릭터 정렬 (보기만 바뀌고 저장된 순서는 그대로)">${[['base','기본순','내가 정한 순서'],['undone','보스 미완료순','이번 주 주간 보스 12개를 아직 다 안 잡은 캐릭터 먼저 (각 무리 안은 기본순)'],['gm','검마 정렬순','이번 달 검은 마법사를 아직 안 잡은 캐릭터 먼저 (각 무리 안은 기본순)']].map(([k,l,t])=>`<button type="button" class="sortlink${charSort===k?' on':''}" data-csort="${k}" aria-pressed="${charSort===k}" title="${t}">${l}</button>`).join('')}</span>`;
  if(tabsEl) tabsEl.innerHTML=`<span class="wtablist" role="tablist" aria-label="월드">${worlds.map((w,i)=>(i?'<span class="wdiv" aria-hidden="true">ㅣ</span>':'')+
      `<span role="tab" tabindex="0" class="wtab${w===worldTab?' on':''}" aria-selected="${w===worldTab}" data-wtab="${esc(w)}" data-world="${esc(w)}" draggable="${multi}" title="${esc(w)} 캐릭터 ${groups.get(w).length}명${multi?' · 끌어서 월드 순서 변경':''}">${worldIcon(w)}<span class="wnm">${esc(w)}</span> <span class="cnt">(${groups.get(w).length})</span></span>`).join('')}</span>`;
  const list=sortedChars(groups.get(worldTab)||[]), w=worldTab;
  // 페이지: 8명씩. 월드 탭·정렬이 바뀌면 1쪽, 인원이 줄면 마지막 쪽으로
  const pk=worldTab+'|'+charSort; if(pk!==charPageKey){ charPageKey=pk; charPage=1; }
  const pages=Math.max(1,Math.ceil(list.length/CHAR_PER_PAGE)); charPage=Math.min(Math.max(1,charPage),pages);
  const p0=(charPage-1)*CHAR_PER_PAGE;
  let ft=$('#charFoot'); if(!ft){ ft=document.createElement('div'); ft.id='charFoot'; ft.className='cfoot'; el.after(ft); }
  let pg=$('#charPager'); if(!pg){ pg=document.createElement('div'); pg.id='charPager'; pg.className='cpager'; }
  ft.innerHTML=sortCtl; ft.appendChild(pg); // 정렬(왼쪽 아래) + 쪽 버튼
  pg.innerHTML=pages>1?Array.from({length:pages},(_,i)=>`<button type="button" class="cpg${i+1===charPage?' on':''}" data-cpage="${i+1}"${i+1===charPage?' aria-current="page"':''}>${i+1}</button>`).join(''):'';
  pg.hidden=pages<=1;
  el.innerHTML=list.slice(p0,p0+CHAR_PER_PAGE).map((c,cj)=>{const ci=p0+cj; const r=cRev(c);return `
    <div class="char ${c.id===S.activeId?'on':''}${charSort==='gm'?(gmDone(c)?' gmdone':''):r.weekly>=S.settings.weeklyLimit?' alldone':''}" data-id="${c.id}" data-world="${esc(w)}" draggable="${fixed?'false':'true'}">
      ${charSort==='gm'?(gmDone(c)?'<div class="dov gmov" aria-hidden="true"><div class="dov-t"><span class="dov-ok"><b class="dov-star">★</b>이번 달 검마 완료</span></div></div>':''):doneOverlay(c,r)}
      ${medalBand(c)}<span class="drag-h" title="드래그해서 순서 변경">⠿</span>
      ${avatar(c)}
      <div class="grow"><div class="nm">${esc(c.name)}</div><div class="meta lvrow"><span class="lv">Lv.${esc(c.level||'?')}</span><span class="job">${esc(c.job||'직업 미설정')}</span></div>${expLine(c)}</div>
      <div style="text-align:right"><div class="rev">${meso(r.meso)}</div><div class="meta">${r.weekly}/${S.settings.weeklyLimit}${needAssign(c)?' <span class="warnc" title="넥슨 계정 미지정 — ✎ 편집에서 계정을 선택하세요">⚠</span>':c.sync?.ok===false?' <span title="'+esc(c.sync.msg)+'">⚠</span>':''}</div></div>
      <div class="ordcol"><button class="ord" data-move="${c.id}|-1" ${ci===0||fixed?'disabled':''} title="위로" aria-label="위로">▲</button><button class="ord" data-move="${c.id}|1" ${ci===list.length-1||fixed?'disabled':''} title="아래로" aria-label="아래로">▼</button></div>
      <button class="btn sm plain" data-edit="${c.id}" title="수정">✎</button>
    </div>`}).join('');
  // 마지막 쪽도 8줄 높이 유지 → 쪽 버튼·아래 카드가 움직이지 않음
  el.style.minHeight='';
  if(pages>1){ const rows=el.querySelectorAll('.char[data-id]'); if(rows.length){ const r0=rows[0].getBoundingClientRect(), gap=rows.length>1?rows[1].getBoundingClientRect().top-r0.bottom:parseFloat(getComputedStyle(el).rowGap)||8;
    const pad=parseFloat(getComputedStyle(el).paddingTop)+parseFloat(getComputedStyle(el).paddingBottom);
    if(rows.length===CHAR_PER_PAGE) charRowsH=el.getBoundingClientRect().height; el.style.minHeight=(charRowsH||Math.ceil(r0.height*CHAR_PER_PAGE+gap*(CHAR_PER_PAGE-1)+pad))+'px'; } }
  fitCharList();
}
let charRowsH=0;

/* ---------- 드래그 앤 드롭: 데스크톱은 HTML5 DnD, 터치는 Pointer Events (⠿ 손잡이) ---------- */
let dnd=null; // {kind:'char'|'world', id, el}
function dndTarget(el, clientY, clientX){
  if(!dnd||!el) return null;
  if(dnd.kind==='char'){
    const t=el.closest('.char[data-id]'); if(!t||t===dnd.el||t.dataset.world!==dnd.el.dataset.world) return null;
    const r=t.getBoundingClientRect(); return {el:t, id:t.dataset.id, after: clientY>r.top+r.height/2};
  }
  const t=el.closest('.wtab[data-world]'); if(!t) return null;
  const w=t.dataset.world; if(w===dnd.id) return null;
  const r=t.getBoundingClientRect(); return {el:t, id:w, after: clientX>r.left+r.width/2};
}
function dndMark(t){
  document.querySelectorAll('.drop-before,.drop-after').forEach(e=>e.classList.remove('drop-before','drop-after'));
  if(t) t.el.classList.add(t.after?'drop-after':'drop-before');
}
function dndStart(kind,id,el){ dnd={kind,id,el}; el.classList.add('dragging'); document.body.classList.add('is-dragging'); }
function dndFinish(t){
  const d=dnd; dnd=null; dndEndAt=Date.now(); dndMark(null); document.body.classList.remove('is-dragging');
  if(d) d.el.classList.remove('dragging');
  if(d&&t){ const ok = d.kind==='char' ? moveCharTo(d.id,t.id,t.after) : moveWorldTo(d.id,t.id,t.after); if(ok) toast('순서를 변경했습니다'); }
  renderChars(); if(tab==='summary') renderSummary();
}
const charList=document.getElementById('charList').closest('.card'); // 월드 탭 + 캐릭터 목록 (드래그 이벤트 범위)
charList.addEventListener('dragstart',e=>{
  const tg=e.target&&e.target.nodeType===3?e.target.parentElement:e.target; // 글자(텍스트 노드)를 잡고 끌 때
  const row=tg?.closest?.('.char[data-id],.wtab[draggable="true"]'); if(!row){ e.preventDefault(); return; }
  if(row.classList.contains('wtab')) dndStart('world',row.dataset.world,row); else dndStart('char',row.dataset.id,row);
  e.dataTransfer.effectAllowed='move'; try{ e.dataTransfer.setData('text/plain',dnd.id); }catch(_){}
});
charList.addEventListener('dragover',e=>{ const t=dndTarget(e.target,e.clientY,e.clientX); dndMark(t); if(t){ e.preventDefault(); e.dataTransfer.dropEffect='move'; } });
charList.addEventListener('drop',e=>{ e.preventDefault(); dndFinish(dndTarget(e.target,e.clientY,e.clientX)); });
charList.addEventListener('dragend',()=>{ if(dnd) dndFinish(null); });
// 터치(또는 펜): ⠿ 손잡이를 눌러 끌기
let wPend=null; // 터치: 월드 탭을 옆으로 10px 이상 끌면 순서 바꾸기 시작
charList.addEventListener('pointerdown',e=>{
  if(e.pointerType==='mouse') return; // 마우스는 HTML5 DnD 사용
  const wt=e.target.closest('.wtab[draggable="true"]'); if(wt){ wPend={el:wt,x:e.clientX,y:e.clientY,id:e.pointerId}; return; }
  const h=e.target.closest('.drag-h'); if(!h) return;
  const row=h.closest('.char[data-id]'); if(!row) return;
  if(charSort!=='base') return; // 미완료순·검마순 보기에서는 캐릭터 순서 잠금
  e.preventDefault();
  dndStart('char',row.dataset.id,row);
  dnd.pointerId=e.pointerId; dnd.last=null;
  try{ h.setPointerCapture(e.pointerId); }catch(_){}
});
document.addEventListener('pointermove',e=>{
  if(wPend&&!dnd&&wPend.id===e.pointerId&&Math.abs(e.clientX-wPend.x)>10){ dndStart('world',wPend.el.dataset.world,wPend.el); dnd.pointerId=e.pointerId; dnd.last=null; wPend=null; }
  if(!dnd||dnd.pointerId!==e.pointerId) return;
  e.preventDefault();
  const under=document.elementFromPoint(e.clientX,e.clientY);
  dnd.last=dndTarget(under,e.clientY,e.clientX); dndMark(dnd.last);
  if(e.clientY<40) window.scrollBy(0,-12); else if(e.clientY>innerHeight-40) window.scrollBy(0,12);
},{passive:false});
document.addEventListener('pointerup',e=>{ wPend=null; if(dnd&&dnd.pointerId===e.pointerId) dndFinish(dnd.last); });
document.addEventListener('pointercancel',e=>{ if(dnd&&dnd.pointerId===e.pointerId) dndFinish(null); });
function renderResetInfo(){
  const now=Date.now(), nw=weekStartMs(now)+7*864e5;
  const d=kst(now); const nm=Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,1)-KST_MS;
  const el=$('#resetInfo'); if(!el) return; // 보스 체크 탭 오른쪽 열 맨 아래 카드 (2026-10-10: 왼쪽 사이드바에서 이동)
  el.innerHTML=`<b>초기화까지 (KST)</b><br>주간(목 00:00): ${untilText(nw-now)}<br>월간(1일 00:00): ${untilText(nm-now)}<br><span style="font-size:.78rem">이번 주: ${fmtWeek(S.period.week)}</span>`;
}
function emptyView(){ return `<div class="card empty"><div class="big">🍁</div><h2 style="justify-content:center">캐릭터를 추가해 보세요</h2><p class="muted">넥슨 Open API 키로 내 계정의 본캐·부캐를 한 번에 불러올 수 있어요.</p>
  <div class="toolbar" style="justify-content:center"><button class="btn" id="importAccBtn">+ 캐릭터 추가 (API 키로 불러오기)</button></div>
  <div class="empty-attrib muted">Data based on NEXON Open API</div></div>${landingHtml()}`; }
/* b203: 로그인 전 첫 화면(= 보이는 캐릭터 없을 때 emptyView, 규칙 10 — 로그인했지만 캐릭터가 없을 때도 같은 화면) — 사이트 소개 + 실제 결정석/아이템 가격 카드(읽기 전용, 공용 가격) */
function landingHtml(){ return `<div class="landing">
  <section class="card seoland" aria-labelledby="landH"><h2 id="landH">메이플스토리 보스 수익·결정석 기록, 메보기</h2>
   <p class="muted">주간 보스와 검은 마법사를 잡을 때마다 결정석 수익을 캐릭터별로 자동 계산해 주는 무료 사이트예요. 넥슨 Open API 키로 캐릭터를 불러오면 게임 스케줄러의 클리어가 자동으로 체크돼요.</p>
   <ul class="seofeat"><li><b>보스 수익 계산</b> — 이번 주 수익, 남은 결정석, 검마 결정석</li><li><b>주간 보스 기록</b> — 캐릭터별 처치 현황과 주간 메소 그래프</li><li><b>득템 기록</b> — 반지 상자·블랙 아이템 드롭과 아이템 판매 수익</li></ul></section>
  <div class="landprices">${priceCard({kind:'cry',land:true})}${priceCard({kind:'item',land:true})}</div></div>`; }

function renderBoss(){
  const v=$('#view'); const c=activeChar();
  if(!c){ v.innerHTML=emptyView(); fitPriceCard(); return; }
  const r=cRev(c); const a=COMMITTED(allRevenue);
  const lim=S.settings.weeklyLimit;
  const bosses=BOSSES.filter(b=>b.type===bossFilter);
  const shown=editMode?bosses:bosses.filter(b=>bossOn(c,b)); // b241: 주간 12개까지
  const cntType=t=>BOSSES.filter(b=>b.type===t&&bossOn(c,b)).length;
  const doneType=t=>BOSSES.filter(b=>b.type===t&&bossOn(c,b)&&isDone(c,b)).length;
  const sy=c.sync||{};
  const acc=accOf(c);
  const syncLine = needAssign(c) ? `<span class="pill err">계정 미지정</span> <span class="muted">이 캐릭터의 넥슨 계정을 선택해야 자동 체크가 됩니다.</span> <button class="btn sm ghost" data-edit="${c.id}">계정 선택</button>`
    : c.ocid ? (sy.ok===false ? `<span class="pill err">API 실패</span> <span class="muted">${esc(sy.msg)}</span>`
      : sy.at ? `<span class="muted">게임 내 주간 보스 처치 <b>${sy.clear??'?'} / ${sy.limit||lim}</b> · <span title="${hm(sy.at)} KST">갱신완료 ${(d=>String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0'))(new Date(sy.at))}</span>${(um=>um.length?` · 매칭 안 된 보스: ${esc(um.join(', '))}`:'')((sy.unmatched||[]).filter(x=>!isSeasonBoss(x)))}</span>` : '<span class="muted">API 연결 캐릭터 — 아직 동기화 전</span>')
    : '<span class="muted">수동 캐릭터 (API 미연결)</span>';
  v.innerHTML=`<div class="bosslay"><div class="grid">
   <div class="card">
    <div style="display:flex;gap:12px;align-items:center;margin-bottom:10px">${avatar(c,'lg')}
      <div style="flex:1;min-width:0"><h2 style="margin:0">${esc(c.name)}${c.isMain?'<span class="mainbadge">★ 본캐</span>':''}</h2>
      <div class="muted">Lv.${esc(c.level||'?')} · ${esc(c.job||'')} · ${esc(worldOf(c))}${(()=>{ const ex=remainingWeekly(c); if(!ex.list.length&&!ex.mon.length) return ''; // 주간 12개 + 월간 다 잡으면 숨김
        return ` <span class="expinc" title="${esc(`남은 예상 수익 — 이번 주 ${ex.done}/${S.settings.weeklyLimit} 처치, 남은 ${ex.left}칸을 아직 안 잡은 보스 중 1인당 결정석 가격 상위로 채울 때\n`+[...ex.list,...ex.mon].map(x=>`· ${x.monthly?'[월간] ':''}${bossTag(x)} ${meso(x.value)}`).join('\n'))}">${miniIcon('ipc')}예상 <b>${meso(ex.meso)}</b><small>(${[ex.list.length?`상위 ${ex.list.length}개`:'',ex.mon.length?`월간 ${ex.mon.length}개`:''].filter(Boolean).join(' + ')})</small>${(u=>u!==null&&u!==ex.meso?`<small class="exp-up">테섭 예정 → ${meso(u)}</small>`:'')(withUpcoming(()=>remainingWeekly(c).meso))}</span>`; })()}</div><div style="margin-top:4px;font-size:.85rem">${syncLine}</div>${bossNextNote(c)}</div></div>
    ${c.medal?.bad?`<div class="medalrow" role="alert" title="${esc(medalTip(c))}"><span class="mdico"><img src="${ITEM_ICONS.pcmedal||''}" alt="${MEDAL_BAD} 훈장" width="32" height="32"><span class="mdtri" aria-hidden="true">!</span></span><span class="mdtxt">${c.medal.empty?`보스 프리셋${c.medal.preset?" "+c.medal.preset:""}에 훈장이 없는 캐릭터 입니다.`:"프리미엄 PC방 훈장을 착용한 캐릭터 입니다."}</span></div>`:''}
    <div class="stats s3">
      <div class="stat"><div class="k">이번 주 주간 보스 수익</div><div class="v acc tirv">${tirMeso(r.meso+pWeekMonthly({c,r}).meso+pItemSale(c),'ci:'+c.id)}</div></div>
      <div class="stat"><div class="k">주간 보스 처치</div><div class="v">${r.weekly} / ${lim}</div><div class="bar ${r.weekly>lim?'over':''}"><i style="width:${Math.min(100,r.weekly/lim*100)}%"></i></div></div>
      <div class="stat"><div class="k">이번달 검마${(ds=>ds.length?` <span class="mdate">(${ds.join(', ')} 격파 완료)</span>`:'')(Object.keys(c.monthly).map(k=>(c.mdate||{})[k]).filter(Boolean).map(d=>`${+d.slice(5,7)}월 ${+d.slice(8,10)}일`))}</div><div class="v">${monthlyCount(c)} / ${S.settings.monthlyLimit}${r.monthMeso?` <span class="mmeso">${meso(r.monthMeso)}</span>`:''}</div><div class="bar"><i style="width:${Math.min(100,monthlyCount(c)/S.settings.monthlyLimit*100)}%"></i></div></div>
      
    </div>
   </div>
   <div class="card">
    <div class="toolbar" style="margin-bottom:10px">
      <div class="seg">${['weekly','monthly'].map(t=>`<button data-filter="${t}" class="${bossFilter===t?'on':''}">${TYPE_LABEL[t]} <span style="opacity:.8">${doneType(t)}/${cntType(t)}</span></button>`).join('')}</div>${weeklyOver(c)||Object.keys(c.bossNext||{}).length?`<span class="bover" role="note">*스케줄러에 등록된 보스가 12마리를 초과했거나, 보스 클리어 후 스케줄러를 수정하여<br>&nbsp;일부 보스가 미출력됩니다.</span>`:''}
      <span style="flex:1"></span>
      ${(!pend&&pendDoneAt&&Date.now()-pendDoneAt<3000)?'<span class="pdone" role="status">저장이 완료되었습니다.</span>':''}${(on=>`<button class="pbtn prevall on" id="revAllBtn" type="button">수익 기록 전체 수정</button><button class="pbtn pcancel${on?' on':''}" id="pendCancel" ${on?'':'disabled'}>취소</button><button class="pbtn psave${on?' on':''}" id="pendSave" ${on?'':'disabled'}>저장</button>`)(!!pend)}
    </div>
    <div class="boss-list">${shown.length?shown.map(b=>bossRow(c,b)).join(''):`<div class="empty muted">${c.ocid?`게임 스케줄러에 등록된 ${TYPE_LABEL[bossFilter]}가 없습니다.<br>게임에서 보스를 스케줄러에 등록한 뒤 동기화(↻)하면 자동으로 표시돼요.`:`넥슨 API로 불러온 캐릭터만 보스가 자동 표시돼요.<br>캐릭터 편집에서 API 키 계정에 연결해 주세요.`}</div>`}</div>
   </div></div><div class="rcol">${COMMITTED(()=>revPanel(allRevenue(activeChars()),activeChar()))}${priceCard()}<div class="card resetcard"><div class="muted" id="resetInfo"></div></div></div></div>`;
}
/* b58: 월간 보스는 '잡은 주'(c.monthly[slot] = 클리어한 주 key)가 현재 주일 때만 이번 주 수익 표시에 합산 — 표시 전용, allRevenue/weekSummary/monthSummary/history 는 건드리지 않음(이중 계산 방지) */
const pWeekMonthly = p => { const l=p.r.mlist.filter(x=>x.counted&&p.c.monthly[x.slot]===S.period.week); return {n:l.length, meso:l.reduce((t,x)=>t+x.value,0), any:p.r.mlist.some(x=>p.c.monthly[x.slot]===S.period.week)||Object.values(p.c.monthly||{}).some(w=>w===S.period.week)}; };
/* b110: 아이템 판매값 (수익 기록 창·전체 수정에서 넣은 c.drev/c.mdrev, 분배면 내 몫). 기록 안 한 아이템 = 0.
 * 그 아이템을 판 캐릭터에만, 준 보스 종류대로: 주간 보스 아이템(drev) → 주간, 검은 마법사 아이템(mdrev) → 월간(이번 주 표시는 검마를 잡은 주일 때만, 결정석과 같은 규칙) */
const revSum = m => Object.values(m||{}).reduce((t,r)=>t+(r&&+r.m>0?+r.m:0),0);
const pItemSale = c => revSum(c.drev) + Object.entries(c.mdrev||{}).reduce((t,[k,r])=>t+(r&&+r.m>0&&c.monthly?.[k.split('|')[0]]===S.period.week?+r.m:0),0);
// b112: 이번 주 가장 비싸게 판 아이템의 아이콘 (보이는 캐릭터, pItemSale 과 같은 범위). 판 게 없으면 아이콘 없음
function topSaleIco(){ let best=null; for(const c of activeChars()){ const L=[...Object.entries(c.drev||{}),...Object.entries(c.mdrev||{}).filter(([k])=>c.monthly?.[k.split('|')[0]]===S.period.week)];
    for(const [k,r] of L) if(r&&+r.m>0&&(!best||+r.m>best.m)) best={m:+r.m,i:r.i||k.split('|')[1]}; }
  try{ return best?`<span class="rpsico" title="${esc(lootName(best.i))}">${lootIco(best.i)}</span>`:''; }catch(e){ return ''; } }
/* b118: 이번 주 수익 보스 아이콘 순서 = 보스 드랍 표 순서(BOSSES 순서 = 인게임 스케줄러 순서), 검은 마법사는 항상 맨 오른쪽 */
function bossTblOrd(slot){ const b=findBoss(slot); if(!b) return 1e5; return b.id==='blackmage'?1e4:BOSSES.indexOf(b); }
/* b116: 이번 주 수익 캐릭터별 '이번주 아이템 판매금' — 아이콘 = 그 캐릭터가 이번 주 가장 비싸게 판 아이템(칠흑 장신구 상자에서 나온 것이면 상자 아이콘). 판 게 없으면 줄 없음 */
function charSaleLine(c){ const sale=pItemSale(c); if(!(sale>0)) return ''; let best=null;
  const L=[...Object.entries(c.drev||{}),...Object.entries(c.mdrev||{}).filter(([k])=>c.monthly?.[k.split('|')[0]]===S.period.week)];
  for(const [k,r] of L) if(r&&+r.m>0&&(!best||+r.m>best.m)) best={m:+r.m,k,i:r.i||k.split('|')[1]};
  const box=best&&(/^cb:/.test(best.i)||parseIK(best.k).it==='chaosbox'); let ico=''; try{ ico=best?lootIco(box?'chaosbox':best.i):''; }catch(e){}
  return `<div class="rp-cl rp-sl">${ico}<span>이번주 아이템 판매금 ${meso(sale)}</span></div>`; }
/* b121: 이번 주 반지 상자 줄 — 가장 많이 얻은 상자 아이콘(같으면 아이템 순서 = 생명→백옥→흑옥→녹옥→홍옥) · 상자 수 · 결과(리4·컨4·연마석·꽝, 0개 숨김). 범위 = '이번주 획득 아이템'과 같은 이번 주 주간 드롭 */
function weekRingLine(){ const by={}, t={r4:0,c4:0,gl:0,x:0}; let n=0;
  for(const c of activeChars()){ const d=charDrops(c,'weekly'); for(const [k,v] of Object.entries(d.items)){ const {it}=parseIK(k); if(!isRing(it)) continue; n+=+v; by[it]=(by[it]||0)+(+v); const o=outTally(d.outcomes[k],v); for(const q in t) t[q]+=o[q]; } }
  if(!n) return ''; const top=Object.keys(by).sort((x,y)=>by[y]-by[x]||itemCmp(x,y))[0];
  // b213: 결과 = 위아래 줄 숫자처럼 오른쪽 숫자 칸(.rpn), 리4·컨4 앞에 리스트레인트·컨티뉴어스 링 아이콘(글씨 높이)
  // b214: 리4·컨4·연마석 = 아이콘 + xN (글자 없음, 말풍선 = 이름), 꽝 = 글자 '꽝 xN'. 개수 표기 xN
  const RI={r4:['ring_restraint',OUT_NAME.r4],c4:['ring_continuous',OUT_NAME.c4],gl:['g_life',ITEMS.g_life.n]};
  const R=['r4','c4','gl','x'].filter(q=>t[q]>0).map(q=>RI[q]?`<span class="rpo rio-${q}" data-tip="${esc(RI[q][1]+' '+xN(t[q]))}" aria-label="${esc(RI[q][1]+' '+xN(t[q]))}">${miniIcon(RI[q][0])}${tsm(xN(t[q]))}</span>`:`<span class="rpo">${tsm('꽝 '+xN(t[q]))}</span>`).join('');
  return `<div class="muted rp-line rp-ring rc-y"><span class="rpl"><span class="rpg">${itemIcon(top)}${rpLbl('반지 상자',n)}</span></span>${R?`<b class="rpn rpouts">${R}</b>`:''}</div>`; }
/* b185: 남은 결정석 — 주간 = remainingWeekly(c).list(남은 칸만큼, 안 잡은 보스 1인당 가격 상위), 검마 = 이번 달 안 잡은 검은 마법사. 보이는 캐릭터만(규칙 9), 0이면 줄 없음 */
const leftOf = c => { const r=remainingWeekly(c), bm=r.mon.filter(x=>x.slot==='blackmage'); return {w:r.list.reduce((t,x)=>t+x.value,0), m:bm.reduce((t,x)=>t+x.value,0), wn:r.list.length, mn:bm.length}; }; // b221: wn = 남은 주간 결정석 개수(캐릭터당 12칸 − 잡은 수, 켜 둔 안 잡은 보스만큼)
const leftLine = (cls,ico,lb,v,big,n) => v>0?(big?`<div class="muted rp-line rp-left ${cls}"><span class="rpl"><span class="rpg">${ico}${rpLbl(lb,n)}</span></span><b class="rpn"><span class="tsmn">-${v.toLocaleString()}</span></b></div>`:`<div class="rp-cl rp-left ${cls}">${ico}<span>${lb} -${meso(v)}</span></div>`):'';
function weekLeftLines(cs){ let w=0,m=0,wn=0,mn=0; const VI=activeIds(); for(const c of cs){ if(!charShown(c)||!VI.has(c.id)) continue; const o=leftOf(c); w+=o.w; m+=o.m; wn+=o.wn; mn+=o.mn; }
  return leftLine('rl-w',miniIcon('ipc'),'이번 주 남은 결정석',w,1)/* b230: 개수 표시 없음 */+leftLine('rl-m',miniIcon('ipcm'),'검마 남은 결정석',m,1)/* b231: 개수 표시 없음 */; }
function charLeftLines(c){ const o=leftOf(c); return leftLine('rl-w',miniIcon('ipc'),'이번 주 남은 결정석',o.w)+leftLine('rl-m',miniIcon('ipcm'),'검마 남은 결정석',o.m); }
function weekMonthly(a){ let n=0, meso=0; a.per.forEach(p=>p.r.mlist.filter(x=>x.counted&&p.c.monthly[x.slot]===S.period.week).forEach(x=>{ n++; meso+=x.value; })); return {n,meso}; }
/* b266: 이번 주 현황 게이지 — 주간 결정석 개수만. 캐릭터마다 min(주간 한도, 켜 둔 주간 보스 수) 칸, 잡은 수 = min(한도, weeklyCount). 보이는(키 있는) 캐릭터만
 * 0~32.99% 빨강 · 33~65.99% 주황 · 66~99.99% 밝은 하늘 · 100% 빛나는 순금. X/Y = 7세그먼트(SVG) 디지털 글씨 */
function weekGaugeData(cs){ const lim=S.settings.weeklyLimit, VI=activeIds(); let done=0,total=0;
  for(const c of cs){ if(!charShown(c)||!VI.has(c.id)) continue; const d=Math.min(lim,weeklyCount(c)); done+=d; total+=Math.max(d,Math.min(lim,expectedAll(c).length)); }
  const pct=total?done/total*100:0; return {done,total,pct,cls:total&&done>=total?'g-gold':pct>=66?'g-sky':pct>=33?'g-org':'g-red'}; }
const SEG7={0:'abcdef',1:'bc',2:'abged',3:'abgcd',4:'fgbc',5:'afgcd',6:'afgedc',7:'abc',8:'abcdefg',9:'abcdfg'};
const SEG7P={a:'2,1 8,1 7,2.6 3,2.6',b:'8.6,1.6 8.6,8.4 7.4,7.6 7.4,2.6',c:'8.6,9.6 8.6,16.4 7.4,15.4 7.4,10.4',d:'2,17 8,17 7,15.4 3,15.4',e:'1.4,9.6 2.6,10.4 2.6,15.4 1.4,16.4',f:'1.4,1.6 2.6,2.6 2.6,7.6 1.4,8.4',g:'2,9 3,8.2 7,8.2 8,9 7,9.8 3,9.8'};
function seg7(str,h=22){ let x=0; const g=[...String(str)].map(ch=>{ let o='';
    if(ch==='%'){ o=`<rect x="${x+1}" y="1.5" width="2.6" height="2.6" class="on"/><rect x="${x+6.4}" y="13.9" width="2.6" height="2.6" class="on"/><polygon points="${x+1.2},17 ${x+2.6},17 ${x+8.8},1 ${x+7.4},1" class="on"/>`; x+=10.5; return o; }
    if(ch==='/'){ o=`<polygon points="${x+1},17 ${x+2.4},17 ${x+7},1 ${x+5.6},1" class="on"/>`; x+=8; return o; }
    const on=SEG7[ch]||''; o=Object.entries(SEG7P).map(([k,p])=>`<polygon transform="translate(${x} 0)" points="${p}" class="${on.includes(k)?'on':'off'}"/>`).join(''); x+=10.5; return o; }).join('');
  return `<svg class="seg7" viewBox="0 0 ${x} 18" width="${(x*h/18).toFixed(1)}" height="${h}" role="img" aria-label="${esc(String(str))}">${g}</svg>`; }
/* b269: 이번 달 검마 진행도 — 검은 마법사만, 월간 기간(S.period.month, 매달 1일 00:00 KST 초기화) 그대로. 검마 켜 둔 보이는(키 있는) 캐릭터 = Y, 이번 달 잡음(c.monthly.blackmage) = X
 * 0~32.99% 회색 · 33~65.99% 노랑 · 66~99.99% 분홍 · 100% 빛나는 빨강 */
function monthGaugeData(cs){ const VI=activeIds(); let done=0,total=0;
  for(const c of cs){ if(!charShown(c)||!VI.has(c.id)||!c.bosses?.blackmage?.enabled) continue; total++; if(c.monthly?.blackmage) done++; }
  const pct=total?done/total*100:0; return {done,total,pct,cls:total&&done>=total?'g-mred':pct>=66?'g-pink':pct>=33?'g-yel':'g-gray'}; }
function gaugeHtml(g,lab,kind){ const p=weekGaugePct(g), full=g.total&&g.done>=g.total;
  return `<div class="rp-gauge ${kind} ${g.cls}" data-pct="${g.pct.toFixed(2)}" title="${lab} ${g.done}/${g.total} (${p}%)"><div class="rpg-col"><div class="rpg-bar"><i style="width:${Math.min(100,g.pct).toFixed(2)}%"></i></div><span class="rpg-xy">${lab} ${g.done}/${g.total}</span></div><span class="rpg-num"><span class="tsmn rpg-t">${p}%</span><span class="tsmn rpg-ing">${full?'완료':'진행중'}</span></span></div>`; }
function weekGauge(cs){ const g=weekGaugeData(cs), m=monthGaugeData(cs); return (g.total?gaugeHtml(g,'이번 주 결정석 진행도','rpg-w'):'')+(m.total?gaugeHtml(m,'이번 달 검마 진행도','rpg-m'):''); }
// b269: 진행률 = 소수 둘째 자리 내림(58.333 → 58.33) → 100.00% 는 다 잡았을 때만
const weekGaugePct = g => g.total&&g.done>=g.total?'100.00':Math.min(99.99,Math.floor(g.done*10000/(g.total||1))/100).toFixed(2);
/* 보스 체크 탭 오른쪽 패널: 이번 주 수익 합계 · 캐릭터별 수익 (좁은 화면에서는 아래로 쌓임) */
function revPanel(a,cur){
  const lim=S.settings.weeklyLimit;
  const per=orderedChars().map(c=>a.per.find(p=>p.c===c)).filter(Boolean);
  const pm=new Map(per.map(p=>[p,pWeekMonthly(p)])), pmeso=p=>p.r.meso+pm.get(p).meso+pItemSale(p.c);
  const max=Math.max(1,...per.map(pmeso));
  const wm=weekMonthly(a);
  /* b115: 이번 주 수익(결정석 + 아이템 판매) 높은 순, 순위 표시(같으면 같은 순위, 0 = 순위 없음). 1~3위 = 다른 순위 카드와 같은 메달 효과 */
  per.sort((x,y)=>pmeso(y)-pmeso(x)); const rk=new Map(); per.forEach((p,i)=>rk.set(p,pmeso(p)>0?(i&&pmeso(per[i-1])===pmeso(p)?rk.get(per[i-1]):i+1):0));
  return `<aside class="revpanel card" aria-label="이번 주 수익 총합">
    <h2>${miniIcon('meso')} 이번 주 수익 총합</h2>
    <div class="muted" style="font-size:.75rem;margin-top:-6px">${fmtWeek(S.period.week)}</div>
    ${(()=>{ const cry=a.total+wm.meso, sale=per.reduce((t,p)=>t+pItemSale(p.c),0), n=activeChars().reduce((t,c)=>t+Object.entries(c.drops||{}).reduce((x,[k,v])=>x+itemCnt(k,v,c.dropOut),0)+Object.entries(c.mdrops||{}).reduce((x,[k,v])=>x+(c.monthly?.[parseIK(k).slot]!==S.period.week?0:itemCnt(k,v,c.mdropOut)),0),0); // b121: 반지 상자 제외(아래 '반지 상자' 줄) — b226: 단 결과가 리4·컨4·연마석이면 셈(itemCnt) · b225: 이번 주에 잡은 검마 아이템(mdrops)도 셈 (판매 금액 pItemSale 과 같은 규칙)
      return `<div class="rp-total tirv tgoldv">${tirN(cry+sale,'eok','rp',' 메소')}</div>${weekGauge(per.map(p=>p.c))}
    <div class="muted rp-line rp-cry rc-g"><span class="rpl"><span class="rpg">${miniIcon('ipc')}${rpLbl('주보 결정석')/* b230: 개수 표시 없음 */}</span></span><b class="rpn">${tsm('+'+a.total.toLocaleString())}</b></div>${wm.n||wm.meso?`<div class="muted rp-line rp-cry rp-cm rc-g"><span class="rpl"><span class="rpg">${miniIcon('ipcm')}${rpLbl('검마 결정석')/* b232: 개수 표시 없음 */}</span></span><b class="rpn">${tsm('+'+wm.meso.toLocaleString())}</b></div>`:''}
    <div class="muted rp-line rp-sale rc-g"><span class="rpl"><span class="rpg">${topSaleIco()||'<span class="ric rpico0" aria-hidden="true"></span>'}${rpLbl('이번주 획득 아이템',n,1)}</span></span><b class="rpn">${tsm('+'+sale.toLocaleString())}</b></div>${weekRingLine()}${weekLeftLines(per.map(p=>p.c))}`; })()}
    <div class="rp-sec">캐릭터별</div>
    <div class="rp-list">${per.map(p=>`<div class="rp-char ${p.c===cur?'on':''}" data-id="${p.c.id}" title="${esc(p.c.name)} 선택">
      <div class="rp-row rp-top">${(r=>`<span class="rp-rk">${r?rankNo(r):'<span class="rkno"><span class="rkn">-</span></span>'}</span>${avatar(p.c,'sm av24 rp-av')/* b233: 주별 득템 표와 같은 24px 초상화(사진 없으면 같은 크기 글자 칸) */}<span class="rp-nm rkname${medal(r)?' md-'+medal(r):''}"><span class="${medal(r)?'spk':''}">${esc(p.c.name)}</span>${p.c.isMain?' <span class="mainbadge">★</span>':''}</span>`)(rk.get(p))}<b>${meso(pmeso(p))}</b></div>
      ${charLeftLines(p.c)}
      <div class="rp-row"><span class="mini"><i style="width:${(pmeso(p)/max*100).toFixed(1)}%"></i></span><span class="muted" style="font-size:.72rem;white-space:nowrap">${p.r.weekly}/${lim}</span></div>
      ${(L=>L.length?`<div class="rp-boss">${L.slice().sort((x,y)=>bossTblOrd(x.slot)-bossTblOrd(y.slot)).map(x=>bossPic(findBoss(x.slot),x.diff,false)).join('')}</div>`:'')([...p.r.wlist,...p.r.mlist.filter(x=>p.c.monthly[x.slot]===S.period.week)])}
      ${(w=>w?`<div class="rp-cl rc-g">${miniIcon('ipc')}<span>주간 결정석 +${meso(w)}</span></div>`:'')(p.r.wlist.length?p.r.meso:0)}${(m=>m?`<div class="rp-cl rc-g">${miniIcon('ipcm')}<span>검마 결정석 +${meso(m)}</span></div>`:'')(pm.get(p).meso)}${charSaleLine(p.c)}
      ${(d=>itemsInline(d.items)?`<div class="rp-items">${itemsInline(d.items,{outs:d.outcomes,revs:d.revs,byBoss:true,bpic:true,diffOf:cfgDiff(p.c)})}</div>`:'')(charAllDrops(p.c))}</div>`).join('')}</div>
  </aside>`;
}
// 보스+난이도별 가격 행 (싼 순서) — 보스 체크 탭 가격 카드
let pcMine = localStorage.getItem('mapleBossTracker.pcMine')==='1';
// 내가 잡는 보스만: 등록된 캐릭터 중 하나라도 켜 둔 보스+난이도 (난이도는 따로)
const myBossKeys = () => new Set(activeChars().flatMap(c=>BOSSES.filter(b=>bossOn(c,b)).map(b=>{ const d=c.bosses[b.id].diff; return priceKey(b,b.diffs.includes(d)?d:b.diffs[0]); })));
const priceRows = g => { const mine=pcMine?myBossKeys():null; return priceRows0(g).filter(r=>!mine||mine.has(r.k)); };
const priceRows0 = g => BOSSES.filter(b=>b.type===g).flatMap(b=>b.diffs.map(d=>({b,d,k:priceKey(b,d),p:price(b,d)}))).sort((x,y)=>(x.p>0?x.p:Infinity)-(y.p>0?y.p:Infinity)); // b251: 가격 미확인(0) = 맨 아래
// b79: '마지막 확인' = KST 'MM.DD HH:MM' (예전 날짜만 있는 값은 'YYYY-MM-DD' 그대로)
const ckText = v => { const t=v&&/T\d/.test(v)?Date.parse(v):NaN; if(!isFinite(t)) return v||'-'; const d=new Date(t+9*3600e3), p=n=>String(n).padStart(2,'0'); return `${p(d.getUTCMonth()+1)}.${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`; };
// b171: 마지막 확인 = checkedAt·테섭 예정 반영 시각 중 늦은 것 (예전 prices.json 은 테섭 반영 때 checkedAt 을 안 바꿨음)
const lastCk = () => { const a=officialInfo.checkedAt||'', b=officialInfo.upAt||''; return (Date.parse(b)||0)>(Date.parse(a)||0)?b:a; };
const priceAutoText = () => officialInfo?`공식 패치 노트 기준 자동 갱신\n(가격 변동일 ${officialInfo.changedAt||'-'}, 마지막 확인 ${ckText(lastCk())})${Object.keys(officialInfo.upcoming||{}).length?`\n테섭 예정 가격: ${officialInfo.upSource?.title||'테스트 서버 공지'}${officialInfo.upAt?` (반영 ${ckText(officialInfo.upAt)})`:''}`:''}${officialInfo.pending.length?` · ${officialInfo.pending.length}개는 ${officialInfo.pending[0].effective}부터 적용`:''}`:'공식 패치 노트 기준 (온라인 주소에서 자동 갱신)';
/* 보스 체크 탭 오른쪽: 결정석 가격 (읽기 전용, prices.json 자동 갱신) */
// 테섭 예정 가격이 있을 때만: 캐릭터별 예상 주간 수익(주간 상위 12 + 월간) 현재 가격 vs 패치 후
let pcTab='price', pcKind='cry'; // b112: 가격 카드 탭 — 결정석 가격 / 아이템 가격
/* b112: 보스 드롭 표에서 수익 기록이 가능한 아이템 — 칠흑 상자 = 고른 장신구, 반지 상자 = 결과(리4·컨4·생명의 연마석). 정렬 = itemCmp(사용자 아이템 우선순위) */
function revItems(){ const set=new Set();
  BOSSES.forEach(b=>b.diffs.forEach(d=>dropsFor(b,d).forEach(k=>{ if(k==='chaosbox') CHAOS_PICK.forEach(x=>set.add('cb:'+x)); else if(isRing(k)){ set.add('ring:r4'); set.add('ring:c4'); set.add('g_life'); } else if(SJM_KEYS.has(k)) set.add('b_sjm'); /* b261 */ else if(!MISS_SKIP_SET.has(ITEMS[k]?.set)) set.add(k); }))); // b253: 로이드·소울 조각·방어구 상자 = 정보용(교환 불가·시세 없음) → 수익/시세 목록 제외
  const seen=new Set(); return [...set].sort(itemCmp).filter(k=>{ const id=priceId(k); if(seen.has(id)) return false; seen.add(id); return true; }); } /* b114: 칠흑 상자 선택(cb:lcm)과 직접 드롭(lcm)은 같은 아이템·같은 시세 → 한 번만 */
const priceId = k => (x=>SJM_KEYS.has(x)?'b_sjm':x)(String(k||'').replace(/^cb:/,'').replace(/^(?:ring:|hong_)(r4|c4)$/,'ring_$1')); // b261: 보스별 장신망 상자 4종 = b_sjm 시세 // b229: 홍옥 리4/컨4 = 같은 반지 → 같은 시세
document.addEventListener('click',e=>{ const t=e.target.closest('[data-pckind]'); if(!t) return; pcKind=t.dataset.pckind; repaintPrices(); });
/* b227: 주간(상위 N) · 검마(월간) 따로 — fullExpected = 둘의 합(예전 그대로) */
function expParts(c){ const w=expectedAll(c).slice(0,S.settings.weeklyLimit).reduce((s,x)=>s+x.value,0);
  const m=BOSSES.filter(b=>b.type==='monthly'&&c.bosses[b.id]?.enabled).reduce((s,b)=>{ const cfg=c.bosses[b.id], d=b.diffs.includes(cfg.diff)?cfg.diff:b.diffs[0]; return s+Math.floor(price(b,d)/curParty(c,b.id)); },0);
  return {w,m}; }
function fullExpected(c){ const x=expParts(c); return x.w+x.m; }
/* b227: '패치 후 예상 주간 수익' = 주간 메소(감소율%) + 검마 메소(감소율%) — 합친 한 숫자 대신 따로. 검마를 안 잡는 캐릭터(합계도 검마 0) = 검마 줄 없음(b228) */
function afterPatchHtml(){
  const rows=activeChars().map(c=>{ const a=expParts(c), b=withUpcoming(()=>expParts(c))||a; return {c,nw:a.w,nm:a.m,xw:b.w,xm:b.m}; }).filter(r=>r.nw||r.nm||r.xw||r.xm);
  const sum=k=>rows.reduce((s,r)=>s+(r[k]||0),0);
  const pct=(n,b)=>{ const d=n-b; return `<span class="pa-p ${d<0?'dn':d>0?'upx':''}">(${d>0?'+':d<0?'−':''}${b?Math.abs(d/b*100).toFixed(1):'0.0'}%)</span>`; };
  const part=(lb,n,b)=>(n||b)?`<span class="pa-k">${lb}</span> ${meso(n)} ${pct(n,b)}`:`<span class="pa-k">${lb}</span> <span class="pa-z">0 메소</span>`;
  const two=(xw,nw,xm,nm)=>`<b class="pa-v"><span class="pa-l">${part('주간',xw,nw)}</span>${(xm||nm)?`<span class="pa-l">+ ${part('검마',xm,nm)}</span>`:''}</b>`; // b228: 검마 0(안 잡음) = 검마 줄 없음
  const tip=r=>`${esc(r.c.name)} — 주간 ${meso(r.nw)} → ${meso(r.xw)} · 검마 ${meso(r.nm)} → ${meso(r.xm)} (현재 가격 → 패치 후)`;
  return `<div class="pc-list pa-list">${rows.map(r=>`<div class="pc-row pa-row" title="${tip(r)}">${avatar(r.c,'sm')}<span class="pc-nm">${esc(r.c.name)}</span>${two(r.xw,r.nw,r.xm,r.nm)}</div>`).join('')||'<div class="muted">캐릭터가 없어요</div>'}</div>
    <div class="pa-total"><span>합계</span>${two(sum('xw'),sum('nw'),sum('xm'),sum('nm'))}</div>
    <div class="pa-note muted">주간 상위 ${S.settings.weeklyLimit}개 · 테섭 예정 가격으로 계산 · (%) = 지금 가격 대비</div>`;
}
document.addEventListener('change',e=>{ if(e.target.id!=='pcMine') return; pcMine=e.target.checked; localStorage.setItem('mapleBossTracker.pcMine',pcMine?'1':'0'); repaintPrices(); });
document.addEventListener('click',e=>{ const t=e.target.closest('[data-pctab]'); if(!t) return; pcTab=t.dataset.pctab; repaintPrices(); });

// 결정석 가격 줄이 안 들어가면 자르지 않고 글자를 조금씩 줄임 (최소 .56rem)
/* b203: 가격 카드가 여러 개(로그인 전 첫 화면 = 결정석·아이템 두 장)일 수 있음 → 모두 다시 그림·맞춤. data-land = 첫 화면 카드(종류 고정·읽기 전용) */
function repaintPrices(){ document.querySelectorAll('.pricecard').forEach(el=>{ el.outerHTML=el.dataset.land?priceCard({kind:el.dataset.land,land:true}):priceCard(); }); fitPriceCard(); }
function fitPriceCard(){ document.querySelectorAll('.pricecard').forEach(fitOnePrice); fitRingLine(); }
/* b213: 반지 상자 줄이 카드 폭보다 길면(결과가 많을 때) 결과 글씨만 조금씩 줄임 — 줄바꿈·잘림 없음, 카드 크기 그대로 */
function fitRing1(r){ const o=r.querySelector('.rpouts'); if(!o||!r.clientWidth) return; o.style.fontSize='';
  for(let f=1; r.scrollWidth>r.clientWidth+.5 && f>.66; ){ f-=.03; o.style.fontSize=(.82*f).toFixed(3)+'rem'; } }
function fitRingLine(){ const ro=fitRingLine._ro||(fitRingLine._ro=typeof ResizeObserver==='function'?new ResizeObserver(es=>es.forEach(e=>fitRing1(e.target))):null);
  document.querySelectorAll('.rp-line.rp-ring').forEach(r=>{ fitRing1(r); ro?.observe(r); }); } // 폭이 바뀌면(스크롤바 등) 다시 맞춤
try{ document.fonts?.ready?.then(()=>fitRingLine()); }catch(e){}
function fitOnePrice(card){ if(!card||!card.querySelector('.pc-row')) return;
  // 폭이 허락하는 만큼 크게(최대 14px) → 안 들어가면 0.5px씩 줄임(최소 9px). 자르지 않음
  const over=()=>[...card.querySelectorAll('.pc-row')].some(r=>{ const n=r.querySelector('.pc-nm'); return n&&n.scrollWidth>n.clientWidth+0.5; });
  let fs=14; card.style.setProperty('--pcfs',fs+'px'); while(over()&&fs>9){ fs-=0.5; card.style.setProperty('--pcfs',fs+'px'); } }
function priceCard(opt={}){ /* b203: opt.kind = 종류 고정, opt.land = 로그인 전 첫 화면(읽기 전용: 종류 버튼 1개만·누를 수 없음, '내가 잡는 보스만'·패치 후 탭 없음) */
  const kind=opt.kind||pcKind, land=!!opt.land, LA=land?` data-land="${kind}"`:'';
  const up=(officialInfo&&officialInfo.upcoming)||{}, PR=land?priceRows0:priceRows;
  const row=r=>{ const u=up[r.k]; return `<div class="pc-row${u?' has-up':''}" title="${esc(r.b.name)} ${D[r.d]} — ${r.p.toLocaleString()} 메소${u?` · 테섭 예정 ${u.toLocaleString()} 메소`:''}">${bossPic(r.b,r.d,false)}<span class="pc-nm">${esc(r.b.name)} ${dlvHtml(r.d)}</span><b>${r.p>0?meso(r.p):'<span class="muted" title="공식 결정석 가격 미발표">가격 미확인</span>'}${u?`<span class="pc-up">테섭 예정 → ${meso(u)}</span>`:''}</b></div>`; };
  const kt0=`<div class="pc-kind" role="tablist"><button type="button" role="tab" data-pckind="cry" class="${pcKind==='cry'?'on':''}" aria-selected="${pcKind==='cry'}">${miniIcon('ipc')} 결정석 가격</button><button type="button" role="tab" data-pckind="item" class="${pcKind==='item'?'on':''}" aria-selected="${pcKind==='item'}">${itemIcon('genesis')} 아이템 가격</button></div>`;
  const kt=land?`<div class="pc-kind pc-kind-land"><span class="on">${kind==='item'?`${itemIcon('genesis')} 아이템 가격`:`${miniIcon('ipc')} 결정석 가격`}</span></div>`:kt0;
  if(kind==='item'){ const P=itemPrices();
    return `<aside class="card pricecard"${LA} aria-label="아이템 가격">${kt}
    <div class="pc-list pc-items">${revItems().map(k=>{ const o=P[priceId(k)]; return `<div class="pc-row pc-it" data-pit="${esc(k)}">${lootIco(k)}<span class="pc-nm">${esc(lootName(k))}</span><b>${o?meso(o.p):'- 메소'}</b></div>`; }).join('')}</div>
    <div class="pc-date muted tiny">가격 확인 : ${(t=>t?kstStamp(t):'-')(Math.max(0,...Object.values(P).map(o=>+o.t||0)))}</div>${priceSrcHtml('pc-date pc-src muted tiny')}
  </aside>`; }
  return `<aside class="card pricecard"${LA} aria-label="결정석 가격">${kt}
    ${land?'':`<div class="pc-head"><label class="pc-mine"><input type="checkbox" id="pcMine"${pcMine?' checked':''}> 내가 잡는 보스만 보기</label></div>`}
    ${!land&&Object.keys(up).length?`<div class="pc-tabs" role="tablist"><button type="button" role="tab" data-pctab="price" class="${pcTab==='price'?'on':''}">가격</button><button type="button" role="tab" data-pctab="after" class="${pcTab==='after'?'on':''}">패치 후 예상 주간 수익</button></div>`:''}
    ${!land&&Object.keys(up).length&&pcTab==='after'?afterPatchHtml():`<div class="pc-list">${PR('weekly').map(row).join('')}${(m=>m.length?`<div class="pc-sep">📅 월간 보스</div>${m.map(row).join('')}`:'')(PR('monthly'))}${!land&&pcMine&&!priceRows('weekly').length&&!priceRows('monthly').length?'<div class="muted">잡는 보스가 없어요</div>':''}</div>`}
    <div class="pc-foot muted">${esc(priceAutoText())}</div>
  </aside>`;
}
/* b127: 보스 드랍 테이블(이번 주 보스 행) 난이도 = 게임 보스 스케줄러 난이도 그림 (원본 68×18 픽셀 그대로).
 * 출처: media.maplestorywiki.net/yetidb/Boss_UI_Difficulty_-_{Easy,Normal,Hard,Chaos,Extreme}.png (위컴알). 글자는 화면 밖 sr 로 남김(검색·테스트·스크린리더) */
const diffImg=d=>ITEM_ICONS['dif_'+d]?`<span class="dimg" title="${D[d]}"><img src="${ITEM_ICONS['dif_'+d]}" alt="" width="68" height="18" aria-hidden="true"><span class="sr">${D[d]}</span></span>`:`<span class="pill">${D[d]}</span>`;
/* b129: 처치한 보스 = 난이도 그림 옆 'CLEAR' 그림 (68×18, 하드 그림 테두리·모양, 초록 #2eb852, 흰 글자).
 * b130: 글자를 스케줄러 그림에서 그대로 — C=CHAOS, L·R=NORMAL, E·A=EASY (가장자리 픽셀 포함), 글자 간격 1px·같은 줄 (/workspace/maple-boss-tracker/b130_clear_pill.png 그대로) */
const clearImg=()=>`<span class="dimg dclr" title="처치 완료"><img src="${ITEM_ICONS.dif_clear}" alt="" width="68" height="18" aria-hidden="true"><span class="sr">CLEAR</span></span>`;
function isDone(c,b){ return b.type==='weekly'?!!c.weekly[b.id]:!!c.monthly[b.id]; }
function bossRow(c,b){
  const slot=b.id; const cfg=c.bosses[slot]||{enabled:false,diff:b.diffs[0],party:1};
  const diff=cfg.diff||b.diffs[0]; const done=isDone(c,b); const pmax=partyMax(b,diff); const party=Math.min(pmax,cfg.party||1);
  const p=price(b,diff); const cr=charCrystals(c).find(x=>x.slot===slot);
  if(false){ // (예전 ⚙ 보스 선택/난이도 화면 — 2026-10-10 제거: 보스·난이도는 넥슨 스케줄러 API로만)
    return `<div class="boss" style="${cfg.enabled?'':'opacity:.7'}">
      <label class="chk ${cfg.enabled?'on':''}" data-toggle="${slot}">${cfg.enabled?'✓':''}</label>
      <div class="grow"><div class="bn">${bossIcon(b)}${esc(b.name)}</div>
        <div class="diffs">${b.diffs.map(d=>`<span class="diff ${d===diff?'sel':''}" data-setdiff="${slot}|${d}">${D[d]} · ${price(b,d)>0?meso(price(b,d)):'가격 미확인'}</span>`).join('')}</div></div>
    </div>`;
  }
  return `<div class="boss ${done?'done':''}">
    <div class="grow"><div class="bn">${bossPic(b,diff)}${esc(b.name)} ${diffImg(diff)}${done?clearImg():''}
      ${cr&&!cr.counted?'<span class="pill err">한도 초과</span>':''}</div>
      ${dropsHtml(b,diff,c)}
    </div>
    <div class="party">파티 <select data-party="${slot}" title="${pmax<CONFIG.MAX_PARTY?`${esc(b.name)} ${D[diff]}: 최대 ${pmax}인`:''}">${Array.from({length:pmax},(_,i)=>`<option ${party===i+1?'selected':''}>${i+1}</option>`).join('')}</select>인</div>
    <div class="price"><b>${meso(Math.floor(p/party))}</b>${party>1?`<br><span>(${meso(p)} ÷ ${party})</span>`:''}</div>
    ${b.type==='weekly'&&(RING_DROPS.r_red?.[b.id]||[]).includes(diff)?`<div class="rredrow">${rredBtn(b,c)}</div>`:''}
  </div>`; /* b229: 좁은 줄(보스 줄 < 400px)에서는 드롭 칸 안 버튼 대신 줄 맨 아래 한 줄 버튼(.rredrow) — 글자 그대로·안 잘림 */
}

/* 캐릭터 별 기록 (2026-10-10): 2026.10.08(이번 주 시작)부터 계속 쌓임, 초기화 없음.
 * 주간 수익 = 지난 주간 기록(S.history) + 이번 주 / 월간 = 월간 기록(S.monthHistory) + 이번 달 / ★득템 = 같은 기간 기록한 드롭 (아이템별 합계) */
const REC_START='2026-10-08';
function charRecords(){
  const a=allRevenue(activeChars()), R={}, VI=activeIds(); // zosu-apikey: 보이는 캐릭터만
  const get=(id,name)=>R[id]||(R[id]={w:0,m:0,items:{},name});
  const addItems=(r,items)=>{ for(const [k,n] of Object.entries(items||{})){ const {it}=parseIK(k); if(ITEMS[it]&&+n>0) r.items[it]=(r.items[it]||0)+(+n); } };
  (S.history||[]).filter(h=>String(h.week)>=REC_START).map(h=>activeRecords(h,VI)).forEach(h=>(h.perChar||[]).forEach(p=>{ const r=get(p.id,p.name); r.w+=+p.meso||0; addItems(r,p.items); }));
  (S.monthHistory||[]).filter(h=>String(h.month)>=REC_START.slice(0,7)).map(h=>activeRecords(h,VI)).forEach(h=>(h.perChar||[]).forEach(p=>{ const r=get(p.id,p.name); r.m+=+p.meso||0; addItems(r,p.items); }));
  a.per.forEach(p=>{ const r=get(p.c.id,p.c.name); r.w+=p.r.meso; r.m+=p.r.monthMeso||0; addItems(r,charAllDrops(p.c).items); });
  return R;
}
function lootHtml(items){
  const ks=Object.keys(items).sort((x,y)=>Object.keys(ITEMS).indexOf(x)-Object.keys(ITEMS).indexOf(y));
  return ks.length?ks.map(k=>`<span class="loot" title="${esc(ITEMS[k].n)}">${lootLabel(k,{name:esc(ITEMS[k].s||ITEMS[k].n),n:items[k]}).replace(' <b class="lx">','<b class="lx">')}</span>`).join(''):'<span class="muted">아직 없음</span>';
}
function renderSummary(){
  const v=$('#view'); if(!vchars().length){v.innerHTML=emptyView();fitPriceCard();return;}
  const R=charRecords();
  v.innerHTML=`<div class="grid"><div class="card"><h2>2026.10.08부터 지금까지의 캐릭터 별 수익 및 득템</h2>
    <div style="overflow-x:auto"><table class="rectab"><thead><tr><th>캐릭터</th><th>월드 · 직업</th><th class="num">주간 수익</th><th class="num">월간 보스</th></tr></thead><tbody>
    ${orderedChars().map(c=>{ const r=R[c.id]||{w:0,m:0,items:{}}; return `<tr><td><b>${esc(c.name)}</b>${c.isMain?'<span class="mainbadge">★</span>':''} <span class="muted">Lv.${esc(c.level||'?')}</span>
      <div class="lootrow"><span class="lootk"><span class="ystar">★</span>득템</span><span class="loots">${lootHtml(r.items)}</span></div></td>
      <td>${esc(worldOf(c))} · ${esc(c.job||'-')}</td><td class="num">${r.w?meso(r.w):'-'}</td><td class="num">${r.m?meso(r.m):'-'}</td></tr>`; }).join('')}
    </tbody></table></div></div></div>`;
}
// (주간 기록 탭 · renderHistory 는 2026-10-10 삭제 — S.history 데이터는 '캐릭터 별 기록'·'총 수익' 탭이 계속 사용)
/* 총 수익: 시작 주(S.startWeek)부터 저장된 모든 주간 기록 + 이번 주, 월간 보스는 별도 합계. 기록은 자동 삭제되지 않음 */
function totalData(skipCur){
  const VI=activeIds(); // b82: 보이는 캐릭터만 (zosu-apikey 헬퍼)
  const weeks0=[...S.history.slice().sort((a,b)=>a.week<b.week?-1:1).map(h=>({...activeRecords(h,VI),cur:false})),{...activeRecords(weekSummary(S.period.week),VI),cur:true}];
  const weeks=skipCur?weeks0.filter(w=>!w.cur):weeks0; // b176: skipCur = 끝난 주만 (평균용)
  const months0=[...S.monthHistory.map(m=>({...activeRecords(m,VI),cur:false})),{...activeRecords(monthSummary(S.period.month),VI),cur:true}];
  // b176: skipCur 이면 이번 주에 잡은 월간 보스(검마) 기록도 뺌 (mweeks 없으면 진행 중인 달 = 이번 주로 봄)
  const months=skipCur?months0.map(m=>({...m,perChar:(m.perChar||[]).filter(p=>!(p.mweeks&&p.mweeks.length?p.mweeks.includes(S.period.week):m.cur)),total:undefined})).map(m=>({...m,total:m.perChar.reduce((t,p)=>t+(+p.meso||0),0)})):months0;
  // b110: 아이템 판매값을 판 캐릭터(perChar)·그 기간(주간 기록 = 주간 보스 아이템, 월간 기록 = 검은 마법사 아이템)에 더함 — 저장된 기록은 그대로, 복사본만
  const withSale=h=>{ const pc=(h.perChar||[]).map(p=>{ const isale=revSum(p.revs); return isale?{...p,crys:+p.meso||0,isale,meso:(+p.meso||0)+isale}:p; });
    const isale=pc.reduce((t,p)=>t+(p.isale||0),0); return isale?{...h,perChar:pc,crys:h.total||0,isale,total:(h.total||0)+isale}:h; };
  weeks.forEach((w,i)=>weeks[i]=withSale(w)); months.forEach((m,i)=>months[i]=withSale(m));
  const wTotal=weeks.reduce((s,w)=>s+(w.total||0),0), mTotal=months.reduce((s,m)=>s+(m.total||0),0);
  const chars={}, items={};
  const nameOf=p=>{ const c=p.id&&S.characters.find(x=>x.id===p.id); return c?c.name:p.name; };
  const keyOf=p=>p.id&&S.characters.some(x=>x.id===p.id)?p.id:'n:'+p.name;
  const ring={r4:0,c4:0,gl:0,x:0,un:0}, sales={}; // b62-8: 아이템 판매 수익 {실제 아이템 키: {n, m}}
  const addS=p=>{ for(const r of Object.values(p.revs||{})){ if(!r||!(+r.m>0)) continue; const pp=Math.max(1,+r.p||1), k=String(r.i||'')+'#'+pp; const o=sales[k]||(sales[k]={n:0,m:0,i:String(r.i||''),p:pp}); o.n++; o.m+=+r.m; } }; // b76: 분배 인원별로 따로
  weeks.forEach(w=>(w.perChar||[]).forEach(addS)); months.forEach(m=>(m.perChar||[]).forEach(addS));
  const add=(p,f)=>{ const k=keyOf(p); const o=chars[k]||(chars[k]={id:k,name:nameOf(p),week:0,month:0,items:{},outs:{},weeks:0}); f(o);
    for(const [ik,n] of Object.entries(p.items||{})){ const {it,party,mode}=parseIK(ik); if(!ITEMS[it]) continue; const a=party>1?it+'#'+party+mode:it; o.items[a]=(o.items[a]||0)+(+n);
      const I=items[a]||(items[a]={n:0,by:{},outs:[]}); I.n+=+n; I.by[o.name]=(I.by[o.name]||0)+(+n);
      if(hasOut(it)){ const l=(p.outcomes||{})[ik]||[]; I.outs.push(...l); (o.outs[a]=o.outs[a]||[]).push(...l); if(isRing(it)&&mode!=='l'){ const t=outTally(l,n); for(const q in ring) ring[q]+=t[q]; } } } }; // 블빵패배 상자의 결과는 내 시드링이 아님
  // 보스(난이도)별 아이템: 난이도는 그 주 기록의 보스 태그 '이름(난이도)' → 없으면 현재 캐릭터 설정
  const byBoss={};
  const addB=p=>{ const tags={}; (p.bosses||[]).forEach(t=>{ const m=/^(.+?)\((.+?)\)/.exec(t); if(m) tags[m[1]]=m[2]; });
    const cc=p.id&&S.characters.find(x=>x.id===p.id);
    for(const [ik,n] of Object.entries(p.items||{})){ const {slot,it,mode}=parseIK(ik); const b=findBoss(slot); if(!b||!ITEMS[it]||!(+n>0)) continue; const sf=mode?'@'+mode:''; // 블빵승리/패배는 따로 집계
      const dl=tags[b.name]||(cc&&cc.bosses[slot]?.diff?D[cc.bosses[slot].diff]:'');
      const bk=slot+'|'+dl, o=byBoss[bk]||(byBoss[bk]={slot,dl,items:{},cnt:0,sc:0}); let u=+n; o.cnt+=+n; o.sc+=+n*sc10(it); // b118: 점수(0.1점 단위) // b83: cnt = 드롭 표에 기록한 아이템 수(1개=1회)
      if(isRing(it)){ const ro=o.ro||(o.ro={}), t=ro[it+sf]||(ro[it+sf]={r4:0,c4:0,x:0}); ((p.outcomes||{})[ik]||[]).forEach(q=>{ if(q in t) t[q]++; }); } // b111: 보스 득템왕 반지 상자 결과
      if(isRing(it)) ((p.outcomes||{})[ik]||[]).forEach(q=>{ if(q==='gl') o.items['g_life'+sf]=(o.items['g_life'+sf]||0)+1; });
      if(it==='chaosbox') ((p.outcomes||{})[ik]||[]).forEach(q=>{ if(/^cb:/.test(q)&&ITEMS[q.slice(3)]&&u>0){ o.items[q+sf]=(o.items[q+sf]||0)+1; u--; } });
      if(u>0) o.items[it+sf]=(o.items[it+sf]||0)+u; } };
  weeks.forEach(w=>(w.perChar||[]).forEach(addB)); months.forEach(m=>(m.perChar||[]).forEach(addB));
  weeks.forEach(w=>(w.perChar||[]).forEach(p=>add(p,o=>{o.week+=p.meso||0; if(p.meso) o.weeks++;})));
  months.forEach(m=>(m.perChar||[]).forEach(p=>add(p,o=>{o.month+=p.meso||0;})));
  return {weeks,months,wTotal,mTotal,grand:wTotal+mTotal,ring,byBoss,sales,chars:Object.values(chars).sort((a,b)=>(b.week+b.month)-(a.week+a.month)),items:Object.entries(items).sort((a,b)=>b[1].n-a[1].n)};
}
// 아이템 칩: 'cb:<장신구>' = 칠흑 상자에서 고른 장신구, 'ring:r4|c4' = 시드링 결과
/* b117: 아이콘이 같은 아이템인지 (칠흑 상자 결과 cb:·x:·블빵 @w/@l 은 같은 아이템) */
const icoId = k => lootBase(String(k||'').replace(/^x:/,'')).replace(/^cb:/,'');
const lootSf = k => /@([wl])$/.exec(k)?.[1]||'', lootBase = k => k.replace(/@[wl]$/,'');
const lootName0 = k => /^cb:/.test(k)?ITEMS[k.slice(3)].n : k==='ring:r4'?OUT_NAME.r4 : k==='ring:c4'?OUT_NAME.c4 : ITEMS[k].n;
const lootName = k => /^x:/.test(k)?ITEMS[k.slice(2)].n+' · 꽝':lootName0(lootBase(k));
const lootIco = k => /^x:/.test(k)?itemIcon(k.slice(2)):lootIco0(lootBase(k));
/* b229: 아이템 표시 공통 — 아이콘 + 이름 칸(+ xN). 홍옥 리4/컨4 = 홍옥 상자 아이콘 + 반지 아이콘 + xN (이름은 .vh 로 숨김, 1개여도 x1). 모든 아이템 목록이 이걸 씀 */
const lootLabel = (k,o={}) => `${lootIco(k)}<span class="${o.cls||'ln'}${hnCls(k)}">${o.name!=null?o.name:esc(lootName(k))}${o.extra||''}</span>${o.n!=null&&(o.n>1||o.n1||isHong(k))?`${isHong(k)?'':' '}<b class="${o.xc||'lx'}">${xN(o.n)}</b>`:''}`;
const lootIco0 = k => /^cb:/.test(k)?itemIcon(k.slice(3)) : k==='ring:r4'?miniIcon('ring_restraint') : k==='ring:c4'?miniIcon('ring_continuous') : itemIcon(k);
const lootOrd = k => /^x:/.test(k)?Object.keys(ITEMS).indexOf(k.slice(2))+.5:lootOrd0(lootBase(k))+({w:.001,l:.002}[lootSf(k)]||0);
const lootOrd0 = k => /^cb:/.test(k)?Object.keys(ITEMS).indexOf('chaosbox')+.01*(1+CHAOS_PICK.indexOf(k.slice(3))) : /^ring:/.test(k)?-1+(k==='ring:c4'?.5:0) : Object.keys(ITEMS).indexOf(k);
const modeTag = k => lootSf(k)?` <span class="ptx ptx-${lootSf(k)}">(${MODE_TXT[lootSf(k)]})</span>`:'';
/* b111: 칠흑 상자에서 고른 장신구(cb:*)를 '혼돈의 칠흑 장신구 상자' 하나로 합침 → 마우스를 올리면 말풍선에 장신구별 아이콘·개수 */
function chaosTip(C,un){ const ks=Object.keys(C).filter(k=>C[k]>0).sort((a,b)=>C[b]-C[a]||itemCmp(a,b));
  return `<b class="tth">${esc(ITEMS.chaosbox.n)}</b>${ks.map(k=>`<span class="ttr">${itemIcon(k)}<span>${esc(ITEMS[k].n)}</span> <b>${xN(C[k])}</b></span>`).join('')}${un?`<span class="ttr muted">미기록 ${xN(un)}</span>`:''}${!ks.length&&!un?'<span class="ttr muted">기록 없음</span>':''}`; }
function chaosMerge(m){ const o={}, tips={}, by={};
  for(const [k,n] of Object.entries(m)){ if(!(n>0)) continue; const sf=lootSf(k), b=lootBase(k);
    if(/^cb:/.test(b)||b==='chaosbox'){ const kk='chaosbox'+(sf?'@'+sf:''); o[kk]=(o[kk]||0)+n; const t=by[kk]||(by[kk]={C:{},un:0}); if(b==='chaosbox') t.un+=n; else t.C[b.slice(3)]=(t.C[b.slice(3)]||0)+n; }
    else o[k]=(o[k]||0)+n; }
  for(const kk in by) tips[kk]=chaosTip(by[kk].C,by[kk].un);
  return {m:o,tips}; }
const tipAttr = h => h?` data-tip="${esc(ITEMS.chaosbox.n)}" data-tiphtml="${esc(h)}"`:'';
/* b111: 보스 강함 순서 (강한 것 먼저): 그란디스(유피테르→세렌), 찬란한 흉성(노말) 바로 아래 스우(익스트림), 검은 마법사, 아케인리버(듄켈→루시드), 그 밖 보스는 맨 뒤(강한 것 먼저) */
const STR_ORD=['jupiter','bellona','baldrix','limbo','star','kaling','adversary','kalos','seren','blackmage','dunkel','jinhilla','dusk','will','lucid'];
function bossStr(slot,d){ const id=typeof slot==='object'?slot?.id:slot; d=DK[d]||d;
  if(id==='lotus'&&d==='extreme') return STR_ORD.indexOf('star')*10+5;
  let i=STR_ORD.indexOf(id); if(i<0){ const j=BOSSES.findIndex(b=>b.id===id); i=j<0?9999:STR_ORD.length+(BOSSES.length-j); }
  return i*10+diffRank(d); }
const lootChips = (m,top,tips) => `<span class="loots">${Object.keys(m).filter(k=>m[k]>0).sort((a,b)=>itemCmp(a,b)).map(k=>`<span class="loot${lootSf(k)?' md-'+lootSf(k):''}"${tipAttr(tips&&tips[k])}>${/^cb:/.test(k)?miniIcon('chaosbox')+' - ':''}${lootLabel(k,{cls:'ln'+(top&&itemCol(k)?' spk '+itemCol(k):''),extra:lootSf(k)?` <span class="ptx ptx-${lootSf(k)}">(${MODE_TXT[lootSf(k)]})</span>`:'',n:m[k],n1:1})}</span>`).join('')}</span>`;
// 시드링 기댓값: 상자 종류별 (획득 상자 수 × 상자 1개의 리4/컨4 확률) 합. 확률 = BOX_INFO (넥슨 공식 확률 공개, 툴팁과 같은 값)
function ringExp(T){ const e={r4:0,c4:0,gl:0}; T.items.forEach(([a,I])=>{ const {it}=parseIK(a); const p=ring4(it); if(p){ e.r4+=I.n*p.r4/100; e.c4+=I.n*p.c4/100; e.gl+=I.n*p.gl/100; } }); return e; }
const fmtExp=v=>(Math.round(v*100)/100).toFixed(2);
const ringExpHtml=T=>{ const e=ringExp(T); return `<span class="ringexp">기댓값 리4 ${fmtExp(e.r4)}개 · 컨4 ${fmtExp(e.c4)}개 · 연마석 ${fmtExp(e.gl)}개</span>`; };
/* b83: 보스 득템왕 — 보스(난이도)별 득템 횟수 순위. 1~3위 보스 이름 색: 아케인리버 이전 = 흰색, 아케인리버 = 연두(검은 마법사 = 검정+밝은 테두리),
 * 세르니움·아르크스·오디움·도원경 = 하늘→파랑, 아르테리아 이후 = 분홍→핫핑크 (반짝임은 다른 순위 표와 같은 .spk) */
const BOSS_REGION={lucid:'arc',will:'arc',dusk:'arc',jinhilla:'arc',dunkel:'arc',blackmage:'bm',seren:'gr1',kalos:'gr1',adversary:'gr1',kaling:'gr1',star:'gr2',limbo:'gr2',baldrix:'gr2',bellona:'gr2',jupiter:'gr2'};

/* b111: 똥캐 TOP5 → b212: TOP3 (1~3위만) — 득템 횟수(득템왕과 같은 셈법) 적은 순. 메달 색 없음, 1위 = 왕관 대신 똥, 5명 모두 초상화 위 똥 + 글자 주변 파리 */
function poopHtml(T){
  const ord=orderedChars().map(c=>c.id), oi=o=>{ const i=ord.indexOf(o.id); return i<0?1e6:i; };
  const rows=T.chars.map(o=>{ const m=noBust(lootOf(o.items,o.outs,md=>md!=='l')); return {...o,ln:Object.values(m).reduce((x,y)=>x+y,0)}; })
    .sort((a,b)=>a.ln-b.ln||oi(a)-oi(b)||a.name.localeCompare(b.name)).slice(0,3);
  const FLY=(n,st='')=>`<svg class="fly f${n}"${st} viewBox="0 0 12 10" width="7" height="6" aria-hidden="true"><ellipse cx="3.6" cy="3" rx="3" ry="2" fill="rgba(200,225,255,.75)"/><ellipse cx="8.4" cy="3" rx="3" ry="2" fill="rgba(200,225,255,.75)"/><ellipse cx="6" cy="6" rx="2.2" ry="3" fill="#222"/><circle cx="6" cy="3.4" r="1.4" fill="#111"/></svg>`; /* b115: 날파리 = 초상화 주변, 작게, 4마리, 빠르게 */
  const av=o=>{ const c=S.characters.find(x=>x.id===o.id); return `<span class="poopav flies">${c?avatar(c,'rkav'):''}<span class="poop" aria-hidden="true">💩</span>${[1,2,3,4].map(n=>{ let h=0; for(const ch of o.id+n) h=(h*131+ch.charCodeAt(0))>>>0; const r=x=>((h=(h*1103515245+12345)>>>0)%1000)/1000*x; return FLY(n,` style="animation-duration:${(0.8+r(1)).toFixed(2)}s;animation-delay:-${r(2).toFixed(2)}s"`); }).join('')}</span>`; };
  const c1=rows[0]&&S.characters.find(x=>x.id===rows[0].id);
  return `<div class="card kingcard" id="poopKing"><h2><span class="poopav ph">${c1?avatar(c1,'hking'):''}<span class="poop" aria-hidden="true">💩</span></span> 똥캐 TOP3</h2><div style="overflow-x:auto"><table class="ranktbl pooptbl"><thead><tr><th>순위</th><th>캐릭터</th><th class="num">득템 횟수</th></tr></thead><tbody>
    ${rows.map((o,i)=>`<tr class="pk${i+1}"><td><span class="rkno">${i===0?'<span class="crown" aria-hidden="true">💩</span>':''}<span class="rkn">${i+1}</span></span></td><td><span class="rkname">${av(o)}<span class="rknm"><b>${esc(o.name)}</b></span></span></td><td class="num"><b>${o.ln}회</b></td></tr>`).join('')||'<tr><td colspan="3" class="muted">기록 없음</td></tr>'}
    </tbody></table></div></div>`;
}
function bossLootKingHtml(T){
  const rows=Object.values(T.byBoss||{}).filter(o=>o.cnt>0).map(o=>({...o,b:findBoss(o.slot),d:DK[o.dl]})).filter(o=>o.b).sort((a,b)=>b.sc-a.sc||b.cnt-a.cnt||BOSSES.indexOf(b.b)-BOSSES.indexOf(a.b)||diffRank(a.dl)-diffRank(b.dl));
  const sl=rankSlice('bloot',rows);
  const nm=o=>`<span class="bdn">${esc(o.b.name)}</span>${o.d?` <span class="dlv dlv-${DIFF_CLS[o.d]||''}">(${D[o.d]||o.dl})</span>`:o.dl?` <span class="muted">(${esc(o.dl)})</span>`:''}`;
  const chips=(m0,ro)=>{ const {m,tips}=chaosMerge(m0); return `<span class="blkchips">${Object.keys(m).filter(k=>m[k]>0).sort(itemCmp).map(k=>{ const t=ro&&isRing(lootBase(k))&&ro[k];
    return `<span class="blkchip"${tips[k]?tipAttr(tips[k]):` title="${esc(lootName(k)+(t?` ${m[k]}개 - 리4 ${t.r4}개 - 컨4 ${t.c4}개 - 꽝 ${t.x}개`:''))}"`}>${t?`${lootIco(k)}${modeTag(k)} <b class="lx">${m[k]}개</b><span class="blro"> - 리4 ${t.r4}개 - 컨4 ${t.c4}개 - 꽝 ${t.x}개</span>`:lootLabel(k,{extra:modeTag(k),n:m[k]})}</span>`; }).join('')}</span>`; };
  return `<div class="card kingcard" id="bossLootKing"><h2>${rows[0]?`<span class="hbi">${bossIcon(rows[0].b)}</span>`:miniIcon('bliss')} 보스 득템왕</h2>${SC_SUB}<div class="blkwrap"><table class="ranktbl blktbl"><thead><tr><th>순위</th><th>보스</th><th class="scth">점수</th><th>득템 목록</th></tr></thead><tbody>
    ${sl.map(([o,r])=>{ const m=medal(r), rg=m?(BOSS_REGION[o.b.id]?'rg-'+BOSS_REGION[o.b.id]:'rg-old'):''; return `<tr class="rk${r}${m?' md-'+m:''}"><td>${rankNo(r)}</td><td class="blkb"><span class="rkname ${m?'md-'+m:''}">${m?`<span class="rkico">${bossPic(o.b,o.d)}</span>`:''}<span class="${m?'spk ':''}${rg}">${nm(o)}</span></span></td><td class="sctd"><b class="${scCls(r)}">${fmtSc(o.sc)}</b></td><td class="blkl">${chips(o.items,o.ro)}</td></tr>`; }).join('')||'<tr><td colspan="4" class="muted">기록 없음</td></tr>'}${rankPad(sl.length,rows.length,4)}
    </tbody></table></div>${rankPager('bloot',rows.length)}</div>`;
}
function bossLootHtml(T){
  const bi=s=>{ const i=BOSSES.findIndex(b=>b.id===s); return i<0?999:i; };
  const rows=Object.values(T.byBoss||{}).filter(o=>Object.values(o.items).some(n=>n>0)).sort((a,b)=>bossStr(a.slot,a.dl)-bossStr(b.slot,b.dl)||bi(a.slot)-bi(b.slot)); // b111: 강한 보스 먼저
  return `<div class="card bossloot"><h2><span class="hbi">${bossIcon(findBoss('zakum'))}</span> 보스 별 누적 획득 아이템</h2>${rows.length?rows.map(o=>{ const b=findBoss(o.slot);
    return `<div class="blrow"><span class="blb"><span class="hbi">${bossPic(b,DK[o.dl]||o.dl)}</span><b>${esc(b.name)}</b>${o.dl?` ${DK[o.dl]?dlvHtml(DK[o.dl]):`<span class="muted">${esc(o.dl)}</span>`}`:''}</span>${lootChips(o.items)}</div>`; }).join(''):'<p class="muted">아직 저장된 드랍 기록이 없습니다.</p>'}</div>`;
}
// 총 아이템 획득량: 반지 상자는 상자 자체 + 기록된 결과(리4·컨4)를 시드링 아이템으로 따로 (꽝은 아이템이 아님), 칠흑 상자는 고른 장신구로
function itemTotalsHtml(T){
  const m={};
  for(const o of Object.values(T.byBoss||{})) for(const [k,n] of Object.entries(o.items)){ const kk=/^cb:/.test(k)?k.slice(3):k; /* '@w'/'@l' 접미사는 유지 → 블빵승리/패배 따로 */ m[kk]=(m[kk]||0)+n; }
  m['ring:r4']=T.ring.r4||0; m['ring:c4']=T.ring.c4||0; // b120: 위 요약 줄 없이 리4·컨4도 다른 아이템처럼 xN (아이템 순서 그대로)
  /* b122: 블빵승리(@w)는 같은 아이템과 합침, 블빵패배(@l)는 따로 맨 뒤에 모아서 */
  const W={}, Lz={}; for(const [k,n] of Object.entries(m)){ if(!(n>0)) continue; if(/@l$/.test(k)) Lz[k]=n; else { const b=k.replace(/@w$/,''); W[b]=(W[b]||0)+n; } }
  return `<div class="card itemtot"><h2>${miniIcon('bliss')} 총 아이템 획득량</h2>${Object.keys(W).length||Object.keys(Lz).length?lootChips(W)+(Object.keys(Lz).length?lootChips(Lz):''):'<p class="muted">아직 저장된 아이템이 없습니다.</p>'}</div>`;
}
// b53: 주별 누적 결정석 메소 = 라인 차트 (주마다 점, 누적 합계 선 + 아래 은은한 면)
/* b58: 월간 보스 결정석 수익은 '잡은 주'(mweeks, c.monthly[slot] 의 주 key)의 수익에 포함. 그 주가 목록에 없거나(예전 기록 — mweeks 없음) 알 수 없으면 같은 달(YYYY-MM)로 시작하는 마지막 주로 근사 */
function monthlyByWeek(T){
  const M={}, keys=T.weeks.map(w=>w.week);
  T.months.forEach(m=>(m.perChar||[]).forEach(p=>(p.bosses||[]).forEach((t,i)=>{
    const mt=/^(.+?)\((.+?)\)(?:\/(\d+)인)?/.exec(t), b=mt&&BOSSES.find(x=>x.name===mt[1]), d=mt&&DK[mt[2]];
    const v=p.bvals&&p.bvals[i]!=null?+p.bvals[i]:(b&&d?Math.floor(price(b,d)/Math.max(1,+mt[3]||1)):0); if(!(v>0)) return;
    let wk=p.mweeks&&p.mweeks[i]; if(!keys.includes(wk)){ const c=keys.filter(k=>String(k).startsWith(m.month)); wk=c.length?c[c.length-1]:''; }
    if(!wk) return; const o=M[wk]||(M[wk]={n:0,meso:0,cry:0,sale:0}); o.n++; o.meso+=v; o.cry+=v; })));
  // b110: 검은 마법사 아이템 판매값 → 그 보스를 잡은 주 (못 찾으면 같은 달 마지막 주)
  T.months.forEach(m=>(m.perChar||[]).forEach(p=>{ for(const [k,r] of Object.entries(p.revs||{})){ if(!r||!(+r.m>0)) continue; const b=findBoss(parseIK(k).slot);
    const i=b?(p.bosses||[]).findIndex(t=>t.startsWith(b.name+'(')):-1; let wk=i>=0&&p.mweeks?p.mweeks[i]:'';
    if(!keys.includes(wk)){ const c=keys.filter(x=>String(x).startsWith(m.month)); wk=c.length?c[c.length-1]:''; } if(!wk) continue;
    const o=M[wk]||(M[wk]={n:0,meso:0,cry:0,sale:0}); o.meso+=+r.m; o.sale+=+r.m; } }));
  return M; }
function thisWeekChart(T){ // b135: 주간 메소 그래프 = 이번 주만, 목 0시(KST) 0 → 날짜별 누적. 시간 기록(c.wat, b135 부터)이 없는 처치·판매는 목요일에 합산
  const ws=weekStartMs(), dayOf=t=>t&&t>=ws?Math.min(6,Math.floor((t-ws)/864e5)):0, today=dayOf(Date.now());
  const z=()=>[0,0,0,0,0,0,0], B=z(), Cr=z(), Sa=z(), Mn=z(), Mm=z(); let known=0; // zosu-apikey: activeChars()
  const dd=ds=>ds?dayOf(Date.parse(ds+'T12:00:00+09:00')):0;
  for(const c of activeChars()){ const r=charRevenue(c), at=c.wat||{};
    r.wlist.filter(x=>x.counted).forEach(x=>{ const i=dayOf(at[x.slot]); Cr[i]+=x.value; known+=x.value; });
    r.mlist.filter(x=>x.counted&&c.monthly[x.slot]===S.period.week).forEach(x=>{ const i=dd((c.mdate||{})[x.slot]); Cr[i]+=x.value; Mn[i]++; Mm[i]+=x.value; known+=x.value; });
    for(const [k,v] of Object.entries(c.drev||{})){ if(!v||!(+v.m>0)) continue; const i=dayOf(at[parseIK(k).slot]); Sa[i]+=+v.m; known+=+v.m; } }
  const cur=T.weeks.find(w=>w.cur)||{}, MW=monthlyByWeek(T)[cur.week]||{}, all=(cur.total||0)+(MW.meso||0); if(all>known) Sa[0]+=all-known;
  for(let i=0;i<7;i++) B[i]=Cr[i]+Sa[i];
  const DN=['목','금','토','일','월','화','수'], W=640, Hh=220, pl=60, pr=14, pt=24, pb=30, bw=(W-pl-pr)/7;
  let s=0; const cums=B.map(v=>s+=v).slice(0,today+1), cmax=Math.max(1,s);
  const X=i=>pl+i*bw+bw/2, Y=v=>Hh-pb-(Hh-pb-pt)*v/cmax;
  const grid=[0,.5,1].map(f=>`<line x1="${pl}" x2="${W-pr}" y1="${Y(cmax*f).toFixed(1)}" y2="${Y(cmax*f).toFixed(1)}" stroke="currentColor" opacity="${f?'.08':'.18'}"/>${segLab(f?fmtEok(cmax*f):'0',pl-6,(Y(cmax*f)+3.5).toFixed(1),'end','cax',9)}`).join('');
  const pts=[`${pl},${Y(0)}`,...cums.map((v,i)=>`${X(i).toFixed(1)},${Y(v).toFixed(1)}`)].join(' ');
  const d0=Date.parse(cur.week+'T00:00:00+09:00')||ws, md=i=>{ const d=new Date(d0+i*864e5+KST_MS); return `${d.getUTCMonth()+1}/${d.getUTCDate()}`; };
  const xl=DN.map((n,i)=>`<text x="${X(i).toFixed(1)}" y="${Hh-pb+16}" text-anchor="middle"${i===today?' font-weight="700"':''}>${n} ${md(i)}</text>`).join('');
  const dots=cums.map((v,i)=>`<g class="lpt" data-tip="${esc(`${md(i)} (${DN[i]})${i===today?' 오늘':''}\n이날 ${meso(B[i])}${Mn[i]?`\n  └ 월간 보스 ${Mn[i]}개 ${meso(Mm[i])} 포함`:''}\n결정석 : ${meso(Cr[i])}\n아이템 판매 : ${meso(Sa[i])}\n이번 주 누적 ${meso(v)}`)}"><rect x="${(X(i)-bw/2).toFixed(1)}" y="${pt-10}" width="${bw.toFixed(1)}" height="${Hh-pb-pt+10}" fill="transparent"/><circle data-tipanchor="1" cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="${i===today?4.5:3.2}" fill="#2f7fd8"/></g>`).join('');
  return `<div class="muted" style="font-size:.75rem;margin:-4px 0 4px">이번 주만 · 목요일 0시(KST)에 0부터</div><div class="chart linechart" id="weekLine" data-total="${s}"><svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="이번 주 메소 그래프">${grid}
    <polyline fill="none" stroke="#2f7fd8" stroke-width="2.5" stroke-linejoin="round" points="${pts}"/>${dots}${xl}
    <text x="${W-pr}" y="14" text-anchor="end" fill="#2f7fd8" font-size="11">이번 주 ${meso(s)}</text></svg></div>`;
}
function wkPageRender(){ const old=document.querySelector('.chart.lux.wk'); if(!old||!wkLast) return; const t=document.createElement('div'); t.innerHTML=cumLineChart(wkLast.rows0,wkLast.T,wkLast.o); const nw=t.firstElementChild; nw.classList.add('inview'); old.replaceWith(nw); if(typeof tsvAnim==='function') tsvAnim(nw); }
document.addEventListener('click',e=>{ const b=e.target.closest?.('[data-wkpg]'); if(!b||b.disabled) return; WK_PAGE=Math.max(0,WK_PAGE+(+b.dataset.wkpg||0)); tipHide(); wkPageRender(); });
/* b211: 주간 메소(perWeek) = 5주씩 페이지 (기본 = 가장 최근 5주). WK_PAGE = 최근부터 몇 번째 페이지(0 = 최신) */
const WK_PER=5; let WK_PAGE=0, wkLast=null;
function cumLineChart(rows0,T,o={}){ // b136: o.perWeek = 점 높이가 그 주 메소(1주차, 2주차 …), 누적 아님
  if(o.perWeek) wkLast={rows0,T,o};
  const MW=T?monthlyByWeek(T):{}; const rowsA=rows0.map((r,wi)=>{ const m=MW[r.week]||{}; return {...r,mm:m.meso||0,mn:m.n||0,wcry:(r.crys??r.total??0),bm:m.cry||0,cry:(r.crys??r.total??0)+(m.cry||0),sale:(r.isale||0)+(m.sale||0),total:(r.total||0)+(m.meso||0),wi}; });
  const nA=rowsA.length, P=o.perWeek?Math.max(1,Math.ceil(nA/WK_PER)):1, pg=o.perWeek?Math.min(Math.max(0,WK_PAGE),P-1):0;
  const rows=o.perWeek&&nA>WK_PER?rowsA.slice(Math.max(0,nA-WK_PER*(pg+1)),nA-WK_PER*pg):rowsA, allSum=rowsA.reduce((t,r)=>t+r.total,0);
  // b138: 고급 다크 스타일 — 오렌지→골드 그라데이션 선 + 은은한 글로우, 오렌지 영역 그라데이션, 점선 격자, 값 라벨(외곽선), 그려지는 애니메이션
  const n=rows.length, pl=60, pr=18, pt=48, pb=40, Hh=260, bw=o.perWeek&&nA>WK_PER?(640-pl-pr)/WK_PER:Math.max(34,(640-pl-pr)/Math.max(1,n)), W=Math.max(640,pl+pr+n*bw);
  let cum=0; const acc=rows.map(r=>cum+=r.total), cums=o.perWeek?rows.map(r=>r.total):acc; const cmax=Math.max(1,...cums)*1.08;
  const X=i=>pl+i*bw+bw/2, Y=v=>Hh-pb-(Hh-pb-pt)*v/cmax, step=Math.max(1,Math.ceil(n/(W/60)));
  const pts=cums.map((v,i)=>`${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(' '), u=++chartUid;
  const top=Math.max(1,...cums), grid=`<line class="cyax" x1="${pl}" x2="${pl}" y1="${pt-6}" y2="${Hh-pb}" stroke="url(#lcv${u})"/>`+cums.map((v,i)=>`<line class="ctick" x1="${X(i).toFixed(1)}" x2="${X(i).toFixed(1)}" y1="${Hh-pb}" y2="${Hh-pb+5}"/>`).join('')+[0,.25,.5,.75,1].map(f=>`<line class="cg${f?'':' cg0'}" x1="${pl}" x2="${W-pr}" y1="${Y(top*f).toFixed(1)}" y2="${Y(top*f).toFixed(1)}" stroke="url(#${f?'lcgr':'lcb'}${u})"/><line class="cytk" x1="${pl-4}" x2="${pl}" y1="${Y(top*f).toFixed(1)}" y2="${Y(top*f).toFixed(1)}"/>${segLab(f?fmtEok(top*f):'0',pl-8,(Y(top*f)+3.5).toFixed(1),'end','cax',9)}`).join('');
  const xl=rows.map((r,i)=>i%step===0||r.cur?`<text class="cxl${r.cur?' cur':''}" x="${X(i).toFixed(1)}" y="${Hh-pb+18}" text-anchor="middle">${o.perWeek?`${r.wi+1}주차`:fmtWeek(r.week).split(' ~')[0]}</text>`:'').join('')+(rows[n-1]&&rows[n-1].cur?`<text class="cxl cur sub" x="${X(n-1).toFixed(1)}" y="${Hh-pb+32}" text-anchor="middle">이번 주</text>`:'');
  const tipOf=(r,v)=>o.perWeek?`${r.wi+1}주차 총 수익 : ${meso(r.total)}\n주간 결정석 : ${meso(r.wcry)}\n검마 결정석 : ${meso(r.bm)}\n아이템 판매 : ${meso(r.sale)}`:`${fmtWeek(r.week)}${r.cur?' (이번 주)':''}\n주간 수익 ${meso(r.total)}`+(r.mn?`\n  └ 월간 보스 ${r.mn}개 ${meso(r.mm)} 포함`:'')+`\n결정석 : ${meso(r.cry)}\n아이템 판매 : ${meso(r.sale)}`+`\n누적 ${meso(o.perWeek?acc[rows.indexOf(r)]:v)}`;
  /* b186: 주간 메소(perWeek) = 주마다 막대 4개 (총 수익 · 주간 결정석 · 검마 · 아이템 판매), 점·선은 총 수익 */
  const WB_LB=['이번주 총 수익','주간 결정석','검마 수익','아이템 판매수익'];
  const bwid=Math.max(4,Math.min(9,bw*.17)), wbars=(r,i)=>[r.total,r.wcry,r.bm,r.sale].map((val,k)=>`<rect class="cbar wb wb${k}" pathLength="1" data-tip="${esc(`${fmtWeek(r.week)}${r.cur?' (이번 주)':''}\n${WB_LB[k]} ${meso(val)}`)}" x="${(X(i)+(k-2)*bwid*1.15+bwid*.075).toFixed(1)}" y="${Y(val).toFixed(1)}" width="${bwid.toFixed(1)}" height="${Math.max(0,Hh-pb-Y(val)).toFixed(1)}" rx="2"/>`).join('');
  const best=cums.indexOf(top);
  const dots=cums.map((v,i)=>`<g class="lpt${rows[i].cur?' cur':''}${i===best&&n>1?' best':''}" ${o.perWeek?'':`data-tip="${esc(tipOf(rows[i],v))}"`} style="--d:${(.15+i*.06).toFixed(2)}s">${o.perWeek?(()=>{ /* b212: 점 범위 = 그 주 칸 전체(양옆 3 띄움 → 옆 주와 안 겹침) · 그래프 맨 위(pt-10)부터 0선까지. 막대가 위라서 막대 말풍선 우선 */ const w=(bw-6)*0.7, x1=X(i)-w/2, y1=pt-10 /* b213: 좌우 = b212 칸의 70%, 점 가운데 */, h=Hh-pb-y1; return `<rect class="whit" data-tip="${esc(tipOf(rows[i],v))}" fill="transparent" x="${x1.toFixed(1)}" y="${y1}" width="${w.toFixed(1)}" height="${h}"/>`; })():''}${o.perWeek?'':`<rect x="${(X(i)-bw/2).toFixed(1)}" y="${pt-10}" width="${bw.toFixed(1)}" height="${Hh-pb-pt+10}" fill="transparent"/>`}${o.perWeek?wbars(rows[i],i):`<rect class="cbar" x="${(X(i)-Math.min(16,bw*.2)).toFixed(1)}" y="${Y(v).toFixed(1)}" width="${(Math.min(32,bw*.4)).toFixed(1)}" height="${Math.max(0,Hh-pb-Y(v)).toFixed(1)}" rx="5" fill="url(#lcbar${u})"/>`}<circle data-tipanchor="1" ${o.perWeek?`class="wdot" data-tip="${esc(tipOf(rows[i],v))}"`:''} cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="${rows[i].cur?5:4}"/></g>${n<=16&&v?`<g class="cval cvd${i===best&&n>1?' best':''}" pointer-events="none" style="--d:${(.3+i*.06).toFixed(2)}s"><title>${fmtEok(v)}</title>${tirSvg(fmtEok(v),X(i),Y(v)-13,13)}</g>`:''}`).join('');
  return `<div class="chart scrollx linechart lux${o.perWeek?' wk':''}"><div class="ctot"><span>${o.perWeek?'총 누적':'누적'}</span><b>${meso(o.perWeek?allSum:Math.max(...cums,0))}</b></div>${o.perWeek&&P>1?`<div class="wkpg" role="group" aria-label="주간 메소 페이지"><button type="button" class="wkpb" data-wkpg="1"${pg>=P-1?' disabled':''} aria-label="이전 5주">◀ 이전</button><span class="wkpn">${P-pg} / ${P}</span><button type="button" class="wkpb" data-wkpg="-1"${pg<=0?' disabled':''} aria-label="다음 5주">다음 ▶</button></div>`:''}${o.perWeek?`<div class="wlegend"><span><i class="wb0"></i>이번주 총 수익</span><span><i class="wb1"></i>주간 결정석</span><span><i class="wb2"></i>검마</span><span><i class="wb3"></i>아이템 판매</span></div>`:''}<svg viewBox="0 0 ${W} ${Hh}" ${W>640?`style="width:${W}px;max-width:none"`:''} role="img" aria-label="주간 메소 그래프">
      <defs><linearGradient id="lcg${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff9a3c" stop-opacity=".38"/><stop offset=".55" stop-color="#ff9a3c" stop-opacity=".1"/><stop offset="1" stop-color="#ff9a3c" stop-opacity="0"/></linearGradient>
      <linearGradient id="lcs${u}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff8a3d"/><stop offset=".6" stop-color="#ffb347"/><stop offset="1" stop-color="#ffd978"/></linearGradient>
      <linearGradient id="lcgr${u}" gradientUnits="userSpaceOnUse" x1="${pl}" y1="0" x2="${W-pr}" y2="0"><stop offset="0" stop-color="#ffcf7a" stop-opacity=".28"/><stop offset=".5" stop-color="#ffb347" stop-opacity=".14"/><stop offset="1" stop-color="#ffcf7a" stop-opacity=".03"/></linearGradient>
      <linearGradient id="lcb${u}" gradientUnits="userSpaceOnUse" x1="${pl}" y1="0" x2="${W-pr}" y2="0"><stop offset="0" stop-color="#ffd978"/><stop offset=".55" stop-color="#ff9a3c"/><stop offset="1" stop-color="#ffd978" stop-opacity=".25"/></linearGradient>
      <linearGradient id="lcv${u}" gradientUnits="userSpaceOnUse" x1="0" y1="${pt-6}" x2="0" y2="${Hh-pb}"><stop offset="0" stop-color="#ffd978" stop-opacity="0"/><stop offset="1" stop-color="#ffd978" stop-opacity=".55"/></linearGradient>
      <linearGradient id="lcbar${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd978" stop-opacity=".55"/><stop offset=".35" stop-color="#ff9a3c" stop-opacity=".28"/><stop offset="1" stop-color="#ff8a3d" stop-opacity=".04"/></linearGradient>
      <filter id="lcf${u}" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      ${grid}${o.perWeek?'':`<polygon class="carea" fill="url(#lcg${u})" points="${X(0).toFixed(1)},${Y(0)} ${pts} ${X(n-1).toFixed(1)},${Y(0)}"/>`}
      <polyline class="cline" pathLength="1" fill="none" stroke="url(#lcs${u})" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" filter="url(#lcf${u})" points="${pts}"/>${dots}${xl}</svg></div>`;
}
function weekChart(rows, opts={}){
  // rows: [{week,total,cur}] — 막대(주간 수익) + 선택적으로 누적선
  const n=rows.length, bw=Math.max(opts.minBar||18,(640-16)/Math.max(1,n)), pl=8, W=Math.max(640,pl*2+n*bw), Hh=240, pb=36, pt=24;
  const max=Math.max(1,...rows.map(r=>r.total));
  let cum=0; const cums=rows.map(r=>cum+=r.total); const cmax=Math.max(1,cum);
  const step=Math.max(1,Math.ceil(n/(W/56)));
  const bars=rows.map((r,i)=>{const h=(Hh-pb-pt)*r.total/max;const x=pl+i*bw+bw*.15,w=bw*.7,y=Hh-pb-h;
    return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${Math.max(h,1).toFixed(1)}" rx="4" fill="${r.cur?'url(#gc)':'url(#g)'}"><title>${fmtWeek(r.week)}: ${meso(r.total)}${opts.cum?` (누적 ${meso(cums[i])})`:''}</title></rect>
    ${!opts.cum||n<=16?`<text x="${(x+w/2).toFixed(1)}" y="${(y-6).toFixed(1)}" text-anchor="middle" class="lbl" font-size="10">${r.total?meso(r.total).replace(/ .*/,''):''}</text>`:''}
    ${i%step===0||r.cur?`<text x="${(x+w/2).toFixed(1)}" y="${Hh-pb+16}" text-anchor="middle">${fmtWeek(r.week).split(' ~')[0]}</text>`:''}
    ${r.cur?`<text x="${(x+w/2).toFixed(1)}" y="${Hh-pb+30}" text-anchor="middle">이번 주</text>`:''}`;}).join('');
  const line=opts.cum?`<polyline fill="none" stroke="#2f7fd8" stroke-width="2.5" points="${cums.map((v,i)=>`${(pl+i*bw+bw/2).toFixed(1)},${(Hh-pb-(Hh-pb-pt)*v/cmax).toFixed(1)}`).join(' ')}"/>
    ${cums.map((v,i)=>`<circle cx="${(pl+i*bw+bw/2).toFixed(1)}" cy="${(Hh-pb-(Hh-pb-pt)*v/cmax).toFixed(1)}" r="3" fill="#2f7fd8"><title>누적 ${meso(v)}</title></circle>`).join('')}
    <text x="${W-6}" y="14" text-anchor="end" fill="#2f7fd8" font-size="11">누적 ${meso(cmax)}</text>`:'';
  return `<div class="chart scrollx"><svg viewBox="0 0 ${W} ${Hh}" ${W>640?`style="width:${W}px;max-width:none"`:''} role="img" aria-label="주간 수익 그래프">
      <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffb066"/><stop offset="1" stop-color="#f28c28"/></linearGradient>
      <linearGradient id="gc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd2a6"/><stop offset="1" stop-color="#f6b37a"/></linearGradient></defs>
      <line x1="0" x2="${W}" y1="${Hh-pb}" y2="${Hh-pb}" stroke="currentColor" opacity=".15"/>${bars}${line}</svg></div>`;
}
const perCharItems = list => (list||[]).filter(p=>itemSum(p.items)).map(p=>`<div class="hitems"><b>${esc(p.name)}</b> ${itemsInline(p.items,{outs:p.outcomes,byBoss:true,diffOf:tagDiff(p,S.characters.find(x=>x.id===p.id))})}</div>`).join('');
/* ---------- 메소왕 / 득템왕 / 블빵 (수익 분석) ---------- */
let rankPage={meso:1,loot:1,bloot:1}; const RANK_PER=10;
const medal = r => r===1?'gold':r===2?'silver':r===3?'bronze':'';
const crown = '<span class="crown" aria-hidden="true">👑</span>';
function rankName(o,r,extra,xc){ const c=S.characters.find(x=>x.id===o.id); const m=medal(r);
  return `<span class="rkname ${m?'md-'+m:''}">${m&&c?avatar(c,'rkav'):''}${r===1?crown:''}<span class="rknm"><b class="${m?'spk':''}">${esc(o.name)}</b>${extra?`<b class="rkcnt${xc?' '+xc:''}">${extra}</b>`:''}</span></span>`; }
const rankNo = r => `<span class="rkno ${medal(r)?'md-'+medal(r):''}">${r===1?crown:''}<span class="rkn">${r}</span></span>`;
function rankPager(kind,n){ const pages=Math.ceil(n/RANK_PER); if(pages<=1) return ''; const cur=Math.min(rankPage[kind],pages);
  return `<div class="cpager rkpager">${Array.from({length:pages},(_,i)=>`<button type="button" class="cpg${i+1===cur?' on':''}" data-rkpage="${kind}|${i+1}"${i+1===cur?' aria-current="page"':''}>${i+1}</button>`).join('')}</div>`; }
const rankPad = (n,total,cols) => total>RANK_PER&&n<RANK_PER ? Array.from({length:RANK_PER-n},()=>`<tr class="rkpad" aria-hidden="true">${'<td>&nbsp;</td>'.repeat(cols)}</tr>`).join('') : '';
const rankSlice = (kind,rows) => { const pages=Math.max(1,Math.ceil(rows.length/RANK_PER)); rankPage[kind]=Math.min(Math.max(1,rankPage[kind]),pages); const st=(rankPage[kind]-1)*RANK_PER; return rows.slice(st,st+RANK_PER).map((o,i)=>[o,st+i+1]); };
/* 기록 → 아이템 칩 키: 반지 상자는 결과(리4·컨4·생명의 연마석), 꽝 상자는 '꽝'(득템에서 제외), 칠흑은 고른 장신구, 결과 미기록 상자는 상자 그대로 */
function lootOf(items,outs,want){ const m={};
  for(const [a,n0] of Object.entries(items||{})){ const {it,mode}=parseIK(a); if(!ITEMS[it]||!want(mode)) continue; let n=+n0||0; const l=[...((outs||{})[a]||[])];
    if(isRing(it)){ for(const o of l.slice(0,n)){ const k=o==='r4'?'ring:r4':o==='c4'?'ring:c4':o==='gl'?'g_life':o==='x'?'x:'+it:''; if(k){ m[k]=(m[k]||0)+1; n--; } } }
    else if(it==='chaosbox'){ for(const o of l.slice(0,n)) if(/^cb:/.test(o)&&ITEMS[o.slice(3)]){ m[o]=(m[o]||0)+1; n--; } }
    if(n>0) m[it]=(m[it]||0)+n; }
  return m; }
/* b118: 득템 점수 (0.1점 단위 정수로 셈 → 소수 오차 없음): 흑옥 상자 0.1 · 백옥 0.2 · 생명 0.4 · 그 밖 아이템 1 (반지 상자는 결과와 상관없이 상자 종류로, 꽝은 0) */
const SC10={r_black:1,r_white:2,r_life:4}, sc10 = it => SC10[it]||10;
function lootSc10(items,outs,want){ let t=0;
  for(const [a,n0] of Object.entries(items||{})){ const {it,mode}=parseIK(a); if(!ITEMS[it]||!want(mode)) continue; let n=+n0||0;
    if(isRing(it)) n-=((outs||{})[a]||[]).slice(0,n).filter(o=>o==='x').length; t+=Math.max(0,n)*sc10(it); }
  return t; }
/* b120: 득템왕 누적 획득 아이템 = 반지 상자(녹옥·홍옥 포함, 꽝 상자도) 그대로 + 상자에서 나온 리4·컨4·생명의 연마석. 점수 = 상자 무게(흑옥 0.1·백옥 0.2·생명 0.4, 녹옥·홍옥 1) + 나온 아이템 1 */
function kingLoot(items,outs,want){ const m=noBust(lootOf(items,outs,want));
  const box={}; for(const [a,n0] of Object.entries(items||{})){ const {it,mode}=parseIK(a); if(ITEMS[it]&&want(mode)&&isRing(it)) box[it]=(box[it]||0)+(+n0||0); }
  for(const k in box) if(box[k]>0) m[k]=box[k]; else delete m[k];
  delete m.g_life; // b122: 생명 상자에서 나온 생명의 연마석은 따로 칸·점수 없음 (상자 0.4점만)
  for(const [a2,n0] of Object.entries(items||{})){ const {it,mode}=parseIK(a2); if(it==='g_life'&&want(mode)&&ITEMS[it]) m.g_life=(m.g_life||0)+(+n0||0); } if(!(m.g_life>0)) delete m.g_life; // 보스가 직접 준 생명의 연마석은 그대로
  return m; }
const kingSc10 = m => Object.entries(m).reduce((t,[k,n])=>t+n*sc10(lootBase(k)),0);
const fmtSc = t => `${t/10}점`;
const scCls = r => 'sc sc-'+(medal(r)||'w');
const SC_SUB = '<div class="kingsub">(흑옥 0.1점, 백옥 0.2점, 생명 0.4점, 아이템 1점)</div>';
const noBust = m => Object.fromEntries(Object.entries(m).filter(([k])=>!/^x:/.test(k))); // 꽝 제외
function kingHtml(T,which){
  const ord=orderedChars().map(c=>c.id), oi=o=>{ const i=ord.indexOf(o.id); return i<0?1e6:i; }, tb=(a,b)=>oi(a)-oi(b)||a.name.localeCompare(b.name);
  const mr=T.chars.slice().sort((a,b)=>(b.week+b.month)-(a.week+a.month)||tb(a,b));
  const lr=T.chars.map(o=>{ const m=kingLoot(o.items,o.outs,md=>md!=='l'); return {...o,loot:m,ln:Object.values(m).reduce((x,y)=>x+y,0),sc:kingSc10(m)}; }).filter(o=>o.ln>0).sort((a,b)=>b.sc-a.sc||b.ln-a.ln||tb(a,b));
  const top1=mr[0]&&(mr[0].week+mr[0].month)>0&&S.characters.find(x=>x.id===mr[0].id); // b62: 제목 아이콘 = 현재 1위 캐릭터 초상화 (없으면 메소 아이콘)
  const MK=`<div class="card kingcard" id="mesoKing"><h2>${top1?avatar(top1,'hking'):miniIcon('meso')} 메소왕</h2><div style="overflow-x:auto"><table class="ranktbl"><thead><tr><th>순위</th><th>캐릭터</th><th class="num">누적 주간 메소량</th><th class="num">누적 월간 메소량</th><th class="num">누적 합계</th></tr></thead><tbody>
    ${rankSlice('meso',mr).map(([o,r])=>`<tr class="rk${r}${medal(r)?' md-'+medal(r):''}"><td>${rankNo(r)}</td><td>${rankName(o,r)}</td><td class="num">${meso(o.week)}</td><td class="num">${o.month?meso(o.month):'-'}</td><td class="num"><b>${meso(o.week+o.month)}</b></td></tr>`).join('')||'<tr><td colspan="5" class="muted">기록 없음</td></tr>'}${rankPad(rankSlice('meso',mr).length,mr.length,5)}
    </tbody></table></div>${rankPager('meso',mr.length)}</div>`;
  const lk1=lr[0]&&S.characters.find(x=>x.id===lr[0].id); // b229: 제목 아이콘 = 득템왕 1위 캐릭터 초상화 (없으면 예전 아이콘)
  const LK=`<div class="card kingcard" id="lootKing"><h2>${lk1?avatar(lk1,'hking'):itemIcon('oath')} 득템왕</h2>${SC_SUB}<div style="overflow-x:auto"><table class="ranktbl"><thead><tr><th>순위</th><th>캐릭터</th><th class="scth">점수</th><th>누적 획득 아이템</th></tr></thead><tbody>
    ${rankSlice('loot',lr).map(([o,r])=>`<tr class="rk${r}${medal(r)?' md-'+medal(r):''}"><td>${rankNo(r)}</td><td>${rankName(o,r)}</td><td class="sctd"><b class="${scCls(r)}">${fmtSc(o.sc)}</b></td><td>${(()=>{ const q=chaosMerge(o.loot); return lootChips(q.m,!!medal(r),q.tips); })()}</td></tr>`).join('')||'<tr><td colspan="4" class="muted">기록 없음</td></tr>'}${rankPad(rankSlice('loot',lr).length,lr.length,4)}
    </tbody></table></div>${rankPager('loot',lr.length)}</div>`;
  return which==='meso'?MK:which==='loot'?LK:MK+LK;
}
/* ---------- b55: 순위 표 공통 · 보스왕 · 에픽빔왕 · 상자깡 · 못 가진 아이템 ---------- */
// 아이템 우선순위 (동점·목록 정렬): 1 광휘 · 1.5 익셉셔널 해머·창세의 뱃지 · 2 신념 연마석/칠흑(루컨마·커포 포함) · 3 생명 연마석/리4/컨4/생명 상자 · 4 소울 에테르 4→1, 백옥 상자 · 5 흑옥 상자 · 6 나머지
function itemPri(k){ const b=String(k).replace(/^cb:/,'').replace(/@[wl]$/,''); const I=ITEMS[b]; if(b==='hong_r4'||b==='hong_c4') return 3.01; // b229: 일반 리4/컨4 바로 다음
  if(I&&I.set==='광휘') return 1;
  if(b==='genesis'||(I&&I.set==='해머')) return 1.5; // b53: 익셉셔널 해머·창세의 뱃지 = 1.5순위
  if(b==='g_faith') return 3.05; if(b==='g_life') return 3.1; /* b115: 신념의 연마석 = 생명의 연마석 바로 위 */
  if(I&&I.set==='칠흑') return 2; // 루컨마·커포도 다른 칠흑 장신구와 같은 순위
  if(['g_life','ring:r4','ring:c4','r_life'].includes(b)) return 3;
  if(/^se[1-4]$/.test(b)) return 4+(4-+b[2])*.1; if(b==='r_white') return 4.5;
  if(b==='r_black') return 5; return 6; }
const itemCmp = (a,b) => itemPri(a)-itemPri(b)||lootOrd(a)-lootOrd(b);
const DIFF_CLS = {easy:'easy',normal:'normal',hard:'hard',extreme:'extreme',chaos:'chaos'};
const DK = Object.fromEntries(Object.entries(D).map(([k,v])=>[v,k]));
// b97: 순위 동점 → 어려운 난이도 먼저 (익스트림 > 하드 = 카오스 > 노말 > 이지). 키(hard) 또는 표시 이름(하드) 모두 받음, 모르면 맨 뒤
const DIFF_RANK = {extreme:0,hard:1,chaos:1,normal:2,easy:3};
const diffRank = d => DIFF_RANK[d] ?? DIFF_RANK[DK[d]] ?? 9;
// b53: 1~3위일 때만 아이템 글자색 — 광휘·해머 = 핫핑크, 칠흑(상자 포함) = 보라, 연마석·에테르 = 하늘
function itemCol(k){ const b=String(k).replace(/^cb:/,'').replace(/^x:/,'').replace(/@[wl]$/,''), I=ITEMS[b]; if(!I) return '';
  if(I.set==='광휘'||I.set==='해머') return 'ic-pink'; if(I.set==='칠흑') return 'ic-purple'; if(I.set==='연마석'||I.set==='에테르') return 'ic-sky'; return ''; }
const bossDiffHtml = (b,d) => `<span class="bdn">${esc(b.name)}</span> <span class="dlv dlv-${DIFF_CLS[d]||''}">(${D[d]||d})</span>`;
/* 공통 순위 표: rows=[{ico, name, cells:[...]}] (정렬된 상태). 1~3위 메달 색·반짝임·아이콘, 10개씩 고정 크기 */
function rankTable(kind,id,title,heads,rows,opt={}){
  const sl=rankSlice(kind,rows), n=heads.length;
  return `<div class="card kingcard" id="${id}"><h2>${title}</h2>${opt.sub||''}<div style="overflow-x:auto"><table class="ranktbl"><thead><tr><th>순위</th>${heads.map((h,i)=>`<th${i?' class="num"':''}>${h}</th>`).join('')}</tr></thead><tbody>
    ${sl.map(([o,r])=>{ const m=medal(r); return `<tr class="rk${r}${m?' md-'+m:''}"><td>${rankNo(r)}</td><td><span class="rkname ${m?'md-'+m:''}">${m&&o.ico?`<span class="rkico">${o.ico}</span>`:''}<span class="${m?'spk':''}${m&&o.col?' '+o.col:''}">${o.name}</span></span></td>${o.cells.map(c=>`<td class="num">${c}</td>`).join('')}</tr>`; }).join('')||`<tr><td colspan="${n+1}" class="muted">기록 없음</td></tr>`}${rankPad(sl.length,rows.length,n+1)}
    </tbody></table></div>${rankPager(kind,rows.length)}</div>`; }
rankPage.boss=1; rankPage.epic=1; rankPage.chaos=1; rankPage.miss=1;
/* zosu-crystal: 결정석 보스왕 = 그 보스가 쌓아준 누적 메소 내림차순 → 같으면 난이도(익스트림>하드=카오스>노말>이지) → 처치 횟수 → 비싼 보스.
 * 키 삭제된 계정(goneAcc·키 없음 = charShown false)의 캐릭터는 visibleCharIds() 로 제외(규칙 9; totalData 의 visHist 와 같은 기준, 한 번 더 확인). */
function bossKills(T){ const R={}, VI=activeIds();
  const go=p=>{ if(!p||!p.id||!VI.has(p.id)) return; (p.bosses||[]).forEach((t,i)=>{ const m=/^(.+?)\((.+?)\)(?:\/(\d+)인)?/.exec(t); if(!m) return; const b=BOSSES.find(x=>x.name===m[1]); const d=DK[m[2]]; if(!b||!d) return;
    const k=b.id+'|'+d, o=R[k]||(R[k]={b,d,n:0,cry:0,sale:0,meso:0}); o.n++; const v=p.bvals&&p.bvals[i]!=null?+p.bvals[i]:Math.floor(price(b,d)/Math.max(1,+m[3]||1)); o.cry+=v||0; o.meso+=v||0; });
    // b110: 그 보스가 준 아이템의 판매값 (키 '보스|아이템', 난이도 = 그 기록의 보스 태그)
    for(const [ik,r] of Object.entries(p.revs||{})){ if(!r||!(+r.m>0)) continue; const b=findBoss(parseIK(ik).slot); if(!b) continue;
      const t=(p.bosses||[]).find(x=>x.startsWith(b.name+'(')), mm=t&&/^(.+?)\((.+?)\)/.exec(t), d=mm&&DK[mm[2]]||(S.characters.find(x=>x.id===p.id)?.bosses?.[b.id]?.diff)||b.diffs[0];
      const k=b.id+'|'+d, o=R[k]||(R[k]={b,d,n:0,cry:0,sale:0,meso:0}); o.sale+=+r.m; o.meso+=+r.m;
      const it=r.i||parseIK(ik).it, L=o.its||(o.its={}), dv=+r.p>1?+r.p:1, q=L[it+'|'+dv]||(L[it+'|'+dv]={it,dv,n:0,m:0}); q.n++; q.m+=+r.m; } };
  T.weeks.forEach(w=>(w.perChar||[]).forEach(go)); T.months.forEach(m=>(m.perChar||[]).forEach(go));
  return Object.values(R).sort((a,b)=>b.meso-a.meso||diffRank(a.d)-diffRank(b.d)||b.n-a.n||price(b.b,b.d)-price(a.b,a.d)); }
/* b115: 보스 메소왕 '누적 아이템 판매값' 말풍선 — [초상화+난이도] 보스 이름 (난이도) / 선 / 이 보스가 준 아이템(분배 표시) 몇 개, 얼마 */
function saleTip(o){ const L=Object.values(o.its||{}).sort((a,b)=>itemCmp(a.it,b.it)||a.dv-b.dv); if(!L.length) return '';
  const h=`<div class="bkt-h">${bossPic(o.b,o.d,false)}<b>${esc(o.b.name)} (${esc(D[o.d]||'')})</b></div><div class="bkt-l">${L.map(q=>`<div class="bkt-r">${lootLabel(q.it,{cls:'bkt-n',extra:q.dv>1?` <span class="muted">(${q.dv}인 분배)</span>`:''})}<span class="bkt-v">${q.n}개, ${meso(q.m)}</span></div>`).join('')}</div>`;
  return ` data-tip="${esc(o.b.name)}" data-tiphtml="${esc(h)}"`; }
function bossKingHtml(T){ const R=bossKills(T);
  return rankTable('boss','bossKing',`${R[0]?`<span class="hbi">${bossIcon(R[0].b)}</span>`:miniIcon('meso')} 보스 메소왕`,['보스','처치 당한 횟수','누적 결정석','누적 아이템 판매값','누적 메소량'],
    R.map(o=>({ico:bossPic(o.b,o.d),name:bossDiffHtml(o.b,o.d),cells:[`<b>${o.n}회</b>`,meso(o.cry),o.sale>0?`<span class="bksale"${saleTip(o)}>${meso(o.sale)}</span>`:meso(o.sale),`<b>${meso(o.meso)}</b>`]}))); }
function epicCounts(T){ const R={}; T.items.forEach(([a,I])=>{ const {it}=parseIK(a); if(isRing(it)||isHong(it)) return; R[it]=(R[it]||0)+I.n; }); return R; } // b229: 홍옥 리4/컨4 도 상자에서 나온 것 → 제외 // 반지 상자와 상자에서 나온 것(리4·컨4·연마석)은 제외, 보스가 직접 준 생명의 연마석은 포함
function chaosCounts(T){ const C=Object.fromEntries(CHAOS_PICK.map(k=>[k,0])); T.items.forEach(([a,I])=>{ if(parseIK(a).it!=='chaosbox') return; (I.outs||[]).forEach(o=>{ const k=String(o).slice(3); if(/^cb:/.test(o)&&k in C) C[k]++; }); }); return C; }
/* b202: 상자깡 비율 = 그 아이템 횟수 / 전체 상자깡 횟수(모든 횟수 합), 소수 1자리. 0개 = 0%, 전체 0 = '-' */
const cbPct=(n,t)=>!t?'-':!n?'0%':(n/t*100).toFixed(1)+'%';
function epicKingHtml(T){ const R=epicCounts(T), tot=Object.values(R).reduce((x,y)=>x+y,0);
  const ks=Object.keys(R).sort((a,b)=>R[b]-R[a]||itemCmp(a,b)), C=chaosCounts(T), ctot=Object.values(C).reduce((x,y)=>x+y,0), cs=CHAOS_PICK.slice().sort((a,b)=>C[b]-C[a]||itemCmp(a,b));
  return rankTable('epic','epicCard',`${miniIcon('sos')} <span class="ept">에픽빔왕</span>`,['아이템','횟수'],ks.map(k=>({ico:lootIco(k),col:itemCol(k),name:k==='chaosbox'?`<span class="tipname"${tipAttr(chaosTip(C,Math.max(0,R[k]-Object.values(C).reduce((x,y)=>x+y,0))))}>${esc(lootName(k))}</span>`:esc(lootName(k)),cells:[xN(R[k])]})),
      {sub:`<div class="epline">에픽빔 누적 횟수 <b class="epgold">${tot}</b></div>`})
    +rankTable('chaos','chaosCard',`${miniIcon('chaosbox')} 혼돈의 칠흑 장신구 상자깡`,['아이템','비율','횟수'],cs.map(k=>({ico:itemIcon(k),col:'ic-purple',name:esc(ITEMS[k].n),cells:[`<span class="cbpct">${cbPct(C[k],ctot)}</span>`,xN(C[k])]}))); }
/* 못 가진 아이템: 모든 보스 드롭 표의 누를 수 있는 아이템 중 한 번도 못 얻은 것 (블빵패배 제외, 분배·블빵승리·1인 = 얻음).
 * 칠흑 상자에서 고른 장신구 = 그 장신구 얻음. 반지 상자: 상자를 얻었으면(결과 무관) 그 상자는 얻음, 상자 결과 생명의 연마석 = 생명의 연마석 얻음. 리4·컨4는 드롭 표 칩이 아니라 목록에 없음.
 * 아이템마다 1줄: 결정석이 가장 싼 보스(난이도)로 표시 */
function missingItems(T){ const got=new Set();
  T.chars.forEach(o=>{ for(const [a,n] of Object.entries(o.items||{})){ const {it,mode}=parseIK(a); if(mode==='l'||!(+n>0)) continue; got.add(it); ((o.outs||{})[a]||[]).forEach(q=>{ if(/^cb:/.test(q)) got.add(q.slice(3)); if(q==='gl') got.add('g_life'); }); } });
  const src={}; BOSSES.forEach(b=>b.diffs.forEach(d=>dropsFor(b,d).forEach(k=>{ if(got.has(k)||MISS_SKIP_SET.has(ITEMS[k]?.set)) return; const p=price(b,d); (src[k]||(src[k]={p:Infinity,list:[]})).list.push({b,d,p}); src[k].p=Math.min(src[k].p,p); })));
  Object.values(src).forEach(o=>o.list.sort((x,y)=>x.p-y.p)); // 같은 아이템을 주는 보스 전부 (결정석 싼 순)
  // zosu-sort: 보스 순서가 아이템 순서보다 먼저 — 줄의 대표 보스(결정석 가장 싼 보스·난이도 = list[0])의 BOSSES 순 → 같은 보스면 난이도(익스트림>하드=카오스>노말>이지) → 그다음 아이템 우선순위
  const bi=s=>{ const i=BOSSES.indexOf(s); return i<0?999:i; };
  return Object.keys(src).sort((a,b)=>bossStr(src[a].list[0].b,src[a].list[0].d)-bossStr(src[b].list[0].b,src[b].list[0].d)||bi(src[a].list[0].b)-bi(src[b].list[0].b)||itemPri(a)-itemPri(b)||src[a].p-src[b].p||lootOrd(a)-lootOrd(b)).map(k=>({k,...src[k]})); }
// 같은 보스의 여러 난이도는 한 덩어리로: 림보 (노말)(하드) — 한 줄에 최대한 들어가게
const missGroups = list => { const g=[]; list.forEach(x=>{ let e=g.find(y=>y.b===x.b); if(!e) g.push(e={b:x.b,ds:[]}); e.ds.push(x.d); }); return g; };
// 못 가진 아이템 목록 (b61): 보스 칸 = 남는 폭 전부(아이콘·이름 칸은 내용 폭), 가로 스크롤 없음.
// 줄마다 따로: 13px 에서 한 줄에 안 들어가면 그 줄만 0.5px씩 줄임(최소 10.5px) → 그래도 안 되면 보스 아이콘 생략 후 다시(최소 10px)
// → 그래도 안 되면 보스 묶음(이름+난이도) 단위로만 다음 줄(묶음 안은 절대 안 끊김). 아이템 이름은 항상 한 줄.
function fitMiss(){ const t=document.querySelector('#missItems .misstbl'); if(!t) return;
  const one=l=>{ const k=l.children; return !k.length||k[k.length-1].offsetTop-k[0].offsetTop<2; };
  t.querySelectorAll('.missbl').forEach(l=>{ l.classList.remove('noico','tight'); let fs=15; const set=()=>l.style.setProperty('--msfs',fs+'px'); set();
    while(!one(l)&&fs>10.5){ fs-=.5; set(); }
    if(!one(l)){ l.classList.add('noico'); fs=15; set(); while(!one(l)&&fs>10){ fs-=.5; set(); }
      if(!one(l)){ l.classList.add('tight'); fs=13; set(); while(!one(l)&&fs>10){ fs-=.5; set(); } }  // b253: 구분점·간격 좁혀 한 번 더(1600px 생명 반지 상자 줄)
      if(!one(l)){ fs=11; set(); } } }); }
function missingHtml(T){ const L=missingItems(T), sl=rankSlice('miss',L);
  return `<div class="card" id="missItems"><h2>${L[0]?`<span class="gray">${itemIcon(L[0].k)}</span>`:miniIcon('chaosbox')} 내가 획득 못한 아이템 목록</h2>
    ${L.length?`<div class="misswrap"><table class="ranktbl misstbl"><tbody>${sl.map(([o])=>`<tr><td class="missb"><div class="missbl">${missGroups(o.list).map(g=>`<span class="missbn"><span class="hbi">${bossIcon(g.b)}</span><span class="bdn">${esc(g.b.name)}</span>${g.ds.map(d=>dlvHtml(d)).join('')}</span>`).join('')}</div></td><td class="missi">${itemIcon(o.k)}</td><td class="missn">${esc(ITEMS[o.k].n)}</td></tr>`).join('')}${rankPad(sl.length,L.length,3)}</tbody></table></div>${rankPager('miss',L.length)}`:'<p class="muted">모든 아이템을 가졌어요!</p>'}</div>`; }
function bbangStats(T){ const p={}; for(const o of T.chars) for(const [a,n] of Object.entries(o.items||{})){ const {party,mode}=parseIK(a); if(mode!=='w'&&mode!=='l') continue; const q=p[party]||(p[party]={w:0,l:0}); q[mode]+=+n||0; } return p; }
const blinkIco = cls => `<span class="blk ${cls||''}" aria-hidden="true">${miniIcon('blink')}</span>`;
function bbangHtml(T){
  const st=bbangStats(T), rows=[2,3,4,5,6].filter(k=>st[k]&&(st[k].w+st[k].l));
  const won={}, lost={}; for(const o of T.chars){ const w=lootOf(o.items,o.outs,m=>m==='w'), l=lootOf(o.items,o.outs,m=>m==='l');
    for(const [k,n] of Object.entries(w)) won[k]=(won[k]||0)+n; for(const [k,n] of Object.entries(l)) lost[k]=(lost[k]||0)+n; }
  return `<div class="card bbcard" id="bbCard"><div class="bbpart" id="bbRate"><h2><span class="blk split" aria-hidden="true"><span class="bk-a">${miniIcon('blink')}</span><span class="bk-b">${miniIcon('blink')}</span></span> 물욕 블빵 승률</h2>
    ${rows.length?`<table class="bbtbl"><tbody>${rows.map(k=>{ const q=st[k], t=q.w+q.l; return `<tr data-party="${k}"><td>${k}인</td><td class="num"><b>${(q.w/t*100).toFixed(1)}%</b></td><td class="muted">${q.w}승 ${q.l}패</td></tr>`; }).join('')}</tbody></table>`:'<p class="muted">아직 블빵 기록이 없어요</p>'}</div>
  <div class="bbpart" id="bbWon"><h2>${blinkIco()} 블빵 이겨서 얻은 아이템들</h2>${Object.keys(won).length?lootChips(won):'<p class="muted">아직 없어요</p>'}</div>
  <div class="bbpart" id="bbLost"><h2>${blinkIco('gray')} 블빵 져서 잃은 아이템들</h2>${Object.keys(lost).length?lootChips(lost):'<p class="muted">아직 없어요</p>'}</div></div>`;
}
/* b176: 평균 공통 — 진행 중인 주(월)는 빼고 끝난 기간만. 끝난 기간이 없으면 null('집계 중') */
const avgDone=(sum,n)=>n>0?sum/n:null;
function doneAvgs(T){ const D=totalData(true), nw=D.weeks.length, MW=monthlyByWeek(D);
  const sale=D.weeks.reduce((t,w)=>t+(w.isale||0),0)+Object.values(MW).reduce((t,o)=>t+(o.sale||0),0);
  const dm=T.months.filter(m=>!m.cur&&m.total);
  return {n:nw,grand:avgDone(D.grand,nw),wTotal:avgDone(D.wTotal,nw),sales:avgDone(sale,nw),items:avgDone(lootSummary(D).items,nw),mTotal:avgDone(dm.reduce((t,m)=>t+m.total,0),dm.length)}; }
const avgTxt=(u,v,unit)=>v==null?`${u} 평균 집계 중`:`${u} 평균 `+(unit?(Math.round(v*10)/10)+unit:Math.round(v).toLocaleString()+' 메소');
const weekTag=n=>`<span class="muted wktag" style="font-weight:500">${fmtWeek(S.startWeek).split(' ~')[0]}부터 · ${n}주차</span>`;
function renderTotal(){
  const v=$('#view'); const T=totalData();
  const nW=T.weeks.length, A=doneAvgs(T);
  let cum=0; const bk=bossKills(T)[0];
  v.innerHTML=`<div class="grid"><div class="card">
    <h2>${miniIcon('ipc')} 누적 수입 ${weekTag(nW)}</h2>
    <div class="stats s3 kbig">
      <div class="stat"><div class="k">${miniIcon('meso')}<span class="kt">총 수익</span></div><div class="v acc tirv tgoldv">${tirN(T.grand,'eok','grand')}</div><div class="muted" id="grandAvg">${tsm(avgTxt('주',A.grand))}</div></div>
      <div class="stat"><div class="k"><span class="hbi">${bossIcon(bk?bk.b:findBoss('kaling'))}</span><span class="kt">주보 누적 메소량</span></div><div class="v tirv">${tirN(T.wTotal,'eok','wTotal')}</div><div class="muted">${tsm(avgTxt('주',A.wTotal))}</div></div>
      <div class="stat"><div class="k"><span class="hbi">${bossIcon(findBoss('blackmage'))}</span><span class="kt">검마 누적 메소량</span></div><div class="v tirv">${T.mTotal?tirN(T.mTotal,'eok','mTotal'):tir('-')}</div><div class="muted">${tsm(avgTxt('월',A.mTotal))}</div></div>
    </div>
  </div>
  <div class="card"><h2>📈 주간 메소 그래프</h2>${cumLineChart(T.weeks,T,{perWeek:1})}</div>
  ${kingHtml(T,'meso')}
  ${bossKingHtml(T)}
  ${missHtml()}
  <div class="card"><h2>🗓 전체 주 목록</h2><div style="overflow-x:auto"><table><thead><tr><th>주차</th><th class="num">클리어</th><th class="num">아이템</th><th class="num">주간 수익</th><th class="num">누적</th></tr></thead><tbody>
    ${(MW=>T.weeks.map(w=>({...w,total:(w.total||0)+((MW[w.week]||{}).meso||0)})))(monthlyByWeek(T)).map(w=>{cum+=w.total||0;return {w,cum};}).reverse().map(({w,cum})=>`<tr><td>${fmtWeek(w.week)}${w.cur?' <span class="pill">이번 주</span>':''}</td><td class="num">${w.cleared??'-'}</td><td class="num">${w.items??itemSum(Object.assign({},...(w.perChar||[]).map(p=>p.items||{})))}</td><td class="num"><b>${meso(w.total||0)}</b></td><td class="num muted">${meso(cum)}</td></tr>`).join('')}
  </tbody></table></div></div></div></div>`;
}
/* b60: 득템 분석 탭 — 결정석 분석에서 옮긴 득템 관련 카드들(모양 그대로) + 맨 위 '누적 득템' 3칸 */
const RING_NOCOUNT = new Set(['r_green','r_red']); // 총 득템·반상 상위에서 제외하는 반지 상자 (b120: '반상 상위' 카드 = 리4·컨4 운 상위 %, 밑 글씨 = 반상 누적 N회)
/* b111: 상위 % = 포아송 이항분포 P(X ≥ 실제). ps = 시행마다 성공 확률 → 성공 k번 이상 나올 확률(%) */
function pbTail(ps,k){ if(k<=0) return 100; let d=[1]; for(const p of ps){ const n=new Array(d.length+1).fill(0); for(let i=0;i<d.length;i++){ n[i]+=d[i]*(1-p); n[i+1]+=d[i]*p; } d=n; }
  let t=0; for(let i=k;i<d.length;i++) t+=d[i]; return Math.min(100,Math.max(0,t*100)); }
const topPct=v=>v==null?'-':`상위 ${v>=0.1||v===0?(Math.round(v*10)/10):Number(v.toPrecision(1))}%`;
function lootSummary(T){
  let items=0, rings=0; const byBox={}, tl={r4:0,c4:0,gl:0}, ex={r4:0,c4:0}, ps=[];
  T.items.forEach(([a,I])=>{ const {it,mode}=parseIK(a); if(mode==='l') return; // 블빵패배는 얻은 게 아님
    if(isRing(it)){ const t=outTally(I.outs,I.n); items+=t.r4+t.c4; // b111: 상자에서 나온 리4·컨4도 득템 1개씩 (녹옥·홍옥 포함)
      if(RING_NOCOUNT.has(it)) return; rings+=I.n; /* b182b: 반지 상자 자체는 총 득템·평균에서 전부 제외 */ byBox[it]=(byBox[it]||0)+I.n;
      tl.r4+=t.r4; tl.c4+=t.c4; const q=ring4(it); if(q){ if(q.gl) tl.gl+=t.gl; ex.r4+=I.n*q.r4/100; ex.c4+=I.n*q.c4/100; const rec=t.r4+t.c4+t.gl+t.x; for(let i=0;i<rec;i++) ps.push((q.r4+q.c4+q.gl)/100); } } // b122: 생명 상자는 연마석도 성공 (상자 1개 = 리4·컨4·연마석 중 하나가 나올 확률을 합친 성공 확률 1개)
    else items+=I.n; });
  const st=bbangStats(T), wins=Object.values(st).reduce((x,q)=>x+q.w,0);
  const E=epicCounts(T), ek=Object.keys(E).sort((a,b)=>E[b]-E[a]||itemCmp(a,b))[0];
  const bk=Object.keys(byBox).sort((a,b)=>byBox[b]-byBox[a]||itemCmp(a,b))[0];
  const exp=ex.r4+ex.c4, rate=exp>0?(tl.r4+tl.c4)/exp*100:null;
  const ringTop=ps.length?pbTail(ps,tl.r4+tl.c4+tl.gl):null; // 결과를 기록한 상자만 시행으로 셈
  const bp=[]; let games=0; for(const [n,q] of Object.entries(st)){ const k=+n; if(!(k>=2)) continue; for(let i=0;i<q.w+q.l;i++) bp.push(1/k); games+=q.w+q.l; }
  const bbTop=games?pbTail(bp,wins):null, bbRows=[2,3,4,5,6].filter(k=>st[k]&&(st[k].w+st[k].l)).map(k=>`${k}인 (${st[k].w}승 ${st[k].l}패)`); const bbRowsT=[2,3,4,5,6].filter(k=>st[k]&&(st[k].w+st[k].l)).map(k=>`${tir(k+'인')} (${tirN(st[k].w,'cnt','lt:bw'+k,'승')} ${tirN(st[k].l,'cnt','lt:bl'+k,'패')})`);
  return {items,rings,wins,ringTop,bbTop,bbRows,bbRowsT,epicIco:ek?lootIco(ek):itemIcon('genesis'),boxIco:itemIcon(bk||'r_black'),rate};
}
function ringCardHtml(T){ return `  <div class="card ringcard"><h2>${miniIcon('ring_restraint')} 시드링 획득 타율</h2>
    ${(()=>{const r=T.ring, rec=r.r4+r.c4+(r.gl||0)+r.x; return rec+r.un?`<div class="ringsum">${miniIcon('ring_continuous')} <b class="rslab">반지 상자 결과</b> : ${[r.r4?`<span class="ro ro-r4">${outIcon('r4')}리4 <b>${xN(r.r4)}</b></span>`:'',r.c4?`<span class="ro ro-c4">${outIcon('c4')}컨4 <b>${xN(r.c4)}</b></span>`:'',r.gl?`<span class="ro ro-gl">${outIcon('gl')}생명의 연마석 <b>${xN(r.gl)}</b></span>`:'',r.x?`<span class="ro ro-x">꽝 <b>${xN(r.x)}</b></span>`:'',r.un?`<span class="ro ro-un">미기록 <b>${xN(r.un)}</b></span>`:''].filter(Boolean).join(' · ')} ${ringExpHtml(T)}</div>`:'';})()}
    ${(()=>{ const h={r4:0,c4:0}; T.items.forEach(([a,I])=>{ const {it,mode}=parseIK(a); if(mode!=='l'&&isHong(it)) h[it.slice(5)]+=I.n; }); // b229: 홍옥 반지 상자로 얻은 리4/컨4 — 꽝·기댓값 없음
      return h.r4+h.c4?`<div class="ringsum hongsum">${itemIcon('r_red')} <b class="rslab">홍옥 반지 상자로 얻은 리4/컨4</b> <span class="hsr">: ${[h.r4?`<span class="ro ro-r4">${outIcon('r4')}리4 <b>${xN(h.r4)}</b></span>`:'',h.c4?`<span class="ro ro-c4">${outIcon('c4')}컨4 <b>${xN(h.c4)}</b></span>`:''].filter(Boolean).join(' · ')}</span></div>`:''; })()}
    ${(()=>{ const R={}; T.items.forEach(([a,I])=>{ const {it,mode}=parseIK(a); if(!isRing(it)) return; const kk=it+(mode?'@'+mode:''); const o=R[kk]||(R[kk]={n:0,outs:[]}); o.n+=I.n; o.outs.push(...I.outs); });
      const ks=Object.keys(R).sort((x,y)=>lootOrd(x)-lootOrd(y));
      return ks.length?`<div class="totloot">${ks.map(k=>`<div class="tl"><span class="loot">${lootIco(k)}<span class="ln">${esc(lootName(k))}${modeTag(k)}</span> <b class="lx">${xN(R[k].n)}</b></span>${outHtml(R[k].outs,R[k].n,true)}</div>`).join('')}</div>`:'<p class="muted">아직 획득한 반지 상자가 없습니다.</p>'; })()}</div>`; }
// b62-8: 아이템 판매 수익 (드롭 때 '수익을 기록할까요?' 에서 입력한 값, 분배는 내 몫) — 간단 카드 (사용자가 나중에 다듬을 예정)
function salesHtml(T){ // b76: '아이템 판매 누적 수익' — 아이템·분배 인원별 줄, 제목 아이콘 = 누적 판매 금액 1위 아이템(b229)
  const S_=T.sales||{}, ok=k=>{ try{ return !!lootName(S_[k].i||k.split('#')[0]); }catch(e){ return false; } };
  const ks=Object.keys(S_).filter(ok).sort((a,b)=>S_[b].m-S_[a].m||itemCmp(S_[a].i||a,S_[b].i||b)||(S_[a].p||1)-(S_[b].p||1)), tot=ks.reduce((x,k)=>x+S_[k].m,0);
  const top={}; ks.forEach(k=>{ const i=S_[k].i||k.split('#')[0]; top[i]=(top[i]||0)+S_[k].m; }); // b229: 제목 아이콘 = 누적 판매 금액이 가장 큰 아이템 (분배 인원 줄 합침)
  const best=Object.keys(top).sort((a,b)=>top[b]-top[a]||itemCmp(a,b))[0];
  const ico=best?`<span class="hbi">${lootIco(best)}</span>`:miniIcon('meso'), pl=p=>p>1?`${p}인 분배`:'1인';
  return `<div class="card" id="salesCard"><h2>${ico} 아이템 판매 누적 수익</h2>
    <div class="stats s3"><div class="stat"><div class="k">${miniIcon('meso')}<span class="kt">총 판매 수익</span></div><div class="v acc tirv tgoldv">${tot?tirN(tot,'eok','sales',' 메소'):tir('-')}</div><div class="muted" id="salesAvg">${tsm(avgTxt('주',doneAvgs(T).sales))}</div></div></div>
    ${ks.length?`<div class="slist">${ks.map(k=>{ const o=S_[k], i=o.i||k.split('#')[0]; return `<div class="sl"><span class="loot"${isHong(i)?` title="${esc(lootName(i))}"`:''}>${lootLabel(i)} <span class="slp">${pl(o.p||1)}</span> <b class="lx">${xN(o.n)}</b></span><b class="slm tirv">${tirMeso(o.m,'sl:'+k)}</b></div>`; }).join('')}</div>`:'<p class="muted" style="margin:8px 0 0">아직 기록한 판매 수익이 없어요 — 보스 드롭을 기록할 때 금액을 넣으면 여기에 모여요.</p>'}</div>`; }
/* b229: '주별 득템 캐릭터 정리' — 한 쪽 = 한 주(목요일 초기화 주, 최신 주가 기본). 캐릭터별 그 주에 얻은 아이템 아이콘 xN.
 * 셈법 = 득템왕과 같은 lootOf(블빵패배 제외) + 꽝 제외 + 반지 상자는 결과(리4·컨4·생명의 연마석)만(b226 이번주 획득 아이템과 같음, 결과 미기록 상자는 안 셈).
 * 검마(월간 기록) 아이템 = 그 검마를 잡은 주(mweeks)로. 주간 기록(S.history)마다 perChar.items·outcomes 가 있어 지난 주도 그대로 나옴.
 * 모든 주를 같은 칸에 겹쳐 그리고(.wlpg grid) 지금 주만 보임 → 표 높이 = 가장 긴 주(쪽을 넘겨도 크기 그대로) */
let WL_PAGE=0; // 0 = 최신 주
function weekLootData(T){
  const nameOf=p=>{ const c=p.id&&S.characters.find(x=>x.id===p.id); return c?c.name:p.name; };
  const wks=T.weeks.map(w=>w.week).filter(Boolean), by={};
  const put=(wk,p,items,outs)=>{ if(!wk||!wks.includes(wk)) return;
    const m=noBust(lootOf(items,outs,md=>md!=='l')); for(const k of Object.keys(m)) if(isRing(k)||!(m[k]>0)) delete m[k];
    if(!Object.keys(m).length) return;
    const W=by[wk]||(by[wk]={}), key=p.id&&S.characters.some(x=>x.id===p.id)?p.id:'n:'+p.name, o=W[key]||(W[key]={id:p.id,name:nameOf(p),m:{}});
    for(const [k,n] of Object.entries(m)) o.m[k]=(o.m[k]||0)+n; };
  T.weeks.forEach(w=>(w.perChar||[]).forEach(p=>put(w.week,p,p.items,p.outcomes)));
  T.months.forEach(M=>(M.perChar||[]).forEach(p=>{ const tags=p.bosses||[], mw=p.mweeks||[], one=[...new Set(mw.filter(Boolean))];
    for(const [ik,n] of Object.entries(p.items||{})){ const b=findBoss(parseIK(ik).slot); const i=b?tags.findIndex(t=>t.startsWith(b.name+'(')||t===b.name):-1;
      const wk=(i>=0&&mw[i])||(one.length===1?one[0]:''); put(wk,p,{[ik]:n},{[ik]:(p.outcomes||{})[ik]||[]}); } }));
  const ord=orderedChars().map(c=>c.id), oi=o=>{ const i=ord.indexOf(o.id); return i<0?1e6:i; };
  return wks.slice().sort((a,b)=>a<b?1:-1).map(wk=>({wk,cur:wk===S.period.week,no:wks.slice().sort().indexOf(wk)+1,rows:Object.values(by[wk]||{}).sort((a,b)=>oi(a)-oi(b)||a.name.localeCompare(b.name))}));
}
function wlIco(pg){ const t={}; pg.rows.forEach(o=>{ const q=chaosMerge(o.m).m; for(const [k,n] of Object.entries(q)) t[k]=(t[k]||0)+n; });
  const best=Object.keys(t).sort((a,b)=>t[b]-t[a]||itemCmp(a,b))[0]; return best?`<span class="hbi">${lootIco(best)}</span>`:itemIcon('oath'); }
const wlLabel = pg => `${fmtWeek(pg.wk)} · ${pg.no}주차${pg.cur?' (이번 주)':''}`;
// b230: 오른쪽 위 주 선택칸 — 글 = 'N주차 (이번 주) · 날짜'(넓은 화면) / 'N주차 (이번 주)'(좁은 화면, 날짜는 밑 ◀▶ 줄에 있음)
const wlOptL = pg => `${pg.no}주차${pg.cur?' (이번 주)':''} · ${fmtWeek(pg.wk)}`, wlOptS = pg => `${pg.no}주차${pg.cur?' (이번 주)':''}`;
const WL_MQ = typeof matchMedia==='function'?matchMedia('(max-width:560px)'):null;
const wlOpt = pg => WL_MQ&&WL_MQ.matches?wlOptS(pg):wlOptL(pg);
function wlGo(card,idx){ const pages=[...card.querySelectorAll('.wlpage')]; if(!pages.length) return; WL_PAGE=Math.min(Math.max(0,idx),pages.length-1);
  pages.forEach((x,i)=>{ x.classList.toggle('on',i===WL_PAGE); if(i===WL_PAGE) x.removeAttribute('aria-hidden'); else x.setAttribute('aria-hidden','true'); });
  const pg=pages[WL_PAGE]; card.querySelector('.wlico').innerHTML=pg.dataset.wlico; card.querySelector('.wlnow').textContent=pg.dataset.wllb;
  const sel=card.querySelector('.wlsel'); if(sel) sel.value=String(WL_PAGE);
  const [older,newer]=card.querySelectorAll('[data-wlpg]'); if(older) older.disabled=WL_PAGE>=pages.length-1; if(newer) newer.disabled=WL_PAGE<=0; tipHide?.(); }
function weekLootHtml(T){
  const P=weekLootData(T); WL_PAGE=Math.min(Math.max(0,WL_PAGE),Math.max(0,P.length-1)); const cur=P[WL_PAGE];
  const row=o=>{ const c=o.id&&S.characters.find(x=>x.id===o.id), q=chaosMerge(o.m); return `<div class="wlrow"><span class="wlb">${c?avatar(c,'sm av24'):''}<b>${esc(o.name)}</b></span>${lootChips(q.m,false,q.tips)}</div>`; };
  const sel=P.length?`<select class="wlsel" aria-label="주 선택">${P.map((pg,i)=>`<option value="${i}" data-l="${esc(wlOptL(pg))}" data-s="${esc(wlOptS(pg))}"${i===WL_PAGE?' selected':''}>${esc(wlOpt(pg))}</option>`).join('')}</select>`:'';
  return `<div class="card wkloot" id="weekLoot"><h2><span class="wlico">${cur?wlIco(cur):itemIcon('oath')}</span><span class="wlt">주별 득템 캐릭터 정리</span>${sel}</h2>
    <div class="wlpg">${P.map((pg,i)=>`<div class="wlpage${i===WL_PAGE?' on':''}" data-wlico="${esc(wlIco(pg))}" data-wllb="${esc(wlLabel(pg))}"${i===WL_PAGE?'':' aria-hidden="true"'}>${pg.rows.length?pg.rows.map(row).join(''):'<p class="muted wlempty">이 주에 얻은 아이템이 없어요.</p>'}</div>`).join('')||'<p class="muted">아직 저장된 드랍 기록이 없습니다.</p>'}</div>
    ${P.length?`<div class="cpager wlpager" role="group" aria-label="주 선택"><button type="button" class="cpg" data-wlpg="1"${WL_PAGE>=P.length-1?' disabled':''} aria-label="지난 주">◀</button><span class="wlnow">${esc(wlLabel(cur))}</span><button type="button" class="cpg" data-wlpg="-1"${WL_PAGE<=0?' disabled':''} aria-label="다음 주">▶</button></div>`:''}</div>`;
}
// 쪽 넘기기 = 다시 그리지 않고 보이는 주만 바꿈(표 크기 그대로, 스크롤 그대로)
document.addEventListener('click',e=>{ const b=e.target.closest?.('[data-wlpg]'); if(!b||b.disabled) return; const card=b.closest('#weekLoot'); if(card) wlGo(card,WL_PAGE+(+b.dataset.wlpg||0)); });
document.addEventListener('change',e=>{ const t=e.target; if(!t.classList?.contains('wlsel')) return; const card=t.closest('#weekLoot'); if(card) wlGo(card,+t.value||0); });
WL_MQ?.addEventListener?.('change',()=>document.querySelectorAll('#weekLoot .wlsel option').forEach(o=>{ o.textContent=WL_MQ.matches?o.dataset.s:o.dataset.l; }));
function renderLoot(){
  const v=$('#view'); const T=totalData(), L=lootSummary(T);
  v.innerHTML=`<div class="grid"><div class="card" id="lootTop">
    <h2>${itemIcon('genesis')} 누적 득템 ${weekTag(T.weeks.length)}</h2>
    <div class="stats s3 kbig">
      <div class="stat" id="ltTotal"><div class="k"><span class="hbi">${L.epicIco}</span><span class="kt">총 득템</span></div><div class="v acc tirv">${tirN(L.items,'cnt','lt:items','개')}</div><div class="muted ltcap" id="itemsAvg">${tsm(avgTxt('주',doneAvgs(T).items,'개'))}</div></div>
      <div class="stat" id="ltRing"><div class="k"><span class="hbi">${L.boxIco}</span><span class="kt">반상 상위</span></div><div class="v">${topPctT(L.ringTop,'lt:ring')}</div><div class="muted ltcap">${tsm(`반상 누적 ${L.rings}회, 녹·홍옥 반상 제외`)}</div></div>
      <div class="stat" id="ltBbang"><div class="k"><span class="blk" aria-hidden="true">${miniIcon('blink')}</span><span class="kt">블빵 상위</span></div><div class="v">${topPctT(L.bbTop,'lt:bb')}</div>${L.bbRowsT.length?`<div class="muted bbrows ltcap">${tsm(L.bbRows.join(', '))}</div>`:''}</div>
    </div>
  </div>
  ${salesHtml(T)}
  ${weekLootHtml(T)}
  ${kingHtml(T,'loot')}
  ${poopHtml(T)}
  ${bossLootKingHtml(T)}
  ${epicKingHtml(T)}
  ${missingHtml(T)}
  ${bbangHtml(T)}
  ${bossLootHtml(T)}
  ${ringCardHtml(T)}
  ${itemTotalsHtml(T)}
  </div>`;
}

/* =====================================================================
 *  캐릭터 모달
 * ===================================================================== */
let editingId=null, lookup=null;
function openCharModal(id){
  editingId=id||null; lookup=null; const c=id&&S.characters.find(x=>x.id===id);
  $('#charModalTitle').textContent=c?'캐릭터 수정':'캐릭터 추가';
  $('#fName').value=c?c.name:''; $('#fJob').value=c?c.job:''; $('#fLevel').value=c?c.level:''; $('#fWorld').value=c?c.world:'';
  $('#fMain').checked=c?!!c.isMain:!S.characters.length;
  $('#fAvatar').outerHTML=avatar(c||{name:'?'},'lg').replace('class="avatar lg"','class="avatar lg" id="fAvatar"');
  $('#fAcc').innerHTML=`<option value="">미지정 (수동 캐릭터)</option>`+accounts().map(a=>`<option value="${a.id}">${esc(a.label)}</option>`).join('');
  $('#fAcc').value = c ? (accOf(c)?c.accId:'') : (accounts().find(a=>a.key)?.id||'');
  $('#fLookupMsg').textContent=hasApi()?'이름 입력 후 [API 조회]로 정보를 채울 수 있어요.':'캐릭터 목록의 [+ 추가]에서 API 키를 등록하면 이름만으로 정보를 불러올 수 있어요.';
  $('#fDelete').classList.toggle('hidden',!c);
  $('#charModal').classList.add('show'); loadPick(); setTimeout(()=>$('#fName').focus(),50);
}
/* 캐릭터 추가 모달의 '이 계정 캐릭터에서 선택' 목록 */
let pickSeq=0;
async function loadPick(force){
  const wrap=$('#fPickWrap'), box=$('#fPick'), a=accById($('#fAcc').value);
  if(editingId||!a||!a.key){ wrap.classList.add('hidden'); return; }
  wrap.classList.remove('hidden'); $('#fPickAcc').textContent=a.label;
  const cached=listCache[a.id];
  if(cached && !force && cached.key===a.key && Date.now()-cached.at<10*60e3){ renderPick(); return; }
  const seq=++pickSeq; box.innerHTML='<div class="muted" style="padding:8px"><span class="spin"></span> 캐릭터 목록을 불러오는 중…</div>';
  try{ const all=await listAccount(a); assignFromList(a,all); save(); if(seq===pickSeq) renderPick(); }
  catch(e){ a.status={ok:false,msg:e.message,at:Date.now()}; save(); if(seq===pickSeq) box.innerHTML=`<div class="impmsg err">${errHtml(e,a)}<button class="btn sm plain" id="fPickRetry">다시 불러오기</button></div>`; }
}
function renderPick(){
  const a=accById($('#fAcc').value), box=$('#fPick'), cached=a&&listCache[a.id]; if(!cached||cached.key!==a.key) return;
  if(!cached.all.length){ box.innerHTML=`<div class="impmsg warn">${emptyHtml(a)}<button class="btn sm plain" id="fPickRetry">다시 불러오기</button></div>`; return; }
  const typed=$('#fName').value.trim(), q=(lookup?.ocid&&lookup.name===typed)?'':normName(typed);
  const have=new Set(S.characters.map(c=>c.ocid).filter(Boolean)), haveName=new Set(S.characters.map(c=>c.name));
  const list=cached.all.filter(x=>!q||normName(x.character_name).includes(q)).sort((x,y)=>y.character_level-x.character_level||x.character_name.localeCompare(y.character_name));
  box.innerHTML=list.length?list.map(x=>{const dup=(x.ocid&&have.has(x.ocid))||haveName.has(x.character_name), on=lookup?.ocid&&lookup.ocid===x.ocid;
    return `<button type="button" class="pick-item ${on?'on':''}" data-pick="${esc(x.ocid)}" ${dup?'disabled':''}><b>${esc(x.character_name)}</b><span class="muted">Lv.${x.character_level} · ${esc(x.character_class)} · ${esc(x.world_name)}${dup?' · 추가됨':''}</span></button>`;}).join('')
    :`<div class="muted" style="padding:8px">'${esc(typed)}'와(과) 일치하는 캐릭터가 이 계정에 없습니다 (전체 ${cached.all.length}명).</div>`;
}
async function pickChar(ocid){
  const a=accById($('#fAcc').value), x=listCache[a?.id]?.all.find(y=>y.ocid===ocid); if(!x) return;
  lookup={ocid:x.ocid,name:x.character_name,image:'',exp:null};
  $('#fName').value=x.character_name; $('#fJob').value=x.character_class; $('#fLevel').value=x.character_level||''; $('#fWorld').value=x.world_name;
  $('#fAvatar').outerHTML=avatar({name:x.character_name},'lg').replace('class="avatar lg"','class="avatar lg" id="fAvatar"');
  $('#fLookupMsg').textContent=`✓ '${a.label}' 계정의 캐릭터를 선택했습니다. [저장]을 누르세요.`; renderPick();
  try{ const b=await nx('/maplestory/v1/character/basic',{ocid:x.ocid},a.key); if(lookup?.ocid!==x.ocid) return;
    lookup.image=b.character_image||''; lookup.exp=expFrom(b,x.character_level);
    $('#fAvatar').outerHTML=avatar({name:x.character_name,image:b.character_image},'lg').replace('class="avatar lg"','class="avatar lg" id="fAvatar"'); }catch(e){}
}
function closeCharModal(){ $('#charModal').classList.remove('show'); }
async function lookupByName(){
  const name=$('#fName').value.trim(); if(!name){toast('이름을 입력하세요');markEmpty($('#fName')).focus();return;}
  const msg=$('#fLookupMsg'); msg.innerHTML='<span class="spin"></span> 조회 중…';
  try{
    const key=accById($('#fAcc').value)?.key||anyKey();
    const {ocid}=await nx('/maplestory/v1/id',{character_name:name},key);
    const b=await nx('/maplestory/v1/character/basic',{ocid},key);
    lookup={ocid,name:b.character_name||name,image:b.character_image,exp:expFrom(b)};
    $('#fName').value=b.character_name||name; $('#fJob').value=b.character_class||''; $('#fLevel').value=b.character_level||''; $('#fWorld').value=b.world_name||'';
    $('#fAvatar').outerHTML=avatar({name,image:b.character_image},'lg').replace('class="avatar lg"','class="avatar lg" id="fAvatar"');
    msg.textContent='✓ 불러왔습니다. (기본 정보는 게임 데이터 반영까지 평균 15분 지연될 수 있음)';
  }catch(e){ msg.textContent='조회 실패: '+e.message; }
}
function saveChar(){
  const name=$('#fName').value.trim(); if(!name){toast('이름을 입력하세요');markEmpty($('#fName')).focus();return;}
  const job=$('#fJob').value.trim(), world=$('#fWorld').value.trim(); const level=Math.max(1,Math.min(300,parseInt($('#fLevel').value)||0))||'';
  const isMain=$('#fMain').checked, accId=$('#fAcc').value||'';
  let c;
  if(editingId){ c=S.characters.find(x=>x.id===editingId); if(c.name!==name && !lookup){ c.ocid=''; c.image=''; delete c.exp; } Object.assign(c,{name,job,level,world}); toast('수정되었습니다'); }
  else{
    c={id:uid(),name,job,level,world,bosses:{},weekly:{},monthly:{},auto:{},sync:{}};
    S.characters.push(c); S.activeId=c.id; tab='boss'; editMode=false; bossFilter='weekly';
    toast('캐릭터 추가! 도는 보스를 선택하세요');
  }
  if(lookup){ c.ocid=lookup.ocid; c.image=lookup.image||''; c.sync={...c.sync,imgAt:Date.now()}; if(lookup.exp) c.exp=lookup.exp; }
  if((c.accId||'')!==accId){ c.accId=accId||undefined; c.sync={...c.sync,ok:undefined,msg:'',at:0}; }
  setMain(c,isMain);
  save(); closeCharModal(); syncTabs(); render();
}
function setMain(c,on){ if(on) S.characters.forEach(x=>x.isMain=(x===c)); else c.isMain=false; }
function deleteChar(){
  const c=S.characters.find(x=>x.id===editingId); if(!c) return;
  if(!confirm(`'${c.name}' 캐릭터를 삭제할까요?`)) return;
  S.characters=S.characters.filter(x=>x.id!==editingId);
  if(S.activeId===editingId) S.activeId=S.characters[0]?.id||null;
  save(); closeCharModal(); render(); toast('삭제되었습니다');
}

/* ---------- 계정 캐릭터 불러오기 ---------- */
let accChars=[], impAccId=null, impBusy=null;
/* 계정 캐릭터 불러오기: 모달을 바로 열고 GET /character/list 결과(목록·0명 안내·오류 코드)를 모달 안에 표시 */
/* ---------- '+ 추가' 통합 모달: API 키(계정) 관리 + 계정 캐릭터 목록에서 여러 명 선택 추가 ---------- */
const maskKey = k => !k ? '' : k.length<=10 ? '••••' : k.slice(0,5)+'••••'+k.slice(-4);
function linkedOf(a){ return S.characters.filter(c=>c.accId===a.id).length; }
const regOkHtml = n => `<span class="okc regok"><span class="okic" aria-hidden="true">✔</span> 등록 완료${n?` · ${n}캐릭 등록 중`:''}</span>`; // b216: 0캐릭이면 '· 0캐릭 등록 중' 안 씀
const accIsMain=a=>!!a.main||(!accounts().some(x=>x.main)&&accounts()[0]===a); // b235: 대표 계정 줄 = 로그아웃 버튼
function renderAccList(){
  const el=$('#accList'); if(!el) return;
  const accs=accounts();
  // b63: 키에 연결된(accId) 캐릭터 수만 — 수동 추가·키 없는 캐릭터는 제외
  const totalLinked=accs.reduce((s,a)=>s+(a.key?linkedOf(a):0),0); // b72: 키 없는 계정(숨긴 캐릭터)은 빼고
  const ht=$('#accKeyTotal'); if(ht){ ht.textContent=`(총 ${totalLinked}캐릭 등록 중)`; ht.hidden=!totalLinked; ht.closest('.addsec-h')?.toggleAttribute('hidden',!totalLinked); } // b216: 0캐릭이면 '🔑 넥슨 API 키 (총 0캐릭 등록 중)' 줄 통째로 숨김
  const shown=accs.filter(a=>a.key||a.main); // b74: 키 없는 부계정 칸(빈 칸)은 목록에 안 보임 — 데이터·캐릭터 연결은 유지, 같은 계정 키를 '+ 계정 추가'로 넣으면 그 칸에 다시 연결
  el.innerHTML=shown.length?shown.map(a=>{
    const linked=linkedOf(a);
    const stt=!a.key?'':a.status?.ok===false?`<span class="warnc" title="${esc(a.status.msg)}">⚠ 오류</span>`:regOkHtml(linked);
    return `<div class="accrow ${a.id===impAccId?'on':''}" ${a.key?`data-acctest="${a.id}" title="이 계정의 캐릭터 보기"`:''}><input class="pin acclbl" data-acclabel="${a.id}" value="${a.key?esc(a.label):''}" placeholder="계정 이름" maxlength="12" aria-label="계정 이름">
      <span class="accst">${stt}${quotaHtml(a.key,false)}</span>
      <span class="accbtns">${accIsMain(a)?`<button class="btn sm ghost acclogout" data-accdel="${a.id}" title="대표 계정 로그아웃 (부계정도 함께)">로그아웃</button>`:`<button class="btn sm plain danger" data-accdel="${a.id}" title="이 API 키 삭제">삭제</button>`}</span></div>`; // b74: 예비 키 줄 삭제
  }).join(''):'<div class="muted acc-empty">등록된 API 키가 없습니다. <b>+ 계정 추가</b>로 키를 넣으면 바로 그 계정의 캐릭터 목록이 나와요.</div>';
  $('#newAccLabel').placeholder='계정 이름'; // b72
  $('#accOpts').innerHTML=''; // (예전 '스케줄러 보스 자동 추가' 옵션 — 2026-10-10 삭제: 항상 켜짐)
}
const bkErr={};
const bkRow = (a,linked) => `<div class="bkrow" data-bkrow="${a.id}">${a.bk
  ? `<input class="pin acclbl" data-bklabel="${a.id}" value="${esc(a.bkLabel||a.label+' 예비')}" maxlength="14" aria-label="예비 키 이름"><span class="accst">${regOkHtml(linked??linkedOf(a))}${quotaHtml(a.bk)}${bkOn(a)?' <span class="muted tiny">오늘 사용 중</span>':''}</span><span class="accbtns"><button class="btn sm plain danger" data-bkdel="${a.id}" title="예비 키 삭제">삭제</button></span>`
  : `<input class="pin acclbl" id="bkLb-${a.id}" maxlength="14" placeholder="${esc(a.label)} 예비" aria-label="예비 키 이름"><input class="pin bkin" id="bkIn-${a.id}" type="password" autocomplete="off" spellcheck="false" placeholder="같은 넥슨 계정의 다른 API 키" aria-label="예비 API 키"><button class="btn sm plain" data-bkadd="${a.id}">등록</button>`}
  ${bkErr[a.id]?`<div class="bkerr" role="alert">${esc(bkErr[a.id])}</div>`:''}</div>`;
// 계정 id 목록: 같은 넥슨 계정인지 비교용 (키 값은 저장·표시하지 않음)
const acctIds = d => [...new Set((Array.isArray(d?.account_list)?d.account_list:[]).map(x=>String(x?.account_id||'')).filter(Boolean))].sort().join(',');
async function bkAdd(id){
  const a=accById(id), inp=$('#bkIn-'+id); if(!a||!inp) return; const k=inp.value.trim(); delete bkErr[id];
  if(!k){ bkErr[id]='예비 API 키를 붙여넣으세요'; return renderAccList(); }
  if(accounts().some(x=>x.key===k||x.bk===k)){ bkErr[id]='이미 등록된 키입니다 (기본 키와 다른 키를 넣으세요)'; return renderAccList(); }
  const btn=document.querySelector(`[data-bkadd="${id}"]`); if(btn){ btn.disabled=true; btn.textContent='확인 중…'; }
  try{
    const mine=acctIds(await nxRaw('/maplestory/v1/character/list',{},a.key).catch(e=>{ if(isQuotaErr(e)) return {account_list:(listCache[a.id]?.all||[]).map(x=>({account_id:x.account_id}))}; throw e; }));
    let theirs; try{ theirs=acctIds(await nxRaw('/maplestory/v1/character/list',{},k)); }catch(e){ throw new Error(isQuotaErr(e)?'예비 키도 지금 호출량 초과입니다. 잠시 후 다시 시도하세요':'넥슨이 이 예비 키를 거부했습니다 (키 확인)'); }
    if(!mine) throw new Error('기본 키의 계정을 확인하지 못했습니다. 잠시 후 다시 시도하세요');
    if(mine!==theirs) throw new Error('같은 넥슨 계정의 키가 아닙니다. 이 계정 주인의 키만 예비 키로 쓸 수 있어요');
    { const rej=await svKeyCheck(k); if(rej) throw new Error(rej); } // b64: 다른 데이터에 등록된 키면 저장 안 함
    a.bk=k; a.bkLabel=($('#bkLb-'+id)?.value||'').trim()||a.label+' 예비'; save(); render(); toast(`'${a.label}' 예비 키를 등록했습니다`);
    if(SV_ON&&svTok()&&gdMeta.on) svSyncSubKeys().catch(()=>{});
  }catch(e){ bkErr[id]=e.message; }
  renderAccList();
}
function bkDel(id){ const a=accById(id); if(!a) return; delete a.bk; delete a.bkLabel; delete bkErr[id]; const d=bkDays(); delete d[id]; localStorage.setItem(BK_DAY_KEY,JSON.stringify(d)); save(); renderAccList(); render(); if(SV_ON&&svTok()&&gdMeta.on) svSyncSubKeys().catch(()=>{}); }
document.addEventListener('click',e=>{ const t=e.target.closest('[data-rkpage]'); if(!t) return; const [k,n]=t.dataset.rkpage.split('|'); rankPage[k]=+n; render(); });
document.addEventListener('click',e=>{ const t=e.target.closest('[data-bkadd],[data-bkdel]'); if(!t) return; e.stopPropagation(); if(t.dataset.bkadd) bkAdd(t.dataset.bkadd); else bkDel(t.dataset.bkdel); },true);
document.addEventListener('change',e=>{ const id=e.target.dataset?.bklabel; if(!id) return; const a=accById(id); if(a){ a.bkLabel=e.target.value.trim()||a.label+' 예비'; save(); } });
document.addEventListener('keydown',e=>{ if(e.key==='Enter'&&e.target.classList?.contains('bkin')){ e.preventDefault(); bkAdd(e.target.id.slice(5)); } });
function openAdd(){ openImport(); }
/* b67: 서버 모드에서 로그인(세션) 전 = 캐릭터 추가 창에 '본계정 API 키 등록'만 (예전 입장 화면의 대표 키 로그인과 같은 일) */
const svNeedMain=()=>!!SV_ON&&!(svTok()&&gdMeta.on);
function svMainAttr(on){ // b71: 'Data based on NEXON Open API' — 등록 칸 밖, 창 아래
  let a=$('#svMainAttr'); if(!on){ a?.remove(); return; }
  if(!a){ a=document.createElement('div'); a.id='svMainAttr'; a.className='svmattrib muted'; a.textContent='Data based on NEXON Open API'; }
  $('#svMainSec')?.insertAdjacentElement('afterend',a);
}
/* b209: API 키 발급 순서 안내(사용자 문구 그대로) — 'API 발급 : 링크' 바로 아래. ☞ 줄 = 그 단계 아래 들여쓰기. 이 링크가 있는 곳은 이 창(로그인 전 본계정 키 등록) 하나뿐 */
const API_GUIDE=[['①','링크 클릭 후 넥슨 로그인'],['②','이용약관 스크롤 끝까지 내린 후 약관 동의'],['③','어떤 게임으로 애플리케이션을 만드실 건가요?','메이플스토리'],
  ['④','아직 개발 단계인가요? 아니면 서비스 출시 단계인가요?','개발 단계'],['⑤','출시할 서비스명을 설정해주세요','메보기'],['⑥',"마이페이지 - 애플리케이션 목록 - 서비스명 '메보기' 클릭"],['⑦','첫번째 API key 옆 복사버튼 누른 후 API키 입력란에 Ctrl+V']];
// 좁은 화면(휴대폰)에서 안내 줄이 넘치면 줄바꿈 대신 글자를 조금씩 줄임(12px → 최소 9px)
function fitApiGuide(){ const ol=document.querySelector('#svMainSec .apiguide'); if(!ol) return; ol.style.fontSize=''; let f=12; while(ol.scrollWidth>ol.clientWidth+1&&f>9){ f-=.5; ol.style.fontSize=f+'px'; } }
addEventListener('resize',()=>fitApiGuide());
function apiGuideHtml(){ return `<ol class="apiguide" aria-label="API 키 발급 방법">${API_GUIDE.map(([n,t,a])=>`<li><span class="agn">${n}</span><span class="agt">${esc(t)}</span>${a?`<div class="aga">☞ ${esc(a)}</div>`:''}</li>`).join('')}</ol>`; }
function svMainRender(){
  const modal=$('#importModal'); if(!modal) return;
  const on=svNeedMain()&&modal.classList.contains('show'); modal.querySelector('.addm')?.classList.toggle('svmain',on);
  let sec=$('#svMainSec'); if(!on){ sec?.remove(); svMainAttr(false); return; }
  if(!sec){ sec=document.createElement('section'); sec.className='addsec'; sec.id='svMainSec'; $('#addTitle').insertAdjacentElement('afterend',sec); }
  const busy=gd.state==='connecting', err=gd.svErr, soft=err===SV_RELOGIN||err===SV_NEED_LOGIN, v=$('#svMainKey')?.value||'';
  const pd=svPend();
  if(pd){ // b68: 가입 승인 대기 — 데이터는 아직 서버에 저장되지 않음
    sec.innerHTML=`<div class="addsec-h"><b>⏳ 승인 대기 중</b></div>
    <div class="svpend"><div>대표 캐릭터: <b>${esc(pd.name||'(이름 없음)')}</b>${pd.world?` · ${esc(pd.world)}`:''}${pd.level?` · Lv.${pd.level}`:''}</div>
      <div class="muted tiny">요청: ${pd.requestedAt?hm(pd.requestedAt):'-'} · 관리자가 승인하면 [승인 확인]을 누르거나 페이지를 다시 열면 바로 시작돼요. 승인 전에는 데이터가 서버에 저장되지 않아요.</div></div>
    <div class="accst svmst" id="svMainSt">${err?`<span class="keyrej${soft?' soft':''}" role="alert">${esc(err)}</span>`:''}</div>
    <div class="toolbar"><button class="btn sm" id="svPendCheck"${busy?' disabled':''}>${busy?'확인 중…':'승인 확인'}</button><button class="btn sm ghost" id="svPendCancel"${busy?' disabled':''}>다른 키로 등록</button></div>
    <div class="svmattrib muted">Data based on NEXON Open API</div>`;
    svMainAttr(false); return;
  }
  // b71: 처음 등록 칸 = API 키 입력 하나 + [등록] 만 (안내 문구 없음). 오류·부계정 경고는 생길 때만 아래 줄에. NEXON 표기는 칸 밖(창 아래)
  sec.innerHTML=`<div class="accrow svmrow"><input id="svMainKey" class="pin" type="password" autocomplete="off" spellcheck="false" placeholder="API키 입력" aria-label="API키 입력"${busy?' disabled':''}><button class="btn sm" id="svMainBtn"${busy?' disabled':''}>${busy?'확인 중…':'등록'}</button></div>
    <div class="svmapi tiny muted">API 발급 : <a href="https://openapi.nexon.com/ko/my-application/create-app/" target="_blank" rel="noopener">https://openapi.nexon.com/ko/my-application/create-app/</a></div>${apiGuideHtml()}
    ${err?`<div class="accst svmst" id="svMainSt"><span class="keyrej${soft?' soft':''}" role="alert">${esc(err)}</span></div>`:'<div class="accst svmst" id="svMainSt" hidden></div>'}`;
  svMainAttr(true); fitApiGuide();
  const inp=$('#svMainKey'); if(inp){ inp.value=v; if(err==='API 키를 넣어 주세요'&&!v) markEmpty(inp); if(!busy) setTimeout(()=>inp.focus(),0); }
}
async function openImport(accId){
  const modal=$('#importModal'), wasOpen=modal.classList.contains('show');
  if(svNeedMain()){ modal.classList.add('show'); impAccId=null; accChars=[]; svMainRender(); return; }
  svMainRender(); // (로그인 상태면 본계정 등록 칸 제거)
  const usable=accounts().filter(a=>a.key);
  let a=(accById(accId)?.key&&accById(accId))||usable.find(x=>x.id===impAccId)||usable[0];
  modal.classList.add('show');
  if(!a){ impAccId=null; accChars=[]; renderAccList(); $('#impSec').classList.add('hidden'); accAddShow(true); return; } // b74: 키가 하나도 없으면(구글 드라이브 모드 등) 추가 줄을 바로 보여 줌
  $('#impSec').classList.remove('hidden');
  if(impBusy===a.id) return; impBusy=a.id; impAccId=a.id; renderAccList();
  $('#impTitle').textContent=`'${a.label}' 계정 캐릭터`;
  accChars=[]; if(!wasOpen){ $('#impMin').value=''; $('#impQ').value=''; } $('#impWorld').innerHTML='<option value="">모든 월드</option>';
  $('#impList').innerHTML=''; $('#impCount').textContent='';
  const msg=$('#impMsg'); msg.className='impmsg'; msg.innerHTML=`<span class="spin"></span> '${esc(a.label)}' 계정의 캐릭터 목록을 불러오는 중…`;
  try{
    const all=await listAccount(a); if(impAccId!==a.id) return;
    const ra=keyRelink(a,all); if(ra){ a=ra; impAccId=ra.id; impBusy=ra.id; } // b64: 키 없는 예전 계정 칸에 다시 연결
    const n=assignFromList(a,all); save();
    if(keySyncPend&&(keySyncPend===a.id||ra)){ keySyncPend=null; if(S.characters.some(c=>c.accId===a.id&&charShown(c))) setTimeout(keySync,0); }
    accChars=all.map(x=>({...x,accId:a.id})).sort((x,y)=>y.character_level-x.character_level||x.character_name.localeCompare(y.character_name));
    const worlds=[...new Set(accChars.map(x=>x.world_name).filter(Boolean))];
    $('#impWorld').innerHTML=`<option value="">모든 월드</option>`+worlds.map(w=>`<option>${esc(w)}</option>`).join('');
    const nAcc=listCache[a.id]?.accounts||0;
    if(!all.length){ msg.className='impmsg warn'; msg.innerHTML=emptyHtml(a)+`<div class="toolbar"><button class="btn sm plain" id="impRetry">다시 불러오기</button></div>`; }
    else { msg.className='impmsg ok'; msg.innerHTML=''; msg.className='impmsg'; }
    renderImportList(); render();
  }catch(e){
    if(impAccId!==a.id) return;
    a.status={ok:false,msg:e.message,at:Date.now()}; save(); render();
    msg.className='impmsg err'; msg.innerHTML=errHtml(e,a)+`<div class="toolbar"><button class="btn sm plain" id="impRetry">다시 불러오기</button></div>`;
  }finally{ if(impBusy===a.id) impBusy=null; }
}
// b64: 새로 추가한 키의 캐릭터 목록(ocid)이 '키 없음' 상태의 예전 계정 칸에 연결된 캐릭터와 겹치면 → 그 칸에 키를 넣고 새 칸은 지움
//   (키 초기화 뒤 다시 등록할 때 캐릭터 연결(accId)·이름·순서가 그대로 유지되게. 캐릭터 데이터는 건드리지 않음)
function keyRelink(a,all){
  if(!a?.key) return null; const ids=new Set((all||[]).map(x=>x.ocid).filter(Boolean)); if(!ids.size) return null;
  { // b219: 지운(goneAccs) 계정 칸에 묶여 숨겨진 캐릭터도 같은 넥슨 캐릭터(ocid)면 이 키에 다시 연결 → 기록과 함께 다시 보임 (예전엔 칸이 지워져 영영 숨겨짐)
    let rv=0; S.characters.forEach(c=>{ if(c.accId&&goneAcc(c.accId)&&c.ocid&&ids.has(c.ocid)){ syncTimerMove(c.accId,a.id); c.accId=a.id; rv++; } }); // b235: 동기화 타이머도 이어감
    if(rv){ const used=new Set(S.characters.map(c=>c.accId)); S.settings.goneAccs=(S.settings.goneAccs||[]).filter(id=>used.has(id)); save(); } }
  const o=accounts().find(x=>x!==a&&!x.key&&a.ah&&x.ah===a.ah)||accounts().find(x=>x!==a&&!x.key&&S.characters.some(c=>c.accId===x.id&&c.ocid&&ids.has(c.ocid))); // b95: 넥슨 계정 해시(ah) 우선
  if(!o) return null;
  if(a.main){ // b72: 본계정(1번 줄)은 그대로 두고, 같은 캐릭터가 붙은 키 없는 예전 칸을 본계정으로 합침 (칸 삭제, 캐릭터 데이터 유지)
    S.characters.forEach(c=>{ if(c.accId===o.id) c.accId=a.id; }); if(o.bk&&!a.bk&&o.bk!==a.key){ a.bk=o.bk; if(o.bkLabel) a.bkLabel=o.bkLabel; }
    S.settings.accounts=accounts().filter(x=>x!==o); save(); return a; }
  o.key=a.key; if(a.bk&&!o.bk){ o.bk=a.bk; if(a.bkLabel) o.bkLabel=a.bkLabel; } if(a.ah&&!o.ah) o.ah=a.ah; delete o.status;
  if(listCache[a.id]){ listCache[o.id]=listCache[a.id]; delete listCache[a.id]; }
  S.settings.accounts=accounts().filter(x=>x!==a); save(); toast(`'${o.label}' 계정에 키를 다시 연결했습니다`); return o;
}
// b64: 서버 모드 — 추가하려는 키가 다른 데이터(캐릭터가 있는)에 이미 등록된 넥슨 계정/부계정·예비 키면 저장하지 않고 빨간 글만
let accRej=null, accAdding=false;
function accRejShow(){
  let d=$('#accRej'); if(!accRej){ d?.remove(); return; }
  if(!d){ d=document.createElement('div'); d.id='accRej'; $('#accList')?.insertAdjacentElement('afterend',d); }
  d.innerHTML=`<div class="accrow accrej"><input class="pin acclbl" value="${esc(accRej.label)}" disabled aria-label="계정 이름"><span class="accst"><span class="keyrej" role="alert" style="color:#ff5a5a;font-weight:600;font-size:.9rem">${esc(accRej.msg)}</span></span></div>`;
}
async function svKeyCheck(k){ // '' = 통과 (서버 모드가 아니거나, 예전 Worker(404)·넥슨 오류 등은 예전 흐름대로 계속)
  if(!SV_ON||!svTok()||!gdMeta.on) return '';
  try{ await svFetch('/api/keycheck',{method:'POST',body:{key:k}}); return ''; }
  catch(e){ return e.code==='sub_key'?'이미 등록된 부계정 API입니다.':''; }
}
async function addAccount(){
  const k=$('#newAccKey').value.trim();
  { const lb=$('#newAccLabel').value.trim()||(accounts().length?'':'본계정'); // b75: 빈 칸 전부 빨간 테두리 (이름 → 키 순서로 안내)
    if(!lb||!k){ newAccLblErr(!lb); markEmpty($('#newAccLabel'),!lb); markEmpty($('#newAccKey'),!k); if(!lb) $('#newAccLabel').focus(); else { toast('API 키를 붙여넣으세요'); $('#newAccKey').focus(); } return; } }
  const dup=accounts().find(a=>a.key===k); if(dup){ toast(`이미 '${dup.label}'(으)로 등록된 키입니다`); openImport(dup.id); return; }
  const n=accounts().length, label=$('#newAccLabel').value.trim()||(n?'':'본계정');
  // b72: 부계정 키는 이름을 꼭 입력 (자동 이름 없음) — 비어 있으면 이름 칸 바로 아래 빨간 글, 등록 안 함
  if(accAdding) return; accAdding=true; accRej=null; accRejShow();
  let rej=''; try{ rej=await svKeyCheck(k); }finally{ accAdding=false; }
  if(rej){ accRej={label,msg:rej}; accRejShow(); $('#newAccKey').value=''; return; }
  const a={id:uid(),label,key:k}; accounts().push(a); save(); keySyncPend=a.id; // b218: 목록을 받은 뒤(openImport) 이 키에 연결된 캐릭터가 있으면 1번 동기화
  $('#newAccKey').value=''; $('#newAccLabel').value=''; accAddShow(false);
  openImport(a.id); render();
}
function newAccLblErr(on){ let d=$('#newAccLblErr');
  if(!on){ d?.remove(); markEmpty($('#newAccLabel'),false); return; }
  if(!d){ d=document.createElement('div'); d.id='newAccLblErr'; d.className='lblerr'; d.setAttribute('role','alert'); d.textContent='계정 이름을 입력해주세요'; $('.accadd')?.insertAdjacentElement('afterend',d); }
}
document.addEventListener('input',e=>{ if(e.target.id==='newAccLabel'&&e.target.value.trim()) newAccLblErr(false); });
// b74: 부계정 추가 줄은 '+ 계정 추가'를 눌렀을 때만 (이름·키·등록·취소). 취소/등록 완료/창 닫기 → 지우고 숨김
function accAddShow(on){ const r=$('#accAddRow'), b=$('#accAddOpen'); if(!r) return;
  r.hidden=!on; if(b) b.hidden=!!on;
  if(on) setTimeout(()=>$('#newAccLabel')?.focus(),0); else { $('#newAccLabel').value=''; $('#newAccKey').value=''; newAccLblErr(false); accRej=null; accRejShow(); }
}
function closeImport(){ accAddShow(false); newAccLblErr(false); $('#importModal').classList.remove('show'); accRej=null; accRejShow(); svMainRender(); if(SV_ON&&gd.svErr&&!svTok()) gd.svErr=''; }
function renderImportList(){
  const min=parseInt($('#impMin').value)||0, w=$('#impWorld').value, q=normName($('#impQ').value);
  const have=new Set(S.characters.map(c=>c.ocid).filter(Boolean)), haveName=new Set(S.characters.map(c=>c.name));
  const multi=(listCache[impAccId]?.accounts||0)>1;
  const list=accChars.filter(x=>x.character_level>=min&&(!w||x.world_name===w)&&(!q||normName(x.character_name+x.character_class).includes(q)));
  $('#impCount').textContent=accChars.length?(list.length===accChars.length?`${accChars.length}명`:`${accChars.length}명 중 ${list.length}명 표시`):'';
  if(!accChars.length){ $('#impList').innerHTML=''; return; }
  $('#impList').innerHTML=list.length?list.map(x=>{const dup=(x.ocid&&have.has(x.ocid))||haveName.has(x.character_name);return `<label class="imp-item ${dup?'dis':''}"><input type="checkbox" value="${esc(x.ocid)}" ${dup?'disabled':''}>
    <div class="grow" style="flex:1"><b>${esc(x.character_name)}</b> <span class="muted">Lv.${x.character_level} · ${esc(x.character_class)}</span></div><span class="muted">${esc(x.world_name)}${dup?' · 추가됨':''}</span></label>`}).join('')
    :`<div class="muted" style="padding:12px">필터 조건에 맞는 캐릭터가 없습니다. <button class="btn sm plain" id="impClear">필터 초기화</button></div>`;
}
function doImport(){
  const ids=[...document.querySelectorAll('#impList input:checked')].map(i=>i.value);
  if(!ids.length){toast('캐릭터를 선택하세요');return;}
  const hadMain=S.characters.some(c=>c.isMain);
  const picked=accChars.filter(x=>ids.includes(x.ocid));
  picked.forEach(x=>S.characters.push({id:uid(),name:x.character_name,job:x.character_class,level:x.character_level,world:x.world_name,ocid:x.ocid,accId:x.accId,image:'',isMain:false,bosses:{},weekly:{},monthly:{},auto:{},sync:{}}));
  if(!hadMain){ const top=S.characters.slice().sort((a,b)=>(b.level||0)-(a.level||0))[0]; if(top) top.isMain=true; }
  if(!S.activeId||!activeChar()) S.activeId=(S.characters.find(c=>c.isMain)||S.characters[0]).id;
  save(); closeImport(); render(); toast(`${picked.length}명 추가 — 동기화를 시작합니다`);
  syncAll();
}

/* =====================================================================
 *  결정석 가격 자동 갱신 — 사이트의 prices.json (GitHub Actions 가 매일 공식 업데이트 공지에서 가격표를 읽어 갱신)
 *  - 가격은 직접 수정할 수 없고, 기본 가격(PRICE_CONFIG)을 공식 값으로 바꿔서 사용
 *  - 적용일(effective)이 아직 안 된 항목은 그날이 될 때까지 기존 값 유지
 *  - 마지막으로 받은 prices.json 은 이 브라우저에 보관 (다음 접속 때 바로 적용, 드라이브에는 넣지 않음)
 * ===================================================================== */
const PRICES_CACHE_KEY='mapleBossTracker.officialPrices';
let officialInfo=null; // {checkedAt, source:{url,title,date}, applied, pending:[{key,effective,price}]}
function parseBossLabel(label){
  const m=/^(.*?)\s*[(（]\s*(.+?)\s*[)）]\s*$/.exec(String(label||'').trim()); if(!m) return null;
  const b=matchBoss(m[1]), d=normDiff(m[2]); if(!b||!d||!b.diffs.includes(d)) return null;
  return {b,d};
}
// 테섭 예정 가격으로 잠깐 바꿔 계산 (예정 가격이 없으면 null)
function withUpcoming(fn){ const up=officialInfo&&officialInfo.upcoming; if(!up||!Object.keys(up).length) return null; const keep={};
  for(const k in up){ keep[k]=PRICE_CONFIG[k]; PRICE_CONFIG[k]=up[k]; } try{ return fn(); } finally{ for(const k in keep) PRICE_CONFIG[k]=keep[k]; } }
// b252: 사용자 승인 내장값 — 공식/자동 수집 가격보다 우선. 다른 공식 값이 오면 덮지 않고 priceConflicts 에 기록.
const BUILTIN_PRICE_LOCK={limbo_extreme:7500000000, baldrix_extreme:9600000000};
const priceConflicts=[];
const noteConflict=(k,v,src)=>{ if(!priceConflicts.some(c=>c.key===k&&c.official===v)){ priceConflicts.push({key:k,builtin:BUILTIN_PRICE_LOCK[k],official:v,src}); try{console.info('[price-conflict]',k,'내장',BUILTIN_PRICE_LOCK[k],'공식',v,src||'');}catch(e){} } };
function applyOfficialPrices(pj){
  if(!pj||!Array.isArray(pj.rows)) return false;
  const today=dayId(); let changed=false, applied=0; const pending=[];
  for(const r of pj.rows){ const m=parseBossLabel(r.boss); const v=Math.round(+r.new); if(!m||!(v>0)) continue;
    const k=priceKey(m.b,m.d);
    if(r.effective && r.effective>today){ pending.push({key:k,effective:r.effective,price:v}); continue; } // 적용일 전에는 기존 값 유지
    if(k in BUILTIN_PRICE_LOCK){ if(v!==BUILTIN_PRICE_LOCK[k]) noteConflict(k,v,(pj.source||{}).url); continue; }
    if(PRICE_CONFIG[k]!==v){ PRICE_CONFIG[k]=v; changed=true; } applied++;
  }
  // 테섭 예정 가격 (pj.upcoming): 실서버 가격은 그대로, 다른 값만 '테섭 예정 → N' 표시
  const upcoming={}; for(const r of (pj.upcoming&&pj.upcoming.rows)||[]){ const m=parseBossLabel(r.boss); const v=Math.round(+r.new); if(m&&v>0){ const k=priceKey(m.b,m.d); if(PRICE_CONFIG[k]!==v) upcoming[k]=v; } }
  officialInfo={checkedAt:pj.checkedAt||'', changedAt:pj.changedAt||'', source:pj.source||{}, applied, pending, upcoming, upSource:(pj.upcoming&&pj.upcoming.source)||null, upAt:(pj.upcoming&&pj.upcoming.detectedAt)||''};
  return changed;
}
function loadOfficialPrices(){
  try{ const c=JSON.parse(localStorage.getItem(PRICES_CACHE_KEY)||'null'); if(c) applyOfficialPrices(prMerge(c,srvPr())); }catch(e){}
  if(!/^https?:$/.test(location.protocol)) return; // 파일로 연 경우: 내장 기본값 사용
  fetchOfficialPrices();
}
// b171: 하루 단위(?d=날짜) 주소 대신 5분 단위 + no-cache → 낮에 가격·확인 시각이 바뀌어도 새로 받음. 화면이 보일 때 5분마다·탭 복귀 때 다시 확인, 내용이 같으면 다시 그리지 않음
let pricesSig='';
function fetchOfficialPrices(){
  if(!/^https?:$/.test(location.protocol)) return;
  fetch(`./prices.json?t=${Math.floor(Date.now()/300000)}`,{cache:'no-cache'}).then(r=>r.ok?r.json():null).then(pj=>{
    if(!pj||!Array.isArray(pj.rows)||!pj.rows.length) return;
    const sig=JSON.stringify(pj); if(sig===pricesSig) return; pricesSig=sig;
    localStorage.setItem(PRICES_CACHE_KEY,sig);
    if(applyOfficialPrices(prMerge(pj,srvPr()))) save(); render();
  }).catch(()=>{});
}
setInterval(()=>{ if(document.visibilityState==='visible') fetchOfficialPrices(); },300000);
/* b193: Worker(매 1분 공지 감시)가 새 업데이트 공지에서 읽은 가격표(feed.prices) — prices.json 보다 공지 id 가 새것이면 줄을 바꾸고,
 * 아니면 마지막 확인(checkedAt)만 늦은 쪽으로. 테섭 예정(upcoming)은 같은 값이 된 줄을 지움(upcoming.reconcile 과 같음) */
let srvPrSig='';
function srvPr(){ try{ return JSON.parse(localStorage.getItem('mapleBossTracker.srvPrices')||'null'); }catch(e){ return null; } }
function prPostId(u){ return +((String(u||'').match(/\/(\d+)\/?$/)||[])[1]||0); }
function prMerge(pj,sp){ if(!pj||!sp) return pj; const o={...pj};
  if(Array.isArray(sp.rows)&&sp.rows.length>=20&&+sp.id>prPostId(pj.source&&pj.source.url)){ o.rows=sp.rows; o.notes=sp.notes||[]; o.source=sp.source||o.source; if(sp.changedAt) o.changedAt=sp.changedAt;
    if(o.upcoming&&Array.isArray(o.upcoming.rows)){ const k=b=>String(b||'').replace(/\s+/g,''); const live=new Map(o.rows.map(r=>[k(r.boss),r.new])); const keep=o.upcoming.rows.filter(r=>live.get(k(r.boss))!==r.new); o.upcoming=keep.length?{...o.upcoming,rows:keep}:undefined; } }
  if(sp.checkedAt&&(!o.checkedAt||Date.parse(sp.checkedAt)>Date.parse(o.checkedAt))) o.checkedAt=sp.checkedAt;
  return o; }
function srvPricesApply(sp){ if(!sp) return; const sig=JSON.stringify(sp); if(sig===srvPrSig) return; srvPrSig=sig; try{ localStorage.setItem('mapleBossTracker.srvPrices',sig); }catch(e){}
  let pj=null; try{ pj=JSON.parse(localStorage.getItem(PRICES_CACHE_KEY)||'null'); }catch(e){} if(!pj) return;
  if(applyOfficialPrices(prMerge(pj,sp))) save(); render(); }
document.addEventListener('visibilitychange',()=>{ if(document.visibilityState==='visible') fetchOfficialPrices(); });

/* =====================================================================
 *  동기화 서버 (Cloudflare Workers + D1, server/ 폴더) — 기능 플래그 (2026-10-10, 아직 꺼 둠)
 *  SYNC_API_URL 이 비어 있으면 지금처럼 구글 드라이브 동기화. 값이 있으면(또는 테스트용 localStorage 'mapleBossTracker.syncApi')
 *  같은 동기화 흐름(gdConnect/gdSync 3-way 병합/gdPush/gdPull)을 그대로 쓰고 저장소만 서버로 바뀜:
 *   - 로그인 = 넥슨 Open API 키 (서버가 넥슨에 확인 → 계정 식별, 원본 키는 서버에 저장 안 함) → 세션 토큰(localStorage)
 *   - 저장 = PUT /api/state (rev 로 동시 저장 감지, 409 → 받아온 내용과 3-way 병합 후 다시 저장). API 키는 보내지 않음(backupData(false))
 *   - 다른 기기에 내려받을 때 키: 로그인에 쓴 키만 자동으로 채움(계정의 ah = 서버가 준 계정 해시로 짝지음), 부계정 키는 대표 키(HKDF)로 AES-GCM 암호화해 서버 keyvault 에 보관 → 대표 키로 로그인하면 복원 (server/worker.js)
 *   - 옮기기: 처음 로그인 때 서버가 비어 있으면 이 PC 데이터를 올림 / '구글 드라이브에서 가져오기' 버튼(한 번, 클릭 시 구글 로그인)
 * ===================================================================== */
// b216: 구글 로그인(드라이브 동기화) 폐지 — 실제 주소(bossmaple.pages.dev · ggoolzip-wq.github.io 등)는 전부 서버 동기화.
//   예전엔 SYNC_HOSTS=['bossmaple.pages.dev'] 만 서버 모드라 github.io 로 열면 드라이브 모드 → 헤더에 '☁ 구글 로그인' 이 떴음.
//   드라이브 코드는 로컬 테스트(localhost·127.0.0.1·file://)에서만 남음(예전 테스트용).
const SYNC_LOCAL = /^(localhost|127\.0\.0\.1|)$/.test(location.hostname);
const SYNC_API_URL = SYNC_LOCAL ? '' : 'https://ggoolzip-sync.bossmaple.workers.dev';
const SYNC_TEST_URL = 'https://ggoolzip-sync.bossmaple.workers.dev'; // 배포한 서버 주소 — 주소 뒤에 ?sync=test 를 붙여 열면 이 브라우저만 서버 모드로 미리 써 보기, ?sync=off 로 되돌림
const SV_ON = (()=>{ let u=SYNC_API_URL;
  try{
    const q=new URLSearchParams(location.search).get('sync');
    if(q==='test'&&SYNC_TEST_URL) localStorage.setItem('mapleBossTracker.syncApi',SYNC_TEST_URL);
    if(q==='off') localStorage.removeItem('mapleBossTracker.syncApi');
    if(q){ const url=new URL(location.href); url.searchParams.delete('sync'); history.replaceState(null,'',url.pathname+url.search+url.hash); }
    u=localStorage.getItem('mapleBossTracker.syncApi')||u;
  }catch(e){} return String(u||'').replace(/\/+$/,''); })();
const SV_TOKEN_KEY='mapleBossTracker.svToken', SV_DEVICE_KEY='mapleBossTracker.svDevice', SV_SUBSIG_KEY='mapleBossTracker.svSubSig', SV_USER_KEY='mapleBossTracker.svUser'; // svUser = 이 기기에서 마지막으로 로그인한 서버 사용자 (다른 사용자로 로그인하면 이 PC 데이터를 올리지 않고 비움) // svDevice = 초대 비밀번호를 통과한 기기 표 (로그아웃해도 유지)
try{ if((localStorage.getItem(SV_SUBSIG_KEY)||'').startsWith('[')) localStorage.removeItem(SV_SUBSIG_KEY); }catch(e){} // b95: 예전 서명(키 원본 포함) 지움
// (b67: svDev — 초대 비밀번호 기기 표 — 더 이상 쓰지 않음. 예전 기기의 mapleBossTracker.svDevice 값은 남아 있어도 무시)
const svTok=()=>{ try{ return localStorage.getItem(SV_TOKEN_KEY)||''; }catch(e){ return ''; } };
const SV_PEND_KEY='mapleBossTracker.svPending', SV_ADMIN_KEY='mapleBossTracker.svAdmin'; // b68: 승인 대기 중인 본계정 키 요청(이 기기) · 관리자 여부
const svPend=()=>{ try{ return JSON.parse(localStorage.getItem(SV_PEND_KEY)||'null'); }catch(e){ return null; } };
const svIsAdmin=()=>SV_ON&&!!svTok()&&localStorage.getItem(SV_ADMIN_KEY)==='1';
const SV_RELOGIN='로그인이 만료되었어요 — 캐릭터 추가(+ 추가)에서 본계정 API 키로 다시 로그인해 주세요 (데이터는 서버와 이 PC에 그대로 있어요)';
const SV_VAULT_KEY='mapleBossTracker.svVault', SV_KEYERR_KEY='mapleBossTracker.svKeyErr'; // b62: 이 기기 로그인 때 금고 상태(open|none|locked) · 마지막 키 보관 오류
const SV_NEED_LOGIN='로그인이 필요해요 — 캐릭터 추가(+ 추가)에서 본계정 API 키를 등록하면 이어서 동기화돼요 (바꾼 내용은 이 PC에 그대로 있어요)';
let svGen=0; // b69: 로그아웃·초기화 때마다 +1 → 그 전에 시작한 서버 요청의 결과는 버림 (로그아웃 뒤 늦게 온 응답이 데이터를 되살리지 않게)
async function svFetch(path,opt={}){
  const tok=svTok(); if(!tok&&!opt.noAuth) throw Object.assign(new Error(SV_NEED_LOGIN),{type:'interaction_required'});
  const gen=svGen; let r;
  try{ r=await fetch(SV_ON+path,{method:opt.method||'GET',keepalive:!!opt.keepalive,headers:{'Content-Type':'application/json',...(opt.noAuth?{}:{Authorization:'Bearer '+tok})},body:opt.body===undefined?undefined:JSON.stringify(opt.body)}); }
  catch(e){ throw Object.assign(new Error('동기화 서버에 연결하지 못했습니다 (인터넷 연결 확인)'),{type:'network'}); }
  let b=null; try{ b=await r.json(); }catch(e){}
  if(gen!==svGen&&!opt.noGen) throw Object.assign(new Error('로그아웃되어 취소됨'),{type:'aborted'});
  // b69: 세션 없음·만료(401) / 차단·거절(403) → 이 PC 의 앱 데이터 전부 지우고 처음 온 사람 상태 (공용 PC). 서버 데이터는 그대로
  if(r.status===401&&!opt.noAuth){ svWipeAll({keepPending:true,broadcast:true}); gd.svErr=SV_RELOGIN; setTimeout(()=>{ gdRender(); if($('#importModal')?.classList.contains('show')) openImport(); },0); throw Object.assign(new Error(SV_NEED_LOGIN),{type:'interaction_required'}); }
  if(r.status===403&&!opt.noAuth&&b&&(b.error==='blocked'||b.error==='rejected'||b.error==='pending')){ svWipeAll({broadcast:true}); gd.svErr=b.message; setTimeout(()=>gdRender(),0); throw Object.assign(new Error(b.message),{type:'interaction_required',code:b.error}); } // b68: 차단·거절
  if(r.status===409&&opt.allow409) return {conflict:true,...b};
  if(!r.ok) throw Object.assign(new Error((b&&b.message)||`동기화 서버 오류 (HTTP ${r.status})`),{status:r.status,code:b&&b.error});
  return b;
}
const svRemote=b=>({app:'maple-boss-tracker',format:1,updatedAt:+b.updatedAt||0,withKeys:true,rev:+b.rev||0,data:b.data}); // 서버에는 키가 원래 없음(withKeys: 다시 저장할 필요 없음 표시)

/* =====================================================================
 *  구글 드라이브 동기화 — Google Identity Services(토큰 모델) + Drive REST v3, 범위 drive.appdata
 *  (내 드라이브의 숨겨진 '앱 데이터' 폴더에 maple-boss-tracker.json 하나만 저장. 다른 파일은 보거나 건드리지 않음)
 * ===================================================================== */
const GD={ SCOPE:'https://www.googleapis.com/auth/drive.appdata', FILE:'maple-boss-tracker.json',
  META_KEY:SV_ON?'mapleBossTracker.svmeta':'mapleBossTracker.gdrive', TOKEN_KEY:'mapleBossTracker.gtoken',
  API:'https://www.googleapis.com/drive/v3', UP:'https://www.googleapis.com/upload/drive/v3',
  ONLINE:'https://ggoolzip-wq.github.io/', DEBOUNCE:5000 };
const gcid=()=>GOOGLE_CLIENT_ID||window.__MBT_GCID||'';
const gdOriginOk=()=>location.protocol==='https:'||/^(localhost|127\.0\.0\.1)$/.test(location.hostname);
const driveUsable=()=>!!gcid()&&gdOriginOk();
const gdUsable=()=>SV_ON?true:driveUsable();
let gd={state:'off',msg:'',token:null,exp:0,ia:false,fileId:null,timer:null,busy:false,again:false,client:null,onTok:null,onErr:null,pending:null};
let gdMeta=(()=>{ // 서버 모드: rev(마지막으로 맞춘 서버 저장 번호)도 보관
   try{ return JSON.parse(localStorage.getItem(GD.META_KEY))||{}; }catch(e){ return {}; } })(); // {on, base(이 PC updatedAt), rU(드라이브 updatedAt), fileId, lastSave, lastLoad} — 맞춘 시점 내용은 GD_BASE_KEY
const gdSaveMeta=()=>localStorage.setItem(GD.META_KEY,JSON.stringify(gdMeta));
try{ const t=JSON.parse(sessionStorage.getItem(GD.TOKEN_KEY)||'null'); if(t&&t.e>Date.now()+60e3){ gd.token=t.t; gd.exp=t.e; } }catch(e){}
const gdLocalDirty=()=>gdMeta.on && (S.updatedAt||0)!==(gdMeta.base||0);
const gdTime=t=>t?`${hm(t)}`:'없음';

function gdSet(state,msg){ gd.state=state; gd.msg=msg||''; gdRender(); }
function gdRender(){
  const b=$('#gBtn'); if(b){
    const L={off:'☁ 구글 로그인',connecting:'☁ 연결 중…',saving:'☁ 저장 중…',reconnect:'☁ 다시 연결',conflict:'☁ 선택 필요',error:'☁ 동기화 오류',
      on: gd.timer||gdLocalDirty() ? '☁ 저장 대기' : (gdMeta.lastSave||gdMeta.lastLoad ? `☁ ${hm(Math.max(gdMeta.lastSave||0,gdMeta.lastLoad||0)).split(' ')[1]} 저장됨` : '☁ 동기화됨')};
    if(SV_ON){ L.off=svPend()&&!svTok()?'⏳ 승인 대기 중':'☁ 로그인'; L.reconnect='☁ 다시 로그인'; }
    b.textContent=SV_ON?(L[gd.state]||'☁ 동기화'):!gcid()?'☁ 구글':!gdOriginOk()?'☁ 구글 (온라인 전용)':(L[gd.state]||'☁ 구글'); b.classList.toggle('warn',['reconnect','conflict','error'].includes(gd.state));
    b.title=gd.msg||(SV_ON?'동기화 (넥슨 API 키로 로그인)':'구글 드라이브 동기화');
    // 서버 모드 로그인 중: 헤더는 [로그아웃]만 (저장은 뒤에서 조용히). 저장 실패만 작은 경고로 표시
    const svIn=SV_ON&&!!svTok()&&gdMeta.on&&gd.state!=='conflict';
    if(svIn){ b.textContent='로그아웃'; b.classList.remove('warn'); b.title='로그아웃 (이 PC의 데이터는 지워지고 서버에 남아요)'; b.setAttribute('aria-haspopup','false'); }
    else b.setAttribute('aria-haspopup','true');
    b.hidden=SV_ON&&!svTok(); // zosu-ui: 로그인 전(서버 모드, 세션 없음) 첫 화면엔 오른쪽 위 로그인 버튼 없음 — 가운데 '캐릭터 추가'가 로그인 길. 로그인 뒤 헤더는 그대로
    // b77: 관리자 입구 = 헤더 [로그아웃] 왼쪽 '👑 관리자' (b67 이후 헤더 버튼이 바로 로그아웃이라 ☁ 메뉴의 관리자 버튼에 갈 수 없었음)
    let ad=$('#svAdminHdr'); const adm=svIn&&svIsAdmin();
    if(adm&&!ad){ ad=document.createElement('button'); ad.id='svAdminHdr'; ad.className='hbtn admhdr'; ad.textContent='👑 관리자'; ad.title='관리자 — 가입 승인'; ad.onclick=e=>{ e.stopPropagation(); openAdmin(); }; b.parentNode.insertBefore(ad,b); }
    if(ad) ad.hidden=!adm;
    let w=$('#svWarn'); const bad=svIn&&['error','reconnect'].includes(gd.state);
    if(bad&&!w){ w=document.createElement('button'); w.id='svWarn'; w.className='hbtn svwarn'; b.parentNode.insertBefore(w,b); }
    if(w){ w.hidden=!bad; if(bad){ w.textContent='⚠ 저장 안 됨'; w.title=(gd.msg||'서버에 저장하지 못했습니다')+' — 눌러서 다시 저장'; } }
  }
  const st=$('#gdStatus'); if(st) st.innerHTML=gdStatusHtml();
}
function svLoginHtml(){ // 서버 모드 로그인 (☁ 메뉴): 이 PC 에 등록된 키로 / 새 키 입력 (키는 화면에 표시하지 않음). b67: 초대 비밀번호 없음 — 주 입구는 캐릭터 추가 창
  const ks=accounts().filter(a=>a.key).sort((x,y)=>(y.main?1:0)-(x.main?1:0));
  return `<div class="svlogin"><div class="muted tiny" style="margin:0 0 6px"><b>대표 키</b>(본계정 넥슨 Open API 키)로 로그인하세요. 다른 기기에서도 대표 키만 넣으면 데이터와 등록한 <b>부계정 키</b>가 그대로 돌아와요. 대표 키 자체는 서버에 저장되지 않아요.</div>
    ${ks.length?`<div class="toolbar">${ks.map(a=>`<button class="btn sm" data-svlogin="${a.id}">${esc(a.label)} 키를 대표 키로 로그인</button>`).join('')}</div>`:''}
    <div class="row" style="display:flex;gap:6px;margin-top:6px"><input class="pin" id="svKey" type="password" autocomplete="off" placeholder="대표 키 (넥슨 API 키) 붙여넣기" style="flex:1;min-width:0;text-align:left"><button class="btn sm" id="svLoginBtn">대표 키로 로그인</button></div>
    ${gd.svErr?`<div class="impmsg warn" style="margin-top:6px">${esc(gd.svErr)}</div>`:''}</div>`;
}
function svSubHtml(){ // 로그인 후: 대표 키 / 부계정 키 추가 (부계정 키는 대표 키로 암호화해 서버 보관)
  const m=svMain(), subs=accounts().filter(a=>a.key&&a!==m&&(!m||a.key!==m.key));
  return `<div class="svsub" style="margin-top:8px"><div class="muted tiny">대표 키: <b>${m?esc(m.label):'이 기기에 없음'}</b> · 부계정 키 ${subs.length}개${subs.length?` (${subs.map(a=>esc(a.label)).join(', ')})`:''}${m?' — 대표 키로 암호화해 서버에 보관':' — 대표 키로 로그인해야 서버에 보관돼요'}</div>${localStorage.getItem(SV_KEYERR_KEY)?`<div class="impmsg warn" style="margin-top:4px">⚠ 키 보관 실패: ${esc(localStorage.getItem(SV_KEYERR_KEY))}</div>`:''}
    <div class="row" style="display:flex;gap:6px;margin-top:4px"><input class="pin" id="svSubKey" type="password" autocomplete="off" placeholder="부계정 넥슨 API 키" style="flex:1;min-width:0;text-align:left"><button class="btn sm" id="svSubBtn">부계정 키 추가</button></div></div>`;
}
function gdStatusHtml(){
  const on=gdMeta.on&&gd.state!=='off';
  if(SV_ON){
    const head={off:'로그인하지 않음',connecting:'연결 중…',saving:'저장 중…',on:gdLocalDirty()||gd.timer?'변경 사항 저장 대기 (약 5초 후 자동 저장)':'✓ 동기화됨',
      reconnect:'다시 로그인 필요',conflict:'어느 데이터를 쓸지 선택이 필요합니다',error:'오류'}[gd.state];
    const logged=!!svTok()&&on;
    return `<div class="gdline"><b>${head}</b>${gd.msg?` <span class="muted">— ${esc(gd.msg)}</span>`:''}</div>
      ${logged?`<div class="muted" style="font-size:.8rem">마지막 저장: ${gdTime(gdMeta.lastSave)} · 마지막 불러오기: ${gdTime(gdMeta.lastLoad)}</div>
      <div class="toolbar" style="margin-top:8px">${gd.state==='error'?'':'<button class="btn sm" id="gdSaveNow">지금 저장</button>'}<button class="btn sm ghost" id="gdLogout">로그아웃</button>
      ${gd.state==='conflict'?'<button class="btn sm" id="gBtn2" onclick="gdReask()">선택하기</button>':''}</div>
      ${svIsAdmin()?'<div class="toolbar" style="margin-top:8px"><button class="btn sm" id="svAdminBtn">👑 관리자 — 가입 승인</button></div>':''}
      ${svSubHtml()}
      `
      :svLoginHtml()}`;
  }
  const head={off:'로그인하지 않음',connecting:'연결 중…',saving:'저장 중…',on:gdLocalDirty()||gd.timer?'변경 사항 저장 대기 (약 5초 후 자동 저장)':'✓ 동기화됨',
    reconnect:'다시 연결 필요',conflict:'어느 데이터를 쓸지 선택이 필요합니다',error:'오류'}[gd.state];
  return `<div class="gdline"><b>${head}</b>${gd.msg?` <span class="muted">— ${esc(gd.msg)}</span>`:''}</div>
    <div class="muted" style="font-size:.8rem">마지막 저장: ${gdTime(gdMeta.lastSave)} · 마지막 불러오기: ${gdTime(gdMeta.lastLoad)}</div>
    <div class="toolbar" style="margin-top:8px">${['reconnect','error'].includes(gd.state)?'<button class="btn sm" id="gdLogin">다시 연결</button>':''}${on
      ? `${['reconnect','error'].includes(gd.state)?'':'<button class="btn sm" id="gdSaveNow">지금 저장</button>'}<button class="btn sm ghost" id="gdLogout">로그아웃</button>`
      : `<button class="btn sm" id="gdLogin">구글 로그인</button>`}
      ${gd.state==='conflict'?'<button class="btn sm" id="gBtn2" onclick="gdReask()">선택하기</button>':''}</div>`;
}
/* 헤더 ☁ 버튼의 작은 드롭다운: 드라이브 동기화 상태 · 로그인/로그아웃 */
function gdMenuHtml(){
  let inner;
  if(!gcid()) inner=`<div class="impmsg warn"><b>구글 연결 준비 중</b><div>나머지 기능은 모두 정상 동작합니다.</div></div>`;
  else if(!gdOriginOk()) inner=`<div class="impmsg warn"><b>구글 동기화는 온라인 주소에서만 됩니다</b><div>파일(file://)로 연 페이지에서는 구글 로그인이 되지 않습니다. 온라인 주소 <a href="${GD.ONLINE}" target="_blank" rel="noopener">${GD.ONLINE}</a> 에서 사용하세요.</div></div>`;
  else inner=`<div id="gdStatus">${gdStatusHtml()}</div>
    <p class="muted tiny">${SV_ON?'🔑 대표 키는 서버에 저장되지 않아요. 부계정 키는 대표 키로 암호화해 보관해서, 다른 기기에서 대표 키로 로그인하면 함께 돌아와요.':''}</p>`;
  if(SV_ON) inner=`<div id="gdStatus">${gdStatusHtml()}</div><p class="muted tiny">🔑 대표 키는 서버에 저장되지 않아요. 부계정 키는 대표 키로 암호화해 보관해서, 다른 기기에서 대표 키로 로그인하면 함께 돌아와요. 변경 후 약 5초 뒤·창을 닫을 때 자동 저장.</p>`;
  return `<div class="gm-h"><b>${SV_ON?'☁️ 동기화':'☁️ 구글 드라이브 동기화'}</b><button class="ringx" id="gMenuClose" aria-label="닫기">✕</button></div>${inner}`;
}
function gdMenu(open){
  const m=$('#gMenu'); if(!m) return; const show=open??m.hidden;
  if(show) m.innerHTML=gdMenuHtml();
  m.hidden=!show; $('#gBtn').setAttribute('aria-expanded',String(show));
}
function gdHeaderClick(){ if(gd.state==='conflict'&&gd.pending){ gdMenu(false); return gdReask(); }
  if(SV_ON&&svTok()&&gdMeta.on){ gdMenu(false); return gdLogout(); } // 서버 모드: 헤더 버튼 = 로그아웃
  if(SV_ON){ gdMenu(false); return openAdd(); } // b67: 로그인 안 함 → 캐릭터 추가 창(본계정 키 등록)
  if(!SV_ON&&gd.state==='reconnect'&&gdMeta.on&&gdUsable()){ gdMenu(false); return gdLogin(); } // [☁ 다시 연결] 한 번 누르면 바로 로그인 → 동기화
  gdMenu(); }
function gdLoadLib(){
  return new Promise((res,rej)=>{
    if(window.google?.accounts?.oauth2) return res();
    let sc=document.getElementById('gsiScript');
    if(!sc){ sc=document.createElement('script'); sc.id='gsiScript'; sc.src='https://accounts.google.com/gsi/client'; sc.async=true; document.head.appendChild(sc); }
    sc.addEventListener('load',()=>res()); sc.addEventListener('error',()=>{ sc.remove(); rej(new Error('구글 로그인 스크립트를 불러오지 못했습니다 (인터넷 연결이나 광고 차단 확장 프로그램 확인)')); });
  });
}
/* 로그인 창(구글 팝업)은 사용자가 직접 누른 동작(☁ 로그인/다시 연결·지금 저장·충돌 선택)에서만 띄움 — gd.ia.
 * 자동 동작(페이지 열기·탭 복귀·1분마다 확인·자동 저장)은 남아 있는 토큰(1시간, 탭 sessionStorage)만 쓰고,
 * 토큰이 없거나 만료되면 팝업 없이 헤더를 [☁ 다시 연결]로 바꿈(변경 내용은 이 PC 에 그대로 → 다시 연결하면 합쳐서 저장). 2026-10-10 */
function gdHasTok(){ return SV_ON?!!svTok():driveHasTok(); }
function driveHasTok(){ return !!(gd.token&&Date.now()<gd.exp-60e3); }
const GD_NEED_LOGIN='구글 로그인 시간(1시간)이 끝났어요 — [☁ 다시 연결]을 한 번 누르면 이어서 동기화돼요 (바꾼 내용은 이 PC에 그대로 있어요)';
async function gdToken(interactive=gd.ia){
  if(SV_ON){ const t=svTok(); if(t) return t; throw Object.assign(new Error(SV_NEED_LOGIN),{type:'interaction_required'}); } // 서버 로그인은 ☁ 메뉴의 키 입력으로만
  return driveToken(interactive);
}
async function driveToken(interactive=gd.ia){
  if(driveHasTok()) return gd.token;
  if(!interactive) throw Object.assign(new Error(GD_NEED_LOGIN),{type:'interaction_required'});
  gd.ia=false; // 한 번의 클릭에 팝업은 최대 한 번
  await gdLoadLib();
  if(!gd.client) gd.client=google.accounts.oauth2.initTokenClient({client_id:gcid(),scope:GD.SCOPE,
    callback:r=>gd.onTok&&gd.onTok(r), error_callback:e=>gd.onErr&&gd.onErr(e)});
  return new Promise((res,rej)=>{
    gd.onTok=r=>{
      if(r.error) return rej(Object.assign(new Error(r.error_description||r.error),{type:r.error}));
      if(google.accounts.oauth2.hasGrantedAllScopes && !google.accounts.oauth2.hasGrantedAllScopes(r,GD.SCOPE))
        return rej(Object.assign(new Error('드라이브 앱 데이터 권한에 체크해야 동기화할 수 있습니다'),{type:'scope'}));
      gd.token=r.access_token; gd.exp=Date.now()+(+r.expires_in||3599)*1000;
      sessionStorage.setItem(GD.TOKEN_KEY,JSON.stringify({t:gd.token,e:gd.exp})); res(gd.token);
    };
    gd.onErr=e=>rej(Object.assign(new Error({popup_failed_to_open:'로그인 팝업이 차단되었습니다',popup_closed:'로그인 창이 닫혔습니다'}[e?.type]||e?.message||'로그인 실패'),{type:e?.type||'unknown'}));
    gd.client.requestAccessToken({prompt:''}); // 이미 동의했다면 창이 잠깐 떴다가 바로 닫힘
  });
}
async function gdFetch(url,opt={},retry=true){ // 구글 드라이브 전용
  const tok=await driveToken();
  const r=await fetch(url,{...opt,headers:{...(opt.headers||{}),Authorization:'Bearer '+tok}});
  if(r.status===401){ gd.token=null; gd.exp=0; sessionStorage.removeItem(GD.TOKEN_KEY); if(retry&&gd.ia) return gdFetch(url,opt,false);
    throw Object.assign(new Error(GD_NEED_LOGIN),{type:'interaction_required'}); }
  if(!r.ok){ let m=''; try{ m=(await r.json()).error?.message||''; }catch(e){}
    throw Object.assign(new Error(`드라이브 오류 (HTTP ${r.status})${m?' — '+m:''}`),{status:r.status}); }
  return r;
}
async function gdFind(){
  if(SV_ON){ const m=await svFetch('/api/state/meta'); return m.rev>0?{id:'sv',rev:m.rev,updatedAt:m.updatedAt}:null; }
  return driveFind();
}
async function gdRead(id){
  if(SV_ON){ const b=await svFetch('/api/state'); gd.remoteRev=+b.rev||0; return svRemote(b); }
  return driveRead(id);
}
async function driveFind(){
  const q=encodeURIComponent(`name='${GD.FILE}' and trashed=false`);
  const r=await gdFetch(`${GD.API}/files?spaces=appDataFolder&q=${q}&orderBy=modifiedTime%20desc&pageSize=10&fields=files(id,modifiedTime,appProperties)`);
  return ((await r.json()).files||[])[0]||null;
}
async function driveRead(id){ return (await gdFetch(`${GD.API}/files/${id}?alt=media`)).json(); }
function gdPayload(){ return {app:'maple-boss-tracker',format:1,savedAt:Date.now(),updatedAt:S.updatedAt||0,characters:S.characters.length,withKeys:true,data:backupData(true)}; }
async function svWrite(keepalive,depth=0){
  const r=await svFetch('/api/state',{method:'PUT',allow409:true,keepalive:!!keepalive,body:{baseRev:gd.remoteRev??gdMeta.rev??0,updatedAt:S.updatedAt||0,data:backupData(false)}});
  if(r.conflict){ // 그 사이 다른 기기가 저장 → 받은 내용과 3-way 병합 후 다시 저장 (gdCommit → gdWrite)
    if(depth>=3||keepalive) throw new Error('다른 기기와 동시에 저장되고 있어요 — 잠시 후 다시 시도해 주세요');
    gd.remoteRev=+r.rev||0; gd.w409=depth+1;
    try{ await gdSync(svRemote(r),{push:true}); } finally{ gd.w409=0; }
    return;
  }
  gd.remoteRev=+r.rev||0; gd.fileId='sv'; gdMeta.lastSave=Date.now(); gdMarkSynced(S.updatedAt||0);
}
// 다른 기기가 마지막으로 맞춘 뒤 저장했는지 (탭 복귀·1분마다·저장 직전 확인)
async function gdRemoteChanged(needSeen){
  if(SV_ON){ const m=await svFetch('/api/state/meta'); return m.rev>0&&m.rev!==(gdMeta.rev||0); }
  const m=await (await gdFetch(`${GD.API}/files/${gd.fileId}?fields=id,appProperties`)).json();
  const rU=+(m.appProperties?.updatedAt||0), seen=gdMeta.rU||gdMeta.base;
  return !!((!needSeen||seen) && rU && rU!==seen && rU!==(S.updatedAt||0));
}
async function gdWrite(keepalive){
  if(SV_ON) return svWrite(keepalive,gd.w409||0);
  const body=JSON.stringify(gdPayload());
  const meta={appProperties:{updatedAt:String(S.updatedAt||0),characters:String(S.characters.length)}};
  if(!gd.fileId){ meta.name=GD.FILE; meta.parents=['appDataFolder']; meta.mimeType='application/json'; }
  const bd='mbt'+Math.random().toString(36).slice(2);
  const mp=`--${bd}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(meta)}\r\n--${bd}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${body}\r\n--${bd}--`;
  const opt={method:gd.fileId?'PATCH':'POST',headers:{'Content-Type':`multipart/related; boundary=${bd}`},body:mp,keepalive:!!keepalive&&mp.length<60000};
  try{
    const r=await gdFetch(gd.fileId?`${GD.UP}/files/${gd.fileId}?uploadType=multipart&fields=id`:`${GD.UP}/files?uploadType=multipart&fields=id`,opt);
    gd.fileId=(await r.json()).id||gd.fileId;
  }catch(e){ if(e.status===404&&gd.fileId){ gd.fileId=null; return gdWrite(keepalive); } throw e; }
  gdMeta.fileId=gd.fileId; gdMeta.lastSave=Date.now(); gdMarkSynced(S.updatedAt||0);
}
/* ---- 동기화 비교·병합 (2026-10-10) ----
 * 비교(contentSig)에서 빼는 값 = GD_LOCAL_RE: 기기 전용(테마·선택 캐릭터·날짜 period·마지막 동기화 시각) + 자동 갱신 값(캐릭터 sync/이미지/EXP/훈장/길드 — b98, 계정 상태·키).
 *   이 값들은 병합할 때도 '이 PC 값'을 씀(키는 이 PC 에 없으면 드라이브 값).
 * 병합 = 3-way: 마지막으로 맞춘 내용(base, localStorage GD_BASE_KEY) 기준으로 한쪽만 바뀐 항목은 그쪽 값, 양쪽이 같은 항목을 다르게 바꾼 경우만 '충돌'.
 *   캐릭터·계정은 id, 주간/월간 기록은 week/month 로 짝지음. 한쪽 삭제 + 다른 쪽 수정 → 수정본 유지(데이터 안 잃음).
 *   API 로 다시 받는 값(레벨·직업·월드·ocid·계정 배정)과 지난 기록 요약은 충돌이어도 묻지 않음(이 PC 값 / 클리어 많은 쪽). */
const GD_BASE_KEY=SV_ON?'mapleBossTracker.svbase':'mapleBossTracker.gdbase';
const GD_LOCAL_RE=/^(theme|activeId|period|updatedAt|version|startWeek)$|^settings\.(lastSync|autoSync|apiKey|driveKeys|apiMode|prices|priceSource|worldLimit)$|^characters\[[^\]]*\]\.(sync|image|exp|medal|guildAt|guild)$|^settings\.accounts\[[^\]]*\]\.(key|bk|status)$/;
const GD_SOFT_RE=/^characters\[[^\]]*\]\.(level|job|world|ocid|accId)$/;
const GD_HIST_RE=/^(history|monthHistory|missW|missM)\[[^\]]*\]$/;
const GD_KEYED={characters:'id',history:'week',monthHistory:'month',missW:'week',missM:'month','settings.accounts':'id'};
const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().filter(k=>v[k]!==undefined).map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
const gdIsObj=v=>!!v&&typeof v==='object'&&!Array.isArray(v);
const gdP=(p,k)=>p?p+'.'+k:k;
const gdSame=(a,b)=>stable(a)===stable(b);
function gdStrip(v,p=''){
  if(Array.isArray(v)){ const kf=GD_KEYED[p]; return v.map(x=>gdStrip(x,kf&&gdIsObj(x)?`${p}[${x[kf]}]`:p+'[]')); }
  if(gdIsObj(v)){ const o={}; for(const k of Object.keys(v)){ const q=gdP(p,k); if(!GD_LOCAL_RE.test(q)) o[k]=gdStrip(v[k],q); } return o; }
  return v;
}
const gdSig=d=>stable(gdStrip(d));
const keysOf=d=>SV_ON?'':((d&&d.settings&&d.settings.accounts)||[]).map(a=>a.id+':'+(a.key||'')).join(',');
function contentSig(d){ return gdSig(d)+'|'+keysOf(d); } // 키가 바뀌어도 저장은 필요 (비교 화면에는 안 씀)
const gdPrep=d=>rollPeriod(normState(JSON.parse(JSON.stringify(d||{}))));
function gdMerge(b,l,r,ctx,p=''){
  if(p&&GD_LOCAL_RE.test(p)){ // b98: 넥슨 API에서 자동으로 받아 오는 캐릭터 값은 충돌로 묻지 않음 — 훈장(medal)은 더 최근에 확인한 쪽(at), guildAt 은 큰 쪽, 나머지는 이 기기 값(없으면 상대)
    if(/\.medal$/.test(p)&&gdIsObj(l)&&gdIsObj(r)) return (+r.at||0)>(+l.at||0)?r:l;
    if(/\.guildAt$/.test(p)&&typeof l==='number'&&typeof r==='number') return Math.max(l,r);
    return l!==undefined&&l!==''&&l!==null?l:r; }
  if(gdSame(l,r)) return l;
  if(ctx.base){ if(gdSame(b,l)) return r; if(gdSame(b,r)) return l; }
  if(l===undefined) return r; if(r===undefined) return l; // 한쪽에만 있음(새로 추가 / 삭제 vs 수정) → 있는 쪽 유지
  const kf=GD_KEYED[p];
  if(kf&&Array.isArray(l)&&Array.isArray(r)) return gdMergeKeyed(b,l,r,kf,ctx,p);
  if(GD_HIST_RE.test(p)) return ((r.cleared||0)>(l.cleared||0)||((r.cleared||0)===(l.cleared||0)&&(r.total||0)>(l.total||0)))?r:l;
  if(gdIsObj(l)&&gdIsObj(r)){ const o={};
    for(const k of new Set([...Object.keys(l),...Object.keys(r)])){ const v=gdMerge(gdIsObj(b)?b[k]:undefined,l[k],r[k],ctx,gdP(p,k)); if(v!==undefined) o[k]=v; }
    return o; }
  if(GD_SOFT_RE.test(p)) return ctx.prefer==='r'?r:l;
  ctx.conf.push(p); return ctx.prefer==='r'?r:l;
}
// b216: 서버 값으로 덮어쓰기 — 기기 전용·자동 갱신 값(GD_LOCAL_RE: 테마·선택 캐릭터·키 등)만 이 PC 값 유지, 나머지는 전부 서버(r)
function gdServerWins(l,r,p=''){
  if(p&&GD_LOCAL_RE.test(p)) return gdMerge(undefined,l,r,{base:false,prefer:'l',conf:[]},p);
  if(r===undefined) return undefined;
  const kf=GD_KEYED[p];
  if(kf&&Array.isArray(r)){ const L=new Map((Array.isArray(l)?l:[]).filter(x=>gdIsObj(x)&&x[kf]!=null).map(x=>[String(x[kf]),x]));
    return r.map(x=>gdIsObj(x)&&x[kf]!=null?gdServerWins(L.get(String(x[kf])),x,`${p}[${x[kf]}]`):x); }
  if(gdIsObj(r)){ const lo=gdIsObj(l)?l:{}, o={};
    for(const k of new Set([...Object.keys(lo),...Object.keys(r)])){ const v=gdServerWins(lo[k],r[k],gdP(p,k)); if(v!==undefined) o[k]=v; }
    return o; }
  return r;
}
function gdMergeKeyed(b,l,r,kf,ctx,p){
  const list=a=>(Array.isArray(a)?a:[]).filter(x=>gdIsObj(x)&&x[kf]!=null), ids=a=>list(a).map(x=>String(x[kf]));
  const map=a=>new Map(list(a).map(x=>[String(x[kf]),x]));
  const B=map(b), L=map(l), R=map(r), lo=ids(l), ro=ids(r);
  // 순서: 이 PC 순서가 base 그대로면 드라이브 순서, 아니면 이 PC 순서 (+ 다른 쪽에만 있는 것은 뒤에)
  const first=ctx.base?(gdSame(lo,ids(b).filter(i=>L.has(i)))?ro:lo):(ctx.prefer==='r'?ro:lo);
  const order=[...new Set([...first,...lo,...ro])], out=[];
  for(const id of order){ const v=gdMerge(B.get(id),L.get(id),R.get(id),ctx,`${p}[${id}]`); if(v!==undefined) out.push(v); }
  return out;
}
function gdBaseData(){ try{ return JSON.parse(localStorage.getItem(GD_BASE_KEY)||'null'); }catch(e){ return null; } }
// 드라이브와 이 PC 가 같은 내용이 된 시점 기록: base(이 PC updatedAt) · rU(드라이브 updatedAt) · 그때 내용(키 제외)
function gdMarkSynced(rU){
  gdMeta.base=S.updatedAt||0; gdMeta.rU=rU||S.updatedAt||0; if(SV_ON) gdMeta.rev=gd.remoteRev??gdMeta.rev??0; gdSaveMeta();
  try{ localStorage.setItem(GD_BASE_KEY,JSON.stringify(backupData(false))); }catch(e){ console.warn('gdbase',e); }
}
const gdLocalEmpty=()=>!S.characters.length && !(S.history||[]).length && !(S.monthHistory||[]).length;

const GD_TEST_USER_HELP='구글 로그인 창에 <b>"액세스 차단됨: … Google 인증 절차를 완료하지 않았습니다"</b>(오류 403: access_denied)가 보였다면, 이 앱이 아직 <b>테스트 모드</b>라서 등록된 계정만 로그인할 수 있기 때문입니다. '
  +'<a href="https://console.cloud.google.com/auth/audience" target="_blank" rel="noopener">Google Cloud 콘솔 &gt; Google 인증 플랫폼 &gt; 대상 &gt; 테스트 사용자</a>에서 <b>사용자 추가</b>로 지금 로그인한 구글 이메일을 넣고 저장한 뒤 다시 시도하세요.';
const GD_UNVERIFIED_HELP='<b>"Google에서 확인하지 않은 앱"</b> 화면이 나오면 정상입니다 (개인용 앱이라 구글 심사를 받지 않았음). <b>계속</b>을 누른 뒤, 권한 화면에서 <b>Google Drive 앱 데이터(자체 구성 데이터) 권한</b>에 체크하고 계속하세요. 테스트 모드에서는 7일마다 한 번씩 다시 허용해야 할 수 있습니다.';
function gdErrInfo(e){
  const t=e?.type||'';
  if(t==='popup_closed') return {short:'로그인 창이 닫혔습니다 — 다시 연결을 눌러 주세요',html:`<p><b>로그인을 끝내기 전에 구글 로그인 창이 닫혔습니다.</b> 다시 시도해 주세요.</p><ul><li>${GD_UNVERIFIED_HELP}</li><li>${GD_TEST_USER_HELP}</li></ul>`};
  if(t==='access_denied') return {short:'구글 로그인이 거부되었습니다 (테스트 사용자 등록 확인)',html:`<p><b>구글이 로그인을 허용하지 않았습니다 (access_denied).</b></p><ul><li>${GD_TEST_USER_HELP}</li><li>권한 화면에서 <b>취소</b>를 눌렀다면 다시 시도해 <b>계속/허용</b>을 눌러 주세요.</li></ul>`};
  if(t==='scope') return {short:'드라이브 권한에 체크하지 않았습니다',html:`<p><b>드라이브 권한이 허용되지 않았습니다.</b> 다시 로그인해서 권한 화면의 <b>Google Drive 앱 데이터(자체 구성 데이터)</b> 항목에 체크한 뒤 계속을 눌러 주세요. 이 권한으로는 이 앱이 만든 숨김 파일 하나만 다루며, 내 드라이브의 다른 파일은 볼 수 없습니다.</p>`};
  if(t==='popup_failed_to_open') return {short:'로그인 팝업이 차단되었습니다 — 다시 연결을 눌러 주세요',html:`<p><b>브라우저가 구글 로그인 팝업을 막았습니다.</b> 상단의 <b>☁ 다시 연결</b>을 직접 눌러 주세요. 그래도 안 되면 주소창 오른쪽의 팝업 차단 아이콘에서 이 사이트의 팝업을 <b>항상 허용</b>으로 바꿔 주세요.</p>`};
  if(/invalid_client|unauthorized_client|origin|redirect_uri/i.test(t+' '+(e?.message||''))) return {short:'구글 클라이언트 설정 오류',html:`<p><b>구글 OAuth 클라이언트 설정 문제입니다 (${esc(t||e.message)}).</b> Google 인증 플랫폼 &gt; 클라이언트의 <b>승인된 JavaScript 원본</b>에 <code>${esc(location.origin)}</code> 이 정확히(끝에 / 없이) 들어 있는지 확인하세요. 바꾼 뒤 반영까지 몇 분 걸릴 수 있습니다.</p>`};
  return null;
}
function gdFail(e,interactive){
  console.warn('drive',e);
  const info=gdErrInfo(e);
  if(info||['immediate_failed','interaction_required'].includes(e.type)){
    gdSet('reconnect',info?info.short:SV_ON?(e.message||SV_NEED_LOGIN):(e.message||'')+' — 상단의 [☁ 다시 연결]을 한 번 눌러 주세요');
    if(info&&interactive) gdHelpModal(info.html);
  } else gdSet('error',e.message||String(e));
}
function gdHelpModal(html){
  $('#gdTitle').textContent='☁️ 구글 로그인 안내';
  $('#gdBody').innerHTML=`<div class="gdhelp">${html}</div><div class="row"><button class="btn plain" id="gdClose2" onclick="$('#driveModal').classList.remove('show')">닫기</button><button class="btn" id="gdLogin">다시 로그인</button></div>`;
  $('#driveModal').classList.add('show');
}
// API 키 비교: 드라이브에만 있는 키는 이 PC로 가져오고, 이 PC에만 있거나 다른 키가 있으면 드라이브에 저장 필요
function gdKeyDiff(d){
  const R={}; ((d&&d.settings&&d.settings.accounts)||[]).forEach(a=>{ if(a&&a.id&&a.key) R[a.id]=a.key; });
  let pulled=0, push=false;
  for(const a of accounts()){ if(!a.key && R[a.id]){ a.key=R[a.id]; pulled++; } else if(a.key && R[a.id]!==a.key) push=true; }
  return {pulled, push};
}
async function gdConnect(interactive){
  if(!interactive && !gdHasTok()){ gdSet('reconnect',SV_ON?SV_NEED_LOGIN:GD_NEED_LOGIN); return; } // 페이지를 열 때 로그인 창을 자동으로 띄우지 않음
  gdSet('connecting', SV_ON?'서버 확인 중…':interactive&&!gdHasTok()?'구글 로그인 창에서 계정을 선택하고 허용해 주세요 ("확인하지 않은 앱" 화면이면 [계속])':'드라이브 확인 중…');
  gd.ia=!!interactive;
  try{
    await gdToken(!!interactive);
    gdSet('connecting',SV_ON?'서버 확인 중…':'드라이브 확인 중…');
    gdMeta.on=true; gdSaveMeta();
    const f=await gdFind(); gd.fileId=f?.id||null;
    if(!f){ if(SV_ON){ gd.remoteRev=0; gdMeta.rev=0; }
      if(gdLocalEmpty()){ gdSet('on',(SV_ON?'서버':'드라이브')+'에 아직 데이터가 없습니다. 캐릭터를 추가하면 자동 저장됩니다'); return; }
      await gdWrite(); gdSet('on','이 PC 데이터를 '+(SV_ON?'서버':'드라이브')+'에 처음 저장했습니다'); return; }
    gd.busy=true; let res;
    try{ res=await gdSync(await gdRead(f.id)); if(SV_ON) svAfterLogin(); } finally{ gd.busy=false; }
    if(res!=='ask'){ gdSet('on',GD_RES_MSG[res]||''); if(res==='loaded') toast('☁ '+GD_RES_MSG.loaded); }
    if(gd.again){ gd.again=false; gdChanged(); }
  }catch(e){ gdFail(e,interactive); }
  finally{ gd.ia=false; }
}
const GD_RES_MSG={same:'',pushed:SV_ON?'이 PC의 변경 사항을 서버에 저장했습니다':'이 PC의 변경 사항을 드라이브에 저장했습니다',pulled:'다른 기기에서 바뀐 데이터를 불러왔습니다',merged:'다른 기기의 변경과 자동으로 합쳤습니다',loaded:SV_ON?'서버 데이터를 불러왔습니다':'드라이브 데이터를 불러왔습니다'};
/* 드라이브 파일과 이 PC 데이터를 맞춤 → 'same'|'pushed'|'pulled'|'merged'|'loaded'|'ask'
 *  - 이 PC 가 비어 있음 → 드라이브 불러오기
 *  - base(마지막으로 맞춘 내용)가 있으면 3-way 병합, 진짜 충돌(같은 항목을 양쪽에서 다르게 수정)일 때만 한 번 질문
 *  - 예전 버전 메타(시각만 있음): 한쪽만 바뀌었으면 그쪽, 둘 다면 묻지 않고 합침(겹치는 값은 최근 수정한 쪽)
 *  - 이 PC 에서 처음 연결 + 내용이 다름 → 한 번 질문(통째로 고르기) */
async function gdSync(remote,o={}){
  if(!remote?.data || !Array.isArray(remote.data.characters)) throw new Error('드라이브 파일 형식이 올바르지 않습니다');
  if(gdLocalEmpty()){ gdApply(remote,null); return 'loaded'; }
  const rU=+remote.updatedAt||0, lU=S.updatedAt||0;
  const rd=gdPrep(remote.data), ld=gdPrep(backupData(true));
  let bd=gdBaseData(); bd=bd?gdPrep(bd):null;
  if(!bd&&gdMeta.base){ if(rU===gdMeta.base) bd=rd; else if(lU===gdMeta.base) bd=ld; }
  if(SV_ON){ // b216: 서버 모드는 묻지 않음('어느 데이터를 쓸까요?' 없음) — 서버에 저장된 값이 항상 이김
    // 서버가 마지막으로 맞춘 내용(base) 그대로면 이 PC 의 저장 안 된 변경만 올림. 서버가 바뀌었으면:
    //  - 불러오기(페이지 열기·1분마다 확인·로그인) → 서버 값으로 통째로 덮어씀 (이 PC 에만 있던 예전 값은 올리지 않음)
    //  - 저장 중(저장 버튼·409) → 방금 이 PC 에서 바꾼 항목만 합치고, 서버와 겹치는 항목은 서버 값
    if(!bd||(gdSig(rd)!==gdSig(bd)&&!o.push)) return gdCommit(gdServerWins(ld,rd),remote);
    return gdCommit(gdMerge(bd,ld,rd,{base:true,prefer:'r',conf:[]}),remote);
  }
  const legacy=!bd&&!!gdMeta.base;
  if(!bd&&!legacy&&gdSig(rd)!==gdSig(ld)) return gdAsk(remote,{mode:'whole'});
  const ctx={base:!!bd,prefer:legacy?(lU>=rU?'l':'r'):'l',conf:[]};
  const m=gdMerge(bd,ld,rd,ctx);
  if(ctx.conf.length&&!legacy) return gdAsk(remote,{mode:'merge',conf:ctx.conf,base:bd});
  return gdCommit(m,remote);
}
// 병합 결과 m 을 이 PC 에 적용(달라졌으면)하고 드라이브에 저장(달라졌으면)
async function gdCommit(m,remote){
  const rU=+remote.updatedAt||0, rd=gdPrep(remote.data);
  ['history','monthHistory','missW','missM'].forEach(k=>{ if(Array.isArray(m[k])) m[k].sort((a,b)=>String(a.week||a.month)<String(b.week||b.month)?-1:1); });
  const mS=contentSig(m), toLocal=mS!==contentSig(gdPrep(backupData(true))), toRemote=mS!==contentSig(rd)||!remote.withKeys;
  if(toLocal){ m.updatedAt=gdSig(m)===gdSig(rd)&&!toRemote?rU:Date.now(); gdLoad(m); }
  if(toRemote){ await gdWrite(); }
  else { if((S.updatedAt||0)!==rU){ S.updatedAt=rU; localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(S)); } gdMeta.lastLoad=Date.now(); gdMarkSynced(rU); }
  if(toLocal&&!toRemote) toast('☁ '+GD_RES_MSG.pulled); // zosu: 자동 병합(merged) 알림은 화면 아래에 띄우지 않음
  return toLocal&&toRemote?'merged':toLocal?'pulled':toRemote?'pushed':'same';
}
function gdLoad(m){ localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(m)); load(); checkResets(); localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(S)); applyTheme(); render(); }
// 드라이브 데이터를 통째로 사용 (이 PC 가 비었을 때 / 처음 연결 질문에서 '드라이브' 선택)
function gdApply(remote,msg){
  const d=JSON.parse(JSON.stringify(remote.data)); d.updatedAt=+remote.updatedAt||Date.now();
  applyData(d); // load() 로 updatedAt 이 드라이브 값 그대로 유지됨 (드라이브의 API 키도 함께 복원)
  gdMeta.lastLoad=Date.now(); gdMarkSynced(+remote.updatedAt||0);
  if(!SV_ON && (gdKeyDiff(d).push || !remote.withKeys)) gdPush(); // 이 PC에만 있던 키를 드라이브에도 저장 (서버 모드는 키를 저장하지 않음)
  if(msg){ gdSet('on',msg); toast('☁ '+msg); }
}
const GD_FIELD={name:'이름',bosses:'보스 설정',weekly:'주간 체크',monthly:'월간 체크',auto:'자동 체크',drops:'획득 아이템',mdrops:'월간 획득 아이템',dropOut:'반지 결과',mdropOut:'반지 결과',drev:'아이템 판매 수익',mdrev:'아이템 판매 수익',isMain:'본캐 지정',
  worldOrder:'월드 순서',dq:'일퀘 표시 설정',settings:'설정',label:'계정 이름'};
function gdConfLabel(p,d){
  const m=/^characters\[([^\]]*)\]\.?([^.\[]*)/.exec(p);
  if(m){ const c=(d.characters||[]).find(x=>String(x.id)===m[1])||S.characters.find(x=>String(x.id)===m[1]); return `${c?c.name:'캐릭터'} · ${GD_FIELD[m[2]]||m[2]||'캐릭터'}`; }
  const a=/^settings\.accounts\[([^\]]*)\]/.exec(p); if(a) return '넥슨 계정 이름';
  return GD_FIELD[p.split(/[.\[]/)[0]]||p;
}
function gdAsk(remote,opt={}){
  if(!remote) return 'ask'; gd.pending={...opt,remote}; gdSet('conflict');
  const rU=+remote.updatedAt||0, lU=S.updatedAt||0, d=remote.data;
  const card=(t,ic,u,chars,weeks,newer,id,btn)=>`<div class="gdside ${newer?'newer':''}"><div class="gdt">${ic} ${t} ${newer?'<span class="pill">최근 수정</span>':''}</div>
    <div>마지막 수정: <b>${u?hm(u):'알 수 없음'}</b></div><div>캐릭터 <b>${chars}</b>명 · 주간 기록 ${weeks}주</div>
    <button class="btn ${newer?'':'ghost'}" id="${id}">${btn}</button></div>`;
  $('#gdTitle').textContent='☁️ 어느 데이터를 쓸까요?';
  if(opt.mode==='merge'){
    const labels=[...new Set((opt.conf||[]).map(p=>gdConfLabel(p,d)))];
    $('#gdBody').innerHTML=`<p class="muted" style="margin-top:0">${SV_ON?'서버(다른 기기)':'구글 드라이브(다른 기기)'}와 이 PC에서 <b>같은 항목을 서로 다르게</b> 바꿨어요. 겹치는 항목만 어느 쪽 값을 쓸지 골라 주세요. <b>나머지 변경은 양쪽 모두 자동으로 합쳐집니다.</b></p>
      <ul class="gdconf">${labels.slice(0,5).map(t=>`<li>${esc(t)}</li>`).join('')}${labels.length>5?`<li>외 ${labels.length-5}곳</li>`:''}</ul>
      <div class="gdsides">${card(SV_ON?'서버 (다른 기기)':'구글 드라이브','☁️',rU,d.characters.length,(d.history||[]).length,rU>lU,'gdUseDrive',SV_ON?'서버 쪽 값으로':'드라이브 쪽 값으로')}
      ${card('이 PC','💻',lU,S.characters.length,(S.history||[]).length,lU>=rU,'gdUseLocal','이 PC 쪽 값으로')}</div>`;
  } else {
    $('#gdBody').innerHTML=`<p class="muted" style="margin-top:0">이 PC에서 처음 연결했는데 ${SV_ON?'서버':'구글 드라이브'}와 이 PC의 데이터가 서로 다릅니다. 어느 쪽을 쓸지 한 번만 골라 주세요. 고르지 않은 쪽은 덮어써집니다.</p>
    <div class="gdsides">${card(SV_ON?'서버 (다른 기기)':'구글 드라이브','☁️',rU,d.characters.length,(d.history||[]).length,rU>lU,'gdUseDrive',SV_ON?'서버 데이터 불러오기':'드라이브 데이터 불러오기')}
    ${card('이 PC','💻',lU,S.characters.length,(S.history||[]).length,lU>=rU,'gdUseLocal','이 PC 데이터로 덮어쓰기')}</div>`;
  }
  $('#driveModal').classList.add('show');
  return 'ask';
}
function gdReask(){ const P=gd.pending; if(P) gdAsk(P.remote,P); }
async function gdResolve(which){
  const P=gd.pending; $('#driveModal').classList.remove('show'); if(!P) return; gd.pending=null;
  const remote=P.remote; gd.ia=true; // 사용자가 직접 고름 → 토큰이 만료됐으면 로그인 창 한 번 허용
  try{
    gdSet('saving');
    if(P.mode==='merge'){
      const ctx={base:true,prefer:which==='drive'?'r':'l',conf:[]};
      const m=gdMerge(P.base,gdPrep(backupData(true)),gdPrep(remote.data),ctx);
      await gdCommit(m,remote); const msg=`겹치는 항목은 ${which==='drive'?'드라이브':'이 PC'} 값으로, 나머지는 합쳤습니다`; gdSet('on',msg); toast('☁ '+msg);
    }
    else if(which==='drive') gdApply(remote,'드라이브 데이터를 불러왔습니다');
    else { if(!gd.fileId) gd.fileId=(await gdFind())?.id||null; await gdWrite(); gdSet('on','이 PC 데이터로 드라이브를 덮어썼습니다'); toast('☁ 이 PC 데이터로 드라이브를 덮어썼습니다'); }
  }catch(e){ gdFail(e); }
  finally{ gd.ia=false; if(SV_ON) svAfterLogin(); }
}
function gdChanged(){
  if(SV_ON){ gdRender(); clearTimeout(gdChanged._t); gdChanged._t=setTimeout(()=>{ if(!pend&&gdLocalDirty()&&!svPushing) svPushBg(); },2000); return; } /* b112: 자동 변경(동기화·주간 초기화 등)은 사용자 수정이 아니므로 [저장] 대신 뒤에서 저장 */ // 서버 모드: 자동 저장 없음 (svSaveNow / 로그아웃 창의 [저장 후 로그아웃]으로만 저장)
  if(!gdMeta.on||!gdUsable()||gd.state==='conflict') return;
  if(gd.state==='reconnect'&&!gdHasTok()){ gdRender(); return; } // 로그인 필요 상태: 이 PC 에만 저장, 다시 연결할 때 합쳐서 저장
  clearTimeout(gd.timer); gd.timer=setTimeout(()=>{ gd.timer=null; gdPush(); },GD.DEBOUNCE); gdRender();
}
// 다른 기기에서 바뀐 내용 확인 (탭으로 돌아올 때·1분마다, 메타데이터만 조회 → 바뀌었을 때만 내용 읽어서 합침)
async function gdPull(force){
  if(SV_ON&&gdLocalDirty()) return; // 저장 안 한 변경이 있으면 받아 오지 않음 (합친 뒤 자동 저장되는 것 방지)
  if(!gdMeta.on||!gdUsable()||gd.state!=='on'||gd.busy||gd.timer||!gd.fileId||!gdHasTok()) return; // 토큰 없으면 조용히 건너뜀(로그인 창 X)
  if(!force&&Date.now()-(gd.pulledAt||0)<55e3) return; gd.pulledAt=Date.now();
  gd.busy=true;
  try{
    if(await gdRemoteChanged(false)){ const res=await gdSync(await gdRead(gd.fileId)); if(res!=='ask') gdSet('on',GD_RES_MSG[res]||''); }
  }catch(e){ console.warn('sync pull',e); if(e.type==='interaction_required') gdSet('reconnect',SV_ON?SV_NEED_LOGIN:GD_NEED_LOGIN); }
  finally{ gd.busy=false; if(gd.again){ gd.again=false; gdChanged(); } }
}
async function gdPush(opts={}){
  clearTimeout(gd.timer); gd.timer=null;
  if(!gdMeta.on||!gdUsable()||gd.state==='conflict') return false;
  if(opts.quick && !gdHasTok()) return false; // 창을 닫는 중에는 로그인 창을 띄울 수 없음
  if(gd.busy){ gd.again=true; return false; }
  if(!opts.manual && !gdHasTok()){ gdSet('reconnect',SV_ON?SV_NEED_LOGIN:GD_NEED_LOGIN); return false; } // 자동 저장은 로그인 창을 띄우지 않음
  gd.busy=true; gdSet('saving'); gd.ia=!!opts.manual;
  try{
    if(!opts.quick){
      if(SV_ON) await svSyncSubKeys();
      if(!gd.fileId) gd.fileId=(await gdFind())?.id||null;
      else{ // 다른 PC에서 그 사이 저장했는지 확인 (덮어쓰기 방지)
        try{
          if(await gdRemoteChanged(true)){ // 다른 기기가 그 사이 저장 → 합친 뒤 저장 (진짜 충돌일 때만 질문)
            const res=await gdSync(await gdRead(gd.fileId),{push:true}); if(res==='ask') return false; gdSet('on',GD_RES_MSG[res]||''); return true; }
        }catch(e){ if(e.status===404) gd.fileId=null; else throw e; }
      }
    }
    await gdWrite(opts.quick); gdSet('on'); return true;
  }catch(e){ gdFail(e,opts.manual); return false; }
  finally{ gd.ia=false; gd.busy=false; if(gd.again){ gd.again=false; gdChanged(); } }
}
function gdLogin(){ $('#driveModal').classList.remove('show'); if(SV_ON){ openAdd(); return; } gdConnect(true); }
/* ---- 서버 모드: 로그인 · 키 연결 · 드라이브에서 가져오기 ---- */
async function svLogin(key,accId,opt={}){
  if(gd.state==='connecting'&&opt.quiet) return; // b68: 열 때 자동 확인은 다른 로그인 중이면 건너뜀
  key=String(key||'').trim(); if(!key){ gd.svErr='API 키를 넣어 주세요'; return gdRender(); }
  gd.svErr=''; gdSet('connecting','넥슨 API 키 확인 중…'); svMainRender();
  try{
    const b=await svFetch('/api/login',{method:'POST',noAuth:true,body:{key,label:(navigator.userAgentData?.platform||navigator.platform||'').slice(0,30)}});
    if(b.status==='pending'||(!b.token&&b.pending)){ // b68: 처음 보는 본계정 키 = 가입 승인 대기 (세션·데이터 없음). 키는 이 기기에만 보관해 나중에 같은 키로 다시 확인
      localStorage.setItem(SV_PEND_KEY,JSON.stringify({key,...(b.pending||{})})); gdSet('off'); svMainRender();
      if(!$('#importModal').classList.contains('show')&&!opt.quiet) openImport();
      if(!opt.quiet) toast(b.newUser?'가입을 요청했어요 — 관리자 승인 후 사용할 수 있어요':'아직 승인 대기 중이에요'); return;
    }
    localStorage.removeItem(SV_PEND_KEY); localStorage.setItem(SV_ADMIN_KEY,b.admin?'1':'0');
    localStorage.setItem(SV_TOKEN_KEY,b.token);
    // 이 PC 데이터 주인 확인: 다른 사용자 → 비우고 서버 데이터만 / 같은 사용자 → 그대로 맞춤 / 이 기기 첫 로그인 → 물어봄
    const prev=localStorage.getItem(SV_USER_KEY);
    const keep=prev?prev===b.user:(gdLocalEmpty()||!!b.rev||confirm('이 PC 데이터를 이 계정으로 올릴까요?\n[취소]를 누르면 이 PC 데이터는 지우고 빈 상태로 시작합니다.')); // b216: 서버에 이미 데이터가 있으면 묻지 않음 — 서버 값으로 덮어씀(gdSync)
    if(!keep){ svWipeLocal(); accId=''; }
    const same=!!prev&&prev===b.user&&keep; // b62: 같은 사용자로 다시 로그인(강제 로그아웃 등) → 마지막으로 맞춘 기준(base·rev) 유지 = 저장 안 한 변경도 3-way 병합
    localStorage.setItem(SV_USER_KEY,b.user); localStorage.setItem(SV_VAULT_KEY,b.vault||'none');
    gd.login={key,accId:accId||'',hashes:b.accounts||[],vault:b.vault||'none',subs:b.subKeys||[],mainBk:b.mainBk||'',mainBkLabel:b.mainBkLabel||''};
    const la=(accId&&accById(accId))||(keep?accounts().find(x=>x.key===key):null); // 등록된 키로 로그인: 첫 저장 전에 계정 해시(ah)를 붙여 둠 → 다른 기기에서 키 짝짓기
    if(la&&((b.accounts?.[0]&&!(b.accounts||[]).includes(la.ah))||(b.vault!=='locked'&&!la.main))){ if(b.accounts?.[0]&&!(b.accounts||[]).includes(la.ah)) la.ah=b.accounts[0]; if(b.vault!=='locked'){ accounts().forEach(x=>delete x.main); la.main=true; } save(); clearTimeout(gd.timer); gd.timer=null; }
    if(same&&localStorage.getItem(GD_BASE_KEY)) gdMeta={...gdMeta,on:true}; else { gdMeta={on:true}; localStorage.removeItem(GD_BASE_KEY); }
    gdSaveMeta(); gd.remoteRev=undefined; gd.fileId=null;
    await gdConnect(true);
    svAfterLogin();
    if(gd.state==='on') setTimeout(keySync,0); // b218: 본계정 키 등록(로그인) 직후 1번 동기화 — 서버에서 받은 캐릭터의 이번 주 기록
    if($('#importModal').classList.contains('show')) openImport(); // b67: 캐릭터 추가 창에서 로그인 → 평소 창(키 목록·캐릭터 목록)으로
    if(gd.state==='on') toast('☁ 로그인했습니다'+(b.newUser?' — 이 데이터를 서버에 저장합니다':''));
    svSeenPull();
  }catch(e){ if(e.code==='rejected'||e.code==='blocked') localStorage.removeItem(SV_PEND_KEY); // b68
    gd.svErr=e.code==='sub_key'?'이미 등록된 부계정 API입니다.':e.message; gdSet('off'); if($('#importModal').classList.contains('show')) svMainRender(); else if(!opt.quiet) gdMenu(true); }
}
function svWipeLocal(){ // 이 브라우저의 보스 데이터 비우기 (테마·기기 표·서버 주소는 유지)
  const th=S.theme; clearTimeout(gd.timer); gd.timer=null; localStorage.removeItem(GD_BASE_KEY); localStorage.removeItem(SV_SUBSIG_KEY);
  const d=defaultState(); d.theme=th; gdLoad(d); lastSig=contentSig(S);
}
/* b69: 공용 PC(PC방) — 로그아웃·세션 없음이면 이 사이트의 앱 데이터(localStorage·sessionStorage 의 mapleBossTracker.*)를 전부 지우고
 * 메모리 상태도 처음으로. 남기는 것: syncApi(테스트용 서버 주소), keepPending 이면 승인 대기 요청(svPending). 다른 탭은 storage 이벤트로 새로고침 */
const SV_KEEP_RE=/^mapleBossTracker\.(syncApi)$/;
function svWipeAll(o={}){
  svGen++; pend=null; clearTimeout(gd.timer); gd.timer=null; try{ clearTimeout(seenT); seenPush=new Set(); }catch(e){}
  gd.fileId=null; gd.remoteRev=undefined; gd.login=null; gd.pending=null; gd.busy=false; gd.again=false;
  const keepP=o.keepPending?localStorage.getItem(SV_PEND_KEY):null;
  for(const st of [localStorage,sessionStorage]){ try{ for(const k of Object.keys(st)) if(k.startsWith('mapleBossTracker.')&&!SV_KEEP_RE.test(k)) st.removeItem(k); }catch(e){} }
  if(keepP) localStorage.setItem(SV_PEND_KEY,keepP);
  try{ localStorage.setItem(KEY_RESET_K,KEY_RESET); }catch(e){} // (b64 키 초기화는 이미 비어 있으므로 다시 할 필요 없음)
  gdMeta={}; try{ feedSeen=new Set(); }catch(e){}
  S=normState(null); lastBody=bodyOf(); lastSig=contentSig(S); applyTheme();
  if(o.broadcast) try{ localStorage.setItem('mapleBossTracker.svLogout',String(Date.now())); localStorage.removeItem('mapleBossTracker.svLogout'); }catch(e){} // 다른 탭에 알림 (로그아웃·세션 끊김만 — 시작할 때 지우는 건 알리지 않음: 탭끼리 새로고침 반복 방지)
  try{ $('#adminModal')?.classList.remove('show'); gdMenu(false); }catch(e){}
  try{ render(); renderFeed(); }catch(e){}
}
// 다른 탭에서 로그아웃(또는 세션 만료로 초기화)하면 이 탭도 새로고침 → 시작할 때 세션이 없으니 빈 상태
addEventListener('storage',e=>{ if(typeof SV_ON!=='undefined'&&SV_ON&&e.key==='mapleBossTracker.svLogout'&&e.newValue) location.reload(); });
function svGate(){ // b67: 입장 화면(초대 비밀번호·대표 키) 폐지 — 바로 대시보드. 예전 화면이 남아 있으면 지움 (호출하는 곳 호환용)
  $('#svGate')?.remove(); document.documentElement.classList.remove('gated');
}
// 로그인에 쓴 키를 계정에 연결: 그 계정의 ah(서버 계정 해시) 기록 / 내려받은 데이터에서 같은 ah 계정에 키 채움 / 없으면 새 계정
function svAfterLogin(){
  const L=gd.login; if(!L||gd.state==='conflict') return; gd.login=null; let ch=false; // 질문 화면이면 고른 뒤(gdResolve)에 다시
  const hs=new Set(L.hashes), acc=accounts();
  const asMain=L.vault!=='locked';
  let a=(L.accId&&acc.find(x=>x.id===L.accId))||acc.find(x=>x.key===L.key)||acc.find(x=>x.ah&&hs.has(x.ah))||(asMain&&acc.find(x=>x.main))||acc.find(x=>!x.key&&x.label==='본계정');
  if(!a){ a={id:'a'+Date.now().toString(36),label:'본계정',key:L.key}; S.settings.accounts=[a,...acc]; ch=true; }
  if(a.key!==L.key){ a.key=L.key; ch=true; } // b72: 같은 넥슨 계정의 새 키 → 새 키가 본계정, 예전 키는 버림
  if(asMain){ // b72: 로그인한 대표 키 = 항상 1번 줄 '본계정'. 같은 계정(ah)·같은 키·예전 본계정 칸이 따로 있으면 합침(캐릭터 연결은 이 칸으로, 칸은 삭제 — 중복·'계정N' 줄 없음)
    if(a.label!=='본계정'){ a.label='본계정'; ch=true; }
    for(const x of accounts().slice()){ if(x===a) continue;
      if(x.key===L.key||(x.ah&&hs.has(x.ah))||x.main){
        S.characters.forEach(c=>{ if(c.accId===x.id) c.accId=a.id; });
        if(x.bk&&!a.bk&&x.bk!==L.key){ a.bk=x.bk; if(x.bkLabel) a.bkLabel=x.bkLabel; }
        if(!a.ah&&x.ah) a.ah=x.ah;
        S.settings.accounts=accounts().filter(y=>y!==x); ch=true; } }
    if(accounts()[0]!==a){ S.settings.accounts=[a,...accounts().filter(y=>y!==a)]; ch=true; }
  }
  if(L.hashes[0]&&a.ah!==L.hashes[0]&&!hs.has(a.ah)){ a.ah=L.hashes[0]; ch=true; }
  if(L.vault!=='locked'){ for(const x of accounts()) if(!!x.main!==(x===a)){ x.main=x===a||undefined; if(!x.main) delete x.main; ch=true; } } // 대표 키 = 로그인에 쓴 키 (부계정 키로 로그인하면 그대로)
  let back=0;
  for(const sub of L.subs||[]){ // 대표 키로 로그인 → 서버가 풀어 준 부계정 키 채우기
    if(!sub?.key||sub.key===a.key||(sub.ah&&hs.has(sub.ah))) continue; // b72: 예전 본계정 키가 부계정으로 남아 있던 것은 버림
    const ac=accounts(), x=ac.find(y=>y.key===sub.key)||ac.find(y=>!y.key&&sub.ah&&y.ah===sub.ah)||ac.find(y=>!y.key&&!y.main&&!y.ah&&sub.label&&y.label===sub.label); // b64: ah 가 없는 예전 칸은 이름으로
    if(x){ if(!x.key){ x.key=sub.key; ch=true; back++; } if(sub.ah&&!x.ah){ x.ah=sub.ah; ch=true; } }
    else { S.settings.accounts=[...ac,{id:'a'+Date.now().toString(36)+ac.length,label:sub.label||`부계정${ac.length}`,key:sub.key,...(sub.ah?{ah:sub.ah}:{})}]; ch=true; back++; }
  }
  if(back) toast(`부계정 키 ${back}개를 불러왔습니다`);
  accounts().forEach(x=>{ if(x.bk||x.bkLabel){ delete x.bk; delete x.bkLabel; ch=true; } }); // b74: 예비 키 버림
  const vaultBk=!!(L.mainBk||(L.subs||[]).some(x=>x&&x.bk)); if(vaultBk) svBkPurge=true; // b74: 금고에 예비 키가 남아 있으면 아래에서 다시 올려(예비 키 없이) 지움
  // b62: 서버 금고에 이 PC 의 키가 전부 있을 때만 '맞춤'으로 표시 (예전엔 금고가 열리기만 하면 맞춤 처리 → 이 PC 에만 있던 키가 영영 안 올라감)
  const vset=new Set([L.key,L.mainBk,...(L.subs||[]).flatMap(x=>[x.key,x.bk])].filter(Boolean));
  const lset=accounts().flatMap(x=>[x.key,x.bk]).filter(Boolean);
  if(L.vault==='open'&&!vaultBk&&lset.every(k=>vset.has(k))&&accounts().filter(x=>x.key&&!x.main).length===(L.subs||[]).length) localStorage.setItem(SV_SUBSIG_KEY,svSubSig());
  else if(L.vault==='open') localStorage.removeItem(SV_SUBSIG_KEY);
  if(ch){ save(); render(); }
  if(svMain()&&svSubSig()!==localStorage.getItem(SV_SUBSIG_KEY)) svSyncSubKeys().then(()=>gdRender()).catch(()=>{});
}
const svMain=()=>accounts().find(a=>a.main&&a.key)||null;
const svSubSig=()=>{ const m=svMain(); if(!m) return ''; const j=JSON.stringify([m.key,m.bk||'',m.bkLabel||'',...accounts().filter(a=>a.key&&a!==m&&a.key!==m.key).map(a=>[a.key,a.label,a.bk||'',a.bkLabel||''])]);
  let h1=0x811c9dc5,h2=0x9e3779b9; for(let i=0;i<j.length;i++){ const c=j.charCodeAt(i); h1=Math.imul(h1^c,16777619); h2=Math.imul(h2^c,2246822519); } return 'h'+(h1>>>0).toString(36)+(h2>>>0).toString(36)+j.length; }; // b95: 키 원본이 localStorage 에 남지 않게 해시만
// 부계정 키를 서버 금고에 (대표 키로 암호화) — 바뀌었을 때만. 대표 키가 이 기기에 없으면 예전처럼 연결만.
let svBkPurge=false; // b74: 금고의 예비 키를 지우려고 한 번 다시 올려야 함
async function svSyncSubKeys(){
  const m=svMain(); if(!m) return svLinkNewKeys();
  const sig=svSubSig(); if(sig===localStorage.getItem(SV_SUBSIG_KEY)) return svLinkNewKeys();
  if(localStorage.getItem(SV_VAULT_KEY)==='locked') return svLinkNewKeys(); // b62: 이 기기는 금고 내용을 모름(대표 계정이 아닌 키로 로그인) → 금고를 덮어쓰지 않음
  const subs=accounts().filter(a=>a.key&&a!==m&&a.key!==m.key);
  if(!subs.length&&!m.bk&&!svBkPurge&&!localStorage.getItem(SV_SUBSIG_KEY)){ localStorage.setItem(SV_SUBSIG_KEY,sig); return; } // 부계정 키가 처음부터 없으면 서버에 올릴 것 없음
  try{
    const r=await svFetch('/api/subkeys',{method:'PUT',body:{main:m.key,...(m.bk?{mainBk:m.bk,...(m.bkLabel?{mainBkLabel:m.bkLabel}:{})}:{}),subs:subs.map(a=>({key:a.key,label:a.label,...(a.bk?{bk:a.bk,...(a.bkLabel?{bkLabel:a.bkLabel}:{})}:{})}))}});
    let ch=false; (r.subs||[]).forEach((x,i)=>{ const a=subs[i]; if(a&&x.ah&&a.ah!==x.ah){ a.ah=x.ah; ch=true; } });
    svBkPurge=false; localStorage.setItem(SV_SUBSIG_KEY,sig); localStorage.setItem(SV_VAULT_KEY,'open'); localStorage.removeItem(SV_KEYERR_KEY);
    if(ch){ S.updatedAt=Date.now(); lastSig=contentSig(S); lastBody=bodyOf(); localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(S)); }
  }catch(e){ if(e.type==='interaction_required') throw e;
    // b62: 실패하면 '맞춤'으로 표시하지 않음 (예전: 실패해도 맞춤 처리 → 다시 안 올림 = 다른 PC 에서 키가 사라지던 원인 중 하나). 다음 저장/키 변경 때 다시 시도
    localStorage.setItem(SV_KEYERR_KEY,String(e.message||e).slice(0,200)); toast('⚠ 부계정·예비 키를 서버에 보관하지 못했어요: '+e.message); }
}
// b62: 키를 추가·삭제하면 (저장 버튼과 무관하게) 2초 뒤 금고에 보관
let svKeysT=null;
function svKeysSoon(){ if(!SV_ON||!svTok()||!gdMeta.on||!svMain()||!['open','none'].includes(localStorage.getItem(SV_VAULT_KEY))) return; // b62 로그인(금고 상태 기록)한 기기만 if(svSubSig()===localStorage.getItem(SV_SUBSIG_KEY)) return;
  clearTimeout(svKeysT); svKeysT=setTimeout(()=>{ svSyncSubKeys().then(()=>gdRender()).catch(()=>{}); },2000); }
async function svAddSub(key){
  key=String(key||'').trim(); if(!key) return toast('부계정 API 키를 넣어 주세요');
  const ac=accounts(); if(ac.some(a=>a.key===key)) return toast('이미 등록된 키입니다');
  const ex=ac.find(a=>!a.key&&!a.main);
  if(ex) ex.key=key; else S.settings.accounts=[...ac,{id:'a'+Date.now().toString(36),label:`부계정${ac.filter(a=>!a.main).length+1}`,key}];
  save(); render(); gdMenu(true); await gdPush({manual:true}); gdMenu(true);
}
// 로그인한 상태에서 새로 등록한 다른 넥슨 계정 키를 같은 데이터에 연결 (그 키로 로그인해도 이 데이터가 열리게)
async function svLinkNewKeys(){
  gd.linkTried=gd.linkTried||new Set(); let ch=false;
  for(const a of accounts()){
    if(!a.key||a.ah||gd.linkTried.has(a.id+':'+a.key)) continue; gd.linkTried.add(a.id+':'+a.key);
    try{ const r=await svFetch('/api/link',{method:'POST',body:{key:a.key}}); if(r.accounts?.[0]){ a.ah=r.accounts[0]; ch=true; } }
    catch(e){ if(e.type==='interaction_required') throw e; toast(`'${a.label}' 키 연결: ${e.message}`); }
  }
  if(ch){ S.updatedAt=Date.now(); lastSig=contentSig(S); lastBody=bodyOf(); localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(S)); }
}
// 예전 구글 드라이브 저장본을 한 번 가져와 이 PC 데이터와 합침 → 서버에 저장 (클릭 시 구글 로그인 창 1번)
async function svImportDrive(){
  gd.ia=true;
  try{
    gdSet('saving','구글 드라이브 저장본 확인 중… (구글 로그인 창에서 허용)');
    await driveToken(true);
    const f=await driveFind(); if(!f){ gdSet('on','구글 드라이브에 저장본이 없습니다'); toast('구글 드라이브에 저장본이 없습니다'); return; }
    const remote=await driveRead(f.id);
    if(!remote?.data||!Array.isArray(remote.data.characters)) throw new Error('드라이브 파일 형식이 올바르지 않습니다');
    const rU=+remote.updatedAt||0, lU=S.updatedAt||0;
    let m;
    if(gdLocalEmpty()) m=gdPrep(remote.data);
    else { const ctx={base:false,prefer:rU>lU?'r':'l',conf:[]}; m=gdMerge(null,gdPrep(backupData(true)),gdPrep(remote.data),ctx); } // 겹치는 값은 최근 수정한 쪽
    m.updatedAt=Date.now(); gdLoad(m); lastSig=contentSig(S);
    await gdPush({manual:true});
    const msg=`구글 드라이브 저장본(캐릭터 ${remote.data.characters.length}명)을 합쳐 서버에 저장했습니다`; gdSet('on',msg); toast('☁ '+msg);
    try{ if(gd.token&&window.google?.accounts?.oauth2?.revoke) google.accounts.oauth2.revoke(gd.token,()=>{}); }catch(e){}
    gd.token=null; gd.exp=0; sessionStorage.removeItem(GD.TOKEN_KEY);
  }catch(e){ const info=gdErrInfo(e); gdSet('on',info?info.short:e.message); if(info) gdHelpModal(info.html); }
  finally{ gd.ia=false; }
}
// 서버 모드: 저장 안 한 변경 (dirty) = 이 PC 수정 시각 ≠ 마지막으로 서버와 맞춘 시각
function svUnsaved(){ return SV_ON&&!!svTok()&&gdMeta.on&&(gdLocalDirty()||!!pend); }
// 수동 저장 (나중에 [저장] 버튼은 이것만 부르면 됨) → true/false
async function svSaveNow(quiet){ const ok=await gdPush({manual:true}); if(ok&&!quiet) toast('☁ 서버에 저장했습니다'); gdRender(); return ok; }
function svAsk(msg,btns,head=''){ return new Promise(res=>{
  const d=document.createElement('div'); d.id='svAsk'; d.className='svask';
  d.innerHTML=`<div class="svaskbox">${head}<div class="svaskmsg">${esc(msg)}</div><div class="svaskbtns">${btns.map(([k,t],i)=>`<button class="btn sm${i?' ghost':''}" data-k="${k}">${esc(t)}</button>`).join('')}</div></div>`;
  d.addEventListener('click',e=>{ const b=e.target.closest('[data-k]'); if(b||e.target===d){ e.stopPropagation(); d.remove(); res(b?b.dataset.k:'cancel'); } });
  if(head) d.classList.add('svaskc');
  document.body.appendChild(d); d.querySelector('[data-k]')?.focus();
}); }
async function gdLogout(o={}){ // 로그아웃만 (이 브라우저 데이터는 그대로 둠 — PC방은 종료 시 자동 초기화)
  if(SV_ON){ // b69: ① 세션이 살아 있으면 남은 변경(저장 안 한 체크·키·읽음)을 먼저 서버에 저장 ② 서버 세션 삭제 ③ 이 PC 의 앱 데이터 전부 삭제 → 처음 온 사람 상태
    if(svTok()&&gdMeta.on&&gd.state!=='conflict'){
      try{ if(pend){ pend=null; save(); } }catch(e){}
      try{ if(gd.timer||gdLocalDirty()){ clearTimeout(gd.timer); gd.timer=null; await gdPush({manual:true}); } }catch(e){}
      try{ if(svTok()&&localStorage.getItem(SV_SUBSIG_KEY)!==svSubSig()) await svSyncSubKeys(); }catch(e){}
      try{ clearTimeout(seenT); await svSeenFlush(); }catch(e){}
    }
    try{ sessionStorage.removeItem('mapleBossTracker.admUsers'); admUsers=null; }catch(e){}
    try{ if(svTok()) await svFetch('/api/logout',{method:'POST',noGen:true}); }catch(e){} // b235: 본계정 로그아웃 = 그냥 로그아웃 (삭제 타이머와 무관)
    svWipeAll({broadcast:true}); gd.svErr=''; gdSet('off'); render(); svGate(); toastHide(); return; // b73: 직접 로그아웃 = 알림 없음 (저장 중 뜬 알림도 지움)
  }
  if(gdMeta.on && gdLocalDirty()){
    const ok=gdHasTok() ? await gdPush() : false;
    if(!ok && !confirm('드라이브에 최신 내용을 저장하지 못했습니다. 그래도 로그아웃할까요? (이 PC에는 그대로 남아 있고, 다음 로그인 때 다시 맞춥니다)')) return;
  }
  try{ if(gd.token&&window.google?.accounts?.oauth2?.revoke) google.accounts.oauth2.revoke(gd.token,()=>{}); }catch(e){}
  clearTimeout(gd.timer); gd.timer=null; gd.token=null; gd.exp=0; gd.fileId=null; sessionStorage.removeItem(GD.TOKEN_KEY);
  gdMeta={}; localStorage.removeItem(GD.META_KEY); localStorage.removeItem(GD_BASE_KEY);
  gdSet('off'); render(); toastHide(); // b73
}

/* =====================================================================
 *  이벤트
 * ===================================================================== */
function syncTabs(){ document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('on',b.dataset.tab===tab)); }
document.addEventListener('click',e=>{
  const wtb=e.target.closest('[data-wtab]'); if(wtb){ if(Date.now()-dndEndAt>350 && wtb.dataset.wtab!==worldTab) setWorldTab(wtb.dataset.wtab); return; }
  const cso=e.target.closest('[data-csort]'); if(cso){ if(cso.dataset.csort!==charSort) setCharSort(cso.dataset.csort); return; }
  const rc=e.target.closest('[data-ring]'); if(rc){ chooseRing(rc.dataset.ring); return; }
  if(e.target.closest('#ringClose')||e.target.id==='ringModal'){ closeRing(); return; }
  if(e.target.closest('#congrats')){ endCelebrate(); return; }
  const dd=e.target.closest('[data-dropdec]'); if(dd){ e.stopPropagation(); changeDrop(dd.dataset.dropdec,-1); return; }
  const dm=e.target.closest('[data-dropmore]'); if(dm){ const id=dm.dataset.dropmore; dropOpen.has(id)?dropOpen.delete(id):dropOpen.add(id); render(); return; }
  const rr=e.target.closest('[data-rred]'); if(rr){ openRred(rr.dataset.rred); return; } // b229
  const dc=e.target.closest('[data-drop]'); if(dc){ changeDrop(dc.dataset.drop,+1); return; }
  if(e.target.closest('.drop.erda')) return; // 솔 에르다의 기운: 정보 표시 전용 (클릭해도 아무 일 없음)
  const svl=e.target.closest('[data-svlogin]'); if(svl){ const a=accById(svl.dataset.svlogin); if(a&&a.key) svLogin(a.key,a.id); return; }
  const t=e.target.closest('[data-cpage],[data-tab],[data-move],[data-wmove],[data-id],[data-edit],[data-filter],[data-check],[data-toggle],[data-setdiff],[data-delhist],[data-acctest],[data-accdel],button[id]');
  if(!t) return;
  const c=activeChar();
  if(t.dataset.tab){ const go=()=>{ if(tab!==t.dataset.tab){ TIR_LAST.clear(); TSV_SEEN.clear(); } /* b173: 탭 복귀 시 디지털 숫자 다시 카운팅 */ const sw=tab!==t.dataset.tab; tab=t.dataset.tab; try{ localStorage.setItem(TAB_KEY,tab); }catch(e){} syncTabs(); render(); if(sw) tabTop(); tabTick(); };
    // 저장 안 한 변경이 있으면 탭 이동 전에 묻기: 예 = 저장 후 이동 / 아니오 = 스냅샷으로 되돌리고 이동 / 닫기 = 머무름
    if(pend&&t.dataset.tab!==tab){ pendGuard(go); return; }
    go(); return; }
  if(t.dataset.cpage){ charPage=+t.dataset.cpage; renderChars(); return; }
  if(t.dataset.move){ e.stopPropagation(); const [id,d]=t.dataset.move.split('|'); moveCharBy(id,+d); render(); return; }
  if(t.dataset.wmove){ e.stopPropagation(); const i=t.dataset.wmove.lastIndexOf('|'); moveWorldBy(t.dataset.wmove.slice(0,i),+t.dataset.wmove.slice(i+1)); render(); return; }
  if(e.target.closest('.drag-h')) return;
  if(t.dataset.edit){ e.stopPropagation(); openCharModal(t.dataset.edit); return; }
  if(t.dataset.id){ const id=t.dataset.id; if(pend&&id!==S.activeId) return pendGuard(()=>{ S.activeId=id; save(); const sw=toBossTab(); render(); if(sw){ tabTop(); tabTick(); } });
    const sy=scrollY, sx=scrollX; S.activeId=id; save(); const sw=toBossTab(); render(); if(sw){ tabTop(); tabTick(); return; } // b213: 다른 탭에서 → 이번 주 보스 = 맨 위
    { const back=()=>{ if(scrollY!==sy||scrollX!==sx) scrollTo(sx,sy); }; back(); requestAnimationFrame(back); setTimeout(back,80); } return; } // b189: 보스 탭에서 캐릭터 클릭 = 스크롤 그대로
  if(t.dataset.filter){ bossFilter=t.dataset.filter; render(); return; }
  if(t.dataset.toggle && c){ const s=t.dataset.toggle,b=findBoss(s);
    if(b.type==='weekly'&&!c.bosses[s]?.enabled&&weeklyFull(c)){ if(c.bossNext?.[s]) delete c.bossNext[s]; else bossNextPut(c,b,{enabled:true,diff:c.bosses[s]?.diff||b.diffs[0]}); save(); render(); toast('이번 주 주간 보스 12개를 다 잡아서 목요일 초기화 때 적용돼요'); return; } // b241
    const cfg=c.bosses[s]||(c.bosses[s]={enabled:false,diff:b.diffs[0],party:1}); cfg.enabled=!cfg.enabled; save(); render(); return; }
  if(t.dataset.setdiff && c){
    if(t.classList.contains('locked')){toast('클리어 체크를 해제한 뒤 난이도를 바꾸세요');return;}
    const [s,d]=t.dataset.setdiff.split('|'); const cfg=c.bosses[s]||(c.bosses[s]={enabled:editMode,diff:d,party:1});
    cfg.diff=d; clampParty(c,s); save(); render(); return;
  }
  if(t.dataset.check && c){
    const s=t.dataset.check,b=findBoss(s);
    if(b.type==='weekly'){
      if(c.weekly[s]){ delete c.weekly[s]; delete c.auto[s]; }
      else { if(weeklyCount(c)>=S.settings.weeklyLimit){ toast(`주간 보스는 캐릭터당 ${S.settings.weeklyLimit}개까지 처치할 수 있습니다`); return; } c.weekly[s]=true; (c.wat||(c.wat={}))[s]=Date.now(); }
    } else {
      if(c.monthly[s]){ delete c.monthly[s]; if(c.mdate) delete c.mdate[s]; delete c.auto[s]; }
      else { if(monthlyCount(c)>=S.settings.monthlyLimit){ toast(`월간 보스는 월 ${S.settings.monthlyLimit}회까지입니다`); return; } c.monthly[s]=S.period.week; (c.mdate||(c.mdate={}))[s]=kstDay(); }
    }
    save(); render(); return;
  }
  if(t.dataset.acctest){ if(e.target.closest('input')) return; const a=accById(t.dataset.acctest); if(a&&a.key) openImport(a.id); return; }
  if(t.dataset.accdel){ const a=accById(t.dataset.accdel); if(!a) return; const n=S.characters.filter(c=>c.accId===a.id).length;
    // b95: 삭제 = API 키(예비 키 포함)만 완전히 지움. 계정 칸(ah = 넥슨 계정 해시)·캐릭터 연결은 남겨 기록은 숨김 → 같은 넥슨 계정 키를 다시 넣으면 그대로 다시 보임.
    //   대표 키 삭제 = 부계정 키도 전부 삭제. 서버의 키 보관·부계정 연결도 /api/unlink 로 지움.
    const all=!!a.main||(!accounts().some(x=>x.main)&&accounts()[0]===a), tgt=all?accounts():[a]; // main 표시 없는 예전 데이터 = 첫 줄이 대표
    if(confirm(all?`'${a.label}' 대표 계정에서 로그아웃할까요?\n모든 부계정도 함께 로그아웃됩니다. 캐릭터 기록은 그대로 남고, 같은 계정 키로 다시 로그인하면 그대로 다시 보입니다.`
      :`'${a.label}' 계정의 API 키를 삭제할까요?\n캐릭터 기록은 지워지지 않고 숨겨지며, 같은 계정 키를 다시 등록하면 다시 보입니다.`)){ // b235: 본계정 = 로그아웃 버튼 (삭제 타이머 없음 — 기록 삭제는 30일 동안 🔄 캐릭터 동기화를 안 눌렀을 때만)
      if(SV_ON&&all){ // b219: 서버 모드에서 대표 키 삭제는 어떤 상태에서도 /api/unlink {all} 을 보내지 않음(부계정 키 금고가 지워졌음)
        if(!svTok()){ $('#importModal').classList.remove('show'); svWipeAll(); render(); return; } // b216: 본계정(대표) 키 삭제 = 이 브라우저만 처음 온 사람 상태(로그아웃·이 PC 데이터 비움 → 예시 화면·API 키 등록 카드).
        // 서버 기록(데이터·부계정 키 금고·계정 연결)은 지우지 않음 → 같은 본계정 키를 다시 등록하면 본캐·부캐 캐릭터·기록이 그대로 돌아옴
        $('#importModal').classList.remove('show'); gdLogout(); return; } // b235: 본계정 로그아웃 (서버 데이터·부계정 키 금고 유지, 부계정도 함께 로그아웃)
      const body=all?{all:true}:{key:a.key,bk:a.bk,ah:a.ah,ahs:a.ahs};
      tgt.forEach(x=>{ x.key=''; delete x.bk; delete x.bkLabel; delete x.status; if(listCache[x.id]) delete listCache[x.id]; });
      accForget(tgt.filter(x=>!x.main&&!(all&&x===accounts()[0]&&!accounts().some(y=>y.main)))); // b102: 부계정 칸은 통째로 지움 (본계정 칸만 남겨 b72 처럼 다시 넣으면 보이게)
      localStorage.removeItem(SV_SUBSIG_KEY); if(impAccId===a.id||all){ impAccId=null; accChars=[]; }
      if(SV_ON&&svTok()) svFetch('/api/unlink',{method:'POST',body}).catch(e=>toast('⚠ 서버의 키 연결을 지우지 못했어요: '+e.message));
      save(); render(); if($('#importModal').classList.contains('show')) openImport(); } return; }
  if(t.dataset.delhist){ if(confirm('이 주간 기록을 삭제할까요?')){ S.history=S.history.filter(h=>h.week!==t.dataset.delhist); save(); render(); } return; }
  switch(t.id){
    case 'editModeBtn': editMode=!editMode; render(); break;
    case 'syncBtn': syncAll(); break; // b236: 30일 타이머는 syncAll 이 끝날 때(syncPressMark)
    case 'importAccBtn': openImport(); break;
    case 'impRetry': openImport(impAccId); break;
    case 'impToSettings': accAddShow(true); break;
    case 'accAddOpen': accAddShow(true); break;
    case 'accAddCancel': accAddShow(false); break;
    case 'impClear': $('#impMin').value=''; $('#impQ').value=''; $('#impWorld').value=''; renderImportList(); break;
    case 'newAccBtn': addAccount(); break;
    case 'impClose': closeImport(); break;
    case 'gMenuClose': gdMenu(false); break;
    case 'gBtn': gdHeaderClick(); break;
    case 'svWarn': svSaveNow(); break;
    case 'pendCancel': if(pend) pendAsk(); break;
    case 'pendSave': pendSave(); break;
    case 'revAllBtn': openRevAll(); break;
    case 'gdLogin': gdLogin(); break;
    case 'svSubBtn': svAddSub($('#svSubKey')?.value); break;
    case 'svMainBtn': svLogin($('#svMainKey')?.value); break;
    case 'svPendCheck': { const pd=svPend(); if(pd?.key) svLogin(pd.key); break; }
    case 'svPendCancel': localStorage.removeItem(SV_PEND_KEY); gd.svErr=''; gdRender(); svMainRender(); break;
    case 'svAdminBtn': gdMenu(false); openAdmin(); break;
    case 'admClose': $('#adminModal').classList.remove('show'); break;
    case 'svLoginBtn': svLogin($('#svKey')?.value); break;
    case 'svImportDrive': gdMenu(false); svImportDrive(); break;
    case 'gdLogout': gdLogout(false); break;
    case 'gdSaveNow': gdPush({manual:true}); break;
    case 'gdUseDrive': gdResolve('drive'); break;
    case 'gdUseLocal': gdResolve('local'); break;
    case 'gdClose': $('#driveModal').classList.remove('show'); break;
  }
});
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ if($('#ringModal').classList.contains('show')) closeRing(); if(celebrate.running) endCelebrate(); if($('#importModal').classList.contains('show')&&!$('#charModal').classList.contains('show')) closeImport(); $('#adminModal')?.classList.remove('show'); gdMenu(false); } });
document.addEventListener('keydown',e=>{ const wt=e.target.closest?.('[data-wtab]'); if(wt&&(e.key==='Enter'||e.key===' ')){ e.preventDefault(); if(wt.dataset.wtab!==worldTab) setWorldTab(wt.dataset.wtab); } });
document.addEventListener('contextmenu',e=>{ const dc=e.target.closest('[data-drop]'); if(!dc) return; e.preventDefault(); if(tipTouchAt&&Date.now()-tipTouchAt<1500) return; /* 터치 길게 누르기 = 툴팁 보기 (취소는 − 버튼) */ changeDrop(dc.dataset.drop,-1); });
/* 드롭 칩 툴팁 (마우스 올림 + 터치): [data-tip] — 터치는 누르는 순간 표시(클릭 동작은 그대로), 3초 뒤·다른 곳 터치 시 닫힘 */
let tipEl=null, tipFor=null, tipTimer=0, tipTouchAt=0;
function tipShow(el){
  if(!tipEl){ tipEl=document.createElement('div'); tipEl.id='mbtTip'; tipEl.setAttribute('role','tooltip'); document.body.appendChild(tipEl); }
  tipFor=el; const [h0,...rest]=String(el.dataset.tip).split('\n'); // 첫 줄 = 굵은 제목(아이템 이름)
  tipEl.classList.toggle('rich',!!el.dataset.tiphtml); tipEl.classList.toggle('ctip',!!el.closest?.('.chart.lux')); // b138
  if(el.dataset.tiphtml) tipEl.innerHTML=el.dataset.tiphtml; /* b111: 아이콘 있는 말풍선 — 우리 코드가 만든 HTML(chaosTip)만 넣음 */ else tipEl.replaceChildren(Object.assign(document.createElement('b'),{className:'tth',textContent:h0}),...(rest.length?['\n'+rest.join('\n')]:[])); tipEl.classList.add('show');
  const r=((el.classList?.contains('whit')&&el.parentNode.querySelector('circle.wdot'))||el.querySelector?.('[data-tipanchor]')||el).getBoundingClientRect(), /* b211: 넓힌 점 범위 → 말풍선은 점 위에 */ w=tipEl.offsetWidth, h=tipEl.offsetHeight, m=8;
  let x=Math.min(Math.max(m,r.left+r.width/2-w/2),innerWidth-w-m), y=r.top-h-10, below=false; if(y<m){ y=Math.min(r.bottom+10,innerHeight-h-m); below=true; }
  tipEl.classList.toggle('below',below); tipEl.style.setProperty('--ax',Math.min(Math.max(14,r.left+r.width/2-x),w-14)+'px');
  tipEl.style.left=x+'px'; tipEl.style.top=y+'px';
}
function tipHide(){ clearTimeout(tipTimer); tipFor=null; if(tipEl) tipEl.classList.remove('show'); }
document.addEventListener('pointerover',e=>{ if(e.pointerType==='touch') return; const t=e.target.closest?.('[data-tip]'); if(t&&(t!==tipFor||!tipEl?.classList.contains('show'))) tipShow(t); else if(!t&&tipFor) tipHide(); });
document.addEventListener('pointerdown',e=>{ const t=e.target.closest?.('[data-tip]');
  if(e.pointerType==='touch'){ tipTouchAt=t?Date.now():0; if(t){ tipShow(t); clearTimeout(tipTimer); tipTimer=setTimeout(tipHide,3000); } else tipHide(); } },true);
let tipKbd=false; // 키보드(Tab)로 칩에 왔을 때만 포커스로 표시/숨김 — 클릭·터치 뒤 다시 그려질 때 툴팁이 사라지지 않게
document.addEventListener('keydown',e=>{ if(e.key==='Tab') tipKbd=true; },true);
document.addEventListener('keydown',e=>{ if(e.key==='Enter'&&e.target.id==='svMainKey'){ e.preventDefault(); svLogin(e.target.value); return; } if(e.key==='Enter'&&e.target.id==='svKey'){ e.preventDefault(); svLogin(e.target.value); } if(e.key==='Enter'&&e.target.id==='svSubKey'){ e.preventDefault(); svAddSub(e.target.value); } });
document.addEventListener('pointerdown',()=>{ tipKbd=false; },true);
document.addEventListener('focusin',e=>{ if(!tipKbd) return; const t=e.target.closest?.('[data-tip]'); if(t) tipShow(t); });
document.addEventListener('focusout',()=>{ if(tipKbd) tipHide(); });
addEventListener('scroll',()=>{ if(tipFor&&tipFor.isConnected&&tipEl.classList.contains('show')) tipShow(tipFor); },true); // 스크롤하면 위치만 다시 맞춤
document.addEventListener('keydown',e=>{ const dc=e.target.closest?.('[data-drop]'); if(!dc) return; if(e.key==='Enter'||e.key===' '){ e.preventDefault(); changeDrop(dc.dataset.drop,+1); } else if(e.key==='Backspace'||e.key==='Delete'||e.key==='-'){ e.preventDefault(); changeDrop(dc.dataset.drop,-1); } });
document.addEventListener('change',e=>{
  const t=e.target; const c=activeChar();
  if(t.dataset.party && c){ const s=t.dataset.party; pendStart(); c.bosses[s].party=parseInt(t.value)||1; clampParty(c,s); save(); render(); }
  if(t.id==='impWorld') renderImportList();
  if(t.dataset.acclabel){ const a=accById(t.dataset.acclabel); if(a&&!t.value.trim()) return; /* b72: 비워 두면 예전 이름 유지 (빨간 글은 등록 버튼을 눌렀을 때만) */ if(a){ a.label=t.value.trim()||a.label; save(); render(); if(a.id===impAccId) $('#impTitle').textContent=`'${a.label}' 계정 캐릭터`; } }
});
$('#ricR').innerHTML=miniIcon('ring_restraint'); $('#ricC').innerHTML=miniIcon('ring_continuous'); $('#ricG').innerHTML=miniIcon('g_life');
$('#impMin').addEventListener('input',renderImportList); $('#impQ').addEventListener('input',renderImportList);
$('#fAcc').addEventListener('change',()=>loadPick());
$('#fName').addEventListener('input',()=>{ if(lookup&&lookup.name&&$('#fName').value.trim()!==lookup.name) lookup=null; renderPick(); });
$('#fPickWrap').addEventListener('click',e=>{ const b=e.target.closest('[data-pick]'); if(b&&!b.disabled){ pickChar(b.dataset.pick); return; } if(e.target.closest('#fPickRetry,#fPickReload')) loadPick(true); });
$('#impAll').onclick=()=>{ const boxes=[...document.querySelectorAll('#impList input:not(:disabled)')]; const all=boxes.every(b=>b.checked); boxes.forEach(b=>b.checked=!all); };
$('#impOk').onclick=doImport;
$('#importModal').addEventListener('click',e=>{ if(e.target.id==='importModal') closeImport(); });
$('#newAccKey').addEventListener('keydown',e=>{ if(e.key==='Enter') addAccount(); });
document.addEventListener('click',e=>{ const m=$('#gMenu'); if(m&&!m.hidden&&!e.target.closest('.gwrap')&&!e.target.closest('#driveModal')) gdMenu(false); });
$('#addCharBtn').onclick=()=>openAdd();
$('#fCancel').onclick=closeCharModal; $('#fSave').onclick=saveChar; $('#fDelete').onclick=deleteChar; $('#fLookup').onclick=lookupByName;
$('#charModal').addEventListener('click',e=>{ if(e.target.id==='charModal') closeCharModal(); });
$('#driveModal').addEventListener('click',e=>{ if(e.target.id==='driveModal') e.target.classList.remove('show'); }); // b110: 모든 가운데 창 — 바깥 클릭 = 닫기/취소
document.addEventListener('keydown',e=>{ if(!$('#charModal').classList.contains('show')) return; if(e.key==='Escape') closeCharModal(); if(e.key==='Enter'&&e.target.id!=='fName') saveChar(); if(e.key==='Enter'&&e.target.id==='fName') (hasApi()?lookupByName():saveChar()); });

// 드라이브 저장용 직렬화 (withKeys=true: API 키 포함 / false: 비교용, 키 제외)
function backupData(withKeys){
  const data=JSON.parse(JSON.stringify(S)); delete data.settings.apiKey;
  data.settings.accounts=(data.settings.accounts||[]).map(a=>({id:a.id,label:a.label,...(a.ah?{ah:a.ah}:{}),...(a.main?{main:true}:{}),...(a.bkLabel?{bkLabel:a.bkLabel}:{}),...(withKeys?{key:a.key||'',...(a.bk?{bk:a.bk}:{})}:{})})); // ah: 동기화 서버 계정 해시(키 아님)
  return data;
}
// 드라이브 데이터 적용: 데이터에 키가 없으면 이 브라우저의 키를 계정 id 기준으로 다시 연결하고, 없는 계정은 유지
function applyData(d){
  d.settings=d.settings||{}; const cur=accounts();
  const acc=(Array.isArray(d.settings.accounts)?d.settings.accounts:[]).map(a=>{ const o=cur.find(x=>x.id===a.id), bk=a.bk||o?.bk; return {...a,key:a.key||o?.key||'',...(bk?{bk}:{})}; });
  cur.forEach(x=>{ if(!acc.some(a=>a.id===x.id)) acc.push(x); }); d.settings.accounts=acc;
  localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(d)); load(); checkResets(); save(); applyTheme(); render();
}

/* =====================================================================
 *  시작
 * ===================================================================== */
/* b217: 시작 렌더 보호 — 렌더 오류로 스크립트가 멈추면 body.html 의 빈 뼈대(예전 헤더 문구·빈 칸)만 남았음 */
document.documentElement.dataset.build='b234'; // 배포 확인용 (개발자 도구: document.documentElement.dataset.build)
function bootRender(where){ try{ render(); }catch(e){ console.error('render@'+where,e); } try{ gdRender(); }catch(e){ console.error('gdRender@'+where,e); } }
$('#jobList').innerHTML=JOBS.map(j=>`<option value="${j}">`).join('');
$('#worldList').innerHTML=WORLDS.map(j=>`<option value="${j}">`).join('');
load();
if(S.theme!=null) S.theme=null; // b67: 예전에 저장된 테마(라이트/다크) 선택 삭제 — 항상 다크
/* b64 (2026-10-12): 등록된 API 키 전체 초기화 (사용자 요청) — 서버 모드 기기마다 이 버전을 처음 열 때 한 번:
 *  이 기기에 저장된 대표·부계정·예비 키(settings.accounts[].key/bk/bkLabel)만 비움. 계정 칸(id·이름·ah)과 캐릭터·기록·수익 등은 그대로.
 *  금고 상태 표시도 지우고, 키가 있던 기기는 세션도 지워 대표 키로 다시 로그인하게 함(같은 사용자 → 저장 안 한 변경 유지·3-way 병합).
 *  서버 금고(keyvault2)·등록부(keyreg)는 같은 날 운영자가 D1 에서 지움. 다시 초기화하려면 KEY_RESET 값을 바꿔 배포. */
const KEY_RESET='b64-2026-10-12', KEY_RESET_K='mapleBossTracker.keyReset';
try{ if(SV_ON&&localStorage.getItem(KEY_RESET_K)!==KEY_RESET){
  let n=0; for(const a of accounts()){ if(a.key){ a.key=''; n++; } if(a.bk){ delete a.bk; n++; } delete a.bkLabel; delete a.status; }
  [SV_SUBSIG_KEY,SV_VAULT_KEY,SV_KEYERR_KEY].forEach(k=>localStorage.removeItem(k));
  if(n){ localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(S)); localStorage.removeItem(SV_TOKEN_KEY); }
  localStorage.setItem(KEY_RESET_K,KEY_RESET);
} }catch(e){}
// b69: 서버 모드인데 세션(토큰)이 없으면 이 PC 에 남은 앱 데이터를 쓰지 않고 지움 (예전 로그인의 데이터가 로그인 없이 보이지 않게). 승인 대기 요청만 유지
try{ if(SV_ON&&!svTok()&&(S.characters.length||accounts().length||S.history.length||(S.monthHistory||[]).length||['svUser','svmeta','svbase','svVault','svSubSig','svAdmin','guild','sched'].some(k=>localStorage.getItem('mapleBossTracker.'+k)!=null))) svWipeAll({keepPending:true}); }catch(e){ console.warn(e); }
// b217: 예전(b216 전) 방식으로 본계정 키를 지운 기기 = 세션은 남았는데 키가 하나도 없음 → 처음 온 사람 상태(예시 화면). 서버 데이터는 그대로(세션만 끝냄)
try{ if(SV_ON&&svTok()&&!accounts().some(a=>a.key||a.bk)&&!svPend()){ const t=svTok(); svWipeAll(); fetch(SV_ON+'/api/logout',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json',Authorization:'Bearer '+t}}).catch(()=>{}); } }catch(e){ console.warn('b217 keyless session',e); }
if(!S.activeId && S.characters[0]) S.activeId=S.characters[0].id;
try{ applyAutoBosses(AUTO_BOSSES); applyAutoBosses(JSON.parse(localStorage.getItem(AUTO_KEY)||'null')); }catch(e){ console.warn('auto bosses',e); } // b251: 가격 적용 전에 보스·난이도부터
checkResets(); loadOfficialPrices(); fetchAutoBosses(); save(); applyTheme(); bootRender('start'); // b217: 이 시점엔 아래쪽 const(admPrices·feed 등)가 아직 없음 → 오류가 나도 스크립트가 멈추지 않게, 파일 끝에서 다시 그림
addEventListener('resize',()=>{ clearTimeout(fitPriceCard._t); fitPriceCard._t=setTimeout(()=>{ fitPriceCard(); fitMiss(); },150); });
/* b109: 왼쪽 위 '메보수' → '이번 주 보스' 탭 (탭 버튼 클릭과 같은 경로: 저장 안 한 변경 확인 포함) */
document.getElementById('logoHome')?.addEventListener('click',e=>{ e.preventDefault(); document.querySelector('#tabs [data-tab="boss"]')?.click(); });
/* 페이지를 열거나 새로고침할 때마다 넥슨 API 동기화 1회 (2026-10-10 사용자 요청) — 🔄 버튼과 같은 syncAll(넥슨 API 전용, 구글 드라이브·로그인 창과 무관).
 * 새로고침을 연달아 해도 API 호출량을 아끼도록: 마지막 동기화(완료) 또는 마지막 '열 때 동기화' 시작이 LOAD_SYNC_GAP_MS(3초, 사용자 결정) 안이면 건너뜀.
 * 시작 시각을 따로 저장(LOAD_SYNC_KEY)하는 이유: 동기화 도중 새로고침하면 lastSync 가 안 바뀌어 매번 다시 시작되기 때문. */
function loadSyncDue(){ if(!hasApi()||!S.characters.length) return false; /* 예시 화면 = 키·계정 없음 → 여기서 false (demoAllowed 는 아래 const 라 시작 때 못 부름) */
  const last=Math.max(+S.settings.lastSync||0, +localStorage.getItem(LOAD_SYNC_KEY)||0); return Date.now()-last>=LOAD_SYNC_GAP_MS; }
// b218: 새로 들어올 때만 자동 동기화였음 → b222(사용자 요청 '페이지 새로고침하면 캐릭터 동기화'): 새로 들어올 때('navigate')·새로고침(F5, 'reload')·뒤로/앞으로('back_forward', bfcache 복원 포함) 모두 1번.
// 겹침 방지 그대로: 동기화 중이거나 마지막 동기화·열 때 동기화 시작이 3초 안이면 건너뜀(loadSyncDue). 예시 화면은 키·캐릭터가 없어 안 함
function navType(){ try{ const e=performance.getEntriesByType('navigation')[0]; if(e&&e.type) return e.type; const n=performance.navigation; if(n) return n.type===1?'reload':n.type===2?'back_forward':'navigate'; }catch(e){} return 'navigate'; }
const NAV_SYNC=['navigate','reload','back_forward'].includes(navType()); // b222 (prerender 등 = 안 함)
if((NAV_SYNC&&loadSyncDue()) || (hasApi() && S.characters.some(c=>c.ocid&&!c.accId))){ try{ localStorage.setItem(LOAD_SYNC_KEY,String(Date.now())); }catch(e){} syncAll({silent:true}); } // + 기존 데이터: 계정 자동 배정
window.addEventListener('pageshow',e=>{ if(!e.persisted||syncing||!loadSyncDue()) return; try{ localStorage.setItem(LOAD_SYNC_KEY,String(Date.now())); }catch(x){} syncAll({silent:true}); }); // b222: 뒤로/앞으로가 bfcache 로 복원되면 스크립트가 다시 안 돌므로 여기서 같은 규칙
setInterval(()=>{ if(checkResets()) render(); else renderResetInfo(); if(!document.hidden) tabTick(); if(!document.hidden) gdPull(); }, 60e3);
document.addEventListener('visibilitychange',()=>{ if(document.hidden){ if(!SV_ON&&(gd.timer||gdLocalDirty())) gdPush({quick:true}); return; } if(checkResets()) render(); tabTick(); gdPull(); }); // (예전: 15분 지났으면 자동 동기화 — 2026-10-10 제거)
window.addEventListener('pagehide',()=>{ if(!SV_ON&&(gd.timer||gdLocalDirty())) gdPush({quick:true}); });

/* b68: 가입 승인 — 관리자(서버가 사용자 id 로 확인)만 목록·승인/거절/차단. 처음 연 기기에서도 관리자 버튼이 보이게 /api/me 로 확인 */
/* b229: 캐릭터 동기화가 끝날 때마다(🔄 버튼·키 등록·들어올 때·F5·뒤로/앞으로 모두, 예외 없이 끝난 동기화) 서버에 시각 1줄 → 관리자 창 '최근 갱신'.
 * (b225 는 🔄 클릭 때만이었음. 서버 쪽은 그대로: POST /api/sync-click = users.sync_click, 10초 안 중복은 0줄) 예시 화면·로컬 = 세션 없음 → 안 보냄 */
function svSyncDone(){ if(!SV_ON||!svTok()||!gdMeta.on) return; svFetch('/api/sync-click',{method:'POST',body:{}}).catch(()=>{}); }
async function svAdminCheck(){ if(!SV_ON||!svTok()||!gdMeta.on) return; try{ const r=await svFetch('/api/me'); localStorage.setItem(SV_ADMIN_KEY,r.admin?'1':'0'); gdRender(); if(!itemPriceLoad._at||Date.now()-itemPriceLoad._at>60e3) itemPriceLoad(); if(r.admin) admPriceLoad(); /* b220: 관리자 시세·mai 는 공용 시세 60초 제한과 따로 (시작 때 늘 건너뛰던 버그) */ const m=$('#gMenu'); if(m&&!m.hidden) gdMenu(true); }catch(e){} }
let admUsers=null, admErr='';
/* b102: 관리자 창 즉시 — 지난 목록(이 탭 sessionStorage)으로 바로 그리고 뒤에서 새로 받음. 사용자 목록+최저가 = 요청 1번(/api/admin/users?prices=1) */
const ADM_CACHE_KEY='mapleBossTracker.admUsers';
let admSeq=0;
async function openAdmin(){ $('#adminModal').classList.add('show'); admErr='';
  if(!admUsers){ try{ const c=JSON.parse(sessionStorage.getItem(ADM_CACHE_KEY)||'null'); if(Array.isArray(c)) admUsers=c; }catch(e){} }
  renderAdmin(); await admLoad(); }
async function admLoad(){ const my=++admSeq;
  try{ const r=await svFetch('/api/admin/users?prices=1'); if(my!==admSeq) return; admUsers=r.users||[]; admErr=''; try{ sessionStorage.setItem(ADM_CACHE_KEY,JSON.stringify(admUsers)); }catch(e){} if(r.prices&&svIsAdmin()) admPriceSave(r.prices); }
  catch(e){ if(my!==admSeq) return; if(!admUsers) admErr=e.message; else toast('관리자 목록을 새로 받지 못했어요: '+e.message); }
  renderAdmin(); }
function renderAdmin(){
  const b=$('#admBody'); if(!b) return;
  if(admErr){ b.innerHTML=`<div class="impmsg warn">${esc(admErr)}</div>`; return; }
  if(!admUsers){ b.innerHTML='<div class="muted">불러오는 중…</div>'; return; }
  const who=u=>`<b>${esc(u.name||'(이름 없음)')}</b><span class="muted">${u.world?' · '+esc(u.world):''}${u.level?' · Lv.'+u.level:''}</span>`;
  const row=(u,info,btns)=>`<div class="admrow" data-admuser="${esc(u.id)}"><div class="admwho">${who(u)}<div class="muted tiny">${info}</div></div><div class="admbtns">${btns}</div></div>`;
  const P=admUsers.filter(u=>u.status==='pending'), A=admUsers.filter(u=>u.status==='ok'||u.status==='blocked'); // b78: 차단 없음 — 예전 차단 사용자는 '사용 중'에(강퇴 가능), 거절한 요청은 목록에 안 보임
  const PG=10, np=Math.max(1,Math.ceil(A.length/PG)); admPage=Math.min(Math.max(1,admPage),np); const Ap=A.slice((admPage-1)*PG,admPage*PG);
  const sec=(t,list,empty,f,shown)=>`<section class="admsec"><h4>${t} <span class="muted">(${list.length})</span></h4>${list.length?(shown||list).map(f).join(''):`<div class="muted tiny">${empty}</div>`}</section>`;
  b.innerHTML=`<div class="admsec admprice" id="admPrice"></div>`+sec('승인 대기',P,'대기 중인 요청이 없어요',u=>row(u,`요청 ${u.requestedAt?hm(u.requestedAt):'-'}`,`<button class="btn sm" data-adm="approve">승인</button><button class="btn sm ghost admno" data-adm="reject">거절</button>`))
    +sec('사용 중',A,'없음',u=>{ const al=u.alts||[], op=admOpen.has(u.id); // b91: 부계정은 본계정 아래 접힘(▽/△), 강퇴 없음, 등록 날짜(KST)
      const tg=al.length?`<button class="admtg" data-admalt="${esc(u.id)}" aria-expanded="${op}" title="부계정 ${al.length}개 ${op?'접기':'펼치기'}">${op?'△':'▽'} 부계정 ${al.length}</button>`:'';
      return row(u,`${u.status==='blocked'?'(예전 차단) ':''}캐릭터 ${u.chars||0} · 데이터 ${Math.ceil((u.size||0)/1024)}KB`,`${tg}${admJoinReg(u)}${u.admin?'<span class="admtag">관리자</span>':`<button class="btn sm ghost admno" data-adm="kick">강퇴</button>`}`)
        +(al.length?`<div class="admalts"${op?'':' hidden'}>${al.map(a=>`<div class="admrow admalt"><div class="admwho"><span class="muted">└</span> <b>${esc(a.label||'부계정')}</b><span class="muted">${a.name?' · '+esc(a.name):''}${a.world?' · '+esc(a.world):''}${a.level?' · Lv.'+a.level:''}</span><div class="muted tiny">부계정 · 캐릭터 ${a.chars||0}</div></div><div class="admbtns">${admReg(a.regAt)}<span class="admkick-sp"></span></div></div>`).join('')}</div>`:''); },Ap)
    +(np>1?`<div class="admpages">${Array.from({length:np},(_,i)=>`<button class="btn sm ${i+1===admPage?'':'ghost'}" data-admpage="${i+1}">${i+1}</button>`).join('')}</div>`:''); // b78: 10명씩 쪽 번호
  renderAdmPrice();
}
async function admDecide(id,action){
  const u=(admUsers||[]).find(x=>x.id===id); const nm=u?.name||'이 사용자';
  if(action==='kick'&&!confirm(`${nm}\n정말 강퇴할까요? 이 사용자의 등록 키와 데이터가 모두 삭제됩니다.`)) return; // b78
  if(action==='reject'&&!confirm(`${nm} — 가입 요청을 거절할까요?`)) return;
  // b102: 낙관적 반영 — 누르자마자 목록을 바꾸고 요청은 뒤에서. 실패하면 되돌리고 오류 알림
  const before=admUsers; admSeq++; // 진행 중인 목록 새로 받기 결과는 버림 (바뀐 화면을 덮지 않게)
  admUsers=(admUsers||[]).flatMap(x=>x.id!==id?[x]:action==='approve'||action==='unblock'?[{...x,status:'ok',joinAt:x.joinAt||Date.now()}]:[]);
  try{ sessionStorage.setItem(ADM_CACHE_KEY,JSON.stringify(admUsers)); }catch(e){}
  renderAdmin();
  try{ await svFetch('/api/admin/decide',{method:'POST',body:{user:id,action}}); if(action!=='kick') toast({approve:'승인했습니다',reject:'거절했습니다',kick:'강퇴했습니다',unblock:'승인했습니다'}[action]+` — ${nm}`); }
  catch(e){ admUsers=before; try{ sessionStorage.setItem(ADM_CACHE_KEY,JSON.stringify(before)); }catch(x){} renderAdmin(); toast(`⚠ ${nm} — 처리하지 못해 되돌렸어요: ${e.message}`); }
}
/* b104: 관리자 전용 시세 — maple.ai.kr '아이템 시세 추적' 페이지(https://maple.ai.kr/blog/item-price-tracker-2026, 본섭 일별 시세)를 Worker 가 한 번 받아 읽음
 * (/api/admin/maple-prices, 관리자만, 브라우저 CORS 없이·요청 1번). robots.txt: Allow / (막힌 곳 /pf/ /admin/ /book/ 뿐).
 * 우리 드롭 표에서 [획득]으로 넣는 아이템 중 그 페이지에 있는 것만 이름으로 맞춤(b208: 서버 MAI_NAMES). 없는 아이템은 그대로(채움·시간 안 바뀜).
 * 수익 기록 창에서 금액 자동 채움 + '최저가 측정 시간 - YYYY-MM-DD HH:mm'(KST, 받아 온 시각). 예전 크롬 확장(b93)은 b104 에서 삭제(넥슨 약관). */
const ADM_PRICE_KEY='mapleBossTracker.admPrices';
const kstStamp=t=>new Date(t+9*3600e3).toISOString().slice(0,16).replace('T',' ');
function admPrices(){ try{ return JSON.parse(localStorage.getItem('mapleBossTracker.admPrices')||'{}')||{}; }catch(e){ return {}; } } // b217: 함수 선언(호이스팅) — 시작 렌더 때 'Cannot access admPrices before initialization' 로 스크립트가 멈췄음
// 반지 상자 결과 'ring:r4'·'ring:c4'(리스트레인트·컨티뉴어스 링 4레벨) → ring_r4·ring_c4, 칠흑 상자 결과 'cb:키' → 키
function admPriceOf(ik){ /* b112: 공용 시세 → 모든 사용자 수익 기록 칸 채움 */ const k=(x=>SJM_KEYS.has(x)?'b_sjm':x)(String(ik||'').replace(/^cb:/,'').replace(/^ring:(r4|c4)$/,'ring_$1')), /* b261 */ o=(typeof itemPrices==='function'?itemPrices():admPrices())[k]; /* b112: 이 기기 + 서버에서 받은 시세 */ return o&&+o.p>0&&+o.t>0?o:null; }
let admPriceMsg='', admPriceBusy=false;
/* b112: 아이템 시세 = 관리자가 등록·갱신한 값(서버 admin_prices) — 로그인한 사용자 누구나 GET /api/prices 로 읽어 이 기기에 보관. 관리자 기기는 admPrices 와 합침(최신 시각 우선) */
const ITEM_PRICE_KEY='mapleBossTracker.itemPrices';
/* b206: 아이템 시세 출처 = Worker 가 받아 읽는 maple.ai.kr '아이템 시세 추적'(server/worker.js MAI_URL 과 같은 주소) — 아이템 가격 표·수익을 기록할까요? 창 아래 '출처 : 링크'(새 탭) */
function priceSrcHtml(cls){ const ITEM_PRICE_SRC='https://maple.ai.kr/blog/item-price-tracker-2026'; /* 함수 안 = 첫 렌더가 먼저 불러도 안전 */ return `<div class="${cls}">출처 : <a href="${ITEM_PRICE_SRC}" target="_blank" rel="noopener noreferrer" title="${ITEM_PRICE_SRC}">maple.ai.kr 아이템 시세 추적</a></div>`; }
function itemPrices(){ let a={}; try{ a=JSON.parse(localStorage.getItem(ITEM_PRICE_KEY)||'{}')||{}; }catch(e){} const b=svIsAdmin()?admPrices():{}, o={...a};
  for(const [k,v] of Object.entries(b)) if(v&&+v.p>0&&(!o[k]||+o[k].t<=+v.t)) o[k]=v; for(const k in o) if(!(o[k]&&+o[k].p>0)) delete o[k]; return o; }
function itemPricePut(P){ if(!P||typeof P!=='object'||!Object.keys(P).length) return; /* b112: 빈 응답으로 지우지 않음 */ let cur={}; try{ cur=JSON.parse(localStorage.getItem(ITEM_PRICE_KEY)||'{}')||{}; }catch(e){}
  for(const [k,o] of Object.entries(P)) if(o&&+o.p>0&&+o.t>0&&(!cur[k]||+cur[k].t<=+o.t)) cur[k]={p:+o.p,t:+o.t}; // 0·빈 값 무시, 더 새 것만
  try{ localStorage.setItem(ITEM_PRICE_KEY,JSON.stringify(cur)); }catch(e){} }
const repaintPriceCard=()=>repaintPrices();
async function itemPriceLoad(){ if(!SV_ON) return; /* b112: 공용 시세 — 로그인 없이도 */ itemPriceLoad._at=Date.now(); try{ const r=await svFetch('/api/prices',{noAuth:true}); itemPricePut(r.prices); repaintPriceCard(); /* b203: 첫 화면 아이템 카드도 (예전엔 아이템 탭이 열려 있을 때만) */ }catch(e){} }
function admPriceSave(P){ const cur=admPrices(); for(const [k,o] of Object.entries(P||{})) if(o&&+o.p>0&&(!cur[k]||cur[k].t<=o.t)) cur[k]={p:+o.p,t:+o.t}; try{ localStorage.setItem(ADM_PRICE_KEY,JSON.stringify(cur)); }catch(e){} }
/* b208: 아이템 키 ↔ maple.ai.kr 이름 짝은 server/worker.js MAI_NAMES 하나뿐(예전 MAI_CODE·maiMap 복사본 없앰). 서버가 맞춘 값(mapped)을 그대로 씀.
 * admMaiGot = 가장 새 시세 날짜에 maple.ai.kr 값을 받은 우리 키 집합(null = 아직 모름) → 시세 등록 창에서 못 받은 아이템 옆 빨간 '시세 정보 없음' */
/* b220: 예전엔 [최저가 갱신] 응답 때만 채워지고(메모리), 시작 때 admPriceLoad 가 itemPriceLoad 의 60초 제한에 걸려 안 불려서 자동(cron) 갱신 뒤엔 늘 비어 있었음.
 * 이제 서버 maiInfo(mai_cache) 하나 = 두 길 똑같음: 시작·로그인 확인 때, 시세 등록 창을 열 때마다 /api/admin/prices 의 mai 를 받고, 이 기기에 보관(창이 바로 그려지게) */
const ADM_MAI_KEY='mapleBossTracker.admMai';
let admMaiGot=null, admMaiDate='';
const admMaiSet=m=>{ if(m&&Array.isArray(m.got)){ admMaiGot=new Set(m.got); admMaiDate=String(m.date||''); try{ localStorage.setItem(ADM_MAI_KEY,JSON.stringify({date:admMaiDate,got:m.got})); }catch(e){} } };
try{ const m=JSON.parse(localStorage.getItem(ADM_MAI_KEY)||'null'); if(m&&Array.isArray(m.got)){ admMaiGot=new Set(m.got); admMaiDate=String(m.date||''); } }catch(e){}
function mktMissPaint(){ const el=document.querySelector('#mktModal'); if(!el) return; for(const row of el.querySelectorAll('.rarow[data-pid]')){ const miss=!!admMaiGot&&!admMaiGot.has(row.dataset.pid), cur=row.querySelector('.mkno');
  if(miss&&!cur) row.querySelector('.raname').insertAdjacentHTML('afterend','<span class="mkno">시세 정보 없음</span>'); else if(!miss&&cur) cur.remove(); } }
/* b112: 다른 기기에서 갱신한 시세를 이 기기로 — 예전엔 관리자 창을 열 때만 받아서, 새 기기(집 PC)에선 수익 기록 창이 빈 칸('0')이었음. 이제 로그인 확인 때마다 받음.
 * 받은 값이 비었거나 실패하면 아무것도 안 바꿈(admPriceSave 는 0·빈 값을 무시하고 더 새 시각만 덮음) */
async function admPriceLoad(){ if(!svIsAdmin()) return; try{ const R=await svFetch('/api/admin/prices'), P=R.prices; admMaiSet(R.mai); mktMissPaint(); if(P&&typeof P==='object'&&Object.keys(P).length){ admPriceSave(P); if(typeof repaintPriceCard==='function'&&pcKind==='item') repaintPriceCard(); } }catch(e){} }
// b106: 대기 없이 바로 요청 (하루 1회 접속, 같은 날은 캐시)
async function admPriceRun(){
  if(!svIsAdmin()||admPriceBusy) return;
  admPriceBusy=true; admPriceMsg='maple.ai.kr 시세 받는 중…'; renderAdmPrice();
  try{
    const r=await svFetch('/api/admin/maple-prices'); const P=r.mapped&&typeof r.mapped==='object'?r.mapped:{}; /* b208: 서버가 맞춘 값(값 있는 것만, t=처음 본 시각) */
    const miss=(r.missing||[]).length; admMaiSet(r.mai||{date:r.date,got:Object.keys(P)}); mktMissPaint();
    admPriceSave(P);
    const sv=await svFetch('/api/admin/prices',{method:'PUT',body:{prices:P}}); admPriceSave(sv.prices); itemPricePut(sv.prices); repaintPriceCard();
    admPriceMsg=`${Object.keys(P).length}개 갱신 (maple.ai.kr ${esc(String(r.date||''))} 본섭 시세)${miss?` · 없음 ${miss}개`:''}`;
  }catch(e){ admPriceMsg=`⚠ ${esc(e.message||'실패')}`; }
  admPriceBusy=false; renderAdmPrice();
}
function renderAdmPrice(){
  const el=$('#admPrice'); if(!el) return;
  const P=admPrices(), ts=Object.values(P).map(o=>o.t), last=ts.length?Math.max(...ts):0;
  const msg=admPriceMsg?`<div class="muted tiny">${admPriceMsg}</div>`:'';
  el.innerHTML=`<div class="admprice-h"><b>경매장 최저가</b><span class="muted tiny">${last?`마지막 측정 ${kstStamp(last)} · ${Object.keys(P).length}개`:'아직 없음'}</span><button class="btn sm" id="admPriceBtn" ${admPriceBusy?'disabled':''}>최저가 갱신</button><button class="btn sm" id="mktBtn">시세 등록</button></div>${msg}<div class="muted tiny admsrc">출처: <a href="https://maple.ai.kr/blog/item-price-tracker-2026" target="_blank" rel="noopener noreferrer">maple.ai.kr</a> (본섭 일별 시세)</div>`;
}
document.addEventListener('click',e=>{ if(e.target.closest('#admPriceBtn')) admPriceRun(); if(e.target.closest('#mktBtn')) openMkt(); });
/* b112: 관리자 '시세 등록' — 수익 기록 가능한 모든 아이템 + 지금 등록된 시세(억 메소), 고친 칸만 저장 → 서버(admin_prices) + 이 기기, 가격 카드 바로 반영 */
function openMkt(){
  if(!svIsAdmin()) return; document.querySelector('#mktModal')?.remove(); const P=itemPrices(), L=revItems();
  const el=document.createElement('div'); el.id='mktModal'; el.className='modal-bg show'; el.setAttribute('role','dialog'); el.setAttribute('aria-modal','true'); el.setAttribute('aria-labelledby','mktTitle');
  const v=k=>{ const o=P[priceId(k)]; return o?String(Math.round(o.p/1e4)/1e4):''; };
  el.innerHTML=`<div class="modal rabox mktbox"><h3 id="mktTitle">시세 등록</h3>
    <div class="ralist">${L.map((k,i)=>`<div class="rarow" data-pid="${esc(priceId(k))}"><span class="raic">${lootIco(k)}</span><span class="raname">${esc(lootName(k))}<small class="ram" data-mkm="${i}">${P[priceId(k)]?meso(P[priceId(k)].p):''}</small></span>${admMaiGot&&!admMaiGot.has(priceId(k))?'<span class="mkno">시세 정보 없음</span>':'' /* b208 */}<label class="rvin rain"><input type="number" inputmode="decimal" min="0" step="0.01" placeholder="-" data-mk="${i}" data-orig="${v(k)}" value="${v(k)}" aria-label="${esc(lootName(k))} 시세 (억 메소)"><span>억 메소</span></label></div>`).join('')}</div>
    <div class="rverr" id="mktErr" role="alert"></div>
    <div class="rabtns"><button class="btn raok" data-mkb="ok">저장</button><button class="btn ghost" data-mkb="cancel">취소</button></div></div>`;
  document.body.appendChild(el);
  const close=()=>{ el.remove(); document.removeEventListener('keydown',kd,true); };
  const kd=e=>{ if(e.key==='Escape'){ e.preventDefault(); e.stopPropagation(); close(); } };
  document.addEventListener('keydown',kd,true);
  el.addEventListener('input',e=>{ const i=e.target.dataset?.mk; if(i==null) return; const x=parseFloat(String(e.target.value).replace(',','.')), o=el.querySelector(`[data-mkm="${i}"]`); if(o) o.textContent=x>0?meso(Math.round(x*1e8)):''; });
  const ok=async()=>{ const t=Date.now(), out={};
    for(const inp of el.querySelectorAll('[data-mk]')){ const s=String(inp.value).trim().replace(',','.'); if(s===inp.dataset.orig||s==='') continue; const x=parseFloat(s);
      if(!(x>0)||x>100000){ $('#mktErr').textContent='금액을 확인해주세요.'; markEmpty(inp); inp.focus(); return; } out[priceId(L[+inp.dataset.mk])]={p:Math.round(x*1e8),t}; }
    if(!Object.keys(out).length){ close(); return; }
    admPriceSave(out); itemPricePut({...itemPrices(),...out}); repaintPriceCard(); renderAdmPrice(); close();
    try{ const sv=await svFetch('/api/admin/prices',{method:'PUT',body:{prices:out}}); admPriceSave(sv.prices); itemPricePut(sv.prices); repaintPriceCard(); renderAdmPrice(); toast(`시세 ${Object.keys(out).length}개 저장`); }
    catch(e){ toast(`⚠ 시세를 서버에 저장하지 못했어요: ${e.message}`); } };
  el.onclick=e=>{ if(e.target===el) return close(); const b=e.target.closest('[data-mkb]'); if(b) b.dataset.mkb==='ok'?ok():close(); };
  admPriceLoad(); /* b220: 열 때마다 서버 mai(자동 갱신 포함) 받아 '시세 정보 없음' 다시 칠함 */
  setTimeout(()=>el.querySelector('[data-mk]')?.focus(),30);
}
let admPage=1; const admOpen=new Set(); // b91: 펼친 본계정 id
const admDay=t=>t?new Date(t+9*3600e3).toISOString().slice(0,10):'-'; // KST
const admJoinReg=u=>`<span class="admreg muted tiny">가입 : ${admDay(u.joinAt)} · 최근 갱신 : ${u.syncAt?hm(u.syncAt):'-'}</span>`; // b238: 등록 → 최근 갱신(users.sync_click = 마지막으로 끝난 동기화; last_sync_at 은 배포 시각으로 채워져 안 씀), 정보 줄의 중복 '최근 갱신' 제거 · b237: 본계정 줄 = 가입(users.created_at)·등록(본계정 키 등록, 없으면 -) 따로
const admReg=t=>`<span class="admreg muted tiny">등록 날짜 : ${t?new Date(t+9*3600e3).toISOString().slice(0,10):'-'}</span>`; // KST
document.addEventListener('click',e=>{ const at=e.target.closest('[data-admalt]'); if(at){ const id=at.dataset.admalt; admOpen.has(id)?admOpen.delete(id):admOpen.add(id); renderAdmin(); return; } const pg=e.target.closest('[data-admpage]'); if(pg){ admPage=+pg.dataset.admpage; renderAdmin(); return; } const t=e.target.closest('[data-adm]'); if(t){ const r=t.closest('[data-admuser]'); if(r) admDecide(r.dataset.admuser,t.dataset.adm); return; }
  if(e.target.id==='adminModal') e.target.classList.remove('show'); });
setTimeout(()=>{ if(!SV_ON) return; itemPriceLoad(); if(svTok()&&gdMeta.on) svAdminCheck(); else if(svPend()?.key) svLogin(svPend().key,'',{quiet:true}); gdRender(); },800); // 승인 대기 → 열 때 한 번 다시 확인

/* =====================================================================
 *  소식 피드 (왼쪽 아래 카드)
 *  GitHub Actions(update-feed.yml, 5분마다)가 feed.json 을 갱신 → 사이트는 그 파일만 읽음.
 *  API 키·외부 요청 없음. 읽음 표시는 이 브라우저 localStorage(mapleBossTracker.feedSeen).
 * ===================================================================== */
const FEED_TABS=[['saryo','사료감지'],['patch','패치내역'],['test','테섭'],['mabbak','마빡도로시']];
const FEED_LIVE='https://ggoolzip-wq.github.io/feed.json', FEED_SEEN_KEY='mapleBossTracker.feedSeen', FEED_ROW=31, FEED_MOBILE_ROWS=6;
const feed={data:null,err:'',tab:'saryo',page:1,per:5,at:0,srv:null,srvKey:''};
let feedSeen=new Set((()=>{ try{ return JSON.parse(localStorage.getItem(FEED_SEEN_KEY))||[]; }catch(e){ return []; } })());
/* b170: 서버(Worker)가 서비스 키로 넥슨 공지를 1분 동안 계속 확인한 결과(feed.srv) — /api/live 30초 폴링에 실려 옴. feed.json(5분) 과 id 로 합침 */
// b265: 마빡도로시 탭은 제목에 '포탈' 이 있는 글을 보이지 않음 (수집기도 건너뜀)
const feedSkip=(t,x)=>t==='mabbak'&&String(x&&x.title||'').includes('포탈');
const feedItems=t=>{ const a=((feed.data&&feed.data.items&&feed.data.items[t])||[]).filter(x=>!feedSkip(t,x)), b=((feed.srv&&feed.srv.items&&feed.srv.items[t])||[]).filter(x=>!feedSkip(t,x)); if(!b.length) return a;
  const ids=new Set(a.map(x=>x.id)), extra=b.filter(x=>!ids.has(x.id)); return extra.length?[...extra,...a].sort((x,y)=>String(y.date||'').localeCompare(String(x.date||''))):a; };
const feedSun=()=>{ const a=feed.data&&feed.data.sunday, b=feed.srv&&feed.srv.sunday; return b&&(!a||+b.id>+a.id)?b:a; };
function feedSrvApply(f){ if(!f||!f.items) return; const k=JSON.stringify([f.items,f.sunday]); if(k===feed.srvKey) return; feed.srv=f; feed.srvKey=k; renderFeed(); }
// b62: 읽음 표시를 서버(로그인한 계정)에 합집합으로 보관 → 다른 PC 에서도 이미 본 글은 N 표시 없음 (서버 모드만, 예전 서버면 조용히 건너뜀)
let seenPush=new Set(), seenT=null;
function svSeenMark(id){ if(!SV_ON||!svTok()) return; seenPush.add(id); clearTimeout(seenT); seenT=setTimeout(svSeenFlush,1500); }
async function svSeenFlush(){ if(!seenPush.size||!svTok()) return; const ids=[...seenPush]; seenPush=new Set();
  try{ const r=await svFetch('/api/seen',{method:'PUT',body:{ids}}); svSeenApply(r.ids); }catch(e){ if(e.status!==404) ids.forEach(x=>seenPush.add(x)); } }
function svSeenApply(ids){ let ch=false; (ids||[]).forEach(x=>{ if(!feedSeen.has(x)){ feedSeen.add(x); ch=true; } }); if(ch){ feedSaveSeen(); renderFeed(); } }
async function svSeenPull(){ if(!SV_ON||!svTok()) return;
  try{ const r=await svFetch('/api/seen'); const srv=new Set(r.ids||[]); svSeenApply(r.ids); const mine=[...feedSeen].filter(x=>!srv.has(x)); if(mine.length){ mine.forEach(x=>seenPush.add(x)); svSeenFlush(); } }catch(e){} }
// b70: 올린 날짜(없으면 처음 수집한 시각 seen)가 7일 지난 글은 안 읽었어도 N·탭 숫자에서 빠짐. 날짜를 모르면 예전처럼. 렌더할 때마다(5분마다 feedLoad 포함) 다시 계산
const FEED_NEW_DAYS=7;
const feedTime=x=>{ const t=Date.parse(x&&x.date||''); if(!isNaN(t)) return t; const u=Date.parse(x&&x.seen||''); return isNaN(u)?NaN:u; };
const feedFresh=(x,now=Date.now())=>{ const t=feedTime(x); return isNaN(t)||now-t<=FEED_NEW_DAYS*864e5; };
const feedIsNew=(x,now)=>!feedSeen.has(x.id)&&feedFresh(x,now);
const feedUnseen=t=>{ const now=Date.now(); return feedItems(t).filter(x=>feedIsNew(x,now)).length; };
function feedSaveSeen(){ // feed 에 아직 있는 글만 기억 (무한히 커지지 않게)
  const live=new Set(FEED_TABS.flatMap(([t])=>feedItems(t).map(x=>x.id)));
  const keep=feed.data?[...feedSeen].filter(id=>live.has(id)):[...feedSeen];
  try{ localStorage.setItem(FEED_SEEN_KEY,JSON.stringify(keep)); }catch(e){}
}
async function feedLoad(){
  try{
    const base=location.protocol==='file:'?FEED_LIVE:'./feed.json'; // 압축본(로컬 파일)으로 열었을 때는 사이트의 feed.json
    const r=await fetch(base+'?t='+Math.floor(Date.now()/3e5),{cache:'no-cache'});
    if(!r.ok) throw new Error('HTTP '+r.status);
    const d=await r.json(); if(!d||typeof d.items!=='object') throw new Error('형식 오류');
    feed.data=d; feed.err=''; feed.at=Date.now();
  }catch(e){ if(!feed.data) feed.err='소식을 불러오지 못했습니다'; }
  renderFeed();
}
const fdKst=iso=>{ const t=Date.parse(iso); if(isNaN(t)) return null; const d=new Date(t+9*3600e3); return {y:d.getUTCFullYear(),m:d.getUTCMonth()+1,d:d.getUTCDate(),h:d.getUTCHours(),mi:d.getUTCMinutes()}; };
const p2=n=>String(n).padStart(2,'0');
function fdShort(iso){ const k=fdKst(iso), now=fdKst(new Date().toISOString()); if(!k) return '';
  return (k.y!==now.y?String(k.y).slice(2)+'.':'')+p2(k.m)+'.'+p2(k.d); }
function fdFull(iso){ const k=fdKst(iso); return k?`${k.y}.${p2(k.m)}.${p2(k.d)} ${p2(k.h)}:${p2(k.mi)}`:''; }
function renderFeed(){
  const c=$('#feedCard'); if(!c) return;
  const t=feed.tab, items=feedItems(t), per=Math.max(1,feed.per), pages=Math.max(1,Math.ceil(items.length/per));
  feed.page=Math.min(Math.max(1,feed.page),pages);
  const src=feed.data&&feed.data.sources&&feed.data.sources[t];
  const tabs=FEED_TABS.map(([k,l])=>{ const n=feedUnseen(k);
    return `<button type="button" class="ftab${k===t?' on':''}" data-ftab="${k}" aria-pressed="${k===t}">${l}${n?`<b class="fcnt" aria-label="새 글 ${n}개">${n>99?'99+':n}</b>`:''}</button>`; }).join('');
  let note='';
  if(src&&src.ok===false) note=`<div class="fnote" title="${esc(src.error||'')}">⚠ 수집 실패${src.lastOkAt?` · 마지막 성공 ${esc(fdFull(src.lastOkAt))}`:''}</div>`;
  const now=Date.now(), rows=items.slice((feed.page-1)*per,feed.page*per).map(x=>{
    const isNew=feedIsNew(x,now), exp=x.end&&Date.parse(x.end)<now;
    const tip=`${x.title}\n${fdFull(x.date)}${x.end?`\n수령 기한 ~${fdFull(x.end)}${exp?' (종료)':''}`:''}`;
    return `<li><a class="fit${exp?' exp':''}" href="${esc(x.url)}" target="_blank" rel="noopener noreferrer" data-fid="${esc(x.id)}" title="${esc(tip)}">${isNew?'<span class="fnew">N</span>':''}<span class="ftt">${esc(x.title)}</span>${x.end?`<span class="fend">~${esc(fdShort(x.end))}</span>`:''}<span class="fdt">${esc(fdShort(x.date))}</span></a></li>`; }).join('');
  const body=feed.err?`<div class="fempty">${esc(feed.err)}</div>`:!feed.data?`<div class="fempty">불러오는 중…</div>`:items.length?`<ul class="flist">${rows}</ul>`:`<div class="fempty">아직 소식이 없습니다</div>`;
  let pager='';
  if(pages>1){ let s=Math.max(1,feed.page-2), e=Math.min(pages,s+4); s=Math.max(1,e-4);
    const nums=[]; for(let i=s;i<=e;i++) nums.push(`<button type="button" class="fpg${i===feed.page?' on':''}" data-fpage="${i}"${i===feed.page?' aria-current="page"':''}>${i}</button>`);
    const more=pages>5;
    pager=(more?`<button type="button" class="fpg fnav" data-fpage="${feed.page-1}"${feed.page<=1?' disabled':''} aria-label="이전">‹</button>`:'')+nums.join('')+(more?`<button type="button" class="fpg fnav" data-fpage="${feed.page+1}"${feed.page>=pages?' disabled':''} aria-label="다음">›</button>`:''); }
  c.innerHTML=`<div class="ftabs" role="tablist">${tabs}</div>${note}<div class="fbody">${body}</div><div class="fpager">${pager}</div>`;
  const sc=$('#sunCard'), sid=JSON.stringify(feedSun()||null);
  if(sc&&(!sc.innerHTML||sc.dataset.sid!==sid||sc.dataset.loaded!==String(!!feed.data))){ renderSun(); sc.dataset.loaded=String(!!feed.data); }
}
/* 썬데이 메이플 카드 (feed.json 의 sunday) — 클릭하면 이벤트 글 */
const SUN_SVG='<svg class="sunico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.6" fill="currentColor"/><g stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 2.2v2.6M12 19.2v2.6M2.2 12h2.6M19.2 12h2.6M5.1 5.1l1.8 1.8M17.1 17.1l1.8 1.8M5.1 18.9l1.8-1.8M17.1 6.9l1.8-1.8"/></g></svg>';
const sunCropUrl=s=>s&&s.crop?(location.protocol==='file:'?FEED_LIVE.replace(/feed\.json$/,''):'./')+s.crop:'';
// 월요일 00:00 KST 가 지나면 지난 글 → '저번 주 혜택'; 새 글(게시일 ≥ 이번 월요일)이 오면 다시 '이번 주 혜택'
function lastMondayKST(now=Date.now()){ const k=new Date(now+9*3600e3); const dow=(k.getUTCDay()+6)%7; return Date.UTC(k.getUTCFullYear(),k.getUTCMonth(),k.getUTCDate()-dow)-9*3600e3; }
function sunPostTime(s){ const v=s&&(s.date||s.start); if(!v) return NaN; return /^\d{4}-\d{2}-\d{2}$/.test(v)?Date.parse(v+'T00:00:00+09:00'):Date.parse(v); }
function sunLabel(s,now=Date.now()){ const t=sunPostTime(s); return isFinite(t)&&t<lastMondayKST(now)?'저번 주 혜택':'이번 주 혜택'; }
setInterval(()=>{ const b=document.querySelector('#sunCard .sunben b'), s=feedSun(); if(b&&s&&b.textContent!==sunLabel(s)) renderSun(); },60e3);
function renderSun(){
  const c=$('#sunCard'); if(!c) return;
  const s=feedSun();
  let body;
  const src=s&&(sunCropUrl(s)||s.image);
  if(s&&src){
    const when=s.start?fdShort(s.start)+(s.end&&fdShort(s.end)!==fdShort(s.start)?' ~ '+fdShort(s.end):''):fdShort(s.date||'');
    const bens=(s.benefit?String(s.benefit).split(/\s*·\s*/).filter(Boolean):[]).slice(0,4); // b256: 최대 4줄
    const lines=bens.length?bens:[s.title||'썬데이 메이플'];
    body=`<button type="button" class="sunimg" data-sunopen title="크게 보기"><img src="${esc(src)}" alt="${esc(s.title||'썬데이 메이플')}" loading="lazy" referrerpolicy="no-referrer"></button>`+
      `<div class="suncap"><span class="ftt">${esc(s.title||'썬데이 메이플')}</span><span class="fdt">${esc(when)}</span></div>`+
      `<div class="sunben"><b>${sunLabel(s)}</b><ul>${lines.map(t=>`<li title="${esc(t)}">${esc(t)}</li>`).join('')}</ul></div>`;
  }else body=`<div class="sunempty">${SUN_SVG}<span>${feed.data||feed.err?'아직 썬데이 메이플 소식이 없어요':'불러오는 중…'}</span></div>`;
  c.innerHTML=`<div class="ftabs"><span class="ftab on stab" role="heading" aria-level="2">${SUN_SVG}썬데이</span></div><div class="sunbody">${body}</div>`;
  c.dataset.sid=JSON.stringify(s||null);
}
/* 썬데이 이미지 크게 보기 (라이트박스): 바깥 클릭·✕·Esc 로 닫기, 이미지를 누르면 원본 폭으로 확대(스크롤) */
let sunLbPrev=null;
function sunLightbox(){
  const s=feedSun(); if(!s) return;
  const full=s.image||sunCropUrl(s); if(!full) return;
  sunLbPrev=document.activeElement;
  const when=s.start?fdFull(s.start)+(s.end?' ~ '+fdFull(s.end):''):'';
  const lb=document.createElement('div'); lb.className='sunlb'; lb.id='sunLb'; lb.setAttribute('role','dialog'); lb.setAttribute('aria-modal','true'); lb.setAttribute('aria-label','썬데이 메이플 이미지');
  lb.innerHTML=`<div class="sunlb-in"><button type="button" class="sunlb-x" aria-label="닫기">✕</button><div class="sunlb-sc"><img src="${esc(full)}" alt="${esc(s.title||'썬데이 메이플')}" referrerpolicy="no-referrer" title="눌러서 확대/축소"></div>`+
    `<div class="sunlb-bar"><span class="sunlb-t">${SUN_SVG}${esc(s.title||'썬데이 메이플')}${when?` <small>${esc(when)}</small>`:''}</span>${s.url?`<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">공지 보기 ↗</a>`:''}</div></div>`;
  document.body.appendChild(lb); document.documentElement.classList.add('sunlb-open');
  lb.addEventListener('click',e=>{
    if(e.target.closest('.sunlb-x')||!e.target.closest('.sunlb-in')) return sunLbClose();
    if(e.target.tagName==='IMG') lb.classList.toggle('zoom');
  });
  lb.querySelector('.sunlb-x').focus();
}
function sunLbClose(){ const lb=$('#sunLb'); if(!lb) return; lb.remove(); document.documentElement.classList.remove('sunlb-open'); if(sunLbPrev&&sunLbPrev.focus) sunLbPrev.focus(); sunLbPrev=null; }
document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&$('#sunLb')){ e.preventDefault(); e.stopPropagation(); sunLbClose(); } },true);
$('#sunCard').addEventListener('click',e=>{ if(e.target.closest('[data-sunopen]')) sunLightbox(); });
/* 카드 높이 = 남은 화면 높이 (페이지가 이 카드 때문에 스크롤되지 않게), 쪽당 글 수 = 그 높이에 들어가는 줄 수 */
const FEED_FLOW_ROWS=5, FEED_MIN_ROWS=5, FEED_PAD=76, SUN_FLOW_H=320; // b257: FEED_PAD = 머리글·탭·쪽 번호 높이(실측 74px, 예전 70 이라 5줄 자리에 4줄만 들어갔음) // b61: 낮은 창(.side-flow)일 때 소식 줄 수·썬데이 높이
function feedFit(){
  const c=$('#feedCard'); if(!c) return; let old=feed.per;
  const sun=$('#sunCard');
  if(matchMedia('(max-width:820px)').matches){ c.style.height=''; feed.per=FEED_MOBILE_ROWS; if(sun){ sun.style.height=''; sun.style.display=''; } }
  else{
    const aside=c.parentElement, main=aside.parentElement, ms=getComputedStyle(main), foot=$('.foot');
    const inner=c.getBoundingClientRect().top-aside.getBoundingClientRect().top;
    const topDoc=main.getBoundingClientRect().top+scrollY+parseFloat(ms.paddingTop)+inner;     // 맨 위에 있을 때
    const below=parseFloat(ms.paddingBottom)+(foot?foot.offsetHeight:0);
    const stick=parseFloat(getComputedStyle(aside).top)||0;
    const view=$('#view'), viewBot=view?Math.max(0,...[...view.children].map(e=>e.getBoundingClientRect().bottom))+scrollY:0; // 그리드가 #view 를 늘리므로 내용 끝 기준
    // 본문이 더 길면 본문 끝까지 써도 페이지 길이가 안 늘어남 / 짧으면 화면 끝(아래 안내문 포함)까지
    const hStatic=Math.max(innerHeight-topDoc-below, viewBot-topDoc);
    const hStick=innerHeight-stick-inner-16;                                                        // 따라 내려올 때도 화면 안
    const h=Math.floor(Math.min(hStatic,hStick))-1;
    const minH=FEED_ROW*2+FEED_PAD, want=FEED_ROW*FEED_MIN_ROWS+FEED_PAD, SUN_MIN=140, gap=12; // b257: 소식(공지) 칸 = 썬데이 최소 높이가 남는 한 5줄
    // 남은 높이를 소식 1/3 : 썬데이 2/3 로 나눔. 썬데이 칸이 너무 작아지면(SUN_MIN 미만) 썬데이를 숨기고 소식이 전부 사용
    // b61: 화면이 낮아(또는 캐릭터 카드가 길어) 소식 최소 + 썬데이 최소가 안 들어가면 → 사이드바를 따라오지 않게(.side-flow, position:static)
    // 하고 두 카드를 기본 높이로 → 페이지가 길어지고 스크롤로 전부 닿음 (예전: 썬데이를 숨기고 sticky 라 아래가 잘림)
    const flow=h-gap<minH+(sun?SUN_MIN:0); aside.classList.toggle('side-flow',flow);
    let fh=Math.max(minH,Math.round((h-gap)/3),Math.min(want,h-gap-SUN_MIN)), sh=h-gap-fh;
    if(flow){ fh=FEED_ROW*FEED_FLOW_ROWS+FEED_PAD; sh=SUN_FLOW_H; }
    if(sun){ if(sh>=SUN_MIN){ sun.style.display=''; sun.style.height=sh+'px'; sun.classList.toggle('tight',sh<230); } else { sun.style.display='none'; fh=h; } }
    c.style.height=Math.max(minH,fh)+'px';
    const fb=c.querySelector('.fbody'); const avail=fb?fb.clientHeight:0;
    feed.per=Math.min(20,Math.max(2,Math.floor(avail/FEED_ROW)));
    if(feed.per!==old){ const first=(feed.page-1)*old; feed.page=Math.floor(first/feed.per)+1; old=feed.per; renderFeed(); }
    // 최소 높이에서 내용(머리글·2줄·쪽 번호)이 넘치면 넘친 만큼 소식 카드를 키우고 썬데이 카드에서 뺌 (모자라면 썬데이 숨김)
    const fb2=c.querySelector('.fbody'), over=Math.max(c.scrollHeight-c.clientHeight, fb2?fb2.scrollHeight-fb2.clientHeight:0);
    if(over>0){ const nh=c.offsetHeight+over; c.style.height=nh+'px';
      if(!flow&&sun&&sun.style.display!=='none'){ const s2=h-gap-nh; if(s2>=SUN_MIN){ sun.style.height=s2+'px'; sun.classList.toggle('tight',s2<230); } else { sun.style.display='none'; c.style.height=Math.max(nh,h)+'px'; } } }
  }
  if(feed.per!==old){ const first=(feed.page-1)*old; feed.page=Math.floor(first/feed.per)+1; renderFeed(); }
}
$('#feedCard').addEventListener('click',e=>{
  const tb=e.target.closest('[data-ftab]'); if(tb){ feed.tab=tb.dataset.ftab; feed.page=1; renderFeed(); feedFit(); return; }
  const pg=e.target.closest('[data-fpage]'); if(pg&&!pg.disabled){ feed.page=+pg.dataset.fpage; renderFeed(); return; }
  const a=e.target.closest('a[data-fid]'); if(a&&!feedSeen.has(a.dataset.fid)){ feedSeen.add(a.dataset.fid); feedSaveSeen(); svSeenMark(a.dataset.fid); setTimeout(renderFeed,0); }
});
$('#feedCard').addEventListener('auxclick',e=>{ const a=e.target.closest('a[data-fid]'); if(a&&e.button===1&&!feedSeen.has(a.dataset.fid)){ feedSeen.add(a.dataset.fid); feedSaveSeen(); svSeenMark(a.dataset.fid); setTimeout(renderFeed,0); } });
renderFeed(); feedFit();
addEventListener('resize',feedFit);
if(window.ResizeObserver){ const ro=new ResizeObserver(()=>feedFit()); document.querySelectorAll('.side-sticky>.card:not(#feedCard):not(#sunCard), .foot, header, #view').forEach(el=>ro.observe(el)); }
feedLoad().then(feedFit);
setInterval(()=>{ if(!document.hidden) feedLoad(); },3e5);
document.addEventListener('visibilitychange',()=>{ if(!document.hidden&&Date.now()-feed.at>3e5) feedLoad(); });
gdRender(); svGate();
if(SV_ON){ if(gdMeta.on&&svTok()){ gdConnect(false).then(()=>svSeenPull()); } else gdRender(); } // 서버 모드: 남은 세션 토큰으로만 (없으면 ☁ 로그인)
else if(gdUsable()){ gdLoadLib().catch(()=>{}); if(gdMeta.on) gdConnect(false); }

/* ===== b210 예시 화면 (demo): 로그인 전 = 위 탭(이번 주 보스·수익 분석·득템 분석·길드 현황) 마다 '예시 화면'.
 * 실제 화면 코드를 그대로 쓰고, 그리는 동안만 S(·schedC·guildC)를 가짜 예시 데이터로 바꿨다가 되돌림 → 진짜 데이터·로그인 흐름은 그대로.
 * 결정석 = 사이트가 지금 쓰는 실제 가격(price()), 아이템 = 공용 시세(itemPrices(), /api/prices), 드롭 = 사이트 드롭 표(dropsFor, 그 난이도). 저장·동기화·넥슨 요청 없음.
 * 신창섭 라이브 탭은 예시 없음(그대로). 로그인한 사용자(캐릭터 0명)는 예전 빈 화면 그대로. */
let DEMO_SC0=null, DEMO_ST=null, DEMO_SIG='', DEMO_SC=null, DEMO_GC=null, demoDepth=0, demoLive=null;
// 로그인 전 = 보이는 캐릭터 0명 + 서버 로그인(구글 드라이브 연결)도 안 함 + 등록한 API 키 계정도 없음. 로그인했는데 캐릭터 0명 = 예전 빈 화면(규칙 10)
const demoAllowed=()=>{ const real=demoLive||S; return !(real.characters||[]).some(charShown) && !(real.settings?.accounts||[]).length && !gdHasTok() && !gdMeta?.on; };
const demoTabOk=()=>tab!=='live';
function demoRng(seed){ let s=seed>>>0; return ()=>{ s=(s*1664525+1013904223)>>>0; return s/4294967296; }; }
// 한 판(보스 1번)당 그 아이템이 나올 확률 — 대략적인 체감 확률(예시용)
const DEMO_P=k=>isRing(k)?.06:/^se\d$/.test(k)?.12:(k==='g_life'||k==='g_faith')?.035:k==='chaosbox'?.025:k==='papmark'?.03:['lcm','eye','belt','book','terror','sos','cfe'].includes(k)?.006:.004;
const demoSig=()=>{ const ip=itemPrices(); return Object.values(PRICE_CONFIG).reduce((a,b)=>a+(+b||0),0)+'|'+Object.entries(ip).map(([k,o])=>k+o.p).sort().join(); };
function demoBuild(){
  const R=demoRng(20261018), R2=demoRng(777), IP=itemPrices(), wk0=weekId(), wk=k=>{ const t=new Date(wk0+'T00:00:00+09:00'); t.setDate(t.getDate()-7*k); return new Date(t.getTime()+9*3600e3).toISOString().slice(0,10); };
  const E=(d,p=1)=>({enabled:true,diff:d,party:p});
  const mk=(i,name,lv,job,bs)=>({id:'demo'+i,name,level:lv,job,world:'스카니아',image:'',accId:'demoA',ocid:'demo-ocid-'+i,isMain:i===1,guild:'메보기예시길드',bosses:bs,weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  const C=[ // 레벨·직업에 맞는 흔한 주간 조합 (12개 제한 안쪽)
    mk(1,'예시히어로',287,'히어로',{lotus:E('hard'),damien:E('hard'),slime:E('chaos'),lucid:E('hard'),will:E('hard'),dusk:E('chaos'),jinhilla:E('hard'),dunkel:E('hard'),seren:E('hard',2),kalos:E('normal',3),kaling:E('normal',3),adversary:E('normal',3),blackmage:E('hard')}),
    mk(2,'샘플비숍',279,'비숍',{papulatus:E('chaos'),lotus:E('hard'),damien:E('hard'),slime:E('chaos'),lucid:E('hard'),will:E('hard'),dusk:E('chaos'),jinhilla:E('hard'),dunkel:E('hard'),seren:E('normal',2),kalos:E('easy',2),kaling:E('easy',3),blackmage:E('hard')}),
    mk(3,'데모아크',272,'아크메이지(불,독)',{zakum:E('chaos'),vellum:E('chaos'),papulatus:E('chaos'),magnus:E('hard'),lotus:E('normal'),damien:E('normal'),slime:E('normal'),lucid:E('normal'),will:E('normal'),dusk:E('normal'),jinhilla:E('normal'),dunkel:E('normal')}),
    mk(4,'견본나로',265,'나이트로드',{zakum:E('chaos'),pierre:E('chaos'),vonbon:E('chaos'),queen:E('chaos'),vellum:E('chaos'),papulatus:E('chaos'),magnus:E('hard'),lotus:E('normal'),damien:E('normal'),slime:E('normal'),lucid:E('easy'),will:E('easy')})];
  const st={...defaultState(), theme:S.theme, characters:C, activeId:'demo1', history:[], monthHistory:[], missW:[], missM:[], startWeek:wk(4)};
  st.settings={...st.settings, accounts:[{id:'demoA',label:'예시 계정',key:'DEMO-NOT-A-KEY',main:true}], guilds:[{world:'스카니아',name:'메보기예시길드'}], suroChars:C.map(c=>c.id), autoSync:false};
  const live=S; S=st;
  try{
    const sale=(c,id,key,ik)=>{ const p=IP[priceId(ik)]; if(!p||!(p.p>0)||R2()>.85) return; const md=c.dmode[key]; if(md==='l') return; const n=md==='w'?1:curParty(c,id); /* b211: 블빵승리 = 전부, 분배 = ÷인원, 블빵패배 = 판 것 없음 */ c.drev[key]={m:Math.round(p.p/n),a:Math.round(p.p/1e4)/1e4,p:n,i:ik}; }; // 판 아이템만, 실제 공용 시세, 분배면 ÷인원
    const loot=(c,id,cfg,map,out)=>{ const b=findBoss(id); for(const it of dropsFor(b,cfg.diff)){ if(!ITEMS[it]||MISS_SKIP_SET.has(ITEMS[it].set)||R()>DEMO_P(it)) continue; /* b253: 정보용 세트는 예시에서 제외(난수 순서 그대로) */ const key=id+'|'+it; map[key]=1;
        const pty=curParty(c,id); if(pty>1) c.dmode[key]=isRing(it)?'s':(R()<1/pty?'w':'l'); // b211: 파티 드롭 = 블빵(승리 확률 1/인원), 반지 상자는 항상 분배
        if(isRing(it)){ const q=ring4(it)||{r4:0,c4:0,gl:0}, r=R()*100, o=r<q.r4?'r4':r<q.r4+q.c4?'c4':r<q.r4+q.c4+q.gl?'gl':'x'; out[key]=[o]; if(o!=='x'&&R()<.5) sale(c,id,key,o==='gl'?'g_life':'ring:'+o); } // 결과 = 실제 상자 확률(BOX_INFO·RING_GL)
        else if(it==='chaosbox'){ const k=CHAOS_PICK[Math.floor(R()*CHAOS_PICK.length)]; out[key]=['cb:'+k]; sale(c,id,key,'cb:'+k); }
        else sale(c,id,key,it); break; } };
    const roll=(c,pClear)=>{ c.weekly={}; c.drops={}; c.dropOut={}; c.drev={}; c.dmode={};
      for(const [id,cfg] of Object.entries(c.bosses)){ const b=findBoss(id); if(!b||b.type!=='weekly'||R()>pClear) continue; c.weekly[id]=true; loot(c,id,cfg,c.drops,c.dropOut); } };
    // b229: 주별 득템 표 예시 — 주마다 잡은 보스의 일반 드롭(반지 상자·칠흑 상자 제외)을 가끔 1개 더 (따로 난수 → 위 난수 순서 그대로)
    const R3=demoRng(2290), extra=(c,pr)=>{ const ids=Object.keys(c.weekly).filter(id=>c.weekly[id]&&curParty(c,id)===1); if(!ids.length||R3()>pr) return; const id=ids[Math.floor(R3()*ids.length)], cfg=c.bosses[id];
      const all=dropsFor(findBoss(id),cfg.diff).filter(it=>ITEMS[it]&&!MISS_SKIP_SET.has(ITEMS[it].set)&&!isRing(it)&&it!=='chaosbox'), eth=all.filter(it=>/^se\d$/.test(it)), its=eth.length&&R3()<.8?eth:all; if(!its.length) return;
      const it=its[Math.floor(R3()*its.length)], key=id+'|'+it; if(!c.drops[key]) c.drops[key]=1; }; // 솔로 보스만(블빵 없음), 소울 에테르가 있으면 대개 에테르
    // b229: 홍옥 반지 상자로 얻은 리4/컨4 예시 (캐릭터 번호, 몇 주 전(0 = 이번 주), 보스, 반지) — 그 주에 그 보스를 잡았을 때만, 절반쯤 판매 기록
    const HONG=[[0,3,'lotus','r4'],[0,1,'will','c4'],[1,2,'lucid','c4'],[0,0,'damien','r4']];
    const hong=(c,i,k)=>HONG.filter(h=>h[0]===i&&h[1]===k&&c.weekly[h[2]]&&(RING_DROPS.r_red[h[2]]||[]).includes(c.bosses[h[2]]?.diff)).forEach(([,,id,o])=>{ const key=id+'|hong_'+o; c.drops[key]=1; const q=IP[priceId('hong_'+o)]; if(q&&q.p>0&&k!==1) c.drev[key]={m:Math.round(q.p),a:Math.round(q.p/1e4)/1e4,p:1,i:'hong_'+o}; }); // 판매금 = 실제 공용 시세(일반 리4/컨4 와 같은 아이템)
    /* 9/17 패치(주간 결정석 가격 변경) 주부터 — 기록 = 지금 가격표와 같은 값 */ for(let k=4;k>=1;k--){ S.period={...S.period,week:wk(k)}; C.forEach((c,i)=>{ roll(c,[.97,.93,.88,.8][i]); extra(c,[.9,.8,.7,.6][i]); hong(c,i,k); });
      missRecord('w',wk(k),missNow('w')); const sum=weekSummary(wk(k)); if(sum.cleared>0) S.history.push(sum); }
    // 검마: 10/1 부터 새 가격(하드 4.65억) — 예시는 10월(이번 달)만, 솔로 → 결정석 가격표 값 그대로
    S.period={week:wk0,day:dayId(),month:monthId()};
    C.forEach((c,i)=>{ roll(c,[.85,.7,.55,.45][i]); extra(c,[.9,.8,.7,.6][i]); hong(c,i,0); c.monthly={}; c.mdrops={}; c.mdropOut={}; c.mdrev={}; }); C[0].monthly.blackmage=wk0; // 이번 주: 일요일쯤 진행 상황
  } finally { S=live; }
  DEMO_SC={}; st.characters.forEach((c,i)=>{ DEMO_SC[c.id]={date:dayId(),at:Date.now(),ok:true,level:c.level,items:{},guild:{suro:{now:[48200,31500,22800,9600][i]||0,max:0},flag:null,mission:null}}; });
  DEMO_GC={'스카니아|메보기예시길드':{date:dayId(),at:Date.now(),ok:true,t1:{guild_point:61500,ranking:418,guild_level:27,guild_master_name:'예시히어로'},t2:{guild_point:1832400,ranking:233,guild_level:27,guild_master_name:'예시히어로'}}};
  return st;
}
let demoWas=false;
function demoRun(fn,args,self){ if(demoDepth>0) return fn.apply(self,args);
  if(!demoAllowed()||!demoTabOk()){ if(demoWas){ demoWas=false; enterFor=null; document.body.classList.remove('demo'); } return fn.apply(self,args); } // 예시 → 내 캐릭터: 첫 화면처럼(팝인 없음)
  demoWas=true;
  const sig=demoSig(); if(!DEMO_ST||sig!==DEMO_SIG){ const keep=DEMO_ST&&DEMO_ST.activeId; DEMO_ST=demoBuild(); DEMO_SIG=sig; if(keep) DEMO_ST.activeId=keep; if(fn!==demoRenderRaw) setTimeout(()=>render(),0); }
  const s0=S, sc0=schedC, gc0=guildC; demoLive=s0; DEMO_SC0=sc0; S=DEMO_ST; schedC=DEMO_SC; guildC=DEMO_GC; demoDepth++; document.body.classList.add('demo');
  try{ return fn.apply(self,args); } finally { demoDepth--; S=s0; schedC=sc0; guildC=gc0; demoLive=null; } }
let demoRenderRaw=null;
{ demoRenderRaw=globalThis.render; const wrapR=name=>{ const f=globalThis[name]; if(typeof f==='function') globalThis[name]=function(...a){ return demoRun(f,a,this); }; };
  ['render','renderChars','renderGuild','renderTabView','renderBoss','renderTotal','renderLoot','fitMiss','repaintPrices','fitPriceCard','charEnter','wkPageRender'].forEach(wrapR);
  // 머리글(동기화 버튼 등)은 예시 데이터가 아니라 진짜 상태로: 예시 안에서 부르면 진짜 S 로 바꿔서 그림
  const hs=globalThis.renderHeaderSync; if(typeof hs==='function') globalThis.renderHeaderSync=function(...a){ if(demoDepth>0&&demoLive){ const d=S,sc=schedC; S=demoLive; schedC=DEMO_SC0||schedC; try{ return hs.apply(this,a); } finally { S=d; schedC=sc; } } return hs.apply(this,a); };
  const wrapX=name=>{ const f=globalThis[name]; if(typeof f==='function') globalThis[name]=function(...a){ if(S===DEMO_ST||(demoAllowed()&&demoTabOk()&&DEMO_ST&&demoDepth>0)) return name==='nx'?Promise.reject(new Error('demo')):undefined; return f.apply(this,a); }; };
  ['save','syncAll','refreshGuild','refreshSched','fillGuildCands','svSaveNow','svPushBg','nx'].forEach(wrapX);
  // 예시 화면이 떠 있는 동안 서버 쓰기(PUT/POST/DELETE) 요청은 보내지 않음 (읽기 GET 은 그대로: /api/prices 등)
  const svF=globalThis.svFetch; if(typeof svF==='function') globalThis.svFetch=function(path,opt,...r){ const m=String(opt?.method||'GET').toUpperCase(); if(m!=='GET'&&(S===DEMO_ST||demoDepth>0)) return Promise.reject(new Error('demo')); return svF.call(this,path,opt,...r); }; }
// 예시 위 띠: 작은 API 키 칸(한 줄) + '[예시] 예시 화면입니다 · …' — 매 렌더 뒤 #view 맨 위에
function demoTopHtml(){ return `<div class="demotop"><div class="card dmkey"><span class="dmk-t">넥슨 Open API 키로 내 본캐·부캐를 불러와요</span><button class="btn" id="importAccBtn">+ 캐릭터 추가 (API 키로 불러오기)</button></div>
  <div class="dmbanner" role="status"><span class="dmbadge">예시</span><b>예시 화면입니다 · API키를 넣으면 내 캐릭터로 보여요</b></div></div>`; }
function demoTopPut(){ const v=$('#view'); if(!v) return; const on=demoAllowed()&&demoTabOk(); document.body.classList.toggle('demo',on); const t=v.querySelector(':scope>.demotop'); if(!on){ t?.remove(); return; } if(!t) v.insertAdjacentHTML('afterbegin',demoTopHtml()); }
new MutationObserver(()=>demoTopPut()).observe(document.getElementById('view'),{childList:true});
// 예시 화면에서: 캐릭터 클릭 = 예시 캐릭터 바꿈, 바꾸는 버튼(체크·드롭·삭제·수정 등)은 막음, '+ 추가' = 실제 키 등록 창
document.addEventListener('click',e=>{ if(!(demoAllowed()&&demoTabOk())) return; const t=e.target;
  if(t.closest('#importAccBtn,#addCharBtn,.side .addbtn,#charAdd')) return; // 실제 로그인 흐름 그대로
  const ch=t.closest('#charList .char[data-id]'); if(ch&&!t.closest('.drag-h,[data-edit],[data-move]')){ e.preventDefault(); e.stopImmediatePropagation(); if(DEMO_ST){ const sw=tab!=='boss', sy=scrollY, sx=scrollX; DEMO_ST.activeId=ch.dataset.id; tab='boss'; syncTabs(); render(); if(sw) tabTop(); else { const back=()=>{ if(scrollY!==sy||scrollX!==sx) scrollTo(sx,sy); }; back(); requestAnimationFrame(back); } } return; }
  const OK='[data-wkpg],[data-wlpg],select.wlsel,[data-tab],[data-filter],[data-pckind],[data-pctab],[data-cpage],.sortlink,[data-sort],[data-lt],[data-page],.pgbtn,a[href]';
  if(t.closest('#view,#charList')&&!t.closest(OK)){ e.preventDefault(); e.stopImmediatePropagation(); } },true);
// 처음 열 때(로그인 전): 이번 주 보스 예시
setTimeout(()=>{ if(demoAllowed()&&tab!=='live'){ tab='boss'; syncTabs(); render(); } },0);
// 가격(결정석·공용 아이템 시세)이 늦게 오면 예시를 새 가격으로 다시 만들고 다시 그림
setInterval(()=>{ if(DEMO_ST&&demoAllowed()&&demoTabOk()&&demoSig()!==DEMO_SIG) render(); },1000);
// 구글 드라이브 모드(github.io)는 공용 시세를 안 받음 → 예시를 보여 줄 때만 공용 시세(GET /api/prices, 로그인 없이)를 한 번 받아서 예시 판매값에 씀
setTimeout(async()=>{ if(SV_ON||!SYNC_TEST_URL||!/github\.io$/.test(location.hostname)||!demoAllowed()||Object.keys(itemPrices()).length) return;
  try{ const r=await fetch(SYNC_TEST_URL+'/api/prices',{cache:'no-store'}); if(!r.ok) return; const j=await r.json(); if(j&&j.prices){ itemPricePut(j.prices); render(); } }catch(e){} },0);
// b217: 모든 선언이 끝난 뒤 한 번 더 그림 (시작 렌더가 아직 없는 값 때문에 실패했어도 화면이 제대로 나오게)
bootRender('end'); pageTop(); requestAnimationFrame(()=>pageTop()); // b223
