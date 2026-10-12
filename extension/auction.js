// b101: 경매장 탭 안에서 검색 실행 (경매장 사이트와 같은 출처·Referer·같은 브라우저 세션 그대로).
// 예전에는 확장 백그라운드(chrome-extension:// 출처)에서 임의의 x-device-id 로 18개 요청을 한꺼번에 보내 → 넥슨이 다른 기기 사용으로 보고 경매장 세션을 끊었을 가능성.
// 규칙: 쿠키는 읽지도 쓰지도 않음, 로그인·로그아웃·인증 주소는 부르지 않음, 요청 사이 0.7초, 401/403 이면 바로 멈춤, 탭을 열거나 닫지 않음.
(() => {
  const store = { get: async k => (await chrome.storage.local.get(k))[k], set: (k, v) => chrome.storage.local.set({ [k]: v }) };
  // 경매장 사이트가 이미 쓰는 기기 id 를 그대로 사용 (localStorage 의 'device' 이름 값; 쿠키 아님). 없으면 확장에 저장한 id.
  function siteDeviceId() {
    try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (!/device/i.test(k)) continue;
      let v = localStorage.getItem(k) || ''; try { const j = JSON.parse(v); if (typeof j === 'string') v = j; } catch (e) {}
      if (/^[0-9a-f-]{16,64}$/i.test(v)) return v; } } catch (e) {}
    return '';
  }
  async function deviceId() { const s = siteDeviceId(); if (s) return s; let d = await store.get('deviceId'); if (!d) { d = [...crypto.getRandomValues(new Uint8Array(16))].map(b => b.toString(16).padStart(2, '0')).join(''); await store.set('deviceId', d); } return d; }
  chrome.runtime.onMessage.addListener((m, _s, reply) => {
    if (m?.type !== 'auctionRun') return;
    (async () => {
      try { const { makeApi, refresh } = await import(chrome.runtime.getURL('core.js'));
        const r = await refresh(makeApi(fetch.bind(window), await deviceId()), m.items, store); reply({ ok: true, ...r, at: Date.now() });
      } catch (e) { if (e.code === 'no_session') await store.set('identity', null); reply({ ok: false, error: String(e.message || e), code: e.code || '' }); }
    })();
    return true;
  });
})();
