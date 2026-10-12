// b93: extension/core.js — 모의 넥슨 경매장 API로 검색 흐름 확인 (실제 넥슨에는 접속하지 않음)
import { makeApi, refresh, MIN_REMAIN } from '../extension/core.js';
let fails = 0; const check = (n, c, d = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (d !== '' ? ' — ' + JSON.stringify(d).slice(0, 300) : '')); if (!c) fails++; };
function mock({ remaining = 100, session = true } = {}) {
  const log = [], keys = {}; let rem = remaining, n = 0;
  const PR = { '마력이 깃든 안대': [3100000000, 2928000000], '데이브레이크 펜던트': [8890000], '몽환의 벨트': [] };
  const res = (status, d) => ({ ok: status < 400, status, text: async () => JSON.stringify(d) });
  const f = async (url, o) => {
    log.push([o.method, url, o.credentials, o.headers]); const u = new URL(url), p = u.pathname;
    if (!session) return res(401, {});
    if (p === '/v1/accounts') return res(200, { accounts: [{ accountId: 7 }] });
    let m = p.match(/^\/v1\/accounts\/7\/gameWorlds\/(\d+)\/characters$/); if (m) return m[1] === '0' ? res(200, { characters: [{ characterId: 11, characterName: 'a', level: 270 }, { characterId: 12, characterName: 'b', level: 285 }] }) : res(500, {});
    if (p === '/v1/market/web/daily-limit') return res(200, { search: { remaining: rem } });
    if (p === '/v1/market/web/items/searches/tool-tip' && o.method === 'POST') { const b = JSON.parse(o.body); if (rem <= 0) return res(429, {}); rem--; const k = 'K' + (++n); keys[k] = b.filters.keyword; return res(200, { searchKey: k, total: 1, items: (PR[b.filters.keyword] || []).map(x => ({ itemName: b.filters.keyword, pricePerItem: String(x) })) }); }
    m = p.match(/^\/v1\/market\/web\/items\/searches\/([^/]+)\/tool-tip$/); if (m) { const kw = keys[decodeURIComponent(m[1])]; if (!kw) return res(404, {}); return res(200, { items: (PR[kw] || []).map(x => ({ itemName: kw, pricePerItem: String(x) })) }); }
    return res(404, {});
  };
  return { f, log, keys, get rem() { return rem; } };
}
const mem = () => { const m = {}; return { get: async k => m[k], set: async (k, v) => { m[k] = v; }, m }; };
const ITEMS = [{ key: 'eye', name: '마력이 깃든 안대' }, { key: 'daybreak', name: '데이브레이크 펜던트' }, { key: 'belt', name: '몽환의 벨트' }];
{ const M = mock(), S = mem(), api = makeApi(M.f, 'dev1');
  const r = await refresh(api, ITEMS, S, 1000);
  check('lowest price per item (min of listings)', JSON.stringify(r.results) === JSON.stringify([{ item: 'eye', lowestPrice: 2928000000, time: 1000 }, { item: 'daybreak', lowestPrice: 8890000, time: 1000 }]), r.results);
  check('3 POSTs first time, no listing → not in results', r.posts === 3 && !r.results.some(x => x.item === 'belt'), r);
  check('identity = highest level char (285)', S.m.identity.characterId === 12 && S.m.identity.worldId === 0, S.m.identity);
  check('only api.mskr.nexon.com, credentials include, client headers', M.log.every(([, u, c, h]) => u.startsWith('https://api.mskr.nexon.com/v1/') && c === 'include' && h['x-client-version'] === '1.0.1' && h['x-platform'] === 'PC_WEB' && !('cookie' in h) && !('Cookie' in h)));
  check('POST body exactMatch keyword, price asc', M.log.filter(x => x[0] === 'POST').length === 3);
  const before = M.rem; const r2 = await refresh(api, ITEMS, S, 2000);
  check('second run reuses searchKeys (0 POST, no search used)', r2.posts === 0 && M.rem === before && r2.results.length === 2, r2);
}
{ const M = mock({ remaining: MIN_REMAIN + 1 }), S = mem(); const r = await refresh(makeApi(M.f, 'd'), ITEMS, S);
  check(`stops new searches when remaining < ${MIN_REMAIN}`, r.posts === 2 && r.skipped.includes('belt') && /멈춤/.test(r.stop), r); }
{ const M = mock({ session: false }), S = mem(); let e = null; try { await refresh(makeApi(M.f, 'd'), ITEMS, S); } catch (x) { e = x; }
  check('no auction session → clear error', e && e.code === 'no_session' && /auction\.maplestory\.nexon\.com/.test(e.message), e && e.message); }
console.log('FAILS:', fails); process.exit(fails ? 1 : 0);
