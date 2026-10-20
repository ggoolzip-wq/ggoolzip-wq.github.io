/* 보스 캐릭터 관리 — 동기화 서버 (Cloudflare Workers + D1)
 *
 * 로그인: 넥슨 Open API 키 → 서버가 넥슨 /maplestory/v1/character/list 로 키를 확인하고 account_id 를 얻음
 *   → 계정 식별값 = sha256(ID_PEPPER + ':' + account_id). 원본 키·account_id 는 저장하지 않음.
 *   → 무작위 세션 토큰 발급 (브라우저 localStorage 보관, 서버에는 sha256(토큰)만).
 * 데이터: 사용자별 JSON 1개 (state). rev 로 동시 저장 충돌 감지(409 → 브라우저가 3-way 병합 후 다시 저장).
 *   저장 전에 settings.apiKey · settings.accounts[].key 를 서버에서도 한 번 더 지움(원본 키가 절대 저장되지 않게).
 *
 * b67 (2026-10-12): 초대 비밀번호 폐지 — /api/login 은 기기 표를 확인하지 않음(누구나 넥슨 키로 가입). 대신 IP별 요청 제한·새 데이터 생성 제한·
 *   데이터 크기 512KB·본문 크기 제한 (위 상수). 아래 초대 비밀번호 설명은 예전 기록 (/api/invite 는 예전 클라이언트용으로만 남음).
 * b68 (2026-10-12): 가입 승인 — 처음 보는 대표 키로 /api/login → users + approval(pending: 대표 캐릭터 이름·월드·레벨·요청 시각) + accounts(계정 해시)만
 *   만들고 세션·금고·데이터 없음 → {status:'pending', pending:{...}}. 거절·차단 → 403 rejected|blocked (세션도 막힘). approval 행이 없는 사용자 = 승인됨(기존 사용자).
 *   관리자(secret ADMIN_USER = users.id): GET /api/admin/users → {users:[{id,status,name,world,level,chars,...}]},
 *   POST /api/admin/decide {user, action: approve|reject|kick (block|unblock 은 예전 호환)}. b78: kick = 그 사용자의 등록 키·데이터·세션 전부 삭제(넥슨 계정이 완전히 풀려 나중에 새로 가입 가능). 관리자가 아니면 403 not_admin.
 * 초대 비밀번호(친구 전용, b67 에서 폐지): 로그인 전에 기기마다 한 번 POST /api/invite {pass} → 기기 표(device ticket, 365일).
 *   서버는 비밀번호 해시만 secret SITE_PASS_HASH 로 보관 (= sha256('ggoolzip-invite:' + 앞뒤 공백 뺀 비밀번호), 대소문자 구분).
 *   SITE_PASS_HASH 가 없으면 로그인 전부 거부(fail closed). 비밀번호를 바꾸면 기존 기기 표로는 새 로그인이 안 됨(이미 로그인한 세션은 유지).
 * 사용량 제한: 로그인·초대 IP별, 읽기/저장은 세션별·사용자별(한 사람이 다른 사람 몫을 다 쓰지 못하게).
 *
 * API (모두 JSON, 인증 = Authorization: Bearer <토큰>)
 *   POST   /api/invite        {pass}               → {device}  (초대 비밀번호 확인, 기기 표 발급)
 *   POST   /api/login         {key, label?} → {status:'ok', admin, token, user, accounts:[hash], newUser, rev} | {status:'pending', pending} (b68)
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
// b67: 초대 비밀번호 없이 열린 서비스 → 크기·횟수 제한 (Cloudflare 무료 플랜 D1 기준)
const MAX_STATE = 512 * 1024;        // 사용자 데이터(state JSON) 최대 512KB (서버에서 키 제거한 뒤 길이)
const MAX_BODY = MAX_STATE + 64 * 1024; // PUT /api/state 요청 본문 최대 (data + 감싸는 값)
const MAX_SMALL_BODY = 64 * 1024;    // 그 밖의 요청 본문 최대
const HISTORY_KEEP = 10;             // 복구용 저장본 최대 10개 (사용자당)
const MAX_ACCTS = 40;                // 한 데이터에 연결하는 넥슨 계정 최대
const LOGIN_LIMIT = { n: 30, windowMs: 10 * 60e3 };           // 로그인 시도 (IP별)
const NEWUSER_LIMIT = { n: 5, windowMs: 86400e3 };            // b68: 가입 승인 요청(새 데이터) IP별 하루 5개 (b67 은 10)
const NEWUSER_ALL = { n: 100, windowMs: 86400e3 };            // b68: 전체 하루 100개 (b67 은 300)
const IP_LIMITS = {                                           // b67: IP별 (1분 창) — 로그인한 요청 포함 모든 요청
  read:  { n: 300, windowMs: 60e3 },
  write: { n: 120, windowMs: 60e3 },
};
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
  // b68: 가입 승인 요청에 보여 줄 대표 캐릭터 (레벨 가장 높은 캐릭터 이름·월드·레벨)
  const chars = (body?.account_list || []).flatMap(a => a.character_list || []);
  const top = chars.sort((x, y) => (+y.character_level || 0) - (+x.character_level || 0))[0];
  Object.defineProperty(hashes, 'top', { value: top ? { name: String(top.character_name || '').slice(0, 30), world: String(top.world_name || '').slice(0, 20), level: +top.character_level || 0 } : null, enumerable: false });
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
    // b68: 가입 승인. 행이 없는 사용자 = 승인됨(b68 이전부터 있던 사용자). status = pending | ok | rejected | blocked
    env.DB.prepare('CREATE TABLE IF NOT EXISTS approval (user_id TEXT PRIMARY KEY, status TEXT NOT NULL, name TEXT, world TEXT, level INTEGER, requested_at INTEGER NOT NULL, decided_at INTEGER)'),
  ]);
  // b91: acct_role.created_at = 그 넥슨 계정(API 키)이 이 데이터에 처음 등록된 시각. 없으면 추가하고 accounts.created_at 으로 채움 (모르면 NULL → 관리자 창 '-')
  try { await env.DB.prepare('ALTER TABLE acct_role ADD COLUMN created_at INTEGER').run(); } catch (e) {}
  // b225: users.sync_click = 사용자가 캐릭터 동기화(🔄) 버튼을 마지막으로 직접 누른 시각 (자동 동기화는 안 적음). 관리자 창 '최근 로그인'
  try { await env.DB.prepare('ALTER TABLE users ADD COLUMN sync_click INTEGER').run(); } catch (e) {}
  await env.DB.prepare('UPDATE acct_role SET created_at=(SELECT a.created_at FROM accounts a WHERE a.acct_hash=acct_role.acct_hash) WHERE created_at IS NULL').run();
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
  for (const s of v.subs || []) { await reg(s.key, 'sub'); await reg(s.bk, 'bk'); for (const h of (s.ahs || (s.ah ? [s.ah] : []))) if (!mainHashes.includes(h)) st.push(env.DB.prepare("INSERT INTO acct_role (acct_hash,user_id,role,created_at) VALUES (?,?,'sub',?) ON CONFLICT(acct_hash) DO UPDATE SET user_id=excluded.user_id, role=excluded.role, created_at=COALESCE(acct_role.created_at, excluded.created_at)").bind(h, userId, now)); }
  for (const h of mainHashes) st.push(env.DB.prepare("INSERT INTO acct_role (acct_hash,user_id,role,created_at) VALUES (?,?,'main',?) ON CONFLICT(acct_hash) DO UPDATE SET user_id=excluded.user_id, role=excluded.role, created_at=COALESCE(acct_role.created_at, excluded.created_at)").bind(h, userId, now));
  await env.DB.batch(st);
}
// b95: 다른 데이터가 '이 넥슨 계정만으로 된' 데이터이고 (캐릭터 없음 | 승인 안 됨(대기·거절·차단)) 이면 부계정으로 옮길 수 있음 (키 주인은 넥슨 확인으로 증명됨).
//  지운 부계정 키를 대표 칸에 넣어 생긴 승인 대기 데이터(b94) / 예전에 그 키로 따로 로그인해 생긴 데이터 → 부계정 다시 추가가 막히지 않게
async function absorbable(env, otherId, hs) {
  if (otherId === adminId(env)) return false;
  const oa = await acctList(env, otherId); if (!oa.every(h => hs.includes(h))) return false;
  const ap = await env.DB.prepare('SELECT status FROM approval WHERE user_id=?').bind(otherId).first();
  if (ap && ap.status !== 'ok') return true;
  const st = await env.DB.prepare('SELECT data FROM state WHERE user_id=?').bind(otherId).first();
  let nChars = 0; try { nChars = st ? (JSON.parse(st.data).characters || []).length : 0; } catch (e) {}
  return nChars === 0;
}
const dropUser = (env, uid) => env.DB.batch(USER_TABLES.map(t => env.DB.prepare(`DELETE FROM ${t} WHERE user_id=?`).bind(uid)).concat(env.DB.prepare('DELETE FROM users WHERE id=?').bind(uid)));
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
// (b67: checkDevice — 초대 비밀번호 기기 표 확인 — 삭제. 로그인은 기기 표 없이)

/* ---------- b68: 가입 승인 · 관리자 ----------
 * 관리자 = Worker secret ADMIN_USER(사용자 id 전체). 바꾸기: `cd server && npx wrangler secret put ADMIN_USER` (D1 users.id 값 입력).
 * 로컬 테스트용으로 D1 meta k='admin_user' 도 읽음 (secret 이 우선). 관리자는 승인 상태와 무관하게 항상 사용 가능. */
let adminCache = null;
const adminId = env => env.ADMIN_USER || adminCache || '';
async function loadAdmin(env) { if (env.ADMIN_USER) return; const r = await env.DB.prepare("SELECT v FROM meta WHERE k='admin_user'").first(); adminCache = r ? r.v : null; }
// b78: user_id 로 사용자에 묶인 표 전부 (계정 삭제·강퇴 공통)
const USER_TABLES = ['state', 'state_history', 'sessions', 'accounts', 'keyvault', 'keyvault2', 'keyreg', 'acct_role', 'seen', 'approval', 'cp'];
/* b132: 가입 승인 스위치 — wrangler.toml [vars] APPROVAL_REQUIRED = "0" 이면 승인 끔(누구나 넥슨 키로 바로 사용), "1"(또는 없음)이면 승인 켬(b68 흐름).
 *  끔: 새 가입에 approval(pending) 행을 만들지 않고, 이미 대기(pending)인 사용자도 바로 로그인·세션 사용 가능. approval 행은 지우거나 바꾸지 않음 →
 *  다시 "1" 로 켜면 그때 대기였던 사용자는 다시 대기. 거절(rejected)·차단(blocked) 은 끔 상태에서도 그대로 막음(관리자가 직접 내린 결정). 승인 코드는 그대로 둠.
 *  AUTO_APPROVE=1 은 로컬 테스트 전용(예전 그대로) — 이것도 승인 끔과 같게 취급. */
const approvalOn = env => env.APPROVAL_REQUIRED !== '0' && env.AUTO_APPROVE !== '1';
const gated = (env, st) => !!st && st !== 'ok' && !(st === 'pending' && !approvalOn(env));
const STATUS_MSG = { pending: '승인 대기 중이에요 — 관리자가 승인하면 사용할 수 있어요', rejected: '가입 요청이 거절되었습니다', blocked: '이 계정은 이용이 차단되었습니다' };
// b102: 관리자 목록용 — 순수 계산 (D1 은 /api/admin/users 에서 표 전체를 한 번씩만 읽음, 사용자마다 쿼리하던 N+1 제거)
// 부계정 = 저장 데이터의 계정 칸 중 서버에 살아 있는 부계정 연결(acct_role role<>'main')이 있는 것만. 키를 지운 칸·키 없는 칸은 안 보임 (b102 사용자 규칙: 삭제한 부계정은 어디에도 안 남음)
function userInfoFrom(st, roles) {
  let d = {}; try { d = st ? JSON.parse(st.data) : {}; } catch (e) {}
  const chars = Array.isArray(d.characters) ? d.characters : [], accs = Array.isArray((d.settings || {}).accounts) ? d.settings.accounts : [];
  let name = '', world = '', level = 0;
  const m = chars.find(c => c && c.isMain) || [...chars].sort((x, y) => (+y?.level || 0) - (+x?.level || 0))[0];
  if (m) { name = String(m.name || ''); world = String(m.world || ''); level = +m.level || 0; }
  const rAt = Object.fromEntries(roles.map(r => [r.acct_hash, r.created_at || 0])), mainHs = roles.filter(r => r.role === 'main').map(r => r.acct_hash), subHs = new Set(roles.filter(r => r.role !== 'main').map(r => r.acct_hash));
  const hsOf = a => (Array.isArray(a.ahs) ? a.ahs : []).concat(a.ah ? [a.ah] : []).filter(h => typeof h === 'string');
  const mainAcc = accs.find(a => a && a.main) || accs.find(a => a && hsOf(a).some(h => mainHs.includes(h))) || (m && accs.find(a => a && a.id === m.accId)) || accs[0];
  const minAt = hs => { const v = hs.map(h => rAt[h]).filter(x => x > 0); return v.length ? Math.min(...v) : 0; };
  const alts = accs.filter(a => a && a !== mainAcc && hsOf(a).some(h => subHs.has(h))).map(a => {
    const cs = chars.filter(c => c && c.accId === a.id).sort((x, y) => (+y?.level || 0) - (+x?.level || 0)), c = cs[0];
    return { label: String(a.label || '').slice(0, 40), name: c ? String(c.name || '') : '', world: c ? String(c.world || '') : '', level: c ? +c.level || 0 : 0, chars: cs.length, regAt: minAt(hsOf(a)) };
  });
  const mainRegAt = minAt(mainAcc ? hsOf(mainAcc) : []) || minAt(mainHs);
  return { chars: chars.length, size: st?.size || 0, savedAt: st?.saved_at || 0, name, world, level, alts, mainRegAt };
}

/* b104: maple.ai.kr 시세 페이지 읽기 — Next.js 페이지 안의 일별 기록 {"date":"YYYY-MM-DD","items":{코드:{challenger,main}}} 중 가장 최근 날짜 하나.
 * 값 단위 = 억 메소. 돌려주는 것: {date, items:{코드:{main}}} (본섭 값만, 숫자만) */
const MAI_URL = 'https://maple.ai.kr/blog/item-price-tracker-2026';
/* b207: 빠른 파서 — 전체 문자열 치환 없이(740KB) 날짜 표시만 정규식으로 훑어 가장 새 날짜 1개의 items 덩어리만 잘라 해석 (CPU 10ms 아낌).
 * minDate 를 주면 그보다 새 날짜가 없을 때 JSON 해석도 안 함 → {date} 만 돌려줌(items 없음) */
export function parseMai(html, minDate) {
  const u = String(html || ''); const re = /\\?"date\\?":\\?"(\d{4}-\d\d-\d\d)\\?",\\?"items\\?":\{/g; let m, bd = '', bi = -1;
  while ((m = re.exec(u))) if (m[1] > bd) { bd = m[1]; bi = m.index + m[0].length - 1; }
  if (!bd) return null;
  if (minDate && bd <= minDate) return { date: bd };
  let d = 0, j = bi; for (; j < u.length && j < bi + 50000; j++) { const c = u.charCodeAt(j); if (c === 123) d++; else if (c === 125 && --d === 0) break; }
  let o; try { o = JSON.parse(u.slice(bi, j + 1).replace(/\\"/g, '"').replace(/\\\\/g, '\\')); } catch (e) { return null; }
  const items = {}; for (const [k, v] of Object.entries(o || {})) { const n = +v?.main; if (k.length <= 40 && n > 0 && n < 1e6) items[k] = { main: n }; }
  return Object.keys(items).length ? { date: bd, items } : null;
}
/* b207/b208: 우리 아이템 키 → maple.ai.kr 이름 후보(앞 = 지금 페이지 이름, 뒤 = 나중에 생기면 쓸 이름). **짝은 여기 하나뿐**(b208: app.js 복사본 없앰 —
 * 관리자 [최저가 갱신] 은 /api/admin/maple-prices 의 mapped 를 그대로 씀). 이름은 maiNorm(띄어쓰기·':'·괄호·'해머' 빼고 얼굴장식→얼장 …)으로 비교.
 * b208: 지금 페이지에 없는 아이템(오만의 원죄·소울 에테르 1~4단계·익셉셔널 귀고리)은 관리자가 손으로 넣음 — 페이지에 그 이름의 유효한 값(>0)이 생길 때만 바뀜 */
const MAI_NAMES = { lcm: ['루컨마', '루즈 컨트롤 머신 마크'], tc: ['언더컨트롤', '컴플리트 언더컨트롤'], eye: ['마깃안', '마력이 깃든 안대'], belt: ['몽벨', '몽환의 벨트'], book: ['마도서', '저주받은 마도서'], terror: ['거공', '거대한 공포'], cfe: ['커포', '커맨더 포스 이어링'], sos: ['고근', '고통의 근원'], genesis: ['창뱃', '창세의 뱃지'], mitra: ['미트라', '미트라의 분노'],
  whisper: ['근원의 속삭임'], oath: ['죽음의 맹세'], bliss: ['황홀한 악몽'], spirit: ['굶주리는 핏빛 원혼'], legacy: ['불멸의 유산'], papmark: ['파풀마', '파풀라투스 마크'], g_life: ['연마석(스카)', '생명의 연마석'], g_faith: ['신마석(스카)', '신념의 연마석'],
  ring_r4: ['리4', '리스트레인트 링 4레벨'], ring_c4: ['컨4', '컨티뉴어스 링 4레벨'], h_face: ['익셉셔널 얼장'], h_eye: ['익셉셔널 눈장'], h_belt: ['익셉셔널 벨트'], h_ear: ['익셉셔널 귀고리', '익셉셔널 이어링'],
  sin: ['오만의 원죄', '원죄'], se1: ['1단계 소울 에테르', '소울 에테르 1단계', '소울에테르1'], se2: ['2단계 소울 에테르', '소울 에테르 2단계', '소울에테르2'], se3: ['3단계 소울 에테르', '소울 에테르 3단계', '소울에테르3'], se4: ['4단계 소울 에테르', '소울 에테르 4단계', '소울에테르4'] };
const maiNorm = n => String(n || '').replace(/[\s:()\[\]·\-]/g, '').replace(/해머/g, '').replace(/얼굴장식/g, '얼장').replace(/눈장식/g, '눈장').replace(/귀걸이/g, '귀고리');
const MAI_BY = (() => { const o = {}; for (const [k, L] of Object.entries(MAI_NAMES)) for (const n of L) o[maiNorm(n)] = k; return o; })();
// 값이 없거나 0·숫자 아님 → 그 아이템은 빼고(덮지도 지우지도 않음). 같은 키에 이름이 여럿이면 앞(지금 이름) 우선
export function maiMap(items, t) { const P = {}, rank = {};
  for (const [n, o] of Object.entries(items || {})) { const k = MAI_BY[maiNorm(n)]; if (!k) continue; const v = +o?.main; if (!(v > 0 && v < 1e6)) continue;
    const r = MAI_NAMES[k].findIndex(x => maiNorm(x) === maiNorm(n)); if (k in rank && rank[k] <= r) continue; rank[k] = r; P[k] = { p: Math.round(v * 1e8), t }; }
  return P; }
export const maiUnmatched = items => Object.keys(items || {}).filter(n => !MAI_BY[maiNorm(n)]).sort();
export const MAI_KEYS = Object.keys(MAI_NAMES); export const maiKeysList = () => MAI_KEYS;
// b220: 시세 등록 창 '시세 정보 없음' 상태 = 이것 하나 (자동 cron·[최저가 갱신] 둘 다 mai_cache 기준으로 같은 값) — got = 가장 새 시세 날짜에 값을 받은 우리 키
export const maiInfo = cv => (cv && cv.items ? { date: cv.date, got: Object.keys(maiMap(cv.items, 0)), unmatched: maiUnmatched(cv.items), fetchedAt: cv.fetchedAt || 0 } : null);
/* b207: maple.ai.kr 시세 자동 갱신 (주인 허락 받음, 예의 있게).
 *  - cron 매 1분 중 KST 분 %30==0(:00·:30, 사용자 결정) 일 때만, 그리고 오늘(KST) 새 날짜를 아직 못 찾았을 때만 1번 요청. 찾으면 그날은 끝, 다음 00:00 KST 부터 다시.
 *  - If-None-Match(저장한 ETag) → 안 바뀌면 304(0바이트). 설명하는 User-Agent.
 *  - 가격 = 시세 데이터의 날짜가 저장한 것보다 새로울 때만 바꿈(다른 페이지 수정으로 ETag 만 바뀌면 가격 그대로).
 *  - admin_prices: 짝이 있는 아이템만 {p, t=처음 본 시각} 으로 덮음(관리자가 손으로 넣은 다른 아이템은 그대로). → 사이트 '가격 확인 :' = 처음 본 시각.
 *  - mai_cache = {date, items, fetchedAt(그 날짜를 처음 본 시각), etag, foundDay, checkedAt} — KST 날짜로 잠그지 않음(b104 버그 고침).
 *  - mai_seen = [{date, at, by}] 새 날짜를 처음 본 시각 기록(최근 60개) → 실제 올라오는 시각 파악용. */
const MAI_UA = 'bossmaple-price-sync/1.0 (+https://bossmaple.pages.dev; daily item price sync with owner permission; contact via site)';
const kday = t => new Date(t + 9 * 3600e3).toISOString().slice(0, 10);
const maiDue = t => new Date(t + 9 * 3600e3).getUTCMinutes() % 30 === 0; // b207: 사용자 결정 = 30분마다(KST :00 · :30)
async function metaGet(env, k) { const r = await env.DB.prepare('SELECT v FROM meta WHERE k=?').bind(k).first(); try { return r ? JSON.parse(r.v) : null; } catch (e) { return null; } }
const metaPut = (env, k, v) => env.DB.prepare('INSERT INTO meta (k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v').bind(k, JSON.stringify(v)).run();
export async function maiRefresh(env, now = Date.now(), by = 'cron') {
  const cv = (await metaGet(env, 'mai_cache')) || {};
  const h = { 'User-Agent': MAI_UA, Accept: 'text/html', 'Accept-Language': 'ko-KR,ko;q=0.9' }; if (cv.etag && cv.date) h['If-None-Match'] = cv.etag;
  const r = await fetch(env.MAI_URL || MAI_URL, { headers: h });
  if (r.status === 304) { cv.checkedAt = now; cv.auto = 1; await metaPut(env, 'mai_cache', cv); return { status: 'same', cv }; }
  if (!r.ok) throw new HttpError(502, 'mai_http', `maple.ai.kr 응답 ${r.status}`);
  const out = parseMai(await r.text(), cv.items ? cv.date : '');
  if (!out) throw new HttpError(502, 'mai_parse', 'maple.ai.kr 시세 표를 읽지 못했습니다 (페이지 구조가 바뀌었을 수 있음)');
  cv.etag = r.headers.get('ETag') || ''; cv.checkedAt = now; cv.auto = 1;
  if (!out.items) { await metaPut(env, 'mai_cache', cv); return { status: 'nochange', cv }; } // 페이지만 바뀜 → 가격 그대로
  const P = maiMap(out.items, now), cur = (await metaGet(env, 'admin_prices')) || {};
  for (const [k, o] of Object.entries(P)) cur[k] = o;
  const seen = (await metaGet(env, 'mai_seen')) || []; seen.push({ date: out.date, at: now, by }); while (seen.length > 60) seen.shift();
  // b208: 페이지에 있는데 우리 짝이 없는 이름 = meta.mai_unmatched {date, at, names, first:{이름: 처음 본 시세 날짜}} → 새 아이템이 생기면 여기서 보고 MAI_NAMES 에 추가
  const um = (await metaGet(env, 'mai_unmatched')) || {}, first = um.first || {}, names = maiUnmatched(out.items); for (const n of names) if (!first[n]) first[n] = out.date;
  const umv = { date: out.date, at: now, names, first, missing: MAI_KEYS.filter(k => !P[k]) };
  const nv = { date: out.date, items: out.items, fetchedAt: now, etag: cv.etag, foundDay: kday(now), checkedAt: now, auto: 1 };
  await env.DB.batch([env.DB.prepare("INSERT INTO meta (k,v) VALUES ('admin_prices',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(JSON.stringify(cur)),
    env.DB.prepare("INSERT INTO meta (k,v) VALUES ('mai_cache',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(JSON.stringify(nv)),
    env.DB.prepare("INSERT INTO meta (k,v) VALUES ('mai_seen',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(JSON.stringify(seen)),
    env.DB.prepare("INSERT INTO meta (k,v) VALUES ('mai_unmatched',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(JSON.stringify(umv))]);
  console.log('mai new date', out.date, Object.keys(P).length);
  return { status: 'new', cv: nv, prices: cur };
}
/* 처음 배포 직후 1번(mai_cache 에 auto 표시가 없을 때 = 자동 확인을 한 번도 안 함)은 :00/:30 을 기다리지 않고 바로 확인 */
export async function maiCron(env, now = Date.now(), cv0) {
  if (env.MAI_OFF) return 'skip';
  const cv = cv0 !== undefined ? cv0 : await metaGet(env, 'mai_cache'); if (!maiDue(now) && cv && cv.auto) return 'skip';
  if (cv && cv.foundDay === kday(now)) return 'done_today';
  return (await maiRefresh(env, now, 'cron')).status;
}

/* ---------- 세션 ---------- */
async function auth(env, req) {
  const m = /^Bearer\s+([A-Za-z0-9_-]{20,100})$/.exec(req.headers.get('Authorization') || '');
  if (!m) throw new HttpError(401, 'no_session', '로그인이 필요합니다');
  const th = await sha256hex(m[1]), now = Date.now();
  const s = await env.DB.prepare('SELECT s.user_id, s.created_at, s.last_used, s.expires_at, a.status FROM sessions s LEFT JOIN approval a ON a.user_id=s.user_id WHERE s.token_hash=?').bind(th).first();
  if (!s || s.expires_at < now || s.created_at < await authEpoch(env)) { if (s) await env.DB.prepare('DELETE FROM sessions WHERE token_hash=?').bind(th).run(); throw new HttpError(401, 'no_session', '로그인이 만료되었습니다 — 다시 로그인하세요'); }
  if (gated(env, s.status) && s.user_id !== adminId(env)) { await env.DB.prepare('DELETE FROM sessions WHERE token_hash=?').bind(th).run(); throw new HttpError(403, s.status, STATUS_MSG[s.status] || STATUS_MSG.blocked); } // b68
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
async function readBody(req, max = MAX_SMALL_BODY) {
  const len = +req.headers.get('Content-Length') || 0;
  if (len > max) throw new HttpError(413, 'too_large', `데이터가 너무 큽니다 (최대 ${Math.round(max / 1024)}KB)`);   // 본문을 읽기 전에 거부
  const t = await req.text();
  if (t.length > max) throw new HttpError(413, 'too_large', `데이터가 너무 큽니다 (최대 ${Math.round(max / 1024)}KB)`);
  try { return JSON.parse(t || '{}'); } catch (e) { throw new HttpError(400, 'bad_json', 'JSON 형식 오류'); }
}
const stateRow = (env, uid) => env.DB.prepare('SELECT rev, updated_at, saved_at, size, data FROM state WHERE user_id=?').bind(uid).first();
const stateOut = (row, withData = true) => row
  ? { rev: row.rev, updatedAt: row.updated_at, savedAt: row.saved_at, ...(withData ? { data: JSON.parse(row.data) } : {}) }
  : { rev: 0, updatedAt: 0, savedAt: 0, ...(withData ? { data: null } : {}) };


/* ---------- b157: 신창섭 라이브 감지 (cron 매 1분, 외부 요청은 여기서만) ---------- */
const LIVE_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36';
const LIVE_SINCE = Date.parse('2026-10-15T00:00:00+09:00');
let LIVE_SCHEMA_OK = false, FEED_SCHEMA_OK = false; // b224: 표 확인(CREATE IF NOT EXISTS)은 isolate 당 1번 — 예전엔 /api/live 마다 3번
async function liveSchema(env) {
  if (LIVE_SCHEMA_OK) return;
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS live_state (src TEXT PRIMARY KEY, live INTEGER NOT NULL, vid TEXT, title TEXT, url TEXT, thumb TEXT, ok INTEGER NOT NULL, err TEXT, checked_at INTEGER NOT NULL)').run();
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS live_items (src TEXT NOT NULL, vid TEXT NOT NULL, title TEXT, url TEXT, status TEXT, start_at INTEGER, first_seen INTEGER NOT NULL, last_seen INTEGER NOT NULL, PRIMARY KEY (src, vid))').run();
  LIVE_SCHEMA_OK = true;
}
const unent = t => String(t || '').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>');
async function ytCheck() {
  const r = await fetch('https://www.youtube.com/@MapleStoryKR/live', { headers: { 'User-Agent': LIVE_UA, 'Accept-Language': 'ko-KR,ko', Cookie: 'CONSENT=YES+1' }, redirect: 'follow' });
  if (!r.ok) throw new Error('yt ' + r.status);
  const h = await r.text();
  const vid = (h.match(/<link rel="canonical" href="https:\/\/www\.youtube\.com\/watch\?v=([\w-]{11})"/) || [])[1] || null;
  const live = /"isLiveNow":true/.test(h) && !!vid;
  const upcoming = !live && vid && /"isUpcoming":true/.test(h);
  const title = unent((h.match(/<meta name="title" content="([^"]*)"/) || [])[1] || '');
  const st = Date.parse((h.match(/"startTimestamp":"([^"]+)"/) || h.match(/"scheduledStartTime":"(\d+)"/) || [])[1] || '') || null;
  const items = vid && (live || upcoming) ? [{ vid, title, url: 'https://www.youtube.com/watch?v=' + vid, status: live ? 'LIVE' : 'RESERVE', start_at: st }] : [];
  return { live, vid: live ? vid : null, title: live ? title : null, url: live ? 'https://www.youtube.com/watch?v=' + vid : 'https://www.youtube.com/@MapleStoryKR/streams', thumb: live ? `https://i.ytimg.com/vi/${vid}/hqdefault.jpg` : null, items };
}
async function nxCheck() {
  const r = await fetch('https://live.nexon.com/channels/23', { headers: { 'User-Agent': LIVE_UA, 'Accept': 'text/html', 'Accept-Language': 'ko-KR,ko' } });
  const h = await r.text();
  const m = h.match(/<script id="__NEXT_DATA__" type="application\/json"[^>]*>([\s\S]*?)<\/script>/);
  if (!r.ok || !m) throw new Error('nx ' + r.status + (m ? '' : ' no data'));
  const d = JSON.parse(m[1]); let hero = null;
  for (const q of d?.props?.pageProps?.dehydratedState?.queries || []) if (q?.state?.data?.heroBroadcasts) { hero = q.state.data.heroBroadcasts; break; }
  const L = (hero || []).filter(b => String(b.serviceId) === '23');
  const items = L.map(b => ({ vid: b.pathKey, title: b.title, url: 'https://live.nexon.com/lives/' + encodeURIComponent(b.pathKey).replace(/%3D/g, '='), status: b.status, start_at: b.scheduledAt ? Date.parse(b.scheduledAt) : null, thumb: b.thumbnailUrl }));
  const on = items.find(b => b.status === 'LIVE');
  return { live: !!on, vid: on?.vid || null, title: on?.title || null, url: on?.url || 'https://live.nexon.com/channels/23', thumb: on?.thumb || items[0]?.thumb || null, items };
}
async function liveCron(env) {
  try { await liveSchema(env); } catch (e) { console.log('live schema', String(e)); throw e; } const now = Date.now();
  /* 넥슨 라이브는 Cloudflare 보안 검사(managed challenge)로 Worker 에서 403 → 끔(NX_ON). 공개 API 는 넥슨 내부 키가 필요해 쓰지 않음 */
  const NX_ON = false;
  for (const [src, fn] of [['yt', ytCheck], ...(NX_ON ? [['nx', nxCheck]] : [])]) {
    try {
      const x = await fn();
      await env.DB.prepare('INSERT OR REPLACE INTO live_state (src,live,vid,title,url,thumb,ok,err,checked_at) VALUES (?,?,?,?,?,?,1,NULL,?)').bind(src, x.live ? 1 : 0, x.vid, x.title, x.url, x.thumb, now).run();
      for (const it of x.items) if ((it.start_at || now) >= LIVE_SINCE)
        await env.DB.prepare('INSERT INTO live_items (src,vid,title,url,status,start_at,first_seen,last_seen) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(src,vid) DO UPDATE SET title=excluded.title,status=excluded.status,start_at=COALESCE(excluded.start_at,live_items.start_at),last_seen=excluded.last_seen').bind(src, it.vid, it.title, it.url, it.status, it.start_at, now, now).run();
      // 이번에 안 보인 LIVE 항목은 종료 처리
      await env.DB.prepare("UPDATE live_items SET status='ENDED' WHERE src=? AND status IN ('LIVE','RESERVE') AND last_seen<?").bind(src, now).run();
    } catch (e) {
      await env.DB.prepare('INSERT INTO live_state (src,live,ok,err,checked_at) VALUES (?,0,0,?,?) ON CONFLICT(src) DO UPDATE SET ok=0,err=excluded.err,checked_at=excluded.checked_at').bind(src, String(e.message || e).slice(0, 120), now).run();
    }
  }
}
async function liveRead(env) {
  await liveSchema(env);
  const st = (await env.DB.prepare('SELECT src,live,vid,title,url,thumb,ok,err,checked_at FROM live_state').all()).results || [];
  const items = (await env.DB.prepare('SELECT src,vid,title,url,status,start_at,first_seen FROM live_items ORDER BY COALESCE(start_at,first_seen) DESC LIMIT 40').all()).results || [];
  const o = { at: Date.now(), list: items, feed: await feedRead(env) }; for (const r of st) o[r.src] = { live: !!r.live, vid: r.vid, title: r.title, url: r.url, thumb: r.thumb, ok: !!r.ok, checked_at: r.checked_at };
  return new Response(JSON.stringify(o), { status: 200, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'public, max-age=15', Vary: 'Origin' } }); // b224: 사이트는 페이지 열 때 1번만 받고 15초 안 새로고침은 브라우저 캐시
}

/* ---------- b170: 넥슨 공지 빠른 감시 (서비스 키 NEXON_SVC_KEY, cron 매 1분 → 그 1분 동안 반복) ----------
   무료 플랜 제약: cron 1회당 외부 서브요청 50개(유튜브 1개 사용) · CPU 10ms. → 1회당 목록 조회 최대 FEED_MAX_LIST 번을 약 55초에 고르게 나눔.
   /notice · /notice-update · /notice-event 를 번갈아 조회(한 번에 1개) → 같은 응답이면 문자열 비교만(CPU 절약), 바뀌었을 때만 JSON 해석.
   새 글: 업데이트 → 패치내역, 공지 제목 '마이너 패치' → 패치내역, 공지/이벤트 상세(1회)에 '메이플 운영자' 수령 → 사료감지, 이벤트 제목 '썬데이 메이플' → 썬데이.
   OCR·결정석 가격·테섭·인벤은 기존 GitHub Actions(5분) 그대로. 사이트는 /api/live(30초 폴링) 응답의 feed 로 받음 → 요청 수 증가 0. */
const FEED_PATHS = [['notice', 'notice', 'notice/detail'], ['notice-update', 'update_notice', null], ['notice-event', 'event_notice', 'notice-event/detail']];
const FEED_MAX_LIST = 44, FEED_MAX_DETAIL = 4, FEED_WINDOW = 55000, FEED_CAP = 30;
const NX_NPC = /메이플\s*운영자|운영자\s*[’'"」』]?\s*NPC/g, NX_RECV = /수령|지급|받기|받으|받아|받을/, NX_EXCL = /수령\s*(?:이\s*)?불가|수령할\s*수\s*없|받을\s*수\s*없|지급되지\s*않|코인\s*(?:샵|상점)|소울\s*(?:교환|조각)|교환\s*(?:하기|해\s*주|할\s*수)/;
const NX_MINOR = /마이너\s*(?:버전\s*)?(?:\(\s*\d+\s*\)\s*)?패치/, NX_SUNDAY = /썬\s*데\s*이\s*메\s*이\s*플/;
const nxPlain = h => unent(String(h || '').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
const nxIso = s => { const m = String(s || '').match(/(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/); return m ? `${m[1]}T${m[2]}:00+09:00` : String(s || ''); };
function nxSaryo(title, body) { const t = `${title} ${body}`; for (const m of t.matchAll(NX_NPC)) { const w = t.slice(Math.max(0, m.index - 100), m.index + m[0].length + 70); if (NX_RECV.test(w) && !NX_EXCL.test(w)) return true; } return false; }
function nxSaryoEnd(body, y0) {
  const m = body.match(/수령\s*기간\s*[:：]?\s*(.{0,90}?)~\s*(.{0,70})/); if (!m) return null;
  const d = m[2].match(/(?:(\d{4})\s*년\s*)?(\d{1,2})\s*월\s*(\d{1,2})\s*일(?:\s*\(\s*\S\s*\))?(?:\s*(오전|오후)\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?)?/); if (!d) return null;
  const ly = m[1].match(/(\d{4})\s*년/); const y = +(d[1] || (ly && ly[1]) || y0);
  let hh = 23, mi = 59; if (d[4]) { hh = (+d[5]) % 12 + (d[4] === '오후' ? 12 : 0); mi = +(d[6] || 0); }
  const p = n => String(n).padStart(2, '0'); return `${y}-${p(+d[2])}-${p(+d[3])}T${p(hh)}:${p(mi)}:00+09:00`;
}
async function feedSchema(env) { if (FEED_SCHEMA_OK) return; await env.DB.prepare('CREATE TABLE IF NOT EXISTS nx_feed (k TEXT PRIMARY KEY, v TEXT NOT NULL, at INTEGER NOT NULL)').run(); FEED_SCHEMA_OK = true; }
async function feedState(env) { const o = {}; for (const r of (await env.DB.prepare('SELECT k,v FROM nx_feed').all()).results || []) { try { o[r.k] = JSON.parse(r.v); } catch (e) {} } return o; }
const feedPut = (env, k, v) => env.DB.prepare('INSERT OR REPLACE INTO nx_feed (k,v,at) VALUES (?,?,?)').bind(k, JSON.stringify(v), Date.now()).run();
async function nxGet(env, path, q) {
  const u = `${env.NEXON_BASE || 'https://open.api.nexon.com'}/maplestory/v1/${path}${q ? '?' + new URLSearchParams(q) : ''}`;
  const r = await fetch(u, { headers: { 'x-nxopen-api-key': env.NEXON_SVC_KEY, accept: 'application/json' } });
  const t = await r.text(); if (!r.ok) throw new Error(`${path} ${r.status}`); return t;
}
/* b193: 결정석 가격 1분 반영 — 새 업데이트 공지(notice-update)가 보이면 그 글 상세(1회)에서 '결정 가격표'를 읽어 nx_feed 'prices' 에 저장.
   (scripts/nexon_prices.py parse_post 를 옮긴 것: 보스·가격 표 + '결정' 문단의 적용일). 가격표 없는 새 공지도 checkedAt(마지막 확인)만 갱신.
   사이트는 /api/live 응답 feed.prices 를 prices.json(매일 19:00 Actions) 위에 덮음 — 공지 id 가 더 새것일 때만 줄을 바꿈. 매 분 가격 긁기 없음. */
const PR_MIN_ROWS = 20;
const prNum = s => { s = String(s || '').replace(/[,\s]/g, ''); let m = s.match(/^(\d+)(?:메소)?$/); if (m) return +m[1];
  m = s.match(/^(?:(\d+)억)?(?:(\d+)만)?(\d+)?(?:메소)?$/); if (m && (m[1] || m[2] || m[3])) return (+m[1] || 0) * 1e8 + (+m[2] || 0) * 1e4 + (+m[3] || 0); return null; };
const prTxt = h => unent(String(h || '').replace(/&nbsp;/gi, ' ').replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
function prParse(html) {
  html = String(html || ''); const rows = [], notes = [];
  if (!/결정/.test(html)) return { rows, notes };
  const parts = html.split(/<table\b/i);
  const paras = h => (h.match(/<(?:p|div|h\d|li)\b[^>]*>[\s\S]*?<\/(?:p|div|h\d|li)>/gi) || []).map(prTxt).filter(Boolean);
  const addNotes = h => { if (!/결정/.test(h)) return; for (const t of paras(h)) if (/힘의 결정|결정 판매|결정 가격|결정의 판매|결정석/.test(t) && !notes.includes(t)) notes.push(t); };
  addNotes(parts[0]);
  for (let i = 1; i < parts.length; i++) {
    const end = parts[i].search(/<\/table>/i), tb = end < 0 ? parts[i] : parts[i].slice(0, end), after = end < 0 ? '' : parts[i].slice(end);
    const pv = parts[i - 1].slice(-3000), hd = tb.slice(0, 3000), quick = (hd.includes('보스') && /가격|기존|변경/.test(hd)) || (pv.includes('결정') && pv.includes('가격'));
    if (!quick) { addNotes(after); continue; } // CPU 아낌: 가격표 후보만 자세히
    const prevP = paras(pv), ctx = prevP[prevP.length - 1] || '';
    const T = (tb.match(/<tr\b[\s\S]*?<\/tr>/gi) || []).map(tr => (tr.match(/<t[dh]\b[\s\S]*?<\/t[dh]>/gi) || []).map(prTxt)).filter(r => r.some(Boolean));
    if (T.length) { const head = T[0].join(' ');
      const isPrice = (head.includes('보스') && /가격|기존|변경/.test(head)) || (ctx.includes('결정') && ctx.includes('가격'));
      if (isPrice) { const body = T[0].slice(1).some(c => prNum(c) != null) ? T : T.slice(1);
        for (const r of body) { if (r.length < 2 || !r[0]) continue; const n = r.slice(1).map(prNum).filter(x => x != null); if (!n.length) continue;
          rows.push({ boss: r[0], old: n.length > 1 ? n[0] : null, new: n[n.length - 1] }); } } }
    addNotes(after);
  }
  for (const r of rows) for (const n of notes) { const m = n.match(/(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일/); const nm = r.boss.replace(/\s*\(.*\)$/, '').trim();
    if (m && nm && n.includes(nm)) { r.effective = `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`; r.effective_note = n; } }
  return { rows, notes };
}
const kstIso = (t = Date.now()) => new Date(t + 9 * 3600e3).toISOString().slice(0, 19) + '+09:00';
async function feedCron(env, t0 = Date.now(), maxList = FEED_MAX_LIST) {
  if (!env.NEXON_SVC_KEY) return;
  await feedSchema(env); const S = await feedState(env);
  const wm = S.wm || {}, items = S.items || { saryo: [], patch: [] }, chk = S.chk || {}; let sunday = S.sunday || null;
  const last = {}; let detail = 0;
  const add = (tab, x) => { const L = items[tab] = items[tab] || []; if (L.some(y => y.id === x.id)) return; L.push(x); L.sort((a, b) => String(b.date).localeCompare(String(a.date))); L.length = Math.min(L.length, FEED_CAP); };
  for (let i = 0; i < maxList; i++) {
    const due = t0 + Math.round(i * FEED_WINDOW / maxList), wait = due - Date.now();
    if (wait > 0) await new Promise(r => setTimeout(r, wait));
    if (Date.now() - t0 > FEED_WINDOW + 3000) break;
    const [path, key, det] = FEED_PATHS[i % 3]; let txt;
    try { txt = await nxGet(env, path); chk[path] = { at: Date.now(), ok: 1 }; }
    catch (e) { chk[path] = { at: Date.now(), ok: 0, err: String(e.message || e).slice(0, 80), lastOk: chk[path]?.lastOk }; continue; }
    chk[path].lastOk = chk[path].at;
    if (last[path] === txt) continue; last[path] = txt;
    let L; try { L = JSON.parse(txt)[key] || []; } catch (e) { continue; }
    const ids = L.map(x => +x.notice_id || 0), top = Math.max(0, ...ids);
    if (!(path in wm)) { wm[path] = top; await feedPut(env, 'wm', wm); continue; }
    const fresh = L.filter(x => +x.notice_id > wm[path]).sort((a, b) => a.notice_id - b.notice_id); if (!fresh.length) continue;
    let w = wm[path];
    for (const x of fresh) {
      const n = +x.notice_id, base = { title: x.title || '', url: x.url || '', date: nxIso(x.date) };
      if (path === 'notice-update') add('patch', { id: `update:${n}`, ...base });
      if ((path === 'notice-update' || (path === 'notice' && NX_MINOR.test(base.title))) && detail < FEED_MAX_DETAIL) { // b193
        const pr = S.prices || {}; pr.checkedAt = kstIso();
        if (path === 'notice-update') { detail++;
          try { const d = JSON.parse(await nxGet(env, 'notice-update/detail', { notice_id: n })); const P = prParse(d.contents);
            if (P.rows.length >= PR_MIN_ROWS && n > (+pr.id || 0)) { const same = JSON.stringify((pr.rows || []).map(r => [r.boss, r.new])) === JSON.stringify(P.rows.map(r => [r.boss, r.new]));
              Object.assign(pr, { id: n, source: { url: `https://maplestory.nexon.com/News/Update/${n}`, title: d.title || base.title, date: String(base.date).slice(0, 10).replace(/-/g, '.') }, rows: P.rows, notes: P.notes, fetchedAt: kstIso(), via: 'worker' });
              if (!same) pr.changedAt = String(base.date).slice(0, 10); }
          } catch (e) { console.log('prices', String(e)); } }
        S.prices = pr; await feedPut(env, 'prices', pr); }
      if (path === 'notice' && NX_MINOR.test(base.title)) add('patch', { id: `minor:${n}`, ...base, src: 'minor' });
      if (path === 'notice-event' && NX_SUNDAY.test(base.title) && (!sunday || n > sunday.id))
        sunday = { id: n, ...base, url: `https://maplestory.nexon.com/News/Event/${n}`, start: nxIso(x.date_event_start), end: nxIso(x.date_event_end), thumb: x.thumbnail_url || '', image: x.thumbnail_url || '', via: 'server' };
      if (det) {
        if (detail >= FEED_MAX_DETAIL) break; // 서브요청 아낌: 남은 글은 다음 회차에
        detail++;
        try { const d = JSON.parse(await nxGet(env, det, { notice_id: n })); const body = nxPlain(d.contents);
          if (nxSaryo(base.title, body)) add('saryo', { id: `${path}:${n}`, ...base, end: nxSaryoEnd(body, +base.date.slice(0, 4) || new Date().getFullYear()), src: path });
        } catch (e) { break; }
      }
      w = n;
    }
    if (w > wm[path]) { wm[path] = w; delete last[path]; if (w < top) delete last[path]; await feedPut(env, 'wm', wm); await feedPut(env, 'items', items); if (sunday) await feedPut(env, 'sunday', sunday); }
  }
  await feedPut(env, 'chk', chk);
}
async function feedRead(env) {
  try { await feedSchema(env); const S = await feedState(env); return { items: S.items || { saryo: [], patch: [] }, sunday: S.sunday || null, chk: S.chk || {}, prices: S.prices || null }; } catch (e) { return null; }
}

/* ---------- 라우트 ---------- */
async function route(req, env) {
  const url = new URL(req.url), p = url.pathname.replace(/\/+$/, ''), M = req.method;
  if (p === '/api/health') return json(200, { ok: true, v: 'b104' });
  if (p === '/api/feed' && M === 'GET') return new Response(JSON.stringify({ at: Date.now(), ...(await feedRead(env)) }), { status: 200, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'public, max-age=5' } }); // b170
  if (p === '/api/live' && M === 'GET') return liveRead(env); // b157: 라이브 상태 (외부 요청 없음, D1 읽기만)
  await ensureSchema(env); await authEpoch(env); await loadAdmin(env); // 첫 요청 때 강제 로그아웃 기준 시각 확정
  // b67: IP별 요청 제한 (읽기 300/분, 쓰기 120/분) — 세션·사용자별 제한과 별개
  await limit(env, await ipKey(env, req, M === 'GET' ? 'ipr' : 'ipw'), M === 'GET' ? IP_LIMITS.read : IP_LIMITS.write);

  if (p === '/api/invite' && M === 'POST') { // b67: 더 이상 필요 없음 (예전 화면이 캐시된 브라우저용으로만 남김 — 로그인은 기기 표를 확인하지 않음)
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
    // b67: 초대 비밀번호(기기 표) 확인 없음 — 누구나 넥슨 키로 로그인/가입. (device 값은 예전 클라이언트가 보내도 무시)
    // b62: 부계정/예비 키로 등록된 키는 로그인 불가 (넥슨 호출 전에 해시로 확인)
    if (await env.DB.prepare('SELECT 1 FROM keyreg WHERE key_hash=?').bind(await keyHash(env, b.key)).first()) throw new HttpError(403, 'sub_key', SUB_MSG);
    const hashes = await nexonAccounts(env, b.key);
    const qs = hashes.map(() => '?').join(',');
    const roles = (await env.DB.prepare(`SELECT role FROM acct_role WHERE acct_hash IN (${qs})`).bind(...hashes).all()).results;
    if (roles.some(r => r.role === 'sub') && !roles.some(r => r.role === 'main')) throw new HttpError(403, 'sub_key', SUB_MSG); // 부계정 계정의 (등록 안 된) 다른 키
    let found = (await env.DB.prepare(`SELECT a.acct_hash, a.user_id, s.saved_at FROM accounts a LEFT JOIN state s ON s.user_id=a.user_id WHERE a.acct_hash IN (${qs})`).bind(...hashes).all()).results;
    // b94: 대표 키 칸 로그인은 '그 사용자의 대표(main) 계정'으로 연결된 계정만 그 사용자로 들어감.
    //  - 지운 부계정 등 대표가 아닌 남은 연결(역할 main 아님) → 연결을 지우고 새 가입(승인 대기)으로 처리 (관리자/다른 사용자 데이터로 들어가지 않게)
    //  - 역할 기록이 전혀 없는 예전(b68 이전) 사용자이고 approval 행도 없으면 → 승인 대기로 바꿈 (자동 승인 방지)
    if (found.length) {
      const mainRows = (await env.DB.prepare(`SELECT acct_hash, user_id FROM acct_role WHERE role='main' AND acct_hash IN (${qs})`).bind(...hashes).all()).results;
      const isMain = f => mainRows.some(r => r.acct_hash === f.acct_hash && r.user_id === f.user_id);
      const keep = [], stale = [];
      for (const f of found) {
        if (isMain(f)) { keep.push(f); continue; }
        const nr = await env.DB.prepare('SELECT COUNT(*) AS n FROM acct_role WHERE user_id=?').bind(f.user_id).first();
        if (!nr || !nr.n) { // 역할 기록 없는 예전 사용자
          if (f.user_id !== adminId(env) && approvalOn(env)) { const t = hashes.top || {};
            await env.DB.prepare("INSERT OR IGNORE INTO approval (user_id,status,name,world,level,requested_at) VALUES (?,'pending',?,?,?,?)").bind(f.user_id, t.name || '', t.world || '', t.level || 0, Date.now()).run(); }
          keep.push(f);
        } else stale.push(f);
      }
      if (stale.length) await env.DB.batch(stale.flatMap(f => [env.DB.prepare('DELETE FROM accounts WHERE acct_hash=? AND user_id=?').bind(f.acct_hash, f.user_id),
        env.DB.prepare("DELETE FROM acct_role WHERE acct_hash=? AND user_id=? AND role<>'main'").bind(f.acct_hash, f.user_id)]));
      found = keep;
    }
    const now = Date.now(); let userId, newUser = false;
    if (found.length) userId = found.sort((x, y) => (y.saved_at || 0) - (x.saved_at || 0))[0].user_id; // 여러 데이터에 걸쳐 있으면 최근 저장한 쪽
    else {
      await limit(env, await ipKey(env, req, 'newuser'), NEWUSER_LIMIT, '이 네트워크에서 오늘 새로 만들 수 있는 데이터 수를 넘었습니다 — 내일 다시 시도하세요');
      await limit(env, 'newuser:all', NEWUSER_ALL, '오늘 새 가입이 많아 잠시 막혀 있습니다 — 내일 다시 시도하세요');
      userId = crypto.randomUUID(); newUser = true; const t = hashes.top || {};
      await env.DB.batch([env.DB.prepare('INSERT INTO users (id,created_at,last_login) VALUES (?,?,?)').bind(userId, now, now)]   // b68: 새 가입 = 승인 대기 (최소 기록만)
        .concat(!approvalOn(env) ? [] : [env.DB.prepare("INSERT INTO approval (user_id,status,name,world,level,requested_at) VALUES (?,'pending',?,?,?,?)").bind(userId, t.name || '', t.world || '', t.level || 0, now)])); } // AUTO_APPROVE=1 = 로컬 테스트 전용 (운영 wrangler.toml 에 넣지 말 것)
    if (!newUser) await env.DB.prepare('UPDATE users SET last_login=? WHERE id=?').bind(now, userId).run();
    const owned = new Set(found.map(f => f.acct_hash));
    const ins = hashes.filter(h => !owned.has(h)).map(h => env.DB.prepare('INSERT OR IGNORE INTO accounts (acct_hash,user_id,created_at) VALUES (?,?,?)').bind(h, userId, now));
    if (ins.length) await env.DB.batch(ins);
    // b68: 승인 안 된 사용자 = 세션·금고·데이터 없음. 대기 중이면 요청 정보만 돌려줌 (클라이언트가 '승인 대기 중' 표시, 나중에 같은 키로 다시 확인)
    const ap = userId === adminId(env) ? null : await env.DB.prepare('SELECT status, name, world, level, requested_at FROM approval WHERE user_id=?').bind(userId).first();
    if (ap && ap.status === 'pending' && approvalOn(env)) {
      const t = hashes.top; if (t && !ap.name) await env.DB.prepare('UPDATE approval SET name=?, world=?, level=? WHERE user_id=?').bind(t.name, t.world, t.level, userId).run();
      return json(200, { status: 'pending', newUser, user: userId.slice(0, 8), pending: { name: ap.name || t?.name || '', world: ap.world || t?.world || '', level: ap.level || t?.level || 0, requestedAt: ap.requested_at } });
    }
    if (ap && gated(env, ap.status)) throw new HttpError(403, ap.status, STATUS_MSG[ap.status] || STATUS_MSG.blocked);
    const token = await newSession(env, userId, b.label);
    const row = await stateRow(env, userId);
    const v = newUser ? null : await vaultOpenAny(env, b.key, hashes, userId);
    if (v) await writeRegistry(env, userId, hashes, v);           // 금고를 연 키 = 대표 계정 → 역할·등록부 최신화
    else if (v === null && !roles.length) await env.DB.batch(hashes.map(h => env.DB.prepare("INSERT OR IGNORE INTO acct_role (acct_hash,user_id,role,created_at) VALUES (?,?,'main',?)").bind(h, userId, Date.now())));
    return json(200, { status: 'ok', admin: userId === adminId(env), token, user: userId.slice(0, 8), accounts: hashes, newUser, rev: row ? row.rev : 0, updatedAt: row ? row.updated_at : 0,
      vault: v === null ? 'none' : v === false ? 'locked' : 'open', subKeys: v ? (v.subs || []) : [], mainBk: v ? (v.mainBk || '') : '', mainBkLabel: v ? (v.mainBkLabel || '') : '' });
  }

  // b112: 아이템 시세(관리자가 등록·갱신한 값) 읽기 — 공용 시세 1개 표(D1 meta.admin_prices) — 로그인 없이 누구나·어느 기기나 같은 값. 쓰기는 관리자만(PUT /api/admin/prices, 0·빈 값 무시, 더 새 시각만) (득템 가격 카드 '아이템 가격' 탭)
  if (p === '/api/prices' && M === 'GET') {
    const r = await env.DB.prepare("SELECT v FROM meta WHERE k='admin_prices'").first(); let v = {}; try { v = r ? JSON.parse(r.v) : {}; } catch (e) {}
    return json(200, { prices: v });
  }
  const me = await auth(env, req);
  const sk = me.th.slice(0, 32);
  if (M === 'GET') await limit(env, 'r:' + sk, LIMITS.read);
  if (M === 'PUT') { await limit(env, 'w:' + sk, LIMITS.write); await limit(env, 'uw:' + me.userId, LIMITS.userWrite); }
  // b225: 🔄 버튼을 직접 눌렀을 때만 페이지가 보냄. 한 번 = UPDATE 1줄 (10초 안 다시 누르면 0줄 — 제한 표 쓰기도 안 함)
  if (p === '/api/sync-click' && M === 'POST') {
    const now = Date.now();
    await env.DB.prepare('UPDATE users SET sync_click=? WHERE id=? AND COALESCE(sync_click,0)<?').bind(now, me.userId, now - 10e3).run();
    return json(200, { ok: true, at: now });
  }
  if (p === '/api/link' && M === 'POST') {
    await limit(env, 'l:' + sk, LIMITS.link);
    const b = await readBody(req);
    const hashes = await nexonAccounts(env, b.key), now = Date.now();
    const qs = hashes.map(() => '?').join(',');
    const other = (await env.DB.prepare(`SELECT DISTINCT user_id FROM accounts WHERE acct_hash IN (${qs}) AND user_id<>?`).bind(...hashes, me.userId).all()).results;
    for (const o of other) if (await absorbable(env, o.user_id, hashes)) await dropUser(env, o.user_id); // b95
    if ((await env.DB.prepare(`SELECT 1 FROM accounts WHERE acct_hash IN (${qs}) AND user_id<>?`).bind(...hashes, me.userId).first())) throw new HttpError(409, 'linked_elsewhere', '이 넥슨 계정은 이미 다른 데이터에 연결되어 있습니다');
    if ((await acctList(env, me.userId)).length + hashes.length > MAX_ACCTS) throw new HttpError(400, 'too_many_accounts', `한 데이터에 넥슨 계정은 ${MAX_ACCTS}개까지`);
    await env.DB.batch(hashes.map(h => env.DB.prepare('INSERT OR IGNORE INTO accounts (acct_hash,user_id,created_at) VALUES (?,?,?)').bind(h, me.userId, now))
      .concat(hashes.map(h => env.DB.prepare("INSERT OR IGNORE INTO acct_role (acct_hash,user_id,role,created_at) VALUES (?,?,'sub',?)").bind(h, me.userId, now))));
    return json(200, { accounts: hashes, all: await acctList(env, me.userId) });
  }
  if (p === '/api/subkeys' && M === 'PUT') {
    await limit(env, 'l:' + sk, LIMITS.link);
    const b = await readBody(req);
    const subsIn = Array.isArray(b.subs) ? b.subs : [];
    if (subsIn.length > 20) throw new HttpError(400, 'too_many_subs', '부계정 키는 20개까지');
    const mine = new Set(await acctList(env, me.userId));
    if (mine.size > MAX_ACCTS) throw new HttpError(400, 'too_many_accounts', `한 데이터에 넥슨 계정은 ${MAX_ACCTS}개까지`);
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
      for (const o of other) { // b62/b95: 옮길 수 있는 데이터면 지우고 이쪽으로
        if (await absorbable(env, o.user_id, hs)) await dropUser(env, o.user_id);
        else throw new HttpError(409, 'linked_elsewhere', `'${String(s0.label || '부계정').slice(0, 30)}' 키의 넥슨 계정은 이미 다른 데이터(캐릭터가 있는 데이터)에 연결되어 있습니다`);
      }
      await env.DB.batch(hs.map(h => env.DB.prepare('INSERT OR IGNORE INTO accounts (acct_hash,user_id,created_at) VALUES (?,?,?)').bind(h, me.userId, now)));
      const bk = await sameAcct(s0.bk, hs, String(s0.label || '부계정').slice(0, 30));
      out.push({ key, ah: hs[0], ...(hs.length > 1 ? { ahs: hs } : {}), label: String(s0.label || '').slice(0, 40), ...(bk ? { bk, ...(s0.bkLabel ? { bkLabel: String(s0.bkLabel).slice(0, 40) } : {}) } : {}) });
    }
    { // b94: 부계정 목록에서 뺀 계정의 연결(accounts·sub 역할)도 지움 → 그 키로 대표 칸 로그인 시 새 가입(승인 대기)
      const live = new Set([...mainHashes, ...out.flatMap(o => o.ahs || [o.ah])]); // 부계정(sub) 역할인데 목록에 없는 것만 (역할 없는 예전 연결·main 은 그대로)
      const gone = (await env.DB.prepare("SELECT acct_hash FROM acct_role WHERE user_id=? AND role='sub'").bind(me.userId).all()).results.map(r => r.acct_hash).filter(h => !live.has(h));
      if (gone.length) await env.DB.batch(gone.flatMap(h => [env.DB.prepare('DELETE FROM accounts WHERE acct_hash=? AND user_id=?').bind(h, me.userId),
        env.DB.prepare("DELETE FROM acct_role WHERE acct_hash=? AND user_id=? AND role<>'main'").bind(h, me.userId)]));
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
    for (const o of other) if (!(await absorbable(env, o.user_id, hs))) throw new HttpError(409, 'sub_key', SUB_MSG); // /api/subkeys 와 같은 규칙 (b95)
    return json(200, { ok: true });
  }
  if (p === '/api/unlink' && M === 'POST') { // b95: 키 삭제 → 그 키·연결 정보 서버에서 완전히 지움 (계정 해시로 묶인 캐릭터 기록은 클라이언트 데이터에 숨김으로 남음)
    await limit(env, 'l:' + sk, LIMITS.link);
    const b = await readBody(req); const st = [];
    const dropSubs = h => [env.DB.prepare("DELETE FROM accounts WHERE acct_hash=? AND user_id=? AND acct_hash NOT IN (SELECT acct_hash FROM acct_role WHERE user_id=? AND role='main')").bind(h, me.userId, me.userId),
      env.DB.prepare("DELETE FROM acct_role WHERE acct_hash=? AND user_id=? AND role<>'main'").bind(h, me.userId)];
    if (b.all) { // 대표 키 삭제 = 부계정 키·예비 키·금고·부계정 연결 전부 (대표 계정 연결(main)은 데이터 주인 표시라 유지)
      st.push(...['keyvault', 'keyvault2', 'keyreg'].map(t => env.DB.prepare(`DELETE FROM ${t} WHERE user_id=?`).bind(me.userId)));
      st.push(env.DB.prepare("DELETE FROM accounts WHERE user_id=? AND acct_hash NOT IN (SELECT acct_hash FROM acct_role WHERE user_id=? AND role='main')").bind(me.userId, me.userId),
        env.DB.prepare("DELETE FROM acct_role WHERE user_id=? AND role<>'main'").bind(me.userId));
    } else {
      for (const k of [b.key, b.bk]) if (k) st.push(env.DB.prepare('DELETE FROM keyreg WHERE key_hash=? AND user_id=?').bind(await keyHash(env, k), me.userId));
      for (const h of (Array.isArray(b.ahs) ? b.ahs : [b.ah]).filter(h => typeof h === 'string' && /^[0-9a-f]{64}$/.test(h)).slice(0, 10)) st.push(...dropSubs(h));
    }
    if (st.length) await env.DB.batch(st);
    return json(200, { ok: true, accounts: await acctList(env, me.userId) });
  }
  if (p === '/api/logout' && M === 'POST') { await env.DB.prepare('DELETE FROM sessions WHERE token_hash=?').bind(me.th).run(); return json(200, { ok: true }); }
  if (p === '/api/logout-all' && M === 'POST') { const r = await env.DB.prepare('DELETE FROM sessions WHERE user_id=?').bind(me.userId).run(); return json(200, { ok: true, removed: r.meta?.changes || 0 }); }
  if (p === '/api/me' && M === 'GET') {
    const row = await env.DB.prepare('SELECT rev, updated_at, saved_at, size FROM state WHERE user_id=?').bind(me.userId).first();
    const ns = await env.DB.prepare('SELECT COUNT(*) AS n FROM sessions WHERE user_id=?').bind(me.userId).first();
    return json(200, { status: 'ok', admin: me.userId === adminId(env), user: me.userId.slice(0, 8), accounts: await acctList(env, me.userId), sessions: ns?.n || 0, rev: row?.rev || 0, updatedAt: row?.updated_at || 0, savedAt: row?.saved_at || 0, size: row?.size || 0 });
  }
  if (p === '/api/state/meta' && M === 'GET') return json(200, stateOut(await env.DB.prepare('SELECT rev, updated_at, saved_at FROM state WHERE user_id=?').bind(me.userId).first(), false));
  if (p === '/api/state' && M === 'GET') return json(200, stateOut(await stateRow(env, me.userId)));
  if (p === '/api/state' && M === 'PUT') {
    const b = await readBody(req, MAX_BODY);
    const d = b.data;
    if (!d || typeof d !== 'object' || !Array.isArray(d.characters)) throw new HttpError(400, 'bad_state', '데이터 형식이 올바르지 않습니다 (characters 없음)');
    const text = JSON.stringify(stripKeys(d)), now = Date.now(), base = Math.max(0, parseInt(b.baseRev) || 0), upd = Math.max(0, +b.updatedAt || 0);
    if (text.length > MAX_STATE) throw new HttpError(413, 'too_large', `데이터가 너무 큽니다 (최대 ${MAX_STATE / 1024}KB, 지금 ${Math.ceil(text.length / 1024)}KB)`);
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
  if (p.startsWith('/api/admin/')) { // b68: 관리자만 (서버에서 사용자 id 로 확인)
    if (!adminId(env) || me.userId !== adminId(env)) throw new HttpError(403, 'not_admin', '관리자만 쓸 수 있습니다');
    if (p === '/api/admin/users' && M === 'GET') { // b102: 쿼리 3개를 한 번에(batch) — 사용자 수와 상관없이 왕복 1번. ?prices=1 이면 최저가도 같이
      const q = [env.DB.prepare('SELECT u.id, u.created_at, u.last_login, u.sync_click, a.status, a.name, a.world, a.level, a.requested_at, a.decided_at FROM users u LEFT JOIN approval a ON a.user_id=u.id ORDER BY u.created_at LIMIT 500'),
        env.DB.prepare("SELECT s.user_id, s.size, s.saved_at, s.data FROM state s LEFT JOIN approval a ON a.user_id=s.user_id WHERE COALESCE(a.status,'ok')<>'pending'"),
        env.DB.prepare('SELECT user_id, acct_hash, role, created_at FROM acct_role')];
      const wantP = url.searchParams.get('prices') === '1'; if (wantP) q.push(env.DB.prepare("SELECT v FROM meta WHERE k='admin_prices'"));
      const [ur, sr, rr, pr] = await env.DB.batch(q);
      const stOf = new Map((sr.results || []).map(r => [r.user_id, r])), roOf = new Map();
      for (const r of rr.results || []) { if (!roOf.has(r.user_id)) roOf.set(r.user_id, []); roOf.get(r.user_id).push(r); }
      const out = (ur.results || []).map(u => {
        const st = u.status || 'ok', inf = st === 'pending' ? { chars: 0, size: 0, savedAt: 0, alts: [] } : userInfoFrom(stOf.get(u.id), roOf.get(u.id) || []);
        return { id: u.id, status: st, admin: u.id === adminId(env), name: inf.name || u.name || '', world: inf.world || u.world || '', level: inf.level || u.level || 0,
          chars: inf.chars, size: inf.size, lastLogin: u.last_login, syncAt: u.sync_click || 0, requestedAt: u.requested_at || 0, regAt: inf.mainRegAt || u.created_at || 0, alts: inf.alts || [] };
      });
      let prices; if (wantP) { try { prices = pr.results?.[0] ? JSON.parse(pr.results[0].v) : {}; } catch (e) { prices = {}; } }
      return json(200, { users: out, ...(wantP ? { prices } : {}) });
    }
    // b93: 관리자 전용 경매장 최저가 (크롬 확장이 관리자 본인 브라우저에서 측정 → 페이지가 저장). {prices:{item:{p:메소, t:측정 ms}}}. 넥슨 세션·쿠키는 오지 않음
    // b104: maple.ai.kr 아이템 시세 페이지(본섭 일별 시세)를 한 번 받아 최신 날짜 값만 돌려줌 (관리자만). 같은 KST 날짜에 이미 받았으면 저장한 것(바깥 요청 없음)
    // b207: 같은 KST 날 잠금 없앰 — 누를 때마다 ETag 조건부 요청(안 바뀌면 304·저장한 것), 새 날짜면 서버가 admin_prices 도 바로 씀(maiRefresh)
    if (p === '/api/admin/maple-prices' && M === 'GET') {
      const x = await maiRefresh(env, Date.now(), 'admin'), cv = x.cv;
      if (!cv.items) throw new HttpError(502, 'mai_parse', 'maple.ai.kr 시세 표를 읽지 못했습니다');
      const mapped = maiMap(cv.items, cv.fetchedAt); // b208: 짝은 서버 하나 — 페이지는 이걸 그대로 PUT (t=처음 본 시각 → 그 뒤 손으로 넣은 값은 PUT 이 안 덮음)
      return json(200, { date: cv.date, items: cv.items, fetchedAt: cv.fetchedAt, checkedAt: cv.checkedAt, mapped, missing: MAI_KEYS.filter(k => !mapped[k]), unmatched: maiUnmatched(cv.items), mai: maiInfo(cv), ...(x.status !== 'new' ? { cached: true } : {}) });
    }
    if (p === '/api/admin/prices' && M === 'GET') {
      const r = await env.DB.prepare("SELECT v FROM meta WHERE k='admin_prices'").first(); let v = {}; try { v = r ? JSON.parse(r.v) : {}; } catch (e) {}
      const cv = await metaGet(env, 'mai_cache'); // b208: 가장 새 시세 날짜에 값을 받은 키(got) → 시세 등록 창 '시세 정보 없음'
      const mi = maiInfo(cv); return json(200, { prices: v, ...(mi ? { mai: mi } : {}) });
    }
    if (p === '/api/admin/prices' && M === 'PUT') {
      const b = await readBody(req), inp = b && typeof b.prices === 'object' && b.prices ? b.prices : {};
      const r = await env.DB.prepare("SELECT v FROM meta WHERE k='admin_prices'").first(); let cur = {}; try { cur = r ? JSON.parse(r.v) : {}; } catch (e) {}
      for (const [k, o] of Object.entries(inp).slice(0, 200)) {
        if (!/^[a-z_0-9]{1,24}$/.test(k) || !o) continue; const pr = Math.round(+o.p), t = Math.round(+o.t);
        if (!(pr > 0 && pr < 1e15 && t > 0)) continue; if (!cur[k] || cur[k].t <= t) cur[k] = { p: pr, t };
      }
      await env.DB.prepare("INSERT INTO meta (k,v) VALUES ('admin_prices',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(JSON.stringify(cur)).run();
      return json(200, { prices: cur });
    }
    if (p === '/api/admin/decide' && M === 'POST') {
      const b = await readBody(req), uid = String(b.user || ''), act = String(b.action || '');
      if (act === 'kick') { // b78: 강퇴 — 사용자 행과 user_id 로 연결된 모든 표에서 삭제 (acct_role·keyreg 가 지워져 같은 넥슨 계정·키로 새로 가입 가능)
        if (uid === me.userId || uid === adminId(env)) throw new HttpError(400, 'self', '관리자 자신은 강퇴할 수 없습니다');
        const u = await env.DB.prepare('SELECT id FROM users WHERE id=?').bind(uid).first();
        if (!u) throw new HttpError(404, 'no_user', '없는 사용자');
        await env.DB.batch(USER_TABLES.map(t => env.DB.prepare(`DELETE FROM ${t} WHERE user_id=?`).bind(uid)).concat(env.DB.prepare('DELETE FROM users WHERE id=?').bind(uid)));
        return json(200, { ok: true, user: uid, status: 'kicked' });
      }
      const to = { approve: 'ok', unblock: 'ok', reject: 'rejected', block: 'blocked' }[act];
      if (!to) throw new HttpError(400, 'bad_action', '알 수 없는 동작');
      if (uid === me.userId) throw new HttpError(400, 'self', '관리자 자신은 바꿀 수 없습니다');
      const u = await env.DB.prepare('SELECT u.id, a.status, a.requested_at FROM users u LEFT JOIN approval a ON a.user_id=u.id WHERE u.id=?').bind(uid).first();
      if (!u) throw new HttpError(404, 'no_user', '없는 사용자');
      const now = Date.now();
      await env.DB.batch([env.DB.prepare('INSERT INTO approval (user_id,status,requested_at,decided_at) VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET status=excluded.status, decided_at=excluded.decided_at').bind(uid, to, u.requested_at || now, now)]
        .concat(to === 'ok' ? [] : [env.DB.prepare('DELETE FROM sessions WHERE user_id=?').bind(uid)])); // 거절·차단 = 바로 로그아웃 (데이터는 지우지 않음)
      return json(200, { ok: true, user: uid, status: to });
    }
    throw new HttpError(404, 'not_found', '없는 주소');
  }
  if (p === '/api/account' && M === 'DELETE') {
    await env.DB.batch(USER_TABLES.map(t => env.DB.prepare(`DELETE FROM ${t} WHERE user_id=?`).bind(me.userId))
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
  async scheduled(event, env, ctx) { ctx.waitUntil(liveCron(env).catch(e => console.log('liveCron', String(e && e.stack || e)))); const now = Date.now();
    ctx.waitUntil((async () => { let cv = null; try { cv = await metaGet(env, 'mai_cache'); } catch (e) {} const mai = !env.MAI_OFF && (maiDue(now) || !(cv && cv.auto));
      await Promise.all([feedCron(env, now, mai ? FEED_MAX_LIST - 1 : FEED_MAX_LIST).catch(e => console.log('feedCron', String(e && e.stack || e))),
        mai ? maiCron(env, now, cv).catch(e => console.log('maiCron', String(e && e.stack || e))) : null]); })()); }, // b207: 30분마다 maple.ai.kr 시세(그 회차는 공지 목록 조회 1번 덜 = 서브요청 50 안) // b157: 매 1분 라이브 감지 · b170: 넥슨 공지 빠른 감시
};
