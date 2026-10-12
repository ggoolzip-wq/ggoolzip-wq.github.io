# HANDOFF — 보스 캐릭터 관리 (메이플스토리 KMS 보스 결정석·드롭 관리)

다른 계정/다른 도우미가 이 저장소만으로 작업을 이어갈 수 있도록 정리한 문서입니다.

## ⚠️ 봇 작업 규칙 (사용자 상시 규칙 — 말 안 해도 항상 따를 것)
1. **작업을 시작할 때마다** 사용자가 부탁한 것들을 **숫자 목록으로 나열해서** 먼저 알린다.
2. **모든 변경은 사용자가 말하지 않아도 이 HANDOFF.md 에 반드시 기록**한다(새 섹션). 그리고 **완료 보고에서 "인수인계 파일(HANDOFF.md)에 기록했다"고 매번 말한다.**
3. **이 규칙(1~7번 전부) 자체도** 다음 봇이 사용자가 말하지 않아도 그대로 따른다(이 섹션은 지우지 말고 맨 위에 유지).
4. **작업이 끝날 때마다** 사용자에게 인수인계 파일 링크(https://github.com/ggoolzip-wq/ggoolzip-wq.github.io/blob/main/HANDOFF.md)와 홈페이지 주소(**https://bossmaple.pages.dev/**; 예전 주소 https://ggoolzip-wq.github.io/ 도 아직 동작)를 보낸다.
5. **작업을 시작할 때마다** 번호 목록과 함께 **예상 소요 시간**도 사용자에게 알린다.
6. **작업을 시작할 때마다** 사용 한도량(사용치)을 사용자에게 알리고, 한도 100% 전에 끝낼 수 없는 작업이면 **'한도 때문에 작업 불가'라고 미리** 알린다.
7. **작업이 끝나면 테스트 결과를 사진으로 자동 전송** (2026-10-12 b70 사용자 요청): 매 작업 끝에 라이브 사이트에서 바뀐 것이 동작하는 모습을 **변경 전/후** 스크린샷으로 `/workspace/maple-boss-tracker/` 에 저장하고, 완료 보고에 그 경로를 넣어 사용자가 묻지 않아도 사진을 보내게 한다(변경 전 화면은 이전 커밋의 index.html 을 라이브 주소로 띄워 재현 가능 — b70 참고).
8. **빈 칸 경고 = 빨간 테두리** (2026-10-12 b75 사용자 요청): 칸을 비워서 경고(빨간 글·알림)가 나오면 그 입력 칸에 `.inerr`(빨간 테두리)를 붙이고(`markEmpty(el)`), 사용자가 입력하면 바로 지운다(전역 input 리스너). 새 입력 칸·경고를 만들 때도 똑같이.
9. **합계·표·차트는 보이는 캐릭터만** (2026-10-12 b82 사용자 요청): 모든 탭(지금·앞으로)의 합계·순위·표·차트는 `visibleCharIds()`(= `vchars()`, 키가 등록된 계정의 캐릭터 + 계정 없는 수동 캐릭터)에 든 캐릭터만 센다. 지난 기록은 `visHist(h)` 로 걸러 합계를 다시 계산(저장된 기록은 절대 지우지 않음 → 키를 다시 넣으면 합계 복귀). 새 집계 코드는 `totalData()` 를 쓰거나 같은 헬퍼를 쓸 것.
- 작업 방식: `src/` 수정 → `python3 tools/build.py` → 테스트 → `git pull --rebase` → main 일반 push(강제 push 금지). GitHub 로그인(gh) 필요.

## 2026-10-12 b71 (캐릭터 추가 창: 처음 등록 칸 = 'API키 입력' + 등록만)
(src 수정→build→테스트→main 일반 push. Worker 변경 없음. HANDOFF 기록은 항상.)
1. 로그인 전 '+ 추가' 창의 본계정 등록 칸(`#svMainSec`, `svMainRender`)을 **API 키 입력 하나(placeholder 정확히 'API키 입력') + [등록] 버튼**만으로. 삭제: '🔑 본계정 API 키 등록' 제목, '본계정' 이름 칸, '키 발급: openapi.nexon.com …' 안내 줄. 창 제목 '캐릭터 추가'는 유지.
2. 오류·'이미 등록된 부계정 API입니다.'·만료 안내는 생길 때만 입력 아래 줄(`#svMainSt`, 평소 hidden). 승인 대기 화면(b68)은 그대로.
3. `Data based on NEXON Open API` 는 등록 칸 밖 창 아래(`#svMainAttr.svmattrib`) + 페이지 꼬리말에 그대로.
4. 테스트: test50 에 b71 검사(칸 글자 = '등록'뿐, placeholder, 보이는 컨트롤 = 입력·버튼), test24 문구 검사 수정, 표기 선택자 `.addm .svmattrib`(50·52). 23·24·29·46·50~53 통과.
5. 규칙 7 사진(라이브, 변경 전/후): /workspace/maple-boss-tracker/oct12i_b71_before_modal.png · oct12i_b71_after_modal.png (전체 화면: oct12i_b71_before_page.png · oct12i_b71_after_page.png).

## 2026-10-12 b70 (소식 카드: 7일 지난 글은 N·숫자 없음)
(src 수정→build→테스트→main 일반 push. Worker 변경 없음. HANDOFF 기록은 항상.)
1. 왼쪽 아래 소식 카드(사료감지/패치내역/테섭/마빡도로시): 글의 올린 날짜(`date`, KST)가 **지금보다 7일 넘게 지난** 글은 안 읽었어도 `N` 표시 없음, 탭 숫자(`.fcnt`)에도 안 셈. 7일 이내 글은 그대로(읽기 전까지 N, 읽음은 서버 동기화). `src/app.js`: `FEED_NEW_DAYS=7`, `feedTime(x)` = date → 없으면 `seen`(처음 수집 시각) → 둘 다 없으면 날짜 모름 = 예전처럼 N, `feedFresh`, `feedIsNew`(N·탭 숫자 공통). 렌더할 때마다 다시 계산 — feedLoad 가 5분마다·탭으로 돌아올 때 다시 그리므로 열어 둔 채로 7일이 지나면 그때 사라짐. 다른 '안 읽은 글 합계'는 없음(탭 숫자뿐).
2. 수집기 `scripts/update_feed.py`: 날짜 없는 글에 처음 수집한 시각 `seen`(ISO, KST) 기록(이미 있으면 유지), 기록하면 feed.json 저장. 지금 feed.json 의 글은 모두 날짜가 있음.
3. 테스트: 신규 **test_tracker54**(1일·7일-3분·날짜 없음·seen 2일 = N / 8일·seen 10일 = N 없음 / 탭 숫자 / 7일 이내는 클릭해야 사라짐 / 열어 둔 채 시간 지나면 다음 렌더에서 사라짐). 46·50·feed_* 통과(15 는 예전부터 실패하던 배치 검사).
5. 상시 규칙 7번(작업 끝나면 테스트 결과 사진 자동 전송) 추가. b70 변경 전/후(라이브 feed.json, 변경 전 = 이전 커밋 58d1614 의 index.html 을 라이브 주소로 띄움): 탭 숫자 사료감지1·패치내역3·테섭2·마빡도로시1 → 사료감지1·패치내역1·테섭·마빡도로시. 사진 /workspace/maple-boss-tracker/oct12h_b70_before_patch.png · oct12h_b70_after_patch.png · oct12h_b70_before_test.png · oct12h_b70_after_test.png.
4. 라이브 확인(13:2x KST, 처음 온 브라우저): 사료감지 1(10/8 글, 3.8일 → N) · 패치내역 1(10/8 만 N, 10/2·9/22 N 없음) · 테섭 0(9/10 글 2개 N 없음) · 마빡도로시 0(9/30 N 없음). 예전엔 이 4개도 N·숫자에 들어갔음. 스크린샷 /workspace/maple-boss-tracker/oct12h_live_feed.png.

## 2026-10-12 b69 (로그아웃 = 이 PC 완전 초기화 — 공용 PC/PC방)
(src 수정→build→테스트→main 일반 push. Worker 변경 없음. HANDOFF 기록은 항상.)
문제: PC방에서 ☁ 메뉴 → 로그아웃 뒤에도(새로고침해도) 캐릭터·데이터가 보임. 원인 후보: ① 로그아웃 뒤 늦게 도착한 서버 응답·다른 탭의 save() 가 localStorage 를 다시 씀(로컬 재현에서 로그아웃 직후 svSubSig 가 다시 생김), ② 시작할 때 세션 확인 없이 localStorage(mapleBossTracker.v1)를 그대로 읽음(예전 b62 규칙: 세션 만료돼도 이 PC 데이터 유지).
1. **로그아웃(서버 모드, `gdLogout`)**: ① 세션이 살아 있으면 남은 변경 먼저 서버로 — 저장 안 한 변경(pend·자동 저장 대기)은 `gdPush`, 키 변경은 `svSyncSubKeys`, 읽음은 `svSeenFlush` ② `POST /api/logout`(서버 세션 삭제) ③ `svWipeAll()`: localStorage·sessionStorage 의 `mapleBossTracker.*` 전부 삭제(데이터·키·금고 표시·소식 읽음·승인 대기 키·관리자 표시·캐시 등; 남기는 것은 테스트용 `syncApi` 뿐) + 메모리 상태 처음으로 + `svGen`+1(그 전에 시작한 서버 요청 결과는 svFetch 가 버림) + 다른 탭에 알림(`mapleBossTracker.svLogout` storage 이벤트 → 다른 탭 새로고침). IndexedDB·Cache Storage·쿠키는 이 앱이 쓰지 않음. 서버 데이터는 안 지움.
2. **세션 없음/무효**: 시작할 때 서버 모드인데 토큰이 없고 이 PC 에 개인 데이터(캐릭터·계정·기록·svUser/svmeta/svbase/svVault/svSubSig/svAdmin/guild/sched)가 있으면 지움(승인 대기 요청만 유지; 다른 탭에 알리지 않음 — 탭끼리 새로고침 반복 방지). 서버가 401(세션 만료·무효)이나 403(차단·거절)을 주면 바로 `svWipeAll` + '다시 로그인' 안내. **b62 의 '세션 만료돼도 이 PC 데이터 유지·다시 로그인하면 3-way 병합'은 폐지**(세션이 없으면 저장 못 한 변경은 버려짐 — 서버 데이터는 그대로).
3. 로그인 전에 이 페이지에서 직접 만든 데이터를 로그인 때 올릴지 묻는 흐름은 그대로(새로고침하면 지워짐).
4. 테스트: 신규 **test_tracker53**(로그아웃 직전 변경 서버 저장 → 예전 토큰 401 → 메모리·localStorage·sessionStorage 비움 → 다른 탭도 빈 상태 → 새로고침해도 빈 화면·+ 추가는 본계정 키만 → 세션 없는 남은 데이터 시작 때 삭제 → 무효 세션 + 로컬 데이터 → 401 → 삭제 → 본계정 키로 다시 → 데이터·부계정 키 복원). test25(로그아웃 시 변경 저장), 46(무효 세션 → 지움, 다시 로그인 → 서버에서 복원), 49(b64 초기화 기기도 세션이 없으니 전부 지움) 기대 수정. 23·24·25·46·49 는 '로그인 전 이 페이지에서 만든 데이터'를 새로고침 뒤 다시 넣는 `inject()` 도우미 사용. 전체 결과: 새·수정 테스트 전부 통과, 예전부터 실패하던 것만(8·10·16 시간 초과, 9·30 가격 꼬리말, 13·14 :8787 다른 서버, 15·27·28 예전 UI 기대).
5. 라이브 확인(12:5x KST, bossmaple.pages.dev, playwright): 가짜 세션+데이터 → 로그아웃 → 메모리·localStorage·sessionStorage 비움 → 새로고침해도 빈 화면, + 추가는 본계정 키만 / 세션 없는 남은 데이터 → 새로고침 때 삭제 / 무효 토큰+데이터 → 401 → 삭제·다시 로그인 안내. (무효 토큰 경우 401 이 오기 전 시작 동기화가 넥슨 호출 수 카운터 `callCount`(날짜·횟수만) 를 다시 쓸 수 있음 — 개인 데이터 아님.) 스크린샷 /workspace/maple-boss-tracker/oct12g_live_after_logout.png.

## 2026-10-12 b68 (가입 승인: 새 본계정 키 = 승인 대기 · 관리자 승인/거절/차단)
(src 수정→build→테스트→main 일반 push, Worker 는 `cd server && PATH=~/.n22/bin:$PATH npx wrangler deploy`. HANDOFF 기록은 항상.)
1. **새 가입 = 승인 대기**: 처음 보는 본계정 키로 /api/login → `users` + 새 표 `approval`(status pending, 대표 캐릭터 이름·월드·레벨 = 넥슨 목록에서 레벨 가장 높은 캐릭터, 요청 시각) + `accounts`(계정 해시, 같은 키로 다시 확인할 때 찾기용)만 만들고 **세션·금고·역할·데이터 없음** → `{status:'pending', pending}`. 같은 키로 다시 → 계속 pending(새로 안 만듦). approval 행이 **없는** 사용자 = 승인됨 → b68 전부터 있던 3명 모두 그대로(관리자 포함), 강제 로그아웃 없음.
2. **화면**: 캐릭터 추가 창에 '⏳ 승인 대기 중' + 대표 캐릭터·요청 시각 + [승인 확인](같은 키로 다시 로그인 시도) / [다른 키로 등록], NEXON 표기 유지. 헤더 버튼도 '⏳ 승인 대기 중'. 키·요청 정보는 이 기기 localStorage `mapleBossTracker.svPending` 에만(서버 저장 X). 페이지 열 때 한 번 자동 확인 → 승인됐으면 바로 로그인(예전 흐름 그대로), 거절이면 빨간 '가입 요청이 거절되었습니다'.
3. **거절·차단**: 로그인 403 `rejected`/`blocked`(빨간 글), 그 사용자의 세션 즉시 삭제, 세션이 남아 있어도 auth 가 403 → 저장·읽기 불가. **데이터는 지우지 않음**(차단 해제하면 그대로). 관리자 자신은 차단 불가.
4. **관리자**: Worker secret `ADMIN_USER` = 사용자의 기존 본 데이터(캐릭터 22·rev 42)의 users.id (앞 8자리 `ef4ca70b`). 로그인하면 ☁ 메뉴에 **'👑 관리자 — 가입 승인'** → 창(#adminModal): 승인 대기(승인/거절) · 사용 중(차단, 관리자 줄은 '관리자') · 차단·거절(차단 해제/승인). 서버 `GET /api/admin/users`, `POST /api/admin/decide {user, action: approve|reject|block|unblock}` — 서버가 세션의 사용자 id 로만 확인(아니면 403 not_admin). 관리자 여부는 로그인 응답·`/api/me` 의 `admin`(localStorage `mapleBossTracker.svAdmin` 은 버튼 표시용일 뿐).
   - **관리자 바꾸기**: D1 에서 새 관리자 users.id 확인(`npx wrangler d1 execute ggoolzip-sync --remote --command "SELECT u.id, s.rev FROM users u LEFT JOIN state s ON s.user_id=u.id"`) → `cd server && npx wrangler secret put ADMIN_USER` 에 그 id 입력(배포 따로 필요 없음). secret 이 없으면 D1 meta `admin_user` 값을 씀(로컬 테스트용). 둘 다 없으면 관리자 없음 → 새 가입은 계속 대기.
5. **제한**: 가입 요청(새 데이터) **IP당 하루 5개**(b67 은 10), 전체 하루 100개(b67 은 300). 확인 버튼은 로그인 제한(IP당 30회/10분) 안에서.
6. 테스트: test_server b68 항목(관리자 없으면 첫 사용자도 대기, 기존 사용자=승인·admin 표시, 대기 응답·최소 기록, 다시 → 그대로 대기, 관리자 목록·승인·비관리자 403, 승인 뒤 저장, 차단 → 세션 끊김·로그인 403·데이터 유지, 거절, 자기 차단 불가, 차단 해제, IP당 5개), 신규 **test_tracker52**(대기 창·헤더·서버에 아무것도 저장 안 됨·새로고침 뒤 대기 유지 / 관리자 ☁ 메뉴 → 승인 → 승인 확인 → 로그인·평소 창 / 비관리자 버튼 없음 / 차단 → 세션 끊김 / 거절 → 빨간 글). 예전 테스트는 `cf_dev.Dev(..., approval=False)` 기본값이 `AUTO_APPROVE=1` 을 넘겨 승인 없이 동작(**운영 wrangler.toml 에 AUTO_APPROVE 넣지 말 것**). 12·19·23·24·25·29·46~52·test_server 통과.
7. 백업(변경 전): /workspace/backup/b68_before_20261012_120119.json (users·sessions·meta, 600). D1 스키마는 Worker 가 approval 표를 자동 생성. Worker Version fc32d5c1 (12:13 KST; ADMIN_USER secret 12:02 KST). 스크린샷 /workspace/maple-boss-tracker/oct12f_pending.png, oct12f_admin.png.

## 2026-10-12 b67 (초대 비밀번호·입장 화면 폐지 → '캐릭터 추가'에서 본계정 키로 로그인 · 공개 접속 남용 방지 · 다크 전용)
(src 수정→build→테스트→main 일반 push, Worker 는 `cd server && PATH=~/.n22/bin:$PATH npx wrangler deploy`. HANDOFF 기록은 항상.)
1. **입장 화면(#svGate)·초대 비밀번호 없음**: bossmaple.pages.dev 는 바로 대시보드(로그인 전 = 빈 화면 '캐릭터를 추가하세요'). `svGate()` 는 예전 #svGate 를 지우는 빈 함수, `svInvite`·기기 표 요청 삭제. 예전 b62·b66·친구 초대 설명은 이 항목으로 대체됨.
2. **로그인·가입 = 왼쪽 위 '캐릭터 추가'(+ 추가)**: 세션이 없으면(`svNeedMain()` = 서버 모드 && !(svTok && gdMeta.on)) 창에 **본계정 API 키 칸 + [등록] 버튼만**(`#svMainSec`, `.addm.svmain` 이 다른 `.addsec` 숨김 — 부계정·예비 키·캐릭터 목록 없음), 아래 키 받는 법 링크와 `Data based on NEXON Open API`. 등록 = 예전 입장 화면 로그인과 같음(POST /api/login: 계정 생성/복원 → 금고 v2 키·데이터·소식 읽음·세션 복원) → 성공하면 같은 창이 **지금까지의 캐릭터 추가 창**으로 바뀜. 부계정/예비 키를 넣으면 '등록 완료' 자리에 빨간 **'이미 등록된 부계정 API입니다.'**(`#svMainSt .keyrej`, #ff5a5a), 잘못된 키는 넥슨 오류 문구 빨간 글. 창을 닫았다 열면 지워짐. ☁ 헤더 '☁ 로그인'·401(만료) 때도 이 창. 로그아웃은 ☁ 메뉴 그대로 → 다시 이 상태. github.io(드라이브 모드)는 변화 없음.
3. **서버(Worker, health v:'b67')**: 세션 생성에 SITE_PASS 불필요(`checkDevice` 삭제, device 값 무시, /api/invite 는 예전 캐시 클라이언트용으로 남김). 남용 방지(D1 `rate` 고정 창, IP 는 해시): 로그인 **IP당 30회/10분**, 새 사용자 생성 **IP당 10명/일 + 전체 300명/일**, 모든 API **IP당 읽기 300/분·쓰기 120/분**(PC방 공유 IP 고려, 기존 세션별 읽기 90/분·저장 20/분, 사용자별 저장 40/분, keycheck 30/10분은 그대로). 크기: 데이터 **사용자당 최대 512KB**(넘으면 413 '최대 512KB, 지금 NKB'; 현재 사용자 데이터 ≈54KB), 요청 본문 Content-Length 로 먼저 거절(state 576KB, 그 외 64KB), 기록(history) **10개** 유지, 데이터당 넥슨 계정 **40개**(link/subkeys). EPOCH_KEY 그대로 → **기존 세션 강제 로그아웃 없음**, 사용자·데이터 그대로. Worker Version af44c079 (11:38 KST 배포, health v:b67, 배포 뒤 D1 개수 배포 전과 같음·기존 세션 1개 그대로).
4. **다크 전용**: 오른쪽 위 라이트/다크 버튼(#themeBtn) 삭제, `applyTheme()` 은 항상 dark, build.py 가 `<html data-theme="dark">` 로 출력, 저장된 `S.theme` 은 load 때 지움(prefers-color-scheme 무시). 라이트 전용 CSS(`[data-theme=light] .expbar>i`, `html[data-theme="light"] #svGate…`) 삭제. style_v1.css 의 :root 기본 변수와 `html:not(.dark)` 규칙은 다크에서도 쓰여 남김. 예전 섹션의 '라이트' 색 설명은 이제 무시.
5. 테스트: test_server(초대 없이 로그인·device 무시, 530KB→413·500KB 저장, 64KB 넘는 본문 413, 새 사용자 11번째 429·기존 사용자 로그인 됨, IP 쓰기 121번째 429), test23·24·25·29·46·49(입장 화면 → 본계정 키 창 흐름), test50(첫 화면·다크 전용 이전·본계정 키 창·모바일·github.io), 신규 **test_tracker51**(처음 온 사람 → 본계정 키만 → 잘못된 키 → 등록 → 일반 창 → 부계정 키 추가 → 로그아웃 → 부계정 키로 로그인 시 빨간 글 → 새 PC 본계정 키로 데이터·키 복원), 12·14·19·47·48 테마 버튼 기대 제거. 전체(run_all.sh) 결과: 새·수정 테스트 전부 통과. 예전부터 실패(이번과 무관, HEAD 에서도 같음): 8·10·16(시간 초과), 9·30(가격 꼬리말 문구), 13·14(박스에 떠 있는 다른 :8787 서버(/workspace/maple-boss-tracker)를 읽음 — 예전 index)·15(예전 UI 기대), 27(아바타), 28(제목 이름).
6. D1 백업(변경 전): /workspace/backup/b67_before_20261012_112957.json (600). D1 스키마 변경 없음. 스크린샷 /workspace/maple-boss-tracker/oct12e_landing.png, oct12e_mainkey_modal.png, oct12e_mainkey_modal_mobile.png.

### b67-secrets (기록만, 코드 변경 없음)
- 2026-10-12 11:31 KST 저장소 Actions secrets 를 메이플 봇이 교체: `NEXON_API_KEY` = 사용자의 새 NEXON Open API **SERVICE 등급** 키(500/s, 2,000만/일), `NEXON_API_KEY2` = 사용자의 예비 **개발 등급** 키. 예전 키 삭제. update-feed 워크플로가 새 키로 성공. 박스 환경 사본: `NEXON_SERVICE_KEY`, `NEXON_BACKUP_KEY`. 코드 변경 불필요.

## 2026-10-12 b64 (등록된 API 키 전체 초기화 · 키 다시 추가 시 예전 계정 칸에 재연결 · 다른 데이터 키 추가 차단)
(src 수정→build→테스트→main 일반 push, Worker 는 `cd server && PATH=~/.n22/bin:$PATH npx wrangler deploy`. HANDOFF 기록은 항상.)
배경: b62 Worker 배포(10:35) 뒤 사용자가 집 PC(키 전부 있음)보다 먼저 PC방에서 대표 키로 로그인 → 금고 v2 가 부계정 0개 상태로 만들어짐(원격 D1 확인: keyvault2 1행, keyreg 0행, acct_role main 4행). 사용자가 '캐릭터 추가 창의 API 키(대표·부계정·예비) 전부 초기화 후 PC방에서 다시 등록'을 요청·확인.
1. **서버(원격 D1) 초기화 — 2026-10-12 10:47 KST**: 사용자 ef4ca70b… 의 `keyvault2`(1행) 삭제, `keyvault`·`keyreg`(이미 0행). `acct_role`(main 4행)·`accounts`(넥슨 계정 연결 9행)·state·state_history·seen·sessions·devices 는 **그대로**.
   - 백업(박스, chmod 600, 내용 출력 안 함): `/workspace/backup/keys_reset_20261012_104640.json`(keyvault2·acct_role·accounts 행) · `/workspace/backup/state_before_b64_20261012.json`(state rev 42 전체, 키 없음).
   - 전/후 행 수 동일: users 3 · accounts 29 · state 3 · state_history 15 · seen 0 · sessions 1 · devices 1 · acct_role 4 · state rev/size/캐릭터 = 42/54192/22. 바뀐 것: keyvault2 1→0.
   - 주의(기록): 첫 DELETE 문의 하위 질의가 잘못 쓰여(users 표에 user_id 열 없음 → 바깥 열로 해석) 사실상 keyvault2 **전체** 삭제 조건이었으나, keyvault2 는 원래 이 사용자 1행뿐이라 결과는 같음. keyvault·keyreg 는 0행이었음.
2. **기기별 키 초기화 (클라이언트, `KEY_RESET='b64-2026-10-12'`, localStorage `mapleBossTracker.keyReset`)**: 서버 모드에서 이 버전을 기기마다 처음 열 때 한 번 — `settings.accounts[].key` 를 '' 로, `bk`·`bkLabel`·`status` 삭제, `svSubSig`·`svVault`·`svKeyErr` 삭제, 키가 있던 기기는 `svToken` 도 삭제(→ 입장 화면, 대표 키로 다시 로그인; svUser·기준(base)은 유지라 저장 안 한 변경도 3-way 병합). 계정 칸(id·이름·ah·main), 캐릭터·accId·보스·수익·기록·소식 읽음은 안 건드림. 다시 전원 초기화 = KEY_RESET 값 바꿔 배포(+ 서버 금고 삭제). 서버 state 에는 원래 키가 없어서 병합으로 키가 돌아오지 않음(key/bk 는 GD_LOCAL 경로).
   - 기존 서버 모드 테스트(23·24·25·29·46)는 미리 넣는 localStorage 에 keyReset 표시를 추가(안 그러면 키가 지워짐).
3. **키 다시 추가 → 예전 칸에 재연결** (`keyRelink(a,all)`, `openImport` 안): '+ API 키 추가'로 넣은 키의 캐릭터 목록(ocid)이 '키 없음' 칸에 연결된 캐릭터와 겹치면 그 칸에 키(·예비 키·ah)를 넣고 새 칸은 지움 → 캐릭터 accId·계정 이름 그대로, 중복 칸 없음. 대표 키는 로그인 때 ah 로 본계정 칸에 들어감(기존). 금고 복원(`svAfterLogin`)은 ah 가 없는 예전 칸이면 **이름(label)** 으로도 짝지음(실데이터의 부계정 칸 3개는 ah 가 없었음).
4. **다른 데이터에 묶인 키 추가 차단**: Worker `POST /api/keycheck {key}`(인증, 세션당 30회/10분, 저장 없음) — keyreg 에 다른 사용자 키로 있거나, 그 넥슨 계정이 **캐릭터가 있는** 다른 데이터에 연결돼 있으면 409 `sub_key` '이미 등록된 부계정 API입니다.'(빈 데이터는 /api/subkeys 가 옮기므로 통과). 클라이언트 `addAccount()`(이제 async)·`bkAdd()` 가 저장 전에 `svKeyCheck()` → 거부면 키를 저장하지 않고 키 목록 아래 `#accRej` 줄에 '등록 완료' 자리 대신 빨간 글(#ff5a5a, 600, .9rem = 입장 화면 경고와 같은 모양)만, 예비 키는 bkerr 빨간 글. 창 닫으면 사라짐. 예전 Worker(404)·넥슨 오류면 예전 흐름대로 진행. Worker 배포 Version 4776323e (10:51 KST), EPOCH_KEY 그대로라 강제 로그아웃 없음.
5. 테스트: test_server.py(b64 keycheck 4개), 신규 **test_tracker49**(초기화 1번만·키만 비움·캐릭터/연결 유지·세션 지움 / 대표 키 로그인 → 본계정 칸 / F·G 다시 추가 → 예전 a2·a3 칸 / 남의 키 → 빨간 글·저장 안 함 / 집 PC 예전 키 → 비운 뒤 대표 키로 PC방 등록분만 복원·중복 칸 없음·금고에 예전 키 안 올라감). 통과: test_server, 4, 5, 23, 24, 25, 29, 36, 46, 49. run_all.sh 에 49 추가.
6. 사용자 할 일: ① PC방 페이지 새로고침(F5) → 입장 화면 → 대표 키 로그인 ② 캐릭터 추가 창에서 부계정 키를 '+ API 키 추가'로 하나씩, 예비 키는 각 계정 줄의 예비 칸에 등록(2초 뒤 서버 금고에 보관, ☁ 메뉴에 '키 보관 실패'가 없는지 확인) ③ 집 PC: **페이지를 새로고침한 뒤**(예전 버전 탭으로 로그인하면 예전 키가 다시 금고에 올라갈 수 있음) 대표 키로 로그인 → 키가 다 돌아옴.
## 2026-10-12 b66 (NEXON Open API 표기 — 입장 화면·첫 화면) **(b67: 초대 비밀번호·입장 화면 폐지 — 지금은 캐릭터 추가 창에서 본계정 키만)**
(같은 방식: src 수정→build→테스트→`git checkout -- *.png`→`git pull --rebase`→main 일반 push. HANDOFF 기록은 항상.)
**이유**: 넥슨 Open API 서비스 단계 신청 — 모든 화면에 출처 표기.
1. **서버 모드 입장 화면**(`#svGate`, bossmaple.pages.dev): 초대 비밀번호 단계·대표 키 로그인 단계 모두 하단에 `Data based on NEXON Open API` (`.svgattrib`). 기존 `.foot` 과 같은 작은 muted·가운데. 화면 하단 고정이라 **스크롤 없이** 1280×800·모바일에서 보임. 키 안내(`details`)가 길어도 `.svgbox` 만 스크롤·표기는 밖.
2. **다크/라이트**(b67: 다크 전용, 무시): 라이트면 입장 상자·배경도 라이트 톤, 표기 색 `#8a7765`(=`--muted`). 다크는 `#9a9aa8`.
3. **github.io**(게이트 없음): 메인 `.foot` 에 이미 같은 문구 있음 + 캐릭터 0명 첫 화면(`emptyView`)에도 `.empty-attrib` 로 동일 문구(스크롤 없이 보이도록).
- 테스트: 신규 **test_tracker50**. 스크린샷 `/workspace/maple-boss-tracker/oct12d_attrib_pass.png` · `oct12d_attrib_key.png`.

## 2026-10-12 b65 (결정석 가격: 매일 19:00 KST 확인 + 마지막 확인 날짜 갱신)
(같은 방식: 최소 수정→`git pull --rebase`→main 일반 push. HANDOFF 기록은 항상. src/·server/ 키 리셋 작업과 겹치지 않게 워크플로·스크립트·HANDOFF 만.)
1. **스케줄**: `update-prices.yml` cron `17 3 * * 5`(금 12:17 KST 대비) → **`0 10 * * *`(매일 19:00 KST)**. GitHub cron 은 수분~십여 분 늦을 수 있음. `workflow_dispatch` 유지.
2. **마지막 확인**: `update_prices.py` 가 확인 성공 시 가격 동일해도 `checkedAt=오늘(KST)` 로 쓰고 커밋(b40부터 이미 매 성공마다 — 7일 하트비트 아님). 사이트 결정석 가격 카드 `(…, 마지막 확인 YYYY-MM-DD)` 가 이를 표시.
3. **피드 경로 유지**: `update_feed.py` 의 테섭/패치 새 글 → 가격 확인·`checkedAt`/`upcoming`/본섭 적용은 그대로(워크플로 미변경).
4. 확인: Actions → 결정석 가격 자동 갱신 → Run workflow → 끝나면 `prices.json` checkedAt=오늘, 라이브 카드 '마지막 확인' = 오늘.

## 2026-10-12 b63 (캐릭터 추가 모달: 키별·전체 등록 캐릭터 수)
(같은 방식: src 수정→build→테스트→`git checkout -- *.png`→`git pull --rebase`→main 일반 push. HANDOFF 기록은 항상.)
1. **캐릭터 추가(+ 추가) 모달** 키 행: 활성화된 키의 `등록 완료` 옆에 ` · N캐릭 등록 중` (N = 그 계정 `accId` 로 연결된 대시보드 캐릭터 수). 본계정·부계정·예비 키 모두 동일(예비 키는 같은 계정 수). 0도 표시(`· 0캐릭 등록 중`).
2. 모달 상단 **🔑 넥슨 API 키** 옆에 `(총 N캐릭 등록 중)` = 위 키별 수의 합. **수동 추가·키가 없는 캐릭터(`accId` 없음)는 제외.**
3. 문구 색 = 기존 `등록 완료` 초록 `#3ccf6e` (`.regok` / `.keycnt`). 다크·라이트 모두 동일. 모달 폭 640→720, 행·헤더 `nowrap` 으로 **한 줄 유지**(잘림·말줄임 없음).
4. 캐릭터 추가/삭제 시 `render()` → 모달이 열려 있으면 `renderAccList()` 재호출로 **즉시 갱신**.
- 코드: `linkedOf`·`regOkHtml` (`src/app.js`), `#accKeyTotal` (`src/body.html`), CSS b63 (`src/extra.css`).
- 테스트: 신규 **test_tracker48**(본3/부2/0·예비키 동일·수동 제외·총합·초록·한 줄·라이브 추가/삭제·라이트). test_tracker28 acc row 검사 통과(새 문구). test13 은 박스에 떠 있는 예전 :8787 서버를 읽어 실패할 수 있음(이번 변경과 무관 — 자체 포트 쓰는 48·28·36 으로 확인).
- 스크린샷: `/workspace/maple-boss-tracker/oct12c_keycount.png`.

## 2026-10-12 b62 (메소왕 1위 초상화 · 누적 수입/누적 득템 아이콘 크기·가운데 정렬 · 부계정/예비 키 복원 · 부계정 키 로그인 차단 · 강제 로그아웃 · 소식 읽음 동기화)
(같은 방식: src 수정→build→테스트→`git checkout -- *.png`→`git pull --rebase`→main 일반 push. HANDOFF 기록은 항상.)
1. **메소왕 제목 아이콘** = 현재 1위 캐릭터 초상화(`kingHtml`: `top1`, `avatar(c,'hking')` 36px). 1위 누적이 0이거나 기록이 없으면 예전 메소 아이콘.
2. **누적 수입**(결정석 분석 맨 위) · 3. **누적 득템**(득템 분석 맨 위): 두 카드의 `.stats.s3` 에 `kbig` 클래스 → 라벨 앞 아이콘(메소 주머니·보스·검마·에픽빔 1위 아이템·반지 상자·**블링크**) 전부 32×32 같은 크기, 라벨 글자는 `<span class="kt">` 로 감싸 flex `align-items:center` → 아이콘 세로 가운데(실측 차이 0px). CSS `src/extra.css` 끝 b62 블록. 보스 탭 정보 칸(.stats.s3, kbig 없음)은 그대로.
   - 테스트: test_tracker44 에 b62 검사(32px·가운데 ±1px·메소왕 초상화·기록 없으면 메소 아이콘). 스크린샷 /workspace/maple-boss-tracker/before_*.png → oct12b_total_top.png · oct12b_loot_top.png · oct12b_mesoking.png.
4. **PC방에서 대표 키로 로그인했더니 부계정 키가 없던 문제** — 로그인 구조(정리, **b67 에서 ① 폐지·입장 화면 없음 → 캐릭터 추가 창 본계정 키**): bossmaple.pages.dev = 서버 모드. 입장 화면 ① **초대 비밀번호**(기기당 1번, POST /api/invite → localStorage `mapleBossTracker.svDevice`) ② **대표 키**(넥슨 API 키, POST /api/login → 세션 `mapleBossTracker.svToken`). 사용자가 말하는 '비밀번호' = 초대 비밀번호. 데이터(S)는 서버 state 에 키 없이, 키는 **금고**(D1, 암호문)에만.
   - 원인(코드로 확인한 것, 원격 D1 은 자격 증명이 없어 직접 확인 못 함):
     a) 금고(v1)가 **대표 키 문자열 그대로**로 암호화 → 대표 계정의 다른 키(예비 키·재발급 키·계정 2개짜리 키)로 로그인하면 'locked' → 부계정 키 0개. 그 기기에서 키를 하나라도 추가하고 저장하면 금고를 그 작은 목록으로 **덮어씀**.
     b) 키는 내용 비교(contentSig)에서 빠져 있어 **키만 추가하면 저장 대상이 아님** → 금고 업로드(svSyncSubKeys)는 다른 변경으로 [저장]을 눌렀을 때만 실행. 그 전에 다른 PC 로 가면 키 없음.
     c) 금고 업로드가 실패(넥슨 429, 예비 키 불일치, 그 부계정이 예전에 따로 로그인해 다른 데이터에 묶임 linked_elsewhere 등)해도 **'올림' 표시(svSubSig)를 해 버려 다시 시도 안 함**(토스트 한 번뿐).
     d) 로그인 때 금고가 열리기만 하면 이 PC 키와 같다고 보고 '올림' 표시 → 이 PC 에만 있던 키가 영영 안 올라감.
   - 수정: 서버 **금고 v2** (`keyvault2`, 키 = HKDF(ID_PEPPER + 대표 넥슨 계정 account_id) — account_id 원본은 저장 안 함, 넥슨이 그 계정 키에만 알려 줌 → 대표 계정의 어떤 키로도 열림; v1 은 대표 키 로그인 때 자동 이전) · 키만 바뀌어도 2초 뒤 금고 보관(`save()`→`svKeysSoon`, b62 로그인한 기기만) · 실패하면 '올림' 표시 안 함 + ☁ 메뉴에 '⚠ 키 보관 실패' (`mapleBossTracker.svKeyErr`) · 로그인 때 이 PC 키가 금고에 다 있을 때만 '올림' 표시, 아니면 합친 전체를 다시 올림 · 금고를 못 연 기기(`mapleBossTracker.svVault`='locked')는 금고를 덮어쓰지 않음 · 예비 키 이름(bkLabel)도 금고에 · 부계정이 예전에 따로 로그인해 생긴 **빈** 데이터(캐릭터 0명)에 묶여 있으면 옮김(캐릭터가 있으면 409 유지).
5. **부계정/예비 키로 로그인 차단**: 서버 `keyreg`(sha256(ID_PEPPER:key:키) → user, 종류 sub|bk — 키 원본 없음) + `acct_role`(계정 해시 → main|sub). 로그인 때 키 해시가 등록부에 있거나, 그 넥슨 계정이 부계정 역할이고 대표 역할 계정이 없으면 403 `sub_key` → 입장 화면 빨간 글 **'이미 등록된 부계정 API입니다.'**(예비 키도 같은 문구 — **대표 계정의 예비 키도 차단**, 사용자 요청대로). 등록부는 부계정 키 저장 때와 대표 키 로그인(금고 열림) 때 다시 씀. /api/link 로 연결한 계정 = sub. 부계정 목록에서 빼도 그 계정은 sub 로 남음(데이터에 연결돼 있으므로).
6. **강제 로그아웃**: **(b67: 초대 비밀번호·입장 화면 폐지 — 지금은 캐릭터 추가 창에서 본계정 키만)** 새 Worker 첫 요청 시각 = D1 meta `auth_epoch_b62` → 그 이전 세션·**기기 표(초대 비밀번호)** 무효 + 한 번 삭제 → 모든 PC 가 초대 비밀번호 + 대표 키 다시 입력. state·history·금고는 안 건드림. 클라이언트: 401 이면 입장 화면 + '로그인이 만료되었어요…' (이 PC 데이터·키는 지우지 않음) **(b69: 폐지 — 이제 401 이면 이 PC 데이터 전부 지움)**, 같은 사용자로 다시 로그인하면 기준(base·rev) 유지 → 저장 안 한 변경도 묻지 않고 3-way 병합. 다시 전원 로그아웃 = worker.js `EPOCH_KEY` 이름 바꿔 배포.
7. **소식 읽음 동기화**(추가 요청): 서버 `seen` 표 + `GET/PUT /api/seen`(합집합, 최근 1500개). 로그인·페이지 열 때 서버 읽음과 합치고(이 PC 에만 있던 것도 올림), 글 클릭하면 1.5초 모아 PUT. 서버 모드만(github.io 드라이브 모드는 예전처럼 브라우저별). 예전 Worker 면 404 → 조용히 건너뜀.
   - **배포 상태(2026-10-12)**: 사이트(클라이언트)는 push 로 배포됨 — 예전 Worker 와도 동작(새 기능만 비활성). **Worker 는 배포 못 함**: 박스에 wrangler 로그인·Cloudflare 토큰·ID_PEPPER/SITE_PASS 사본(/home/box/.config/ggoolzip/)이 없음(박스 초기화로 보임). 저장소 secret CLOUDFLARE_API_TOKEN 은 Pages 전용이라 쓰지 않음. → 4(서버 부분)·5·6·7 은 **Worker 배포 순간 적용**되고 6(전원 로그아웃)도 그때 자동으로 일어남. 배포: `cd server && npm install && npx wrangler login && npx wrangler deploy` (Node 22). D1 schema 실행 불필요. 배포 후 할 일: 키가 다 있는 PC(집 PC)에서 초대 비밀번호+대표 키로 다시 로그인 → 그 PC 의 키 전체가 금고 v2 로 올라감 → 다른 PC 는 대표 키만으로 전부 복원.
   - 테스트: test_server.py(b62 항목: 부계정/예비/연결 계정 로그인 403, 재발급·다른 키로 금고 v2 열림, v1→v2 이전, 빈 데이터 옮김/캐릭터 있으면 409, 읽음 합집합, 기준 시각 이전 세션 401·기기 표 need_invite·데이터 그대로; 테스트 도우미 tests/v1seal.mjs), 신규 **test_tracker46**(A: 키만 추가 → 금고·등록부, 읽음 저장 / 새 PC B: 대표 키 → 키 5개·예비 이름·데이터·N 없음 / 새 PC C: 부계정·예비 키 → 빨간 글 / A 예전 세션 → 입장 화면, 이 PC 데이터 유지 → 비밀번호부터 다시 → 저장 안 한 변경 유지·서버 반영 / 새 PC D: 전부 복원), test_tracker24 금고 표 이름 수정. 박스에 Node 22 를 /home/box/.local/node22 에 다시 설치함(wrangler dev 테스트용). 스크린샷 /workspace/maple-boss-tracker/oct12b_subkey_warn.png.
8. **'수익을 기록할까요?' 창** (1~7 push 뒤 추가 요청): 득템 축하 **바로 전**마다 `askRev()` → `#revModal`. 제목 앞 아이템 아이콘(반지 결과·칠흑 장신구·연마석은 고른 결과 아이콘) + '수익을 기록할까요?', 그 아래 작은 안내 문구 **'이 아이템의 경매장 최저가 시세를 적어주세요.'**(`#rvGuide`, 사용자가 매번 직접 입력), 분배면 'N인 분배 · 입력한 금액 ÷ N'. 몸통 = 왼쪽 [숫자 입력][억 메소] 한 줄 + 아래 가운데 주황(#ff8a1f) '기록하기', 오른쪽 '아니오'. 아니오·Esc·바깥 클릭 = 기록 없이 축하. Enter = 기록하기. 빈 값/0 → '금액(억 메소)을 넣어 주세요'.
   - 창 안 뜸: 반지 상자 꽝(x), 블빵패배(l) — 축하도 없으므로.
   - 저장: `c.drev`(주간)/`c.mdrev`(월간)[보스|아이템 키] = `{m: 억×1e8 ÷ 나눔수(반올림), a: 입력한 억, p: 나눔수, i: 아이템/결과 키}` — 획득 기록(보스·아이템당 기간 1번)마다 하나. 나눔수 = 파티>1 이고 블빵승리(w)·꽝(n)이 아니면 파티 인원(분배·반지 상자), 1인·블빵승리 = 1. 획득 취소 → 그 기록도 삭제, 주간/월간 초기화 때 삭제, [취소](pend) 되돌림 포함. S 안에 있으므로 서버 state·드라이브로 동기화(키 아님). 주간/월간 기록(history perChar.revs)으로 넘어감.
   - 이번 주 수익(`revPanel` → `itemsInline` opts.revs): 기록한 아이템 줄 바로 아래 금액 `.dlrev` — 1pt 작게(`calc(1em - 1pt)`), 핫핑크 #ff4fa3.
   - 득템 분석 탭: `#lootTop` 바로 아래 **'아이템 판매 수익'** 카드(`salesHtml`, `#salesCard`) — 총 판매 수익(억·메소·건수) + 아이템별 합계(`totalData().sales`, 지난 주/월 기록 + 이번 주/월).
   - 기존 테스트(7·8·11·21·27·28·31·32·37)는 드롭 클릭 흐름이 바뀌어 페이지 열 때 '아니오' 자동 클릭(MutationObserver init script)을 넣음. 신규 **test_tracker47**(1인 2.5억=250,000,000 / 2인 분배 ÷2 / 블빵승리 전부 / 취소 시 삭제 / 블빵패배·반지 꽝 창 없음 / 아니오·Esc / 분홍 1pt 작게 / 판매 수익 카드 / perChar.revs / 라이트·모바일). 스크린샷 /workspace/maple-boss-tracker/oct12b_revmodal.png(+ _light, _mobile, oct12b_revpink.png, oct12b_salescard.png).

## 2026-10-12 b61 (못 가진 아이템 목록 가로 스크롤 제거 · 낮은 창에서 카드 잘림)
(같은 방식: src 수정→build→테스트→main push, gh 로그인 필요. HANDOFF 기록은 항상.)
1. **내가 가지지 못한 아이템 목록** (b53 4번 미해결 해결): 가로 스크롤 래퍼 제거(`.misswrap` overflow-x:hidden). 표 칸 = 보스 목록(`td.missb` 안 `.missbl` flex-wrap, 남는 폭 전부) · 아이콘(`td.missi`) · 이름(`td.missn`, 항상 한 줄, width 1%). 구분점 '·' 은 `.missbn::after`.
   `fitMiss()` 는 **줄마다 따로**: 13px 한 줄 → 안 들어가면 그 줄만 0.5px씩(최소 10.5px) → 그래도 안 되면 그 줄 보스 아이콘 생략(`.noico`) 후 13px부터 다시(최소 10px) → 그래도 안 되면 11px 로 **보스 묶음(이름+난이도) 단위 줄바꿈**(묶음 안·아이템 이름은 절대 안 끊김). 예전엔 표 전체 글자를 9px 까지 줄이고도 스크롤됐음.
   - 실측(테스트 데이터, 보스 8개 묶인 줄): 1920/1600 = 전부 한 줄(긴 줄만 12px), 1366·1280 = 8보스 줄 1개만 2줄(아이콘 생략 11px), 1100~1000 = 6·8보스 줄 2~3줄. 1000~1366px 에서 8보스 줄을 10px 이상으로 한 줄에 넣는 건 폭이 물리적으로 부족(9px 로도 1280 에서 241px 초과)해서 보스 칸 안 줄바꿈으로 처리 — 가로 스크롤·잘림은 없음.
   - 모바일(≤760px): 행 = 위 [아이콘 이름] / 아래 보스 목록 전체 폭(grid), 잘림 없음.
   - 테스트: 신규 test_tracker45 (1920~320px 모든 쪽: 가로 넘침 0, 이름·보스 묶음 한 줄, 글자 ≥10px, 1600 이상은 줄바꿈 0). 스크린샷 /workspace/maple-boss-tracker/oct12_before_*.png · oct12_after_*.png.
2. **낮은 창에서 아래 카드 잘림** (1366x650·1280x720·1024x700·1280x560 등):
   - 원인: 왼쪽 사이드바 `.side-sticky` 는 sticky 이고, `feedFit()` 이 남은 높이가 모자라면 **썬데이 카드를 display:none** 으로 숨겼음(캐릭터가 많거나 창이 낮으면 1920x1080 에서도 숨김). 오른쪽 `.rcol` 은 sticky + 높이 100vh−172px 고정이라 수익 패널·결정석 가격 목록이 작은 칸 안에서만 스크롤됨.
   - 왼쪽: `feedFit()` 이 `h-gap < 소식 최소 + SUN_MIN(140)` 이면 사이드바에 `.side-flow`(position:static) → 소식 카드 `FEED_ROW*FEED_FLOW_ROWS(5)+70`px, 썬데이 `SUN_FLOW_H`(320px) 고정, 썬데이 안 숨김 → 페이지가 길어지고 스크롤로 전부 보임. 공간이 충분하면 예전 그대로(sticky, 남은 높이 1:2 로 나눔, 페이지 안 길어짐, 쪽 번호 유지).
   - 오른쪽: `@media(min-width:1181px) and (max-height:759px)` 에서 `.rcol` 일반 흐름(static, 높이 자동), 수익 패널·가격 카드 높이 제한 없음, 가격 목록 `.pc-list` 만 최대 440px(그 안 스크롤). 760px 이상 높이는 예전 그대로. (≤1180px 폭은 원래부터 일반 흐름)
   - 테스트: test_tracker45 (2) — 캐릭터 8명/1명 × 4개 크기 × 4개 탭: 소식·썬데이(·보스 탭 수익/가격/초기화) 카드가 숨김 없이 스크롤해서 화면 안에 완전히 보이고 안쪽 잘림 없음; 1920x1080·1280x800(1명)은 sticky·페이지 안 길어짐. 예전 코드에서 35개 실패 확인. test_tracker16 의 '낮은 창 = 썬데이 숨김' 기대값을 새 동작으로 수정(이 테스트는 원래 타임아웃으로 거기까지 못 감).
   - 스크린샷: /workspace/maple-boss-tracker/oct12_before_side_*_bottom.png → oct12_after_side_*_bottom.png (맨 아래로 스크롤한 보스 현황).
- 전체 테스트(run_all.sh) 2026-10-12: 새 실패 없음. 이번 변경 전 HEAD 에서도 실패하던 것: test_tracker8·10·16(타임아웃), 9·30(푸터 문구), 13·14·15(예전 UI 기대값). test16 은 타임아웃 때문에 낮은 창 검사까지 못 감.

## 2026-10-12 b62-배포 (Worker 배포 완료)
- 2026-10-12 10:35 KST 메이플 봇이 Worker `ggoolzip-sync` 배포 완료(Version 82680d9f). 사용자가 박스 브라우저에서 Cloudflare(980330k@naver.com) 로그인 → wrangler OAuth. wrangler login 의 콜백이 오래된 탭 요청(state 불일치)으로 계속 실패해서, 같은 client_id·PKCE 로 직접 받는 스크립트(/tmp/cfl/login.mjs)로 토큰을 받아 ~/.config/.wrangler/config/default.toml 에 저장함. Node 22 는 ~/.n22/bin.
- 기존 secret(ID_PEPPER, SITE_PASS_HASH)은 Cloudflare 에 그대로 남아 있어 재설정 불필요. D1 schema 실행 안 함.
- 이 배포로 b62 의 4(서버 부분)·5·6·7 이 켜졌고, 6(전원 로그아웃)이 새 Worker 첫 요청 때 자동으로 일어남(데이터 삭제 없음).
- 사용자 할 일: **(b67: 초대 비밀번호·입장 화면 폐지 — 지금은 캐릭터 추가 창에서 본계정 키만)** 부계정 키가 다 있는 PC 에서 초대 비밀번호 + 본계정 키로 다시 로그인 → 전체 키가 서버 금고로 올라감.

## 2026-10-11 b53 (사용자 요청 10개 일괄) — 다음 봇 인수인계
작업 전 `gh auth status` 로 GitHub 로그인(ggoolzip-wq) 확인 필요. 로그인이 없으면 사용자에게 `gh auth login`(기기 코드 승인)을 부탁할 것. 수정은 `src/` 만, `python3 tools/build.py` 후 `git pull --rebase` → 일반 push(강제 push 금지).
1. **반짝이 가루** (`src/extra.css` `.spk`): 예전 ✦ 두 개 → `.spk::before/::after` 두 겹의 아주 작은 radial-gradient 점들이 글자 전체 위에서 어긋난 주기(`spkd1` 1.1s, `spkd2` 1.4s, steps)로 깜빡·위치 이동. 모션 줄이기면 정지. 1~3위 이름(`.spk`)에 적용.
2. **아이템 순위** (`itemPri()`): 광휘 1 · **익셉셔널 해머(set '해머')·창세의 뱃지 1.5** · 신념 연마석·칠흑 전부(**루즈 컨트롤 머신 마크·커맨더 포스 이어링도 이제 다른 칠흑과 같은 2**) · 이하 그대로. 해석: 사용자 문장이 모호했음(커포·루컨마를 1.5로 올린다는 뜻일 수도 있음) → '해머·창세=1.5, 루컨마·커포=칠흑과 동급(2)'로 해석.
3. **녹옥 반지 상자**: `RING_OFF`(app.js) — `dropsFor`에서 제외, `dropsOff`(회색 칩 .drop.off, 클릭 불가)에 포함 → 못 가진 아이템 목록에서도 사라짐. ITEMS·예전 기록은 그대로.
4. **못 가진 아이템 다중 보스**: `missingItems()` 가 아이템마다 `list`(그 아이템을 주는 모든 보스·난이도, 결정석 싼 순) 반환, `missGroups()` 가 같은 보스 난이도를 묶어 '림보 (노말)(하드)' 로 표시, 보스는 ' · ' 로 이음. 행이 길어 한 줄 유지 위해 보스가 4개 이상 묶이면 보스 아이콘 생략 + `fitMiss()` 가 글자를 13px→최소 9px 로 줄이고, 그래도 넘치면 표 래퍼 가로 스크롤(1280px 이하에선 가장 긴 행이 스크롤됨 = 미해결).
5. **3위 안일 때만 글자색** (`itemCol()` + `rankTable` 의 `o.col`, CSS `.ic-pink/.ic-purple/.ic-sky`): 광휘 세트·익셉셔널 해머 = 핫핑크(#ff4fa3), 칠흑 세트·혼돈의 칠흑 장신구 상자 = 보라(#b36bff), 연마석류·소울 에테르류 = 하늘(#5fd0ff). 적용 표: 에픽빔왕, 상자깡(전부 보라). 4위 이하·못 가진 목록은 색 없음. 창세의 뱃지(set 칠흑)는 보라, 에테르넬 등은 색 없음.
6. **보스 옆 난이도 표기** `dlvHtml(d)` = `<span class="dlv dlv-<난이도>">(노말)</span>` (색은 b55 의 `.dlv-*`). 추가한 곳: 이번 주 수익 패널 아이템 줄(`dropLine` 7번째 인자 diff, `itemsInline` opts.diffOf — `cfgDiff(c)`=현재 설정 / `tagDiff(p,c)`=기록의 '이름(난이도)' 태그), 결정석 가격 카드 줄(`priceCard` row, 예전 muted 일반 글씨 → 색 글씨), 보스 별 누적 획득 아이템(`bossLootHtml`), 반지 상자 모달 부제(innerHTML). **캐릭터 정보의 보스 드롭 표(`bossRow`·`dropsHtml`, `.pill`)는 그대로.** 12/12 덮개 '검마 격파 필요'에는 넣지 않음(test_tracker12 가 문구 정확히 검사).
7. `.dlv{font-weight:800}` — 괄호+난이도는 항상 굵게.
8. **시드링 획득 타율**: `.ringsum` 1.1rem 굵게(한 줄 nowrap), 라벨 `.rslab`(반지 상자 결과) 초록 #3fd07a, 기댓값 `.ringexp` .7rem·색 없음(inherit).
9. **블빵 카드**: `.bbtbl tr:last-child td{border-bottom:0}` 로 선 2개→1개, `.bbpart+.bbpart` margin/padding 16px (이 카드에만).
10. **주별 누적 결정석 메소** → `cumLineChart()` 라인 차트(누적 선+면+점, y축 눈금 억 단위, 이번 주 점은 주황). 예전 `weekChart()` 는 쓰이지 않지만 남겨 둠.
- **한 줄 규칙**: 난이도를 붙였다고 두 줄이 되면 안 됨 → 가격 카드는 `fitPriceCard()`(글자 축소), 못 가진 목록은 `fitMiss()`, 시드링은 nowrap. 새 표기를 넣을 땐 1920/1600/1280 에서 높이/잘림 확인.
- **테스트**: 신규 `tests/test_tracker42.py`(+ run_all.sh 에 추가). test_tracker41(반짝이·상자깡 순서·못 가진 목록 list)·test_tracker40(가격 카드 \(난이도\) 표기)는 새 동작에 맞게 기대값 수정. 기존 실패(이번 변경과 무관): test_tracker8(스우 r_red 대기), test_tracker9(card foot 문구)·test_tracker30(price foot 문구) — b45 이후 푸터 문구 변경으로 인한 예전 테스트 불일치. test_tracker29 는 `/workspace/shots` 폴더가 있어야 함. 테스트가 루트 PNG(screenshot.png 등)를 덮어쓰므로 커밋 전 `git checkout -- *.png` 할 것.
- 미해결/모호: 위 2번 해석, 4번 1280px 이하 가로 스크롤, 6번의 '모든 구간' 은 위 목록만 확인(드롭 외에 보스가 나오는 곳은 이미 난이도 표기).

## 2026-10-11 b54-후속 (반짝이 별·익스트림 주홍·득템왕 색·에픽빔 스포트라이트)
(위 b53 이후 후속, 같은 방식: src 수정→build→테스트→main push. gh 로그인 필요, git push 인증은 `gh auth setup-git`.)
1. **반짝이(.spk) 재설계**: 흰 가루가 글자를 가려서 → `::before/::after` 가 `background-color:currentColor` + 별(✦) SVG `mask-image` 3개씩(4~6px)로, 글자색(아이템 색 포함)과 같은 색, 최대 불투명도 .5/.45 로 은은하게 깜빡(`spkd1` 2.2s, `spkd2` 2.6s·지연 1s). 모션 줄이기면 정지(.3). 가독성 최우선이라 더 키우지 말 것.
2. **익스트림 색**: `.dlv-extreme` #ff6a00 → 주홍 #ff4500 (난이도 색 정의는 이 한 곳).
3. **득템왕 아이템 색**: `lootChips(m, top)` — 득템왕에서 메달(1~3위) 행만 `top=true` → 각 칩 이름 `.ln` 에 `spk` + `itemCol()` 클래스(핫핑크/보라/하늘). 4위 이하·다른 칩 목록(총 획득량 등)은 색 없음. 색 클래스 CSS 는 `.rkname` 의존을 없애 어디서나 적용.
4. **에픽빔 누적 횟수 숫자(.epgold)**: 글자 모양 안에서만 보이는 작은 흰 스포트라이트(radial-gradient 레이어, `epgs` 2.8s)가 금빛 숫자를 훑음. reduced-motion 이면 정지. (참고: 예전 `.lx.aur.epsum` 오로라 스타일은 현재 쓰이지 않음)
- 테스트: test_tracker42 에 위 4개 검사 추가.

## 2026-10-11 b55-후속 (별 반짝이 살짝 강화 · 스포트라이트)
(주의: 위 b55 순위 표 섹션과 별개인 후속 작업. 같은 방식: src 수정→build→테스트→main push, gh 로그인 필요. HANDOFF 기록은 사용자가 말 안 해도 항상 할 것.)
1. 별 반짝이(.spk) 살짝 강화: 별 6→8개(::before 4 + ::after 4), 최대 불투명도 .5/.45 → .65/.6. 글자색(currentColor) 유지, 가독성 우선이라 더 키우지 말 것.
2. **스포트라이트**(`src/extra.css` 끝, `@keyframes spl`): 글자 모양 안에서만 흰 빛이 훑음 = `background-clip:text` + `-webkit-text-fill-color:transparent`, 맨 아래 레이어 `linear-gradient(currentColor,currentColor)` 로 글자색 유지. 강도/속도는 CSS 변수 `--spa`(강도)/`--spd`(주기): 1위 `tr.rk1` 2.2s·.9, 2위 3.2s·.7, 3위 3.2s·.5, `.dlv-extreme` 3.2s·.65(자체 변수라 순위 행 안에서도 이 값). 대상: `tr.rk1~3` 안의 `.spk`(자식 요소 없는 것) · `.spk .bdn` · `.spk .dlv` (메소왕·득템왕(이름·1~3위 아이템 칩)·보스왕·에픽빔왕·상자깡 순위 글자) + 모든 `.dlv-extreme` (익스트림 표기 전부, 주홍 #ff4500 유지). 자식 span 이 있는 `.spk` 에 transparent fill 을 걸면 자식 글자색이 사라지므로 leaf 만 적용. 투명 글자에선 text-shadow 가 빛을 가려 → text-shadow 제거, 순위 글자는 `filter:drop-shadow(0 0 4px currentColor)` 로 글로우 대체. reduced-motion 이면 정지.
- 에픽빔 누적 횟수 숫자의 스포트라이트(`epgs`, b54)는 그대로.
- 테스트: test_tracker42 에 스포트라이트 값 검사 추가.

## 2026-10-11 b56 (순위 행 전체 스포트라이트 · 익스트림 900 굵기·검은 빛)
(같은 방식: src 수정→build→테스트→main push, gh 로그인 필요. HANDOFF 기록은 항상.)
1. **1~3위 행의 모든 글자에 스포트라이트**: `tr.rk1~3` 안에서 자식 요소가 없는(leaf) `td/span/b/strong/small/em` 전부(순위 숫자·횟수·메소량·아이템 이름 등; 👑 `.crown` 이모지·`.rkpad` 제외). 속도/강도는 b55 그대로(`tr.rk1` 2.2s·.9, `rk2` 3.2s·.7, `rk3` 3.2s·.5). `rankNo()` 가 숫자를 `<span class="rkn">` 으로 감쌈(👑와 같은 요소에 섞여 있으면 leaf 가 아니라서). 메소왕·득템왕·보스왕·에픽빔왕·상자깡 등 `tr.rkN` 을 쓰는 모든 순위 표에 자동 적용 — 새 순위 표도 셀 텍스트를 leaf 요소로 만들 것(텍스트+자식 요소 혼합 금지: 투명 글자색이 자식 색을 지움).
2. **익스트림**: `.dlv-extreme{font-weight:900}`.
3. **익스트림 빛 = 검은색**: 빛 색을 CSS 변수 `--splc`(기본 255,255,255)로 바꾸고 `.dlv-extreme{--splc:0,0,0}`; 글자색 #ff4500 유지, 속도/강도 3.2s·.65.
- 테스트: test_tracker42 에 '1위 행 모든 글자' · '익스트림 900/주홍/검은 빛' 검사 추가.

## 2026-10-11 b57 ((익스트림) 검은 눈부심 · 번쩍—쉼 타이밍)
(같은 방식: src 수정→build→테스트→main push, gh 로그인 필요. HANDOFF 기록은 항상.) 익스트림 난이도(`.dlv-extreme`) 스포트라이트만 변경, 1~3위 행 스포트라이트(`spl`)는 그대로.
- 빛 구성(`src/extra.css` 끝 b57 블록, `html body .dlv-extreme×4` 로 우선순위 확보): 어두운 선명 코어(22% 폭, 검정 .98→0) + 넓은 부드러운 헤일로(60% 폭, 검정 .55→0) + 글자색 `currentColor` 바닥층. 지나가는 순간(14%)에만 `filter:drop-shadow` 주황 글로우로 번쩍임. 글자색 #ff4500·굵기 900 유지.
- 타이밍 `@keyframes spx` 2.8s: 0~30%(≈0.84초) 확 지나감, 30~100%(≈1.96초) 정지 후 반복. reduced-motion 이면 animation:none.
- 검은색이 주황 위에서 가독성을 해치면 코어 불투명도(.98)·폭을 줄일 것.
- 테스트: test_tracker42 의 스포트라이트 검사를 spx/2.8s 로 수정.

## 2026-10-11 b58 (이번 주 수익 패널: 월간 보스 합산)
(같은 방식: src 수정→build→테스트→main push, gh 로그인 필요. HANDOFF 기록은 항상.)
- 보스 체크 탭 '이번 주 수익' 패널(`revPanel`)의 '○월 월간 보스 (따로 합산)' 영역(.rp-month) 삭제. 대신 주황 큰 합계(.rp-total)와 그 아래 상세 금액에 **이번 주에 잡은 월간 보스 수익을 합산**하고, 상세 아래에 '월간 보스 결정석 N개 (금액 메소 포함)' 줄(.rp-mline, 0개면 줄 없음).
- 규칙: `weekMonthly(a)` — `c.monthly[slot]` 은 월간 보스를 **클리어한 주 key**(S.period.week)이므로, 그 값이 현재 `S.period.week` 일 때만 합산. 목요일 주간 리셋으로 주 key 가 바뀌면 자동 제외(월간 데이터는 월 리셋까지 남아 있어도 이번 주 수익엔 안 더함). 예전 데이터처럼 값이 주 key 가 아니면 제외.
- **표시 전용**: `allRevenue()`·`weekSummary()`(주간 history 저장)·`monthSummary()`·메소왕/수익 분석 집계는 그대로 → 월간 수익은 여전히 월간 기록 쪽에만 저장, 이중 계산 없음. 패널의 캐릭터별 줄(금액·바)은 기존대로 주간 보스만(합계와 캐릭터별 합이 월간분만큼 다를 수 있음 — 필요하면 다음에 캐릭터별에도 반영).
- 캐릭터 정보 카드의 '이번 달 월간 보스' 통계(monthMeso)는 그대로.
- **b58-추가 (6-b)** 
  - 주별 누적 결정석 메소 라인 차트(`cumLineChart(rows,T)`): `monthlyByWeek(T)` 가 월간 기록(`monthSummary` perChar 의 `bosses/bvals/mweeks`)에서 월간 보스 수익을 **잡은 주**(`mweeks[i]` = `c.monthly[slot]` 주 key)의 수익에 더함. `monthSummary` 가 이제 `mweeks` 를 저장. mweeks 가 없거나(b58 이전 월간 기록) 그 주가 목록에 없으면 같은 달(YYYY-MM)로 시작하는 마지막 주로 **근사**. 이번 달 진행 중 기록은 라이브 값 사용. 메소왕·history·`totalData` 합계는 그대로(차트 표시만 월간 포함, 누적 끝값 = 총 수익과 같아짐).
  - 툴팁: 모든 그래프 점/칸은 `data-tip`(기존 `#mbtTip` 공용 툴팁)로 표시 — 라인 차트 `.lpt`(주 전체 폭 투명 칸 + `data-tipanchor` 점 위에 말풍선), 빠뜨린 보스메소 차트 `.mpt`. 툴팁 스타일: 둥근 모서리 12px·부드러운 그림자·작은 꼬리(`--ax` 로 대상 위치, 아래에 뜨면 `.below`), 화면 밖으로 안 나가게 보정. 새 차트를 만들 땐 `<title>` 대신 `data-tip`(첫 줄 = 굵은 제목)을 쓸 것. (`weekChart()` 는 쓰이지 않음.)
  - test_tracker43 에 차트(지난 주/이번 주 월간 포함)·툴팁 검사 추가.
- 테스트: 신규 test_tracker43(전/같은 주/지난 주, 이중 계산 없음), test_tracker28 의 '(따로 합산)' 검사를 '삭제됨'으로 수정.

## 2026-10-11 b59 (이번 주 수익 패널 월간 보스 표시 다듬기)
(같은 방식: src 수정→build→테스트→main push, gh 로그인 필요. HANDOFF 기록은 항상.)
- '월간 보스 결정석 N개' 줄에서 금액 괄호 제거(개수만).
- 캐릭터별 줄(`revPanel`, `pWeekMonthly(p)`): 그 캐릭터의 월간 보스를 **이번 주(c.monthly[slot] === S.period.week)** 에 클리어했을 때만 월간 보스 메소를 캐릭터 금액·막대에 추가하고 '· 월간 ✓' 표시. 지난 주 이전에 돌린 월간 보스는 ✓·금액·합계 모두 제외(목요일 주 변경 후 자동으로 사라짐). 합계(`weekMonthly`)와 같은 기준이라 캐릭터별 합 = 큰 합계. 표시 전용 — `allRevenue/weekSummary/monthSummary` 는 그대로(이중 계산 없음).
- 캐릭터 정보 카드의 '이번 달 월간 보스' 통계는 그대로.
- 테스트: test_tracker43 에 위 3가지(금액 괄호 없음, 이번 주 캐릭터 금액+✓, 지난 주 ✓ 없음·금액 제외) 추가.

## 2026-10-11 b60 (결정석 분석 / 득템 분석 탭 분리 외)
(같은 방식. 요청 8-A~H 전부 기록. 실행파일 작업은 취소됨 — 사이트만.)
- A. `meso()` 가 항상 ' 메소' 단위를 붙임(0 → '0 메소'). 차트 작은 라벨은 `.replace(/ .*/,'')` 로 숫자만 사용. 메소 금액이 나오는 앱 전체(가격 카드·수익 패널·표·툴팁·요약 등)에 자동 적용 — 가격 카드는 줄이 길어져 `fitPriceCard()` 가 글자를 줄임.
- B. 홍옥 반지 상자(r_red)도 `RING_OFF` → 회색 비활성 칩(드롭 표 맨 끝, 클릭 불가), 못 가진 아이템 목록에서도 제외.
- C. 캐릭터 정보 '이번 주 주간 보스 수익' (이 캐릭터 문구 삭제) = 주간 + 이번 주(`c.monthly[slot]===S.period.week`)에 잡은 월간(검마) 결정석 수익(`pWeekMonthly`), 별도 문구 없음.
- D. 월간 보스 클리어 날짜: `c.mdate[slot]='YYYY-MM-DD'`(KST, `kstDay()`) — 체크 토글·API 자동 체크 시 저장(이미 있으면 유지), 해제하면 삭제, 월 초기화 때 비움, `normChar` 기본값 {}, `monthSummary` perChar 에 `mdates` 저장. 캐릭터 정보 '이번 달 월간 보스 (10/8)' 로 표시, 기존(날짜 없는) 기록은 날짜 표시 안 함(근사 안 함). 캐릭터 객체의 일반 필드라 드라이브/서버 3-way 병합(gdMerge)은 characters[id] 안에서 그대로 병합.
- E. 탭 이름 '수익 분석' → '결정석 분석'(탭 id 는 호환 위해 `total` 그대로). 새 탭 '득템 분석'(id `loot`, `renderLoot`) 을 바로 옆에 추가(TABS·render 매핑·탭 복원 포함).
- F. 결정석 분석 맨 위 카드: 제목 '누적 수입', 칸 3개만 — 총 수익 / '주보 누적 메소량'(아이콘 = 결정석 보스왕 1위 보스, 동적) / '검마 누적 메소량'. '획득 아이템 누적' 칸 삭제. '주별 누적 결정석 메소' 제목 옆 부가 글씨 삭제. '보스왕' → '결정석 보스왕'.
- G. 결정석 분석에 남은 것: 누적 수입, 주별 누적 차트, 메소왕, 결정석 보스왕, '지금까지 빠뜨린 보스메소는?'(missHtml), 전체 주 목록. (`kingHtml(T,'meso'|'loot')` 로 메소왕/득템왕 분리.)
- H. 득템 분석 탭(`renderLoot`): 맨 위 '누적 득템'(창세의 뱃지 아이콘) 3칸 — ① 총 득템(개수만, 아이콘 = 에픽빔왕 1위 아이템 동적, '녹옥, 홍옥 반지 상자 제외') ② 반상 누적(N회, 아이콘 = 가장 많이 얻은 반지 상자, '리4컨4 타율 N% · 녹옥, 홍옥 반지 상자 제외'; 타율 = (리4+컨4 실제) ÷ (기댓값 합) ×100, 기댓값은 제외 상자 빼고 `ring4()` 기준) ③ 누적 블빵 승리 횟수(N회만). 그 아래는 옮겨온 카드들 모양 그대로: 득템왕, 에픽빔왕+상자깡, 내가 가지지 못한 아이템, 블빵 승률·이긴/진 아이템, 보스 별 누적 획득 아이템, 시드링 획득 타율(`ringCardHtml`), 총 아이템 획득량. **일단 여기까지 — 새 기능 추가 금지.**
- 해석: '총 득템'은 블빵패배(잃은 것)는 제외, '총 수입' 제목은 실제 제목인 '총 수익'(h2) 을 '누적 수입'으로 바꿈, '누적 수익 테이블 3개'는 stat 3칸, 기존 '획득 아이템 누적' 칸만 삭제(아래 설명 문구는 유지).
- 테스트: 탭이 나뉘어 total 탭 기대 일부를 loot 탭으로 수정, test_tracker44(득템 분석 신규) 추가.

## 2026-10-10 배치 (b28)
- 취소/저장 비교: `pendSig()` (파티 숫자화·빈 드롭 제거) — 원인: 저장 데이터에 `party` 키가 없거나 문자열 '1' → 1→2→1 후 `party:1`이 새로 생겨 서명 불일치. `normChar`가 이제 party 를 항상 숫자로.
- `DROPS_OFF`: 보스 장신구(파풀라투스 마크 제외)·여명 세트 = 표 끝 회색 칩(.drop.off, 클릭 불가).
- API/API 자동 표시, 보스 행 클리어 체크 아이콘 삭제. '월간 보스 (따로 합산)' 두 줄.
- 추가 모달: 키 가림/등록 N명/캐릭터 목록 버튼/계정 캐릭터 N명 줄/메이플 계정N 표시 삭제, '✔ 등록 완료', 행 클릭 = 그 계정 목록, '캐릭터 추가' 버튼은 월드 선택 옆.
- 탭: '캐릭터 별 기록' 삭제, '총 수익' → '수익 분석'. 캐릭터별 누적 본캐 초상 = 왼쪽 목록과 같은 `avatar()`. '에픽빔 본 횟수' (x숫자 오로라 그라데이션).
- 칠흑 상자: `openChaos()` 모달(7종) → `dropOut[key]=['cb:<item>']` (반지 결과와 같은 자리), 기록은 `[상자 아이콘] - 이름`.
- 획득 축하: 모든 드롭 획득 시 `celebrate(null,item)` + `iconBurst(src)` (아이콘 42개 CSS transform, 2.1초 후 제거, reduced-motion 이면 생략). 반지=결과 아이콘, 칠흑=고른 장신구.
- 썬데이: `sunLabel()` — 게시일(`sunday.date`) < 이번 주 월요일 00:00 KST 이면 '저번 주 혜택' (1분마다 재확인).

- **b45 (2026-10-10)**: '최고 전투력' 패널·Worker /api/cp·클라이언트 호출 삭제(D1 cp 테이블은 미사용으로 남김), 정보 패널 3칸 균등. 캐릭터 목록의 주황 ★본캐 뱃지 제거(닉네임 전체 표시). 오른쪽 열 340px(≤1500: 310, ≤1360: 290 + 작은 글씨), main max-width 1640 가운데 정렬. 결정석 가격 줄이 안 들어가면 `fitPriceCard()`가 글자를 줄임(자르지 않음). test_tracker34 가 1920/1600/1280 검사.

- **b46 (2026-10-10)**: (1) 아이템 항목(.dl/.loot/.ro/.cbx/.drop)은 white-space:nowrap 한 덩어리 — 안 들어가면 첫 아이콘부터 다음 줄. (2) 오른쪽 열 400px(≤1700: 360, ≤1500: 330, ≤1360: 300), main 1760 가운데. `fitPriceCard()` 는 14px 에서 시작해 안 들어가면 0.5px씩 줄임(최소 9px), 창 크기 바뀌면 다시. (3) 수익 분석 '지금까지 빠뜨린 보스메소는? (주간/월간 Ver)': `S.missW`/`S.missM` (기간당 1개, 3-way 병합 키 week/month). 주간/월간 초기화 때 `resetCore` 가 초기화 직전 상태로 `remainingWeekly` (상위 12·스케줄러·파티 분배 / 월간 보스) 못 잡은 것을 기록. 몇 주 안 열었으면 `missBackfill` 이 S.history(캐릭터별 클리어 보스)로 지난 주를 채움(approx:true, 지금 보스 설정·가격 기준 근사). 기록이 없는 주(안 열고 클리어도 없던 주)는 알 수 없어 건너뜀. 월간은 백필 불가(월간 기록에 못 잡은 캐릭터가 없음). 서버 모드면 기록 추가 후 svSaveNow. (4) 일퀘 현황 탭·코드·dqicons.json·build_dqicons.py·test_tracker33 삭제 (S.dq 는 불러올 때 지움, 스케줄러 보스 가져오기·길드 지하수로는 그대로). test_tracker35. 참고: test_tracker8 은 이 변경 전부터 스우 r_red 칩 대기에서 실패(드롭 표 정리 이후).

- **b48 (2026-10-10) 예비 API 키**: 계정(본계정·부계정)마다 예비 키 1개 (`a.bk`, 이름 `a.bkLabel`, '+추가' 모달 계정 줄 아래). 등록 시 기본 키와 예비 키의 /character/list account_id 집합이 같아야 함(아니면 빨간 메시지). `nx()` 가 기본 키 429/OPENAPI00007(또는 quota/한도 메시지)면 같은 요청을 예비 키로 다시 보내고, `mapleBossTracker.bkDay` 에 그 계정을 오늘(KST)로 표시 → 그날은 예비 키만. 서버 금고: `/api/subkeys` 가 `mainBk`·`subs[].bk` 를 같은 계정인지 확인(backup_mismatch 400) 후 AES-GCM 금고에 함께 저장, 대표 키 로그인 때 `mainBk`·`subKeys[].bk` 로 돌려줌. 남은 호출: `mapleBossTracker.callCount` = {day, c:{키해시:호출수}, x:{키해시:한도 도달}} — 이 브라우저에서 보낸 호출만 셈(추정, 1,000/일). 키 값은 저장·로그 안 함(해시만). test_tracker36, test_server.

- **b51**: 축하 이모지는 Twemoji PNG(CC-BY 4.0, itemicons.json emo_*) 이미지 — 글자 이모지는 그라데이션 background-clip:text 때문에 투명했고 PC방 윈도우엔 컬러 이모지 글꼴이 없을 수 있음. 그라데이션은 .cg-t 글자에만. 반지 상자 꽝은 2인 이상이어도 블빵 창 없이 1인처럼 기록 (dmode 'n' → 기록 키에 인원 안 붙임, 라벨 없음).
- **b50**: 블빵 창 = 큰 아이템 아이콘 + 이름만 (반지 상자·칠흑은 고른 결과/장신구, askBbang 의 disp). 칠흑 항목(.dl.cbl)도 inline-flex nowrap 한 덩어리, 이번 주 수익 항목은 가로로 흐르다 안 들어가면 항목째 다음 줄.
- **b49 (2026-10-11) 블빵**: 파티 2인 이상 보스에서 아이템 획득 시 `askBbang()` 3지선다(블빵승리 / 블빵패배 / 분배 / 취소). 반지 상자·칠흑은 결과/장신구 고른 뒤. 선택은 `c.dmode`/`c.mdmode` {'보스|아이템':'w'|'l'|'s'} (대기 중 변경 → 취소/저장, 리셋 때 지움). 기록 키: 'boss|item#2w' / '#2l' (분배·예전 기록은 '#2'). 표시: '(n인 블빵승리)' 하늘색 .ptx-w, '(n인 블빵패배)' 회색 .ptx-l. 결정석 수익은 항상 1/n (선택과 무관). 수익 분석 집계: 승리/패배는 '@w'/'@l' 로 따로 칩, 패배한 반지 상자의 결과는 내 시드링 집계·기댓값에서 제외. 블링크 아이콘 = maplestory.io KMS 389 skill 400001007 (itemicons.json 'blink'). 생명 반지 상자 꽝 = '셋 다 못 먹었어요'. 축하 메시지에 무작위 이모지(😚😙😊😘🥳). test_tracker37.

- **b52 (2026-10-11) 수익 분석**: '캐릭터별 누적…' → '메소왕'(누적 합계 순, 1~3위 초상화+금/은/동 빛, 1위 왕관 2개, 10위씩 페이지 `rankPage`), '득템왕'(죽음의 맹세 아이콘, `lootOf()` — 반지 상자는 결과로, 블빵패배·꽝 제외, 블빵승리·분배·1인 포함). '시드링 획득 타율'(대박 확률 줄 삭제)은 총 아이템 획득량 바로 위. 에픽빔 아래 '블빵 승률'(인원별 N승 M패, `bbangStats`) · '블빵 이겨서 얻은 아이템들' · '블빵 져서 잃은 아이템들'. 빠뜨린 보스메소 '!' 는 배경 없는 굵은 노랑(주간)/빨강(월간). test_tracker38.

## 1. 개요
- 목적: 메이플스토리(KMS) 본캐·부캐의 **주간/월간 보스 클리어 체크 → 강렬한 힘의 결정 판매 수익 계산**, 보스 드롭(반지 상자 등) 획득 **개수** 기록, 주간·누적 기록.
- 라이브 주소: **https://bossmaple.pages.dev/** (현재 홈페이지 주소; 2026-10-11 사용자 정정). 예전 주소 https://ggoolzip-wq.github.io/ (GitHub Pages, `main` 브랜치 루트)도 병기. 예전 주소 `https://ggoolzip-wq.github.io/maple-boss-tracker/` 는 새 주소로 리디렉트(저장소 `ggoolzip-wq/maple-boss-tracker`의 index.html).
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
.github/workflows/update-prices.yml   매일 10:00 UTC(19:00 KST) 가격 갱신 + workflow_dispatch (b65)
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
- `.github/workflows/update-prices.yml`: **매일 10:00 UTC(19:00 KST)** + 수동 실행(b65). `scripts/update_prices.py`가 https://maplestory.nexon.com/News/Update 목록을 최신순으로 훑어 '강렬한 힘의 결정' 가격표가 있는 공지를 찾아 `prices.json`(rows: boss/old/new/effective, source url/title/date, checkedAt, fetchedAt) 갱신. **확인 성공 때마다 `checkedAt`(마지막 확인)=오늘(KST)로 갱신·커밋**(가격이 같아도 — 카드가 신선해 보이도록). 가격 rows 가 바뀔 때만 `changedAt` 갱신.
- **피드 경로 유지(b39)**: `update_feed.py` 가 테섭/패치 새 글을 보면 가격 확인·`checkedAt` 갱신(또는 upcoming/본섭 적용). 매일 19:00 스케줄과 병행 — 피드 워크플로는 건드리지 않음.
- 사이트는 로드 시 `./prices.json?d=날짜`를 받아 보스·난이도 이름 매칭 후 적용. 적용일(effective)이 미래면 그날까지 대기. 실패 시 캐시/내장 가격(2026-09-17 공지) 사용. 카드 문구: `(가격 변동일 …, 마지막 확인 YYYY-MM-DD)` ← `checkedAt`.
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
- 사용자 분리·입장 화면 (2026-10-10 04:1x KST): **(b67: 초대 비밀번호·입장 화면 폐지 — 지금은 캐릭터 추가 창에서 본계정 키만)** 원인 = 로그아웃해도 이 PC 데이터가 남고, 새 사용자 첫 로그인 때 "서버 비어 있음 → 이 PC 데이터 올림" 규칙으로 남의 데이터가 올라감. 수정: svUser(이 기기의 마지막 서버 사용자) 기록, 다른 사용자로 로그인하면 이 PC 데이터를 비우고 서버 데이터만 사용, 로그아웃 시 비움, 이 기기 첫 로그인 + 이 PC 데이터 있음 → "이 PC 데이터를 이 계정으로 올릴까요?" 확인. 서버 모드 입장 화면(#svGate): 빈 화면 → 초대 비밀번호 → 대표 키(+API 키 받는 법) → 로그인 성공 후 사이트, 세션 있으면 바로 사이트. test_tracker25.py.
- Cloudflare Pages (2026-10-10 04:4x KST): https://bossmaple.pages.dev — 이 주소에서는 서버 동기화가 기본(SYNC_HOSTS, 입장 화면 바로), github.io 는 구글 드라이브 그대로. 배포 = tools/pages_dist.sh → _site → `wrangler pages deploy _site --project-name bossmaple --branch main`. 자동 배포: .github/workflows/deploy-pages.yml (push + 피드/가격/썬데이 워크플로 완료 후) — 저장소 secret CLOUDFLARE_API_TOKEN·CLOUDFLARE_ACCOUNT_ID 필요(없으면 건너뜀). Worker CORS = github.io + bossmaple.pages.dev.
- 2026-10-10 05:xx KST 대규모 변경: 보스 목록 [취소]/[저장](대기 중 변경은 스냅샷과 비교, 저장 전엔 수익·저장소 미반영, 서버 모드 수동 저장의 유일한 경로) · 자동 저장/로그아웃 경고/beforeunload 없음 · 드롭은 보스·아이템당 기간 1회(예전 2+ → 1로 이전) · 드롭 표에서 보스 장신구(파풀 마크 제외)·여명 세트 제외 · 탭: 보스 현황/캐릭터 별 기록(2026-10-08부터 누적, ★득템)/총 수익(시드링 획득·물욕 누적 획득, 아이콘), 주간 기록 탭 삭제(S.history 는 유지) · 개수 표기 xN · 예상 수익 = 남은 주간(12칸 중) + 미처치 월간 · 일퀘 제목 아이콘, 길드 본캐 행은 지하 수로만 · +추가 모달: 스케줄러 자동추가 옵션·이름으로 직접 추가 삭제 · 보스·난이도는 스케줄러로만. 테스트: test_tracker26·27, test_tracker11 은 다중 개수 전제라 run_all 에서 뺌.
- **친구 초대 전용 (2026-10-10)**: **(b67: 초대 비밀번호·입장 화면 폐지 — 지금은 캐릭터 추가 창에서 본계정 키만)** 기기마다 한 번 초대 비밀번호(POST /api/invite → 기기 표 `mapleBossTracker.svDevice`, 로그아웃해도 유지) → 넥슨 키 로그인. Worker secret `SITE_PASS_HASH` = sha256('ggoolzip-invite:'+비밀번호, 앞뒤 공백만 제거·대소문자 구분), 없으면 로그인 거부. 비밀번호 사본: 박스 /home/box/.config/ggoolzip/SITE_PASS (600, 사용자가 정한 값). 바꾸기: `cd server && bash set-site-pass.sh` (README). 사용량 제한: 세션별 읽기 90/분·저장 20/분, 사용자별 저장 40/분, 초대 시도 IP별 10/10분.
- 남은 일: 사용자 Cloudflare 가입 → `npx wrangler login --device`(또는 API 토큰) → d1 create · schema · ID_PEPPER · deploy → 미리 써 보기 → SYNC_API_URL 켜기. 나중 단계(미구현): 매일 18:00 KST cron 으로 maplescouter 헥사환산(캐릭터 1명으로 먼저 시험).

## 8. 사용자가 정한 동작·취향 (변경 시 사용자 확인 필요)
- **항상 다크 테마**(2026-10-12 b67 사용자 요청): 라이트 모드·테마 전환 버튼 없음. 새 UI 는 다크만 만들고 확인(라이트 색 추가 금지).
- **초대 비밀번호 없음**(b67): 누구나 bossmaple.pages.dev 에 들어와 '캐릭터 추가'에서 본계정 키로 가입 요청 → **관리자(사용자 본 데이터) 승인 후 사용**(b68).
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
- **update-prices.yml**: (b39) 주 1회 대비 → **(b65) 다시 매일 19:00 KST**. 본섭 직접 변경·피드 누락 보완 + 매일 `checkedAt` 갱신. 피드의 새 공지 촉발 경로는 그대로.
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

## 2026-10-10 b43 — 최고 전투력 (헥사 환산·hexa.json·set_hexa/check_hexa 삭제)
- 캐릭터 정보 칸: '최고 전투력' 값(억/만) + 작은 글씨 조합('장비 2 · 하이퍼 3 · 어빌 1 · 링크 1') + 'YYYY-MM-DD HH:MM 갱신'. 자료 없으면 '—'. 툴팁에 현재 프리셋 전투력(API).
- 계산: Worker server/cp.js (넥슨 Open API 만). 엔드포인트 POST /api/cp {ocid,name,key} → D1 `cp` 표(user_id, ocid PK), GET /api/cp. 키는 그 요청에만 쓰고 저장 안 함. 캐릭터당 KST 하루 1번(서버가 day 로 막음, 같은 날은 저장값 반환), 세션당 10분 60회 제한.
  - 호출 API(캐릭터당 7회): character/basic, stat, hyper-stat(프리셋 1~3), item-equipment(프리셋 1~3), ability(프리셋), link-skill(프리셋), set-effect.
  - 모델: (4×주+부)/100 × 공(마) × (1+(뎀+보공)/100) × (1.35+크뎀/100). 보정 계수 k = API 전투력/모델(현재) → 현재 조합은 API 값과 정확히 같음. 프리셋 조합 81개(장비×하이퍼×어빌×링크)는 현재 대비 변화량만 반영하고 최대값.
  - 근사(정확한 교체가 어려운 부분): 스탯 %적용 기본값·스탯%·공% 는 알 수 있는 원천(장비·어빌·링크·세트·AP)으로 추정, 하이퍼 스탯 수치는 %미적용, 설명 안 되는 나머지는 고정 · 세트는 칠흑/에테르넬/마이스터만 이름으로 다시 셈(그 외 세트 개수 유지) · 조건부 효과(N초 동안·전투 돌입 시 등) 제외 · 최종뎀·방무·유니온(프리셋 없음)·심볼·펫·캐시는 프리셋 무관이라 고정.
  - 림강혼망(렌, 2026-10-10 실제 API 응답으로 로컬 계산): 현재(장비1·하이퍼1·어빌3·링크2) API 226,966,178 = 모델 재현(보정 k=0.7654) → 최고 433,060,423 (장비 2 · 하이퍼 3 · 어빌 1 · 링크 1). k 가 1과 23% 차이 = 공식에 안 들어간 직업/숨은 값 → 프리셋 간 비율은 맞지만 절대값은 추정.
  - 스케줄(cron)은 안 씀: 서버는 사용자 키를 저장하지 않으므로(대표 키 원본 저장 금지 원칙) 사용자 키로 서버 혼자 조회할 수 없음 → 사이트에서 캐릭터 동기화가 끝날 때(syncAll finally → cpRefresh) 오늘 아직 계산 안 한 캐릭터만 요청. 동기화 서버 로그인(bossmaple / ?sync=test) 때만, github.io(드라이브 모드)는 '—'.
  - 테스트: tests/test_cp.mjs (node), test_tracker34. D1 표는 원격에 CREATE TABLE IF NOT EXISTS 로 추가함.
- b43: 캐릭터 목록 줄의 ⠿ 손잡이를 왼쪽 여백 안 absolute(폭 10px)로 → 초상화~✎ 묶음 좌우 여백 11px/11px (전에는 손잡이+간격 때문에 왼쪽 34px). test_tracker34 에서 측정.

---

# 메이플 봇2 인계 (2026-10-09 ~ 10-11, 시간순 전체 기록)

> 이 섹션만 읽어도 이어서 작업할 수 있게 썼습니다. 위쪽 섹션은 이전 봇 기록(그대로 둠). 커밋은 `git log --since=2026-10-09`.

## 0. 기본 정보
- 저장소: `ggoolzip-wq/ggoolzip-wq.github.io` (main). 소스 `src/` (app.js · extra.css · body.html · itemicons.json) → `python3 tools/build.py` 가 **index.html 한 파일**로 합침. index.html 은 커밋해야 함(빌드 결과도 커밋).
- 배포: GitHub Pages(`https://ggoolzip-wq.github.io/`) + Cloudflare Pages `https://bossmaple.pages.dev/` (push 시 워크플로 자동 배포, `tools/pages_dist.sh`). 확인: `gh run list -L 2`, `curl` 로 새 코드 문자열 grep.
- 테스트: `tests/test_tracker*.py` (Playwright, `CHROME=/usr/bin/google-chrome python3 tests/test_trackerNN.py`), 전체 `tests/run_all.sh`. 스크린샷은 `/workspace/shots/` (저장소에 커밋하지 않음 — 테스트가 저장소 안 PNG를 바꾸면 `git checkout -- '*.png'`).
- 상태: `localStorage['mapleBossTracker.v1']` = `S` (characters, history, monthHistory, missW, missM, settings…). 탭은 `mapleBossTracker.tab`.

## 1. 시간순 작업
**10-09**
- 루트 주소로 이전, UI 개편(설정 탭 제거, + 추가 통합 모달, 헤더 동기화 메뉴), 12/12 완료 덮개(★ 이번 주 보스 완료 / ! 검마 격파 필요).
- 일퀘 현황·길드 현황 탭 추가(나중에 일퀘는 삭제 — 아래 6).
- **소식 피드 카드** (`scripts/update_feed.py`, 5분 Action → `feed.json`): 사료감지·패치내역·테섭·마빡도로시, 마이너 패치 누적(최대 5쪽 탐색).
- **썬데이 메이플 카드**: `scripts/sunday_watch.py`(매일 10:00~10:20 KST 5초 간격, Open API 우선·홈페이지 대체), `sunday_ocr.py`(혜택 OCR, 자동 자르기 sunday.png), 라이트박스. 예비 키 `NEXON_API_KEY2` 를 워크플로에 전달.
**10-10 새벽**
- 드라이브 동기화 반복 질문 수정 → 구글 로그인 창 자동으로 안 띄움. 이후 **구글 드라이브 동기화는 Cloudflare 로 교체**.
- 드롭 표: 연마석·소울 에테르 각각 칩, 에르다/에테르넬 정보 칩(개수 배지, 클릭 안 됨). 툴팁은 반지 상자(녹옥 제외: 이름 + 리4/컨4 확률)·칠흑 상자·에테르넬만.
- 🔄 동기화 버튼 → 캐릭터 카드 머리글 아이콘. 페이지 로드 시 자동 동기화(3초 규칙), 주기 자동 동기화 삭제.
- **Cloudflare Worker + D1** (`server/worker.js`, `schema.sql`, `wrangler.toml`; Worker `ggoolzip-sync.bossmaple.workers.dev`):
  - 로그인 = 넥슨 Open API 키 → Worker 가 검증하고 계정 id 해시로 사용자 식별. **원본 키는 서버에 평문 저장 안 함**. 세션 토큰은 localStorage, 서버엔 해시.
  - 친구 초대 비밀번호 **(b67: 초대 비밀번호·입장 화면 폐지 — 지금은 캐릭터 추가 창에서 본계정 키만)** `SITE_PASS_HASH`(secret, 기기당 1번, 시도 제한, fail closed). 변경: `wrangler secret put SITE_PASS_HASH`. 원문은 `/home/box/.config/ggoolzip/SITE_PASS`(600).
  - 대표 키/부계정 키: 부계정 키는 대표 키(HKDF→AES-GCM)로 암호화해 서버 금고에. 세션·사용자별 요청 제한.
  - bossmaple.pages.dev 에서는 서버 모드 기본(입장 화면). 다른 사용자로 로그인하면 이 PC 데이터를 올리지 않음, 로그아웃 시 비움.
  - **서버 모드는 자동 저장 없음** — 헤더 [저장]/[취소] (스냅샷 비교), 탭 이동 시 저장 여부 물음.
- b28~b40: 취소/저장, 칠흑 상자 장신구 고르기 창, 아이콘 터짐 효과, 수익 분석 탭, 에픽빔 합계 반짝 효과, 캐릭터 목록 페이지(8개, 고정 높이), 생명의 연마석 결과, 녹색 선택 칩.
- **결정석 가격 자동화** (`scripts/update_prices.py`, `nexon_prices.py`, `upcoming.py`): 공식 패치 노트에서 가격 → `prices.json`. 테섭 공지에서 '테섭 예정' 가격 감지(`upcoming`), 본섭 패치 때 맞으면 지움(reconcile). feed 잡이 같이 돌림, 주 1회 대체 실행. 같아도 `checkedAt` 갱신. 데모 예정 가격 제거 스크립트 `scripts/remove_demo_upcoming.py`(라이브 데모는 삭제 완료).
- 헥사 환산(hexa.json) → 최고 전투력(Worker /api/cp) → **둘 다 삭제** (6 참고).
- b45~b46: 오른쪽 열 넓힘·가운데 정렬, 결정석 가격 글자 자동 맞춤(`fitPriceCard`), 아이템 항목 줄바꿈 단위, 빠뜨린 보스메소 주간/월간 그래프(`S.missW`/`S.missM`, 주간은 history 백필, 월간은 백필 없음), 일퀘 탭 삭제.
**10-10 밤 ~ 10-11**
- b48 **예비 API 키**: 추가 모달에서 계정별 예비 키(이름 예: '본계정 예비'), 같은 넥슨 계정인지 확인(캐릭터 목록/ouid), 429·`OPENAPI00007` 시 예비 키로 자동 전환해 KST 다음 날까지 사용. 서버 금고에 암호화 저장, 로그에 키 없음. '남은 호출 약 742/1000'(클라이언트 추정), 한도/전환 시 빨간 표시.
- b49~b51 **블빵**: 파티(2인 이상) 드롭 시 블빵승리/블빵패배/분배 3지선다 창(큰 아이템 아이콘 + 이름). 생명 반지 '셋 다 못 먹었어요', 반지 꽝은 라벨 없는 꽝, 축하 이모지는 Twemoji 이미지(그라데이션 clip 밖).
- b52~b53 **수익 분석 표** (아래 3).

## 2. 블빵 로직 (중요)
- 기록 키 `보스|아이템` → `c.drops`/`c.mdrops`, 결과 `c.dropOut`(반지 r4/c4/gl/x, 칠흑 `cb:<장신구>`), 모드 `c.dmode`/`c.mdmode` = `w`(블빵승리)/`l`(블빵패배)/`s`(분배)/`n`(꽝, 라벨 없음). history 에는 `아이템#인원모드` (예 `g_faith#2w`), `parseIK()` 로 분해.
- **결정석 수익은 블빵과 무관하게 항상 1/n.** 블빵패배: 수익 0 추가 없음, 축하 없음, 드롭/에픽빔 집계엔 포함.
- 1인: 창 없음. 칠흑: 장신구 고르고 → 3지선다. **반지 상자는 b53부터 블빵 창 없이 항상 분배(`s`)**, 꽝은 `n`.
- 예전 기록(모드 없음)은 예전처럼 표시.

## 3. 수익 분석 탭 (위→아래)
총 수익 → 주별 누적 → **메소왕**(누적 합계 순, 1위 왕관×2+금, 2위 은, 3위 동, 1~3위 초상화) → **득템왕 (아이템 1개 당 1점)**(블빵승리·분배·1인 포함, 블빵패배·꽝 제외; 반지는 결과로, 칠흑은 `[상자]-[장신구]`; 닉네임 뒤 선홍색 '(N점)') → **에픽빔 본 횟수**(수식어 없이 같은 아이템 합침, 칠흑은 상자 개수, 합계 숫자만) → **혼돈의 칠흑 장신구 상자깡**(장신구 7종, 0 포함, `CHAOS_PICK` 순서) → **블빵 카드 하나**(물욕 블빵 승률: 인원별 % · N승 M패, 기록 없는 인원 숨김 / 이겨서 얻은 / 져서 잃은, 구분선) → 보스 별 누적 획득 아이템(자쿰 아이콘) → 시드링 획득 타율 → 총 아이템 획득량 → 빠뜨린 보스메소(주간 노란 '!', 월간 빨간 '!') → 전체 주 목록.
- 순위 동점은 왼쪽 캐릭터 목록 기본순(`orderedChars()`).

## 4. 기타 b53
- 선택된 드롭 칩: 초록 + 가운데 SVG 체크(`.drop.got::after`, 크기 안 바뀜).
- 이번 주 수익 주황 합계만 억 단위 소수 1자리('271.3억 메소').
- 결정석 가격: 월간 보스 📅, '(가격 변동일 YYYY-MM-DD, 마지막 확인 YYYY-MM-DD)'. `prices.json.changedAt` = 현재 가격을 정한 패치 노트 날짜(지금 2026-09-17, 공지 813). `update_prices.py` 가 rows 가 실제로 바뀔 때만 changedAt 을 그 공지 날짜로 갱신.

## 5. 일반 규칙 (사용자 고정 선호 — 반드시 지킬 것)
- **다크 전용**(b67): 테마 전환 버튼 없음, 라이트 모드 없음.
- **공용 PC 기준**(b69): 서버 모드에서 로그아웃·세션 없음 = 이 PC 의 앱 데이터 전부 삭제(처음 온 사람 상태). 로그아웃 전에 남은 변경은 서버에 저장.
- 답변·UI 문구는 **한국어**. 개수 표기는 **xN** (예 x3).
- **자동 저장 없음**: 서버 모드는 수동 [저장]/[취소]. 드롭 선택 시 토스트 없음.
- **페이지 나누기는 모두 고정 크기**: 마지막 쪽도 빈 행으로 채워 표 높이가 같고, 페이지 버튼 위치가 절대 안 움직임 (캐릭터 목록 8개, 메소왕/득템왕 10개 `rankPad`). 앞으로 만드는 모든 페이지 UI 에 적용.
- **항목은 중간에서 줄바꿈 금지**: 아이콘+이름+개수+결과(+라벨)가 한 덩어리, 안 들어가면 통째로 다음 줄.
- 글자 잘림 금지(필요하면 글자 줄이기), 1920×1080·1280×800 확인.
- 라이브 사이트에서 임의 테스트(가짜 기록 저장 등) 전엔 **먼저 물어볼 것**. 데모는 로컬에서.
- 작업 끝: push → 배포 확인 → HANDOFF 갱신 → 짧게 보고 + 스크린샷.

## 6. 삭제한 기능과 이유
- **일퀘 현황 탭**: 스케줄러 일퀘 데이터가 늦고(특히 익몬) 부정확, 사용자 요청으로 삭제(스케줄러 보스 가져오기는 유지).
- **헥사 환산 / 최고 전투력**: 넥슨 API 값이 스냅샷이라 실시간이 아니고 프리셋 계산이 불확실 → 사용자 요청으로 패널·hexa.json·스크립트·Worker /api/cp 사용 중단.
- 구글 드라이브 동기화: Cloudflare 서버 동기화로 대체. 주기 자동 동기화·본캐 뱃지 삭제.

## 7. 남은 문제
- `tests/test_tracker8.py` 가 시작부터 오류(b52 이전부터, 드롭 표 오래된 선택자) — 고치거나 새 테스트로 대체 필요.
- 넥슨 스케줄러의 익몬(익스트림 몬스터파크) 퀘스트 반영이 늦음(API 쪽 지연) — 일퀘 탭을 다시 만들 일 있으면 주의.
- 득템왕 행은 칩이 많으면 48px 보다 길어질 수 있음(그때 고정 높이 규칙이 깨짐 — 칩 줄수 제한이 필요하면 추가).

## 2026-10-11 b54
- 축하 문구: 랜덤 이모지·🎉 삭제 → '축하드립니다!' 앞에 드롭한 보스 아이콘(`celebrate(o,item,boss)`; 일반 드롭·반지 상자·칠흑 모두 boss 전달).
- 결정석 가격 오른쪽 위 '[ ] 내가 잡는 보스만 보기' (`pcMine`, localStorage `mapleBossTracker.pcMine`). 켜면 등록된 캐릭터 중 하나라도 켜 둔(스케줄러로 가져온) 보스+난이도만 한 번씩, 난이도는 따로(하드/익스트림 스우 별도). 테섭 예정 표시와 같이 동작, 패치 후 탭에서도 토글 유지(그 탭은 캐릭터별이라 필터 영향 없음). 글자 맞춤 규칙 그대로. test_tracker40 (테섭 예정은 테스트에서만 모의).
- 참고: 스케줄러 가져오기(`applyScheduler`)는 **일간/일일 보스를 일부러 건너뜀**(cycle daily skip) → 주간·월간 보스만 추적.

## 2026-10-11 b55 — 수익 분석 순위 표
- **모든 순위 표 공통** (`rankTable()` / 메소왕·득템왕은 `kingHtml`): 10개씩, 고정 크기(`rankPad`), 1쪽이면 페이지 버튼 없음. 1~3위 금/은/동 빛 + 같은 색 반짝임(`.spk` ✦ 두 개), 1~3위 앞에 초상화/보스 아이콘/아이템 아이콘.
- 정렬: 보스 동점은 결정석 비싼 쪽 먼저. 아이템 우선순위 `itemPri()`/`itemCmp()` (1 광휘 · 2 신념 연마석·칠흑(루컨마·커포 제외) · 3 생명 연마석·리4·컨4·생명 상자 · 4 소울 에테르 4→1·백옥 상자 · 5 흑옥 상자 · 6 나머지) — 동점, 아이템 칩 목록, 못 가진 아이템에 사용.
- 난이도 색: 이지 #4db8ff · 노말 #7ed957 · 하드 빨강 · 익스트림 진한 주황 · 카오스 연보라, 보스 이름 흰색, '보스 (난이도)' (`bossDiffHtml`).
- 에픽빔 집계: 반지 상자와 상자에서 나온 것(리4·컨4·상자 생명의 연마석)은 **이미 b53부터 제외**되어 있었음(결과는 outs 로만 저장). 보스가 직접 준 생명의 연마석은 셈.
- 요약 카드: 총 수익·주간·월간 큰 숫자 억 1자리, 주 평균·월 평균은 원 단위, 획득 아이템 'N종' 삭제.
- 득템왕: 제목 '득템왕', 닉네임 뒤 '(N회)' 를 닉네임과 같은 색·크기·기준선으로(`.rknm` baseline flex).
- 보스왕(득템왕 아래): 기록(주간·월간 history + 이번 주/달)의 보스 태그로 보스+난이도별 처치 횟수, 쌓아준 메소 = 실제 들어온 결정석(파티 나눔). b55부터 history perChar 에 `bvals`(보스별 실제 금액) 저장, 예전 기록은 현재 가격/파티로 추정.
- 에픽빔왕: 숫자 없는 제목 + '에픽빔 누적 횟수 N'(반짝이는 금색 `.epgold`), 순위 표. 상자깡도 순위 표(0 포함).
- 내가 가지지 못한 아이템 목록(상자깡 아래): 모든 보스 드롭 표의 누를 수 있는 아이템 중 못 얻은 것(블빵패배 제외). 칠흑 상자에서 고른 장신구 = 얻음. 반지 상자: 상자를 얻으면(결과 무관) 그 상자 얻음, 상자 결과 생명의 연마석 = 생명의 연마석 얻음, 리4·컨4는 드롭 칩이 아니라 목록에 없음. 아이템마다 1줄(결정석이 가장 싼 보스·난이도로 표시), 우선순위→가격 순. 제목 아이콘 = 첫 아이템 흑백. test_tracker41.

## b72 — 본계정 1번 줄 고정 · 부계정 이름 필수 · 키 없는 계정 캐릭터 숨김 (2026-10-12)
- **본계정 순서**: `svAfterLogin` — 로그인한 대표 키(금고 locked 아님)의 칸 = 항상 1번 줄 '본계정'. 찾는 순서 accId → 같은 키 → ah∈해시 → main 칸 → 키 없는 '본계정' → 새로 만듦(이름 '본계정', 맨 앞; 예전 `계정N` 생성 없앰). 같은 넥슨 계정의 새 키면 키를 바꿔 예전 키 버림. 같은 키·같은 ah·예전 main 칸이 따로 있으면 캐릭터 accId 를 본계정으로 옮기고 칸 삭제(중복 없음). 금고 부계정 중 ah∈해시(예전 본계정 키)는 복원 안 함 → 목록이 바뀌면 기존 `svSyncSubKeys` 로 서버 금고에서도 빠짐.
- `keyRelink`: 새로 넣은 키가 main 이면 키를 예전 칸으로 옮기지 않고, 같은 캐릭터가 붙은 키 없는 예전 칸을 본계정으로 합침 (예전엔 본계정 키가 '계정4' 같은 칸으로 옮겨가던 원인).
- **부계정 이름**: 이름 칸 placeholder 항상 '계정 이름', 자동 이름(부계정N) 없음. 이름 비운 채 **등록 버튼을 눌렀을 때만** 이름 칸 아래 빨간 '계정 이름을 입력해주세요'(`#newAccLblErr`, .lblerr) + 등록 안 함, 이름 입력하면 사라짐. 목록의 이름 칸을 비우면 예전 이름 유지(경고 없음).
- **키 없는 계정 캐릭터 숨김**: `charShown(c)`(accId 없음·계정 없음 → 보임, 아니면 key 있어야) / `vchars()`. 사이드바·보스 현황·분석 뷰·길드·이번 주 수익 패널·동기화 루프·activeChar(숨기면 첫 보이는 캐릭터)에서 사용. 데이터는 그대로 — 키 다시 등록하면(keyRelink) 다시 보임. **지난 기록(history·월 기록·누적 기록 charRecords)은 숨긴 캐릭터 것도 유지·합산** (`allRevenue(list)` — 인자 없으면 전체, 기록 저장용).
- '키 없음' 글자 전부 삭제: 키 없는 칸은 상태 비움, 이름 칸 값 비움 + placeholder '계정 이름'(빈 칸처럼), maskKey '' , 동기화 오류 문구 'API 키 미등록'. 등록 캐릭터 수에서 키 없는 계정 제외.
- 테스트: test_tracker55 (run_all 에 추가). 49/51/53/5 는 부계정 추가 때 이름을 채우도록 수정. 관련 23·24·29·46·48–54 통과, 28 은 예전부터 실패(제목 기대값).
- 스크린샷: /workspace/maple-boss-tracker/oct12j_b72_before_page.png, _before_modal.png, _after_page.png, _test_modal.png, _test_nameerr.png

## b73 — 직접 로그아웃 때 알림(토스트) 없음 (2026-10-12)
- `gdLogout`: 서버 모드 '로그아웃했습니다 — 이 PC의 데이터를…' 토스트, 드라이브 모드 '구글 드라이브에서 로그아웃했습니다' 토스트 삭제. 로그아웃 전 저장 중 뜬 '☁ 서버에 저장했습니다' 등도 `toastHide()` 로 바로 숨김. 새로고침 뒤 빈 화면에서도 알림 없음.
- 서버가 세션을 거부(401/403)할 때의 '다시 로그인' 안내는 그대로 (별도 경로, 변경 없음).
- 테스트: test_tracker53 에 로그아웃 직후·새로고침 후 토스트 없음 확인 추가. 52·53·55 통과.
- 스크린샷: /workspace/maple-boss-tracker/oct12k_b73_before_logout.png, oct12k_b73_after_logout.png, oct12k_b73_test_logout.png

## b74 — 캐릭터 추가 창: 예비 키 삭제 · '+ 계정 추가' · 키 발급 안내 삭제 (2026-10-12)
- **예비 API 키 기능 UI 전부 삭제** (bkRow 줄·이름·등록·삭제). 기존 데이터: `normState` 와 `svAfterLogin` 에서 a.bk/a.bkLabel 버림, 금고 복원 안 함. 금고에 예비 키가 있으면(`L.mainBk`/sub.bk) `svBkPurge` → 다음 `svSyncSubKeys` 가 예비 키 없이 다시 올려 서버 금고·등록부(keyreg)에서도 빠짐. 429 때 예비 키로 다시 보내는 코드는 bk 가 없으니 동작 안 함(코드는 남김).
- **부계정 추가 줄**: 미리 만들어진 빈 입력 줄 없음. 목록 = 본계정 + 키 등록된 부계정만 (키 없는 부계정 칸은 목록에 안 보임 — b72 빈 칸 표시를 대체. 데이터·캐릭터 연결은 유지, 같은 계정 키를 넣으면 keyRelink 로 그 칸에 다시 붙음). 아래 '+ 계정 추가' → `#accAddRow` 한 줄(이름 placeholder '계정 이름' + 'API키 입력' + 등록 + 취소). 등록 때 이름 비면 b72 빨간 경고. 취소·등록 완료·창 닫기 → 줄 지우고 숨김. 키가 하나도 없으면(구글 드라이브 모드) 줄을 바로 보여 줌. `accAddShow(on)`.
- '키 발급: openapi.nexon.com …' 안내 줄 삭제.
- 테스트: test_tracker55 에 b74 확인 추가. test36(예비 키 전용) 삭제·run_all 에서 뺌. 46·48·49 는 예비 키 기대값 제거, 4·5·13·23·49–55 는 '+ 계정 추가'로 줄 열고 입력. 통과: 4 5 23 24 29 46 48 49 50 51 52 53 54 55 (13 은 예전부터 :8787 문제).
- 스크린샷: /workspace/maple-boss-tracker/oct12l_b74_before_modal.png, oct12l_b74_after_modal.png, oct12l_b74_after_addrow.png, oct12l_b74_test_addrow.png


## b75 — 보스 목록 저장 문구 · 저장 안 한 변경 확인 · 수익 기록 창 · 빈 칸 빨간 테두리 (2026-10-12)
- 보스 목록 [저장]: 하단 알림('저장했습니다'·'☁ 서버에 저장했습니다') 없음 → [취소] 왼쪽에 초록 '저장이 완료되었습니다.'(`.pdone`, 3초 뒤 사라짐, `pendDoneAt`). `svSaveNow(quiet)`.
- 저장 안 한 변경(pend)이 있을 때 탭 이동·다른 캐릭터 선택 → `pendGuard(go)`: 가운데 창에 그 캐릭터 사진(avatar)+이름 위에 '지금까지의 변경사항을 저장하시겠습니까?' 예/아니오. 예=저장 후 이동, 아니오=버리고(알림 없이) 이동, 바깥 클릭=머무름. `svAsk(msg,btns,head)` 에 head 인자 추가. (따로 '닫는' 캐릭터 패널은 없어서 탭·캐릭터 선택에 적용)
- '수익을 기록할까요?' 창: 바깥(배경) 클릭 = 아무것도 안 함(창 유지). 빈 금액 기록하기 → '금액을 입력해주세요.' + 빨간 테두리.
- 빈 칸 빨간 테두리(규칙 8): 수익 금액, 부계정 이름·API 키(이름 비면 b72 빨간 글 + 테두리, 키 비면 테두리 + 알림), 본계정 키 칸(svMainKey), 캐릭터 이름(fName).
- 테스트: test_tracker56 (run_all 추가). 25·31·37·47·51·55 통과.
- 스크린샷: /workspace/maple-boss-tracker/oct12m_b75_before_save.png, _before_guard.png, _before_rev.png, oct12m_b75_after_save.png, _after_guard.png, _after_rev.png, oct12m_b75_test_rev.png

## b76 — 득템 분석 '아이템 판매 누적 수익' (2026-10-12)
- 제목 '아이템 판매 수익' → '아이템 판매 누적 수익'. 제목 아이콘 = 표에서 판매 건수가 가장 많은 아이템(분배 인원 합산, 같으면 itemCmp 순), 기록 없으면 메소 아이콘.
- 총 판매 수익(주황) '32.5억' → '32.5억 메소'. 줄 금액은 기존 meso() 그대로('…억 …만 메소').
- `totalData().sales` 키 = 아이템#인원 ({n,m,i,p}; r.p = 기록 때 나눈 인원). 같은 아이템도 1인/2인 분배/3인 분배… 따로 줄·따로 건수. 줄마다 '1인'·'N인 분배' 표시(.slp), 한 줄 고정(nowrap, 긴 이름은 말줄임), 가로 스크롤 없음(390px 확인).
- 테스트: test_tracker57 (run_all 추가), test47 제목 기대값 수정. 47·57 통과.
- 스크린샷: /workspace/maple-boss-tracker/oct12n_b76_before_sales.png, oct12n_b76_after_sales.png

## b77 — 관리자 버튼이 안 보이던 문제 (2026-10-12)
- 원인: b67 이후 서버 모드 로그인 상태의 헤더 버튼(#gBtn)은 바로 '로그아웃' 이라 ☁ 메뉴(gdMenu)를 열 길이 없음 → 메뉴 안의 '👑 관리자 — 가입 승인'(#svAdminBtn)에 갈 수 없었음. 로그인 경로·SV_ADMIN_KEY('1')·gdMeta.on·svAdminCheck 는 정상(라이브에서 실제 키로 확인).
- 수정: 헤더 오른쪽 위 [로그아웃] 바로 왼쪽에 '👑 관리자' 버튼(#svAdminHdr, 어두운 바탕 노란 글) — 관리자이고 로그인 중일 때만, 새로고침 뒤에도(svAdminCheck → gdRender). 누르면 가입 승인 창(openAdmin).
- 라이브 확인(실제 관리자 키, 화면·로그에 키 없음): 로그인 직후·새로고침 뒤 버튼 보임, 눌러서 관리자 창 열림, 확인 후 로그아웃. 'bot-check' 세션 1개 삭제(백업 /workspace/backup/b77_sessions_before_20261012_151011.json, 600). 사용자 'Windows' 세션 2개는 그대로.
- 참고: 사용자 데이터 vault:'none' = 서버 금고에 부계정 키 없음(b64 키 초기화 뒤 부계정 키를 다시 등록하지 않음 — 예상된 상태). 계정 칸 4개 중 키 있는 건 본계정 1개뿐 → b72 규칙으로 캐릭터 22명 중 본계정 8명만 보이고 14명은 숨김(데이터 유지, 부계정 키를 '+ 계정 추가'로 다시 넣으면 다시 보임).
- 테스트: test_tracker52 에 헤더 관리자 버튼(로그아웃 왼쪽, 새로고침 뒤, 비관리자 없음) 추가.
- 스크린샷: /workspace/maple-boss-tracker/oct12o_b77_before_header.png, oct12o_b77_after_header.png, oct12o_b77_after_reload.png, oct12o_b77_test_header.png

## b78 — 관리자 창: 차단 → 강퇴, 사용 중 10명씩 쪽 번호 (2026-10-12)
- 서버 `POST /api/admin/decide {action:'kick'}`: 그 사용자의 users 행 + user_id 로 묶인 모든 표(state·state_history·sessions·accounts·keyvault·keyvault2·keyreg·acct_role·seen·approval·cp; `USER_TABLES`, /api/account DELETE 와 공통) 삭제 → 넥슨 계정·키가 완전히 풀려 같은 키로 다시 오면 새 사용자(승인 대기). 관리자 자신·ADMIN_USER 는 강퇴 불가(400 self). block/unblock 동작은 예전 호환으로 서버에 남김(화면에는 없음).
- 화면: '사용 중'의 [차단] → [강퇴], 누르면 확인 창 '<캐릭터 이름>\n정말 강퇴할까요? 이 사용자의 등록 키와 데이터가 모두 삭제됩니다.'. 아래 '차단 · 거절' 칸 삭제. 예전 '차단' 사용자는 '사용 중'에 '(예전 차단)'으로 보이고 강퇴 가능(지금 라이브에는 0명).
- 거절(승인 대기의 [거절])은 그대로: 상태 rejected 로 남김(데이터는 처음부터 없음) — 같은 키로 요청을 반복하지 못하게. 목록에는 안 보임. 필요하면 나중에 거절도 삭제 방식으로 바꿀 수 있음.
- '사용 중' 10명씩 + 쪽 번호 버튼(1, 2, …, 11명 이상일 때만) `admPage`.
- 배포: D1 전체 백업 /workspace/backup/b78_before_20261012_151637.sql (600) 후 Worker 배포. 라이브에서는 실제 사용자를 강퇴하지 않음 — 버튼·창만 확인, 강퇴 동작은 로컬(test_tracker52)에서 확인.
- 스크린샷: /workspace/maple-boss-tracker/oct12p_b78_before_admin.png, oct12p_b78_after_admin.png, oct12p_b78_test_admin.png, oct12p_b78_test_pages.png

## b79 — 결정석 가격 카드 '마지막 확인' 시각 (2026-10-12)
- prices.json `checkedAt` = KST 전체 시각(ISO, 예 2026-10-12T19:00:12+09:00). `scripts/update_prices.py`(매일 19:00 KST Action·touch) 와 `scripts/update_feed.py`(새 공지 촉발 경로, 날짜가 바뀐 첫 실행만 — `checkedAt[:10]` 비교) 둘 다 now ISO 저장.
- 화면: '(가격 변동일 2026-09-17, 마지막 확인 10.12 19:00)' — `ckText()` 가 KST 'MM.DD HH:MM'. 예전 날짜만 있는 값은 그대로 표시. 가격 변동일은 그대로. 한 줄(390px 확인).
- 현재 prices.json 의 checkedAt 은 오늘 Action 실행 시각(커밋 57a3549, 10:53:33 KST)으로 채움 — 다음 19:00 실행부터 자동.
- 테스트: test_tracker58 (run_all 추가), test_upcoming 기대값(날짜 → ISO) 수정.
- 스크린샷: /workspace/maple-boss-tracker/oct12q_b79_before_foot.png, oct12q_b79_after_foot.png, oct12q_b79_test_foot.png

## b80 — 관리자 강퇴 뒤 하단 알림 없음 (2026-10-12)
- `admDecide`: action==='kick' 이면 '강퇴했습니다 — …' 토스트 안 띄움 (승인·거절 알림은 그대로).
- 테스트: test_tracker52 에 강퇴 직후 토스트 없음 확인 추가. 라이브에서는 실제 사용자를 강퇴하지 않으므로 로컬 서버 화면으로 확인.
- 스크린샷: /workspace/maple-boss-tracker/oct12r_b80_before_kick.png (로컬, 알림 있음), oct12r_b80_after_kick.png (로컬, 알림 없음)

## b81 — [저장] 즉시 (2026-10-12)
- 측정(라이브, 실제 데이터 22캐릭·54KB): render 26ms, contentSig 1ms — 화면은 빠름. 느렸던 원인 = [저장] 뒤 서버 저장(구독 키 동기화 + 원격 변경 확인 + PUT, 3번 왕복 ≈0.5s~수 초)이 끝날 때까지 버튼이 켜진 채(svUnsaved) 남고, 탭/캐릭터 이동 확인(예)도 그 저장을 기다렸음.
- 수정: `pendSave` = 이 PC 에 바로 확정 + '저장이 완료되었습니다.' + 버튼 꺼짐 → `svPushBg()` 가 뒤에서 서버 저장(기다리지 않음). 저장 중(`svPushing`)엔 버튼 꺼둠, 실패하면 버튼 다시 켜지고 헤더 '⚠ 저장 안 됨'(누르면 다시 저장) + 뒤에서 최대 3번 더 시도(1.5·3·4.5초). 탭/캐릭터 이동 '예'도 바로 이동.
- 테스트: test_tracker59 (서버 1.5초 지연에도 클릭 20ms 안에 확정, 뒤에서 서버 반영, 끊김 → 경고 → 다시 저장). 25·31·53·56 통과.
- 스크린샷: /workspace/maple-boss-tracker/oct12s_b81_before_save.png (라이브 이전: 저장 뒤에도 버튼 켜짐), oct12s_b81_test_save.png (저장 직후 버튼 꺼짐·완료 문구, 서버 지연 중), oct12s_b81_localtest_save.png


## b82 — 키 없는 계정 캐릭터를 모든 합계에서 제외 (2026-10-12)
- `visibleCharIds()` / `visHist(h,ids)` 추가(규칙 9). `totalData()` 의 주간·월간 기록(지난 기록 + 이번 주/달)을 보이는 캐릭터 id 로 걸러 total·cleared·crystals·items 다시 계산 → 결정석 분석(누적 수입·주별 차트·보스왕·빠뜨린 보스메소…), 득템 분석(누적 득템·득템왕·에픽빔왕·판매 수익·블빵…) 등 totalData 를 쓰는 모든 표·차트. 빠뜨린 보스 계산(missW)도 숨은 캐릭터 제외. b72 의 '지난 기록은 숨은 캐릭터도 합산' 결정을 대체.
- 기록(S.history·monthHistory)은 그대로 저장 — 키를 다시 등록하면 합계 복귀(test_tracker60). 기록 안에 id 가 없거나 지금 목록에 없는(삭제된) 캐릭터 기록도 빠짐.
- 스크린샷: /workspace/maple-boss-tracker/oct12t_b82_before_total.png, _before_loot.png (라이브 이전: 숨은 캐릭터 포함), oct12t_b82_after_total.png, _after_loot.png, oct12t_b82_test_total.png
