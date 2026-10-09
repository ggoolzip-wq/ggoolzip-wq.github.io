-- 보스 캐릭터 관리 동기화 서버 D1 스키마
-- 원본 넥슨 API 키는 어디에도 저장하지 않음. 계정 식별 = sha256(ID_PEPPER + ':' + 넥슨 account_id)
CREATE TABLE IF NOT EXISTS users (
  id          TEXT PRIMARY KEY,          -- 무작위 uuid
  created_at  INTEGER NOT NULL,
  last_login  INTEGER NOT NULL
);
-- 한 사용자(데이터 묶음)에 넥슨 계정 여러 개(본계정·부계정 키) 연결 가능
CREATE TABLE IF NOT EXISTS accounts (
  acct_hash   TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS accounts_user ON accounts(user_id);
-- 로그인 세션: 브라우저는 원본 토큰, 서버는 sha256(토큰)만 보관
CREATE TABLE IF NOT EXISTS sessions (
  token_hash  TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL,
  created_at  INTEGER NOT NULL,
  last_used   INTEGER NOT NULL,
  expires_at  INTEGER NOT NULL,
  label       TEXT
);
CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id);
-- 사용자별 앱 데이터 (JSON 1개, API 키 제거된 상태). rev = 저장할 때마다 +1 (동시 저장 충돌 감지)
CREATE TABLE IF NOT EXISTS state (
  user_id     TEXT PRIMARY KEY,
  rev         INTEGER NOT NULL,
  updated_at  INTEGER NOT NULL,          -- 앱의 S.updatedAt (내용이 실제로 바뀐 시각)
  saved_at    INTEGER NOT NULL,
  size        INTEGER NOT NULL,
  data        TEXT NOT NULL
);
-- 복구용: 최근 10개 저장본
CREATE TABLE IF NOT EXISTS state_history (
  user_id     TEXT NOT NULL,
  rev         INTEGER NOT NULL,
  saved_at    INTEGER NOT NULL,
  data        TEXT NOT NULL,
  PRIMARY KEY (user_id, rev)
);
-- 로그인 시도 제한 (IP 해시별)
CREATE TABLE IF NOT EXISTS rate (
  k           TEXT PRIMARY KEY,
  n           INTEGER NOT NULL,
  reset_at    INTEGER NOT NULL
);
-- 초대 비밀번호를 통과한 기기 표 (원본 표는 브라우저, 서버는 해시만). pass_ver = SITE_PASS_HASH 앞 12자 → 비밀번호를 바꾸면 무효
CREATE TABLE IF NOT EXISTS devices (
  ticket_hash TEXT PRIMARY KEY,
  created_at  INTEGER NOT NULL,
  expires_at  INTEGER NOT NULL,
  pass_ver    TEXT NOT NULL
);

-- 부계정 넥슨 키: 대표 키에서 HKDF 로 만든 AES-GCM 키로 암호화한 것만 보관 (worker.js 참고)
CREATE TABLE IF NOT EXISTS keyvault (
  user_id    TEXT PRIMARY KEY,
  iv         TEXT NOT NULL,
  ct         TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);
