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
  API_DELAY_MS: 250,               // 호출 간 간격 (개발 단계 키: 초당 5건 제한)
  AUTO_SYNC_MIN: 15                // 자동 동기화 주기(분)
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
  // 특수 스킬 반지 상자 (낮은 확률) — 녹옥(1~3Lv) · 홍옥(1~4Lv) · 흑옥(1~4Lv) · 백옥(3~4Lv) · 생명(3~4Lv, 생명의 연마석 포함)
  r_green:{n:'녹옥의 보스 반지 상자',s:'녹옥 반지 상자',set:'반지',note:'1~3레벨 특수 스킬 반지'},
  r_red:{n:'홍옥의 보스 반지 상자',s:'홍옥 반지 상자',set:'반지',note:'1~4레벨 특수 스킬 반지'},
  r_black:{n:'흑옥의 보스 반지 상자',s:'흑옥 반지 상자',set:'반지',note:'1~4레벨 특수 스킬 반지'},
  r_white:{n:'백옥의 보스 반지 상자',s:'백옥 반지 상자',set:'반지',note:'3~4레벨 특수 스킬 반지'},
  r_life:{n:'생명의 보스 반지 상자',s:'생명 반지 상자',set:'반지',note:'3~4레벨 특수 스킬 반지 또는 생명의 연마석'}
};
// 보스별 반지 상자 (정심심 블로그 2026-09-04 정리 · 나무위키 '특수 스킬 반지' · maple.ai.kr 보스 보상과 대조)
const RING_DROPS = {
  r_green:{lotus:['normal'],damien:['normal'],slime:['normal'],lucid:['easy','normal'],will:['easy','normal'],dusk:['normal'],dunkel:['normal']},
  r_red:{lotus:['hard'],damien:['hard'],lucid:['hard'],will:['hard'],jinhilla:['normal']},
  r_black:{dusk:['chaos'],dunkel:['hard'],slime:['chaos'],jinhilla:['hard'],seren:['normal']},
  r_white:{lotus:['extreme'],blackmage:['hard','extreme'],seren:['hard','extreme'],kalos:['easy','normal'],kaling:['easy','normal'],adversary:['easy','normal'],star:['normal'],bellona:['easy','normal']},
  r_life:{kalos:['chaos','extreme'],kaling:['hard','extreme'],limbo:['normal','hard'],baldrix:['normal','hard'],adversary:['hard','extreme'],star:['hard'],jupiter:['normal','hard'],bellona:['hard']}
};
const SET_LABEL = {'반지':'특수 스킬 반지 상자 (낮은 확률)','광휘':'광휘의 보스 세트','칠흑':'칠흑의 보스 세트','여명':'여명의 보스 세트','보장':'보스 장신구 세트','해머':'익셉셔널 강화 재료'};
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
  kalos:[['h_eye',['extreme']]],
  adversary:[['legacy',['hard','extreme']]],
  kaling:[['chaosbox',['normal','hard','extreme']],['h_ear',['extreme']]],
  star:[['bliss',['hard']],['chaosbox',['normal','hard']]],
  limbo:[['whisper',['hard']],['chaosbox',['normal','hard']]],
  baldrix:[['oath',['hard']],['chaosbox',['normal','hard']]],
  bellona:[['spirit',['hard']],['chaosbox',['normal','hard']]],
  jupiter:[['sin',['hard']],['chaosbox',['normal','hard']]],
  blackmage:[['genesis',['hard','extreme']],['h_belt',['extreme']]]
};
const dropsFor = (b,diff) => [...(DROPS[b.id]||[]).filter(([,ds])=>ds.includes(diff)).map(([k])=>k),
  ...Object.entries(RING_DROPS).filter(([,m])=>(m[b.id]||[]).includes(diff)).map(([k])=>k)];
const DROP_MAX = 3; // 한 줄 유지: 넘치면 +N
function itemIcon(k){
  const it=ITEMS[k], src=ITEM_ICONS[k];
  return src?`<img src="${src}" alt="" aria-hidden="true">`:`<span class="ifb" aria-hidden="true">${esc((it?.n||'?').slice(0,1))}</span>`;
}
const dropOpen=new Set(); // '+N'을 눌러 펼친 보스 행
function dropsHtml(b,diff,c){
  const ks=dropsFor(b,diff); if(!ks.length) return '';
  const tip=k=>{const it=ITEMS[k]; return `${it.n} — ${SET_LABEL[it.set]}${it.note?' · '+it.note:''} (${D[diff]})`;};
  const cnt=k=>c?dropCount(c,b,k):0;
  const chip=k=>{const it=ITEMS[k], n=cnt(k);
    return `<span class="drop s-${it.set} ${n?'got':''}" ${c?`data-drop="${b.id}|${k}" role="button" tabindex="0"`:''} title="${esc(tip(k))}${c?`\n클릭: 획득 +1${n?' · 우클릭/−: 가장 최근 1개 취소':''}`:''}">${itemIcon(k)}<span class="dn">${esc(it.s||it.n)}</span>${n?`<b class="dcnt">×${n}</b><span class="ddec" data-dropdec="${b.id}|${k}" role="button" aria-label="1개 취소" title="1개 취소">−</span>`:''}</span>`;};
  const open=c&&dropOpen.has(b.id);
  const shown=(!open&&ks.length>DROP_MAX)?ks.slice(0,DROP_MAX-1):ks, rest=ks.slice(shown.length);
  const restGot=rest.reduce((s,k)=>s+cnt(k),0);
  // 아래 줄: 이 보스에서 획득한 아이템 (모든 화면과 같은 형식: 이름(N인 분배) ×개수 결과)
  const mine=c?(d=>({items:Object.fromEntries(Object.entries(d.items).filter(([k])=>k.split('|')[0]===b.id)),outcomes:d.outcomes}))(charDrops(c,b.type)):null;
  const ringLine=mine?itemsInline(mine.items,{outs:mine.outcomes}):'';
  return `<div class="drops ${open?'open':''}" aria-label="주요 희귀 드롭">${shown.map(chip).join('')}${rest.length?`<span class="drop more ${restGot?'got':''}" ${c?`data-dropmore="${b.id}" role="button"`:''} title="${esc(rest.map(tip).join('\n'))}">${rest.map(k=>itemIcon(k)).join('')}<span class="dn">+${rest.length}</span>${restGot?`<b class="dcnt">×${restGot}</b>`:''}</span>`:''}${open&&ks.length>DROP_MAX?`<span class="drop more" data-dropmore="${b.id}" role="button" title="접기"><span class="dn">접기</span></span>`:''}</div>${ringLine?`<div class="ringouts">${ringLine}</div>`:''}`;
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
    prices:{}, accounts:[], autoSync:true, autoEnable:true, lastSync:0};
}
function defaultState(){
  return {version:5, theme:null, activeId:null, characters:[], worldOrder:[], history:[], monthHistory:[], startWeek:weekId(), settings:defaultSettings(),
    period:{week:weekId(), day:dayId(), month:monthId()}};
}
/* character: {id,name,job,level,world,ocid,image,isMain, bosses:{slot:{enabled,diff,party}},
 *   weekly:{slot:true}, monthly:{slot:weekId}, auto:{slot:true}, sync:{at,ok,msg,clear,limit,unmatched,imgAt}} */
let S;
function load(){
  try{ const raw=localStorage.getItem(CONFIG.STORAGE_KEY); S = raw?Object.assign(defaultState(),JSON.parse(raw)):defaultState(); }
  catch(e){ console.warn(e); S=defaultState(); }
  S.settings=Object.assign(defaultSettings(),S.settings||{});
  migrate();
  S.settings.prices={}; delete S.settings.priceSource; // 가격 수동 수정 기능 제거: 가격은 공식 prices.json 자동 갱신 값만 사용
  delete S.settings.driveKeys; // 예전 '키도 드라이브에 저장' 선택 항목 (이제 항상 저장)
  delete S.settings.apiMode;
  // ↑ 예전 연결 방식(로컬 프록시) 설정 — 이제 항상 open.api.nexon.com 직접 호출
  S.settings.weeklyLimit=CONFIG.WEEKLY_BOSS_LIMIT; S.settings.monthlyLimit=CONFIG.MONTHLY_BOSS_LIMIT; // 처치 한도는 고정값 (설정 화면 제거)
  delete S.settings.worldLimit; // 월드 결정석 판매 한도 기능 제거 (수익 = 클리어한 보스 합계, 상한 없음)
  S.characters.forEach(normChar);
  if(typeof S.updatedAt!=='number') S.updatedAt=0;
  lastBody=bodyOf();
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
function normChar(c){ ['bosses','weekly','monthly','auto','sync','drops','mdrops','dropOut','mdropOut'].forEach(k=>c[k]=c[k]||{}); delete c.dropParty; delete c.mdropParty; c.world=c.world||''; }
// updatedAt: 데이터 내용이 실제로 바뀐 시각 (구글 드라이브 동기화에서 어느 쪽이 최신인지 비교)
let lastBody=null;
function bodyOf(){ const u=S.updatedAt; S.updatedAt=0; const b=JSON.stringify(S); S.updatedAt=u; return b; }
function save(){
  const b=bodyOf(), changed=b!==lastBody;
  if(changed){ S.updatedAt=Date.now(); lastBody=b; }
  localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(S));
  if(changed) gdChanged();
}
const price = (b,diff) => { const k=priceKey(b,diff); return (k in S.settings.prices)?S.settings.prices[k]:(PRICE_CONFIG[k]||0); };
const activeChar = () => S.characters.find(c=>c.id===S.activeId);
const uid = () => Math.random().toString(36).slice(2,9)+Date.now().toString(36).slice(-4);
const worldOf = c => c.world || '월드 미지정';

/* ---------- 리셋 처리 ---------- */
function checkResets(){
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
  if(changed){ S.period=now; save(); if(msgs.length) toast(msgs.join(' · ')); }
  return changed;
}

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
    const party=Math.max(1,cfg.party||1), diff=cfg.diff;
    list.push({slot,name:b.name,type:b.type,diff,party,gross:price(b,diff),value:Math.floor(price(b,diff)/party),auto:!!c.auto[slot]});
  }
  list.sort((a,b)=>b.value-a.value);
  let w=0,m=0; list.forEach(x=>{ if(x.type==='weekly'){ x.counted = w < S.settings.weeklyLimit; w++; } else { x.counted = m < S.settings.monthlyLimit; m++; } });
  return list;
}
function charRevenue(c){ const l=charCrystals(c), sum=t=>l.filter(x=>x.type===t&&x.counted).reduce((s,x)=>s+x.value,0);
  return {list:l, wlist:l.filter(x=>x.type==='weekly'), mlist:l.filter(x=>x.type==='monthly'), weekly:weeklyCount(c), meso:sum('weekly'), monthMeso:sum('monthly')}; }
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
const curParty = (c,slot) => Math.max(1, Math.min(6, parseInt(c?.bosses?.[slot]?.party)||1));
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
    if(!b || !diff || !b.diffs.includes(diff)){ unmatched.push(`${r.content_name}(${r.difficulty||'?'})`); continue; }
    if(seen[b.id]) continue;
    const done=isDone(r), reg=flagOn(r.registration_flag);
    const cfg=c.bosses[b.id];
    if(done){
      if((b.type==='weekly'&&staleWeek)||(b.type==='monthly'&&staleMonth)) continue;
      seen[b.id]=true;
      c.bosses[b.id]={enabled:true,diff,party:cfg?.party||1};
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
      try{ total+=applyScheduler(c, await nx('/maplestory/v1/scheduler/character-state',{ocid:c.ocid},a.key)); }
      catch(e){ errs++; const hint=/OPENAPI0000[234]/.test(e.code||'')?` — 스케줄러 조회 불가: '${a.label}' 계정의 캐릭터가 아니거나 2026-06-25 이후 접속 기록이 없을 수 있어요. 수동 체크는 계속 가능합니다.`:''; c.sync=Object.assign(c.sync||{},{at:Date.now(),ok:false,msg:e.message+hint}); }
    }
    S.settings.lastSync=Date.now(); save();
    if(!opts.silent || total || assigned || accMsgs.length) toast(`동기화 완료 — 새로 체크된 보스 ${total}개`+(assigned?` · 계정 자동 연결 ${assigned}명`:'')+(errs?` · 일부 캐릭터 실패 ${errs}`:'')+(accMsgs.length?` · 계정 오류: ${accMsgs.join(', ')}`:''));
  }catch(e){ if(!opts.silent) toast('동기화 실패: '+e.message); save(); }
  finally{ syncing=false; render(); }
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
function render(){ if(!['boss','summary','history','total'].includes(tab)) tab='boss';
  renderChars(); renderHeaderSync(); renderResetInfo(); if($('#importModal').classList.contains('show')) renderAccList();
  ({boss:renderBoss,summary:renderSummary,history:renderHistory,total:renderTotal})[tab](); }
/* 헤더: 🔄 지금 동기화 (API 키가 있을 때만) */
function renderHeaderSync(){
  const b=$('#syncBtn'); if(!b) return; const st=S.settings; b.hidden=!hasApi(); b.disabled=syncing;
  b.classList.toggle('busy',syncing); b.setAttribute('aria-busy',String(syncing));
  b.innerHTML=`<svg class="rot" viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.34-5.66" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M20 4v5h-5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="hl">동기화</span>`;
  b.title=syncing?'동기화 중…':`지금 동기화 (보스 클리어 자동 체크)\n마지막 동기화: ${st.lastSync?hm(st.lastSync)+' KST':'없음'}${st.autoSync?`\n열려 있으면 ${CONFIG.AUTO_SYNC_MIN}분마다 자동`:''}`;
  b.setAttribute('aria-label',`동기화 — 마지막 ${st.lastSync?hm(st.lastSync):'없음'}`);
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
function renderChars(){
  if(dnd) return; // 드래그 중에는 다시 그리지 않음
  const el=$('#charList');
  if(!S.characters.length){ el.innerHTML='<div class="muted" style="padding:8px 2px">아직 캐릭터가 없습니다.<br><b>+ 추가</b> 또는 아래 <b>넥슨 API</b>로 불러오세요.</div>'; return; }
  const groups=worldGroups(); const worlds=[...groups.keys()];
  const multi=worlds.length>1;
  el.innerHTML=worlds.map((w,wi)=>{ const cs=groups.get(w);
    const head = multi||w!=='월드 미지정' ? `<div class="world-h" data-world="${esc(w)}" ${multi?'draggable="true"':''}>
        ${multi?'<span class="drag-h" title="드래그해서 월드 순서 변경">⠿</span>':''}<span style="flex:1">🌐 ${esc(w)} <span style="font-weight:500">(${cs.length})</span></span>
        ${multi?`<button class="ord" data-wmove="${esc(w)}|-1" ${wi===0?'disabled':''} title="월드 위로" aria-label="월드 위로">▲</button><button class="ord" data-wmove="${esc(w)}|1" ${wi===worlds.length-1?'disabled':''} title="월드 아래로" aria-label="월드 아래로">▼</button>`:''}</div>` : '';
    return head + cs.map((c,ci)=>{const r=charRevenue(c);return `
    <div class="char ${c.id===S.activeId?'on':''}${r.weekly>=S.settings.weeklyLimit?' alldone':''}" data-id="${c.id}" data-world="${esc(w)}" draggable="true">
      ${r.weekly>=S.settings.weeklyLimit?`<span class="donestamp" title="이번 주 주간 보스 ${r.weekly}/${S.settings.weeklyLimit} 완료" aria-label="주간 보스 완료">완</span>`:''}
      <span class="drag-h" title="드래그해서 순서 변경">⠿</span>
      ${avatar(c)}
      <div class="grow"><div class="nm">${esc(c.name)}${c.isMain?'<span class="mainbadge">★ 본캐</span>':''}</div><div class="meta lvrow"><span class="lv">Lv.${esc(c.level||'?')}</span><span class="job">${esc(c.job||'직업 미설정')}</span></div>${expLine(c)}</div>
      <div style="text-align:right"><div class="rev">${meso(r.meso)}</div><div class="meta">${r.weekly}/${S.settings.weeklyLimit}${needAssign(c)?' <span class="warnc" title="넥슨 계정 미지정 — ✎ 편집에서 계정을 선택하세요">⚠</span>':c.sync?.ok===false?' <span title="'+esc(c.sync.msg)+'">⚠</span>':''}</div></div>
      <div class="ordcol"><button class="ord" data-move="${c.id}|-1" ${ci===0?'disabled':''} title="위로" aria-label="위로">▲</button><button class="ord" data-move="${c.id}|1" ${ci===cs.length-1?'disabled':''} title="아래로" aria-label="아래로">▼</button></div>
      <button class="btn sm plain" data-edit="${c.id}" title="수정">✎</button>
    </div>`}).join('');}).join('');
}

/* ---------- 드래그 앤 드롭: 데스크톱은 HTML5 DnD, 터치는 Pointer Events (⠿ 손잡이) ---------- */
let dnd=null; // {kind:'char'|'world', id, el}
function dndTarget(el, clientY){
  if(!dnd||!el) return null;
  if(dnd.kind==='char'){
    const t=el.closest('.char[data-id]'); if(!t||t===dnd.el||t.dataset.world!==dnd.el.dataset.world) return null;
    const r=t.getBoundingClientRect(); return {el:t, id:t.dataset.id, after: clientY>r.top+r.height/2};
  }
  const t=el.closest('[data-world]'); if(!t) return null;
  const w=t.dataset.world; if(w===dnd.id) return null;
  const head=document.querySelector(`.world-h[data-world="${CSS.escape(w)}"]`);
  const rows=[...document.querySelectorAll(`.char[data-world="${CSS.escape(w)}"]`)];
  const top=head.getBoundingClientRect().top, bottom=(rows.at(-1)||head).getBoundingClientRect().bottom;
  return {el:head, id:w, after: clientY>(top+bottom)/2};
}
function dndMark(t){
  document.querySelectorAll('.drop-before,.drop-after').forEach(e=>e.classList.remove('drop-before','drop-after'));
  if(t) t.el.classList.add(t.after?'drop-after':'drop-before');
}
function dndStart(kind,id,el){ dnd={kind,id,el}; el.classList.add('dragging'); document.body.classList.add('is-dragging'); }
function dndFinish(t){
  const d=dnd; dnd=null; dndMark(null); document.body.classList.remove('is-dragging');
  if(d) d.el.classList.remove('dragging');
  if(d&&t){ const ok = d.kind==='char' ? moveCharTo(d.id,t.id,t.after) : moveWorldTo(d.id,t.id,t.after); if(ok) toast('순서를 변경했습니다'); }
  renderChars(); if(tab==='summary') renderSummary();
}
const charList=document.getElementById('charList');
charList.addEventListener('dragstart',e=>{
  const row=e.target.closest?.('.char[data-id],.world-h[draggable]'); if(!row){ e.preventDefault(); return; }
  if(row.classList.contains('world-h')) dndStart('world',row.dataset.world,row); else dndStart('char',row.dataset.id,row);
  e.dataTransfer.effectAllowed='move'; try{ e.dataTransfer.setData('text/plain',dnd.id); }catch(_){}
});
charList.addEventListener('dragover',e=>{ const t=dndTarget(e.target,e.clientY); dndMark(t); if(t){ e.preventDefault(); e.dataTransfer.dropEffect='move'; } });
charList.addEventListener('drop',e=>{ e.preventDefault(); dndFinish(dndTarget(e.target,e.clientY)); });
charList.addEventListener('dragend',()=>{ if(dnd) dndFinish(null); });
// 터치(또는 펜): ⠿ 손잡이를 눌러 끌기
charList.addEventListener('pointerdown',e=>{
  if(e.pointerType==='mouse') return; // 마우스는 HTML5 DnD 사용
  const h=e.target.closest('.drag-h'); if(!h) return;
  const row=h.closest('.char[data-id],.world-h'); if(!row) return;
  e.preventDefault();
  if(row.classList.contains('world-h')) dndStart('world',row.dataset.world,row); else dndStart('char',row.dataset.id,row);
  dnd.pointerId=e.pointerId; dnd.last=null;
  try{ h.setPointerCapture(e.pointerId); }catch(_){}
});
document.addEventListener('pointermove',e=>{
  if(!dnd||dnd.pointerId!==e.pointerId) return;
  e.preventDefault();
  const under=document.elementFromPoint(e.clientX,e.clientY);
  dnd.last=dndTarget(under,e.clientY); dndMark(dnd.last);
  if(e.clientY<40) window.scrollBy(0,-12); else if(e.clientY>innerHeight-40) window.scrollBy(0,12);
},{passive:false});
document.addEventListener('pointerup',e=>{ if(dnd&&dnd.pointerId===e.pointerId) dndFinish(dnd.last); });
document.addEventListener('pointercancel',e=>{ if(dnd&&dnd.pointerId===e.pointerId) dndFinish(null); });
function renderResetInfo(){
  const now=Date.now(), nw=weekStartMs(now)+7*864e5;
  const d=kst(now); const nm=Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,1)-KST_MS;
  $('#resetInfo').innerHTML=`<b>초기화까지 (KST)</b><br>주간(목 00:00): ${untilText(nw-now)}<br>월간(1일 00:00): ${untilText(nm-now)}<br><span style="font-size:.78rem">이번 주: ${fmtWeek(S.period.week)}</span>`;
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
      : sy.at ? `<span class="pill api">API</span> <span class="muted">게임 내 주간 보스 처치 <b>${sy.clear??'?'} / ${sy.limit||lim}</b> · ${hm(sy.at)} KST 동기화${sy.unmatched?.length?` · 매칭 안 된 보스: ${esc(sy.unmatched.join(', '))}`:''}</span>` : '<span class="muted">API 연결 캐릭터 — 아직 동기화 전</span>')
    : '<span class="muted">수동 캐릭터 (API 미연결)</span>';
  v.innerHTML=`<div class="bosslay"><div class="grid">
   <div class="card">
    <div style="display:flex;gap:12px;align-items:center;margin-bottom:10px">${avatar(c,'lg')}
      <div style="flex:1;min-width:0"><h2 style="margin:0">${esc(c.name)}${c.isMain?'<span class="mainbadge">★ 본캐</span>':''}</h2>
      <div class="muted">Lv.${esc(c.level||'?')} · ${esc(c.job||'')} · ${esc(worldOf(c))}</div><div style="margin-top:4px;font-size:.85rem">${syncLine}</div></div></div>
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
   </div></div><div class="rcol">${revPanel(a,c)}${priceCard()}</div></div>`;
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
  const diff=cfg.diff||b.diffs[0]; const done=isDone(c,b); const party=cfg.party||1;
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
    <div class="party">파티 <select data-party="${slot}">${Array.from({length:CONFIG.MAX_PARTY},(_,i)=>`<option ${party===i+1?'selected':''}>${i+1}</option>`).join('')}</select>인</div>
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
  $('#accOpts').innerHTML=accounts().length?`<label class="checkline"><input type="checkbox" id="sAuto" ${S.settings.autoSync?'checked':''}> 열려 있으면 ${CONFIG.AUTO_SYNC_MIN}분마다 자동 동기화</label>
    <label class="checkline"><input type="checkbox" id="sAutoEnable" ${S.settings.autoEnable?'checked':''}> 인게임 스케줄러에 등록된 보스를 자동으로 선택 목록에 추가</label>`:'';
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
 *  구글 드라이브 동기화 — Google Identity Services(토큰 모델) + Drive REST v3, 범위 drive.appdata
 *  (내 드라이브의 숨겨진 '앱 데이터' 폴더에 maple-boss-tracker.json 하나만 저장. 다른 파일은 보거나 건드리지 않음)
 * ===================================================================== */
const GD={ SCOPE:'https://www.googleapis.com/auth/drive.appdata', FILE:'maple-boss-tracker.json',
  META_KEY:'mapleBossTracker.gdrive', TOKEN_KEY:'mapleBossTracker.gtoken',
  API:'https://www.googleapis.com/drive/v3', UP:'https://www.googleapis.com/upload/drive/v3',
  ONLINE:'https://ggoolzip-wq.github.io/', DEBOUNCE:5000 };
const gcid=()=>GOOGLE_CLIENT_ID||window.__MBT_GCID||'';
const gdOriginOk=()=>location.protocol==='https:'||/^(localhost|127\.0\.0\.1)$/.test(location.hostname);
const gdUsable=()=>!!gcid()&&gdOriginOk();
let gd={state:'off',msg:'',token:null,exp:0,fileId:null,timer:null,busy:false,again:false,client:null,onTok:null,onErr:null,pending:null};
let gdMeta=(()=>{ try{ return JSON.parse(localStorage.getItem(GD.META_KEY))||{}; }catch(e){ return {}; } })(); // {on, base, fileId, lastSave, lastLoad}
const gdSaveMeta=()=>localStorage.setItem(GD.META_KEY,JSON.stringify(gdMeta));
try{ const t=JSON.parse(sessionStorage.getItem(GD.TOKEN_KEY)||'null'); if(t&&t.e>Date.now()+60e3){ gd.token=t.t; gd.exp=t.e; } }catch(e){}
const gdLocalDirty=()=>gdMeta.on && (S.updatedAt||0)!==(gdMeta.base||0);
const gdTime=t=>t?`${hm(t)}`:'없음';

function gdSet(state,msg){ gd.state=state; gd.msg=msg||''; gdRender(); }
function gdRender(){
  const b=$('#gBtn'); if(b){
    const L={off:'☁ 구글 로그인',connecting:'☁ 연결 중…',saving:'☁ 저장 중…',reconnect:'☁ 다시 연결',conflict:'☁ 선택 필요',error:'☁ 동기화 오류',
      on: gd.timer||gdLocalDirty() ? '☁ 저장 대기' : (gdMeta.lastSave||gdMeta.lastLoad ? `☁ ${hm(Math.max(gdMeta.lastSave||0,gdMeta.lastLoad||0)).split(' ')[1]} 저장됨` : '☁ 동기화됨')};
    b.textContent=!gcid()?'☁ 구글':!gdOriginOk()?'☁ 구글 (온라인 전용)':(L[gd.state]||'☁ 구글'); b.classList.toggle('warn',['reconnect','conflict','error'].includes(gd.state));
    b.title=gd.msg||'구글 드라이브 동기화';
  }
  const st=$('#gdStatus'); if(st) st.innerHTML=gdStatusHtml();
}
function gdStatusHtml(){
  const on=gdMeta.on&&gd.state!=='off';
  const head={off:'로그인하지 않음',connecting:'연결 중…',saving:'저장 중…',on:gdLocalDirty()||gd.timer?'변경 사항 저장 대기 (약 5초 후 자동 저장)':'✓ 동기화됨',
    reconnect:'다시 연결 필요',conflict:'어느 데이터를 쓸지 선택이 필요합니다',error:'오류'}[gd.state];
  return `<div class="gdline"><b>${head}</b>${gd.msg?` <span class="muted">— ${esc(gd.msg)}</span>`:''}</div>
    <div class="muted" style="font-size:.8rem">마지막 저장: ${gdTime(gdMeta.lastSave)} · 마지막 불러오기: ${gdTime(gdMeta.lastLoad)}</div>
    <div class="toolbar" style="margin-top:8px">${['reconnect','error'].includes(gd.state)?'<button class="btn sm" id="gdLogin">다시 연결</button>':''}${on
      ? `${['reconnect','error'].includes(gd.state)?'':'<button class="btn sm" id="gdSaveNow">지금 저장</button>'}<button class="btn sm ghost" id="gdLogout">로그아웃</button>`
      : `<button class="btn sm" id="gdLogin">구글 로그인</button>`}
      ${gd.state==='conflict'?'<button class="btn sm" id="gBtn2" onclick="gdAsk(gd.pending)">선택하기</button>':''}</div>`;
}
/* 헤더 ☁ 버튼의 작은 드롭다운: 드라이브 동기화 상태 · 로그인/로그아웃 */
function gdMenuHtml(){
  let inner;
  if(!gcid()) inner=`<div class="impmsg warn"><b>구글 연결 준비 중</b><div>나머지 기능은 모두 정상 동작합니다.</div></div>`;
  else if(!gdOriginOk()) inner=`<div class="impmsg warn"><b>구글 동기화는 온라인 주소에서만 됩니다</b><div>파일(file://)로 연 페이지에서는 구글 로그인이 되지 않습니다. 온라인 주소 <a href="${GD.ONLINE}" target="_blank" rel="noopener">${GD.ONLINE}</a> 에서 사용하세요.</div></div>`;
  else inner=`<div id="gdStatus">${gdStatusHtml()}</div>
    <p class="muted tiny">🔑 API 키도 함께 저장돼요 (내 드라이브 앱 전용 숨김 폴더). 변경 후 약 5초 뒤·창을 닫을 때 자동 저장.</p>`;
  return `<div class="gm-h"><b>☁️ 구글 드라이브 동기화</b><button class="ringx" id="gMenuClose" aria-label="닫기">✕</button></div>${inner}`;
}
function gdMenu(open){
  const m=$('#gMenu'); if(!m) return; const show=open??m.hidden;
  if(show) m.innerHTML=gdMenuHtml();
  m.hidden=!show; $('#gBtn').setAttribute('aria-expanded',String(show));
}
function gdHeaderClick(){ if(gd.state==='conflict'&&gd.pending){ gdMenu(false); return gdAsk(gd.pending); } gdMenu(); }
function gdLoadLib(){
  return new Promise((res,rej)=>{
    if(window.google?.accounts?.oauth2) return res();
    let sc=document.getElementById('gsiScript');
    if(!sc){ sc=document.createElement('script'); sc.id='gsiScript'; sc.src='https://accounts.google.com/gsi/client'; sc.async=true; document.head.appendChild(sc); }
    sc.addEventListener('load',()=>res()); sc.addEventListener('error',()=>{ sc.remove(); rej(new Error('구글 로그인 스크립트를 불러오지 못했습니다 (인터넷 연결이나 광고 차단 확장 프로그램 확인)')); });
  });
}
async function gdToken(){
  if(gd.token && Date.now()<gd.exp-60e3) return gd.token;
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
async function gdFetch(url,opt={},retry=true){
  const tok=await gdToken();
  const r=await fetch(url,{...opt,headers:{...(opt.headers||{}),Authorization:'Bearer '+tok}});
  if(r.status===401&&retry){ gd.token=null; sessionStorage.removeItem(GD.TOKEN_KEY); return gdFetch(url,opt,false); }
  if(!r.ok){ let m=''; try{ m=(await r.json()).error?.message||''; }catch(e){}
    throw Object.assign(new Error(`드라이브 오류 (HTTP ${r.status})${m?' — '+m:''}`),{status:r.status}); }
  return r;
}
async function gdFind(){
  const q=encodeURIComponent(`name='${GD.FILE}' and trashed=false`);
  const r=await gdFetch(`${GD.API}/files?spaces=appDataFolder&q=${q}&orderBy=modifiedTime%20desc&pageSize=10&fields=files(id,modifiedTime,appProperties)`);
  return ((await r.json()).files||[])[0]||null;
}
async function gdRead(id){ return (await gdFetch(`${GD.API}/files/${id}?alt=media`)).json(); }
function gdPayload(){ return {app:'maple-boss-tracker',format:1,savedAt:Date.now(),updatedAt:S.updatedAt||0,characters:S.characters.length,withKeys:true,data:backupData(true)}; }
async function gdWrite(keepalive){
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
  gdMeta.fileId=gd.fileId; gdMeta.base=S.updatedAt||0; gdMeta.lastSave=Date.now(); gdSaveMeta();
}
// 비교용: 키·자동 동기화 시각 등 기기마다 다른 값은 빼고 비교
const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().filter(k=>v[k]!==undefined).map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
function gdNorm(d){ const x=JSON.parse(JSON.stringify(d||{})); delete x.updatedAt; delete x.period; x.settings=x.settings||{};
  x.settings.accounts=(x.settings.accounts||[]).map(a=>({id:a.id,label:a.label})); delete x.settings.lastSync; delete x.settings.apiKey; delete x.settings.driveKeys; delete x.theme; return stable(x); }
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
    gdSet('reconnect',info?info.short:(e.message||'')+' — 상단의 [☁ 다시 연결]을 한 번 눌러 주세요');
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
  gdSet('connecting', interactive?'구글 로그인 창에서 계정을 선택하고 허용해 주세요 ("확인하지 않은 앱" 화면이면 [계속])':'드라이브 확인 중…');
  let slow=null; if(!interactive && !gd.token) slow=setTimeout(()=>{ if(gd.state==='connecting') gdSet('reconnect','상단의 [☁ 다시 연결]을 한 번 눌러 주세요'); },15000);
  try{
    await gdToken(); clearTimeout(slow);
    gdSet('connecting','드라이브 확인 중…');
    gdMeta.on=true; gdSaveMeta();
    const f=await gdFind(); gd.fileId=f?.id||null;
    if(!f){ if(gdLocalEmpty()){ gdSet('on','드라이브에 아직 데이터가 없습니다. 캐릭터를 추가하면 자동 저장됩니다'); return; }
      await gdWrite(); gdSet('on','이 PC 데이터를 드라이브에 처음 저장했습니다'); return; }
    const remote=await gdRead(f.id);
    if(!remote?.data || !Array.isArray(remote.data.characters)) throw new Error('드라이브 파일 형식이 올바르지 않습니다');
    const rU=+remote.updatedAt||0, lU=S.updatedAt||0, base=gdMeta.base||0;
    if(gdLocalEmpty()) return gdApply(remote,'드라이브 데이터를 불러왔습니다');
    if((base && rU===base && lU===base) || gdNorm(remote.data)===gdNorm(backupData(false))){ gdMeta.base=lU; gdMeta.lastLoad=Date.now(); gdSaveMeta();
      const kd=gdKeyDiff(remote.data); if(kd.pulled) save(); // 드라이브에만 있는 키 → 이 PC로 (save 가 자동 저장도 예약)
      if(kd.push || rU!==lU || !remote.withKeys) await gdWrite(); gdSet('on'); return; }
    if(base && rU===base && lU!==base){ await gdWrite(); gdSet('on','이 PC의 변경 사항을 드라이브에 저장했습니다'); return; }
    if(base && lU===base && rU!==base) return gdApply(remote,'다른 PC에서 바뀐 데이터를 불러왔습니다');
    gdAsk(remote);
  }catch(e){ clearTimeout(slow); gdFail(e,interactive); }
}
function gdApply(remote,msg){
  const d=remote.data; d.updatedAt=+remote.updatedAt||Date.now();
  applyData(d); // load() 로 updatedAt 이 드라이브 값 그대로 유지됨 (드라이브의 API 키도 함께 복원)
  gdMeta.base=S.updatedAt; gdMeta.lastLoad=Date.now(); gdSaveMeta();
  if(gdKeyDiff(d).push || !remote.withKeys) gdPush(); // 이 PC에만 있던 키를 드라이브에도 저장
  gdSet('on',msg); toast('☁ '+msg);
}
function gdAsk(remote){
  if(!remote) return; gd.pending=remote; gdSet('conflict');
  const rU=+remote.updatedAt||0, lU=S.updatedAt||0, d=remote.data;
  const card=(t,ic,u,chars,weeks,newer,id,btn)=>`<div class="gdside ${newer?'newer':''}"><div class="gdt">${ic} ${t} ${newer?'<span class="pill">최근 수정</span>':''}</div>
    <div>마지막 수정: <b>${u?hm(u):'알 수 없음'}</b></div><div>캐릭터 <b>${chars}</b>명 · 주간 기록 ${weeks}주</div>
    <button class="btn ${newer?'':'ghost'}" id="${id}">${btn}</button></div>`;
  $('#gdTitle').textContent='☁️ 어느 데이터를 쓸까요?';
  $('#gdBody').innerHTML=`<p class="muted" style="margin-top:0">구글 드라이브와 이 PC의 데이터가 서로 다릅니다. 어느 쪽을 쓸지 한 번만 골라 주세요. 고르지 않은 쪽은 덮어써집니다.</p>
    <div class="gdsides">${card('구글 드라이브','☁️',rU,d.characters.length,(d.history||[]).length,rU>lU,'gdUseDrive','드라이브 데이터 불러오기')}
    ${card('이 PC','💻',lU,S.characters.length,(S.history||[]).length,lU>=rU,'gdUseLocal','이 PC 데이터로 덮어쓰기')}</div>`;
  $('#driveModal').classList.add('show');
}
async function gdResolve(which){
  const remote=gd.pending; $('#driveModal').classList.remove('show'); if(!remote) return; gd.pending=null;
  try{
    if(which==='drive') gdApply(remote,'드라이브 데이터를 불러왔습니다');
    else { gdSet('saving'); if(!gd.fileId) gd.fileId=(await gdFind())?.id||null; await gdWrite(); gdSet('on','이 PC 데이터로 드라이브를 덮어썼습니다'); toast('☁ 이 PC 데이터로 드라이브를 덮어썼습니다'); }
  }catch(e){ gdFail(e); }
}
function gdChanged(){
  if(!gdMeta.on||!gdUsable()||gd.state==='conflict') return;
  clearTimeout(gd.timer); gd.timer=setTimeout(()=>{ gd.timer=null; gdPush(); },GD.DEBOUNCE); gdRender();
}
async function gdPush(opts={}){
  clearTimeout(gd.timer); gd.timer=null;
  if(!gdMeta.on||!gdUsable()||gd.state==='conflict') return false;
  if(opts.quick && !(gd.token&&Date.now()<gd.exp-60e3)) return false; // 창을 닫는 중에는 로그인 창을 띄울 수 없음
  if(gd.busy){ gd.again=true; return false; }
  gd.busy=true; gdSet('saving');
  try{
    if(!opts.quick){
      if(!gd.fileId) gd.fileId=(await gdFind())?.id||null;
      else{ // 다른 PC에서 그 사이 저장했는지 확인 (덮어쓰기 방지)
        try{ const m=await (await gdFetch(`${GD.API}/files/${gd.fileId}?fields=id,appProperties`)).json();
          const rU=+(m.appProperties?.updatedAt||0);
          if(gdMeta.base && rU && rU!==gdMeta.base && rU!==(S.updatedAt||0)){ gd.busy=false; gdAsk(await gdRead(gd.fileId)); return false; }
        }catch(e){ if(e.status===404) gd.fileId=null; else throw e; }
      }
    }
    await gdWrite(opts.quick); gdSet('on'); return true;
  }catch(e){ gdFail(e); return false; }
  finally{ gd.busy=false; if(gd.again){ gd.again=false; gdChanged(); } }
}
function gdLogin(){ $('#driveModal').classList.remove('show'); gdConnect(true); }
async function gdLogout(){ // 로그아웃만 (이 브라우저 데이터는 그대로 둠 — PC방은 종료 시 자동 초기화)
  if(gdMeta.on && gdLocalDirty()){
    const ok=gd.token&&Date.now()<gd.exp-60e3 ? await gdPush() : false;
    if(!ok && !confirm('드라이브에 최신 내용을 저장하지 못했습니다. 그래도 로그아웃할까요? (이 PC에는 그대로 남아 있고, 다음 로그인 때 다시 맞춥니다)')) return;
  }
  try{ if(gd.token&&window.google?.accounts?.oauth2?.revoke) google.accounts.oauth2.revoke(gd.token,()=>{}); }catch(e){}
  clearTimeout(gd.timer); gd.timer=null; gd.token=null; gd.exp=0; gd.fileId=null; sessionStorage.removeItem(GD.TOKEN_KEY);
  gdMeta={}; localStorage.removeItem(GD.META_KEY);
  gdSet('off'); render(); toast('구글 드라이브에서 로그아웃했습니다');
}

/* =====================================================================
 *  이벤트
 * ===================================================================== */
function syncTabs(){ document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('on',b.dataset.tab===tab)); }
document.addEventListener('click',e=>{
  const rc=e.target.closest('[data-ring]'); if(rc){ chooseRing(rc.dataset.ring); return; }
  if(e.target.closest('#ringClose')||e.target.id==='ringModal'){ closeRing(); return; }
  if(e.target.closest('#congrats')){ endCelebrate(); return; }
  const dd=e.target.closest('[data-dropdec]'); if(dd){ e.stopPropagation(); changeDrop(dd.dataset.dropdec,-1); return; }
  const dm=e.target.closest('[data-dropmore]'); if(dm){ const id=dm.dataset.dropmore; dropOpen.has(id)?dropOpen.delete(id):dropOpen.add(id); render(); return; }
  const dc=e.target.closest('[data-drop]'); if(dc){ changeDrop(dc.dataset.drop,+1); return; }
  const t=e.target.closest('[data-tab],[data-move],[data-wmove],[data-id],[data-edit],[data-filter],[data-check],[data-toggle],[data-setdiff],[data-delhist],[data-acctest],[data-accdel],button[id]');
  if(!t) return;
  const c=activeChar();
  if(t.dataset.tab){ tab=t.dataset.tab; syncTabs(); render(); return; }
  if(t.dataset.move){ e.stopPropagation(); const [id,d]=t.dataset.move.split('|'); moveCharBy(id,+d); render(); return; }
  if(t.dataset.wmove){ e.stopPropagation(); const i=t.dataset.wmove.lastIndexOf('|'); moveWorldBy(t.dataset.wmove.slice(0,i),+t.dataset.wmove.slice(i+1)); render(); return; }
  if(e.target.closest('.drag-h')) return;
  if(t.dataset.edit){ e.stopPropagation(); openCharModal(t.dataset.edit); return; }
  if(t.dataset.id){ S.activeId=t.dataset.id; save(); if(tab==='history'||tab==='total') {tab='boss';syncTabs();} render(); return; }
  if(t.dataset.filter){ bossFilter=t.dataset.filter; render(); return; }
  if(t.dataset.toggle && c){ const s=t.dataset.toggle,b=findBoss(s); const cfg=c.bosses[s]||(c.bosses[s]={enabled:false,diff:b.diffs[0],party:1}); cfg.enabled=!cfg.enabled; save(); render(); return; }
  if(t.dataset.setdiff && c){
    if(t.classList.contains('locked')){toast('클리어 체크를 해제한 뒤 난이도를 바꾸세요');return;}
    const [s,d]=t.dataset.setdiff.split('|'); const cfg=c.bosses[s]||(c.bosses[s]={enabled:editMode,diff:d,party:1});
    cfg.diff=d; save(); render(); return;
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
    case 'gdLogout': gdLogout(false); break;
    case 'gdSaveNow': gdPush(); break;
    case 'gdUseDrive': gdResolve('drive'); break;
    case 'gdUseLocal': gdResolve('local'); break;
    case 'gdClose': $('#driveModal').classList.remove('show'); break;
  }
});
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ if($('#ringModal').classList.contains('show')) closeRing(); if(celebrate.running) endCelebrate(); if($('#importModal').classList.contains('show')&&!$('#charModal').classList.contains('show')) closeImport(); gdMenu(false); } });
document.addEventListener('contextmenu',e=>{ const dc=e.target.closest('[data-drop]'); if(!dc) return; e.preventDefault(); changeDrop(dc.dataset.drop,-1); });
document.addEventListener('keydown',e=>{ const dc=e.target.closest?.('[data-drop]'); if(!dc) return; if(e.key==='Enter'||e.key===' '){ e.preventDefault(); changeDrop(dc.dataset.drop,+1); } else if(e.key==='Backspace'||e.key==='Delete'||e.key==='-'){ e.preventDefault(); changeDrop(dc.dataset.drop,-1); } });
document.addEventListener('change',e=>{
  const t=e.target; const c=activeChar();
  if(t.dataset.party && c){ const s=t.dataset.party; c.bosses[s].party=parseInt(t.value)||1; save(); render(); }
  if(t.id==='sAuto'){ S.settings.autoSync=t.checked; save(); render(); }
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
  data.settings.accounts=(data.settings.accounts||[]).map(a=>withKeys?{id:a.id,label:a.label,key:a.key||''}:{id:a.id,label:a.label});
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
const autoDue=()=>hasApi() && S.settings.autoSync && S.characters.some(c=>c.ocid) && Date.now()-(S.settings.lastSync||0) > CONFIG.AUTO_SYNC_MIN*60e3;
if(autoDue() || (hasApi() && S.characters.some(c=>c.ocid&&!c.accId))) syncAll({silent:true}); // 기존 데이터: 계정 자동 배정
setInterval(()=>{ if(checkResets()) render(); else renderResetInfo(); if(!document.hidden && autoDue()) syncAll({silent:true}); }, 60e3);
document.addEventListener('visibilitychange',()=>{ if(document.hidden){ if(gd.timer||gdLocalDirty()) gdPush({quick:true}); return; } if(checkResets()) render(); if(autoDue()) syncAll({silent:true}); });
window.addEventListener('pagehide',()=>{ if(gd.timer||gdLocalDirty()) gdPush({quick:true}); });
gdRender();
if(gdUsable()){ gdLoadLib().catch(()=>{}); if(gdMeta.on) gdConnect(false); }
