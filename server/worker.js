/* 보스 캐릭터 관리 — 동기화 서버 (Cloudflare Workers + D1)
 *
 * 로그인: 넥슨 Open API 키 → 서버가 넥슨 /maplestory/v1/character/list 로 키를 확인하고 account_id 를 얻음
 *   → 계정 식별값 = sha256(ID_PEPPER + ':' + account_id). 원본 키·account_id 는 저장하지 않음.
 *   → 무작위 세션 토큰 발급 (브라우저 localStorage 보관, 서버에는 sha256(토큰)만).
 * 데이터: 사용자별 JSON 1개 (state). rev 로 동시 저장 충돌 감지(409 → 브라우저가 3-way 병합 후 다시 저장).
 *   저장 전에 settings.apiKey · settings.accounts[].key 를 서버에서도 한 번 더 지움(원본 키가 절대 저장되지 않게).
 *
 * 초대 비밀번호(친구 전용): 로그인 전에 기기마다 한 번 POST /api/invite {pass} → 기기 표(device ticket, 365일).
 *   서버는 비밀번호 해시만 secret SITE_PASS_HASH 로 보관 (= sha256('ggoolzip-invite:' + 앞뒤 공백 뺀 비밀번호), 대소문자 구분).
 *   SITE_PASS_HASH 가 없으면 로그인 전부 거부(fail closed). 비밀번호를 바꾸면 기존 기기 표로는 새 로그인이 안 됨(이미 로그인한 세션은 유지).
 * 사용량 제한: 로그인·초대 IP별, 읽기/저장은 세션별·사용자별(한 사람이 다른 사람 몫을 다 쓰지 못하게).
 *
 * API (모두 JSON, 인증 = Authorization: Bearer <토큰>)
 *   POST   /api/invite        {pass}               → {device}  (초대 비밀번호 확인, 기기 표 발급)
 *   POST   /api/login         {key, device, label?} → {token, user, accounts:[hash], newUser, rev}
 *   POST   /api/link          {key}                (인증) 다른 넥슨 계정 키를 같은 데이터에 연결 → {accounts}
 *   POST   /api/keycheck      {key}                (인증, b64) 추가하려는 부계정·예비 키가 다른 데이터에 이미 등록됐는지 → 200 | 409 sub_key
 *   PUT    /api/subkeys       {main, subs:[{key,label}]} (인증) 부계정 키를 대표 키로 암호화해 보관 → {subs:[{ah,label}], accounts}
 *
 * 부계정 키 보관: AES-GCM-256, 키 = HKDF-SHA256(ikm=대표 키, salt=sha256(ID_PEPPER), info='ggoolzip-subkeys:v1:'+user_id).
 *   서버에는 암호문(iv+ct)만. 대표 키 원본은 저장하지 않으므로 서버(DB만 가진 사람 포함)는 대표 키 없이 풀 수 없음.
 *   대표 키로 /api/login 하면 서버가 그 순간에만 복호화해 subKeys 로 돌려줌 (부계정 키로 로그인하면 subKeys 없음: vault='locked').
 *   POST   /api/logout                             (인증) 이 세션 삭제
 *   POST   /api/logout-all                         (인증) 모든 기기 세션 삭제
 *   GET    /api/me                                 (인증) → {user, accounts, sessions, rev, updatedAt, savedAt, size}
 *   GET    /api/state/meta                         (인증) → {rev, updatedAt, savedAt}
 *   GET    /api/state                              (인증) → {rev, updatedAt, savedAt, data|null}
 *   PUT    /api/state         {baseRev, updatedAt, data} (인증) → {rev, savedAt} | 409 {rev, updatedAt, savedAt, data}
 *   DELETE /api/account                            (인증) 내 데이터·세션·계정 연결 전부 삭제
 *   GET    /api/health
 *   GET    /api/seen  · PUT /api/seen {ids:[...]}   (인증, b62) 소식 카드 읽음 표시 — 서버가 합집합으로 보관 (기기 간 동기화)
 *
 * b62 (2026-10-12):
 *  - 금고 v2 (keyvault2): AES-GCM 키 = HKDF(ikm = ID_PEPPER + 대표 넥슨 계정 account_id). account_id 원본은 저장하지 않고(해시만),
 *    넥슨이 그 계정의 '아무' 유효한 키(대표 키·예비 키·재발급 키)에만 알려 주므로, 대표 계정의 어떤 키로 로그인해도 금고가 열림.
 *    (v1 = 대표 키 문자열 그대로 → 예비 키/재발급 키/다른 키로는 'locked' 이었음.) v1 은 대표 키로 열리면 자동으로 v2 로 옮김.
 *  - 부계정·예비 키 등록부 (keyreg: sha256(ID_PEPPER:key:키) → user_id, 종류) + 계정 역할 (acct_role: 계정 해시 → main|sub).
 *    부계정/예비 키로 로그인하면 403 sub_key '이미 등록된 부계정 API입니다.' (키 원본은 저장 안 함, 해시만)
 *  - 강제 로그아웃: meta.auth_epoch_b62 (이 버전이 처음 실행된 시각) 이전에 만든 세션·기기 표(초대 비밀번호)는 무효.
 *    사용자 데이터(state·history·금고)는 그대로 — 다시 로그인하면 돌아옴.
 */
const SESSION_DAYS = 365;
const MAX_BODY = 1_800_000;          // D1 한 행 최대 2MB
const HISTORY_KEEP = 10;
const LOGIN_LIMIT = { n: 30, windowMs: 10 * 60e3 };
const INVITE_LIMIT = { n: 10, windowMs: 10 * 60e3 };          // 초대 비밀번호 시도 (IP별)
const LIMITS = {                                               // 세션별·사용자별 (1분 창)
  read:  { n: 90, windowMs: 60e3 },                            //   GET (앱은 1분에 1~2번 확인)
  write: { n: 20, windowMs: 60e3 },                            //   PUT (자동 저장은 5초 모아서)
  userWrite: { n: 40, windowMs: 60e3 },                        //   한 사용자의 모든 기기 합계
  link:  { n: 10, windowMs: 10 * 60e3 },
  keycheck: { n: 30, windowMs: 10 * 60e3 },                   // b64: 키 추가 전 확인
};
const DEVICE_DAYS = 365;
const DAY = 86400e3;

const enc = new TextEncoder();
async function sha256hex(s) {
  const d = await crypto.subtle.digest('SHA-256', enc.encode(s));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('');
}
function randToken() {
  const b = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
const pepper = env => env.ID_PEPPER || 'ggoolzip-dev-pepper';

/* ---------- CORS ---------- */
function allowedOrigin(env, origin) {
  if (!origin) return '';
  const list = String(env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
  if (list.includes(origin)) return origin;
  if (env.ALLOW_LOCALHOST === '1' && /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) return origin;
  return '';
}
function corsHeaders(env, req) {
  const o = allowedOrigin(env, req.headers.get('Origin'));
  const h = { 'Vary': 'Origin' };
  if (o) Object.assign(h, {
    'Access-Control-Allow-Origin': o,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Authorization, Content-Type',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Expose-Headers': 'Retry-After',
  });
  return h;
}
const json = (status, body, extra = {}) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...extra },
});
class HttpError extends Error { constructor(status, code, msg, extra) { super(msg || code); this.status = status; this.code = code; this.extra = extra; } }

/* ---------- 넥슨 키 확인 ---------- */
async function nexonAccounts(env, key) {
  key = String(key || '').trim();
  if (key.length < 16 || key.length > 300 || /\s/.test(key)) throw new HttpError(400, 'bad_key', 'API 키 형식이 올바르지 않습니다');
  let r;
  try {
    r = await fetch(`${env.NEXON_BASE || 'https://open.api.nexon.com'}/maplestory/v1/character/list`, { headers: { 'x-nxopen-api-key': key, 'accept': 'application/json' } });
  } catch (e) { throw new HttpError(502, 'nexon_unreachable', '넥슨 API에 연결하지 못했습니다'); }
  let body = null; try { body = await r.json(); } catch (e) {}
  if (r.status === 429) throw new HttpError(429, 'nexon_rate', '넥슨 API 호출 한도 초과 — 잠시 후 다시 시도하세요');
  if (r.status === 400 || r.status === 401 || r.status === 403) throw new HttpError(401, 'invalid_key', '넥슨이 이 API 키를 거부했습니다 (키 확인)', { nexon: body?.error?.name || '' });
  if (!r.ok) throw new HttpError(502, 'nexon_error', `넥슨 API 오류 (HTTP ${r.status})`);
  const ids = [...new Set((body?.account_list || []).map(a => String(a.account_id || '')).filter(Boolean))];
  if (!ids.length) throw new HttpError(400, 'no_account', '이 키로 조회되는 메이플 계정이 없습니다');
  const hashes = [];
  for (const id of ids) hashes.push(await sha256hex(pepper(env) + ':' + id));
  Object.defineProperty(hashes, 'ids', { value: ids, enumerable: false }); // 원본 account_id (금고 v2 키 유도에만, 저장 안 함)
  return hashes;
}
const keyHash = (env, key) => sha256hex(pepper(env) + ':key:' + String(key || '').trim()); // 키 원본 대신 저장하는 값 (keyreg)

/* ---------- b62: 새 표 (배포만 하면 자동 생성 — 원격 schema 실행 불필요) ---------- */
let schemaOk = false;
async function ensureSchema(env) {
  if (schemaOk) return;
  await env.DB.batch([
    env.DB.prepare('CREATE TABLE IF NOT EXISTS keyvault2 (user_id TEXT PRIMARY KEY, owner_hash TEXT NOT NULL, iv TEXT NOT NULL, ct TEXT NOT NULL, updated_at INTEGER NOT NULL)'),
    env.DB.prepare('CREATE TABLE IF NOT EXISTS keyreg (key_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, kind TEXT NOT NULL, updated_at INTEGER NOT NULL)'),
    env.DB.prepare('CREATE INDEX IF NOT EXISTS keyreg_user ON keyreg(user_id)'),
    env.DB.prepare('CREATE TABLE IF NOT EXISTS acct_role (acct_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, role TEXT NOT NULL)'),
    env.DB.prepare('CREATE INDEX IF NOT EXISTS acct_role_user ON acct_role(user_id)'),
    env.DB.prepare('CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)'),
    env.DB.prepare('CREATE TABLE IF NOT EXISTS seen (user_id TEXT PRIMARY KEY, ids TEXT NOT NULL, updated_at INTEGER NOT NULL)'),
  ]);
  schemaOk = true;
}
/* ---------- b62: 강제 로그아웃 기준 시각 ---------- */
const EPOCH_KEY = 'auth_epoch_b62';   // 다시 전원 로그아웃시키려면 이 이름만 바꿔 배포 (예: auth_epoch_b63)
let epochMs = 0;
async function authEpoch(env) {
  if (epochMs) return epochMs;
  const now = Date.now();
  const ins = await env.DB.prepare('INSERT OR IGNORE INTO meta (k,v) VALUES (?,?)').bind(EPOCH_KEY, String(now)).run();
  const r = await env.DB.prepare('SELECT v FROM meta WHERE k=?').bind(EPOCH_KEY).first();
  epochMs = +r.v || now;
  if (ins.meta?.changes) await env.DB.batch([ // 처음 한 번: 예전 세션·기기 표 정리 (데이터는 건드리지 않음)
    env.DB.prepare('DELETE FROM sessions WHERE created_at<?').bind(epochMs),
    env.DB.prepare('DELETE FROM devices WHERE created_at<?').bind(epochMs)]);
  return epochMs;
}

/* ---------- 부계정 키 금고 (AES-GCM, 대표 키에서 HKDF) ---------- */
const b64 = u8 => btoa(String.fromCharCode(...u8));
const unb64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
async function vaultKey(env, mainKey, userId) {
  const ikm = await crypto.subtle.importKey('raw', enc.encode(String(mainKey).trim()), 'HKDF', false, ['deriveKey']);
  const salt = new Uint8Array(await crypto.subtle.digest('SHA-256', enc.encode('ggoolzip-vault-salt:' + pepper(env))));
  return crypto.subtle.deriveKey({ name: 'HKDF', hash: 'SHA-256', salt, info: enc.encode('ggoolzip-subkeys:v1:' + userId) }, ikm, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
}
async function vaultSeal(env, mainKey, userId, obj) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv, additionalData: enc.encode(userId) }, await vaultKey(env, mainKey, userId), enc.encode(JSON.stringify(obj))));
  return { iv: b64(iv), ct: b64(ct) };
}
// v2: 대표 넥슨 계정 account_id 로 유도 (그 계정의 어떤 유효한 키로도 열림)
async function vaultKey2(env, accountId, userId) {
  const ikm = await crypto.subtle.importKey('raw', enc.encode(pepper(env) + ':acct:' + String(accountId)), 'HKDF', false, ['deriveKey']);
  const salt = new Uint8Array(await crypto.subtle.digest('SHA-256', enc.encode('ggoolzip-vault-salt:' + pepper(env))));
  return crypto.subtle.deriveKey({ name: 'HKDF', hash: 'SHA-256', salt, info: enc.encode('ggoolzip-subkeys:v2:' + userId) }, ikm, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
}
async function vault2Seal(env, hashes, userId, obj) { // hashes = nexonAccounts(대표 키) 결과 (ids 포함). 소유 계정 = 첫 계정
  const id = hashes.ids[0], owner = hashes[0], iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv, additionalData: enc.encode(userId) }, await vaultKey2(env, id, userId), enc.encode(JSON.stringify(obj))));
  await env.DB.batch([
    env.DB.prepare('INSERT INTO keyvault2 (user_id,owner_hash,iv,ct,updated_at) VALUES (?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET owner_hash=excluded.owner_hash, iv=excluded.iv, ct=excluded.ct, updated_at=excluded.updated_at').bind(userId, owner, b64(iv), b64(ct), Date.now()),
    env.DB.prepare('DELETE FROM keyvault WHERE user_id=?').bind(userId)]); // v1 은 지움
}
// 로그인 키로 금고 열기: null = 없음, false = 이 키로는 못 엶, 객체 = 내용 (+ .migrated)
async function vaultOpenAny(env, key, hashes, userId) {
  const r2 = await env.DB.prepare('SELECT owner_hash, iv, ct FROM keyvault2 WHERE user_id=?').bind(userId).first();
  if (r2) {
    const i = hashes.indexOf(r2.owner_hash); if (i < 0) return false;
    try {
      const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: unb64(r2.iv), additionalData: enc.encode(userId) }, await vaultKey2(env, hashes.ids[i], userId), unb64(r2.ct));
      return JSON.parse(new TextDecoder().decode(pt));
    } catch (e) { return false; }
  }
  const v1 = await vaultOpen(env, key, userId);
  if (v1) { await vault2Seal(env, hashes, userId, v1); } // v1 → v2 자동 이전 (대표 키로 열렸을 때만)
  return v1;
}
// 등록부·역할 다시 쓰기 (금고 내용 기준). 키 원본은 저장하지 않음 (해시만)
async function writeRegistry(env, userId, mainHashes, v) {
  const now = Date.now(), st = [env.DB.prepare('DELETE FROM keyreg WHERE user_id=?').bind(userId)]; // 역할(sub)은 지우지 않음: 부계정 목록에서 뺀 계정도 계속 부계정 (대표 계정이 되면 main 으로 바뀜)
  const reg = async (k, kind) => { if (k) st.push(env.DB.prepare('INSERT OR REPLACE INTO keyreg (key_hash,user_id,kind,updated_at) VALUES (?,?,?,?)').bind(await keyHash(env, k), userId, kind, now)); };
  await reg(v.mainBk, 'bk');
  for (const s of v.subs || []) { await reg(s.key, 'sub'); await reg(s.bk, 'bk'); for (const h of (s.ahs || (s.ah ? [s.ah] : []))) if (!mainHashes.includes(h)) st.push(env.DB.prepare("INSERT OR REPLACE INTO acct_role (acct_hash,user_id,role) VALUES (?,?,'sub')").bind(h, userId)); }
  for (const h of mainHashes) st.push(env.DB.prepare("INSERT OR REPLACE INTO acct_role (acct_hash,user_id,role) VALUES (?,?,'main')").bind(h, userId));
  await env.DB.batch(st);
}
const SUB_MSG = '이미 등록된 부계정 API입니다.';
async function vaultOpen(env, mainKey, userId) { // 없으면 null, 대표 키가 아니면 false
  const r = await env.DB.prepare('SELECT iv, ct FROM keyvault WHERE user_id=?').bind(userId).first();
  if (!r) return null;
  try {
    const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: unb64(r.iv), additionalData: enc.encode(userId) }, await vaultKey(env, mainKey, userId), unb64(r.ct));
    return JSON.parse(new TextDecoder().decode(pt));
  } catch (e) { return false; }
}

/* ---------- 사용량 제한 (D1 고정 창 카운터, 요청당 쓰기 1번) ---------- */
async function hit(env, k, lim) {
  const now = Date.now();
  const row = await env.DB.prepare(`INSERT INTO rate (k,n,reset_at) VALUES (?1,1,?2)
    ON CONFLICT(k) DO UPDATE SET n=CASE WHEN reset_at<?3 THEN 1 ELSE n+1 END, reset_at=CASE WHEN reset_at<?3 THEN ?2 ELSE reset_at END
    RETURNING n, reset_at`).bind(k, now + lim.windowMs, now).first();
  if (Math.random() < 0.01) await env.DB.prepare('DELETE FROM rate WHERE reset_at<?').bind(now - DAY).run(); // 오래된 카운터 정리
  return row.n <= lim.n ? 0 : Math.max(1, Math.ceil((row.reset_at - now) / 1000));
}
async function limit(env, k, lim, msg) {
  const wait = await hit(env, k, lim);
  if (wait) throw new HttpError(429, 'too_many', msg || `요청이 너무 많습니다 — ${wait}초 뒤 다시 시도하세요`, { retryAfter: wait });
}
const ipKey = async (env, req, kind) => kind + ':' + (await sha256hex(pepper(env) + ':ip:' + (req.headers.get('CF-Connecting-IP') || req.headers.get('X-Forwarded-For') || 'local'))).slice(0, 32);
const rateLimit = async (env, req) => limit(env, await ipKey(env, req, 'login'), LOGIN_LIMIT, '로그인 시도가 너무 많습니다 — 10분 뒤 다시 시도하세요');

/* ---------- 초대 비밀번호 ---------- */
const normPass = p => String(p || '').trim(); // 앞뒤 공백만 제거 (대소문자 구분)
function sameHex(a, b) { a = String(a || '').toLowerCase(); b = String(b || '').toLowerCase(); if (a.length !== b.length || !a.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }
const passVer = env => String(env.SITE_PASS_HASH || '').toLowerCase().slice(0, 12); // 비밀번호가 바뀌면 달라짐 → 예전 기기 표 무효
async function checkDevice(env, device) {
  if (!env.SITE_PASS_HASH) throw new HttpError(503, 'not_configured', '서버 설정이 아직 끝나지 않았습니다 (초대 비밀번호 미설정)');
  if (!/^[A-Za-z0-9_-]{20,100}$/.test(String(device || ''))) throw new HttpError(403, 'need_invite', '초대 비밀번호를 먼저 입력해 주세요');
  const d = await env.DB.prepare('SELECT created_at, expires_at, pass_ver FROM devices WHERE ticket_hash=?').bind(await sha256hex(device)).first();
  if (!d || d.expires_at < Date.now() || d.pass_ver !== passVer(env) || d.created_at < await authEpoch(env)) throw new HttpError(403, 'need_invite', '초대 비밀번호를 다시 입력해 주세요 (비밀번호가 바뀌었거나 만료됨)');
}

/* ---------- 세션 ---------- */
async function auth(env, req) {
  const m = /^Bearer\s+([A-Za-z0-9_-]{20,100})$/.exec(req.headers.get('Authorization') || '');
  if (!m) throw new HttpError(401, 'no_session', '로그인이 필요합니다');
  const th = await sha256hex(m[1]), now = Date.now();
  const s = await env.DB.prepare('SELECT user_id, created_at, last_used, expires_at FROM sessions WHERE token_hash=?').bind(th).first();
  if (!s || s.expires_at < now || s.created_at < await authEpoch(env)) { if (s) await env.DB.prepare('DELETE FROM sessions WHERE token_hash=?').bind(th).run(); throw new HttpError(401, 'no_session', '로그인이 만료되었습니다 — 다시 로그인하세요'); }
  if (now - s.last_used > DAY) await env.DB.prepare('UPDATE sessions SET last_used=?, expires_at=? WHERE token_hash=?').bind(now, now + SESSION_DAYS * DAY, th).run();
  return { userId: s.user_id, th };
}
async function newSession(env, userId, label) {
  const token = randToken(), now = Date.now();
  await env.DB.prepare('INSERT INTO sessions (token_hash,user_id,created_at,last_used,expires_at,label) VALUES (?,?,?,?,?,?)')
    .bind(await sha256hex(token), userId, now, now, now + SESSION_DAYS * DAY, String(label || '').slice(0, 60)).run();
  return token;
}
const acctList = async (env, userId) => (await env.DB.prepare('SELECT acct_hash FROM accounts WHERE user_id=? ORDER BY created_at').bind(userId).all()).results.map(r => r.acct_hash);

/* ---------- 데이터 ---------- */
// 원본 API 키가 서버에 저장되지 않도록 한 번 더 제거
function stripKeys(data) {
  const s = data && data.settings;
  if (s && typeof s === 'object') {
    delete s.apiKey; delete s.driveKeys;
    if (Array.isArray(s.accounts)) s.accounts = s.accounts.map(a => { if (a && typeof a === 'object') { const { key, ...rest } = a; return rest; } return a; });
  }
  return data;
}
async function readBody(req) {
  const len = +req.headers.get('Content-Length') || 0;
  if (len > MAX_BODY) throw new HttpError(413, 'too_large', '데이터가 너무 큽니다');
  const t = await req.text();
  if (t.length > MAX_BODY) throw new HttpError(413, 'too_large', '데이터가 너무 큽니다');
  try { return JSON.parse(t || '{}'); } catch (e) { throw new HttpError(400, 'bad_json', 'JSON 형식 오류'); }
}
const stateRow = (env, uid) => env.DB.prepare('SELECT rev, updated_at, saved_at, size, data FROM state WHERE user_id=?').bind(uid).first();
const stateOut = (row, withData = true) => row
  ? { rev: row.rev, updatedAt: row.updated_at, savedAt: row.saved_at, ...(withData ? { data: JSON.parse(row.data) } : {}) }
  : { rev: 0, updatedAt: 0, savedAt: 0, ...(withData ? { data: null } : {}) };

/* ---------- 라우트 ---------- */
async function route(req, env) {
  const url = new URL(req.url), p = url.pathname.replace(/\/+$/, ''), M = req.method;
  if (p === '/api/health') return json(200, { ok: true, v: 'b62' });
  await ensureSchema(env); await authEpoch(env); // 첫 요청 때 강제 로그아웃 기준 시각 확정

  if (p === '/api/invite' && M === 'POST') {
    if (!env.SITE_PASS_HASH) throw new HttpError(503, 'not_configured', '서버 설정이 아직 끝나지 않았습니다 (초대 비밀번호 미설정)');
    await limit(env, await ipKey(env, req, 'invite'), INVITE_LIMIT, '비밀번호 시도가 너무 많습니다 — 10분 뒤 다시 시도하세요');
    const b = await readBody(req);
    if (!sameHex(await sha256hex('ggoolzip-invite:' + normPass(b.pass)), env.SITE_PASS_HASH)) throw new HttpError(403, 'bad_invite', '초대 비밀번호가 맞지 않습니다');
    const device = randToken(), now = Date.now();
    await env.DB.prepare('INSERT INTO devices (ticket_hash,created_at,expires_at,pass_ver) VALUES (?,?,?,?)').bind(await sha256hex(device), now, now + DEVICE_DAYS * DAY, passVer(env)).run();
    return json(200, { device });
  }

  if (p === '/api/login' && M === 'POST') {
    await rateLimit(env, req);
    const b = await readBody(req);
    await checkDevice(env, b.device);
    // b62: 부계정/예비 키로 등록된 키는 로그인 불가 (넥슨 호출 전에 해시로 확인)
    if (await env.DB.prepare('SELECT 1 FROM keyreg WHERE key_hash=?').bind(await keyHash(env, b.key)).first()) throw new HttpError(403, 'sub_key', SUB_MSG);
    const hashes = await nexonAccounts(env, b.key);
    const qs = hashes.map(() => '?').join(',');
    const roles = (await env.DB.prepare(`SELECT role FROM acct_role WHERE acct_hash IN (${qs})`).bind(...hashes).all()).results;
    if (roles.some(r => r.role === 'sub') && !roles.some(r => r.role === 'main')) throw new HttpError(403, 'sub_key', SUB_MSG); // 부계정 계정의 (등록 안 된) 다른 키
    const found = (await env.DB.prepare(`SELECT a.acct_hash, a.user_id, s.saved_at FROM accounts a LEFT JOIN state s ON s.user_id=a.user_id WHERE a.acct_hash IN (${qs})`).bind(...hashes).all()).results;
    const now = Date.now(); let userId, newUser = false;
    if (found.length) userId = found.sort((x, y) => (y.saved_at || 0) - (x.saved_at || 0))[0].user_id; // 여러 데이터에 걸쳐 있으면 최근 저장한 쪽
    else { userId = crypto.randomUUID(); newUser = true; await env.DB.prepare('INSERT INTO users (id,created_at,last_login) VALUES (?,?,?)').bind(userId, now, now).run(); }
    if (!newUser) await env.DB.prepare('UPDATE users SET last_login=? WHERE id=?').bind(now, userId).run();
    const owned = new Set(found.map(f => f.acct_hash));
    const ins = hashes.filter(h => !owned.has(h)).map(h => env.DB.prepare('INSERT OR IGNORE INTO accounts (acct_hash,user_id,created_at) VALUES (?,?,?)').bind(h, userId, now));
    if (ins.length) await env.DB.batch(ins);
    const token = await newSession(env, userId, b.label);
    const row = await stateRow(env, userId);
    const v = newUser ? null : await vaultOpenAny(env, b.key, hashes, userId);
    if (v) await writeRegistry(env, userId, hashes, v);           // 금고를 연 키 = 대표 계정 → 역할·등록부 최신화
    else if (v === null && !roles.length) await env.DB.batch(hashes.map(h => env.DB.prepare("INSERT OR IGNORE INTO acct_role (acct_hash,user_id,role) VALUES (?,?,'main')").bind(h, userId)));
    return json(200, { token, user: userId.slice(0, 8), accounts: hashes, newUser, rev: row ? row.rev : 0, updatedAt: row ? row.updated_at : 0,
      vault: v === null ? 'none' : v === false ? 'locked' : 'open', subKeys: v ? (v.subs || []) : [], mainBk: v ? (v.mainBk || '') : '', mainBkLabel: v ? (v.mainBkLabel || '') : '' });
  }

  const me = await auth(env, req);
  const sk = me.th.slice(0, 32);
  if (M === 'GET') await limit(env, 'r:' + sk, LIMITS.read);
  if (M === 'PUT') { await limit(env, 'w:' + sk, LIMITS.write); await limit(env, 'uw:' + me.userId, LIMITS.userWrite); }
  if (p === '/api/link' && M === 'POST') {
    await limit(env, 'l:' + sk, LIMITS.link);
    const b = await readBody(req);
    const hashes = await nexonAccounts(env, b.key), now = Date.now();
    const qs = hashes.map(() => '?').join(',');
    const other = (await env.DB.prepare(`SELECT user_id FROM accounts WHERE acct_hash IN (${qs}) AND user_id<>?`).bind(...hashes, me.userId).all()).results;
    if (other.length) throw new HttpError(409, 'linked_elsewhere', '이 넥슨 계정은 이미 다른 데이터에 연결되어 있습니다');
    await env.DB.batch(hashes.map(h => env.DB.prepare('INSERT OR IGNORE INTO accounts (acct_hash,user_id,created_at) VALUES (?,?,?)').bind(h, me.userId, now))
      .concat(hashes.map(h => env.DB.prepare("INSERT OR IGNORE INTO acct_role (acct_hash,user_id,role) VALUES (?,?,'sub')").bind(h, me.userId))));
    return json(200, { accounts: hashes, all: await acctList(env, me.userId) });
  }
  if (p === '/api/subkeys' && M === 'PUT') {
    await limit(env, 'l:' + sk, LIMITS.link);
    const b = await readBody(req);
    const subsIn = Array.isArray(b.subs) ? b.subs : [];
    if (subsIn.length > 20) throw new HttpError(400, 'too_many_subs', '부계정 키는 20개까지');
    const mine = new Set(await acctList(env, me.userId));
    const mainHashes = await nexonAccounts(env, b.main);
    if (!mainHashes.some(h => mine.has(h))) throw new HttpError(403, 'not_main', '대표 키가 이 데이터의 계정이 아닙니다');
    const mainKey = String(b.main).trim(), now = Date.now(), out = [], seen = new Set();
    // 예비 키: 같은 넥슨 계정(계정 해시 집합이 같음)이어야 함 — 스케줄러는 그 계정 주인 키로만 동작
    const sameAcct = async (key, hs, label) => { const bk = String(key || '').trim(); if (!bk) return '';
      if (bk === mainKey || seen.has(bk)) throw new HttpError(400, 'backup_dup', `'${label}' 예비 키가 다른 키와 같습니다`);
      const bh = await nexonAccounts(env, bk); const A = new Set(hs);
      if (bh.length !== A.size || !bh.every(h => A.has(h))) throw new HttpError(400, 'backup_mismatch', `'${label}' 예비 키는 같은 넥슨 계정의 키가 아닙니다`);
      seen.add(bk); return bk; };
    const mainBk = await sameAcct(b.mainBk, mainHashes, '대표 계정');
    for (const s0 of subsIn) {
      const key = String(s0?.key || '').trim(); if (!key || key === mainKey || seen.has(key)) continue; seen.add(key);
      const hs = await nexonAccounts(env, key);
      const qs = hs.map(() => '?').join(',');
      const other = (await env.DB.prepare(`SELECT DISTINCT user_id FROM accounts WHERE acct_hash IN (${qs}) AND user_id<>?`).bind(...hs, me.userId).all()).results;
      for (const o of other) { // b62: 예전에 이 부계정 키로 따로 로그인해서 생긴 '빈' 데이터면 이쪽으로 옮김 (키 주인임은 넥슨 확인으로 증명됨)
        const oa = await acctList(env, o.user_id), st = await env.DB.prepare('SELECT data FROM state WHERE user_id=?').bind(o.user_id).first();
        let nChars = 0; try { nChars = st ? (JSON.parse(st.data).characters || []).length : 0; } catch (e) {}
        if (oa.every(h => hs.includes(h)) && nChars === 0) {
          await env.DB.batch(['state', 'state_history', 'sessions', 'accounts', 'keyvault', 'keyvault2', 'keyreg', 'acct_role', 'seen'].map(t => env.DB.prepare(`DELETE FROM ${t} WHERE user_id=?`).bind(o.user_id))
            .concat(env.DB.prepare('DELETE FROM users WHERE id=?').bind(o.user_id)));
        } else throw new HttpError(409, 'linked_elsewhere', `'${String(s0.label || '부계정').slice(0, 30)}' 키의 넥슨 계정은 이미 다른 데이터(캐릭터가 있는 데이터)에 연결되어 있습니다`);
      }
      await env.DB.batch(hs.map(h => env.DB.prepare('INSERT OR IGNORE INTO accounts (acct_hash,user_id,created_at) VALUES (?,?,?)').bind(h, me.userId, now)));
      const bk = await sameAcct(s0.bk, hs, String(s0.label || '부계정').slice(0, 30));
      out.push({ key, ah: hs[0], ...(hs.length > 1 ? { ahs: hs } : {}), label: String(s0.label || '').slice(0, 40), ...(bk ? { bk, ...(s0.bkLabel ? { bkLabel: String(s0.bkLabel).slice(0, 40) } : {}) } : {}) });
    }
    const vv = { v: 2, subs: out, ...(mainBk ? { mainBk, ...(b.mainBkLabel ? { mainBkLabel: String(b.mainBkLabel).slice(0, 40) } : {}) } : {}) };
    await vault2Seal(env, mainHashes, me.userId, vv);
    await writeRegistry(env, me.userId, mainHashes, vv);
    return json(200, { subs: out.map(({ ah, label }) => ({ ah, label })), accounts: await acctList(env, me.userId) });
  }
  if (p === '/api/keycheck' && M === 'POST') { // b64: 캐릭터 추가 창에서 부계정·예비 키를 넣을 때 미리 확인 (저장 안 함)
    await limit(env, 'kc:' + sk, LIMITS.keycheck);
    const b = await readBody(req);
    const kr = await env.DB.prepare('SELECT user_id FROM keyreg WHERE key_hash=?').bind(await keyHash(env, b.key)).first();
    if (kr && kr.user_id !== me.userId) throw new HttpError(409, 'sub_key', SUB_MSG);         // 다른 데이터에 부계정/예비 키로 등록된 키
    const hs = await nexonAccounts(env, b.key), qs = hs.map(() => '?').join(',');
    const other = (await env.DB.prepare(`SELECT DISTINCT user_id FROM accounts WHERE acct_hash IN (${qs}) AND user_id<>?`).bind(...hs, me.userId).all()).results;
    for (const o of other) { // /api/subkeys 와 같은 규칙: 그 계정만 있는 '빈' 데이터면 옮길 수 있으므로 통과, 아니면 거부
      const oa = await acctList(env, o.user_id), st = await env.DB.prepare('SELECT data FROM state WHERE user_id=?').bind(o.user_id).first();
      let nChars = 0; try { nChars = st ? (JSON.parse(st.data).characters || []).length : 0; } catch (e) {}
      if (!(oa.every(h => hs.includes(h)) && nChars === 0)) throw new HttpError(409, 'sub_key', SUB_MSG);
    }
    return json(200, { ok: true });
  }
  if (p === '/api/logout' && M === 'POST') { await env.DB.prepare('DELETE FROM sessions WHERE token_hash=?').bind(me.th).run(); return json(200, { ok: true }); }
  if (p === '/api/logout-all' && M === 'POST') { const r = await env.DB.prepare('DELETE FROM sessions WHERE user_id=?').bind(me.userId).run(); return json(200, { ok: true, removed: r.meta?.changes || 0 }); }
  if (p === '/api/me' && M === 'GET') {
    const row = await env.DB.prepare('SELECT rev, updated_at, saved_at, size FROM state WHERE user_id=?').bind(me.userId).first();
    const ns = await env.DB.prepare('SELECT COUNT(*) AS n FROM sessions WHERE user_id=?').bind(me.userId).first();
    return json(200, { user: me.userId.slice(0, 8), accounts: await acctList(env, me.userId), sessions: ns?.n || 0, rev: row?.rev || 0, updatedAt: row?.updated_at || 0, savedAt: row?.saved_at || 0, size: row?.size || 0 });
  }
  if (p === '/api/state/meta' && M === 'GET') return json(200, stateOut(await env.DB.prepare('SELECT rev, updated_at, saved_at FROM state WHERE user_id=?').bind(me.userId).first(), false));
  if (p === '/api/state' && M === 'GET') return json(200, stateOut(await stateRow(env, me.userId)));
  if (p === '/api/state' && M === 'PUT') {
    const b = await readBody(req);
    const d = b.data;
    if (!d || typeof d !== 'object' || !Array.isArray(d.characters)) throw new HttpError(400, 'bad_state', '데이터 형식이 올바르지 않습니다 (characters 없음)');
    const text = JSON.stringify(stripKeys(d)), now = Date.now(), base = Math.max(0, parseInt(b.baseRev) || 0), upd = Math.max(0, +b.updatedAt || 0);
    if (text.length > MAX_BODY) throw new HttpError(413, 'too_large', '데이터가 너무 큽니다');
    const r = base === 0
      ? await env.DB.prepare('INSERT INTO state (user_id,rev,updated_at,saved_at,size,data) VALUES (?,1,?,?,?,?) ON CONFLICT(user_id) DO NOTHING').bind(me.userId, upd, now, text.length, text).run()
      : await env.DB.prepare('UPDATE state SET rev=rev+1, updated_at=?, saved_at=?, size=?, data=? WHERE user_id=? AND rev=?').bind(upd, now, text.length, text, me.userId, base).run();
    if (!r.meta || !r.meta.changes) return json(409, { error: 'conflict', message: '다른 기기가 먼저 저장했습니다', ...stateOut(await stateRow(env, me.userId)) });
    const rev = base + 1;
    await env.DB.batch([
      env.DB.prepare('INSERT OR REPLACE INTO state_history (user_id,rev,saved_at,data) VALUES (?,?,?,?)').bind(me.userId, rev, now, text),
      env.DB.prepare('DELETE FROM state_history WHERE user_id=? AND rev<=?').bind(me.userId, rev - HISTORY_KEEP),
    ]);
    return json(200, { rev, savedAt: now, updatedAt: upd });
  }
  if (p === '/api/seen' && M === 'GET') { const r = await env.DB.prepare('SELECT ids FROM seen WHERE user_id=?').bind(me.userId).first(); return json(200, { ids: r ? JSON.parse(r.ids) : [] }); }
  if (p === '/api/seen' && M === 'PUT') { // 합집합 저장 (최근 1500개)
    const b = await readBody(req);
    const add = (Array.isArray(b.ids) ? b.ids : []).map(x => String(x).slice(0, 80)).filter(Boolean).slice(0, 1500);
    const r = await env.DB.prepare('SELECT ids FROM seen WHERE user_id=?').bind(me.userId).first();
    const cur = r ? JSON.parse(r.ids) : [], set = new Set(cur);
    for (const x of add) if (!set.has(x)) { set.add(x); cur.push(x); }
    const out = cur.slice(-1500);
    await env.DB.prepare('INSERT INTO seen (user_id,ids,updated_at) VALUES (?,?,?) ON CONFLICT(user_id) DO UPDATE SET ids=excluded.ids, updated_at=excluded.updated_at').bind(me.userId, JSON.stringify(out), Date.now()).run();
    return json(200, { ids: out });
  }
  if (p === '/api/account' && M === 'DELETE') {
    await env.DB.batch(['state', 'state_history', 'sessions', 'accounts', 'keyvault', 'keyvault2', 'keyreg', 'acct_role', 'seen'].map(t => env.DB.prepare(`DELETE FROM ${t} WHERE user_id=?`).bind(me.userId))
      .concat(env.DB.prepare('DELETE FROM users WHERE id=?').bind(me.userId)));
    return json(200, { ok: true });
  }
  throw new HttpError(404, 'not_found', '없는 주소');
}

export default {
  async fetch(req, env) {
    const cors = corsHeaders(env, req);
    if (req.method === 'OPTIONS') return new Response(null, { status: cors['Access-Control-Allow-Origin'] ? 204 : 403, headers: cors });
    if (req.headers.get('Origin') && !cors['Access-Control-Allow-Origin']) return json(403, { error: 'origin', message: '허용되지 않은 사이트' }, cors);
    try {
      const res = await route(req, env);
      for (const [k, v] of Object.entries(cors)) res.headers.set(k, v);
      return res;
    } catch (e) {
      if (e instanceof HttpError) return json(e.status, { error: e.code, message: e.message, ...(e.extra || {}) }, { ...cors, ...(e.extra?.retryAfter ? { 'Retry-After': String(e.extra.retryAfter) } : {}) });
      console.error(e);
      return json(500, { error: 'server', message: '서버 오류' }, cors);
    }
  },
  // async scheduled(event, env, ctx) {}  // 나중 단계: 매일 18:00 KST maplescouter 헥사환산 (아직 구현 안 함)
};
