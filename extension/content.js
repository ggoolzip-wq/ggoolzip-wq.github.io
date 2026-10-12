// bossmaple 페이지 ↔ 확장 다리 (window.postMessage). 이 페이지의 메시지만 받고, 쿠키·저장소는 건드리지 않음.
(() => {
  const post = m => window.postMessage({ src: 'bossmaple-ext', ...m }, location.origin);
  const hello = () => post({ type: 'hello', version: chrome.runtime.getManifest().version });
  window.addEventListener('message', e => {
    if (e.source !== window || e.origin !== location.origin) return;
    const m = e.data; if (!m || m.src !== 'bossmaple-page') return;
    if (m.type === 'ping') hello();
    if (m.type === 'refresh') { post({ type: 'progress' }); chrome.runtime.sendMessage({ type: 'refresh', items: m.items }, r => post({ type: 'prices', reqId: m.reqId, ...(r || { ok: false, error: '확장 응답 없음' }) })); }
    if (m.type === 'takePending') chrome.runtime.sendMessage({ type: 'takePending' }, r => { if (r && r.ok) post({ type: 'prices', reqId: 'pending', ...r }); });
  });
  hello();
})();
