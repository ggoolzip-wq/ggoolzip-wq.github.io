'use strict';
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
  API_DELAY_MS: 250               // 호출 간 간격 (개발 단계 키: 초당 5건 제한)
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
  'kaling_easy':320000000, 'kaling_normal':593000000, 'kaling_hard':1560000000, 'kaling_extreme':5387000000,
  'star_normal':576000000, 'star_hard':2678000000,
  'limbo_normal':995000000, 'limbo_hard':2385000000,
  'baldrix_normal':1320000000, 'baldrix_hard':3078000000,
  'bellona_easy':396000000, 'bellona_normal':824000000, 'bellona_hard':2950000000,
  'jupiter_normal':1560000000, 'jupiter_hard':4845000000,
  // 월간
  'blackmage_hard':465000000, 'blackmage_extreme':5680000000
};

const D = {easy:'이지',normal:'노말',hard:'하드',chaos:'카오스',extreme:'익스트림'};
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
  {id:'limbo',name:'림보',type:'weekly',diffs:['normal','hard']},
  {id:'baldrix',name:'발드릭스',type:'weekly',diffs:['normal','hard']},
  {id:'bellona',name:'벨로나',type:'weekly',diffs:['easy','normal','hard']},
  {id:'jupiter',name:'유피테르',type:'weekly',diffs:['normal','hard']},
  {id:'blackmage',name:'검은 마법사',type:'monthly',diffs:['hard','extreme'],aliases:['검마']}
];
const TYPE_LABEL = {weekly:'주간 보스',monthly:'월간 보스'};
/* 보스 초상화 (64px WebP, base64 내장 — 오프라인 동작). 출처: 게임 내 보스 선택 UI 일러스트("Boss UI - *.png")를
 * MapleStory Fandom Wiki(maplestory.fandom.com) 및 MapleStory Wiki(maplestorywiki.net — 최초의 대적자·찬란한 흉성·발드릭스·림보)에서
 * 받아 얼굴 위주로 잘라 축소. 이미지가 없으면 글자 아이콘으로 대체. */
const BOSS_ICONS = /*__BOSS_ICONS__*/{};
function bossIcon(b){
  const src=BOSS_ICONS[b.id];
  if(src) return `<img class="bicon" src="${src}" alt="" aria-hidden="true">`;
  let h=0; for(const ch of b.id) h=(h*31+ch.charCodeAt(0))%360;
  return `<span class="bicon fb" style="--h:${h}" aria-hidden="true">${esc(b.name.replace(/^(선택받은|감시자|최초의|찬란한)\s*/,'').slice(0,1))}</span>`;
}
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
  r_black:{n:'흑옥의 보스 반지 상자',s:'흑옥 반지 상자',set:'반지',note:'1~4레벨 특수 스킬 반지'},
  r_white:{n:'백옥의 보스 반지 상자',s:'백옥 반지 상자',set:'반지',note:'3~4레벨 특수 스킬 반지'},
  r_life:{n:'생명의 보스 반지 상자',s:'생명 반지 상자',set:'반지',note:'3~4레벨 특수 스킬 반지 또는 생명의 연마석'},
  // 에테르넬 방어구 교환 재료 — 확정 지급, 정보 칩 전용(클릭·기록·수익 없음). ETERNAL 참고
  e_kalos_f:{n:'남겨진 칼로스의 의지 조각',set:'에테르넬'}, e_kalos:{n:'남겨진 칼로스의 의지',set:'에테르넬'},
  e_adv_f:{n:'이어진 고대의 결의 조각',set:'에테르넬'}, e_adv:{n:'이어진 고대의 결의',set:'에테르넬'},
  e_kaling_f:{n:'뒤엉킨 흉수의 고리 조각',set:'에테르넬'}, e_kaling:{n:'뒤엉킨 흉수의 고리',set:'에테르넬'},
  e_star_f:{n:'황홀한 환상의 단편 조각',set:'에테르넬'}, e_star:{n:'황홀한 환상의 단편',set:'에테르넬'},
  e_bellona:{n:'저주받은 원혼의 잔재',set:'에테르넬'}, e_limbo:{n:'왜곡된 욕망의 결정',set:'에테르넬'},
  e_baldrix:{n:'영원한 충성의 흔적',set:'에테르넬'}, e_jupiter:{n:'뒤틀린 갈망의 편린',set:'에테르넬'}
};
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
const ring4=k=>{ const b=BOX_INFO[k]; return b?{r4:b.r*b.lv4,c4:b.c*b.lv4}:null; };
const CHAOS_BOX=['루즈 컨트롤 머신 마크 (얼굴장식)','마력이 깃든 안대 (눈장식)','몽환의 벨트 (벨트)','저주받은 마도서 선택 상자 (포켓)','거대한 공포 (반지)','커맨더 포스 이어링 (귀고리)','고통의 근원 (펜던트)'];
/* 드롭 칩 툴팁 (2026-10-10 사용자 요청): 반지 상자(녹옥 제외)·혼돈의 칠흑 장신구 상자·에테르넬 칩에만. 그 외 칩(에르다 포함)은 툴팁·title 없음.
 * 반지 상자 = 이름 + '리4: x%' + '컨4: y%' 만 / 칠흑 상자 = 이름 + 구성품. 난이도·'클릭: 획득 +1' 같은 안내 줄 없음. */
function itemTip(k){
  const it=ITEMS[k]; if(!it) return '';
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
  r_life:{kalos:['chaos','extreme'],kaling:['hard','extreme'],limbo:['normal','hard'],baldrix:['normal','hard'],adversary:['hard','extreme'],star:['hard'],jupiter:['normal','hard'],bellona:['hard']}
};
const SET_LABEL = {'반지':'특수 스킬 반지 상자 (낮은 확률)','광휘':'광휘의 보스 세트','칠흑':'칠흑의 보스 세트','여명':'여명의 보스 세트','보장':'보스 장신구 세트','해머':'익셉셔널 강화 재료','연마석':'연마석 (특수 스킬 반지 강화 재료)','에테르':'소울 에테르 (소울웨폰 재료)'};
// 보스별 [아이템, 드롭 난이도들] — 해당 난이도를 선택했을 때만 표시
const DROPS = {
  zakum:[['cfs',['chaos']],['aquatic',['chaos']],['zbelt',['chaos']]],
  magnus:[['wentus',['hard']],['shoulder',['hard']]],
  papulatus:[['papmark',['chaos']]],
  lotus:[['lcm',['hard','extreme']],['tc',['extreme']]],
  damien:[['eye',['hard']]],
  slime:[['gar',['normal','chaos']]],
  lucid:[['belt',['hard']],['twilight',['normal','hard']]],
  will:[['book',['hard']],['twilight',['normal','hard']]],
  dusk:[['terror',['chaos']],['estella',['normal','chaos']]],
  jinhilla:[['sos',['hard']],['daybreak',['normal','hard']]],
  dunkel:[['cfe',['hard']],['estella',['normal','hard']]],
  seren:[['mitra',['hard','extreme']],['daybreak',['normal','hard','extreme']],['h_face',['extreme']]],
  kalos:[['h_eye',['extreme']],['g_life',['normal','chaos','extreme']]],
  adversary:[['legacy',['hard','extreme']],['g_life',['normal','hard','extreme']],['se1',['normal','hard','extreme']]],
  kaling:[['chaosbox',['normal','hard','extreme']],['h_ear',['extreme']],['g_life',['normal']],['g_faith',['hard','extreme']],['se1',['normal','hard','extreme']]],
  star:[['bliss',['hard']],['chaosbox',['normal','hard']],['g_life',['normal']],['g_faith',['hard']],['se2',['normal','hard']]],
  limbo:[['whisper',['hard']],['chaosbox',['normal','hard']],['g_faith',['normal','hard']],['se3',['normal','hard']]],
  baldrix:[['oath',['hard']],['chaosbox',['normal','hard']],['g_faith',['normal','hard']],['se3',['normal','hard']]],
  bellona:[['spirit',['hard']],['chaosbox',['normal','hard']],['g_life',['normal']],['g_faith',['hard']],['se2',['normal','hard']]],
  jupiter:[['sin',['hard']],['chaosbox',['normal','hard']],['g_faith',['normal','hard']],['se4',['normal','hard']]],
  blackmage:[['genesis',['hard','extreme']],['h_belt',['extreme']]]
};
const dropsFor = (b,diff) => [...(DROPS[b.id]||[]).filter(([,ds])=>ds.includes(diff)).map(([k])=>k),
  ...Object.entries(RING_DROPS).filter(([,m])=>(m[b.id]||[]).includes(diff)).map(([k])=>k)];
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
  bellona:{normal:['e_bellona',1],hard:['e_bellona',2]}, limbo:{normal:['e_limbo',1],hard:['e_limbo',2]},
  baldrix:{normal:['e_baldrix',1],hard:['e_baldrix',2]}, jupiter:{normal:['e_jupiter',1],hard:['e_jupiter',2]}
};
const eternalFor = (b,diff) => { const v=ETERNAL[b?.id]?.[diff]; return v?{k:v[0],n:v[1]}:null; };
function eternalTip(k,n,diff){
  const up=E_UP[k], main=up||k, it=ITEMS[k], party=['e_bellona','e_limbo','e_baldrix','e_jupiter'].includes(main)?'개인보상':'단체보상';
  return `${it.n} ${n}개 (${party})\n`+(up?`2개 → ${ITEMS[up].n} 1개로 교환\n${ITEMS[up].n} 10개 → `:`10개 → `)+`에테르넬 ${E_PART[main]} 중 1개 선택`;
}
function itemIcon(k){
  const it=ITEMS[k], src=ITEM_ICONS[k];
  return src?`<img src="${src}" alt="" aria-hidden="true">`:`<span class="ifb" aria-hidden="true">${esc((it?.n||'?').slice(0,1))}</span>`;
}
const dropOpen=new Set(); // '+N'을 눌러 펼친 보스 행
function dropsHtml(b,diff,c){
  const ks=dropsFor(b,diff), en=erdaFor(b,diff); if(!ks.length&&!en&&!eternalFor(b,diff)) return '';
  const et=eternalFor(b,diff);
  const erda=(en?`<span class="drop erda" aria-label="솔 에르다의 기운 ${en}개">${itemIcon('erda')}<b class="ecnt">${en}</b></span>`:'')
    +(et?`<span class="drop erda eter" data-tip="${esc(eternalTip(et.k,et.n,diff))}" aria-label="${esc(ITEMS[et.k].n)} ${et.n}개">${itemIcon(et.k)}<b class="ecnt">${et.n}</b></span>`:'');
  const cnt=k=>c?dropCount(c,b,k):0;
  const chip=k=>{const it=ITEMS[k], n=cnt(k);
    return `<span class="drop s-${it.set} ${n?'got':''}" ${c?`data-drop="${b.id}|${k}" role="button" tabindex="0"`:''}${(t=>t?` data-tip="${esc(t)}"`:'')(itemTip(k))}>${itemIcon(k)}<span class="dn">${esc(it.s||it.n)}</span>${n?`<b class="dcnt">×${n}</b><span class="ddec" data-dropdec="${b.id}|${k}" role="button" aria-label="1개 취소">−</span>`:''}</span>`;};
  // 2026-10-10 사용자 요청: 아이템을 '+N' 묶음 칩으로 합치지 않음 — 생명/신념 연마석, 소울 에테르 1~4단계, 반지 상자 모두 각자 칩(각자 아이콘·클릭 +1), 넘치면 다음 줄로
  const shown=ks;
  // 아래 줄: 이 보스에서 획득한 아이템 (모든 화면과 같은 형식: 이름(N인 분배) ×개수 결과)
  const mine=c?(d=>({items:Object.fromEntries(Object.entries(d.items).filter(([k])=>k.split('|')[0]===b.id)),outcomes:d.outcomes}))(charDrops(c,b.type)):null;
  const ringLine=mine?itemsInline(mine.items,{outs:mine.outcomes}):'';
  return `<div class="drops open" aria-label="주요 희귀 드롭">${erda}${shown.map(chip).join('')}</div>${ringLine?`<div class="ringouts">${ringLine}</div>`:''}`;
}
function changeDrop(key, delta){
  const c=activeChar(); if(!c) return; const [slot,item]=key.split('|'); const b=findBoss(slot); if(!b||!ITEMS[item]) return;
  if(delta>0 && isRing(item)){ openRing(key); return; } // 반지 상자는 결과를 고른 뒤 +1
  const m=dropMap(c,b.type); const n=Math.max(0,(+m[key]||0)+delta); if(n) m[key]=n; else delete m[key];
  const pty=curParty(c,slot);
  if(delta<0 && isRing(item)){ const om=outMap(c,b.type); const l=om[key]; if(l&&l.length) l.pop(); if(!n||(l&&!l.length)) delete om[key]; } // 가장 최근 획득(결과 포함) 취소
  save(); render(); toast(`${ITEMS[item].n}${delta>0?partyTxt(pty):''} ${delta>0?'획득':'취소'} — ${c.name} 이번 ${b.type==='monthly'?'달':'주'} ${n}개`);
}
/* 반지 상자 결과 선택 모달 (닫기 = 기록 안 함) */
let ringPending=null;
function openRing(key){
  const c=activeChar(); const [slot,item]=key.split('|'); const b=findBoss(slot); if(!c||!b) return;
  ringPending={cid:c.id,key};
  const diff=c.bosses[slot]?.diff;
  $('#ringBoxIcon').innerHTML=itemIcon(item); $('#ringTitle').textContent=`${ITEMS[item].n} 획득!`;
  const pty=curParty(c,slot);
  $('#ringSub').textContent=`${c.name} · ${b.name}${diff?` (${D[diff]})`:''}${pty>1?` · ${pty}인 분배`:''} — 상자에서 무엇이 나왔나요?`;
  $('#ringModal').classList.add('show'); setTimeout(()=>document.querySelector('#ringModal [data-ring="r4"]')?.focus(),30);
}
function closeRing(){ ringPending=null; $('#ringModal').classList.remove('show'); }
function chooseRing(o){
  const p=ringPending; if(!p||!(o in OUT_LABEL)) return; closeRing();
  const c=S.characters.find(x=>x.id===p.cid); if(!c) return; const [slot,item]=p.key.split('|'); const b=findBoss(slot);
  const m=dropMap(c,b.type); m[p.key]=(+m[p.key]||0)+1;
  const pty=curParty(c,slot);
  const om=outMap(c,b.type); const l=om[p.key]||(om[p.key]=[]);
  // 기능 도입 전 획득분(결과 없음)은 '개수 − 결과 수' = 미기록으로 표시
  l.push(o); save(); render();
  if(o==='x') toast(`${ITEMS[item].s}${partyTxt(pty)} — 꽝 기록 (${c.name} 이번 ${b.type==='monthly'?'달':'주'} ${m[p.key]}개)`); else celebrate(o);
}
/* 축하 연출: 캔버스 불꽃놀이 + 꽃가루 (~2.6초, 외부 라이브러리 없음) */
function celebrate(o){
  const cv=$('#fx'), msg=$('#congrats');
  msg.innerHTML=`<div class="cg-in">${o==='r4'?miniIcon('ring_restraint'):miniIcon('ring_continuous')}<div class="cg-big">축하드립니다!</div><div class="cg-sub">${OUT_NAME[o]} 획득 🎉</div></div>`;
  msg.classList.add('show'); cv.classList.add('show'); celebrate.running=true;
  clearTimeout(celebrate._t); celebrate._t=setTimeout(endCelebrate,2700);
  if(matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const dpr=Math.min(2,devicePixelRatio||1), W=innerWidth, H=innerHeight; cv.width=W*dpr; cv.height=H*dpr; const g=cv.getContext('2d'); g.setTransform(dpr,0,0,dpr,0,0);
  const P=[], COL=['#ff5a5f','#ffb400','#4ecdc4','#a66cff','#ffe66d','#ff8fab','#7bdff2','#9be84a'];
  const burst=(x,y)=>{ const n=70, col=COL[Math.random()*COL.length|0]; for(let i=0;i<n;i++){ const a=Math.PI*2*i/n, v=2+Math.random()*4; P.push({x,y,vx:Math.cos(a)*v,vy:Math.sin(a)*v,life:1,dec:.012+Math.random()*.012,r:2+Math.random()*1.5,col:Math.random()<.3?COL[Math.random()*COL.length|0]:col,k:'s'}); } };
  for(let i=0;i<90;i++) P.push({x:Math.random()*W,y:-20-Math.random()*H*.5,vx:(Math.random()-.5)*2,vy:2+Math.random()*3,life:1,dec:.004,r:4+Math.random()*4,col:COL[i%COL.length],k:'c',rot:Math.random()*6,vr:(Math.random()-.5)*.3});
  const t0=performance.now(); let nb=0;
  const step=now=>{ if(!celebrate.running) return; const t=now-t0;
    while(nb<6 && t>nb*320){ burst(W*(.18+Math.random()*.64), H*(.15+Math.random()*.35)); nb++; }
    g.clearRect(0,0,W,H);
    for(const q of P){ if(q.life<=0) continue; q.x+=q.vx; q.y+=q.vy; q.life-=q.dec;
      if(q.k==='s'){ q.vx*=.985; q.vy=q.vy*.985+.06; g.globalAlpha=Math.max(0,q.life); g.fillStyle=q.col; g.beginPath(); g.arc(q.x,q.y,q.r,0,7); g.fill(); }
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
    S.characters.forEach(normChar);
    S.dq=Object.assign(defaultDq(),S.dq&&typeof S.dq==='object'?S.dq:{}); ['off','charOff','hide'].forEach(k=>{ if(!S.dq[k]||typeof S.dq[k]!=='object') S.dq[k]={}; });
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
  // 총 수익 집계 시작 주: 가장 오래된 기록 주(없으면 이번 주). 한 번 정하면 저장되어 유지
  { const ws=(S.history||[]).map(h=>h.week).filter(Boolean).sort(); const first=ws[0]||S.period?.week||weekId();
    if(!S.startWeek || first<S.startWeek) S.startWeek=first; }
  if(!Array.isArray(S.worldOrder)) S.worldOrder=[];
  // 단일 API 키 → 여러 넥슨 계정(계정마다 라벨 + 키). 기존 키는 '본계정'이 됨
  if(!Array.isArray(S.settings.accounts)) S.settings.accounts=[];
  if(S.settings.apiKey){
    const k=String(S.settings.apiKey).trim();
    if(k && !S.settings.accounts.some(a=>a.key===k)) S.settings.accounts.unshift({id:uid(),label:S.settings.accounts.length?'계정'+(S.settings.accounts.length+1):'본계정',key:k});
    delete S.settings.apiKey;
  }
}
/* 보스·난이도별 최대 파티 인원 (기본 CONFIG.MAX_PARTY=6). 익스트림 스우 2인 · 최초의 대적자/찬란한 흉성/벨로나/림보/발드릭스/유피테르 3인 */
const PARTY_MAX = { lotus:{extreme:2}, adversary:3, star:3, bellona:3, limbo:3, baldrix:3, jupiter:3 };
const partyMax = (b,diff) => { const v=PARTY_MAX[b?.id??b]; const n=typeof v==='object'?v?.[diff]:v; return Math.max(1,Math.min(CONFIG.MAX_PARTY,+n||CONFIG.MAX_PARTY)); };
/* 저장된 파티 인원이 한도를 넘으면 한도로 낮춤 (나머지는 그대로) */
function clampParty(c,slot){ const cfg=c?.bosses?.[slot]; if(!cfg) return; const b=findBoss(slot); if(!b) return; const m=partyMax(b,cfg.diff||b.diffs[0]); if((parseInt(cfg.party)||1)>m) cfg.party=m; }
function normChar(c){ ['bosses','weekly','monthly','auto','sync','drops','mdrops','dropOut','mdropOut'].forEach(k=>c[k]=c[k]||{}); delete c.dropParty; delete c.mdropParty; c.world=c.world||''; Object.keys(c.bosses).forEach(s=>clampParty(c,s)); }
// updatedAt: 데이터 내용이 '실제로' 바뀐 시각 (구글 드라이브 동기화에서 어느 쪽이 최신인지 비교)
// — 기기마다 다른 값·자동으로 계속 바뀌는 값(테마, 선택한 캐릭터, 날짜(period), 마지막 동기화 시각, 캐릭터 sync/이미지/EXP, 계정 상태)은
//   contentSig 에서 빠지므로 updatedAt 을 바꾸지 않고 드라이브 저장도 하지 않음 (2026-10-10: 이것 때문에 '어느 데이터를 쓸까요?'가 반복됐음)
let lastBody=null, lastSig=null;
function bodyOf(){ const u=S.updatedAt; S.updatedAt=0; const b=JSON.stringify(S); S.updatedAt=u; return b; }
function save(){
  const sig=contentSig(S), changed=sig!==lastSig;
  if(changed){ S.updatedAt=Date.now(); lastSig=sig; }
  lastBody=bodyOf();
  localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(S));
  if(changed) gdChanged();
}
const price = (b,diff) => { const k=priceKey(b,diff); return (k in S.settings.prices)?S.settings.prices[k]:(PRICE_CONFIG[k]||0); };
const activeChar = () => S.characters.find(c=>c.id===S.activeId);
const uid = () => Math.random().toString(36).slice(2,9)+Date.now().toString(36).slice(-4);
const worldOf = c => c.world || '월드 미지정';

/* ---------- 리셋 처리 ---------- */
function resetCore(){
  const now={week:weekId(),day:dayId(),month:monthId()}; let changed=false; const msgs=[];
  if(S.period.week!==now.week){
    const sum=weekSummary(S.period.week);
    if(sum.cleared>0 && !S.history.some(h=>h.week===S.period.week)) S.history.push(sum);
    S.history.sort((a,b)=>a.week<b.week?-1:1);
    S.characters.forEach(c=>{c.weekly={}; c.drops={}; c.dropOut={}; for(const k in c.auto) if(findBoss(k)?.type==='weekly') delete c.auto[k];});
    msgs.push('주간 보스가 초기화되었습니다 (지난 주 기록 저장됨)'); changed=true;
  }
  if(S.period.month!==now.month){
    const ms=monthSummary(S.period.month); if(ms.cleared>0 && !S.monthHistory.some(h=>h.month===ms.month)) S.monthHistory.push(ms);
    S.monthHistory.sort((a,b)=>a.month<b.month?-1:1);
    S.characters.forEach(c=>{c.monthly={}; c.mdrops={}; c.mdropOut={}; for(const k in c.auto) if(findBoss(k)?.type==='monthly') delete c.auto[k];}); msgs.push('월간 보스 초기화'); changed=true; }
  if(S.period.day!==now.day) changed=true;
  if(changed) S.period=now;
  return {changed,msgs};
}

function checkResets(){ const r=resetCore(); if(r.changed){ save(); if(r.msgs.length) toast(r.msgs.join(' · ')); } return r.changed; }
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
  for(const b of BOSSES){ if(b.type!=='weekly') continue; const cfg=c.bosses[b.id]; if(!cfg?.enabled) continue;
    const diff=b.diffs.includes(cfg.diff)?cfg.diff:b.diffs[0], party=curParty(c,b.id);
    l.push({slot:b.id,name:b.name,diff,party,value:Math.floor(price(b,diff)/party)}); }
  l.sort((a,b)=>b.value-a.value); const top=l.slice(0,S.settings.weeklyLimit);
  return {list:top, all:l.length, meso:top.reduce((s,x)=>s+x.value,0)};
}
function allRevenue(){
  const per=S.characters.map(c=>({c,r:charRevenue(c)}));
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
const cleanOut = m => Object.fromEntries(Object.entries(m||{}).filter(([,a])=>Array.isArray(a)&&a.length).map(([k,a])=>[k,a.filter(o=>o==='r4'||o==='c4'||o==='x')]));
const OUT_LABEL = {r4:'리4', c4:'컨4', x:'꽝'};
/* 파티 인원: 이번 주/이번 달의 획득 기록은 그 캐릭터의 해당 보스 '파티 인원' 설정을 따릅니다 (드롭다운을 바꾸면 이번 기간 기록 표시도 바뀜).
 * 주간/월간 초기화로 기록에 저장될 때 키에 인원이 고정됩니다: 'boss|item'(1인) / 'boss|item#N'(N인 분배) */
const curParty = (c,slot) => { const cfg=c?.bosses?.[slot], b=findBoss(slot); return Math.max(1, Math.min(b?partyMax(b,cfg?.diff||b.diffs[0]):CONFIG.MAX_PARTY, parseInt(cfg?.party)||1)); };
const partyTxt = p => p>1 ? ` (${p}인 분배)` : '';
// 'boss|item', 'boss|item#3', 'item', 'item#2' → {slot, it, party}
function parseIK(k){ const [a,pp]=String(k).split('#'); const i=a.indexOf('|'); return {slot:i>=0?a.slice(0,i):'', it:i>=0?a.slice(i+1):a, party:Math.max(1,parseInt(pp)||1)}; }
// 이번 기간 획득 기록 → 현재 파티 인원을 붙인 키
function charDrops(c,type){
  const m=type==='monthly'?c.mdrops:c.drops, om=type==='monthly'?c.mdropOut:c.dropOut, I={}, O={};
  for(const [k,n] of Object.entries(m||{})){ if(!(+n>0)) continue; const slot=k.split('|')[0], p=curParty(c,slot), key=p>1?`${k}#${p}`:k;
    I[key]=+n; const l=(om||{})[k]; if(Array.isArray(l)&&l.length) O[key]=l.filter(o=>o==='r4'||o==='c4'||o==='x'); }
  return {items:I, outcomes:O};
}
const charAllDrops = c => { const w=charDrops(c,'weekly'), m=charDrops(c,'monthly'); return {items:{...w.items,...m.items}, outcomes:{...w.outcomes,...m.outcomes}}; };
const OUT_NAME = {r4:'리스트레인트 링 4레벨', c4:'컨티뉴어스 링 4레벨'};
const miniIcon = k => ITEM_ICONS[k] ? `<img class="ric" src="${ITEM_ICONS[k]}" alt="" aria-hidden="true">` : '';
const outIcon = o => o==='r4'?miniIcon('ring_restraint'):o==='c4'?miniIcon('ring_continuous'):'';
function outTally(list, n){ const t={r4:0,c4:0,x:0,un:0}; (list||[]).forEach(o=>{ if(o in t) t[o]++; }); t.un=Math.max(0,(+n||0)-(list||[]).length); return t; }
// 순서대로: '미기록 · 리4 · 꽝' / compact: '리4×2 · 꽝×3 · 미기록×1'
function outHtml(list, n, compact){
  list=list||[]; const t=outTally(list,n); const parts=[];
  if(compact){ for(const o of ['r4','c4','x']) if(t[o]) parts.push(`<span class="ro ro-${o}">${outIcon(o)}${OUT_LABEL[o]}${t[o]>1?'×'+t[o]:''}</span>`); }
  else { if(t.un) parts.push(`<span class="ro ro-un">미기록${t.un>1?'×'+t.un:''}</span>`); list.forEach(o=>parts.push(`<span class="ro ro-${o}">${outIcon(o)}${OUT_LABEL[o]}</span>`)); }
  if(compact&&t.un) parts.push(`<span class="ro ro-un">미기록${t.un>1?'×'+t.un:''}</span>`);
  return parts.length?`<span class="routs">${parts.join('<span class="rsep"> · </span>')}</span>`:'';
}
// 주간 기록: 주간 보스 결정석 수익 + 주간 보스 획득 아이템 (월간 보스는 monthSummary 로 따로)
function weekSummary(wid){
  const a=allRevenue();
  const perChar=a.per.map(p=>({id:p.c.id, name:p.c.name, job:p.c.job, world:p.c.world, meso:p.r.meso, count:p.r.wlist.length, bosses:p.r.wlist.map(bossTag), ...(sp=>({items:cleanItems(sp.items), outcomes:cleanOut(sp.outcomes)}))(charDrops(p.c,'weekly'))}));
  return {week:wid, weeklyOnly:true, total:a.total, cleared:a.per.reduce((s,p)=>s+p.r.wlist.length,0), crystals:a.count, items:perChar.reduce((s,p)=>s+itemSum(p.items),0), perChar};
}
function monthSummary(mid){
  const a=allRevenue();
  return {month:mid, total:a.monthTotal, cleared:a.per.reduce((s,p)=>s+p.r.mlist.length,0),
    perChar:a.per.filter(p=>p.r.mlist.length||itemSum(cleanItems(p.c.mdrops))).map(p=>({id:p.c.id, name:p.c.name, meso:p.r.monthMeso, bosses:p.r.mlist.map(bossTag), ...(sp=>({items:cleanItems(sp.items), outcomes:cleanOut(sp.outcomes)}))(charDrops(p.c,'monthly'))}))};
}
/* 획득 아이템 줄 (모든 화면 공통 형식): [아이콘] 아이템 이름 (N인 분배) ×개수 · 반지 상자는 결과 집계(리4·컨4·꽝·미기록)
 * byBoss: 보스별로 따로 (보스 이름 표시) / 기본: 아이템 + 인원별 합계 */
function dropLine(it, party, n, outs, boss){
  const I=ITEMS[it];
  return `<span class="dl ${party>1?'pty':''}" title="${esc((boss?boss+' · ':'')+I.n+partyTxt(party))} ×${n}">${boss?`<span class="dlb">${esc(boss)}</span>`:''}<span class="dlt">${itemIcon(it)}<span class="dln">${esc(I.n+partyTxt(party))}</span> <b class="dlc">×${n}</b>${isRing(it)?' '+outHtml(outs,n,true):''}</span></span>`;
}
function itemsInline(items, opts={}){
  const agg={}, outs={}, meta={};
  for(const [k,n] of Object.entries(items||{})){ const {slot,it,party}=parseIK(k); if(!ITEMS[it]||!(+n>0)) continue;
    const a=(opts.byBoss?slot+'|':'')+it+'#'+party; meta[a]={slot,it,party};
    agg[a]=(agg[a]||0)+(+n); if(isRing(it)) (outs[a]=outs[a]||[]).push(...((opts.outs||{})[k]||[])); }
  const bi=s=>{ const i=BOSSES.findIndex(b=>b.id===s); return i<0?999:i; }, ii=it=>Object.keys(ITEMS).indexOf(it);
  const ks=Object.keys(agg).sort((x,y)=>{ const X=meta[x], Y=meta[y]; return (opts.byBoss?bi(X.slot)-bi(Y.slot):0) || ii(X.it)-ii(Y.it) || X.party-Y.party; });
  if(!ks.length) return opts.empty??'';
  return `<span class="dls">${ks.map(a=>{ const {slot,it,party}=meta[a]; return dropLine(it,party,agg[a],outs[a],opts.byBoss?(findBoss(slot)?.name||''):''); }).join('')}</span>`;
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
let lastCall=0;
/* ---------- 넥슨 계정(API 키) ----------
 * character/list · scheduler 는 '키 소유 계정'의 캐릭터만 조회되므로 캐릭터마다 소속 계정(accId)의 키를 사용 */
const accounts = () => S.settings.accounts;
const accById = id => accounts().find(a=>a.id===id);
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
    <li>그래도 비어 있으면 [이름으로 직접 추가]를 사용하세요. 이름 조회는 이 키로도 계속 됩니다.</li></ul>`;
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
async function nx(path, params={}, keyArg){
  const key=(keyArg||'').trim(); if(!key) throw new Error('API 키가 설정되지 않았습니다');
  const wait=lastCall+CONFIG.API_DELAY_MS-Date.now(); if(wait>0) await sleep(wait); lastCall=Date.now();
  const qs=new URLSearchParams(Object.entries(params).filter(([,v])=>v!=null&&v!=='')).toString();
  let res;
  try{ res=await fetch(CONFIG.API_BASE+path+(qs?'?'+qs:''),{headers:{'x-nxopen-api-key':key,'accept':'application/json'}}); }
  catch(e){ const err=new Error('네트워크 오류 — 인터넷 연결 또는 브라우저 확장 프로그램·네트워크의 차단 여부를 확인하세요.'); err.status=0; err.code='NETWORK'; throw err; }
  let body=null; try{ body=await res.json(); }catch(e){}
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
function applyScheduler(c, data){
  const d=String(data?.date||'').slice(0,10);
  const staleWeek = d && d < S.period.week, staleMonth = d && d.slice(0,7) < S.period.month;
  const unmatched=[]; let checked=0;
  const isDone = r => flagOn(r.complete_flag) || flagOn(r.clear_flag); // 공식 스펙: complete_flag (일부 문서는 clear_flag 표기)
  const rows=(data?.boss_contents||[]).slice().sort((a,b)=>isDone(b)-isDone(a));
  const seen={};
  for(const r of rows){
    const cyc=String(r.cycle||'').toLowerCase();
    if(/daily|일일|일간/.test(cyc)) continue; // 일일 보스는 추적하지 않음
    const b=matchBoss(r.content_name), diff=normDiff(r.difficulty);
    if(!b && RETIRED_BOSS_NAMES.includes(normName(r.content_name))) continue; // 일일 보스로 바뀐 보스
    if(!b && isSeasonBoss(r.content_name)) continue; // 시즌 보스(메이린 등)는 추적 대상이 아님 — '매칭 안 된 보스'에서 제외
    if(!b || !diff || !b.diffs.includes(diff)){ unmatched.push(`${r.content_name}(${r.difficulty||'?'})`); continue; }
    if(seen[b.id]) continue;
    const done=isDone(r), reg=flagOn(r.registration_flag);
    const cfg=c.bosses[b.id];
    if(done){
      if((b.type==='weekly'&&staleWeek)||(b.type==='monthly'&&staleMonth)) continue;
      seen[b.id]=true;
      c.bosses[b.id]={enabled:true,diff,party:cfg?.party||1}; clampParty(c,b.id);
      if(b.type==='weekly'){ if(!c.weekly[b.id]) checked++; c.weekly[b.id]=true; }
      else { if(!c.monthly[b.id]) checked++; c.monthly[b.id]=c.monthly[b.id]||S.period.week; }
      c.auto[b.id]=true;
    } else if(reg && S.settings.autoEnable && !cfg){
      seen[b.id]=true; c.bosses[b.id]={enabled:true,diff,party:1};
    }
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
  c.sync=Object.assign(c.sync||{},{imgAt:Date.now()});
}
let syncing=false;
const LOAD_SYNC_GAP_MS=3e3, LOAD_SYNC_KEY='mapleBossTracker.loadSyncAt'; // 페이지 열 때 자동 동기화 최소 간격 (아래 loadSyncDue)
async function syncAll(opts={}){
  if(syncing) return; if(!hasApi()){ if(!opts.silent) toast('+ 추가에서 넥슨 API 키를 먼저 등록하세요'); return; }
  syncing=true; renderHeaderSync(); let total=0, errs=0, assigned=0; const badAcc=new Set(), accMsgs=[];
  try{
    // 1) 계정별 캐릭터 목록 → 소속 계정 자동 배정 + 레벨/직업/월드/ocid 갱신
    for(const a of accounts()){
      if(!a.key) continue;
      try{ assigned+=assignFromList(a, await listAccount(a)); }
      catch(e){ a.status={ok:false,msg:e.message,at:Date.now()}; badAcc.add(a.id); accMsgs.push(`${a.label}: ${e.message}`); if(/네트워크/.test(e.message)) throw e; }
    }
    // 2) 캐릭터별: 자기 계정 키로 이미지(하루 1회) + 스케줄러
    for(const c of S.characters){
      const a=accOf(c);
      if(!a){ if(c.ocid){ errs++; c.sync=Object.assign(c.sync||{},{at:Date.now(),ok:false,msg:'넥슨 계정 미지정 — 등록된 어느 계정의 캐릭터 목록에도 없습니다. ✎ 편집에서 계정을 선택하거나 해당 계정의 API 키를 추가하세요.'}); } continue; }
      if(!a.key||badAcc.has(a.id)){ errs++; c.sync=Object.assign(c.sync||{},{at:Date.now(),ok:false,msg:`'${a.label}' 계정 API 키 오류: ${a.status?.msg||'키 없음'}`}); continue; }
      if(!c.ocid){ try{ c.ocid=(await nx('/maplestory/v1/id',{character_name:c.name},a.key)).ocid; }catch(e){ c.sync={...c.sync,ok:false,msg:'ocid 조회 실패: '+e.message}; errs++; continue; } }
      try{ await fetchBasic(c,a.key); }catch(e){} // 이미지·레벨·EXP 갱신 (동기화마다)
      try{ total+=applyScheduler(c, await fetchSched(c,a)); } // fetchSched: 같은 응답으로 일퀘/길드 요약도 저장
      catch(e){ errs++; const hint=/OPENAPI0000[234]/.test(e.code||'')?` — 스케줄러 조회 불가: '${a.label}' 계정의 캐릭터가 아니거나 2026-06-25 이후 접속 기록이 없을 수 있어요. 수동 체크는 계속 가능합니다.`:''; c.sync=Object.assign(c.sync||{},{at:Date.now(),ok:false,msg:e.message+hint}); }
    }
    S.settings.lastSync=Date.now(); save();
    if(!opts.silent || total || assigned || accMsgs.length) toast(`동기화 완료 — 새로 체크된 보스 ${total}개`+(assigned?` · 계정 자동 연결 ${assigned}명`:'')+(errs?` · 일부 캐릭터 실패 ${errs}`:'')+(accMsgs.length?` · 계정 오류: ${accMsgs.join(', ')}`:''));
  }catch(e){ if(!opts.silent) toast('동기화 실패: '+e.message); save(); }
  finally{ syncing=false; render(); }
}

/* =====================================================================
 *  일퀘 현황 · 길드 현황 — 스케줄러(/scheduler/character-state) 재사용
 *  스케줄러 응답 요약을 localStorage(SCHED_KEY)에 캐릭터별로 보관 → 동기화·탭 자동 갱신이 같은 캐시를 씀.
 *  실측(2026-10-09) 이름: daily_contents '[일일 퀘스트] 세르니움 조사' … '[일일 퀘스트] 기어드락 크로노스의 잔재 수집',
 *  '몬스터파크'(contents, now/max=…/14), weekly_contents '[몬스터파크] 익스트림 몬스터파커에 도전해보겠나?'(주간 퀘스트, now/max=…/5),
 *  '[길드] 지하 수로' · '[길드] 플래그 레이스' · '[길드] 주간 미션 포인트'(now_count = 이번 주 점수).
 *  quest_state: "2" 완료, "1" 진행 중, "0" 기타(미수락·미해금).
 * ===================================================================== */
const DQ_ITEMS = [ // lv: 일일 퀘스트 수행 가능 레벨 (그란디스 지역)
  {id:'cer',  label:'세르니움',   key:'세르니움',   lv:260, col:'#e0b04a'},
  {id:'arcs', label:'아르크스',   key:'아르크스',   lv:265, col:'#e2843a'},
  {id:'odium',label:'오디움',     key:'오디움',     lv:270, col:'#3fb3a3'},
  {id:'dow',  label:'도원경',     key:'도원경',     lv:275, col:'#e57ba8'},
  {id:'art',  label:'아르테리아', key:'아르테리아', lv:280, col:'#d9574a'},
  {id:'car',  label:'카르시온',   key:'카르시온',   lv:285, col:'#4a8fe0'},
  {id:'tal',  label:'탈라하트',   key:'탈라하트',   lv:290, col:'#9a6ae0'},
  {id:'gear', label:'기어드락',   key:'기어드락',   lv:295, col:'#8a97a8'},
  {id:'mp',   label:'몬스터파크', kind:'mp',  lv:0,   col:'#4caf50'},
  {id:'xmp',  label:'익스트림 몬파', kind:'xmp', lv:260, col:'#1f9e74', weekly:true},
];
const DQ_ICONS = /*__DQ_ICONS__*/{}; // 지역 아이콘 data URI (어센틱/그랜드 어센틱심볼, 몬스터파크 이용권, 익몬=몬스터파크 NPC 슈피겔만 얼굴) — src/dqicons.json
const dqIco = (it,cls='dqico') => DQ_ICONS[it.id]?`<img class="${cls}" src="${DQ_ICONS[it.id]}" alt="" width="20" height="20" decoding="async">`:'';
const DQ_TTL_MS = 10*60e3;      // 일퀘 탭: 캐릭터별 스케줄러 10분마다 (접속 중/접속 종료 시에만 넥슨이 갱신)
const GUILD_TTL_MS = 30*60e3;   // 길드 랭킹: 하루 1번(09:30경) 갱신 데이터라 30분 캐시
const MP_CHAR_DAILY = 7;        // 몬스터파크: 캐릭터당 하루 7회 (스케줄러 max_count 14 = 월드 기준)
const GUILD = {name:'봉사활동', world:'스카니아'}; // 고정값 (사용자 요청 시 변경)
const SCHED_KEY = 'mapleBossTracker.sched', GUILD_KEY = 'mapleBossTracker.guild';
const lsGet = k => { try{ return JSON.parse(localStorage.getItem(k)||'null'); }catch(e){ return null; } };
const lsSet = (k,v) => { try{ localStorage.setItem(k,JSON.stringify(v)); }catch(e){} };
let schedC = lsGet(SCHED_KEY) || {};   // charId → {date, level, items{id:{st,now,max,reg,name}}, guild{suro,flag,mission}, at, ok, msg}
let guildC = lsGet(GUILD_KEY);          // {date, t1, t2, at, ok, msg}
let dqBusy=false, guildBusy=false, dqEdit=false, apiPauseUntil=0;

function schedSummary(d){
  const daily=Array.isArray(d?.daily_contents)?d.daily_contents:[], weekly=Array.isArray(d?.weekly_contents)?d.weekly_contents:[];
  const nm=r=>normName(r?.content_name);
  const pick=r=>r?{st:String(r.quest_state??''),now:Number(r.now_count)||0,max:Number(r.max_count)||0,reg:flagOn(r.registration_flag),name:String(r.content_name||'')}:null;
  const items={};
  for(const it of DQ_ITEMS){
    let r=null;
    if(it.kind==='mp') r=daily.find(x=>nm(x)==='몬스터파크');
    else if(it.kind==='xmp') r=weekly.find(x=>nm(x).includes('익스트림몬스터파'))||daily.find(x=>nm(x).includes('익스트림몬스터파'));
    else r=daily.find(x=>nm(x).includes(normName(it.key)) && (x.type==='quest'||/일일/.test(x.content_name||'')));
    if(r) items[it.id]=pick(r);
  }
  const g=k=>{ const r=weekly.find(x=>nm(x).includes(k)); return r?{now:Number(r.now_count)||0,max:Number(r.max_count)||0}:null; };
  return {date:String(d?.date||'').slice(0,10)||dayId(), level:Number(d?.character_level)||0, items,
    guild:{suro:g('지하수로'), flag:g('플래그레이스'), mission:g('주간미션포인트')}, at:Date.now(), ok:true, msg:''};
}
function schedPut(c,d){ schedC[c.id]=schedSummary(d); lsSet(SCHED_KEY,schedC); }
function schedErr(c,e){ schedC[c.id]={...(schedC[c.id]||{}),errAt:Date.now(),ok:false,msg:e.message,code:e.code||''}; lsSet(SCHED_KEY,schedC); }
/* 스케줄러 1회 호출 = 보스 자동 체크(applyScheduler) + 일퀘/길드 요약 저장 (동기화와 같은 경로) */
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
      try{ n+=applyScheduler(c, await fetchSched(c,accOf(c))); }
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
  const ttl=guildC?.ok&&guildC.date===dayId()?3*GUILD_TTL_MS:GUILD_TTL_MS;
  if(!force && guildC && Date.now()-(guildC.at||0)<ttl) return;
  guildBusy=true; renderTabView();
  const k=kst(), ready=k.getUTCHours()*60+k.getUTCMinutes()>=9*60+30;
  const days=(ready?[dayId()]:[]).concat(dayId(Date.now()-864e5));
  let got=null, lastErr=null;
  try{
    for(const d of days){
      const rows={};
      try{
        for(const t of [2,1]){
          const r=await nx('/maplestory/v1/ranking/guild',{date:d,world_name:GUILD.world,ranking_type:t,guild_name:GUILD.name},key);
          rows[t]=(Array.isArray(r?.ranking)?r.ranking:[]).find(x=>x&&x.guild_name===GUILD.name&&(!x.world_name||x.world_name===GUILD.world))||null;
        }
      }catch(e){ lastErr=e; if(e.code==='OPENAPI00007'||e.status===429||e.code==='NETWORK') break; continue; }
      if(rows[1]||rows[2]){ got={date:d,t1:rows[1],t2:rows[2]}; break; }
    }
    if(got) guildC={...got,at:Date.now(),ok:true,msg:''};
    else guildC={...(guildC||{}),at:Date.now(),ok:false,msg:lastErr?lastErr.message:`'${GUILD.world}' 월드 랭킹에서 '${GUILD.name}' 길드를 찾지 못했습니다`};
    lsSet(GUILD_KEY,guildC);
  } finally { guildBusy=false; renderTabView(); }
}
/* 60초 타이머·탭 열기·화면 복귀 시 호출: 열려 있는 탭만 갱신 */
function tabTick(){
  if(document.hidden) return;
  if(tab==='daily') refreshSched(dqChars().filter(c=>!S.dq.hide[c.id]));
  else if(tab==='guild'){ refreshGuild(); refreshSched(S.characters.filter(c=>c.isMain)); }
}
function renderTabView(){ if(tab==='daily') renderDaily(); else if(tab==='guild') renderGuild(); }
const hhmm = t => { const d=kst(t); return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`; };
const dqChars = () => orderedChars().filter(schedOk);
/* 항목 상태: lock(레벨 미달) · none(스케줄러에 없음) · done · prog · idle */
function dqState(it, x, lv){
  if(it.lv && lv && lv<it.lv) return 'lock';
  if(!x) return 'none';
  if(it.kind==='mp') return x.now>=Math.min(MP_CHAR_DAILY, x.max||MP_CHAR_DAILY)?'done':x.now>0?'prog':'idle';
  if(x.st==='2' || (it.kind==='xmp' && x.max>0 && x.now>=x.max)) return 'done';
  if(x.st==='1') return 'prog';
  return 'idle';
}
const DQ_TXT = {done:'완료', prog:'진행 중', idle:'미수락', none:'정보 없음'};
function dqCell(c, it, x, st, off){
  // 몬스터파크: 캐릭터당 하루 7회 기준(n/7회) · 익스트림 몬파: 주간 퀘스트(주간 n/5) · 진행 중 퀘스트에 카운트가 있으면 '진행 n/m'
  let txt=DQ_TXT[st], cnt='';
  if(x && it.kind==='mp'){ txt=st==='done'?'완료':''; cnt=`${Math.min(x.now,MP_CHAR_DAILY)}/${MP_CHAR_DAILY}회`; }
  else if(x && it.kind==='xmp'){ txt=st==='done'?'완료':'주간'; cnt=x.max>0?`${x.now}/${x.max}`:''; }
  else if(x && st==='prog' && x.max>0){ txt='진행'; cnt=`${x.now}/${x.max}`; }
  const tip = (x?.name||it.label)+(it.weekly?' (주간)':'')+(it.kind==='mp'?` · 오늘 ${x?.now??0}회 (캐릭터당 하루 ${MP_CHAR_DAILY}회, 스케줄러 최대 ${x?.max??'-'})`:'')+(dqEdit?'\n클릭: 이 캐릭터에서 '+(off?'다시 표시':'숨기기'):'');
  return `<div class="dqi s-${st}${off?' off':''}" style="--c:${it.col}" data-dqi="${it.id}" ${dqEdit?`data-dqc="${c.id}|${it.id}" role="button" tabindex="0"`:''} title="${esc(tip)}">
    <b class="dqn">${dqIco(it)}<span>${esc(it.label)}</span></b><span class="dqs">${esc(txt)}${cnt?`${txt?' ':''}<em>${cnt}</em>`:''}</span>
    ${st==='done'?`<div class="dqov" aria-hidden="true"><span class="dqov-n">${dqIco(it,'dqico ov')}${esc(it.label)}</span><span class="dqov-t"><b>✓</b> 완료</span></div>`:''}</div>`;
}
function renderDaily(){
  const v=$('#view'); const D=S.dq, all=dqChars(), today=dayId();
  const noKey=S.characters.filter(c=>!schedOk(c)).length;
  const shown=all.filter(c=>dqEdit||!D.hide[c.id]), hidden=all.length-all.filter(c=>!D.hide[c.id]).length;
  const items=DQ_ITEMS.filter(it=>!D.off[it.id]);
  const newest=Math.max(0,...all.map(c=>schedC[c.id]?.at||0));
  const status=dqBusy?'<span class="dqspin" aria-hidden="true"></span>갱신 중…':newest?`갱신 ${hhmm(newest)} · 10분마다 자동`:'';
  const chips=dqEdit?`<div class="dqedit"><span class="muted tiny">표시 항목 (전체 캐릭터)</span><div class="dqchips">${DQ_ITEMS.map(it=>`<button class="dqchip${D.off[it.id]?'':' on'}" data-dqg="${it.id}" style="--c:${it.col}" aria-pressed="${!D.off[it.id]}">${esc(it.label)}</button>`).join('')}</div>
    <div class="muted tiny">카드의 항목을 누르면 그 캐릭터에서만 숨기거나 다시 표시 · 카드의 👁 로 캐릭터 숨기기</div></div>`:'';
  const card=c=>{
    const x=schedC[c.id], ok=x&&x.ok!==false&&x.date===today, lv=Number(ok&&x.level||c.level)||0, co=D.charOff[c.id]||{};
    const hid=!!D.hide[c.id];
    let body='', done=0, tot=0;
    if(!x||(!ok&&x.ok!==false)) body=`<div class="dqmsg muted">${dqBusy||!x?'불러오는 중…':'오늘 데이터를 기다리는 중…'}</div>`;
    else if(x.ok===false&&x.date!==today) body=`<div class="dqmsg warnc">⚠ 스케줄러 조회 실패 — ${esc(x.msg||'')}</div>`;
    else{
      const locked=[], cells=[];
      for(const it of items){
        const st=dqState(it,x.items?.[it.id],lv), off=!!co[it.id];
        if(st==='lock'){ locked.push(it); continue; }
        if(off&&!dqEdit) continue;
        if(!off&&st!=='none'){ tot++; if(st==='done') done++; }
        cells.push(dqCell(c,it,x.items?.[it.id],st,off));
      }
      body=(cells.length?`<div class="dqcells">${cells.join('')}</div>`:`<div class="dqmsg muted">표시할 항목이 없어요${dqEdit?'':' · 편집에서 항목을 켜세요'}</div>`)
        +(locked.length?`<div class="dqlock muted" title="캐릭터 레벨이 낮아 아직 할 수 없는 항목">🔒 ${locked.map(it=>`${esc(it.label)} Lv.${it.lv}`).join(' · ')}</div>`:'')
        +(x.ok===false?`<div class="dqlock warnc">⚠ 최근 갱신 실패 (${hhmm(x.errAt)}) — ${esc(x.msg||'')}</div>`:'');
    }
    return `<div class="card dqc${hid?' hid':''}${tot&&done===tot?' alldone':''}" data-dqchar="${c.id}">
      <div class="dqh">${avatar(c)}<div class="grow"><div class="nm">${esc(c.name)}${c.isMain?'<span class="mainbadge">★</span>':''}</div><div class="meta">Lv.${esc(lv||'?')} · ${esc(c.job||'')}</div></div>
      ${tot?`<span class="dqcnt${done===tot?' full':''}">${done}/${tot}</span>`:''}${dqEdit?`<button class="btn sm plain dqeye" data-dqhide="${c.id}" title="${hid?'이 캐릭터 다시 표시':'이 캐릭터 숨기기'}" aria-label="${hid?'다시 표시':'숨기기'}">${hid?'숨김':'👁'}</button>`:''}</div>
      ${body}</div>`;
  };
  v.innerHTML=`<div class="card dqtop"><h2>📋 일퀘 현황 <span class="muted" style="font-weight:500">${esc(today)}</span><span class="hspace"></span><span class="muted tiny dqstat">${status}</span>
      <button class="btn sm ${dqEdit?'':'plain'}" id="dqEditBtn" aria-pressed="${dqEdit}">${dqEdit?'완료':'편집'}</button></h2>${chips}
    ${!hasApi()?'<div class="note">넥슨 API 키를 등록하면 메이플 스케줄러에서 일퀘 진행 상황을 실시간으로 불러옵니다. 사이드바 <b>+ 추가</b>에서 계정별 API 키를 등록하세요.</div>':''}</div>
    ${shown.length?`<div class="dqgrid">${shown.map(card).join('')}</div>`:(hasApi()?'<div class="card muted">표시할 캐릭터가 없습니다.</div>':'')}
    ${hidden&&!dqEdit||noKey?`<div class="muted tiny dqfoot">${hidden&&!dqEdit?`숨긴 캐릭터 ${hidden}명 (편집에서 다시 표시)`:''}${hidden&&!dqEdit&&noKey?' · ':''}${noKey?`API 키가 연결되지 않은 캐릭터 ${noKey}명은 표시하지 않아요`:''}</div>`:''}`;
}
const num = n => (Number(n)||0).toLocaleString('ko-KR');
function renderGuild(){
  const v=$('#view'), g=guildC, mains=S.characters.filter(c=>c.isMain);
  const tile=(lbl,ico,r)=>`<div class="gtile"><div class="gk">${ico} ${lbl}</div>${r?`<div class="gv">${num(r.guild_point)}<small>점</small></div><div class="grk"><b>${num(r.ranking)}</b>위</div>`:`<div class="gv dim">기록 없음</div><div class="grk muted">랭킹 미등록</div>`}</div>`;
  const info=g?.t2||g?.t1;
  const head=!hasApi()?'<div class="note">넥슨 API 키를 등록하면 길드 랭킹을 불러옵니다. 사이드바 <b>+ 추가</b>에서 API 키를 등록하세요.</div>'
    : !g ? `<div class="muted">${guildBusy?'불러오는 중…':'잠시 후 불러옵니다…'}</div>`
    : `${info?`<div class="gmeta"><span class="glv">Lv.${esc(info.guild_level)}</span><span>마스터 <b>${esc(info.guild_master_name||'-')}</b></span></div>
       <div class="gtiles">${tile('지하 수로','🌊',g.t2)}${tile('플래그 레이스','🚩',g.t1)}</div>`:''}
       ${g.ok===false?`<div class="dqlock warnc">⚠ 길드 랭킹 조회 실패 — ${esc(g.msg||'')}</div>`:''}`;
  const sub=g?.date?`<span class="muted tiny">기준 ${esc(g.date)}${g.date!==dayId()?' (어제 · 오늘 랭킹 준비 전)':''}${guildBusy?' · 갱신 중…':g.at?` · 확인 ${hhmm(g.at)}`:''}</span>`:'';
  const row=c=>{ const x=schedC[c.id], gg=x?.guild||{}, has=x&&x.ok!==false;
    const cell=(o,lbl)=>`<div class="gsc"><span class="muted tiny">${lbl}</span><b>${o?num(o.now)+(o.max>0?`<small>/${num(o.max)}</small>`:''):'-'}</b></div>`;
    return `<div class="grow-r">${avatar(c)}<div class="grow"><div class="nm">${esc(c.name)} <span class="mainbadge">★ 본캐</span></div><div class="meta">Lv.${esc(c.level||'?')} · ${esc(c.job||'')}</div></div>
      ${!schedOk(c)?'<span class="muted tiny">API 키 미연결</span>':!x?`<span class="muted tiny">${dqBusy?'불러오는 중…':'대기 중…'}</span>`:!has?`<span class="warnc tiny" title="${esc(x.msg||'')}">⚠ 조회 실패</span>`
       :`<div class="gsc main"><span class="muted tiny">지하 수로</span><b>${gg.suro?num(gg.suro.now):'-'}</b></div>${cell(gg.flag,'플래그')}${cell(gg.mission,'주간 미션')}`}</div>`; };
  v.innerHTML=`<div class="grid"><div class="card gcard"><h2>🛡️ ${esc(GUILD.name)} <span class="muted" style="font-weight:500">${esc(GUILD.world)}</span><span class="hspace"></span>${sub}</h2>${head}</div>
    <div class="card"><h2>⭐ 본캐 지하 수로 <span class="muted" style="font-weight:500">이번 주</span></h2>
      ${mains.length?mains.map(row).join(''):'<div class="muted">★ 본캐로 지정된 캐릭터가 없습니다. 사이드바 ✎에서 본캐로 지정하세요.</div>'}
      <div class="muted tiny" style="margin-top:8px">캐릭터 점수는 메이플 스케줄러의 '[길드] 지하 수로' 점수(이번 주 누적, 목요일 초기화)입니다. 길드 순위·점수는 넥슨 길드 랭킹(하루 1번, 09:30경 갱신) 기준입니다.</div></div></div>`;
}

/* =====================================================================
 *  유틸 / UI
 * ===================================================================== */
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
function meso(n){
  n=Math.round(n||0); if(n===0) return '0';
  const eok=Math.floor(n/1e8), man=Math.floor(n%1e8/1e4), rest=n%1e4;
  let s=''; if(eok) s+=eok.toLocaleString()+'억 '; if(man) s+=man.toLocaleString()+'만'; if(!eok&&!man) s=rest.toLocaleString();
  return s.trim();
}
function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');clearTimeout(toast._t);toast._t=setTimeout(()=>t.classList.remove('show'),3200);}
const safeImg = u => /^https:\/\/open\.api\.nexon\.com\//.test(u||'') ? u : '';
const avatar = (c,cls='') => `<div class="avatar ${cls}">${safeImg(c.image)?`<img src="${esc(c.image)}" alt="" loading="lazy" onerror="this.remove()">`:esc((c.name||'?').slice(0,1))}</div>`;
let tab='boss', bossFilter='weekly', editMode=false;

function applyTheme(){
  const dark = S.theme ? S.theme==='dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.dataset.theme = dark?'dark':'light';
  $('#themeBtn').textContent = dark?'☀️ 라이트':'🌙 다크';
}
function render(){ if(!['boss','summary','history','total','daily','guild'].includes(tab)) tab='boss';
  renderChars(); renderHeaderSync(); if($('#importModal').classList.contains('show')) renderAccList();
  ({boss:renderBoss,summary:renderSummary,history:renderHistory,total:renderTotal,daily:renderDaily,guild:renderGuild})[tab](); renderResetInfo(); }
/* 캐릭터 카드 제목 옆: 🔄 지금 동기화 아이콘 버튼 (API 키가 있을 때만, 넥슨 API 전용 — 구글 드라이브는 헤더 ☁ 버튼) */
function renderHeaderSync(){
  const b=$('#syncBtn'); if(!b) return; const st=S.settings; b.hidden=!hasApi(); b.disabled=syncing;
  b.classList.toggle('busy',syncing); b.setAttribute('aria-busy',String(syncing));
  if(!b.querySelector('svg')) b.innerHTML=`<svg class="rot" viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.34-5.66" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M20 4v5h-5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`; // 아이콘만 (2026-10-10: 헤더 → 캐릭터 카드 제목 옆)
  b.title=syncing?'동기화 중…':`지금 동기화 (보스 클리어 자동 체크)\n마지막 동기화: ${st.lastSync?hm(st.lastSync)+' KST':'없음'}\n페이지를 열거나 새로고침할 때 자동 (${LOAD_SYNC_GAP_MS/1e3}초 안에 다시 열면 건너뜀)`;
  b.setAttribute('aria-label',syncing?'동기화 중':`지금 동기화 — 마지막 ${st.lastSync?hm(st.lastSync):'없음'}`);
}

/* ---------- 사용자 지정 순서 ----------
 * S.characters 배열 순서 = 월드 그룹 안에서의 표시 순서, S.worldOrder = 월드 그룹 순서.
 * 동기화·가져오기·본캐 지정은 이 순서를 바꾸지 않습니다(새 캐릭터는 맨 뒤에 추가). */
function worldGroups(){
  const groups=new Map();
  for(const w of S.worldOrder) groups.set(w,[]);
  for(const c of S.characters){ const w=worldOf(c); if(!groups.has(w)) groups.set(w,[]); groups.get(w).push(c); }
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
  const same=S.characters.filter(x=>worldOf(x)===worldOf(c)); const i=same.indexOf(c), j=i+dir;
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
let charSort=(()=>{ try{ return localStorage.getItem(CHAR_SORT_KEY)==='undone'?'undone':'base'; }catch(e){ return 'base'; } })();
const sortedChars = cs => charSort!=='undone' ? cs : [...cs.filter(c=>weeklyCount(c)<S.settings.weeklyLimit), ...cs.filter(c=>weeklyCount(c)>=S.settings.weeklyLimit)];
function setCharSort(v){ charSort=v==='undone'?'undone':'base'; try{ localStorage.setItem(CHAR_SORT_KEY,charSort); }catch(e){} render(); }
/* 캐릭터 목록: 8명까지 보이고 넘으면 목록 안에서 스크롤 (페이지는 안 늘어남).
 * 데스크톱에서 화면이 낮아 8줄 + 소식 카드 최소 높이가 안 들어가면 들어가는 만큼만(최소 4줄) 보여 줌 → 사이드바 때문에 페이지가 길어지지 않음. */
const CHAR_ROWS=8, CHAR_ROWS_MIN=4, SIDE_FEED_MIN=31*2+70+12; // 소식 카드 최소 높이(feedFit 의 minH) + 카드 간격
function fitCharList(){
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
function renderChars(){
  if(dnd) return; // 드래그 중에는 다시 그리지 않음
  const el=$('#charList'), tabsEl=$('#worldTabs');
  const fixed=charSort==='undone'; // 미완료순 보기에서는 순서 바꾸기(드래그·▲▼) 잠금 — 기본순에서만
  el.classList.toggle('sorted',fixed);
  if(!S.characters.length){ if(tabsEl) tabsEl.innerHTML=''; el.innerHTML='<div class="muted" style="padding:8px 2px">아직 캐릭터가 없습니다.<br><b>+ 추가</b> 또는 아래 <b>넥슨 API</b>로 불러오세요.</div>'; fitCharList(); return; }
  const groups=worldGroups(); const worlds=[...groups.keys()];
  // 다른 곳(수익 요약 등)에서 다른 월드 캐릭터를 고르면 그 월드 탭으로
  const act=activeChar();
  if(seenActive===null) seenActive=S.activeId;
  else if(S.activeId!==seenActive){ seenActive=S.activeId; if(act&&worldOf(act)!==worldTab){ worldTab=worldOf(act); try{ localStorage.setItem(WORLD_TAB_KEY,worldTab); }catch(e){} } }
  if(!groups.has(worldTab)) worldTab=(act&&groups.has(worldOf(act)))?worldOf(act):worlds[0];
  const multi=worlds.length>1;
  const sortCtl=`<span class="charsort" role="group" aria-label="캐릭터 정렬 (보기만 바뀌고 저장된 순서는 그대로)">${[['base','기본순','내가 정한 순서'],['undone','보스 미완료순','이번 주 주간 보스 12개를 아직 다 안 잡은 캐릭터 먼저 (각 무리 안은 기본순)']].map(([k,l,t])=>`<button type="button" class="sortlink${charSort===k?' on':''}" data-csort="${k}" aria-pressed="${charSort===k}" title="${t}">${l}</button>`).join('')}</span>`;
  if(tabsEl) tabsEl.innerHTML=`<span class="wtablist" role="tablist" aria-label="월드">${worlds.map((w,i)=>(i?'<span class="wdiv" aria-hidden="true">ㅣ</span>':'')+
      `<span role="tab" tabindex="0" class="wtab${w===worldTab?' on':''}" aria-selected="${w===worldTab}" data-wtab="${esc(w)}" data-world="${esc(w)}" draggable="${multi}" title="${esc(w)} 캐릭터 ${groups.get(w).length}명${multi?' · 끌어서 월드 순서 변경':''}">${worldIcon(w)}<span class="wnm">${esc(w)}</span> <span class="cnt">(${groups.get(w).length})</span></span>`).join('')}</span>${sortCtl}`;
  const list=sortedChars(groups.get(worldTab)||[]), w=worldTab;
  el.innerHTML=list.map((c,ci)=>{const r=charRevenue(c);return `
    <div class="char ${c.id===S.activeId?'on':''}${r.weekly>=S.settings.weeklyLimit?' alldone':''}" data-id="${c.id}" data-world="${esc(w)}" draggable="${fixed?'false':'true'}">
      ${doneOverlay(c,r)}
      <span class="drag-h" title="드래그해서 순서 변경">⠿</span>
      ${avatar(c)}
      <div class="grow"><div class="nm">${esc(c.name)}${c.isMain?'<span class="mainbadge">★ 본캐</span>':''}</div><div class="meta lvrow"><span class="lv">Lv.${esc(c.level||'?')}</span><span class="job">${esc(c.job||'직업 미설정')}</span></div>${expLine(c)}</div>
      <div style="text-align:right"><div class="rev">${meso(r.meso)}</div><div class="meta">${r.weekly}/${S.settings.weeklyLimit}${needAssign(c)?' <span class="warnc" title="넥슨 계정 미지정 — ✎ 편집에서 계정을 선택하세요">⚠</span>':c.sync?.ok===false?' <span title="'+esc(c.sync.msg)+'">⚠</span>':''}</div></div>
      <div class="ordcol"><button class="ord" data-move="${c.id}|-1" ${ci===0||fixed?'disabled':''} title="위로" aria-label="위로">▲</button><button class="ord" data-move="${c.id}|1" ${ci===list.length-1||fixed?'disabled':''} title="아래로" aria-label="아래로">▼</button></div>
      <button class="btn sm plain" data-edit="${c.id}" title="수정">✎</button>
    </div>`}).join('');
  fitCharList();
}

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
  if(charSort==='undone') return; // 미완료순 보기에서는 캐릭터 순서 잠금
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
function emptyView(){ return `<div class="card empty"><div class="big">🍁</div><h2 style="justify-content:center">캐릭터를 추가해 보세요</h2><p class="muted">직접 추가하거나, 넥슨 Open API 키로 내 계정의 본캐·부캐를 한 번에 불러올 수 있어요.</p>
  <div class="toolbar" style="justify-content:center"><button class="btn" id="importAccBtn">+ 캐릭터 추가 (API 키로 불러오기)</button><button class="btn ghost" onclick="openCharModal()">이름으로 직접 추가</button></div></div>`; }

function renderBoss(){
  const v=$('#view'); const c=activeChar();
  if(!c){ v.innerHTML=emptyView(); return; }
  const r=charRevenue(c); const a=allRevenue();
  const lim=S.settings.weeklyLimit;
  const bosses=BOSSES.filter(b=>b.type===bossFilter);
  const shown=editMode?bosses:bosses.filter(b=>c.bosses[b.id]?.enabled);
  const cntType=t=>BOSSES.filter(b=>b.type===t&&c.bosses[b.id]?.enabled).length;
  const doneType=t=>BOSSES.filter(b=>b.type===t&&c.bosses[b.id]?.enabled&&isDone(c,b)).length;
  const sy=c.sync||{};
  const acc=accOf(c);
  const syncLine = needAssign(c) ? `<span class="pill err">계정 미지정</span> <span class="muted">이 캐릭터의 넥슨 계정을 선택해야 자동 체크가 됩니다.</span> <button class="btn sm ghost" data-edit="${c.id}">계정 선택</button>`
    : c.ocid ? (sy.ok===false ? `<span class="pill err">API 실패</span> <span class="muted">${esc(sy.msg)}</span>`
      : sy.at ? `<span class="pill api">API</span> <span class="muted">게임 내 주간 보스 처치 <b>${sy.clear??'?'} / ${sy.limit||lim}</b> · ${hm(sy.at)} KST 동기화${(um=>um.length?` · 매칭 안 된 보스: ${esc(um.join(', '))}`:'')((sy.unmatched||[]).filter(x=>!isSeasonBoss(x)))}</span>` : '<span class="muted">API 연결 캐릭터 — 아직 동기화 전</span>')
    : '<span class="muted">수동 캐릭터 (API 미연결)</span>';
  v.innerHTML=`<div class="bosslay"><div class="grid">
   <div class="card">
    <div style="display:flex;gap:12px;align-items:center;margin-bottom:10px">${avatar(c,'lg')}
      <div style="flex:1;min-width:0"><h2 style="margin:0">${esc(c.name)}${c.isMain?'<span class="mainbadge">★ 본캐</span>':''}</h2>
      <div class="muted">Lv.${esc(c.level||'?')} · ${esc(c.job||'')} · ${esc(worldOf(c))}${(()=>{ if(r.weekly>0) return ''; const ex=expectedWeekly(c); if(!ex.list.length) return ''; // 이번 주 처치 0회일 때만
        return ` <span class="expinc" title="${esc(`예상 주간 수익 — 켜 둔 주간 보스 ${ex.all}개 중 1인당 결정석 가격 상위 ${ex.list.length}개를 모두 잡을 때\n`+ex.list.map(x=>`· ${bossTag(x)} ${meso(x.value)}`).join('\n'))}">${miniIcon('ipc')}예상 <b>${meso(ex.meso)}</b><small>(상위 ${ex.list.length}개)</small></span>`; })()}</div><div style="margin-top:4px;font-size:.85rem">${syncLine}</div></div></div>
    <div class="stats s4">
      <div class="stat"><div class="k">이번 주 주간 보스 수익 (이 캐릭터)</div><div class="v acc">${meso(r.meso)}</div></div>
      <div class="stat"><div class="k">주간 보스 처치</div><div class="v">${r.weekly} / ${lim}</div><div class="bar ${r.weekly>lim?'over':''}"><i style="width:${Math.min(100,r.weekly/lim*100)}%"></i></div></div>
      <div class="stat"><div class="k">이번 달 월간 보스</div><div class="v">${monthlyCount(c)} / ${S.settings.monthlyLimit}${r.monthMeso?` <span class="mmeso">${meso(r.monthMeso)}</span>`:''}</div><div class="bar"><i style="width:${Math.min(100,monthlyCount(c)/S.settings.monthlyLimit*100)}%"></i></div></div>
      <div class="stat"><div class="k">전체 캐릭터 주간 합계</div><div class="v acc">${meso(a.total)}</div></div>
    </div>
   </div>
   <div class="card">
    <div class="toolbar" style="margin-bottom:10px">
      <div class="seg">${['weekly','monthly'].map(t=>`<button data-filter="${t}" class="${bossFilter===t?'on':''}">${TYPE_LABEL[t]} <span style="opacity:.8">${doneType(t)}/${cntType(t)}</span></button>`).join('')}</div>
      <span style="flex:1"></span>
      <button class="btn sm ${editMode?'':'ghost'}" id="editModeBtn">${editMode?'✓ 선택 완료':'⚙ 보스 선택/난이도'}</button>
    </div>
    ${editMode?`<div class="note" style="margin-bottom:10px">이 캐릭터가 도는 보스를 켜고 난이도를 고르세요. 보스는 한 주(월)에 한 난이도만 클리어할 수 있다고 가정합니다.</div>`:''}
    ${bossFilter==='monthly'?'<div class="muted" style="margin-bottom:8px">월간 보스(검은 마법사)는 매월 1일 00:00 초기화되며 월 1회만 처치 가능합니다. 주간 수익과 별도로 「이번 달 월간 보스」 수익으로 집계됩니다.</div>':''}
    <div class="boss-list">${shown.length?shown.map(b=>bossRow(c,b)).join(''):`<div class="empty muted">선택된 ${TYPE_LABEL[bossFilter]}가 없습니다.<br><button class="btn sm" style="margin-top:8px" onclick="editMode=true;render()">보스 선택하기</button></div>`}</div>
   </div></div><div class="rcol">${revPanel(a,c)}${priceCard()}<div class="card resetcard"><div class="muted" id="resetInfo"></div></div></div></div>`;
}
/* 보스 체크 탭 오른쪽 패널: 이번 주 수익 합계 · 캐릭터별 수익 (좁은 화면에서는 아래로 쌓임) */
function revPanel(a,cur){
  const lim=S.settings.weeklyLimit;
  const per=orderedChars().map(c=>a.per.find(p=>p.c===c)).filter(Boolean);
  const max=Math.max(1,...per.map(p=>p.r.meso));
  return `<aside class="revpanel card" aria-label="이번 주 수익 요약">
    <h2>💰 이번 주 수익</h2>
    <div class="muted" style="font-size:.75rem;margin-top:-6px">${fmtWeek(S.period.week)} · 전체 캐릭터</div>
    <div class="rp-total">${meso(a.total)}<small> 메소</small></div>
    <div class="muted" style="font-size:.75rem">${a.total.toLocaleString()} · 주간 보스 결정석 ${a.count}개</div>
    ${a.monthTotal||S.characters.some(c=>c.bosses.blackmage?.enabled)?`<div class="rp-month"><span>🌙 ${+S.period.month.slice(5)}월 월간 보스 <small class="muted">(별도)</small></span><b>${a.monthTotal?meso(a.monthTotal):'-'}</b></div>`:''}
    <div class="rp-sec">캐릭터별</div>
    <div class="rp-list">${per.map(p=>`<div class="rp-char ${p.c===cur?'on':''}" data-id="${p.c.id}" title="${esc(p.c.name)} 선택">
      <div class="rp-row"><span class="rp-nm">${esc(p.c.name)}${p.c.isMain?' <span class="mainbadge">★</span>':''}</span><b>${meso(p.r.meso)}</b></div>
      <div class="rp-row"><span class="mini"><i style="width:${(p.r.meso/max*100).toFixed(1)}%"></i></span><span class="muted" style="font-size:.72rem;white-space:nowrap">${p.r.weekly}/${lim}${monthlyCount(p.c)?' · 월간 ✓':''}</span></div>
      ${(d=>itemsInline(d.items)?`<div class="rp-items">${itemsInline(d.items,{outs:d.outcomes,byBoss:true})}</div>`:'')(charAllDrops(p.c))}</div>`).join('')}</div>
    ${(()=>{const n=S.characters.reduce((s,c)=>s+itemSum(c.drops),0); return `<div class="muted" style="font-size:.72rem;margin-top:6px">🎁 이번 주 획득 아이템 ${n}개 · 보스 행의 아이템을 누르면 +1</div>`;})()}
  </aside>`;
}
// 보스+난이도별 가격 행 (싼 순서) — 보스 체크 탭 가격 카드
const priceRows = g => BOSSES.filter(b=>b.type===g).flatMap(b=>b.diffs.map(d=>({b,d,k:priceKey(b,d),p:price(b,d)}))).sort((x,y)=>x.p-y.p);
const priceAutoText = () => officialInfo?`공식 패치 노트 기준 자동 갱신 (마지막 확인 ${officialInfo.checkedAt||'-'})${officialInfo.pending.length?` · ${officialInfo.pending.length}개는 ${officialInfo.pending[0].effective}부터 적용`:''}`:'공식 패치 노트 기준 (온라인 주소에서 자동 갱신)';
/* 보스 체크 탭 오른쪽: 결정석 가격 (읽기 전용, prices.json 자동 갱신) */
function priceCard(){
  const row=r=>`<div class="pc-row" title="${esc(r.b.name)} ${D[r.d]} — ${r.p.toLocaleString()} 메소">${bossIcon(r.b)}<span class="pc-nm">${esc(r.b.name)} <span class="muted">${D[r.d]}</span></span><b>${meso(r.p)}</b></div>`;
  return `<aside class="card pricecard" aria-label="결정석 가격">
    <div class="pc-head"><h2>${miniIcon('ipc')||'💎'} 결정석 가격</h2></div>
    <div class="pc-list">${priceRows('weekly').map(row).join('')}<div class="pc-sep">🌙 월간 보스</div>${priceRows('monthly').map(row).join('')}</div>
    <div class="pc-foot muted">${esc(priceAutoText())}</div>
  </aside>`;
}
function isDone(c,b){ return b.type==='weekly'?!!c.weekly[b.id]:!!c.monthly[b.id]; }
function bossRow(c,b){
  const slot=b.id; const cfg=c.bosses[slot]||{enabled:false,diff:b.diffs[0],party:1};
  const diff=cfg.diff||b.diffs[0]; const done=isDone(c,b); const pmax=partyMax(b,diff); const party=Math.min(pmax,cfg.party||1);
  const p=price(b,diff); const cr=charCrystals(c).find(x=>x.slot===slot);
  if(editMode){
    return `<div class="boss" style="${cfg.enabled?'':'opacity:.7'}">
      <label class="chk ${cfg.enabled?'on':''}" data-toggle="${slot}">${cfg.enabled?'✓':''}</label>
      <div class="grow"><div class="bn">${bossIcon(b)}${esc(b.name)}</div>
        <div class="diffs">${b.diffs.map(d=>`<span class="diff ${d===diff?'sel':''}" data-setdiff="${slot}|${d}">${D[d]} · ${meso(price(b,d))}</span>`).join('')}</div></div>
    </div>`;
  }
  return `<div class="boss ${done?'done':''}">
    <label class="chk ${done?'on':''}" data-check="${slot}" title="클리어 체크">${done?'✓':''}</label>
    <div class="grow"><div class="bn">${bossIcon(b)}${esc(b.name)} <span class="pill">${D[diff]}</span>
      ${c.auto[slot]&&done?'<span class="pill api" title="넥슨 스케줄러 API에서 자동 체크됨">API 자동</span>':''}
      ${cr&&!cr.counted?'<span class="pill err">한도 초과</span>':''}</div>
      ${b.diffs.length>1?`<div class="diffs">${b.diffs.map(d=>`<span class="diff ${d===diff?'sel':''} ${done&&d!==diff?'locked':''}" data-setdiff="${slot}|${d}">${D[d]}</span>`).join('')}</div>`:''}
      ${dropsHtml(b,diff,c)}
    </div>
    <div class="party">파티 <select data-party="${slot}" title="${pmax<CONFIG.MAX_PARTY?`${esc(b.name)} ${D[diff]}: 최대 ${pmax}인`:''}">${Array.from({length:pmax},(_,i)=>`<option ${party===i+1?'selected':''}>${i+1}</option>`).join('')}</select>인</div>
    <div class="price"><b>${meso(Math.floor(p/party))}</b>${party>1?`<br><span>(${meso(p)} ÷ ${party})</span>`:''}</div>
  </div>`;
}

function renderSummary(){
  const v=$('#view'); if(!S.characters.length){v.innerHTML=emptyView();return;}
  const a=allRevenue(); const kills=a.per.reduce((s,p)=>s+p.r.weekly,0);
  v.innerHTML=`<div class="grid"><div class="card">
    <h2>📊 이번 주 수익 요약 <span class="muted" style="font-weight:500">${fmtWeek(S.period.week)}</span></h2>
    <div class="stats s4">
      <div class="stat"><div class="k">주간 보스 예상 수익</div><div class="v acc">${meso(a.total)}</div><div class="muted">${a.total.toLocaleString()} 메소</div></div>
      <div class="stat"><div class="k">주간 보스 처치 (전체)</div><div class="v">${kills} / ${S.characters.length*S.settings.weeklyLimit}</div><div class="bar"><i style="width:${Math.min(100,kills/Math.max(1,S.characters.length*S.settings.weeklyLimit)*100)}%"></i></div></div>
      <div class="stat"><div class="k">주간 결정석 · 캐릭터</div><div class="v">${a.count}개 <span class="muted" style="font-size:.8rem;font-weight:500">· ${S.characters.length}명</span></div></div>
      <div class="stat"><div class="k">🌙 이번 달 월간 보스 <span class="muted">(${fmtMonth(S.period.month)}, 별도)</span></div><div class="v">${a.monthTotal?meso(a.monthTotal):'-'}</div><div class="muted">${a.monthCount?`${a.monthCount}회 클리어`:'아직 클리어 없음'}</div></div>
    </div>
  </div>
  <div class="card"><h2>캐릭터별</h2>
    <div style="overflow-x:auto"><table><thead><tr><th>캐릭터</th><th>월드 · 직업</th><th class="num">주간 보스</th><th class="num">주간 수익</th><th class="num">월간 보스</th></tr></thead><tbody>
    ${orderedChars().map(c=>a.per.find(p=>p.c===c)).map(p=>`<tr><td><b>${esc(p.c.name)}</b>${p.c.isMain?'<span class="mainbadge">★</span>':''} <span class="muted">Lv.${esc(p.c.level||'?')}</span></td><td>${esc(worldOf(p.c))} · ${esc(p.c.job||'-')}</td><td class="num">${p.r.weekly}/${S.settings.weeklyLimit}</td><td class="num"><b>${meso(p.r.meso)}</b></td><td class="num muted">${p.r.monthMeso?meso(p.r.monthMeso):'-'}</td></tr>`).join('')}
    <tr><td colspan="3"><b>합계</b></td><td class="num"><b style="color:var(--accent)">${meso(a.total)}</b></td><td class="num">${a.monthTotal?meso(a.monthTotal):'-'}</td></tr></tbody></table></div>
  </div>
  ${a.per.filter(p=>p.r.list.length).map(p=>`<div class="card"><details ${a.per.length<=3?'open':''}><summary>${esc(p.c.name)} — 결정석 상세 (${p.r.list.length})${(d=>itemsInline(d.items)?' · 획득 '+itemsInline(d.items,{outs:d.outcomes,byBoss:true}):'')(charAllDrops(p.c))}</summary>
    <table><thead><tr><th>보스</th><th>구분</th><th class="num">파티</th><th class="num">결정석 가격</th><th class="num">분배 후</th></tr></thead><tbody>
    ${p.r.list.map(x=>`<tr style="${x.counted?'':'opacity:.45;text-decoration:line-through'}"><td><span class="bname">${bossIcon(findBoss(x.slot))}${esc(x.name)} (${D[x.diff]})</span> ${x.auto?'<span class="pill api">API</span>':''}</td><td>${TYPE_LABEL[x.type]}</td><td class="num">${x.party}</td><td class="num">${meso(x.gross)}</td><td class="num">${meso(x.value)}</td></tr>`).join('')}
    </tbody></table></details></div>`).join('')}
  </div>`;
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
const perCharItems = list => (list||[]).filter(p=>itemSum(p.items)).map(p=>`<div class="hitems"><b>${esc(p.name)}</b> ${itemsInline(p.items,{outs:p.outcomes,byBoss:true})}</div>`).join('');
function renderHistory(){
  const v=$('#view'); const H=S.history.slice(-12);
  const cur=weekSummary(S.period.week);
  const rows=[...H.map(h=>({...h,cur:false})),{...cur,cur:true}];
  const all=[{...cur,cur:true},...S.history.slice().reverse()];
  v.innerHTML=`<div class="grid"><div class="card"><h2>📈 주간 수익 추이 <span class="muted" style="font-weight:500">최근 ${rows.length}주 · 주간 보스 결정석</span></h2>
    ${weekChart(rows)}
    ${H.length?'':'<p class="muted">아직 저장된 지난 주 기록이 없습니다. 매주 목요일 00:00(KST) 초기화 시 자동으로 기록됩니다.</p>'}
  </div>
  <div class="card"><h2>주간 기록 <span class="muted" style="font-weight:500">결정석 수익 · 획득 아이템</span></h2>
  <div style="overflow-x:auto"><table class="htable"><thead><tr><th>주차</th><th class="num">클리어</th><th class="num">결정석</th><th class="num">아이템</th><th class="num">결정석 수익</th><th></th></tr></thead><tbody>
    ${all.map(h=>`<tr><td>${fmtWeek(h.week)}${h.cur?' <span class="pill">이번 주</span>':''}<div class="muted">${(h.perChar||[]).filter(p=>p.meso).map(p=>`${esc(p.name)} ${meso(p.meso)}`).join(' · ')}</div>${perCharItems(h.perChar)}</td><td class="num">${h.cleared}</td><td class="num">${h.crystals??'-'}</td><td class="num">${h.items??itemSum(Object.assign({},...(h.perChar||[]).map(p=>p.items||{})))}</td><td class="num"><b>${meso(h.total)}</b></td><td class="num">${h.cur?'':`<button class="btn sm plain" data-delhist="${h.week}" title="기록 삭제">✕</button>`}</td></tr>`).join('')}
  </tbody></table></div>
  </div>
  <div class="card"><h2>🌙 월간 보스 기록 <span class="muted" style="font-weight:500">주간 수익과 별도</span></h2>
    <div style="overflow-x:auto"><table><thead><tr><th>월</th><th class="num">클리어</th><th class="num">수익</th></tr></thead><tbody>
    ${[{...monthSummary(S.period.month),cur:true},...S.monthHistory.slice().reverse()].map(m=>`<tr><td>${fmtMonth(m.month)}${m.cur?' <span class="pill">이번 달</span>':''}<div class="muted">${(m.perChar||[]).filter(p=>p.bosses?.length).map(p=>`${esc(p.name)} ${esc((p.bosses||[]).join(', '))} ${meso(p.meso)}`).join(' · ')||'-'}</div>${perCharItems(m.perChar)}</td><td class="num">${m.cleared||0}</td><td class="num"><b>${m.total?meso(m.total):'-'}</b></td></tr>`).join('')}
    </tbody></table></div></div></div>`;
}
/* 총 수익: 시작 주(S.startWeek)부터 저장된 모든 주간 기록 + 이번 주, 월간 보스는 별도 합계. 기록은 자동 삭제되지 않음 */
function totalData(){
  const weeks=[...S.history.slice().sort((a,b)=>a.week<b.week?-1:1).map(h=>({...h,cur:false})),{...weekSummary(S.period.week),cur:true}];
  const months=[...S.monthHistory.map(m=>({...m,cur:false})),{...monthSummary(S.period.month),cur:true}];
  const wTotal=weeks.reduce((s,w)=>s+(w.total||0),0), mTotal=months.reduce((s,m)=>s+(m.total||0),0);
  const chars={}, items={};
  const nameOf=p=>{ const c=p.id&&S.characters.find(x=>x.id===p.id); return c?c.name:p.name; };
  const keyOf=p=>p.id&&S.characters.some(x=>x.id===p.id)?p.id:'n:'+p.name;
  const ring={r4:0,c4:0,x:0,un:0};
  const add=(p,f)=>{ const k=keyOf(p); const o=chars[k]||(chars[k]={name:nameOf(p),week:0,month:0,items:{},outs:{},weeks:0}); f(o);
    for(const [ik,n] of Object.entries(p.items||{})){ const {it,party}=parseIK(ik); if(!ITEMS[it]) continue; const a=party>1?it+'#'+party:it; o.items[a]=(o.items[a]||0)+(+n);
      const I=items[a]||(items[a]={n:0,by:{},outs:[]}); I.n+=+n; I.by[o.name]=(I.by[o.name]||0)+(+n);
      if(isRing(it)){ const l=(p.outcomes||{})[ik]||[]; I.outs.push(...l); (o.outs[a]=o.outs[a]||[]).push(...l); const t=outTally(l,n); for(const q in ring) ring[q]+=t[q]; } } };
  weeks.forEach(w=>(w.perChar||[]).forEach(p=>add(p,o=>{o.week+=p.meso||0; if(p.meso) o.weeks++;})));
  months.forEach(m=>(m.perChar||[]).forEach(p=>add(p,o=>{o.month+=p.meso||0;})));
  return {weeks,months,wTotal,mTotal,grand:wTotal+mTotal,ring,chars:Object.values(chars).sort((a,b)=>(b.week+b.month)-(a.week+a.month)),items:Object.entries(items).sort((a,b)=>b[1].n-a[1].n)};
}
function renderTotal(){
  const v=$('#view'); const T=totalData();
  const nW=T.weeks.length, avg=Math.round(T.wTotal/Math.max(1,nW)), itemsN=T.items.reduce((s,[,I])=>s+I.n,0);
  let cum=0;
  v.innerHTML=`<div class="grid"><div class="card">
    <h2>🏆 총 수익 <span class="muted" style="font-weight:500">${fmtWeek(S.startWeek).split(' ~')[0]}부터 · ${nW}주</span></h2>
    <div class="stats s4">
      <div class="stat"><div class="k">총 수익 (주간 + 월간)</div><div class="v acc">${meso(T.grand)}</div><div class="muted">${T.grand.toLocaleString()} 메소</div></div>
      <div class="stat"><div class="k">주간 보스 누적</div><div class="v">${meso(T.wTotal)}</div><div class="muted">주 평균 ${meso(avg)}</div></div>
      <div class="stat"><div class="k">🌙 월간 보스 누적 (별도)</div><div class="v">${T.mTotal?meso(T.mTotal):'-'}</div><div class="muted">${T.months.filter(m=>m.total).length}개월</div></div>
      <div class="stat"><div class="k">🎁 획득 아이템 누적</div><div class="v">${itemsN}개</div><div class="muted">${T.items.length}종</div></div>
    </div>
    <p class="muted" style="margin:8px 0 0;font-size:.78rem">수익은 결정석 판매 금액만 합산합니다(드롭 아이템은 개수만 기록). 주간 기록은 자동으로 지워지지 않으며 구글 로그인 시 드라이브에 함께 저장됩니다.</p>
  </div>
  <div class="card"><h2>📈 주별 수익 · 누적 <span class="muted" style="font-weight:500">막대: 주간 결정석 수익 · 파란 선: 누적</span></h2>${weekChart(T.weeks,{cum:true,minBar:22})}</div>
  <div class="card"><h2>👤 캐릭터별 누적</h2><div style="overflow-x:auto"><table><thead><tr><th>캐릭터</th><th class="num">주간 보스</th><th class="num">월간 보스</th><th class="num">합계</th><th>획득 아이템</th></tr></thead><tbody>
    ${T.chars.map(o=>`<tr><td><b>${esc(o.name)}</b></td><td class="num">${meso(o.week)}</td><td class="num muted">${o.month?meso(o.month):'-'}</td><td class="num"><b>${meso(o.week+o.month)}</b></td><td>${itemsInline(o.items,{empty:'<span class="muted">-</span>',outs:o.outs})}</td></tr>`).join('')||'<tr><td colspan="5" class="muted">기록 없음</td></tr>'}
  </tbody></table></div></div>
  <div class="card"><h2>🎁 아이템별 누적 획득</h2>
    ${(()=>{const r=T.ring, rec=r.r4+r.c4+r.x; return rec+r.un?`<div class="ringsum">💍 반지 상자 결과: <span class="ro ro-r4">${outIcon('r4')}리4 <b>${r.r4}</b>개</span> · <span class="ro ro-c4">${outIcon('c4')}컨4 <b>${r.c4}</b>개</span> · <span class="ro ro-x">꽝 <b>${r.x}</b>회</span>${r.un?` · <span class="ro ro-un">미기록 ${r.un}회</span>`:''} · 대박 확률 <b>${rec?((r.r4+r.c4)/rec*100).toFixed(1)+'%':'-'}</b> <span class="muted">(결과를 기록한 ${rec}회 기준)</span></div>`:'';})()}
    ${T.items.length?`<div style="overflow-x:auto"><table><thead><tr><th>아이템</th><th class="num">개수</th><th>캐릭터별</th></tr></thead><tbody>
    ${T.items.map(([a,I])=>{ const {it:k,party}=parseIK(a); return `<tr><td><span class="dls">${dropLine(k,party,I.n,I.outs)}</span></td><td class="num"><b>${I.n}</b></td><td class="muted">${Object.entries(I.by).map(([n,c])=>`${esc(n)} ×${c}`).join(' · ')}</td></tr>`; }).join('')}
  </tbody></table></div>`:'<p class="muted">아직 획득한 아이템이 없습니다. 보스 체크 탭에서 보스 행의 아이템 칩을 누르면 개수가 기록됩니다.</p>'}</div>
  <div class="card"><h2>🗓 전체 주 목록</h2><div style="overflow-x:auto"><table><thead><tr><th>주차</th><th class="num">클리어</th><th class="num">아이템</th><th class="num">주간 수익</th><th class="num">누적</th></tr></thead><tbody>
    ${T.weeks.map(w=>{cum+=w.total||0;return {w,cum};}).reverse().map(({w,cum})=>`<tr><td>${fmtWeek(w.week)}${w.cur?' <span class="pill">이번 주</span>':''}</td><td class="num">${w.cleared??'-'}</td><td class="num">${w.items??itemSum(Object.assign({},...(w.perChar||[]).map(p=>p.items||{})))}</td><td class="num"><b>${meso(w.total||0)}</b></td><td class="num muted">${meso(cum)}</td></tr>`).join('')}
  </tbody></table></div></div></div>`;
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
  const name=$('#fName').value.trim(); if(!name){toast('이름을 입력하세요');return;}
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
  const name=$('#fName').value.trim(); if(!name){toast('이름을 입력하세요');return;}
  const job=$('#fJob').value.trim(), world=$('#fWorld').value.trim(); const level=Math.max(1,Math.min(300,parseInt($('#fLevel').value)||0))||'';
  const isMain=$('#fMain').checked, accId=$('#fAcc').value||'';
  let c;
  if(editingId){ c=S.characters.find(x=>x.id===editingId); if(c.name!==name && !lookup){ c.ocid=''; c.image=''; delete c.exp; } Object.assign(c,{name,job,level,world}); toast('수정되었습니다'); }
  else{
    c={id:uid(),name,job,level,world,bosses:{},weekly:{},monthly:{},auto:{},sync:{}};
    S.characters.push(c); S.activeId=c.id; tab='boss'; editMode=true; bossFilter='weekly';
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
const maskKey = k => !k ? '키 없음' : k.length<=10 ? '••••' : k.slice(0,5)+'••••'+k.slice(-4);
function renderAccList(){
  const el=$('#accList'); if(!el) return;
  el.innerHTML=accounts().length?accounts().map(a=>{
    const linked=S.characters.filter(c=>c.accId===a.id).length;
    const stt=!a.key?'<span class="warnc">키 없음</span>':a.status?.ok===false?`<span class="warnc" title="${esc(a.status.msg)}">⚠ 오류</span>`:a.status?.ok?(a.status.count?`<span class="okc">✓ ${a.status.count}명</span>`:'<span class="warnc" title="연결은 됐지만 캐릭터 0명 — [캐릭터 목록]에서 원인 확인">⚠ 0명</span>'):'<span class="muted">미확인</span>';
    return `<div class="accrow ${a.id===impAccId?'on':''}"><input class="pin acclbl" data-acclabel="${a.id}" value="${esc(a.label)}" maxlength="12" aria-label="계정 이름">
      <code class="kmask" title="API 키 (가림)">${esc(maskKey(a.key))}</code><span class="accst">${stt} <span class="muted">· 등록 ${linked}명</span></span>
      <span class="accbtns"><button class="btn sm ${a.id===impAccId?'':'ghost'}" data-acctest="${a.id}" ${a.key?'':'disabled'}>캐릭터 목록</button><button class="btn sm plain danger" data-accdel="${a.id}" title="이 API 키 삭제">삭제</button></span></div>`;
  }).join(''):'<div class="muted acc-empty">등록된 API 키가 없습니다. 아래에 키를 붙여넣고 <b>+ API 키 추가</b>를 누르면 바로 그 계정의 캐릭터 목록이 나와요.</div>';
  $('#newAccLabel').placeholder=accounts().length?`부계정${accounts().length}`:'본계정';
  $('#accOpts').innerHTML=accounts().length?`<label class="checkline"><input type="checkbox" id="sAutoEnable" ${S.settings.autoEnable?'checked':''}> 인게임 스케줄러에 등록된 보스를 자동으로 선택 목록에 추가</label>`:'';
}
function openAdd(){ openImport(); }
async function openImport(accId){
  const modal=$('#importModal'), wasOpen=modal.classList.contains('show');
  const usable=accounts().filter(a=>a.key);
  const a=(accById(accId)?.key&&accById(accId))||usable.find(x=>x.id===impAccId)||usable[0];
  modal.classList.add('show');
  if(!a){ impAccId=null; accChars=[]; renderAccList(); $('#impSec').classList.add('hidden'); setTimeout(()=>$('#newAccKey').focus(),50); return; }
  $('#impSec').classList.remove('hidden');
  if(impBusy===a.id) return; impBusy=a.id; impAccId=a.id; renderAccList();
  $('#impTitle').textContent=`'${a.label}' 계정 캐릭터`;
  accChars=[]; if(!wasOpen){ $('#impMin').value=''; $('#impQ').value=''; } $('#impWorld').innerHTML='<option value="">모든 월드</option>';
  $('#impList').innerHTML=''; $('#impCount').textContent='';
  const msg=$('#impMsg'); msg.className='impmsg'; msg.innerHTML=`<span class="spin"></span> '${esc(a.label)}' 계정의 캐릭터 목록을 불러오는 중…`;
  try{
    const all=await listAccount(a); if(impAccId!==a.id) return;
    const n=assignFromList(a,all); save();
    accChars=all.map(x=>({...x,accId:a.id})).sort((x,y)=>y.character_level-x.character_level||x.character_name.localeCompare(y.character_name));
    const worlds=[...new Set(accChars.map(x=>x.world_name).filter(Boolean))];
    $('#impWorld').innerHTML=`<option value="">모든 월드</option>`+worlds.map(w=>`<option>${esc(w)}</option>`).join('');
    const nAcc=listCache[a.id]?.accounts||0;
    if(!all.length){ msg.className='impmsg warn'; msg.innerHTML=emptyHtml(a)+`<div class="toolbar"><button class="btn sm plain" id="impRetry">다시 불러오기</button></div>`; }
    else { msg.className='impmsg ok'; msg.innerHTML=`✓ 캐릭터 <b>${all.length}명</b>${nAcc>1?` (메이플 계정 ${nAcc}개 합계)`:''}${n?` · 이미 등록된 ${n}명 이 계정으로 연결`:''} — 추가할 캐릭터를 골라 <b>선택 추가</b>를 누르세요.`; }
    renderImportList(); render();
  }catch(e){
    if(impAccId!==a.id) return;
    a.status={ok:false,msg:e.message,at:Date.now()}; save(); render();
    msg.className='impmsg err'; msg.innerHTML=errHtml(e,a)+`<div class="toolbar"><button class="btn sm plain" id="impRetry">다시 불러오기</button></div>`;
  }finally{ if(impBusy===a.id) impBusy=null; }
}
function addAccount(){
  const k=$('#newAccKey').value.trim(); if(!k){ toast('API 키를 붙여넣으세요'); $('#newAccKey').focus(); return; }
  const dup=accounts().find(a=>a.key===k); if(dup){ toast(`이미 '${dup.label}'(으)로 등록된 키입니다`); openImport(dup.id); return; }
  const n=accounts().length, label=$('#newAccLabel').value.trim()||(n?`부계정${n}`:'본계정');
  const a={id:uid(),label,key:k}; accounts().push(a); save();
  $('#newAccKey').value=''; $('#newAccLabel').value='';
  openImport(a.id); render();
}
function closeImport(){ $('#importModal').classList.remove('show'); }
function renderImportList(){
  const min=parseInt($('#impMin').value)||0, w=$('#impWorld').value, q=normName($('#impQ').value);
  const have=new Set(S.characters.map(c=>c.ocid).filter(Boolean)), haveName=new Set(S.characters.map(c=>c.name));
  const multi=(listCache[impAccId]?.accounts||0)>1;
  const list=accChars.filter(x=>x.character_level>=min&&(!w||x.world_name===w)&&(!q||normName(x.character_name+x.character_class).includes(q)));
  $('#impCount').textContent=accChars.length?(list.length===accChars.length?`${accChars.length}명`:`${accChars.length}명 중 ${list.length}명 표시`):'';
  if(!accChars.length){ $('#impList').innerHTML=''; return; }
  $('#impList').innerHTML=list.length?list.map(x=>{const dup=(x.ocid&&have.has(x.ocid))||haveName.has(x.character_name);return `<label class="imp-item ${dup?'dis':''}"><input type="checkbox" value="${esc(x.ocid)}" ${dup?'disabled':''}>
    <div class="grow" style="flex:1"><b>${esc(x.character_name)}</b> <span class="muted">Lv.${x.character_level} · ${esc(x.character_class)}</span></div><span class="muted">${esc(x.world_name)}${multi?` · 메이플 계정${x.accIdx+1}`:''}${dup?' · 추가됨':''}</span></label>`}).join('')
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
function applyOfficialPrices(pj){
  if(!pj||!Array.isArray(pj.rows)) return false;
  const today=dayId(); let changed=false, applied=0; const pending=[];
  for(const r of pj.rows){ const m=parseBossLabel(r.boss); const v=Math.round(+r.new); if(!m||!(v>0)) continue;
    const k=priceKey(m.b,m.d);
    if(r.effective && r.effective>today){ pending.push({key:k,effective:r.effective,price:v}); continue; } // 적용일 전에는 기존 값 유지
    if(PRICE_CONFIG[k]!==v){ PRICE_CONFIG[k]=v; changed=true; } applied++;
  }
  officialInfo={checkedAt:pj.checkedAt||'', source:pj.source||{}, applied, pending};
  return changed;
}
function loadOfficialPrices(){
  try{ const c=JSON.parse(localStorage.getItem(PRICES_CACHE_KEY)||'null'); if(c) applyOfficialPrices(c); }catch(e){}
  if(!/^https?:$/.test(location.protocol)) return; // 파일로 연 경우: 내장 기본값 사용
  fetch(`./prices.json?d=${dayId()}`,{cache:'no-cache'}).then(r=>r.ok?r.json():null).then(pj=>{
    if(!pj||!Array.isArray(pj.rows)||!pj.rows.length) return;
    localStorage.setItem(PRICES_CACHE_KEY,JSON.stringify(pj));
    if(applyOfficialPrices(pj)) save(); render();
  }).catch(()=>{});
}

/* =====================================================================
 *  동기화 서버 (Cloudflare Workers + D1, server/ 폴더) — 기능 플래그 (2026-10-10, 아직 꺼 둠)
 *  SYNC_API_URL 이 비어 있으면 지금처럼 구글 드라이브 동기화. 값이 있으면(또는 테스트용 localStorage 'mapleBossTracker.syncApi')
 *  같은 동기화 흐름(gdConnect/gdSync 3-way 병합/gdPush/gdPull)을 그대로 쓰고 저장소만 서버로 바뀜:
 *   - 로그인 = 넥슨 Open API 키 (서버가 넥슨에 확인 → 계정 식별, 원본 키는 서버에 저장 안 함) → 세션 토큰(localStorage)
 *   - 저장 = PUT /api/state (rev 로 동시 저장 감지, 409 → 받아온 내용과 3-way 병합 후 다시 저장). API 키는 보내지 않음(backupData(false))
 *   - 다른 기기에 내려받을 때 키: 로그인에 쓴 키만 자동으로 채움(계정의 ah = 서버가 준 계정 해시로 짝지음), 부계정 키는 대표 키(HKDF)로 AES-GCM 암호화해 서버 keyvault 에 보관 → 대표 키로 로그인하면 복원 (server/worker.js)
 *   - 옮기기: 처음 로그인 때 서버가 비어 있으면 이 PC 데이터를 올림 / '구글 드라이브에서 가져오기' 버튼(한 번, 클릭 시 구글 로그인)
 * ===================================================================== */
const SYNC_HOSTS = ['bossmaple.pages.dev']; // 이 주소로 열면 서버 동기화가 기본 (입장 화면 바로 표시). github.io 는 아직 구글 드라이브
const SYNC_API_URL = SYNC_HOSTS.includes(location.hostname) ? 'https://ggoolzip-sync.bossmaple.workers.dev' : ''; // 비우면 구글 드라이브
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
const svDev=()=>{ try{ return localStorage.getItem(SV_DEVICE_KEY)||''; }catch(e){ return ''; } };
const svTok=()=>{ try{ return localStorage.getItem(SV_TOKEN_KEY)||''; }catch(e){ return ''; } };
const SV_NEED_LOGIN='로그인이 필요해요 — 상단 ☁ 버튼에서 넥슨 API 키로 로그인하면 이어서 동기화돼요 (바꾼 내용은 이 PC에 그대로 있어요)';
async function svFetch(path,opt={}){
  const tok=svTok(); if(!tok&&!opt.noAuth) throw Object.assign(new Error(SV_NEED_LOGIN),{type:'interaction_required'});
  let r;
  try{ r=await fetch(SV_ON+path,{method:opt.method||'GET',keepalive:!!opt.keepalive,headers:{'Content-Type':'application/json',...(opt.noAuth?{}:{Authorization:'Bearer '+tok})},body:opt.body===undefined?undefined:JSON.stringify(opt.body)}); }
  catch(e){ throw Object.assign(new Error('동기화 서버에 연결하지 못했습니다 (인터넷 연결 확인)'),{type:'network'}); }
  let b=null; try{ b=await r.json(); }catch(e){}
  if(r.status===401&&!opt.noAuth){ localStorage.removeItem(SV_TOKEN_KEY); throw Object.assign(new Error(SV_NEED_LOGIN),{type:'interaction_required'}); }
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
    if(SV_ON){ L.off='☁ 로그인'; L.reconnect='☁ 다시 로그인'; }
    b.textContent=SV_ON?(L[gd.state]||'☁ 동기화'):!gcid()?'☁ 구글':!gdOriginOk()?'☁ 구글 (온라인 전용)':(L[gd.state]||'☁ 구글'); b.classList.toggle('warn',['reconnect','conflict','error'].includes(gd.state));
    b.title=gd.msg||(SV_ON?'동기화 (넥슨 API 키로 로그인)':'구글 드라이브 동기화');
  }
  const st=$('#gdStatus'); if(st) st.innerHTML=gdStatusHtml();
}
function svLoginHtml(){ // 서버 모드 로그인: (기기당 한 번) 초대 비밀번호 → 이 PC 에 등록된 키로 / 새 키 입력 (키는 화면에 표시하지 않음)
  if(!svDev()) return `<div class="svlogin"><div class="muted tiny" style="margin:0 0 6px">친구 초대 전용이에요. <b>초대 비밀번호</b>를 넣어 주세요 (이 기기에서 한 번만).</div>
    <div class="row" style="display:flex;gap:6px"><input class="pin" id="svInvite" type="password" autocomplete="off" placeholder="초대 비밀번호" style="flex:1;min-width:0;text-align:left"><button class="btn sm" id="svInviteBtn">확인</button></div>
    ${gd.svErr?`<div class="impmsg warn" style="margin-top:6px">${esc(gd.svErr)}</div>`:''}</div>`;
  const ks=accounts().filter(a=>a.key).sort((x,y)=>(y.main?1:0)-(x.main?1:0));
  return `<div class="svlogin"><div class="muted tiny" style="margin:0 0 6px"><b>대표 키</b>(본계정 넥슨 Open API 키)로 로그인하세요. 다른 기기에서도 대표 키만 넣으면 데이터와 등록한 <b>부계정 키</b>가 그대로 돌아와요. 대표 키 자체는 서버에 저장되지 않아요.</div>
    ${ks.length?`<div class="toolbar">${ks.map(a=>`<button class="btn sm" data-svlogin="${a.id}">${esc(a.label)} 키를 대표 키로 로그인</button>`).join('')}</div>`:''}
    <div class="row" style="display:flex;gap:6px;margin-top:6px"><input class="pin" id="svKey" type="password" autocomplete="off" placeholder="대표 키 (넥슨 API 키) 붙여넣기" style="flex:1;min-width:0;text-align:left"><button class="btn sm" id="svLoginBtn">대표 키로 로그인</button></div>
    ${gd.svErr?`<div class="impmsg warn" style="margin-top:6px">${esc(gd.svErr)}</div>`:''}</div>`;
}
function svSubHtml(){ // 로그인 후: 대표 키 / 부계정 키 추가 (부계정 키는 대표 키로 암호화해 서버 보관)
  const m=svMain(), subs=accounts().filter(a=>a.key&&a!==m&&(!m||a.key!==m.key));
  return `<div class="svsub" style="margin-top:8px"><div class="muted tiny">대표 키: <b>${m?esc(m.label):'이 기기에 없음'}</b> · 부계정 키 ${subs.length}개${subs.length?` (${subs.map(a=>esc(a.label)).join(', ')})`:''}${m?' — 대표 키로 암호화해 서버에 보관':' — 대표 키로 로그인해야 서버에 보관돼요'}</div>
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
      ${svSubHtml()}
      ${driveUsable()?`<div class="toolbar" style="margin-top:6px"><button class="btn sm ghost" id="svImportDrive" title="예전 구글 드라이브 저장본을 이 PC 데이터와 합친 뒤 서버에 저장 (구글 로그인 창이 한 번 뜸)">구글 드라이브에서 가져오기 (한 번)</button></div>`:''}`
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
    <p class="muted tiny">${SV_ON?'🔑 대표 키는 서버에 저장되지 않아요. 부계정 키는 대표 키로 암호화해 보관해서, 다른 기기에서 대표 키로 로그인하면 함께 돌아와요. 변경 후 약 5초 뒤·창을 닫을 때 자동 저장.':'🔑 API 키도 함께 저장돼요 (내 드라이브 앱 전용 숨김 폴더). 변경 후 약 5초 뒤·창을 닫을 때 자동 저장.'}</p>`;
  if(SV_ON) inner=`<div id="gdStatus">${gdStatusHtml()}</div><p class="muted tiny">🔑 대표 키는 서버에 저장되지 않아요. 부계정 키는 대표 키로 암호화해 보관해서, 다른 기기에서 대표 키로 로그인하면 함께 돌아와요. 변경 후 약 5초 뒤·창을 닫을 때 자동 저장.</p>`;
  return `<div class="gm-h"><b>${SV_ON?'☁️ 동기화':'☁️ 구글 드라이브 동기화'}</b><button class="ringx" id="gMenuClose" aria-label="닫기">✕</button></div>${inner}`;
}
function gdMenu(open){
  const m=$('#gMenu'); if(!m) return; const show=open??m.hidden;
  if(show) m.innerHTML=gdMenuHtml();
  m.hidden=!show; $('#gBtn').setAttribute('aria-expanded',String(show));
}
function gdHeaderClick(){ if(gd.state==='conflict'&&gd.pending){ gdMenu(false); return gdReask(); }
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
    try{ await gdSync(svRemote(r)); } finally{ gd.w409=0; }
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
 * 비교(contentSig)에서 빼는 값 = GD_LOCAL_RE: 기기 전용(테마·선택 캐릭터·날짜 period·마지막 동기화 시각) + 자동 갱신 값(캐릭터 sync/이미지/EXP, 계정 상태·키).
 *   이 값들은 병합할 때도 '이 PC 값'을 씀(키는 이 PC 에 없으면 드라이브 값).
 * 병합 = 3-way: 마지막으로 맞춘 내용(base, localStorage GD_BASE_KEY) 기준으로 한쪽만 바뀐 항목은 그쪽 값, 양쪽이 같은 항목을 다르게 바꾼 경우만 '충돌'.
 *   캐릭터·계정은 id, 주간/월간 기록은 week/month 로 짝지음. 한쪽 삭제 + 다른 쪽 수정 → 수정본 유지(데이터 안 잃음).
 *   API 로 다시 받는 값(레벨·직업·월드·ocid·계정 배정)과 지난 기록 요약은 충돌이어도 묻지 않음(이 PC 값 / 클리어 많은 쪽). */
const GD_BASE_KEY=SV_ON?'mapleBossTracker.svbase':'mapleBossTracker.gdbase';
const GD_LOCAL_RE=/^(theme|activeId|period|updatedAt|version|startWeek)$|^settings\.(lastSync|autoSync|apiKey|driveKeys|apiMode|prices|priceSource|worldLimit)$|^characters\[[^\]]*\]\.(sync|image|exp)$|^settings\.accounts\[[^\]]*\]\.(key|status)$/;
const GD_SOFT_RE=/^characters\[[^\]]*\]\.(level|job|world|ocid|accId)$/;
const GD_HIST_RE=/^(history|monthHistory)\[[^\]]*\]$/;
const GD_KEYED={characters:'id',history:'week',monthHistory:'month','settings.accounts':'id'};
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
  if(p&&GD_LOCAL_RE.test(p)) return l!==undefined&&l!==''&&l!==null?l:r;
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
async function gdSync(remote){
  if(!remote?.data || !Array.isArray(remote.data.characters)) throw new Error('드라이브 파일 형식이 올바르지 않습니다');
  if(gdLocalEmpty()){ gdApply(remote,null); return 'loaded'; }
  const rU=+remote.updatedAt||0, lU=S.updatedAt||0;
  const rd=gdPrep(remote.data), ld=gdPrep(backupData(true));
  let bd=gdBaseData(); bd=bd?gdPrep(bd):null;
  if(!bd&&gdMeta.base){ if(rU===gdMeta.base) bd=rd; else if(lU===gdMeta.base) bd=ld; }
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
  ['history','monthHistory'].forEach(k=>{ if(Array.isArray(m[k])) m[k].sort((a,b)=>String(a.week||a.month)<String(b.week||b.month)?-1:1); });
  const mS=contentSig(m), toLocal=mS!==contentSig(gdPrep(backupData(true))), toRemote=mS!==contentSig(rd)||!remote.withKeys;
  if(toLocal){ m.updatedAt=gdSig(m)===gdSig(rd)&&!toRemote?rU:Date.now(); gdLoad(m); }
  if(toRemote){ await gdWrite(); }
  else { if((S.updatedAt||0)!==rU){ S.updatedAt=rU; localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(S)); } gdMeta.lastLoad=Date.now(); gdMarkSynced(rU); }
  if(toLocal) toast('☁ '+(toRemote?GD_RES_MSG.merged:GD_RES_MSG.pulled));
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
const GD_FIELD={name:'이름',bosses:'보스 설정',weekly:'주간 체크',monthly:'월간 체크',auto:'자동 체크',drops:'획득 아이템',mdrops:'월간 획득 아이템',dropOut:'반지 결과',mdropOut:'반지 결과',isMain:'본캐 지정',
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
  if(!gdMeta.on||!gdUsable()||gd.state==='conflict') return;
  if(gd.state==='reconnect'&&!gdHasTok()){ gdRender(); return; } // 로그인 필요 상태: 이 PC 에만 저장, 다시 연결할 때 합쳐서 저장
  clearTimeout(gd.timer); gd.timer=setTimeout(()=>{ gd.timer=null; gdPush(); },GD.DEBOUNCE); gdRender();
}
// 다른 기기에서 바뀐 내용 확인 (탭으로 돌아올 때·1분마다, 메타데이터만 조회 → 바뀌었을 때만 내용 읽어서 합침)
async function gdPull(force){
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
            const res=await gdSync(await gdRead(gd.fileId)); if(res==='ask') return false; gdSet('on',GD_RES_MSG[res]||''); return true; }
        }catch(e){ if(e.status===404) gd.fileId=null; else throw e; }
      }
    }
    await gdWrite(opts.quick); gdSet('on'); return true;
  }catch(e){ gdFail(e,opts.manual); return false; }
  finally{ gd.ia=false; gd.busy=false; if(gd.again){ gd.again=false; gdChanged(); } }
}
function gdLogin(){ $('#driveModal').classList.remove('show'); if(SV_ON){ gdMenu(true); setTimeout(()=>$('#svKey')?.focus(),0); return; } gdConnect(true); }
/* ---- 서버 모드: 로그인 · 키 연결 · 드라이브에서 가져오기 ---- */
async function svLogin(key,accId){
  key=String(key||'').trim(); if(!key){ gd.svErr='API 키를 넣어 주세요'; return gdRender(); }
  gd.svErr=''; gdSet('connecting','넥슨 API 키 확인 중…'); if($('#svGate')) svGate();
  try{
    const b=await svFetch('/api/login',{method:'POST',noAuth:true,body:{key,device:svDev(),label:(navigator.userAgentData?.platform||navigator.platform||'').slice(0,30)}});
    localStorage.setItem(SV_TOKEN_KEY,b.token);
    // 이 PC 데이터 주인 확인: 다른 사용자 → 비우고 서버 데이터만 / 같은 사용자 → 그대로 맞춤 / 이 기기 첫 로그인 → 물어봄
    const prev=localStorage.getItem(SV_USER_KEY);
    const keep=prev?prev===b.user:(gdLocalEmpty()||confirm(b.rev?'이 PC 데이터를 이 계정 데이터와 합칠까요?\n[취소]를 누르면 이 PC 데이터는 지우고 서버에 있는 이 계정 데이터만 불러옵니다.':'이 PC 데이터를 이 계정으로 올릴까요?\n[취소]를 누르면 이 PC 데이터는 지우고 빈 상태로 시작합니다.'));
    if(!keep){ svWipeLocal(); accId=''; }
    localStorage.setItem(SV_USER_KEY,b.user);
    gd.login={key,accId:accId||'',hashes:b.accounts||[],vault:b.vault||'none',subs:b.subKeys||[]};
    const la=(accId&&accById(accId))||(keep?accounts().find(x=>x.key===key):null); // 등록된 키로 로그인: 첫 저장 전에 계정 해시(ah)를 붙여 둠 → 다른 기기에서 키 짝짓기
    if(la&&((b.accounts?.[0]&&!(b.accounts||[]).includes(la.ah))||(b.vault!=='locked'&&!la.main))){ if(b.accounts?.[0]&&!(b.accounts||[]).includes(la.ah)) la.ah=b.accounts[0]; if(b.vault!=='locked'){ accounts().forEach(x=>delete x.main); la.main=true; } save(); clearTimeout(gd.timer); gd.timer=null; }
    gdMeta={on:true}; gdSaveMeta(); localStorage.removeItem(GD_BASE_KEY); gd.remoteRev=undefined; gd.fileId=null;
    await gdConnect(true);
    svGate();
    svAfterLogin();
    if(gd.state==='on') toast('☁ 로그인했습니다'+(b.newUser?' — 이 데이터를 서버에 저장합니다':''));
  }catch(e){ if(e.code==='need_invite') localStorage.removeItem(SV_DEVICE_KEY); gd.svErr=e.message; gdSet('off'); if($('#svGate')) svGate(); else gdMenu(true); }
}
function svWipeLocal(){ // 이 브라우저의 보스 데이터 비우기 (테마·기기 표·서버 주소는 유지)
  const th=S.theme; clearTimeout(gd.timer); gd.timer=null; localStorage.removeItem(GD_BASE_KEY); localStorage.removeItem(SV_SUBSIG_KEY);
  const d=defaultState(); d.theme=th; gdLoad(d); lastSig=contentSig(S);
}
function svGate(){ // 서버 모드 입장 화면: ① 초대 비밀번호 → ② 대표 키 → ③ 로그인 성공 후에만 사이트 내용 (세션이 있으면 바로 사이트)
  let g=$('#svGate');
  if(!SV_ON||(svTok()&&gdMeta.on)){ if(g){ g.remove(); document.documentElement.classList.remove('gated'); } return; }
  if(!g){ g=document.createElement('div'); g.id='svGate'; document.body.appendChild(g); document.documentElement.classList.add('gated'); }
  const err=gd.svErr?`<div class="impmsg warn" style="margin-top:10px">${esc(gd.svErr)}</div>`:'';
  const step=svDev()?2:1, busy=gd.state==='connecting';
  g.innerHTML=`<div class="svgbox" data-step="${step}"><div class="svgt">보스 캐릭터 관리</div>${step===1
    ?`<div class="svgd">친구 초대 전용이에요. <b>초대 비밀번호</b>를 넣어 주세요.<br><span class="muted">이 기기에서 한 번만 물어봐요.</span></div>
      <div class="svgr"><input class="pin" id="svInvite" type="password" autocomplete="off" placeholder="초대 비밀번호"><button class="btn sm" id="svInviteBtn">확인</button></div>`
    :`<div class="svgd"><b>대표 키</b>(본계정 넥슨 Open API 키)로 로그인하세요.<br><span class="muted">대표 키는 서버에 저장되지 않아요. 등록한 부계정 키는 다른 기기에서도 대표 키만 넣으면 돌아와요.</span></div>
      <div class="svgr"><input class="pin" id="svKey" type="password" autocomplete="off" placeholder="대표 키 붙여넣기"${busy?' disabled':''}><button class="btn sm" id="svLoginBtn"${busy?' disabled':''}>${busy?'확인 중…':'로그인'}</button></div>
      <details class="svghelp" open><summary>넥슨 API 키 받는 법</summary><ol>
        <li><a href="https://openapi.nexon.com/ko/" target="_blank" rel="noopener">openapi.nexon.com</a> 에서 넥슨 ID로 로그인</li>
        <li>내 애플리케이션 → <b>애플리케이션 등록</b></li>
        <li>게임은 <b>메이플스토리</b>, 타입은 <b>개발 단계</b>(서비스명만 입력) → 약관 동의 후 등록</li>
        <li>애플리케이션 상세 화면의 <b>API Key</b>를 복사해 위에 붙여넣기</li></ol>
        <div class="muted">넥슨 계정마다 키가 따로 있어요 (부계정은 로그인 후 따로 추가).</div></details>`}
    ${err}</div>`;
  setTimeout(()=>$(step===1?'#svGate #svInvite':'#svGate #svKey')?.focus(),0);
}
async function svInvite(pass){
  if(!String(pass||'').trim()){ gd.svErr='초대 비밀번호를 넣어 주세요'; return gdMenu(true); }
  gd.svErr='';
  try{ const b=await svFetch('/api/invite',{method:'POST',noAuth:true,body:{pass}}); localStorage.setItem(SV_DEVICE_KEY,b.device); toast('초대 확인 완료 — 이제 넥슨 API 키로 로그인하세요'); }
  catch(e){ gd.svErr=e.message; }
  if($('#svGate')) return svGate();
  gdMenu(true); setTimeout(()=>$(svDev()?'#svKey':'#svInvite')?.focus(),0);
}
// 로그인에 쓴 키를 계정에 연결: 그 계정의 ah(서버 계정 해시) 기록 / 내려받은 데이터에서 같은 ah 계정에 키 채움 / 없으면 새 계정
function svAfterLogin(){
  const L=gd.login; if(!L||gd.state==='conflict') return; gd.login=null; let ch=false; // 질문 화면이면 고른 뒤(gdResolve)에 다시
  const hs=new Set(L.hashes), acc=accounts();
  let a=(L.accId&&acc.find(x=>x.id===L.accId))||acc.find(x=>x.key===L.key)||acc.find(x=>!x.key&&hs.has(x.ah));
  if(!a){ a={id:'a'+Date.now().toString(36),label:acc.length?`계정${acc.length+1}`:'본계정',key:L.key}; S.settings.accounts=[...acc,a]; ch=true; }
  if(!a.key){ a.key=L.key; ch=true; }
  if(L.hashes[0]&&a.ah!==L.hashes[0]&&!hs.has(a.ah)){ a.ah=L.hashes[0]; ch=true; }
  if(L.vault!=='locked'){ for(const x of accounts()) if(!!x.main!==(x===a)){ x.main=x===a||undefined; if(!x.main) delete x.main; ch=true; } } // 대표 키 = 로그인에 쓴 키 (부계정 키로 로그인하면 그대로)
  let back=0;
  for(const sub of L.subs||[]){ // 대표 키로 로그인 → 서버가 풀어 준 부계정 키 채우기
    if(!sub?.key||sub.key===a.key) continue;
    const ac=accounts(), x=ac.find(y=>y.key===sub.key)||ac.find(y=>!y.key&&sub.ah&&y.ah===sub.ah);
    if(x){ if(!x.key){ x.key=sub.key; ch=true; back++; } if(sub.ah&&!x.ah){ x.ah=sub.ah; ch=true; } }
    else { S.settings.accounts=[...ac,{id:'a'+Date.now().toString(36)+ac.length,label:sub.label||`부계정${ac.length}`,key:sub.key,...(sub.ah?{ah:sub.ah}:{})}]; ch=true; back++; }
  }
  if(back) toast(`부계정 키 ${back}개를 불러왔습니다`);
  if(L.vault==='open'&&!back) localStorage.setItem(SV_SUBSIG_KEY,svSubSig()); // 서버 금고와 같으면 다시 올리지 않음
  if(ch){ save(); render(); }
  if(svMain()&&svSubSig()!==localStorage.getItem(SV_SUBSIG_KEY)) svSyncSubKeys().then(()=>gdRender()).catch(()=>{});
}
const svMain=()=>accounts().find(a=>a.main&&a.key)||null;
const svSubSig=()=>{ const m=svMain(); return m?JSON.stringify([m.key,...accounts().filter(a=>a.key&&a!==m&&a.key!==m.key).map(a=>[a.key,a.label])]):''; };
// 부계정 키를 서버 금고에 (대표 키로 암호화) — 바뀌었을 때만. 대표 키가 이 기기에 없으면 예전처럼 연결만.
async function svSyncSubKeys(){
  const m=svMain(); if(!m) return svLinkNewKeys();
  const sig=svSubSig(); if(sig===localStorage.getItem(SV_SUBSIG_KEY)) return svLinkNewKeys();
  const subs=accounts().filter(a=>a.key&&a!==m&&a.key!==m.key);
  if(!subs.length&&!localStorage.getItem(SV_SUBSIG_KEY)){ localStorage.setItem(SV_SUBSIG_KEY,sig); return; } // 부계정 키가 처음부터 없으면 서버에 올릴 것 없음
  try{
    const r=await svFetch('/api/subkeys',{method:'PUT',body:{main:m.key,subs:subs.map(a=>({key:a.key,label:a.label}))}});
    let ch=false; (r.subs||[]).forEach((x,i)=>{ const a=subs[i]; if(a&&x.ah&&a.ah!==x.ah){ a.ah=x.ah; ch=true; } });
    localStorage.setItem(SV_SUBSIG_KEY,sig);
    if(ch){ S.updatedAt=Date.now(); lastSig=contentSig(S); lastBody=bodyOf(); localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(S)); }
  }catch(e){ if(e.type==='interaction_required') throw e; toast('부계정 키 보관: '+e.message); localStorage.setItem(SV_SUBSIG_KEY,sig); }
}
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
async function gdLogout(){ // 로그아웃만 (이 브라우저 데이터는 그대로 둠 — PC방은 종료 시 자동 초기화)
  if(SV_ON){
    if(gdMeta.on && gdLocalDirty() && svTok()){ const ok=await gdPush(); if(!ok && !confirm('서버에 최신 내용을 저장하지 못했습니다. 그래도 로그아웃할까요? (저장 안 된 변경은 사라집니다)')) return; }
    try{ if(svTok()) await svFetch('/api/logout',{method:'POST'}); }catch(e){}
    clearTimeout(gd.timer); gd.timer=null; gd.fileId=null; gd.remoteRev=undefined; localStorage.removeItem(SV_TOKEN_KEY); localStorage.removeItem(SV_SUBSIG_KEY);
    gdMeta={}; localStorage.removeItem(GD.META_KEY); localStorage.removeItem(GD_BASE_KEY);
    svWipeLocal(); gdSet('off'); render(); svGate(); toast('로그아웃했습니다 (이 PC의 보스 데이터도 지웠어요 — 다시 로그인하면 서버에서 불러옵니다)'); return;
  }
  if(gdMeta.on && gdLocalDirty()){
    const ok=gdHasTok() ? await gdPush() : false;
    if(!ok && !confirm('드라이브에 최신 내용을 저장하지 못했습니다. 그래도 로그아웃할까요? (이 PC에는 그대로 남아 있고, 다음 로그인 때 다시 맞춥니다)')) return;
  }
  try{ if(gd.token&&window.google?.accounts?.oauth2?.revoke) google.accounts.oauth2.revoke(gd.token,()=>{}); }catch(e){}
  clearTimeout(gd.timer); gd.timer=null; gd.token=null; gd.exp=0; gd.fileId=null; sessionStorage.removeItem(GD.TOKEN_KEY);
  gdMeta={}; localStorage.removeItem(GD.META_KEY); localStorage.removeItem(GD_BASE_KEY);
  gdSet('off'); render(); toast('구글 드라이브에서 로그아웃했습니다');
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
  const dc=e.target.closest('[data-drop]'); if(dc){ changeDrop(dc.dataset.drop,+1); return; }
  if(e.target.closest('.drop.erda')) return; // 솔 에르다의 기운: 정보 표시 전용 (클릭해도 아무 일 없음)
  const svl=e.target.closest('[data-svlogin]'); if(svl){ const a=accById(svl.dataset.svlogin); if(a&&a.key) svLogin(a.key,a.id); return; }
  const t=e.target.closest('[data-tab],[data-dqg],[data-dqc],[data-dqhide],[data-move],[data-wmove],[data-id],[data-edit],[data-filter],[data-check],[data-toggle],[data-setdiff],[data-delhist],[data-acctest],[data-accdel],button[id]');
  if(!t) return;
  const c=activeChar();
  if(t.dataset.tab){ tab=t.dataset.tab; syncTabs(); render(); tabTick(); return; }
  if(t.dataset.dqg){ const k=t.dataset.dqg; if(S.dq.off[k]) delete S.dq.off[k]; else S.dq.off[k]=1; save(); renderDaily(); return; }
  if(t.dataset.dqc){ dqToggleChar(t.dataset.dqc); return; }
  if(t.dataset.dqhide){ const id=t.dataset.dqhide; if(S.dq.hide[id]) delete S.dq.hide[id]; else S.dq.hide[id]=1; save(); renderDaily(); return; }
  if(t.dataset.move){ e.stopPropagation(); const [id,d]=t.dataset.move.split('|'); moveCharBy(id,+d); render(); return; }
  if(t.dataset.wmove){ e.stopPropagation(); const i=t.dataset.wmove.lastIndexOf('|'); moveWorldBy(t.dataset.wmove.slice(0,i),+t.dataset.wmove.slice(i+1)); render(); return; }
  if(e.target.closest('.drag-h')) return;
  if(t.dataset.edit){ e.stopPropagation(); openCharModal(t.dataset.edit); return; }
  if(t.dataset.id){ S.activeId=t.dataset.id; save(); if(['history','total','daily','guild'].includes(tab)) {tab='boss';syncTabs();} render(); return; }
  if(t.dataset.filter){ bossFilter=t.dataset.filter; render(); return; }
  if(t.dataset.toggle && c){ const s=t.dataset.toggle,b=findBoss(s); const cfg=c.bosses[s]||(c.bosses[s]={enabled:false,diff:b.diffs[0],party:1}); cfg.enabled=!cfg.enabled; save(); render(); return; }
  if(t.dataset.setdiff && c){
    if(t.classList.contains('locked')){toast('클리어 체크를 해제한 뒤 난이도를 바꾸세요');return;}
    const [s,d]=t.dataset.setdiff.split('|'); const cfg=c.bosses[s]||(c.bosses[s]={enabled:editMode,diff:d,party:1});
    cfg.diff=d; clampParty(c,s); save(); render(); return;
  }
  if(t.dataset.check && c){
    const s=t.dataset.check,b=findBoss(s);
    if(b.type==='weekly'){
      if(c.weekly[s]){ delete c.weekly[s]; delete c.auto[s]; }
      else { if(weeklyCount(c)>=S.settings.weeklyLimit){ toast(`주간 보스는 캐릭터당 ${S.settings.weeklyLimit}개까지 처치할 수 있습니다`); return; } c.weekly[s]=true; }
    } else {
      if(c.monthly[s]){ delete c.monthly[s]; delete c.auto[s]; }
      else { if(monthlyCount(c)>=S.settings.monthlyLimit){ toast(`월간 보스는 월 ${S.settings.monthlyLimit}회까지입니다`); return; } c.monthly[s]=S.period.week; }
    }
    save(); render(); return;
  }
  if(t.dataset.acctest){ const a=accById(t.dataset.acctest); if(a&&a.key) openImport(a.id); return; }
  if(t.dataset.accdel){ const a=accById(t.dataset.accdel); if(!a) return; const n=S.characters.filter(c=>c.accId===a.id).length;
    if(confirm(`'${a.label}' 계정을 삭제할까요?${n?`\n연결된 캐릭터 ${n}명은 삭제되지 않고 '계정 미지정' 상태가 됩니다.`:''}`)){ S.characters.forEach(c=>{ if(c.accId===a.id) delete c.accId; }); S.settings.accounts=accounts().filter(x=>x!==a); if(impAccId===a.id){ impAccId=null; accChars=[]; } save(); render(); if($('#importModal').classList.contains('show')) openImport(); } return; }
  if(t.dataset.delhist){ if(confirm('이 주간 기록을 삭제할까요?')){ S.history=S.history.filter(h=>h.week!==t.dataset.delhist); save(); render(); } return; }
  switch(t.id){
    case 'editModeBtn': editMode=!editMode; render(); break;
    case 'dqEditBtn': dqEdit=!dqEdit; renderDaily(); break;
    case 'syncBtn': syncAll(); break;
    case 'importAccBtn': openImport(); break;
    case 'impRetry': openImport(impAccId); break;
    case 'impManual': closeImport(); openCharModal(); break;
    case 'impToSettings': $('#newAccKey')?.focus(); break;
    case 'impClear': $('#impMin').value=''; $('#impQ').value=''; $('#impWorld').value=''; renderImportList(); break;
    case 'newAccBtn': addAccount(); break;
    case 'impClose': closeImport(); break;
    case 'gMenuClose': gdMenu(false); break;
    case 'gBtn': gdHeaderClick(); break;
    case 'gdLogin': gdLogin(); break;
    case 'svSubBtn': svAddSub($('#svSubKey')?.value); break;
    case 'svInviteBtn': svInvite(($('#svGate #svInvite')||$('#svInvite'))?.value); break;
    case 'svLoginBtn': if($('#svGate')){ svLogin($('#svGate #svKey')?.value); break; } svLogin($('#svKey')?.value); break;
    case 'svImportDrive': gdMenu(false); svImportDrive(); break;
    case 'gdLogout': gdLogout(false); break;
    case 'gdSaveNow': gdPush({manual:true}); break;
    case 'gdUseDrive': gdResolve('drive'); break;
    case 'gdUseLocal': gdResolve('local'); break;
    case 'gdClose': $('#driveModal').classList.remove('show'); break;
  }
});
function dqToggleChar(v){ const [id,k]=v.split('|'); const o=S.dq.charOff[id]||(S.dq.charOff[id]={}); if(o[k]) delete o[k]; else o[k]=1; if(!Object.keys(o).length) delete S.dq.charOff[id]; save(); renderDaily(); }
document.addEventListener('keydown',e=>{ const q=(e.key==='Enter'||e.key===' ')&&e.target.closest?.('[data-dqc]'); if(q){ e.preventDefault(); dqToggleChar(q.dataset.dqc); } });
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ if($('#ringModal').classList.contains('show')) closeRing(); if(celebrate.running) endCelebrate(); if($('#importModal').classList.contains('show')&&!$('#charModal').classList.contains('show')) closeImport(); gdMenu(false); } });
document.addEventListener('keydown',e=>{ const wt=e.target.closest?.('[data-wtab]'); if(wt&&(e.key==='Enter'||e.key===' ')){ e.preventDefault(); if(wt.dataset.wtab!==worldTab) setWorldTab(wt.dataset.wtab); } });
document.addEventListener('contextmenu',e=>{ const dc=e.target.closest('[data-drop]'); if(!dc) return; e.preventDefault(); if(tipTouchAt&&Date.now()-tipTouchAt<1500) return; /* 터치 길게 누르기 = 툴팁 보기 (취소는 − 버튼) */ changeDrop(dc.dataset.drop,-1); });
/* 드롭 칩 툴팁 (마우스 올림 + 터치): [data-tip] — 터치는 누르는 순간 표시(클릭 동작은 그대로), 3초 뒤·다른 곳 터치 시 닫힘 */
let tipEl=null, tipFor=null, tipTimer=0, tipTouchAt=0;
function tipShow(el){
  if(!tipEl){ tipEl=document.createElement('div'); tipEl.id='mbtTip'; tipEl.setAttribute('role','tooltip'); document.body.appendChild(tipEl); }
  tipFor=el; const [h0,...rest]=String(el.dataset.tip).split('\n'); // 첫 줄 = 굵은 제목(아이템 이름)
  tipEl.replaceChildren(Object.assign(document.createElement('b'),{className:'tth',textContent:h0}),...(rest.length?['\n'+rest.join('\n')]:[])); tipEl.classList.add('show');
  const r=el.getBoundingClientRect(), w=tipEl.offsetWidth, h=tipEl.offsetHeight, m=8;
  let x=Math.min(Math.max(m,r.left+r.width/2-w/2),innerWidth-w-m), y=r.top-h-8; if(y<m) y=Math.min(r.bottom+8,innerHeight-h-m);
  tipEl.style.left=x+'px'; tipEl.style.top=y+'px';
}
function tipHide(){ clearTimeout(tipTimer); tipFor=null; if(tipEl) tipEl.classList.remove('show'); }
document.addEventListener('pointerover',e=>{ if(e.pointerType==='touch') return; const t=e.target.closest?.('[data-tip]'); if(t&&(t!==tipFor||!tipEl?.classList.contains('show'))) tipShow(t); else if(!t&&tipFor) tipHide(); });
document.addEventListener('pointerdown',e=>{ const t=e.target.closest?.('[data-tip]');
  if(e.pointerType==='touch'){ tipTouchAt=t?Date.now():0; if(t){ tipShow(t); clearTimeout(tipTimer); tipTimer=setTimeout(tipHide,3000); } else tipHide(); } },true);
let tipKbd=false; // 키보드(Tab)로 칩에 왔을 때만 포커스로 표시/숨김 — 클릭·터치 뒤 다시 그려질 때 툴팁이 사라지지 않게
document.addEventListener('keydown',e=>{ if(e.key==='Tab') tipKbd=true; },true);
document.addEventListener('keydown',e=>{ if(e.key==='Enter'&&e.target.id==='svKey'){ e.preventDefault(); svLogin(e.target.value); } if(e.key==='Enter'&&e.target.id==='svSubKey'){ e.preventDefault(); svAddSub(e.target.value); } if(e.key==='Enter'&&e.target.id==='svInvite'){ e.preventDefault(); svInvite(e.target.value); } });
document.addEventListener('pointerdown',()=>{ tipKbd=false; },true);
document.addEventListener('focusin',e=>{ if(!tipKbd) return; const t=e.target.closest?.('[data-tip]'); if(t) tipShow(t); });
document.addEventListener('focusout',()=>{ if(tipKbd) tipHide(); });
addEventListener('scroll',()=>{ if(tipFor&&tipFor.isConnected&&tipEl.classList.contains('show')) tipShow(tipFor); },true); // 스크롤하면 위치만 다시 맞춤
document.addEventListener('keydown',e=>{ const dc=e.target.closest?.('[data-drop]'); if(!dc) return; if(e.key==='Enter'||e.key===' '){ e.preventDefault(); changeDrop(dc.dataset.drop,+1); } else if(e.key==='Backspace'||e.key==='Delete'||e.key==='-'){ e.preventDefault(); changeDrop(dc.dataset.drop,-1); } });
document.addEventListener('change',e=>{
  const t=e.target; const c=activeChar();
  if(t.dataset.party && c){ const s=t.dataset.party; c.bosses[s].party=parseInt(t.value)||1; clampParty(c,s); save(); render(); }
  if(t.id==='sAutoEnable'){ S.settings.autoEnable=t.checked; save(); }
  if(t.id==='impWorld') renderImportList();
  if(t.dataset.acclabel){ const a=accById(t.dataset.acclabel); if(a){ a.label=t.value.trim()||a.label; save(); render(); if(a.id===impAccId) $('#impTitle').textContent=`'${a.label}' 계정 캐릭터`; } }
});
$('#ricR').innerHTML=miniIcon('ring_restraint'); $('#ricC').innerHTML=miniIcon('ring_continuous');
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
document.addEventListener('keydown',e=>{ if(!$('#charModal').classList.contains('show')) return; if(e.key==='Escape') closeCharModal(); if(e.key==='Enter'&&e.target.id!=='fName') saveChar(); if(e.key==='Enter'&&e.target.id==='fName') (hasApi()?lookupByName():saveChar()); });
$('#themeBtn').onclick=()=>{ const dark=document.documentElement.dataset.theme==='dark'; S.theme=dark?'light':'dark'; save(); applyTheme(); };

// 드라이브 저장용 직렬화 (withKeys=true: API 키 포함 / false: 비교용, 키 제외)
function backupData(withKeys){
  const data=JSON.parse(JSON.stringify(S)); delete data.settings.apiKey;
  data.settings.accounts=(data.settings.accounts||[]).map(a=>({id:a.id,label:a.label,...(a.ah?{ah:a.ah}:{}),...(a.main?{main:true}:{}),...(withKeys?{key:a.key||''}:{})})); // ah: 동기화 서버 계정 해시(키 아님)
  return data;
}
// 드라이브 데이터 적용: 데이터에 키가 없으면 이 브라우저의 키를 계정 id 기준으로 다시 연결하고, 없는 계정은 유지
function applyData(d){
  d.settings=d.settings||{}; const cur=accounts();
  const acc=(Array.isArray(d.settings.accounts)?d.settings.accounts:[]).map(a=>({...a,key:a.key||cur.find(x=>x.id===a.id)?.key||''}));
  cur.forEach(x=>{ if(!acc.some(a=>a.id===x.id)) acc.push(x); }); d.settings.accounts=acc;
  localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(d)); load(); checkResets(); save(); applyTheme(); render();
}

/* =====================================================================
 *  시작
 * ===================================================================== */
$('#jobList').innerHTML=JOBS.map(j=>`<option value="${j}">`).join('');
$('#worldList').innerHTML=WORLDS.map(j=>`<option value="${j}">`).join('');
load();
if(!S.activeId && S.characters[0]) S.activeId=S.characters[0].id;
checkResets(); loadOfficialPrices(); save(); applyTheme(); render();
/* 페이지를 열거나 새로고침할 때마다 넥슨 API 동기화 1회 (2026-10-10 사용자 요청) — 🔄 버튼과 같은 syncAll(넥슨 API 전용, 구글 드라이브·로그인 창과 무관).
 * 새로고침을 연달아 해도 API 호출량을 아끼도록: 마지막 동기화(완료) 또는 마지막 '열 때 동기화' 시작이 LOAD_SYNC_GAP_MS(3초, 사용자 결정) 안이면 건너뜀.
 * 시작 시각을 따로 저장(LOAD_SYNC_KEY)하는 이유: 동기화 도중 새로고침하면 lastSync 가 안 바뀌어 매번 다시 시작되기 때문. */
function loadSyncDue(){ if(!hasApi()||!S.characters.length) return false;
  const last=Math.max(+S.settings.lastSync||0, +localStorage.getItem(LOAD_SYNC_KEY)||0); return Date.now()-last>=LOAD_SYNC_GAP_MS; }
if(loadSyncDue() || (hasApi() && S.characters.some(c=>c.ocid&&!c.accId))){ try{ localStorage.setItem(LOAD_SYNC_KEY,String(Date.now())); }catch(e){} syncAll({silent:true}); } // + 기존 데이터: 계정 자동 배정
setInterval(()=>{ if(checkResets()) render(); else renderResetInfo(); if(!document.hidden) tabTick(); if(!document.hidden) gdPull(); }, 60e3);
document.addEventListener('visibilitychange',()=>{ if(document.hidden){ if(gd.timer||gdLocalDirty()) gdPush({quick:true}); return; } if(checkResets()) render(); tabTick(); gdPull(); }); // (예전: 15분 지났으면 자동 동기화 — 2026-10-10 제거)
window.addEventListener('pagehide',()=>{ if(gd.timer||gdLocalDirty()) gdPush({quick:true}); });
/* =====================================================================
 *  소식 피드 (왼쪽 아래 카드)
 *  GitHub Actions(update-feed.yml, 5분마다)가 feed.json 을 갱신 → 사이트는 그 파일만 읽음.
 *  API 키·외부 요청 없음. 읽음 표시는 이 브라우저 localStorage(mapleBossTracker.feedSeen).
 * ===================================================================== */
const FEED_TABS=[['saryo','사료감지'],['patch','패치내역'],['test','테섭'],['mabbak','마빡도로시']];
const FEED_LIVE='https://ggoolzip-wq.github.io/feed.json', FEED_SEEN_KEY='mapleBossTracker.feedSeen', FEED_ROW=31, FEED_MOBILE_ROWS=6;
const feed={data:null,err:'',tab:'saryo',page:1,per:5,at:0};
let feedSeen=new Set((()=>{ try{ return JSON.parse(localStorage.getItem(FEED_SEEN_KEY))||[]; }catch(e){ return []; } })());
const feedItems=t=>((feed.data&&feed.data.items&&feed.data.items[t])||[]);
const feedUnseen=t=>feedItems(t).filter(x=>!feedSeen.has(x.id)).length;
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
    const isNew=!feedSeen.has(x.id), exp=x.end&&Date.parse(x.end)<now;
    const tip=`${x.title}\n${fdFull(x.date)}${x.end?`\n수령 기한 ~${fdFull(x.end)}${exp?' (종료)':''}`:''}`;
    return `<li><a class="fit${exp?' exp':''}" href="${esc(x.url)}" target="_blank" rel="noopener noreferrer" data-fid="${esc(x.id)}" title="${esc(tip)}">${isNew?'<span class="fnew">N</span>':''}<span class="ftt">${esc(x.title)}</span>${x.end?`<span class="fend">~${esc(fdShort(x.end))}</span>`:''}<span class="fdt">${esc(fdShort(x.date))}</span></a></li>`; }).join('');
  const body=feed.err?`<div class="fempty">${esc(feed.err)}</div>`:!feed.data?`<div class="fempty">불러오는 중…</div>`:items.length?`<ul class="flist">${rows}</ul>`:`<div class="fempty">아직 소식이 없습니다</div>`;
  let pager='';
  if(pages>1){ let s=Math.max(1,feed.page-2), e=Math.min(pages,s+4); s=Math.max(1,e-4);
    const nums=[]; for(let i=s;i<=e;i++) nums.push(`<button type="button" class="fpg${i===feed.page?' on':''}" data-fpage="${i}"${i===feed.page?' aria-current="page"':''}>${i}</button>`);
    const more=pages>5;
    pager=(more?`<button type="button" class="fpg fnav" data-fpage="${feed.page-1}"${feed.page<=1?' disabled':''} aria-label="이전">‹</button>`:'')+nums.join('')+(more?`<button type="button" class="fpg fnav" data-fpage="${feed.page+1}"${feed.page>=pages?' disabled':''} aria-label="다음">›</button>`:''); }
  c.innerHTML=`<div class="ftabs" role="tablist">${tabs}</div>${note}<div class="fbody">${body}</div><div class="fpager">${pager}</div>`;
  const sc=$('#sunCard'), sid=JSON.stringify(feed.data&&feed.data.sunday||null);
  if(sc&&(!sc.innerHTML||sc.dataset.sid!==sid||sc.dataset.loaded!==String(!!feed.data))){ renderSun(); sc.dataset.loaded=String(!!feed.data); }
}
/* 썬데이 메이플 카드 (feed.json 의 sunday) — 클릭하면 이벤트 글 */
const SUN_SVG='<svg class="sunico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.6" fill="currentColor"/><g stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 2.2v2.6M12 19.2v2.6M2.2 12h2.6M19.2 12h2.6M5.1 5.1l1.8 1.8M17.1 17.1l1.8 1.8M5.1 18.9l1.8-1.8M17.1 6.9l1.8-1.8"/></g></svg>';
const sunCropUrl=s=>s&&s.crop?(location.protocol==='file:'?FEED_LIVE.replace(/feed\.json$/,''):'./')+s.crop:'';
function renderSun(){
  const c=$('#sunCard'); if(!c) return;
  const s=feed.data&&feed.data.sunday;
  let body;
  const src=s&&(sunCropUrl(s)||s.image);
  if(s&&src){
    const when=s.start?fdShort(s.start)+(s.end&&fdShort(s.end)!==fdShort(s.start)?' ~ '+fdShort(s.end):''):fdShort(s.date||'');
    const bens=(s.benefit?String(s.benefit).split(/\s*·\s*/).filter(Boolean):[]).slice(0,3);
    const lines=bens.length?bens:[s.title||'썬데이 메이플'];
    body=`<button type="button" class="sunimg" data-sunopen title="크게 보기"><img src="${esc(src)}" alt="${esc(s.title||'썬데이 메이플')}" loading="lazy" referrerpolicy="no-referrer"></button>`+
      `<div class="suncap"><span class="ftt">${esc(s.title||'썬데이 메이플')}</span><span class="fdt">${esc(when)}</span></div>`+
      `<div class="sunben"><b>이번 주 혜택</b><ul>${lines.map(t=>`<li title="${esc(t)}">${esc(t)}</li>`).join('')}</ul></div>`;
  }else body=`<div class="sunempty">${SUN_SVG}<span>${feed.data||feed.err?'아직 썬데이 메이플 소식이 없어요':'불러오는 중…'}</span></div>`;
  c.innerHTML=`<div class="ftabs"><span class="ftab on stab" role="heading" aria-level="2">${SUN_SVG}썬데이</span></div><div class="sunbody">${body}</div>`;
  c.dataset.sid=JSON.stringify(s||null);
}
/* 썬데이 이미지 크게 보기 (라이트박스): 바깥 클릭·✕·Esc 로 닫기, 이미지를 누르면 원본 폭으로 확대(스크롤) */
let sunLbPrev=null;
function sunLightbox(){
  const s=feed.data&&feed.data.sunday; if(!s) return;
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
    const minH=FEED_ROW*2+70, SUN_MIN=140, gap=12;
    // 남은 높이를 소식 1/3 : 썬데이 2/3 로 나눔. 썬데이 칸이 너무 작아지면(SUN_MIN 미만) 썬데이를 숨기고 소식이 전부 사용
    let fh=Math.max(minH,Math.round((h-gap)/3)), sh=h-gap-fh;
    if(sun){ if(sh>=SUN_MIN){ sun.style.display=''; sun.style.height=sh+'px'; sun.classList.toggle('tight',sh<230); } else { sun.style.display='none'; fh=h; } }
    c.style.height=Math.max(minH,fh)+'px';
    const fb=c.querySelector('.fbody'); const avail=fb?fb.clientHeight:0;
    feed.per=Math.min(20,Math.max(2,Math.floor(avail/FEED_ROW)));
    if(feed.per!==old){ const first=(feed.page-1)*old; feed.page=Math.floor(first/feed.per)+1; old=feed.per; renderFeed(); }
    // 최소 높이에서 내용(머리글·2줄·쪽 번호)이 넘치면 넘친 만큼 소식 카드를 키우고 썬데이 카드에서 뺌 (모자라면 썬데이 숨김)
    const fb2=c.querySelector('.fbody'), over=Math.max(c.scrollHeight-c.clientHeight, fb2?fb2.scrollHeight-fb2.clientHeight:0);
    if(over>0){ const nh=c.offsetHeight+over; c.style.height=nh+'px';
      if(sun&&sun.style.display!=='none'){ const s2=h-gap-nh; if(s2>=SUN_MIN){ sun.style.height=s2+'px'; sun.classList.toggle('tight',s2<230); } else { sun.style.display='none'; c.style.height=Math.max(nh,h)+'px'; } } }
  }
  if(feed.per!==old){ const first=(feed.page-1)*old; feed.page=Math.floor(first/feed.per)+1; renderFeed(); }
}
$('#feedCard').addEventListener('click',e=>{
  const tb=e.target.closest('[data-ftab]'); if(tb){ feed.tab=tb.dataset.ftab; feed.page=1; renderFeed(); feedFit(); return; }
  const pg=e.target.closest('[data-fpage]'); if(pg&&!pg.disabled){ feed.page=+pg.dataset.fpage; renderFeed(); return; }
  const a=e.target.closest('a[data-fid]'); if(a&&!feedSeen.has(a.dataset.fid)){ feedSeen.add(a.dataset.fid); feedSaveSeen(); setTimeout(renderFeed,0); }
});
$('#feedCard').addEventListener('auxclick',e=>{ const a=e.target.closest('a[data-fid]'); if(a&&e.button===1&&!feedSeen.has(a.dataset.fid)){ feedSeen.add(a.dataset.fid); feedSaveSeen(); setTimeout(renderFeed,0); } });
renderFeed(); feedFit();
addEventListener('resize',feedFit);
if(window.ResizeObserver){ const ro=new ResizeObserver(()=>feedFit()); document.querySelectorAll('.side-sticky>.card:not(#feedCard):not(#sunCard), .foot, header, #view').forEach(el=>ro.observe(el)); }
feedLoad().then(feedFit);
setInterval(()=>{ if(!document.hidden) feedLoad(); },3e5);
document.addEventListener('visibilitychange',()=>{ if(!document.hidden&&Date.now()-feed.at>3e5) feedLoad(); });
gdRender(); svGate();
if(SV_ON){ if(gdMeta.on&&svTok()) gdConnect(false); else gdRender(); } // 서버 모드: 남은 세션 토큰으로만 (없으면 ☁ 로그인)
else if(gdUsable()){ gdLoadLib().catch(()=>{}); if(gdMeta.on) gdConnect(false); }
