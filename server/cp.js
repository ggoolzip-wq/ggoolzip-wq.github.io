/* 최고 전투력: 넥슨 Open API 만으로 프리셋 조합(장비 3 × 하이퍼 3 × 어빌리티 3 × 링크 3) 중 최대 전투력 추정.
 *
 * 전투력 모델 (KMS, 나무위키·인벤 공식): (4×주스탯 + 부스탯)/100 × 공격력(마력) × (1 + (데미지%+보공%)/100) × (1.35 + 크뎀%/100)
 *   → 직업·숨은 값(무기 상수, 최종뎀 등) 차이는 보정 계수 k = API 전투력 / 모델(현재 상태) 로 맞춤 → 현재 조합은 API 값과 정확히 일치.
 *   각 프리셋 조합은 '현재 대비 변화량'만 모델에 반영:
 *     주/부 스탯: 최종 = (%적용 기본값)×(1+스탯%) + %미적용 + 잔차.   %적용 기본값·스탯% 는 알 수 있는 원천(장비·어빌·링크·세트·AP)으로 추정,
 *                하이퍼 스탯 수치는 %미적용, 설명 안 되는 나머지는 고정 잔차.
 *     공격력: 최종 = (기본값)×(1+공%) — 기본값의 모르는 부분은 고정, 공% 는 장비 잠재 + 링크 등.
 *     데미지·보공·크뎀: 최종 값에 변화량을 더함.
 *   장비 프리셋을 바꾸면 세트 효과도 다시 계산(에테르넬·마이스터·칠흑: 이름으로 판별, 단계 값은 API set-effect 의 set_option_full).
 *   근사: 그 외 세트(보스 장신구·여명 등)는 현재 개수 유지 · 조건부 효과(전투 돌입 시·N초 동안 등)는 제외 · 최종 데미지 변화는 무시. */
const STAT = ['STR', 'DEX', 'INT', 'LUK'];
const KOR = { 힘: 'STR', 민첩성: 'DEX', 지력: 'INT', 운: 'LUK' };
const SUB = { STR: 'DEX', DEX: 'STR', INT: 'LUK', LUK: 'DEX' };
const CHAOS = ['루즈 컨트롤 머신 마크', '마력이 깃든 안대', '몽환의 벨트', '저주받은', '거대한 공포', '커맨더 포스 이어링', '고통의 근원', '창세의 뱃지', '미트라의 분노', '컴플리트 언더컨트롤'];
const SETS = [{ k: '칠흑', has: n => CHAOS.some(c => n.includes(c)), max: 9 }, { k: '에테르넬', has: n => n.startsWith('에테르넬') }, { k: '마이스터', has: n => n.includes('마이스터') }];

const zero = () => ({ f: { STR: 0, DEX: 0, INT: 0, LUK: 0 }, n: { STR: 0, DEX: 0, INT: 0, LUK: 0 }, p: { STR: 0, DEX: 0, INT: 0, LUK: 0 }, atk: 0, matk: 0, atkp: 0, matkp: 0, dmg: 0, boss: 0, cd: 0 });
function add(a, b, s = 1) { const r = zero(); for (const g of ['f', 'n', 'p']) for (const k of STAT) r[g][k] = a[g][k] + s * b[g][k]; for (const k of ['atk', 'matk', 'atkp', 'matkp', 'dmg', 'boss', 'cd']) r[k] = a[k] + s * b[k]; return r; }
const num = s => parseFloat(String(s || '0').replace(/,/g, '')) || 0;

// 잠재능력 줄 ("STR +12%", "공격력 +30", "캐릭터 기준 10레벨 당 STR +2", "보스 몬스터 데미지 +40%")
function potLine(v, t, lv) {
  t = String(t || '').replace(/\s+/g, ' ').trim(); let m;
  if ((m = /캐릭터 기준 (\d+)레벨 당 (STR|DEX|INT|LUK) \+(\d+)/.exec(t))) { v.f[m[2]] += Math.floor(lv / +m[1]) * +m[3]; return; }
  if ((m = /^(STR|DEX|INT|LUK|올스탯) \+(\d+)%$/.exec(t))) { for (const k of m[1] === '올스탯' ? STAT : [m[1]]) v.p[k] += +m[2]; return; }
  if ((m = /^(STR|DEX|INT|LUK|올스탯) \+(\d+)$/.exec(t))) { for (const k of m[1] === '올스탯' ? STAT : [m[1]]) v.f[k] += +m[2]; return; }
  if ((m = /^공격력 \+(\d+)%$/.exec(t))) { v.atkp += +m[1]; return; }
  if ((m = /^마력 \+(\d+)%$/.exec(t))) { v.matkp += +m[1]; return; }
  if ((m = /^공격력 \+(\d+)$/.exec(t))) { v.atk += +m[1]; return; }
  if ((m = /^마력 \+(\d+)$/.exec(t))) { v.matk += +m[1]; return; }
  if ((m = /^보스 몬스터 (?:공격 시 )?데미지 \+(\d+)%$/.exec(t))) { v.boss += +m[1]; return; }
  if ((m = /^데미지 \+(\d+)%$/.exec(t))) { v.dmg += +m[1]; return; }
  if ((m = /^크리티컬 데미지 \+(\d+(?:\.\d+)?)%$/.exec(t))) { v.cd += +m[1]; return; }
}
// 세트 효과 한 단계 ("올스탯  +10, 공격력  +10, 마력  +10, 보스 몬스터 데미지 +10%")
function setLine(v, t) { for (const part of String(t || '').split(',')) potLine(v, part, 0); }
// 어빌리티·하이퍼·링크 문장 ("힘 150 증가", "보스 몬스터 공격 시 데미지 20% 증가", "공격력과 마력 25, …"). hyper=true → 스탯 수치는 %미적용
const COND = /동안|지속|돌입|처치|적용시키면|약점|낮은|걸린|HP가|소환|일반 몬스터|확률로|발동|중첩|사용 시/;
function effLine(v, text, hyper) {
  for (let c of String(text || '').split(/[\/\n]/)) {
    if (COND.test(c) && !/^\s*보스 몬스터 공격 시 데미지/.test(c)) continue;
    for (let t of c.split(',')) {
      t = t.replace(/\s+/g, ' ').trim(); let m;
      if ((m = /보스 몬스터 공격 시 데미지 (\d+)% 증가/.exec(t))) { v.boss += +m[1]; continue; }
      if ((m = /^데미지 (\d+)% 증가/.exec(t))) { v.dmg += +m[1]; continue; }
      if ((m = /크리티컬 데미지 (\d+)% 증가/.exec(t))) { v.cd += +m[1]; continue; }
      if ((m = /모든 능력치 (\d+)% 증가/.exec(t))) { for (const k of STAT) v.p[k] += +m[1]; continue; }
      if ((m = /모든 능력치 (\d+) 증가/.exec(t))) { for (const k of STAT) v[hyper ? 'n' : 'f'][k] += +m[1]; continue; }
      if ((m = /공격력과 마력 (\d+)/.exec(t))) { v.atk += +m[1]; v.matk += +m[1]; continue; }
      if ((m = /^공격력 (\d+)% 증가/.exec(t))) { v.atkp += +m[1]; continue; }
      if ((m = /^마력 (\d+)% 증가/.exec(t))) { v.matkp += +m[1]; continue; }
      if ((m = /^공격력 (\d+) 증가/.exec(t))) { v.atk += +m[1]; continue; }
      if ((m = /^마력 (\d+) 증가/.exec(t))) { v.matk += +m[1]; continue; }
      if ((m = /^(힘|민첩성|지력|운|STR|DEX|INT|LUK) (\d+) 증가/.exec(t))) { v[hyper ? 'n' : 'f'][KOR[m[1]] || m[1]] += +m[2]; continue; }
    }
  }
}
function equipVec(items, lv, setFull) {
  const v = zero(); const cnt = {};
  for (const it of items || []) {
    const o = it.item_total_option || {};
    for (const k of STAT) v.f[k] += num(o[k.toLowerCase()]);
    v.atk += num(o.attack_power); v.matk += num(o.magic_power); v.boss += num(o.boss_damage); v.dmg += num(o.damage);
    for (const k of STAT) v.p[k] += num(o.all_stat);
    for (const i of [1, 2, 3]) { potLine(v, it['potential_option_' + i], lv); potLine(v, it['additional_potential_option_' + i], lv); }
    const n = String(it.item_name || ''); for (const s of SETS) if (s.has(n)) cnt[s.k] = (cnt[s.k] || 0) + 1;
  }
  for (const s of SETS) { const full = setFull[s.k]; if (!full) continue; const c = Math.min(cnt[s.k] || 0, s.max || 99);
    for (const o of full) if (o.set_count <= c) setLine(v, o.set_option); }
  return v;
}
const listVec = (arr, f, hyper) => { const v = zero(); for (const x of arr || []) effLine(v, f(x), hyper); return v; };

export function bestCP(d) {
  const fs = Object.fromEntries((d.stat.final_stat || []).map(x => [x.stat_name, x.stat_value]));
  const apiCP = num(fs['전투력']); const lv = num(d.basic?.character_level);
  const S = Object.fromEntries(STAT.map(k => [k, num(fs[k])]));
  const main = STAT.reduce((a, k) => S[k] > S[a] ? k : a, 'STR'), sub = SUB[main], mag = main === 'INT';
  const setFull = {}; for (const s of d.setEffect?.set_effect || []) for (const t of SETS) if (String(s.set_name).startsWith(t.k)) setFull[t.k] = s.set_option_full || [];
  const eq = d.equip || {}, curEqNo = num(eq.preset_no) || 1;
  const E = [1, 2, 3].map(i => (eq['item_equipment_preset_' + i] || []).length ? equipVec(eq['item_equipment_preset_' + i], lv, setFull) : null);
  const Ecur = equipVec(eq.item_equipment, lv, setFull);
  const hy = d.hyper || {}, curHy = num(hy.use_preset_no) || 1;
  const H = [1, 2, 3].map(i => hy['hyper_stat_preset_' + i] ? listVec(hy['hyper_stat_preset_' + i], x => x.stat_increase, true) : null);
  const ab = d.ability || {}, curAb = num(ab.preset_no) || 1;
  const A = [1, 2, 3].map(i => ab['ability_preset_' + i] ? listVec(ab['ability_preset_' + i].ability_info, x => x.ability_value) : null);
  const Acur = listVec(ab.ability_info, x => x.ability_value);
  const lk = d.link || {};
  const L = [1, 2, 3].map(i => (lk['character_link_skill_preset_' + i] || []).length ? listVec(lk['character_link_skill_preset_' + i], x => x.skill_effect) : null);
  const Lcur = listVec(lk.character_link_skill, x => x.skill_effect);
  const curLk = L.findIndex(v => v && JSON.stringify(v) === JSON.stringify(Lcur)) + 1 || 0;
  const Hcur = H[curHy - 1] || zero();
  const known = add(add(add(Ecur, Acur), Lcur), Hcur);
  const ap = k => num(fs['AP 배분 ' + k]);
  // 현재 상태 분해: 스탯 = B(1+P) + N + R
  const st = (v, k, R) => (v.f[k] + ap(k)) * (1 + v.p[k] / 100) + v.n[k] + R;
  const R = Object.fromEntries([main, sub].map(k => [k, S[k] - st(known, k, 0)]));
  const ak = mag ? ['matk', 'matkp'] : ['atk', 'atkp'], Afin = num(fs[mag ? '마력' : '공격력']);
  const Xa = Afin / (1 + known[ak[1]] / 100) - known[ak[0]];
  const base = { dmg: num(fs['데미지']), boss: num(fs['보스 몬스터 데미지']), cd: num(fs['크리티컬 데미지']) };
  const model = v => { const sm = st(v, main, R[main]), ss = st(v, sub, R[sub]); const a = (v[ak[0]] + Xa) * (1 + v[ak[1]] / 100);
    const dmg = base.dmg + v.dmg - known.dmg, boss = base.boss + v.boss - known.boss, cd = base.cd + v.cd - known.cd;
    return (4 * sm + ss) / 100 * a * (1 + (dmg + boss) / 100) * (1.35 + cd / 100); };
  const m0 = model(known), k = apiCP && m0 ? apiCP / m0 : 1;
  let best = { cp: apiCP, combo: { equip: curEqNo, hyper: curHy, ability: curAb, link: curLk } };
  const opt = arr => arr.map((v, i) => v ? i + 1 : 0).filter(Boolean);
  for (const e of opt(E)) for (const h of opt(H)) for (const a of opt(A)) for (const l of (opt(L).length ? opt(L) : [0])) {
    const v = add(add(add(E[e - 1], A[a - 1]), l ? L[l - 1] : Lcur), H[h - 1]);
    const cp = Math.round(k * model(v));
    if (cp > best.cp) best = { cp, combo: { equip: e, hyper: h, ability: a, link: l } };
  }
  return { best: best.cp, combo: best.combo, apiCP, current: { equip: curEqNo, hyper: curHy, ability: curAb, link: curLk }, k: +k.toFixed(4), check: Math.round(k * m0), main };
}

/* 넥슨 Open API 에서 필요한 응답 모으기 (사용자 자신의 키, 재시도 없음) */
export async function fetchCPData(ocid, key, fetchImpl = fetch) {
  const A = 'https://open.api.nexon.com/maplestory/v1/';
  const g = async p => { const r = await fetchImpl(A + p + (p.includes('?') ? '&' : '?') + 'ocid=' + encodeURIComponent(ocid), { headers: { 'x-nxopen-api-key': key, accept: 'application/json' } });
    if (!r.ok) throw new Error('nexon ' + r.status + ' ' + p); return r.json(); };
  const out = {};
  for (const [k, p] of [['basic', 'character/basic'], ['stat', 'character/stat'], ['hyper', 'character/hyper-stat'], ['equip', 'character/item-equipment'],
    ['ability', 'character/ability'], ['link', 'character/link-skill'], ['setEffect', 'character/set-effect']]) out[k] = await g(p);
  return out;
}
