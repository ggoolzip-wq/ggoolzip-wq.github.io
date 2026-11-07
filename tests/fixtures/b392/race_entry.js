// 테스트 전용 진입점(운영 배포 대상 아님 — wrangler.toml main 은 worker.js 그대로). 실제 worker.js 를 그대로 감싸
// X-Epic-Test-Hold: "앞ms,뒤ms" 헤더가 있으면 R2 put 앞/뒤에 기다려 경합 순서를 고정한다. 판정 코드는 worker.js 원본만 실행.
import real from '../../../server/worker.js';
const wait = ms => new Promise(r => setTimeout(r, Math.min(10000, Math.max(0, +ms || 0))));
export default {
  async fetch(req, env, ctx) {
    const h = String(req.headers.get('X-Epic-Test-Hold') || '').split(',');
    if (!h[0] && !h[1] || !env.EPIC) return real.fetch(req, env, ctx);
    const R = env.EPIC, EPIC = new Proxy(R, { get(t, k) { if (k === 'put') return async (...a) => { await wait(h[0]); const r = await t.put(...a); await wait(h[1]); return r; }; const v = t[k]; return typeof v === 'function' ? v.bind(t) : v; } });
    return real.fetch(req, { ...env, EPIC }, ctx);
  },
  scheduled: (...a) => real.scheduled && real.scheduled(...a),
};
