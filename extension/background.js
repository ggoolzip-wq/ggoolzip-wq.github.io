const store = { get: async k => (await chrome.storage.local.get(k))[k], set: (k, v) => chrome.storage.local.set({ [k]: v }) };

let running = null;
async function run(items) {
  if (running) return running;
  running = (async () => {
    try {
      if (!Array.isArray(items) || !items.length) items = (await store.get('items')) || [];
      else await store.set('items', items.slice(0, 80).map(x => ({ key: String(x.key), name: String(x.name) })));
      if (!items.length) return { ok: false, error: '대시보드(관리자 창)에서 먼저 한 번 눌러주세요 — 아이템 목록이 없습니다.' };
      // b101: 검색은 열려 있는 경매장 탭 안(auction.js)에서만. 확장이 직접 넥슨에 요청하거나 탭을 열고 닫지 않음.
      const tabs = await chrome.tabs.query({ url: 'https://auction.maplestory.nexon.com/*' });
      if (!tabs.length) return { ok: false, code: 'no_tab', error: '크롬에서 경매장(https://auction.maplestory.nexon.com)을 열어 로그인한 탭을 그대로 두고 다시 눌러주세요.' };
      let res = null;
      for (const t of tabs) { try { res = await chrome.tabs.sendMessage(t.id, { type: 'auctionRun', items }); break; } catch (e) { res = { ok: false, code: 'no_tab', error: '경매장 탭을 새로고침한 뒤 다시 눌러주세요 (확장 설치·업데이트 전에 연 탭).' }; } }
      if (!res?.ok) return res;
      await store.set('last', res); await store.set('pending', res); // pending: 대시보드가 열리면 넘겨줌 (팝업에서 실행한 경우)
      return res;
    } catch (e) { return { ok: false, error: String(e.message || e), code: e.code || '' }; }
    finally { running = null; }
  })();
  return running;
}
chrome.runtime.onMessage.addListener((m, _s, reply) => {
  if (m?.type === 'refresh') { run(m.items).then(reply); return true; }
  if (m?.type === 'takePending') { store.get('pending').then(p => { store.set('pending', null); reply(p || null); }); return true; }
  if (m?.type === 'status') { Promise.all([store.get('last'), store.get('items')]).then(([l, i]) => reply({ last: l || null, items: (i || []).length })); return true; }
});
