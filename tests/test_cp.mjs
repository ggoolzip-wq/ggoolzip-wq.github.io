// server/cp.js 단위 테스트 (가짜 넥슨 응답): 현재 조합 = API 전투력(보정), 더 좋은 프리셋 → 더 큰 값, 조합 선택
import { bestCP } from '../server/cp.js';
const fails = []; const check = (n, c, d = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (d !== '' ? ' — ' + JSON.stringify(d) : '')); if (!c) fails.push(n); };
const it = (name, str, atk, pots) => ({ item_name: name, item_total_option: { str: String(str), dex: '0', int: '0', luk: '0', attack_power: String(atk), magic_power: '0', boss_damage: '0', damage: '0', all_stat: '0' },
  potential_option_1: pots[0], potential_option_2: pots[1], potential_option_3: pots[2] });
const drop = it('미카엘라의 새 안경', 12, 15, ['아이템 드롭률 +20%', '메소 획득량 +20%', 'STR +9%']);
const boss = it('마력이 깃든 안대', 174, 73, ['STR +12%', '올스탯 +6%', 'STR +12%']);
const weap = it('데스티니 초극검', 500, 700, ['공격력 +12%', '보스 몬스터 데미지 +40%', '공격력 +12%']);
const fs = { STR: 30000, DEX: 5000, INT: 4000, LUK: 4000, 공격력: 6000, 마력: 1000, 데미지: 80, '보스 몬스터 데미지': 300, '크리티컬 데미지': 90, 전투력: 100000000, 'AP 배분 STR': 1400, 'AP 배분 DEX': 4 };
const d = {
  basic: { character_level: 290 },
  stat: { final_stat: Object.entries(fs).map(([k, v]) => ({ stat_name: k, stat_value: String(v) })) },
  equip: { preset_no: 1, item_equipment: [drop, weap], item_equipment_preset_1: [drop, weap], item_equipment_preset_2: [boss, weap], item_equipment_preset_3: [] },
  hyper: { use_preset_no: 1, hyper_stat_preset_1: [{ stat_increase: '힘 150 증가' }, { stat_increase: '획득 경험치 10.0% 증가' }], hyper_stat_preset_2: [{ stat_increase: '힘 150 증가' }, { stat_increase: '보스 몬스터 공격 시 데미지 51% 증가' }], hyper_stat_preset_3: null },
  ability: { preset_no: 2, ability_info: [{ ability_value: '메소 획득량 20% 증가' }], ability_preset_1: { ability_info: [{ ability_value: '보스 몬스터 공격 시 데미지 20% 증가' }, { ability_value: '공격력 21 증가' }] }, ability_preset_2: { ability_info: [{ ability_value: '메소 획득량 20% 증가' }] } },
  link: { character_link_skill: [{ skill_effect: '데미지 15% 증가' }], character_link_skill_preset_1: [{ skill_effect: '데미지 15% 증가' }], character_link_skill_preset_2: [{ skill_effect: '10초 동안 데미지 60% 증가' }] },
  setEffect: { set_effect: [] },
};
const r = bestCP(d);
check('current combo reproduces API 전투력 exactly (calibrated)', r.check === 100000000 && r.apiCP === 100000000, r);
check('max > current, picks 장비 2 · 하이퍼 2 · 어빌 1', r.best > r.apiCP && r.combo.equip === 2 && r.combo.hyper === 2 && r.combo.ability === 1, r);
check('conditional link (N초 동안) not counted → link 1', r.combo.link === 1, r.combo);
check('current presets detected', r.current.equip === 1 && r.current.hyper === 1 && r.current.ability === 2 && r.current.link === 1, r.current);
const same = JSON.parse(JSON.stringify(d)); same.equip.item_equipment_preset_2 = [drop, weap]; same.hyper.hyper_stat_preset_2 = same.hyper.hyper_stat_preset_1; same.ability.ability_preset_1 = same.ability.ability_preset_2;
const r2 = bestCP(same); check('all presets same → max = API value', r2.best === 100000000, r2);
console.log('FAILS:', fails); process.exit(fails.length ? 1 : 0);
