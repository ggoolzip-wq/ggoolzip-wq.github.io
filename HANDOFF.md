# HANDOFF — 보스 캐릭터 관리 (메이플스토리 KMS 보스 결정석·드롭 관리)

다른 계정/다른 도우미가 이 저장소만으로 작업을 이어갈 수 있도록 정리한 문서입니다.

## 1. 개요
- 목적: 메이플스토리(KMS) 본캐·부캐의 **주간/월간 보스 클리어 체크 → 강렬한 힘의 결정 판매 수익 계산**, 보스 드롭(반지 상자 등) 획득 **개수** 기록, 주간·누적 기록.
- 라이브 주소: **https://ggoolzip-wq.github.io/** (GitHub Pages, `main` 브랜치 루트). 예전 주소 `https://ggoolzip-wq.github.io/maple-boss-tracker/` 는 새 주소로 리디렉트(저장소 `ggoolzip-wq/maple-boss-tracker`의 index.html).
- 서버 없음. **index.html 한 파일**(CSS/JS/아이콘 base64 내장, 외부 라이브러리 없음). 데이터는 브라우저 localStorage + (선택) 구글 드라이브 appDataFolder.
- 사용자: 한국어 사용, 비개발자. 집 PC와 PC방에서 같은 데이터로 사용.

## 2. 저장소 구조
```
index.html              빌드 결과물 (Pages가 그대로 서비스) — 직접 고치지 말고 src/ 수정 후 빌드
favicon.png, apple-touch-icon.png   주황버섯 아이콘
prices.json             결정석 공식 가격 (GitHub Action이 매일 갱신)
README.md               사용자용 사용법 (한국어)
HANDOFF.md              이 문서
.nojekyll               Jekyll 처리 끔
.github/workflows/update-prices.yml   매일 03:17 UTC 가격 갱신 + workflow_dispatch
scripts/nexon_prices.py 공식 업데이트 공지 HTML → 가격표 파서 (표준 라이브러리만)
scripts/update_prices.py  위 파서로 prices.json 갱신 (실패 시 기존 파일 유지, exit 0)
src/app.js              앱 전체 JS (상태·렌더·이벤트·API·드라이브 동기화)
src/body.html           <body> 마크업 (헤더, 모달들)
src/style_v1.css, src/extra.css   스타일 (extra.css가 뒤에 붙음)
src/icons.json          보스 아이콘 base64 (미리 생성됨)
src/itemicons.json      드롭 아이템 아이콘 32px base64 (tools/build_items.py로 생성)
src/logo.json           주황버섯 16/32/64px data URI (tools/build_logo.py로 생성)
src/assets/             아이템·반지·주황버섯 원본 PNG
tools/build.py          src/ → index.html
tools/build_items.py    src/assets → src/itemicons.json (Pillow 필요)
tools/build_logo.py     주황버섯 PNG → logo.json, favicon.png, apple-touch-icon.png
tests/                  Playwright 회귀 테스트(test_tracker4~14), mock_nexon.py, fixtures/(공지 HTML 사본), run_all.sh
```

## 3. 빌드 · 테스트 · 배포
- 빌드: `python3 tools/build.py` → 루트 `index.html` 갱신. (빌드는 표준 라이브러리만 사용)
- 아이콘 재생성(필요할 때만): `pip install pillow` 후 `python3 tools/build_items.py`, `python3 tools/build_logo.py src/assets/orange_mushroom_1210102.png src/logo.json .`
- 테스트: `pip install playwright && python -m playwright install chromium` → `bash tests/run_all.sh` (크롬 지정: `CHROME=/usr/bin/google-chrome`). 결과/스크린샷은 `tests/out/`.
  - 테스트는 `python -m http.server 8787`로 루트를 띄우거나 file:// 로 엽니다. 넥슨 API·구글(GIS/Drive)은 전부 모의(mock) 응답 — 실제 키·개인 데이터 없음.
  - test_tracker4/5/6/7/8/10은 결과를 출력(PASS/값)하는 형식, 9/11/12/13은 `FAILS: []`·`ERRORS: []`로 판정. 모든 테스트에서 JS 오류(ERRORS) 0이어야 함.
  - test13 = 현재 UI 구조(＋추가 통합 모달, 헤더 동기화, ☁ 메뉴) 핵심 테스트.
  - test14 = 일퀘 현황·길드 현황 탭(탭 순서·ㅡ 구분선, 항목/상태/잠금, 완료 덮개·호버, 편집(전체/캐릭터별/카드 숨김)·저장, 10분 캐시·자동 갱신, 길드 랭킹 어제 대체, 본캐 수로, 375/320px). `MBT_SHOTDIR=폴더`면 tab_daily.png·tab_daily_hover.png·tab_guild.png 를 그 폴더에도 저장. mock_nexon.py에 실제 응답 이름 그대로의 daily/weekly_contents와 /ranking/guild 모의 응답, 호출 기록(CALLS)·GUILD_EMPTY 추가.
  - test12 = 12/12 완료 덮개(문구·두 줄 배치·카드 안 맞춤·호버/클릭/터치 통과). `MBT_SHOT=경로`를 주면 사이드바 스크린샷을 그 경로에도 저장.
  - 주의: 8787 포트를 다른 서버(예: 로컬 개발 사본 /workspace/maple-boss-tracker)가 이미 쓰고 있으면 테스트가 그쪽 파일을 엽니다 → 개발 사본도 같은 index.html로 맞춘 뒤 테스트.
- 배포: `main`에 일반 push(강제 push 금지) → Pages가 1분 내 반영. 확인: `curl -s https://ggoolzip-wq.github.io/ | grep '<title>'`.
- Action이 prices.json을 커밋하므로 push 전 `git pull --rebase`.

## 4. 데이터 모델 · 저장소 키
- localStorage
  - `mapleBossTracker.v1` — 앱 상태 S (version 5)
  - `mapleBossTracker.officialPrices` — 마지막으로 받은 prices.json 캐시
  - `mapleBossTracker.sched` — 캐릭터별 스케줄러 요약 캐시 `{charId:{date, level, items{cer…xmp:{st,now,max,reg,name}}, guild{suro,flag,mission}, at, ok, msg, errAt}}` (일퀘·길드 탭용, 드라이브 동기화 안 함)
  - `mapleBossTracker.guild` — 길드 랭킹 캐시 `{date, t1, t2(랭킹 행), at, ok, msg}`
  - `mapleBossTracker.gdrive` — 드라이브 동기화 메타 `{on, base, fileId, lastSave, lastLoad}`
  - sessionStorage `mapleBossTracker.gtoken` — 구글 액세스 토큰(탭 세션 동안만)
  - 키 이름·드라이브 파일명은 기존 데이터 호환을 위해 **바꾸지 말 것** (예전 이름 maple-boss-tracker 그대로).
- S 구조(요약): `characters[]`(id, name, job, level, world, ocid, accId, isMain, image, exp, `bosses{slot:{enabled,diff,party}}`, `weekly{slot:true}`, `monthly{slot:week}`, `auto`, `sync`, `drops{'slot|item':n}`, `mdrops`, `dropOut{'slot|item':['r4'|'c4'|'x']}`, `mdropOut`), `history[]`(주간 기록: week,total,cleared,crystals,items,perChar[{id,name,meso,count,bosses,items{'slot|item#N':n},outcomes}]), `monthHistory[]`, `startWeek`, `period{week,day,month}`, `worldOrder`, `dq{off{항목:1}, charOff{charId:{항목:1}}, hide{charId:1}}`(일퀘 현황 표시 설정, load()에서 기본값 보정), `activeId`, `theme`, `updatedAt`, `settings{accounts[{id,label,key,status}], autoSync, autoEnable, lastSync, weeklyLimit:12, monthlyLimit:1, prices:{}}`.
- 초기화: 주간 = 목요일 00:00 KST, 월간 = 1일 00:00 KST. `checkResets()`가 지난 기간을 history/monthHistory로 보관(그 시점 파티 인원으로 라벨 고정, 키 `item#N`).
- 마이그레이션은 `load()/migrate()/normChar()`에서 처리(예전 필드 삭제: apiMode, driveKeys, worldLimit, dropParty, priceSource, 수동 가격 등). 새 기능은 항상 기존 데이터가 깨지지 않게 추가.
- 구글 드라이브: 파일 `maple-boss-tracker.json` (appDataFolder, 범위 `drive.appdata`). 내용 `{app, format:1, savedAt, updatedAt, characters(개수), withKeys:true, data:S(API 키 포함)}`.
  - 로그인 시: 드라이브만 있음→불러오기, 이 PC만→업로드, 둘 다 다르면 시각·캐릭터 수를 보여 주고 한 번 질문(드라이브 불러오기 / 이 PC로 덮어쓰기). 이후 변경 5초 뒤·페이지 숨김 시 자동 저장, 저장 전 원격 updatedAt 확인으로 덮어쓰기 방지.

## 5. 넥슨 Open API (https://openapi.nexon.com)
- 브라우저에서 `https://open.api.nexon.com` **직접 호출**(헤더 `x-nxopen-api-key`). 프록시 없음.
- 사용 엔드포인트: `/maplestory/v1/ranking/guild`(길드 탭, date 필수, ranking_type 1 플래그·2 지하수로, guild_name 필터, 키 아무거나), `/maplestory/v1/character/list`(키 소유 계정의 캐릭터 목록, account_list 여러 개 합침), `/maplestory/v1/id`(이름→ocid), `/maplestory/v1/character/basic`(레벨·직업·이미지·경험치), `/maplestory/v1/scheduler/character-state`(메이플 스케줄러: 보스 complete_flag/clear_flag → 자동 체크).
- 규칙: character/list·scheduler는 **그 키를 발급한 넥슨 계정의 캐릭터만** 조회 → 계정마다 키 등록(accounts[]), 캐릭터는 accId로 키 연결. 스케줄러는 2026-06-25 이후 접속한 캐릭터만. 파티 인원은 API에 없음(수동).
- 오류는 HTTP 상태+코드(OPENAPI00001~00011)+서버 메시지+한국어 안내로 표시.
- 자동 동기화: 페이지가 열려 있으면 15분마다(옵션), 헤더 **동기화** 버튼으로 수동.
- 스케줄러 호출은 `fetchSched(c,a)` 한 곳 → 응답을 `applyScheduler`(보스 자동 체크)와 `schedSummary`(일퀘·길드 요약 캐시)에 같이 사용. 동기화도 이 함수를 씀.
- 일퀘/길드 탭 자동 갱신: `tabTick()`(탭 열 때·60초 타이머·화면 복귀). 열린 탭에 필요한 캐릭터만, 캐시가 10분(DQ_TTL_MS) 넘었거나 날짜가 바뀐 것만 순서대로(`nx`의 250ms 간격) 호출. 동기화 중이면 건너뜀, 호출량 초과(OPENAPI00007/429)면 10분 쉼. 숨긴 캐릭터는 호출 안 함.
- 길드 랭킹: 09:30 KST 이후면 오늘 → 비었거나 오류면 어제(그 전엔 바로 어제). 30분 캐시(오늘 자료면 90분). 고정값 `GUILD={name:'봉사활동', world:'스카니아'}`(src/app.js).

### 스케줄러 실제 응답 (2026-10-09, 개발 키로 실측 — 이름 매칭 근거)
- daily_contents 일일 퀘스트(type quest): `[일일 퀘스트] 세르니움 조사`, `[일일 퀘스트] 호텔 아르크스 주변 청소`, `[일일 퀘스트] 오디움 일대 탐사`, `[일일 퀘스트] 도원경 오염 정화`, `[일일 퀘스트] 아르테리아 잔당 처치`, `[일일 퀘스트] 카르시온 복구 지원`, `[일일 퀘스트] 탈라하트 고대신의 힘 조사`, `[일일 퀘스트] 기어드락 크로노스의 잔재 수집` (그 외 소멸의 여로~리멘 9개는 표시 안 함). quest_state "2" 완료 / "1" 진행 중(now/max 예: 0/100) / "0" 기타(레벨 미달·미수락).
- daily_contents `몬스터파크`(type contents, now/max = n/14 — 14는 월드 기준, 캐릭터당 하루 7회라 앱은 7회 이상이면 완료).
- 익스트림 몬스터파크는 일일 항목이 없고 weekly_contents `[몬스터파크] 익스트림 몬스터파커에 도전해보겠나?`(주간 퀘스트, now/max n/5)만 있음 → 앱은 '주간 n/5', quest_state 2 또는 n≥max면 완료.
- 지하 수로: weekly_contents `[길드] 지하 수로` now_count = 이번 주 점수(max_count 0). 같은 형식으로 `[길드] 플래그 레이스`, `[길드] 주간 미션 포인트`(now/10).
- 레벨 260 미만 등 스케줄러에 등록 항목이 없는 캐릭터는 daily_contents가 빈 배열.
- 앱의 지역별 수행 레벨(DQ_ITEMS.lv): 260/265/270/275/280/285/290/295 — 레벨 미달은 칸 대신 🔒 줄. 기어드락 295는 실측상 285·288 캐릭터 모두 state 0이라 일관되지만 공식 확인은 안 됨.

## 6. 결정석 가격 자동 갱신
- `.github/workflows/update-prices.yml`: 매일 03:17 UTC(12:17 KST) + 수동 실행. `scripts/update_prices.py`가 https://maplestory.nexon.com/News/Update 목록을 최신순으로 훑어 '강렬한 힘의 결정' 가격표가 있는 공지를 찾아 `prices.json`(rows: boss/old/new/effective, source url/title/date, checkedAt, fetchedAt) 갱신. 내용이 바뀌었을 때만 커밋(가격 동일하면 7일마다 checkedAt만).
- 사이트는 로드 시 `./prices.json?d=날짜`를 받아 보스·난이도 이름 매칭 후 적용. 적용일(effective)이 미래면 그날까지 대기. 실패 시 캐시/내장 가격(2026-09-17 공지) 사용.
- 가격은 **보스당 한 줄, 수정 UI 없음**, 출처 라벨 없음. 오른쪽 '결정석 가격' 카드(강렬한 힘의 결정 (주간) 아이콘, 싼 순서)에 작게 '마지막 확인 날짜'.
- 테스트 픽스처: `tests/fixtures/`(공식 공지 813 사본, 46행). 이 작업 박스에서는 nexon.com 접속이 막혀 실서버 확인 불가였음 — Action 실행 결과는 GitHub Actions 탭에서 확인.

## 7. 구글 OAuth
- 클라이언트 ID: `463037848804-2ut2277bsc2cf4vpf4qb0rl7hlt9ur8c.apps.googleusercontent.com` (src/app.js 상단 `GOOGLE_CLIENT_ID`). 승인된 JavaScript 원본: `https://ggoolzip-wq.github.io` (경로 없음).
- Google Identity Services 토큰 모델(`accounts.google.com/gsi/client`) + Drive REST v3, 범위 `https://www.googleapis.com/auth/drive.appdata`(비민감 범위).
- 동의 화면은 **테스트 모드**일 가능성 → 사용할 구글 계정을 'Google 인증 플랫폼 > 대상 > 테스트 사용자'에 추가해야 함. '확인되지 않은 앱' 화면은 '계속'으로 진행. access_denied/popup_closed 등은 한국어 안내 모달.
- https 또는 localhost에서만 로그인 가능(file://에서는 ☁ 메뉴에 안내).

## 8. 사용자가 정한 동작·취향 (변경 시 사용자 확인 필요)
- **단순한 UI** 선호. 설정 탭 없음. JSON 백업(내보내기/가져오기) 없음. 로컬 프록시(serve.py) 없음.
- 일일 보스 없음. 처치 한도 고정: 캐릭터당 **주간 12 / 월간 1**(UI 없음). 월드 판매 한도 계산 없음.
- **주간 수익에서 월간 보스(검은 마법사) 제외**, '이번 달 월간 보스'로 따로 표시·월간 기록에 보관.
- 수익 = 결정석만. **드롭은 개수만 기록**(메소 환산 없음). 칩 클릭 +1, − 배지/우클릭 −1.
- 반지 상자(녹옥/홍옥/흑옥/백옥/생명) 클릭 → 결과 선택 모달 '리스트레인트 링 4레벨 / 컨티뉴어스 링 4레벨 / 둘 다 못 먹었어요'(리4/컨4/꽝). 리4·컨4는 **불꽃놀이 + 축하드립니다!**. X/Esc는 기록 안 함.
- 파티 표시: 1인은 이름만, 파티는 '아이템 (N인 분배)'. 이번 주/달 기록은 **현재 파티 인원 설정을 따름**, 기록 보관(초기화) 후에는 고정. 모든 화면에서 같은 형식·×개수.
- 결정석 가격: 보스당 단일 가격, 출처 라벨 없음, 자동 갱신만.
- 사이드바: 캐릭터 카드에 레벨 항상 표시. ('완' 도장은 사용자 요청으로 **삭제됨**.)
- 이번 주 12/12인 캐릭터 카드: **반투명 검정 덮개**(rgba(0,0,0,.55), 카드 모서리와 동일) + 가운데 '★ 이번 주 보스 완료'(★ 노랑, 글자 흰색 굵게).
  월간 보스(검은 마법사)를 **선택해 둔 캐릭터가 이번 달 아직 안 잡았으면** 그 **아래 둘째 줄**에 빨간 원형 (!) + 빨간 '검마 격파 필요'(괄호 없음, 가운데 정렬, 조금 작은 글씨 .74rem) 표시(선택 안 했으면 경고 없음 → 한 줄).
  두 줄 모두 카드 안에 들어가야 함(데스크톱·375px·320px 모바일에서 test12가 확인). (2026-10-09 변경: 예전엔 같은 줄에 '(검마 격파 안함)')
  마우스를 올리면 덮개가 0.15초 동안 사라짐(@media hover). 덮개는 pointer-events:none → 클릭·✎·▲▼·드래그 정렬 그대로. 12 미만/주간 초기화 시 사라짐. 코드: src/app.js doneOverlay(), extra.css .dov*.
- 헤더: 로고 = 메이플 **주황버섯**(몹 1210102) 실제 게임 이미지(파비콘 동일), **동기화** 버튼(아이콘+텍스트, 마지막 시각은 툴팁, 동기화 중 아이콘 회전), **☁** 버튼 → 작은 메뉴(상태·구글 로그인/로그아웃·지금 저장).
- 캐릭터 추가: 사이드바 **+ 추가** 하나로 통합 모달 — 여러 넥슨 API 키 관리(이름, 가린 키, 캐릭터 목록, 삭제, + API 키 추가) → 바로 그 계정 캐릭터 목록(검색·필터·여러 명 선택 추가), 아래 '이름으로 직접 추가'. 기존 캐릭터는 ✎로 수정.
- **넥슨 API 키는 드라이브에 기본 저장**(앱 전용 숨김 폴더). 체크박스 없음.
- **'로그아웃 후 이 PC 데이터 지우기' 버튼 없음**(사용자 결정: PC방 PC는 종료 시 자동 초기화). ☁ 메뉴엔 일반 로그인/로그아웃만.
- 사이트 이름 '보스 캐릭터 관리'. 주소는 루트(ggoolzip-wq.github.io).
- 상단 탭: 보스 체크 · 수익 요약 · 주간 기록 · 총 수익 · **ㅡ(짧은 가로 구분선)** · **일퀘 현황** · **길드 현황**. 사이드바 캐릭터를 누르면 보스 체크 탭으로 이동(주간 기록·총 수익과 같음).
- 일퀘 현황: 설정 탭 없이 탭 안 **편집** 토글 하나로 표시 항목(전체 칩)·캐릭터별 항목(칸 클릭)·캐릭터 카드 숨김(👁) 설정. 완료 칸 = 보스 완료 덮개와 같은 rgba(0,0,0,.55) 덮개 + 지역명/✓ 완료, 마우스를 올리면 사라짐(밑글자는 덮개가 있을 때 숨김). 코드: src/app.js renderDaily()/dqCell(), extra.css .dq*.
- 길드 현황: 길드/월드는 고정값(설정 없음, 사용자가 바꿔 달라고 하면 GUILD 상수 수정). 본캐 목록 = isMain 캐릭터(현재 UI는 본캐 1명만 지정 가능).

## 9. 알려진 한계 · 주의
- 실제 구글 로그인·실제 넥슨 키 흐름은 자동 테스트로 확인 불가(모의 응답으로 검증). 실서버 동작은 사용자 확인으로 검증해 옴.
- 공식 공지 HTML 구조가 바뀌면 파서가 0행 → Action은 기존 prices.json 유지(경고만). 이때 scripts/nexon_prices.py 수정 필요.
- 공지 표에 없는 보스 가격은 내장 기본값(src/app.js PRICE_CONFIG) 사용.
- GitHub 무료 계정: 60일간 커밋이 없으면 예약 Action이 자동 비활성화될 수 있음(Actions 탭에서 다시 켜기).
- index.html은 아이콘 base64 때문에 약 365KB.
- 몬스터파크 now_count가 캐릭터 기준인지 월드 기준인지 API 문서에 없음(실측 두 캐릭터 모두 0이라 미확인). 앱은 캐릭터 기준으로 보고 7회 이상이면 완료 처리.
- 스케줄러 일퀘·몬파 정보는 넥슨이 '접속 중·접속 종료 시'에만 갱신 → 게임 안에서 막 끝낸 퀘스트는 접속을 끊기 전엔 반영이 늦을 수 있음.
- 320px 화면에서 API 키가 있으면(동기화 버튼 표시) 헤더 버튼이 약 20px 넘침 — 이번 작업 전부터 있던 현상(헤더는 손대지 않음).
- 드롭 목록(src/app.js DROPS, RING_DROPS)은 커뮤니티 자료 기준(반지 상자 분류: 2026-09 기준).

## 10. 보류 중인 아이디어
- **테스트 서버 공지의 가격을 '다음 패치 예정 가격'으로 표시** — 사용자 결정 대기 중(아직 구현 안 함).

## 11. 변경 기록
- 2026-10-09: 상단 탭에 ㅡ 구분선 + **일퀘 현황**·**길드 현황** 탭 추가. 스케줄러 호출을 fetchSched()로 통일(동기화·탭 공용, 요약 캐시 mapleBossTracker.sched). 일퀘: 그란디스 8지역 일퀘·몬파·익몬(주간), 완료 덮개·호버, 레벨 잠금 줄, 편집(전체/캐릭터별/카드 숨김 → S.dq), 10분 자동 갱신. 길드: 봉사활동(스카니아) 지하 수로·플래그 레이스 점수·순위·레벨·마스터(오늘→어제 대체), 본캐 이번 주 지하 수로·플래그·주간 미션. test14 추가, mock 확장, run_all에 14 포함.
- 2026-10-09: 완료 덮개 경고를 둘째 줄로 분리 — 1줄 '★ 이번 주 보스 완료', 2줄 빨간 (!) '검마 격파 필요'(괄호 제거). 글씨 .82rem/.74rem, (!) 13px. test12 갱신(문구, 두 줄·가운데·카드 안 맞춤 데스크톱/375/320px, 터치 탭 통과).
