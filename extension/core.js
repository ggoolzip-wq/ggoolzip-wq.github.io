// bossmaple 경매장 최저가 — 검색 로직 (background.js 와 테스트(node)가 같이 씀)
// 엔드포인트·헤더는 github.com/oyc0401/maple-auction-mcp (server/src/auction/api.ts, mapping.ts, 2026-07 실측값) 기준.
// 안전 규칙: https://api.mskr.nexon.com 만 호출, credentials:'include' 로 브라우저가 쿠키를 붙일 뿐 쿠키 값은 읽거나 보내지 않음.
export const BASE = 'https://api.mskr.nexon.com/v1';
export const WORLDS = [0, 1, 3, 4, 5, 10, 16, 29, 43, 44, 45, 46, 48, 49, 50, 51, 52, 54];
export const MIN_REMAIN = 10; // 남은 하루 검색 횟수가 이보다 적으면 새 검색(POST)을 멈춤
const ok = u => { try { const x = new URL(u); return x.protocol === 'https:' && x.hostname === 'api.mskr.nexon.com'; } catch (e) { return false; } };

export function makeApi(fetchFn, deviceId) {
  const headers = body => ({ accept: 'application/json, text/plain, */*', 'x-platform': 'PC_WEB', 'x-device-id': deviceId, 'x-client-version': '1.0.1', ...(body ? { 'Content-Type': 'application/json' } : {}) });
  async function call(method, url, body) {
    if (!ok(url)) throw new Error('blocked url');
    const r = await fetchFn(url, { method, credentials: 'include', headers: headers(body), ...(body ? { body: JSON.stringify(body) } : {}) });
    const t = await r.text(); let d = null; try { d = JSON.parse(t); } catch (e) {}
    return { ok: r.ok, status: r.status, data: d };
  }
  return {
    accounts: () => call('GET', `${BASE}/accounts`),
    chars: (a, w) => call('GET', `${BASE}/accounts/${a}/gameWorlds/${w}/characters`),
    dailyLimit: () => call('GET', `${BASE}/market/web/daily-limit`),
    create: body => call('POST', `${BASE}/market/web/items/searches/tool-tip`, body),
    page: (key, id) => call('GET', `${BASE}/market/web/items/searches/${encodeURIComponent(key)}/tool-tip?` + new URLSearchParams({ page: '1', limit: '20', sortType: 'PRICE_PER_ITEM_ASC', accountId: String(id.accountId), characterId: String(id.characterId) })),
  };
}

// 검색 기준 캐릭터 = 계정의 최고 레벨 캐릭터 (모두 GET, 검색 횟수 안 씀)
export async function findIdentity(api) {
  const acc = await api.accounts();
  if (!acc.ok) throw Object.assign(new Error('경매장 세션이 없습니다. 크롬에서 https://auction.maplestory.nexon.com 을 열어 로그인한 뒤 다시 눌러주세요.'), { code: 'no_session', status: acc.status });
  let best = null;
  for (const a of acc.data?.accounts || []) {
    const rs = await Promise.all(WORLDS.map(w => api.chars(a.accountId, w).then(r => ({ w, r }))));
    for (const { w, r } of rs) if (r.ok) for (const c of r.data?.characters || []) if (!best || (c.level || 0) > best.level) best = { worldId: w, accountId: a.accountId, characterId: c.characterId, level: c.level || 0 };
  }
  if (!best) throw Object.assign(new Error('메이플 캐릭터를 찾지 못했습니다.'), { code: 'no_char' });
  return best;
}
const remaining = async api => { const r = await api.dailyLimit(); const v = r.ok ? r.data?.search?.remaining : null; return typeof v === 'number' ? v : null; };
const lowest = (data, name) => { const it = (data?.items || []).filter(x => x && x.itemName === name && Number(x.pricePerItem) > 0); return it.length ? Math.min(...it.map(x => Number(x.pricePerItem))) : null; };
const body = (name, id) => ({ worldId: id.worldId, accountId: id.accountId, characterId: id.characterId, page: 1, limit: 10, sortType: 'PRICE_PER_ITEM_ASC', saveRecentKeyword: false, filters: { exactMatch: true, keyword: name } });

/* items = [{key, name}]. store = {get(k), set(k,v)} (chrome.storage 또는 테스트용).
 * 이미 받은 searchKey 가 살아 있으면 GET 으로 다시 봄(검색 횟수 안 씀). 없거나 만료됐을 때만 POST(1회 소진).
 * 시작 전·POST 마다 남은 횟수(daily-limit, GET)를 보고 MIN_REMAIN 미만이면 멈춤. */
export async function refresh(api, items, store, now = Date.now()) {
  let id = await store.get('identity');
  if (!id) { id = await findIdentity(api); await store.set('identity', id); }
  const keys = (await store.get('searchKeys')) || {};
  const out = [], skipped = []; let left = await remaining(api), posts = 0, stop = '';
  for (const it of items) {
    let price = null, got = false;
    const k = keys[it.name];
    if (k) { const r = await api.page(k, id); if (r.ok && r.data) { price = lowest(r.data, it.name); got = true; } else if (r.status === 401) throw Object.assign(new Error('경매장 세션이 만료됐습니다. 경매장 페이지를 새로고침해주세요.'), { code: 'no_session' }); else delete keys[it.name]; }
    if (!got) {
      if (left != null && left < MIN_REMAIN) { stop = `남은 검색 ${left}회 — 멈춤`; skipped.push(it.key); continue; }
      const r = await api.create(body(it.name, id)); posts++;
      if (r.status === 401) throw Object.assign(new Error('경매장 세션이 만료됐습니다. 경매장 페이지를 새로고침해주세요.'), { code: 'no_session' });
      if (r.status === 429) { stop = '하루 검색 한도'; skipped.push(it.key); break; }
      if (!r.ok) { skipped.push(it.key); continue; }
      if (r.data?.searchKey) keys[it.name] = r.data.searchKey;
      price = lowest(r.data, it.name); if (left != null) left--;
      if (posts % 5 === 0) { const v = await remaining(api); if (v != null) left = v; }
    }
    if (price != null) out.push({ item: it.key, lowestPrice: price, time: now });
  }
  await store.set('searchKeys', keys);
  return { results: out, skipped, posts, remaining: await remaining(api), stop };
}
