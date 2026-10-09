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
  - test13 = 현재 UI 구조(＋추가 통합 모달, 헤더 동기화, ☁ 메뉴) 핵심 테스트.
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
- 클라이언트 ID: `463037848804-2ut2277bsc2cf4vpf4qb0rl7hlt9ur8c.apps.googleusercontent.com` (src/app.js 상단 `GOOGLE_CLIENT_ID`). 승인된 JavaScript 원본: `https://ggoolzip-wq.github.io` (경로 없음).
- Google Identity Services 토큰 모델(`accounts.google.com/gsi/client`) + Drive REST v3, 범위 `https://www.googleapis.com/auth/drive.appdata`(비민감 범위).
- 동의 화면은 **테스트 모드**일 가능성 → 사용할 구글 계정을 'Google 인증 플랫폼 > 대상 > 테스트 사용자'에 추가해야 함. '확인되지 않은 앱' 화면은 '계속'으로 진행. access_denied/popup_closed 등은 한국어 안내 모달.
- https 또는 localhost에서만 로그인 가능(file://에서는 ☁ 메뉴에 안내).

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
- 헤더: 로고 = 메이플 **주황버섯**(몹 1210102) 실제 게임 이미지(파비콘 동일), **동기화** 버튼(아이콘+텍스트, 마지막 시각은 툴팁, 동기화 중 아이콘 회전), **☁** 버튼 → 작은 메뉴(상태·구글 로그인/로그아웃·지금 저장).
- 캐릭터 추가: 사이드바 **+ 추가** 하나로 통합 모달 — 여러 넥슨 API 키 관리(이름, 가린 키, 캐릭터 목록, 삭제, + API 키 추가) → 바로 그 계정 캐릭터 목록(검색·필터·여러 명 선택 추가), 아래 '이름으로 직접 추가'. 기존 캐릭터는 ✎로 수정.
- **넥슨 API 키는 드라이브에 기본 저장**(앱 전용 숨김 폴더). 체크박스 없음.
- **'로그아웃 후 이 PC 데이터 지우기' 버튼 없음**(사용자 결정: PC방 PC는 종료 시 자동 초기화). ☁ 메뉴엔 일반 로그인/로그아웃만.
- 사이트 이름 '보스 캐릭터 관리'. 주소는 루트(ggoolzip-wq.github.io).
- 상단 탭: 보스 체크 · 수익 요약 · 주간 기록 · 총 수익 · **ㅡ(짧은 가로 구분선)** · **일퀘 현황** · **길드 현황**. 사이드바 캐릭터를 누르면 보스 체크 탭으로 이동(주간 기록·총 수익과 같음).
- 일퀘 칸 아이콘(이름 왼쪽 20px, 모바일 18px, 완료 덮개 안에도 18px로 살짝 어둡게): 세르니움~카르시온 = 넥슨 Open API `/character/symbol-equipment`의 어센틱심볼 symbol_icon(터래플), 탈라하트/기어드락 = maplestory.io GMS/270 item 1714000/1714001(그랜드 어센틱심볼, JMS/444와 픽셀 동일 — KMS 389 데이터엔 아직 없음), 몬스터파크 = maplestory.io KMS/389 item 4001864(몬스터파크 REBORN 무료 이용권), 익스트림 몬파 = maplestory.io KMS/389 NPC 9071000 '슈피겔만'(몬스터파크 맵 951000000, 흰 호랑이 버전) 얼굴·모자만 잘라냄(원본 src/assets/dqicons/xmp_src_npc9071000.png).
- 일퀘 칸은 **모든 상태에서 가운데 정렬**(아이콘+지역명, 상태 줄). **완료 칸은 항상 덮개**(편집 중 캐릭터별로 숨김 처리한 완료 칸 포함) — test14가 '완료'로 보이는 모든 칸에 덮개가 보이는지 확인.
- 일퀘 현황: 설정 탭 없이 탭 안 **편집** 토글 하나로 표시 항목(전체 칩)·캐릭터별 항목(칸 클릭)·캐릭터 카드 숨김(👁) 설정. 완료 칸 = 보스 완료 덮개와 같은 rgba(0,0,0,.55) 덮개 + 지역명/✓ 완료, 마우스를 올리면 사라짐(밑글자는 덮개가 있을 때 숨김). 코드: src/app.js renderDaily()/dqCell(), extra.css .dq*.
- 소식 카드: 왼쪽 아래, 페이지가 카드 때문에 스크롤되면 안 됨(안쪽 스크롤도 없음, 쪽 번호로). 새로고침 버튼·설정 없음. 마빡도로시 = 인벤 닉네임 검색(포털 글보다 실제 게시글 우선).
- 길드 현황: 길드/월드는 고정값(설정 없음, 사용자가 바꿔 달라고 하면 GUILD 상수 수정). 본캐 목록 = isMain 캐릭터(현재 UI는 본캐 1명만 지정 가능).

## 9. 알려진 한계 · 주의
- 실제 구글 로그인·실제 넥슨 키 흐름은 자동 테스트로 확인 불가(모의 응답으로 검증). 실서버 동작은 사용자 확인으로 검증해 옴.
- 공식 공지 HTML 구조가 바뀌면 파서가 0행 → Action은 기존 prices.json 유지(경고만). 이때 scripts/nexon_prices.py 수정 필요.
- 공지 표에 없는 보스 가격은 내장 기본값(src/app.js PRICE_CONFIG) 사용.
- GitHub 무료 계정: 60일간 커밋이 없으면 예약 Action이 자동 비활성화될 수 있음(Actions 탭에서 다시 켜기).
- index.html은 아이콘 base64 때문에 약 395KB.
- 몬스터파크 now_count가 캐릭터 기준인지 월드 기준인지 API 문서에 없음(실측 두 캐릭터 모두 0이라 미확인). 앱은 캐릭터 기준으로 보고 7회 이상이면 완료 처리.
- 스케줄러 일퀘·몬파 정보는 넥슨이 '접속 중·접속 종료 시'에만 갱신 → 게임 안에서 막 끝낸 퀘스트는 접속을 끊기 전엔 반영이 늦을 수 있음.
- 320px 화면에서 API 키가 있으면(동기화 버튼 표시) 헤더 버튼이 약 20px 넘침 — 이번 작업 전부터 있던 현상(헤더는 손대지 않음).
- 소식 카드 높이는 남은 화면에 맞추므로 캐릭터가 많으면(사이드바 위쪽이 길면) 1280x800에서 쪽당 2줄까지 줄어듦(최소 2줄 — 그보다 좁으면 그만큼 페이지가 길어짐).
- 인벤은 GitHub Actions(해외 클라우드 IP)를 막을 수 있음 → 실패 시 카드에 '수집 실패' 표시. 실측 결과는 11장 변경 기록 참고.
- 드롭 목록(src/app.js DROPS, RING_DROPS)은 커뮤니티 자료 기준(반지 상자 분류: 2026-09 기준).

## 10. 보류 중인 아이디어
- **테스트 서버 공지의 가격을 '다음 패치 예정 가격'으로 표시** — 사용자 결정 대기 중(아직 구현 안 함).

## 11. 변경 기록
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
