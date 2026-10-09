# 동기화 서버 (Cloudflare Workers + D1)

보스 캐릭터 관리 사이트의 구글 드라이브 동기화를 대신할 무료 서버. **아직 배포·사용 안 함** (사이트의 `SYNC_API_URL` 이 비어 있으면 기존 구글 드라이브 동기화 그대로).

## 구조
- `worker.js` — API (로그인/연결/로그아웃/데이터 읽기·저장/계정 삭제). 설명은 파일 맨 위 주석.
- `schema.sql` — D1 표: users · accounts(넥슨 계정 해시 → 사용자) · sessions(토큰 해시) · state(사용자별 JSON 1개, rev) · state_history(최근 10개) · rate(로그인 시도 제한).
- `wrangler.toml` — 이름 `ggoolzip-sync`, D1 바인딩 `DB`, 허용 사이트(CORS) `https://ggoolzip-wq.github.io` + localhost.

## 보안 요점
- **친구 초대 전용**: 기기마다 처음 한 번 초대 비밀번호(POST /api/invite) → 기기 표(365일, 브라우저 localStorage `mapleBossTracker.svDevice`, 서버는 해시만). 그 뒤에 넥슨 키 로그인. 서버는 비밀번호 해시만 secret `SITE_PASS_HASH` 로 보관 = sha256('ggoolzip-invite:' + 앞뒤 공백 뺀 비밀번호, 대소문자 구분). 없으면 로그인 전부 거부. 시도 제한 IP별 10회/10분.
- 사용량 제한(한 사람이 다른 사람 몫을 못 쓰게): 세션별 읽기 90회/분 · 저장 20회/분, 사용자별 저장 40회/분, 키 연결 10회/10분, 로그인 IP별 30회/10분. 넘으면 429 + Retry-After.
- 넥슨 API 키는 로그인할 때 넥슨 `/maplestory/v1/character/list` 확인에만 쓰고 **저장하지 않음**. 계정 식별 = `sha256(ID_PEPPER:account_id)`.
- 세션 토큰은 브라우저 localStorage, 서버에는 `sha256(토큰)` 만. 365일(쓸 때마다 연장), 로그아웃·모든 기기 로그아웃 가능.
- 저장 데이터에서 `settings.apiKey` · `settings.accounts[].key` 를 서버가 한 번 더 지움.

## 처음 배포 (한 번)
Node 22 이상 필요 (이 박스: `/home/box/.local/node22/bin`).
```bash
cd server && npm install
npx wrangler login --device            # 나온 주소를 열어 코드 승인 (또는 CLOUDFLARE_API_TOKEN 환경 변수)
npx wrangler d1 create ggoolzip-sync   # 출력된 database_id → wrangler.toml 에 붙여넣기
npm run db:init:remote                 # 표 만들기
npx wrangler secret put ID_PEPPER < ~/.config/ggoolzip/ID_PEPPER   # 바꾸면 모든 계정 연결이 끊김, 보관할 것
bash set-site-pass.sh                  # 초대 비밀번호 → SITE_PASS_HASH (env SITE_PASS 또는 입력)
npm run deploy                         # → https://ggoolzip-sync.<계정>.workers.dev
```
그 뒤 사이트에서 미리 써 보기: 브라우저 콘솔에서 `localStorage.setItem('mapleBossTracker.syncApi','https://ggoolzip-sync.<계정>.workers.dev')` 후 새로고침.
모두에게 켜기: `src/app.js` 의 `SYNC_API_URL` 에 주소 → `python3 tools/build.py` → push.

## 초대 비밀번호 바꾸기 (명령 한 줄)
```bash
cd server && bash set-site-pass.sh          # 새 비밀번호를 물어봄(화면에 안 보임), 사본은 ~/.config/ggoolzip/SITE_PASS
# 또는: printf '%s' "ggoolzip-invite:새비밀번호" | sha256sum | cut -d' ' -f1 | npx wrangler secret put SITE_PASS_HASH
```
바꾸면 아직 로그인 안 한 기기는 새 비밀번호를 넣어야 함. 이미 로그인한 기기(세션)는 계속 사용 가능 — 모두 끊으려면 각 기기 로그아웃 또는 D1 `DELETE FROM sessions`.

## 로컬 테스트
`python3 tests/test_server.py` (API) · `python3 tests/test_tracker23.py` (브라우저 2대 동기화). wrangler dev + 로컬 D1 + 넥슨 모의 서버를 스스로 띄움.

## 무료 한도 (2026-10 기준)
Workers 요청 10만/일, D1 저장 5GB · 읽기 500만 행/일 · 쓰기 10만 행/일. 사용자 1명이 하루 종일 탭을 열어 두면 1분마다 확인 1회 ≈ 1,440 요청/일.

## 나중 단계 (아직 구현 안 함)
매일 18:00 KST(09:00 UTC) cron 으로 maplescouter 헥사환산 가져오기 — 캐릭터 1명으로 먼저 시험.
