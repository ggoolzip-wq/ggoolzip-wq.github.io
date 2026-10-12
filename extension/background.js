import { makeApi, refresh } from './core.js';
const store = { get: async k => (await chrome.storage.local.get(k))[k], set: (k, v) => chrome.storage.local.set({ [k]: v }) };
async function deviceId() { let d = await store.get('deviceId'); if (!d) { d = [...crypto.getRandomValues(new Uint8Array(16))].map(b => b.toString(16).padStart(2, '0')).join(''); await store.set('deviceId', d); } return d; }
let running = null;
async function run(items) {
  if (running) return running;
  running = (async () => {
    try {
      if (!Array.isArray(items) || !items.length) items = (await store.get('items')) || [];
      else await store.set('items', items.slice(0, 80).map(x => ({ key: String(x.key), name: String(x.name) })));
      if (!items.length) return { ok: false, error: '대시보드(관리자 창)에서 먼저 한 번 눌러주세요 — 아이템 목록이 없습니다.' };
      const r = await refresh(makeApi(fetch.bind(globalThis), await deviceId()), items, store);
      const res = { ok: true, ...r, at: Date.now() };
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
