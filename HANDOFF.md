# HANDOFF — 보스 캐릭터 관리 (메이플스토리 KMS 보스 결정석·드롭 관리)

다른 계정/다른 도우미가 이 저장소만으로 작업을 이어갈 수 있도록 정리한 문서입니다.

## 2026-10-10 배치 (b28)
- 취소/저장 비교: `pendSig()` (파티 숫자화·빈 드롭 제거) — 원인: 저장 데이터에 `party` 키가 없거나 문자열 '1' → 1→2→1 후 `party:1`이 새로 생겨 서명 불일치. `normChar`가 이제 party 를 항상 숫자로.
- `DROPS_OFF`: 보스 장신구(파풀라투스 마크 제외)·여명 세트 = 표 끝 회색 칩(.drop.off, 클릭 불가).
- API/API 자동 표시, 보스 행 클리어 체크 아이콘 삭제. '월간 보스 (따로 합산)' 두 줄.
- 추가 모달: 키 가림/등록 N명/캐릭터 목록 버튼/계정 캐릭터 N명 줄/메이플 계정N 표시 삭제, '✔ 등록 완료', 행 클릭 = 그 계정 목록, '캐릭터 추가' 버튼은 월드 선택 옆.
- 탭: '캐릭터 별 기록' 삭제, '총 수익' → '수익 분석'. 캐릭터별 누적 본캐 초상 = 왼쪽 목록과 같은 `avatar()`. '에픽빔 본 횟수' (x숫자 오로라 그라데이션).
- 칠흑 상자: `openChaos()` 모달(7종) → `dropOut[key]=['cb:<item>']` (반지 결과와 같은 자리), 기록은 `[상자 아이콘] - 이름`.
- 획득 축하: 모든 드롭 획득 시 `celebrate(null,item)` + `iconBurst(src)` (아이콘 42개 CSS transform, 2.1초 후 제거, reduced-motion 이면 생략). 반지=결과 아이콘, 칠흑=고른 장신구.
- 썬데이: `sunLabel()` — 게시일(`sunday.date`) < 이번 주 월요일 00:00 KST 이면 '저번 주 혜택' (1분마다 재확인).

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
sunday.png              최신 썬데이 메이플 이미지에서 '이벤트 기간~혜택' 부분만 자른 것 (Action 의 OCR 단계가 새 글마다 덮어씀)
feed.json               소식 피드 (GitHub Action이 5분마다 확인, 새 글이 있을 때만 커밋) — 10장 참고
README.md               사용자용 사용법 (한국어)
HANDOFF.md              이 문서
.nojekyll               Jekyll 처리 끔
.github/workflows/update-prices.yml   매일 03:17 UTC 가격 갱신 + workflow_dispatch
.github/workflows/sunday-watch.yml    매일 09:45/09:50 KST 예약 → 10:00~10:20 KST 5초마다 썬데이 새 글 확인(scripts/sunday_watch.py) + workflow_dispatch(test_minutes, pretend_new)
.github/workflows/update-feed.yml     5분마다 소식 수집(scripts/update_feed.py) + workflow_dispatch, secret NEXON_API_KEY(+ 예비 NEXON_API_KEY2) 사용
scripts/sunday_watch.py 썬데이 새 글 감시(10:00~10:20 KST, 5초 간격, API 우선·홈페이지 대체, 찾으면 바로 처리) — sunday-watch.yml 에서 실행
scripts/sunday_ocr.py   썬데이 이미지 OCR(혜택 글자) + 자르기 → sunday.png (Action 에서 새 썬데이 글일 때만, tesseract·Pillow 필요)
scripts/update_feed.py  소식 수집기 4종(사료감지·패치내역·테섭·마빡도로시) → feed.json (표준 라이브러리만)
scripts/nexon_prices.py 공식 업데이트 공지 HTML → 가격표 파서 (표준 라이브러리만)
scripts/update_prices.py  위 파서로 prices.json 갱신 (실패 시 기존 파일 유지, exit 0)
src/app.js              앱 전체 JS (상태·렌더·이벤트·API·드라이브 동기화)
src/body.html           <body> 마크업 (헤더, 모달들)
src/style_v1.css, src/extra.css   스타일 (extra.css가 뒤에 붙음)
src/icons.json          보스 아이콘 base64 (미리 생성됨)
src/itemicons.json      드롭 아이템 아이콘 32px base64 (tools/build_items.py로 생성)
src/dqicons.json        일퀘 현황 칸 아이콘 40px base64 (tools/build_dqicons.py로 src/assets/dqicons/*.png에서 생성, build.py가 /*__DQ_ICONS__*/ 자리에 넣음)
src/logo.json           주황버섯 16/32/64px data URI (tools/build_logo.py로 생성)
src/assets/             아이템·반지·주황버섯 원본 PNG
tools/build.py          src/ → index.html
tools/build_items.py    src/assets → src/itemicons.json (Pillow 필요)
tools/build_logo.py     주황버섯 PNG → logo.json, favicon.png, apple-touch-icon.png
tests/                  Playwright 회귀 테스트(test_tracker4~15), test_feed_minor.py(피드 수집기 마이너 패치, 네트워크 없음), mock_nexon.py, fixtures/(공지 HTML 사본), run_all.sh
```

## 3. 빌드 · 테스트 · 배포
- 빌드: `python3 tools/build.py` → 루트 `index.html` 갱신. (빌드는 표준 라이브러리만 사용)
- 아이콘 재생성(필요할 때만): `pip install pillow` 후 `python3 tools/build_dqicons.py`(일퀘 아이콘), `python3 tools/build_items.py`, `python3 tools/build_logo.py src/assets/orange_mushroom_1210102.png src/logo.json .`
- 테스트: `pip install playwright && python -m playwright install chromium` → `bash tests/run_all.sh` (크롬 지정: `CHROME=/usr/bin/google-chrome`). 결과/스크린샷은 `tests/out/`.
  - 테스트는 `python -m http.server 8787`로 루트를 띄우거나 file:// 로 엽니다. 넥슨 API·구글(GIS/Drive)은 전부 모의(mock) 응답 — 실제 키·개인 데이터 없음.
  - test_tracker4/5/6/7/8/10은 결과를 출력(PASS/값)하는 형식, 9/11/12/13은 `FAILS: []`·`ERRORS: []`로 판정. 모든 테스트에서 JS 오류(ERRORS) 0이어야 함.
  - test13 = 현재 UI 구조(＋추가 통합 모달, 🔄 동기화 버튼, ☁ 메뉴) 핵심 테스트. test22 = 페이지 열 때 자동 동기화(3초 간격)·🔄 버튼 위치/모바일·예전 15분 자동 동기화 제거.
  - test14 = 일퀘 현황·길드 현황 탭(탭 순서·ㅡ 구분선, 항목/상태/잠금, 완료 덮개·호버, 편집(전체/캐릭터별/카드 숨김)·저장, 10분 캐시·자동 갱신, 길드 랭킹 어제 대체, 본캐 수로, 375/320px). `MBT_SHOTDIR=폴더`면 tab_daily.png·tab_daily_hover.png·tab_guild.png 를 그 폴더에도 저장. mock_nexon.py에 실제 응답 이름 그대로의 daily/weekly_contents와 /ranking/guild 모의 응답, 호출 기록(CALLS)·GUILD_EMPTY 추가.
  - test16 = 썬데이 카드(잘린 sunday.png 사용·없으면 원본, 혜택 여러 줄, 라이트박스: 원본 이미지·가운데·화면 맞춤·공지 보기 링크·확대·Esc/✕/바깥 클릭 닫기·포커스 복귀·320px; 모의 feed.json·긴 세로 모의 이미지: 위치, '☀ 썬데이' 머리글·노란 아이콘, 링크, 혜택 줄(없으면 제목), 1280x800·1920x1080 세 탭에서 1/3:2/3·페이지 길이 그대로·화면 안·contain, 낮은 창, 390/320 모바일, 글 없음 안내, 새 글 교체·같은 데이터 재사용). 스크린샷 sun_*.png. test_feed_sunday.py = 수집기(API 우선·HTML 대체·혜택 추출, 네트워크 없음).
  - test15 = 소식 피드 카드(모의 feed.json, 패치 탭에 마이너 패치 2건 섞임: 위치, 탭·안 읽은 수, N 배지·읽음 유지, 사료 기한·만료 흐림, 한 줄 말줄임, 쪽 번호 5개+‹›, 탭 전환 시 1쪽, 수집 실패 표시, 1280x800·1920x1080 모든 탭에서 카드 때문에 페이지가 길어지지 않음·스크롤해도 화면 안, 390/320px 모바일). 스크린샷 feed_card*.png.
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
  - `mapleBossTracker.feedSeen` — 소식 카드에서 읽은(클릭한) 글 id 배열 (feed.json에 남아 있는 것만 보관, 드라이브 동기화 안 함)
  - `mapleBossTracker.gdrive` — 드라이브 동기화 메타 `{on, base(맞춘 시점 이 PC updatedAt), rU(맞춘 시점 드라이브 updatedAt), fileId, lastSave, lastLoad}`
  - `mapleBossTracker.gdbase` — 마지막으로 드라이브와 맞춘 시점의 내용(키 제외) = 3-way 병합 기준 (2026-10-10 추가, 로그아웃 시 삭제)
  - sessionStorage `mapleBossTracker.gtoken` — 구글 액세스 토큰 `{t, e(만료 시각)}` (탭 세션 동안만, 1시간 — 같은 탭 새로고침은 다시 로그인 없이 사용. PC방 공용 PC 라 localStorage 에는 두지 않음)
  - 키 이름·드라이브 파일명은 기존 데이터 호환을 위해 **바꾸지 말 것** (예전 이름 maple-boss-tracker 그대로).
- S 구조(요약): `characters[]`(id, name, job, level, world, ocid, accId, isMain, image, exp, `bosses{slot:{enabled,diff,party}}`, `weekly{slot:true}`, `monthly{slot:week}`, `auto`, `sync`, `drops{'slot|item':n}`, `mdrops`, `dropOut{'slot|item':['r4'|'c4'|'x']}`, `mdropOut`), `history[]`(주간 기록: week,total,cleared,crystals,items,perChar[{id,name,meso,count,bosses,items{'slot|item#N':n},outcomes}]), `monthHistory[]`, `startWeek`, `period{week,day,month}`, `worldOrder`, `dq{off{항목:1}, charOff{charId:{항목:1}}, hide{charId:1}}`(일퀘 현황 표시 설정, load()에서 기본값 보정), `activeId`, `theme`, `updatedAt`, `settings{accounts[{id,label,key,status}], autoSync, autoEnable, lastSync, weeklyLimit:12, monthlyLimit:1, prices:{}}`.
- 초기화: 주간 = 목요일 00:00 KST, 월간 = 1일 00:00 KST. `checkResets()`가 지난 기간을 history/monthHistory로 보관(그 시점 파티 인원으로 라벨 고정, 키 `item#N`).
- 마이그레이션은 `load()/migrate()/normChar()`에서 처리(예전 필드 삭제: apiMode, driveKeys, worldLimit, dropParty, priceSource, 수동 가격 등). 새 기능은 항상 기존 데이터가 깨지지 않게 추가.
- 구글 드라이브: 파일 `maple-boss-tracker.json` (appDataFolder, 범위 `drive.appdata`). 내용 `{app, format:1, savedAt, updatedAt, characters(개수), withKeys:true, data:S(API 키 포함)}`.
  - **동기화 방식 (2026-10-10 개편 — '어느 데이터를 쓸까요?'가 계속 뜨던 버그 수정)**
    - 원인이었던 것: ① `save()`가 S 의 **아무 값**이나 바뀌어도 updatedAt 을 갱신 → 자동 동기화(5분마다 lastSync·캐릭터 sync 시각·이미지·EXP), 캐릭터 탭 클릭(activeId), 테마, 자정 period 변경만으로도 '수정됨'이 되어 드라이브에 저장. ② 비교(gdNorm)에 캐릭터 sync/image/exp·activeId 가 남아 있어 두 기기 내용이 항상 '다름'. ③ 판단이 시각(updatedAt vs base)뿐이라 두 기기가 모두 열려 있거나(집 PC 켜 둔 채 PC방) 시작할 때 자동 동기화가 먼저 돌면 매번 '둘 다 바뀜'→질문. 고른 뒤에도 다음 자동 동기화에서 또 같은 상황 → 반복.
    - 이제: `contentSig(d)` = `gdStrip`(GD_LOCAL_RE 경로 제외) + 키. 제외 = **기기 전용**(theme, activeId, period, updatedAt, version, startWeek, settings.lastSync/prices…) + **자동 갱신 값**(characters[].sync/image/exp, settings.accounts[].key/status). `save()`는 contentSig 가 바뀔 때만 updatedAt 갱신·드라이브 저장 예약(localStorage 는 항상 저장).
    - `gdSync(remote)`(연결 시·저장 전 원격이 바뀌었을 때·탭 복귀/1분마다 `gdPull`(메타데이터만 조회)): 이 PC 비었으면 드라이브 불러오기. `GD_BASE_KEY` 의 base 가 있으면 **3-way 병합 `gdMerge`**: 한쪽만 바꾼 항목은 그쪽 값, 캐릭터·계정은 id / 기록은 week·month 로 짝지음, 추가·삭제 반영(삭제 vs 수정이면 수정본 유지), 기기 전용·자동 갱신 값은 이 PC 값(키는 이 PC 에 없으면 드라이브 값). API 값(level/job/world/ocid/accId)·지난 기록 요약은 충돌이어도 묻지 않음. 병합 전 양쪽을 `rollPeriod`로 이번 주·월로 넘겨서 지난 주 체크가 이번 주로 섞이지 않게 함.
    - **질문은 진짜 충돌(같은 항목을 양쪽에서 다르게 수정)일 때만** — 충돌 항목 이름(예: '부캐 · 이름')을 보여 주고 '드라이브 쪽 값으로 / 이 PC 쪽 값으로'; 나머지 변경은 그대로 합쳐짐. 고르면 결과를 저장하고 base 갱신 → 다시 안 물음. '나중에'(✕)로 닫으면 헤더 [☁ 선택 필요]로 다시 열기(그동안 자동 저장 멈춤).
    - base 가 없는 경우: 예전 버전 메타(base 시각만)면 한쪽만 바뀐 경우 그쪽, 둘 다면 **묻지 않고 합침**(겹치는 값은 최근 수정한 쪽, 한쪽에만 있는 캐릭터·체크는 유지 — 다른 PC 에서 지운 캐릭터가 한 번 되살아날 수는 있음). 메타도 없는 처음 연결 + 내용이 다르면 예전처럼 한 번 '통째로 고르기'.
    - 저장(`gdPush`) 전 원격 updatedAt 이 rU 와 다르면(다른 기기가 저장함) 덮어쓰지 않고 gdSync 로 합친 뒤 저장. 페이지 숨김 시 빠른 저장(keepalive)은 확인 없이 저장하지만, 다른 기기는 다음 저장/복귀 때 base 기준으로 합치므로 잃지 않음.
    - 테스트: test10(기존 시나리오 + 다른 항목 동시 수정 → 자동 병합, 같은 항목 → 질문·나중에·헤더로 다시 열기), **test17**(두 기기 집/PC방 모의 드라이브: 자동 갱신 값만 바뀜 → 저장 안 함, 서로 다른 수정·추가·삭제 자동 병합, 진짜 충돌 1회 질문 후 재발 없음, 새로고침 후 질문 없음, 예전 메타 자동 병합, 지난 주 체크 롤오버).

## 5. 넥슨 Open API (https://openapi.nexon.com)
- 브라우저에서 `https://open.api.nexon.com` **직접 호출**(헤더 `x-nxopen-api-key`). 프록시 없음.
- 사용 엔드포인트: `/maplestory/v1/ranking/guild`(길드 탭, date 필수, ranking_type 1 플래그·2 지하수로, guild_name 필터, 키 아무거나), `/maplestory/v1/character/list`(키 소유 계정의 캐릭터 목록, account_list 여러 개 합침), `/maplestory/v1/id`(이름→ocid), `/maplestory/v1/character/basic`(레벨·직업·이미지·경험치), `/maplestory/v1/scheduler/character-state`(메이플 스케줄러: 보스 complete_flag/clear_flag → 자동 체크).
- 규칙: character/list·scheduler는 **그 키를 발급한 넥슨 계정의 캐릭터만** 조회 → 계정마다 키 등록(accounts[]), 캐릭터는 accId로 키 연결. 스케줄러는 2026-06-25 이후 접속한 캐릭터만. 파티 인원은 API에 없음(수동).
- 오류는 HTTP 상태+코드(OPENAPI00001~00011)+서버 메시지+한국어 안내로 표시.
- 자동 동기화(넥슨 API 전용 syncAll — 계정별 캐릭터 목록·레벨/이미지·스케줄러 보스 클리어 체크; 구글 드라이브와 무관, 로그인 창 없음): **페이지를 열거나 새로고침할 때마다 1회** + 캐릭터 카드 제목 옆 **🔄 아이콘 버튼**으로 수동. 연달아 새로고침 대비: 마지막 동기화 완료(settings.lastSync) 또는 마지막 '열 때 동기화' 시작(localStorage `mapleBossTracker.loadSyncAt`)이 **3초**(LOAD_SYNC_GAP_MS, 사용자 결정) 안이면 건너뜀. 2026-10-10 **제거**: '열려 있으면 15분마다 자동 동기화' 설정(settings.autoSync — 불러올 때 삭제, 드라이브 비교 제외)·그 체크박스(+ 추가 창)·1분 타이머/탭 복귀 시 15분 경과 자동 동기화(CONFIG.AUTO_SYNC_MIN, autoDue). 일퀘/길드 탭을 보고 있을 때의 스케줄러 새로 고침(tabTick)은 그 화면 표시용이라 그대로.
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

## 6-1. 소식 피드 (왼쪽 아래 카드, 2026-10-09 추가) + 썬데이 메이플 카드
- 구조: `.github/workflows/update-feed.yml`(cron `*/5 * * * *` + 수동 실행) → `scripts/update_feed.py`가 4개 출처를 확인해 **새 글만** `feed.json`에 추가 → 바뀐 게 있을 때만 커밋(`git pull --rebase -X theirs` 후 push, 최대 5회 재시도). 사이트는 `./feed.json?t=<5분 단위>`만 읽음(로드 시 + 5분마다 + 탭 복귀 시). **사용자 API 키 사용 안 함.** file:// 로 열면 https://ggoolzip-wq.github.io/feed.json 을 읽음(Pages는 CORS *).
- GitHub cron은 실제로 5~15분 늦게 도는 일이 흔함(무료 러너 사정). 저장소에 60일간 커밋이 없으면 예약 실행이 꺼질 수 있지만 피드 커밋이 있어서 사실상 유지됨.
- 출처(소스별 try/except, 하나가 실패해도 나머지는 계속):
  - **사료감지(saryo)**: 넥슨 Open API `/maplestory/v1/notice`(매회) + `/notice-event`(15분마다), 워터마크보다 큰 id만 `…/detail` 조회(회당 최대 10건). 규칙 = 본문에 '메이플 운영자' 또는 '운영자 NPC'가 있고, 그 앞 100자·뒤 70자 안에 수령/지급/받기 등이 있음. 제외: '수령 불가', '받을 수 없', '지급되지 않', 코인샵/상점, 소울 교환/조각, '교환하기/교환해 주/교환할 수'('교환 여부' 같은 안내 문구는 제외하지 않음 — 150276 본문에 있음). '수령 기간 … ~ M월 D일 (오전|오후) H시 M분'에서 마감 추출(없으면 23:59) → `end`. 만료된 글은 카드에서 흐리게.
  - **패치내역(patch)**: `/notice-update`(10분마다) + **마이너 패치**(매회): 공식 공지사항 중 제목이 `MINOR_RE`(`마이너\s*(버전)?\s*(\(N\))?\s*패치` — '마이너패치'·'마이너 패치'·실제 형식 '[패치완료] 10/8(목) ver1.2.419 마이너버전(8) 패치'·'… 마이너(7) 패치(19:21 적용)') 에 맞는 글을 **다른 피드 글처럼 쌓음**(id `minor:<공지번호>`, src 'minor', 업데이트 공지와 날짜순으로 섞임): 처음 한 번(워터마크 `minor` 없을 때)만 최근 2개를 채우고(백필), 이후엔 워터마크보다 번호가 큰 새 글만 맨 위에 추가 — 예전 글은 지우지 않고 아래·다음 쪽으로 밀려남(탭당 200개 한도만). (2026-10-09 사용자 정정: '최신 2개만 유지'가 아님, 2개는 첫 백필 개수.) 출처 = **1순위 Open API** — 사료감지가 같은 회차에 받은 `/notice` 목록(최근 20건, 점검 분류 글 포함, 추가 API 호출 0, 날짜에 시각 있음). **대체(fallback)** = 홈페이지 검색 HTML `https://maplestory.nexon.com/News/Notice/All?search=마이너` — API 목록이 없을 때(실패) 또는 첫 백필인데 API 20건 안에 마이너 패치가 2개 미만일 때만(백필은 2개 모일 때까지, API 실패 대체는 1쪽 글이 전부 워터마크보다 새로우면 `&page=2..5`까지; `parse_notice_list` — news_board 안 li, 오늘 글은 'PM 07:22'처럼 시각만 → 오늘 날짜로). 이미 있는 글은 제목·날짜만 매번 갱신([패치예정]→[패치완료] 제목 변경 반영). API·HTML 둘 다 실패하면 경고만 남기고 기존 글 유지(패치 탭 실패로 표시 안 함). 테스트: `tests/test_feed_minor.py`(픽스처 `tests/fixtures/notice_all.html` = 공지사항 목록 웨이백 사본 2026-06-23).
  - **테섭(test)**: https://maplestory.nexon.com/Testworld/News/Update 목록 HTML 스크랩(`[수정N]` em 태그 제거).
  - **마빡도로시(mabbak)**: 인벤 닉네임 검색 `https://www.inven.co.kr/board/maple/{게시판}?name=nicname&keyword=마빡도로시`, 게시판 5974·2304·2314·2316·2587 각 1회(1.2초 간격, 회당 5요청 + 새 글당 본문 1요청). 새 글은 본문의 articleTitle/articleDate(연도·시각)로 기록. 게시판 첫 방문 땐 워터마크만 설정(공지 고정글·옛 글을 채우지 않음). 모든 게시판이 실패할 때만 소스 실패.
- **썬데이 메이플(feed.json `sunday`, 탭 아님)**: 가장 최근 제목에 '썬데이 메이플'(`SUNDAY_RE`, 띄어쓰기 무관)이 있는 이벤트 글 1건 `{id, title, url(/News/Event/<id>), image, thumb, start, end, date, benefit, benefitSrc(text|summary), via(api|html)}`.
  - **1순위 Open API**: 사료감지가 15분마다 받는 `/notice-event` 목록 재사용(추가 호출 0) → 번호가 바뀐 새 썬데이 글일 때만 `/notice-event/detail` **1회**(contents 의 gen_container 첫 이미지 = 대표 이미지, 절대 위치 작은 gif 제외) → 주 1회 정도 = **하루 평균 +0.15회**.
  - **대체 HTML**: API 목록 실패 시(15분 회차) 또는 저장된 썬데이가 없는데 API(진행 중 이벤트)에 없을 때만 `/News/Event/Ongoing?search=썬데이`(+저장된 것 없으면 `/News/Event/Closed?search=썬데이`) → 이미지가 없으면 글 페이지 `/News/Event/<id>` HTML(`parse_event_page`, 기간 'YYYY년 MM월 DD일 HH시 MM분 ~ …').
  - **매일 10:00~10:20 KST 집중 감시(sunday-watch.yml + scripts/sunday_watch.py, 2026-10-10 추가)**: 썬데이 글은 보통 오전 10시에 올라오므로, 5분 피드(15분마다 /notice-event)보다 빨리 잡으려고 별도 워크플로. 예약 `45 0 * * *`·`50 0 * * *`(09:45/09:50 KST, GitHub 예약 지연 대비 두 번, concurrency `sunday-watch` 라 하나만; 두 번째는 첫 번째가 끝난 뒤 시간이 지났으면 바로 끝) → 10:00 KST 까지 대기 → **5초마다**(사용자 결정) `/notice-event`(update_feed.nx, 키1→키2) 확인, API 가 실패한 회차만 홈페이지 `/News/Event/Ongoing?search=썬데이` → 저장된 sunday.id 보다 큰 썬데이 글을 찾는 즉시 멈추고 `update_feed.src_sunday`(detail 1회) → 같은 OCR 단계(scripts/sunday_ocr.py: 혜택·sunday.png) → 커밋. **이번 주 썬데이(시작일+1일이 아직 안 지남)가 이미 저장돼 있으면 확인 안 함(호출 0)**, 10:20 이후 시작이면 바로 끝.
    - API 호출: 최대 20분÷5초 = **240회 + detail 1회 ≈ 하루 최대 241회** → 기존 약 530회와 합쳐 약 770회(1,000회 한도 안, 넘치면 키2). 이번 주 글이 이미 있는 날은 0회.
    - 커밋 충돌 방지: OCR 뒤 `--save`로 sunday 만 임시 파일에 저장 → `git fetch` + `reset --hard origin/main`(update-feed 가 그 사이 올린 최신 feed.json) → `--apply`로 sunday 만 덮어쓰기 + sunday.png → 커밋·push(최대 5회 재시도). update-feed 는 자기 concurrency 그룹 그대로라 20분 감시 중에도 5분 실행이 막히지 않음.
    - 수동 테스트: Actions → Sunday watch → Run workflow: `test_minutes`=N(지금부터 N분만), `pretend_new`=true(저장된 썬데이도 새 글처럼 다시 처리 — OCR·자르기·커밋까지 확인). 테스트 `tests/test_sunday_watch.py`(모의 시계: 240회, 발견 즉시 멈춤, HTML 대체, 이번 주 글 있으면 0회, --apply 병합, 워크플로 설정).
  - 이미지(lwi.nexon.com)는 **핫링크 가능**(Referer 무관 200, `Access-Control-Allow-Origin: *`) → 저장소에 내려받지 않고 URL 그대로 사용(img referrerpolicy=no-referrer). 실제 이미지는 876×3692 같은 아주 긴 세로 이미지라 카드에서는 contain 으로 작게 보임 — 클릭하면 글.
  - **OCR(글 하나당 한 번)**: 썬데이 혜택은 보통 이미지에만 있으므로, update_feed.py 가 `sunday_needs_ocr()`(새 이미지이거나 OCR 실패 3회 미만)일 때 `sunday_ocr=true` 출력 → update-feed.yml 의 'Sunday OCR' 단계에서만 `apt-get install tesseract-ocr tesseract-ocr-kor` + `pip install pillow`(평소 5분 실행엔 설치 안 함) → `scripts/sunday_ocr.py`: 원본 이미지를 700px 조각(80px 겹침)으로 나눠 2배 확대, 원본/반전 두 번 `tesseract --psm 6 tsv`(kor+eng) → 단어 상자를 줄로 묶고 한 글자씩 끊긴 한글을 붙임('어 빌 리 티'→'어빌리티') → 혜택 줄 = 키워드(어빌리티·스타포스·파괴·미라클 타임·추가옵션·메소·몬스터파크·경험치·큐브·심볼 …) + 값(%, 할인, 감소, 증가, N배 …), 값이 다음 줄이면 합침, '단, … 않습니다' 안내·합계(=, +)·44자 초과 제외, 최대 3개, 짧게 다듬기('이하에서'→'이하', '강화 시' 제거, OCR '2123 이하'→'21성 이하'). 결과 `sunday.benefit`(' · '로 연결), `benefitSrc:'ocr'`(본문 글자에서 찾은 'text'가 있으면 그걸 우선).
  - **자르기(sunday.png)**: 같은 OCR 줄 위치로 '이벤트 기간' 줄 ~ 마지막 혜택/안내 줄(아래 '바로가기·궁금하다면' 전)까지 + 여백 → Pillow 로 잘라 저장소 루트 `sunday.png`(새 글마다 덮어씀) → `sunday.crop = 'sunday.png?v=<id>'`. 못 찾으면 crop 없음 → 카드는 원본 이미지. OCR 기록 `sunday.ocr = {image, ok, at, tries, box, cropSize, lines(최대 40줄), error?}` — 같은 이미지는 다시 OCR 안 함, 실패는 3번까지 재시도. 1397 실측: 혜택 '어빌리티 재설정 명성치 비용 50% 할인 · 21성 이하 스타포스 파괴 확률 30% 감소', 자르기 (0,470)-(876,1103).
  - 로컬 확인: `python3 scripts/sunday_ocr.py --image 파일또는URL [--crop out.png]` (tesseract-ocr-kor, Pillow 필요). 테스트 `tests/test_sunday_ocr.py`(모의 + tesseract 가 있으면 픽스처 sunday_1397.jpg 실측).
  - 혜택 한 줄(`sunday_benefit`, OCR 전 1차): ① 제목·본문 글자에서 키워드(미라클 타임, 샤이닝 스타포스, 스타포스 … 할인/감소, 몬스터파크 … N%, 룬, 심볼 N배, 경험치/메소 N%, 큐브 할인, 솔 에르다, 몬스터 컬렉션, 주문의 흔적) 최대 3개 ' · ' ② 없으면 본문의 짧은 문장(수정/안내/기간 문구 제외) ③ 없으면 빈 값 → 사이트가 글 제목 표시. **썬데이 공지는 보통 이미지뿐이라 대개 ③(제목)** — → 그래서 아래 OCR 단계가 이미지에서 혜택을 읽음.
  - 실패해도 다른 출처에 영향 없음(경고만). 테스트: `tests/test_feed_sunday.py`(픽스처 event_sunday_1317.html = 2026-05-10 스페셜 썬데이 글, event_closed.html, event_ongoing.html — 웨이백 사본).
- API 호출량(개발 키 1,000회/일): 5분 실행 288회 × /notice 1 + /notice-update 144 + /notice-event 96 ≈ 530회/일 + 새 공지 detail. 마이너 패치는 추가 호출 0(/notice 재사용), 썬데이는 새 글일 때 detail 1회(주 1회 정도). **sunday-watch(10:00~10:20 KST, 5초) 최대 +241회/일 → 합계 약 770회/일.** (cron 지연 때문에 실제로는 더 적음.) 키는 저장소 secret `NEXON_API_KEY` (2026-10-09 설정, 개발 키). **두 번째 키** secret `NEXON_API_KEY2`(2026-10-09 설정)도 update-feed.yml 에 전달 — `nx()`가 1번 키에서 HTTP 429·401·403 또는 오류 코드 OPENAPI00007(호출량 초과)·OPENAPI00005(유효하지 않은 키)·OPENAPI00001/00002를 받으면 같은 요청을 2번 키로 다시 보내고, 이번 실행 동안 1번 키는 건너뜀(다른 오류는 전환 안 함). 둘 다 막히면 원래처럼 출처 실패 표시. 테스트 `tests/test_feed_keys.py`. (update-prices 는 Open API 를 안 써서 키 불필요.) 결과적으로 하루 한도는 사실상 키 2개분(2,000회). 할당량이 모자라면 실서비스 키로 교체: Settings → Secrets → Actions.
- 처음 실행/워터마크 없는 출처는 '지금 있는 글 = 이미 본 것'으로 처리(예전 글을 채우지 않음). 시드(2026-10-09): 사료 150276 '(추가) 리워드 드롭 관련 오류 안내'(~2026-10-21 23:59), 패치 814 '클라이언트 1.2.419(5) 업데이트 안내', 테섭 199·198, 마빡도로시 인벤 5974/7258005 '10월 테섭(라방) 일정 / 2026 한글날 이벤트 요약'(2026-09-30 02:36).
- feed.json 형식: `{version:1, updatedAt, sunday?:{…위 썬데이, crop?, ocr?}, sources:{saryo|patch|test|mabbak:{label, ok, checkedAt, lastOkAt, error}}, state:{watermarks:{notice, notice-event, notice-update, minor, test, inven:<게시판>}}, items:{saryo|patch|test|mabbak:[{id, title, url, date(ISO KST), end?, src?, board?}]}}` — id로 중복 제거, 최신순, 탭당 최대 200개. 저장 조건 = 새 글 / 출처 성공·실패 바뀜 / 워터마크 바뀜 / 3시간 하트비트(상태 시각 갱신). `GITHUB_OUTPUT`에 changed=true|false.
- 로컬 실행: `NEXON_API_KEY=… python3 scripts/update_feed.py` (옵션 `FEED_ALL=1` 모든 출처 강제, `FEED_OUT=경로`, `FEED_PROXY=http://…` nexon.com·인벤 요청에만 프록시).
- 썬데이 카드(src/app.js renderSun(), extra.css .suncard/.sun*): 소식 카드 바로 아래 `#sunCard`. 머리글 = 소식 탭과 같은 모양의 탭 하나 '☀ 썬데이'(인라인 SVG 해, #f5c518). 본문 = 이미지(crop 이 있으면 ./sunday.png, 없으면 원본; object-fit:contain) → 제목·기간 한 줄(썬데이 칸이 230px 미만이면 .tight 로 숨김) → 맨 아래 노란 띠 '이번 주 혜택' + 혜택마다 한 줄(최대 3줄, 각 줄 말줄임, 없으면 제목). **이미지 클릭 = 라이트박스**(공식 사이트로 바로 가지 않음): 어두운 배경(rgba(0,0,0,.8)) 가운데에 원본 전체 이미지(없으면 잘린 것)를 화면에 맞춰 표시, 이미지를 누르면 원본 폭으로 확대(스크롤), 바깥 클릭·✕(노란 동그라미)·Esc 로 닫기, 아래 줄에 제목·기간 + '공지 보기 ↗'(새 탭 글), 열려 있는 동안 페이지 스크롤 잠금, 닫으면 포커스 복귀. 모바일도 화면 안(✕는 안쪽 위). 글이 없으면 점선 상자 + 해 아이콘 + '아직 썬데이 메이플 소식이 없어요'. 데스크톱 높이: feedFit 이 남은 높이(예전 소식 카드 높이) h 를 **소식 1/3 : 썬데이 2/3**(사이 12px)로 나눔 — 소식은 최소 2줄 높이(132px) 보장, 썬데이 칸이 140px 미만이면 썬데이를 숨기고 소식이 전부 사용(페이지가 길어지지 않게). 모바일(≤820px)은 소식 다음 순서(order 3), 이미지 높이 min(70vh, 520px). 같은 데이터면 다시 그리지 않음(이미지 재요청 없음).
- 카드 UI(src/app.js renderFeed()/feedFit(), extra.css .feedcard/.ftab/.fit/.fpg): 탭 4개 + 안 읽은 수, 글 = N 배지·한 줄 제목(말줄임)·날짜(올해가 아니면 yy.mm.dd)·사료는 ~마감일, 클릭 = 새 탭 + 읽음. 안쪽 스크롤 없음 — 쪽 번호(최대 5개, 6쪽 이상이면 ‹ ›), 탭 바꾸면 1쪽. 카드 높이 = 남은 화면 높이(본문이 더 길면 본문 끝까지, 짧으면 화면 끝 − 아래 안내문, 따라 내려올 때도 화면 안), 쪽당 줄 수 = 그 높이 ÷ 31px(최소 2, 최대 20). 820px 이하 모바일은 본문 아래로(사이드바 display:contents + order) 고정 6줄. 출처 실패면 탭 안에 작게 '⚠ 수집 실패 · 마지막 성공 …'(오류는 툴팁). 새로고침 버튼 없음.

## 7. 구글 OAuth
- **로그인 창(팝업) 규칙 (2026-10-10, 'PC방에서 자꾸 로그인하라고 함' 수정)**: `requestAccessToken` 은 **사용자가 직접 누른 동작에서만, 그 동작당 최대 1번**(gd.ia 플래그: ☁ 구글 로그인/다시 연결·헤더 [☁ 다시 연결]·'지금 저장'(gdPush({manual:true}))·충돌 선택 버튼). 자동 동작(페이지 열기 gdConnect(false)·탭 복귀/1분 gdPull·자동 저장 gdPush·401 응답)은 **남은 토큰(gdHasTok)만 사용**, 없거나 만료/거부(401)면 팝업 없이 `gdSet('reconnect', GD_NEED_LOGIN)` → 헤더 [☁ 다시 연결]. 그 상태에서 바꾼 내용은 이 PC 에만 저장(gdChanged 가 저장 예약 안 함) → 헤더 버튼 **한 번** 누르면(gdHeaderClick → gdLogin) 로그인·3-way 병합·저장. 예전 원인: 토큰(1시간)이 없거나 만료되면 페이지 열 때·자동 저장 때 자동으로 팝업을 시도(브라우저가 막으면 '다시 연결', 안 막으면 로그인 창) + 401 이면 자동 재시도 팝업. fb26dde 의 gdPull 은 원래도 토큰이 있을 때만 돌아 원인이 아니었음. 테스트 test20.
- 클라이언트 ID: `463037848804-2ut2277bsc2cf4vpf4qb0rl7hlt9ur8c.apps.googleusercontent.com` (src/app.js 상단 `GOOGLE_CLIENT_ID`). 승인된 JavaScript 원본: `https://ggoolzip-wq.github.io` (경로 없음).
- Google Identity Services 토큰 모델(`accounts.google.com/gsi/client`) + Drive REST v3, 범위 `https://www.googleapis.com/auth/drive.appdata`(비민감 범위).
- 동의 화면은 **테스트 모드**일 가능성 → 사용할 구글 계정을 'Google 인증 플랫폼 > 대상 > 테스트 사용자'에 추가해야 함. '확인되지 않은 앱' 화면은 '계속'으로 진행. access_denied/popup_closed 등은 한국어 안내 모달.
- https 또는 localhost에서만 로그인 가능(file://에서는 ☁ 메뉴에 안내).

## 7-1. 동기화 서버 (Cloudflare Workers + D1) — 준비만, 아직 꺼 둠 (2026-10-10)
- 사용자 승인한 새 계획: 구글 드라이브 동기화를 무료 Cloudflare Workers + D1 서버로 바꿈. **1단계(코드·테스트)만 완료, 배포 안 함, 사이트 동작 변화 없음.**
- 서버: `server/` (worker.js · schema.sql · wrangler.toml · README.md, `npm install` 로 wrangler 4 — Node 22 필요, 박스에는 /home/box/.local/node22). 자세한 API·배포 순서는 server/README.md.
- 로그인 = 넥슨 Open API 키 → 서버가 넥슨 /maplestory/v1/character/list 로 확인 → account_id 해시(sha256(ID_PEPPER:id))로 사용자 찾기/만들기 → 세션 토큰(브라우저 localStorage `mapleBossTracker.svToken`, 서버는 토큰 해시만, 365일). 원본 키는 서버에 저장 안 함(저장 데이터에서도 서버가 키 필드 삭제). 한 사용자에 넥슨 계정 여러 개 연결(/api/link — 로그인 중 새 키를 등록하면 저장 전에 자동 연결).
- 데이터 = 사용자별 JSON 1개 + rev. PUT 할 때 baseRev 가 다르면 409 + 서버 내용 → 브라우저가 기존 3-way 병합(gdSync/gdMerge, 마지막으로 맞춘 내용 = localStorage `mapleBossTracker.svbase`) 후 다시 저장. 최근 10개 저장본 보관(state_history). 로그인 시도 IP별 30회/10분.
- 클라이언트: src/app.js `SYNC_API_URL`(지금 '') — 비면 구글 드라이브 그대로. 값 또는 localStorage `mapleBossTracker.syncApi`(미리 써 보기용)가 있으면 서버 모드: 같은 gd* 흐름(gdConnect/gdSync/gdPush/gdPull/gdAsk)에서 저장소 함수만 바뀜(gdFind/gdRead/gdWrite/gdRemoteChanged/gdToken → sv*; 드라이브 전용은 driveToken/driveFind/driveRead). 메타 `mapleBossTracker.svmeta`(rev 포함). ☁ 메뉴 = '본계정 키로 로그인' 버튼 + 키 입력칸 / 로그인 후 지금 저장·로그아웃·'구글 드라이브에서 가져오기 (한 번)'(구글 로그인 창 1번 → 드라이브 저장본을 이 PC 와 합쳐 서버 저장). 처음 로그인 때 서버가 비어 있으면 이 PC 데이터를 올림. 키는 서버로 안 보냄(backupData(false), 계정에는 키 대신 ah = 서버 계정 해시) → 다른 기기에서는 로그인한 키만 자동으로 채워지고 다른 계정 키는 다시 입력. 로그인 창 자동으로 안 띄움(토큰 없으면 ☁ 로그인/다시 로그인).
- 테스트: tests/test_server.py(API·보안·CORS) · tests/test_tracker23.py(브라우저 2대: 로그인·업로드·내려받기·자동 저장·당겨오기·409 병합·진짜 충돌 질문·새로고침·드라이브 가져오기·로그아웃). 둘 다 wrangler dev(로컬 D1)+넥슨 모의(tests/mock_nexon_list.py, cf_dev.py)를 스스로 띄움, wrangler 없으면 SKIP.
- 진행 (2026-10-10 03:1x KST): wrangler 로그인 완료(박스). D1 `ggoolzip-sync` 생성(id 0c815aec-…, WNAM) + 스키마 적용. ID_PEPPER 생성 → 박스 /home/box/.config/ggoolzip/ID_PEPPER (600) 백업. **Worker 배포는 막힘**: Cloudflare 계정 이메일 인증 필요(오류 10034) + workers.dev 하위 도메인 등록 필요. CORS 에 https://maple.pages.dev 추가(단 maple.pages.dev 는 이미 다른 사람이 사용 중 — 프로젝트 만들지 않음). 미리 써 보기: `SYNC_TEST_URL`(app.js)에 서버 주소를 넣고 배포하면 `https://ggoolzip-wq.github.io/?sync=test` 로 이 브라우저만 서버 모드, `?sync=off` 로 되돌림.
- 배포 완료 (2026-10-10 03:27 KST): workers.dev 하위 도메인 `bossmaple` 등록, Worker = https://ggoolzip-sync.bossmaple.workers.dev (ID_PEPPER·SITE_PASS_HASH secret 설정됨). `SYNC_TEST_URL` 에 이 주소 입력 → `?sync=test` 사용 가능. `SYNC_API_URL` 은 아직 비어 있음(실서비스는 구글 드라이브 그대로).
- 대표 키/부계정 키 (2026-10-10 03:4x KST): 로그인 = 대표 키, 로그인 후 "부계정 키 추가". 부계정 키는 대표 키 HKDF→AES-GCM 으로 암호화해 D1 keyvault 에 보관, 대표 키로 다른 기기 로그인 시 자동 복원 (계정 `main:true` 표시). 원격 스키마 적용 + Worker 재배포 완료. 테스트: test_server.py(금고 8개 항목), test_tracker24.py(브라우저 2대). 자세한 건 server/README.md.
- 사용자 분리·입장 화면 (2026-10-10 04:1x KST): 원인 = 로그아웃해도 이 PC 데이터가 남고, 새 사용자 첫 로그인 때 "서버 비어 있음 → 이 PC 데이터 올림" 규칙으로 남의 데이터가 올라감. 수정: svUser(이 기기의 마지막 서버 사용자) 기록, 다른 사용자로 로그인하면 이 PC 데이터를 비우고 서버 데이터만 사용, 로그아웃 시 비움, 이 기기 첫 로그인 + 이 PC 데이터 있음 → "이 PC 데이터를 이 계정으로 올릴까요?" 확인. 서버 모드 입장 화면(#svGate): 빈 화면 → 초대 비밀번호 → 대표 키(+API 키 받는 법) → 로그인 성공 후 사이트, 세션 있으면 바로 사이트. test_tracker25.py.
- Cloudflare Pages (2026-10-10 04:4x KST): https://bossmaple.pages.dev — 이 주소에서는 서버 동기화가 기본(SYNC_HOSTS, 입장 화면 바로), github.io 는 구글 드라이브 그대로. 배포 = tools/pages_dist.sh → _site → `wrangler pages deploy _site --project-name bossmaple --branch main`. 자동 배포: .github/workflows/deploy-pages.yml (push + 피드/가격/썬데이 워크플로 완료 후) — 저장소 secret CLOUDFLARE_API_TOKEN·CLOUDFLARE_ACCOUNT_ID 필요(없으면 건너뜀). Worker CORS = github.io + bossmaple.pages.dev.
- 2026-10-10 05:xx KST 대규모 변경: 보스 목록 [취소]/[저장](대기 중 변경은 스냅샷과 비교, 저장 전엔 수익·저장소 미반영, 서버 모드 수동 저장의 유일한 경로) · 자동 저장/로그아웃 경고/beforeunload 없음 · 드롭은 보스·아이템당 기간 1회(예전 2+ → 1로 이전) · 드롭 표에서 보스 장신구(파풀 마크 제외)·여명 세트 제외 · 탭: 보스 현황/캐릭터 별 기록(2026-10-08부터 누적, ★득템)/총 수익(시드링 획득·물욕 누적 획득, 아이콘), 주간 기록 탭 삭제(S.history 는 유지) · 개수 표기 xN · 예상 수익 = 남은 주간(12칸 중) + 미처치 월간 · 일퀘 제목 아이콘, 길드 본캐 행은 지하 수로만 · +추가 모달: 스케줄러 자동추가 옵션·이름으로 직접 추가 삭제 · 보스·난이도는 스케줄러로만. 테스트: test_tracker26·27, test_tracker11 은 다중 개수 전제라 run_all 에서 뺌.
- **친구 초대 전용 (2026-10-10)**: 기기마다 한 번 초대 비밀번호(POST /api/invite → 기기 표 `mapleBossTracker.svDevice`, 로그아웃해도 유지) → 넥슨 키 로그인. Worker secret `SITE_PASS_HASH` = sha256('ggoolzip-invite:'+비밀번호, 앞뒤 공백만 제거·대소문자 구분), 없으면 로그인 거부. 비밀번호 사본: 박스 /home/box/.config/ggoolzip/SITE_PASS (600, 사용자가 정한 값). 바꾸기: `cd server && bash set-site-pass.sh` (README). 사용량 제한: 세션별 읽기 90/분·저장 20/분, 사용자별 저장 40/분, 초대 시도 IP별 10/10분.
- 남은 일: 사용자 Cloudflare 가입 → `npx wrangler login --device`(또는 API 토큰) → d1 create · schema · ID_PEPPER · deploy → 미리 써 보기 → SYNC_API_URL 켜기. 나중 단계(미구현): 매일 18:00 KST cron 으로 maplescouter 헥사환산(캐릭터 1명으로 먼저 시험).

## 8. 사용자가 정한 동작·취향 (변경 시 사용자 확인 필요)
- 썬데이 새 글 감시: 매일 10:00~10:20 KST, **5초 간격**(사용자 결정, 최대 240회/일).
- 데이터 출처는 **넥슨 Open API 우선**, 홈페이지 HTML 스크랩은 API 실패/자료 없음일 때만 대체(2026-10-09 사용자 요청). 호출 수는 하루 한도(개발 키 1,000회) 안에서 — 이미 받은 목록 재사용.
- 썬데이 카드: 소식 카드 아래, 소식 1/3 : 썬데이 2/3, 이미지는 contain(페이지 길어지면 안 됨) + 이벤트 기간~혜택 부분만 자동 자르기, '☀ 썬데이' 탭 머리글(노란 해), 맨 아래 이번 주 실제 혜택(OCR, 혜택마다 한 줄; 못 읽으면 글 제목). 이미지 클릭 = 라이트박스(공식 사이트로 이동 X, '공지 보기' 링크만).
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
- 헤더: 로고 = 메이플 **주황버섯**(몹 1210102) 실제 게임 이미지(파비콘 동일), **☁** 버튼(구글 드라이브 — 1시간 지나면 여기에 [☁ 다시 연결]). (🔄 넥슨 동기화 버튼은 2026-10-10 왼쪽 캐릭터 카드 제목 '캐릭터' 바로 옆으로 이동: 동그란 아이콘만, aria-label·title(마지막 시각) 유지, 동기화 중 회전, 모바일 32px) → 작은 메뉴(상태·구글 로그인/로그아웃·지금 저장).
- 캐릭터 추가: 사이드바 **+ 추가** 하나로 통합 모달 — 여러 넥슨 API 키 관리(이름, 가린 키, 캐릭터 목록, 삭제, + API 키 추가) → 바로 그 계정 캐릭터 목록(검색·필터·여러 명 선택 추가), 아래 '이름으로 직접 추가'. 기존 캐릭터는 ✎로 수정.
- **넥슨 API 키는 드라이브에 기본 저장**(앱 전용 숨김 폴더). 체크박스 없음.
- **'로그아웃 후 이 PC 데이터 지우기' 버튼 없음**(사용자 결정: PC방 PC는 종료 시 자동 초기화). ☁ 메뉴엔 일반 로그인/로그아웃만.
- 사이트 이름 '보스 캐릭터 관리'. 주소는 루트(ggoolzip-wq.github.io).
- 상단 탭: 보스 체크 · 수익 요약 · 주간 기록 · 총 수익 · **ㅡ(짧은 가로 구분선)** · **일퀘 현황** · **길드 현황**. 사이드바 캐릭터를 누르면 보스 체크 탭으로 이동(주간 기록·총 수익과 같음).
- 일퀘 칸 아이콘(이름 왼쪽 20px, 모바일 18px, 완료 덮개 안에도 18px로 살짝 어둡게): 세르니움~카르시온 = 넥슨 Open API `/character/symbol-equipment`의 어센틱심볼 symbol_icon(터래플), 탈라하트/기어드락 = maplestory.io GMS/270 item 1714000/1714001(그랜드 어센틱심볼, JMS/444와 픽셀 동일 — KMS 389 데이터엔 아직 없음), 몬스터파크 = maplestory.io KMS/389 item 4001864(몬스터파크 REBORN 무료 이용권), 익스트림 몬파 = maplestory.io KMS/389 NPC 9071000 '슈피겔만'(몬스터파크 맵 951000000, 흰 호랑이 버전) 얼굴·모자만 잘라냄(원본 src/assets/dqicons/xmp_src_npc9071000.png).
- 일퀘 칸은 **모든 상태에서 가운데 정렬**(아이콘+지역명, 상태 줄). **완료 칸은 항상 덮개**(편집 중 캐릭터별로 숨김 처리한 완료 칸 포함) — test14가 '완료'로 보이는 모든 칸에 덮개가 보이는지 확인.
- 일퀘 현황: 설정 탭 없이 탭 안 **편집** 토글 하나로 표시 항목(전체 칩)·캐릭터별 항목(칸 클릭)·캐릭터 카드 숨김(👁) 설정. 완료 칸 = 보스 완료 덮개와 같은 rgba(0,0,0,.55) 덮개 + 지역명/✓ 완료, 마우스를 올리면 사라짐(밑글자는 덮개가 있을 때 숨김). 코드: src/app.js renderDaily()/dqCell(), extra.css .dq*.
- 소식 카드: 왼쪽 아래, 페이지가 카드 때문에 스크롤되면 안 됨(안쪽 스크롤도 없음, 쪽 번호로). 새로고침 버튼·설정 없음. 마빡도로시 = 인벤 닉네임 검색(포털 글보다 실제 게시글 우선).
- 드롭 표: **아이템을 묶지 않음**(2026-10-10 사용자 요청 — 예전 '+N' 묶음 칩 삭제, 모든 칩 각자 아이콘·클릭 +1, 넘치면 다음 줄로 wrap). 연마석(생명/신념)·소울 에테르(1~4단계)도 각각 일반 드롭 칩(클릭 +1, 개수만). 저장 키는 원래부터 아이템별('보스|g_life' 등)이라 변환 없음. **솔 에르다의 기운**은 드롭 표 맨 앞 **정보 전용** 칩(점선 테두리, 아이콘 왼쪽 위 숫자 배지 = 확정 지급 개수) — 클릭·기록·수익 없음(src/app.js ERDA/erdaFor).
- **에테르넬 장비 조각 정보 칩**(2026-10-10): 에르다 칩 바로 뒤, 같은 모양(.drop.erda.eter, 보라 배지) — 클릭·기록·수익 없음, 왼쪽 위 개수 배지. src/app.js `ETERNAL`/`eternalFor`/`E_UP`/`E_PART`, ITEMS e_*. 출처 나무위키 '에테르넬 세트' 3. 획득처(칼로스 노말 의지 조각 3·카오스 의지 5·익스 14 / 대적자 노말 결의 조각 4·하드 6·익스 16 / 카링 이지 고리 조각 1·노말 5·하드 7·익스 18 / 흉성 노말 단편 조각 6·하드 18 / 벨로나·림보·발드릭스·유피테르 노말 1·하드 2; 앞 4보스 단체 보상, 뒤 4보스 개인 보상). '조각'(이지/노멀) 2개 = 상위 1개, 상위 10개 = 에테르넬 방어구 1개(앞 4보스 모자·상의·하의·어깨장식, 뒤 4보스 장갑·신발·망토). 아이콘 src/assets/itemicons/(2636606·2634472·2636607·2635747 = maplestory.io KMST 1170, 2638063·2639252 = GMS 270, eternal_*.png = 나무위키 파일 i.namu.wiki).
- **드롭 칩 툴팁**(2026-10-10): `title` 대신 `data-tip` + 공용 #mbtTip(마우스 올림 / 터치는 누르는 순간 표시·3초 뒤 닫힘 — 탭 클릭 동작(+1)은 그대로 / Tab 포커스). 터치 길게 누르기(contextmenu)는 −1 하지 않음(− 버튼으로 취소). **툴팁은 반지 상자(녹옥 제외)·혼돈의 칠흑 장신구 상자·에테르넬 칩에만**(2026-10-10 사용자 요청 — 나머지 칩·에르다 칩은 툴팁/title 없음, − 버튼도 aria-label 만). 첫 줄은 굵은 제목. 내용(itemTip/eternalTip): 반지 상자 = 이름 + `리4: x%` + `컨4: y%` 만 / 칠흑 상자 = 이름 + 7종(루컨마·마깃안·몽벨·마도서 선택 상자·거공·커포·고근 — 나무위키 '칠흑의 보스 세트' 5.11) / 에테르넬 = '이름 N개 (단체보상|개인보상)' + 교환·부위 (난이도·'확정 지급'·'정보 표시'·'클릭: 획득 +1' 줄 없음). 반지 확률은 **넥슨 공식 확률 공개** maplestory.nexon.com/Guide/OtherProbability/bossRingBox/ringBox{Green,Red,Black,White,Life}Jade: 4레벨 확률 = 반지 확률 × 4레벨 확률 → 녹옥 없음(1~3Lv) · 홍옥 6.92308%×10% = 0.69% · 흑옥 12.5%×20% = 2.50% · 백옥 14.28571%×35% = 5.00% · 생명 14.51613%×70% = 10.16% (리렌·컨티 동일). BOX_INFO/ring4/fmtPct. 테스트 test21.
- 시즌 보스(예: '시즌 보스 메이린')는 '매칭 안 된 보스'에 표시하지 않음(isSeasonBoss, 이미 저장된 목록도 표시 때 거름).
- 이번 주 주간 보스 처치 0회인 캐릭터: 이름 아래 'Lv · 직업 · 월드' 옆에 강렬한 힘의 결정 아이콘 + **예상 주간 수익** = 켜 둔 주간 보스(⚙ 보스 선택의 난이도·파티 인원 그대로)를 1인당 가격 높은 순 상위 12개 합(실제 수익 계산과 같은 규칙, expectedWeekly). 툴팁에 12개 목록. 1마리라도 잡으면 사라짐, 켜 둔 보스가 없으면 표시 안 함.
- 파티 인원 최대: 기본 6, **익스트림 스우 2**, **최초의 대적자·찬란한 흉성·벨로나·림보·발드릭스·유피테르 3(모든 난이도)** — PARTY_MAX/partyMax. 저장값이 한도를 넘으면 불러올 때·난이도 바꿀 때 한도로 낮춤(clampParty), 나머지 값은 그대로.
- 사이드바 캐릭터 목록: **최대 8줄**, 넘으면 목록 안에서 스크롤(fitCharList). 데스크톱에서 화면이 낮아 8줄 + 소식 카드 최소 높이가 안 들어가면 들어가는 만큼(최소 4줄) — 1280x800 은 6줄, 1920x1080 은 8줄. (고른 월드 탭의 캐릭터 기준)
- **월드 탭**(캐릭터 카드, 2026-10-10 사용자 승인 디자인): 예전 '🌐 월드' 묶음 머리글 대신 한 줄 탭 '[아이콘]스카니아 (3) ㅣ [아이콘]루나 (2)'. 탭을 누르면 그 월드 캐릭터만 표시. 밑줄 글자, 활성 = 굵은 주황(다크 #ff9a3c / 라이트 #c95a00), 마우스 올리면 주황. 선택은 기기별 localStorage 'mapleBossTracker.worldTab'. 다른 화면에서 다른 월드 캐릭터를 고르면 그 월드 탭으로 바뀜. 월드 순서 = **탭 끌어 놓기**(마우스 HTML5 DnD, 터치는 탭을 옆으로 10px 이상 끌기) → S.worldOrder(드라이브 동기화). 월드가 하나면 탭 하나. (예전 월드 ▲▼ 버튼은 없어짐)
- 월드 아이콘: 공식 홈페이지 아이콘 ssl.nexon.com/s2/game/maplestory/renewal/common/world_icon/icon_N.png(13~14px 원본 그대로 base64, tools/build_worlds.py → src/worldicons.json, 원본 src/assets/worldicons/). 번호↔월드는 maple.gg 월드 아이콘과 픽셀 100% 일치로 확인. 스카니아 8 · 베라 12 · 루나 9 · 제니스 10 · 크로아 11 · 유니온 7 · 엘리시움 13 · 이노시스 6 · 레드 5 · 오로라 4 · 아케인 14 · 노바 15 · 에오스 3 · 핼리오스 2 · 챌린저스(2·3·4 포함) 20 · 버닝* 16. 모르는 월드는 아이콘 없이 이름만.
- 캐릭터 정렬 링크(밑줄 글자 버튼, 활성 = 굵게, 마우스 올리면 다크 #ff9a3c 주황 / 라이트 #c95a00 진한 주황): **월드 탭 줄 오른쪽**, 고른 월드 안에서 적용. **기본순**(저장된 순서) / **보스 미완료순**(이번 주 12/12 안 된 캐릭터 먼저, 각 무리 안은 기본순 — 안정 분할). 저장된 순서는 안 바뀜. 미완료순 보기에서는 순서 바꾸기(드래그·▲▼) 잠금. 선택은 **기기별 localStorage 'mapleBossTracker.charSort'**(드라이브 동기화 안 함 — 보기 설정이라 기기마다 달라도 되고 드라이브 충돌 대상이 늘지 않게).
- '초기화까지 (KST)' 카드: **보스 체크 탭 오른쪽 열 맨 아래**(항상 화면 안 — 넘치면 수익 패널·결정석 가격 목록이 안에서 스크롤). 오른쪽 열은 높이 고정(100vh−172px — 위 108px + 아래 안내문 58px 를 빼서 본문이 짧아도 페이지 스크롤이 안 생김): 결정석 가격 카드가 남는 높이 전부(약 16줄 목표 — 수익 패널 최대 높이 = max(170px, 100vh−736px)) → 1920x1080 17줄·수익 패널 전부, 1280x800 11줄·수익 패널 170px(안에서 스크롤). 캐릭터가 적어 본문이 짧으면 왼쪽 소식 카드가 최소 2줄까지 작아질 수 있음(test15). (2026-10-10: 열 높이가 내용 높이라 가격 카드가 2줄만 보이던 것 수정) 그 자리(왼쪽)는 소식/썬데이 카드가 위로 올라와 채움. 오른쪽 열이 없는 다른 탭에서는 표시 안 함. 1180px 이하에서는 오른쪽 열이 아래로 쌓이며 그 맨 끝.
- 길드 현황: 길드/월드는 고정값(설정 없음, 사용자가 바꿔 달라고 하면 GUILD 상수 수정). 본캐 목록 = isMain 캐릭터(현재 UI는 본캐 1명만 지정 가능).

## 9. 알려진 한계 · 주의
- 실제 구글 로그인·실제 넥슨 키 흐름은 자동 테스트로 확인 불가(모의 응답으로 검증). 실서버 동작은 사용자 확인으로 검증해 옴.
- 공식 공지 HTML 구조가 바뀌면 파서가 0행 → Action은 기존 prices.json 유지(경고만). 이때 scripts/nexon_prices.py 수정 필요.
- 공지 표에 없는 보스 가격은 내장 기본값(src/app.js PRICE_CONFIG) 사용.
- GitHub 무료 계정: 60일간 커밋이 없으면 예약 Action이 자동 비활성화될 수 있음(Actions 탭에서 다시 켜기).
- index.html은 아이콘 base64 때문에 약 395KB.
- 몬스터파크 now_count가 캐릭터 기준인지 월드 기준인지 API 문서에 없음(실측 두 캐릭터 모두 0이라 미확인). 앱은 캐릭터 기준으로 보고 7회 이상이면 완료 처리.
- 스케줄러 일퀘·몬파 정보는 넥슨이 '접속 중·접속 종료 시'에만 갱신 → 게임 안에서 막 끝낸 퀘스트는 접속을 끊기 전엔 반영이 늦을 수 있음.
- (예전: 320px 화면에서 헤더 동기화 버튼 때문에 약 20px 넘침 — 2026-10-10 버튼을 캐릭터 카드로 옮겨 해소)
- 소식 카드 높이는 남은 화면에 맞추므로 캐릭터가 많으면(사이드바 위쪽이 길면) 1280x800에서 쪽당 2줄까지 줄어듦(최소 2줄 — 그보다 좁으면 그만큼 페이지가 길어짐).
- 인벤은 GitHub Actions(해외 클라우드 IP)를 막을 수 있음 → 실패 시 카드에 '수집 실패' 표시. 실측 결과는 11장 변경 기록 참고.
- 드롭 목록(src/app.js DROPS, RING_DROPS)은 커뮤니티 자료 기준(반지 상자 분류: 2026-09 기준).
- 신념의 연마석 아이콘은 KMS 데이터(maplestory.io KMS 389)에 아직 없어 GMS 270 item 2539003 'Grindstone of Faith' 사용. 소울 에테르 1~4단계 아이콘은 maplestory.io 미수록 → maple.ai.kr 소울웨폰 개편 글의 게임 아이콘 이미지(1~4단계 순)를 잘라 배경 제거(src/assets/itemicons/soul_ether_N.png). 공식 데이터에 올라오면 교체 권장.
- 솔 에르다의 기운 개수는 나무위키 각 보스 문서(2026-10-10 열람) 기준 — 패치로 바뀐 적 있음(림보·발드릭스 상향). 바뀌면 ERDA 상수만 고치면 됨.

## 10. 보류 중인 아이디어
- ~~테스트 서버 공지의 가격을 '다음 패치 예정 가격'으로 표시~~ → 2026-10-10 구현 (아래 b38).

## 11. 변경 기록
- 2026-10-10 (3): **동기화 서버 준비**(server/ Cloudflare Workers + D1, 기능 플래그 SYNC_API_URL — 꺼 둠, 배포 안 함) · test_server · test23.
- 2026-10-10 (2): 드롭 칩 툴팁을 반지 상자(녹옥 제외)·칠흑 상자·에테르넬에만, 반지 상자 = 이름 + 리4/컨4 · 🔄 동기화 버튼을 캐릭터 카드 제목 옆 아이콘으로 · **페이지 열 때 자동 동기화(3초 간격)**, 15분 자동 동기화 설정/타이머 제거(autoSync 삭제) · test22, test13/21 갱신.
- 2026-10-10: **구글 로그인 창 자동으로 안 띄움**(7장) · **결정석 가격 카드 높이**(오른쪽 열 높이 고정, 16줄 목표) · **드롭 '+N' 묶음 삭제**(모든 아이템 각자 칩) · **에테르넬 장비 조각 정보 칩** · **드롭 칩 툴팁(마우스·터치)** + 반지 상자 리렌4/컨티4 확률(넥슨 확률 공개) · 칠흑 상자 구성품. test20·test21 추가, test9/10/17/18 갱신, tools/build_items.py 에 e_* 아이콘.
- 2026-10-10: **레이아웃** — 캐릭터 목록 8줄 + 안쪽 스크롤, '초기화까지' 카드를 오른쪽 열 맨 아래로(화면 안 고정), 소식 카드가 위로. **캐릭터 정렬**(기본순/보스 미완료순, 밑줄 링크). **월드 탭**(공식 월드 아이콘, 탭 끌어 놓기로 월드 순서) — 예전 월드 머리글·▲▼ 대체. tools/build_worlds.py·src/worldicons.json, build.py 에 WORLD_ICONS 치환. 소식 카드 최소 높이에서 내용이 넘치면 그만큼 키우고 썬데이에서 뺌(test15 1280x800). test19 추가, test4/mock 의 월드 헬퍼 갱신, test6 드롭 칩 선택자에서 에르다 칩 제외.
- 2026-10-10: **드롭 표에 연마석·소울 에테르·솔 에르다의 기운** — 생명/신념의 연마석, 1~4단계 소울 에테르를 보스·난이도별로 추가(저장된 드롭 개수 형식 그대로), 드롭 표 맨 앞에 솔 에르다의 기운 정보 칩(왼쪽 위 개수 배지, 클릭·집계 없음). **시즌 보스 메이린** '매칭 안 된 보스'에서 제외. 보스 처치 0회 캐릭터에 **예상 주간 수익(상위 12개)**. **보스별 최대 파티 인원**(익스 스우 2, 대적자·흉성·벨로나·림보·발드릭스·유피테르 3) + 저장값 자동 낮춤. tools/build_items.py 키 g_life,g_faith,se1~4,erda. test18 추가.
- 2026-10-10: **구글 드라이브 '어느 데이터를 쓸까요?' 반복 수정** — 자동 갱신·기기 전용 값은 비교/저장 대상에서 제외(updatedAt 안 바뀜), 마지막으로 맞춘 내용 기준 3-way 자동 병합, 진짜 충돌일 때만 한 번 질문(충돌 항목만 선택, 나머지는 합침), 탭 복귀·1분마다 다른 기기 변경 확인(gdPull). 예전 메타는 묻지 않고 합침. test17 추가, test10 갱신.
- 2026-10-10: **sunday-watch.yml** 추가 — 매일 10:00~10:20 KST 5초마다 썬데이 새 글 확인(API 우선·홈페이지 대체), 찾으면 즉시 처리(OCR·sunday.png)·커밋(최신 main 에 sunday 만 병합). 최대 +241 API 호출/일. scripts/sunday_watch.py, test_sunday_watch.py.
- 2026-10-10: 썬데이 **OCR 혜택**(실제 혜택 글자, 여러 줄) + **자동 자르기 sunday.png**(이벤트 기간~혜택 상자) + **라이트박스**(이미지 클릭 시 크게 보기, 공식 사이트 대신; '공지 보기' 링크). update-feed.yml 에 조건부 OCR 단계, scripts/sunday_ocr.py, test_sunday_ocr.py(+픽스처 sunday_1397.jpg), test16 갱신. NEXON_API_KEY2 를 workflow 에 전달(workflow 권한 받은 뒤 푸시). tests/mock_nexon.py 스케줄러 응답 날짜를 오늘(KST)로(고정 10-09 라 다음 날 test14 가 깨지던 것).
- 2026-10-09: **썬데이 메이플 카드** 추가(소식 카드 아래, 소식 1/3 : 썬데이 2/3, '☀ 썬데이' 탭 머리글, 이미지 클릭 = 글, 맨 아래 '이번 주 혜택'). update_feed.py src_sunday(API /notice-event 재사용 + 새 글 detail 1회, HTML 대체). 마이너 패치도 **API(/notice) 우선, 홈페이지 검색은 대체**로 변경(사용자 요청: 가능한 곳은 넥슨 Open API 우선). test16·test_feed_sunday 추가, test_feed_minor 갱신. 예비 넥슨 키 secret NEXON_API_KEY2 + 자동 전환(호출량 초과·잘못된 키), test_feed_keys 추가.
- 2026-10-09: 마이너 패치를 '최신 2개만 유지'에서 **누적**으로 변경(사용자 정정) — 처음 2개 백필 후 새 글은 맨 위에 추가, 예전 글 삭제 안 함(탭당 200개). 워터마크 `minor`. test_feed_minor 갱신(백필·새 글 추가·삭제 안 함·재채움 없음·쪽 넘김).
- 2026-10-09: 소식 카드 **패치내역** 탭에 공지사항 '마이너 패치' 추가(6-1장, 처음엔 최신 2개만 표시하는 방식이었음 — 위 항목에서 누적으로 바뀜). scripts/update_feed.py(MINOR_RE, parse_notice_list, src_minor, apply_minor), test_feed_minor.py + 픽스처 notice_all.html, test15 모의 feed에 minor 2건(탭 수 16, 날짜순 확인), run_all에 포함. 사이트(src/index.html) 변경 없음.
- 2026-10-09: **소식 피드 카드** 추가(왼쪽 아래, 사료감지·패치내역·테섭·마빡도로시). update-feed.yml(5분 cron) + scripts/update_feed.py + feed.json(시드), secret NEXON_API_KEY(개발 키) 설정. 카드 높이 자동 맞춤·쪽 번호·N 배지/안 읽은 수(localStorage feedSeen)·수집 실패 표시. test15 추가(run_all에 15). 자세한 내용은 6-1장.
- 2026-10-09: 일퀘 칸 지역 아이콘 추가(어센틱/그랜드 어센틱심볼 8종, 몬스터파크 이용권, 익몬 = 몬스터파크 NPC 슈피겔만 얼굴; 출처는 8장). 칸 내용 모든 상태 가운데 정렬. tools/build_dqicons.py·src/dqicons.json 추가, build.py에 DQ_ICONS 치환.
- 2026-10-09: 완료 덮개 확인 — 미리보기 사진에서 단풍용사 '아르크스' 칸에 덮개가 없던 것은 미리보기 스크립트가 그 칸에 마우스를 올린 채 찍었기 때문(버그 아님). 다만 편집 중 '캐릭터별 숨김'으로 표시된 완료 칸에는 덮개가 빠지던 불일치가 있어 고침(완료면 항상 덮개). test14에 '완료로 보이는 모든 칸에 덮개(불투명도 1, rgba .55)' 확인, 아이콘·가운데 정렬 확인 추가.
- 2026-10-09: 상단 탭에 ㅡ 구분선 + **일퀘 현황**·**길드 현황** 탭 추가. 스케줄러 호출을 fetchSched()로 통일(동기화·탭 공용, 요약 캐시 mapleBossTracker.sched). 일퀘: 그란디스 8지역 일퀘·몬파·익몬(주간), 완료 덮개·호버, 레벨 잠금 줄, 편집(전체/캐릭터별/카드 숨김 → S.dq), 10분 자동 갱신. 길드: 봉사활동(스카니아) 지하 수로·플래그 레이스 점수·순위·레벨·마스터(오늘→어제 대체), 본캐 이번 주 지하 수로·플래그·주간 미션. test14 추가, mock 확장, run_all에 14 포함.
- 2026-10-09: 완료 덮개 경고를 둘째 줄로 분리 — 1줄 '★ 이번 주 보스 완료', 2줄 빨간 (!) '검마 격파 필요'(괄호 제거). 글씨 .82rem/.74rem, (!) 13px. test12 갱신(문구, 두 줄·가운데·카드 안 맞춤 데스크톱/375/320px, 터치 탭 통과).

## 2026-10-10 수익 분석 (b31)
- 제목: '주별 누적 결정석 메소', '캐릭터별 누적 결정석 메소'.
- '보스 별 누적 아이템 드랍' (`bossLootHtml`, `totalData().byBoss`): 저장된 주간·월간 기록 + 이번 주/달 요약을 보스+난이도로 합산. 난이도는 그 기록의 보스 태그 '이름(난이도)', 없으면 현재 캐릭터 설정. 칠흑 상자는 고른 장신구('cb:<key>'), 미기록분만 상자로.
- '총 아이템 획득량' (`itemTotalsHtml`): 아이템별 합계(아이콘·이름·수량만). 반지 상자는 상자 수 + 기록된 결과 리4/컨4를 시드링 아이템으로 따로(꽝은 아이템 아님, 시드링 획득 섹션과 같은 `T.ring` 집계). 칠흑 상자는 장신구로 합쳐짐(같은 장신구 직접 드롭과 합산). 0개 숨김.

## 2026-10-10 b32
- 드롭 클릭 토스트의 '저장을 눌러야 기록돼요' 삭제. 대기 중 변경(pend)이 있는 채로 상단 탭을 바꾸면 '변경사항을 저장하시겠습니까?' — 예 = `pendSave()` 후 이동, 아니오 = `pendCancel()`(스냅샷으로 되돌림) 후 이동, 바깥 닫기 = 머무름.
- 수익 분석 표 라벨: '캐릭터별 누적 결정석 메소 ＆ 누적 획득 아이템' / 누적 주간 보스 메소량 / 누적 월간 보스 메소량 / 누적 합계 / 누적 획득 아이템.
- 시드링 기댓값 `ringExp(T)`: Σ 상자 수 × `ring4(box)` (BOX_INFO = 넥슨 공식 확률 공개 bossRingBox 페이지, 툴팁과 같은 값). 홍옥 리4·컨4 각 0.69%, 흑옥 2.50%, 백옥 5.00%, 생명 10.16%, 녹옥 0.
- 에픽빔 합계: 하늘색 그라데이션 + drop-shadow 글로우 + epshine 애니메이션(모션 줄이기 시 정지), 제목 `.ept` 부드럽게. '보스 별 누적 획득 아이템'.

## b36
- 에픽빔 합계 숫자 (b37): `.epbeam` ::before = conic-gradient 대각선 4방향 프리즘 광선(epray), ::after = 흰·청록 코어 글로우(epcore). 절대 위치·pointer-events:none, 모션 줄이기 시 정지. 푸터의 localStorage/드라이브 저장 문구 삭제.
- 캐릭터 목록 (b37): 스크롤 대신 8명씩 페이지 (`CHAR_PER_PAGE`, `#charPager`). 월드 탭·정렬 변경 → 1쪽, 인원 감소 → 마지막 쪽으로, 1쪽뿐이면 숨김. `fitCharList()` 는 높이 제한 없이 즉시 반환.
- 결정석 가격 하단: (마지막 확인 …) 은 다음 줄.

## 2026-10-10 b37–b38
- 에픽빔 합계 광선: 짧고 약하게(46px, 불투명도 낮춤), ::before 가 `rotate` 360° 회전(`--epdur` = 접속마다 4~10초 무작위, EP_DUR). 모션 줄이기 시 정지.
- 칠흑 모달이 왼쪽에 붙던 원인: 바깥 막에 `.modal`(상자용: width 100%, max-width 420px) 클래스를 써서 화면 왼쪽 420px 짜리 막이 됨 → 바깥 `.modal-bg`, 상자 `.modal`. test30 에서 1920·1280·375 폭 가운데 확인(칠흑·축하·저장 묻기).
- 생명 반지 상자 결과에 '생명의 연마석'(gl, 아이콘 g_life) — 반지 결과처럼 dropOut 에 저장, 불꽃은 연마석 아이콘, 수익 분석 보스별·총 아이템에 생명의 연마석으로 합산, 시드링 요약에 표시.
- 불꽃 아이콘 42px(1.3배). 캐릭터 목록 페이지 마지막 쪽도 8줄 높이(min-height) 유지. 동기화 줄 'HH:MM KST 동기화' → '갱신완료'(시각은 title). 마지막 상단 탭 복원(localStorage mapleBossTracker.tab, 없으면 보스 현황). 수익 분석·로그인 메뉴의 드라이브 저장 안내 문구 삭제.
- **테섭 예정 결정석 가격 (b38)**: update_feed.py 가 테섭 새 글(src_test 의 새 항목)마다 본문을 받아 nexon_prices.parse_post 로 가격표를 찾고, 있으면 prices.json 의 `upcoming`{source,rows,detectedAt} 에 저장(scripts/upcoming.py add_upcoming, 실서버와 같은 줄은 넣지 않음). 실서버 rows 는 그대로. update_prices.py(본섭 12:17) 는 upcoming 을 유지하고 같은 가격이 적용된 줄을 지움(reconcile, 모두 적용되면 upcoming 삭제). update-feed.yml 이 prices_changed 일 때 prices.json 도 커밋. 사이트: 가격 카드 각 줄에 '테섭 예정 → N', 예상 결정석 수익 옆에도 '테섭 예정 → N'(예정 가격으로 다시 계산, withUpcoming), 카드 아래에 테섭 글 제목. tests/test_upcoming.py(공지 픽스처를 테섭 본문으로 사용, 10% 인하 시나리오), test_tracker31(로컬 데모, 실서버에는 데모 데이터 없음).

## 2026-10-10 b39 — 결정석 가격 갱신 방식 (비용 절약)
- **5분 피드 작업(update_feed.py)이 주 경로**: 테섭 새 글 → 본문 전체에서 결정석 표 찾기(test_prices). 있으면 prices.json `upcoming` 에 1회 저장, 없으면 `checkedAt`(마지막 확인)만 오늘(KST)로. 실서버 가격은 그대로.
- **본섭 적용(patch_prices)**: 패치내역 소스(notice-update)에 새 `update:` 글이 나오고 `upcoming` 이 있을 때만 그 공지 본문을 받아 가격표(20줄 이상, 값 정상)로 실서버 rows/source 갱신 + `upcoming` 삭제. 예정 가격이 없으면 본문을 받지 않음.
- **update-prices.yml**: 매일 → 주 1회(금 12:17 KST) 대비용으로 축소. 지우지 않은 이유: 테섭을 거치지 않고 본섭에 바로 들어간 가격 변경·피드 작업이 놓친 경우(실패/차단)를 일주일 안에 잡아 주고, 7일 하트비트로 '마지막 확인'도 유지. 금요일 = 목요일 정기 패치 다음 날.
- **사이트**: `upcoming` 이 있으면 결정석 가격 카드에 탭 '가격 / 패치 후 예상 주간 수익'. 후자는 캐릭터별 주간 상위 12개 + 월간 보스(fullExpected)를 예정 가격으로 다시 계산(withUpcoming)하고 현재 가격 대비 증감(+초록/−빨강)과 합계. upcoming 이 없어지면 탭 자동으로 사라짐. 테스트: test_upcoming.py(6·7), test_tracker31(로컬 10% 데모, 스크린샷 b39_*).
- b39: 에픽빔 합계 숫자 광선(::before/::after, 회전, EP_DUR) 삭제 → 숫자 자체에 진주빛 그라데이션(흰→하늘→연보라, eppearl 3.2s 반짝임) + 흰/하늘/보라 drop-shadow 글로우. 모션 줄이기 시 정지.

## 2026-10-10 b40
- 패치 후 예상 주간 수익: 증감 뒤 (−x.x%) — 기준은 현재 가격 수익. 금액·%는 항상 prices.json `upcoming`(진짜 테섭 공지에서 파싱한 가격) vs 현재 실서버 가격으로 계산. 무작위 없음.
- **라이브 데모 예정 가격 (임시)**: prices.json `upcoming.demo = true`, 제목 '[데모] 임시 예정 가격 (무작위 5~20% 인하, 실제 테섭 아님)'. 54개 보스·난이도 전부, 시드 20261010 로 5~20% 인하, 만 메소 단위 반올림.
  - 안전장치: `upcoming.is_demo` → update_feed.patch_prices 는 데모일 때 본섭 공지를 읽지 않고 실서버 가격을 바꾸지 않음. 진짜 테섭 글이 오면 add_upcoming 이 데모를 통째로 버리고 그 글의 가격으로 교체(섞지 않음).
  - **삭제**: `python3 scripts/remove_demo_upcoming.py && git commit -am '데모 테섭 예정 가격 삭제' && git push` (demo=true 일 때만 지움). 그러면 '테섭 예정' 표시와 새 탭이 사라짐.
- 갱신완료 뒤 시각(HH:MM). 드롭 칩 선택 = 초록 배경+테두리, ✓ 없음(크기 그대로 → 줄바꿈 안 생김).
- 캐릭터 정렬은 목록 왼쪽 아래(#charFoot, 쪽 버튼과 한 줄): 기본순 / 보스 미완료순 / 검마 정렬순(이번 달 검은 마법사 미처치 먼저, c.monthly.blackmage; 완료 캐릭터는 흐리게 + '★이번 달 검마 완료' 덮개). 기본순 외에는 순서 바꾸기 잠금.
- 버그 수정: update_prices.py 가 가격이 같으면 7일마다만 checkedAt 를 바꿔 '변경 없음'으로 끝나던 문제 → 확인 성공 때마다 checkedAt=오늘(바뀌면 커밋). 피드 작업의 테섭 '결정석 변경 없음' 경로도 checkedAt=오늘.
- b42: 일퀘 현황 10분 자동 갱신(탭 열기·60초 타이머·화면 복귀) 삭제, '10분마다 자동' 문구 삭제 → 제목 옆 🔄(#dqSync, 캐릭터 동기화와 같은 SYNC_SVG·.ibtn.sbtn; 누르면 보이는 캐릭터 스케줄러 강제 갱신). 페이지 열 때는 보스 동기화(syncAll, 3초 규칙, 넥슨 API 전용·로그인 창 없음)가 같은 스케줄러 응답으로 일퀘 캐시도 채움. 길드 탭 자동 갱신은 그대로. test_tracker33.
