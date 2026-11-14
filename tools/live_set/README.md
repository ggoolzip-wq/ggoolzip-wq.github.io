# 전체 라이브 회귀 세트 (b428, 사용자 지시 t564u·t565u·t566u)

인식 코드(맵·난이도·상자·닉·공중 아이템)를 바꾸면 **받은 모든 보상 영상**을 실제 라이브 인식기(index.html, 크롬)로 다시 돌려
화면 확인 정답(`truth.json`)과 비교한다. **전부 PASS 가 배포 조건** (아이템 오기록 0 포함).

- 영상: 박스 `/workspace/reward_live_set/vids/*.mp4` (a1–a4, h2–h6, n1–n7, v01–v10(v08 없음), w01–w09, x01–x08 = 42개). 저장소에는 영상을 넣지 않음.
- 정답 `truth.json`: 영상마다 닉(화면 좌하단 Lv 옆 이름), 보스, 난이도(맵 이름 <난이도>), 아이템(공중 드롭 줄 화면 확인한 기록 대상).
  `itemsChecked:false` 영상은 '기록 대상 오기록 없음'만 채점(드롭 줄 전수 확인 전).
- 실행:
  ```
  LIVE_VIDDIR=/workspace/reward_live_set/vids LIVE_ROOT=<저장소> LIVE_SPEC=tools/live_set/truth.json \
  LIVE_OUT=/tmp/out LIVE_CHARS='["림강혼망","2터래플","터래플","zetking","린벨자","랑트킹","트딕이"]' python3 tools/live_set/run_set.py
  python3 tools/live_set/score.py /tmp/out_old /tmp/out     # 영상별 PASS/FAIL 표, 합계
  ```
- 채점: 보스·난이도는 '보상 상자 감지' 순간 기준(영상 끝에 다음 보스 대기맵으로 이동하는 경우가 많음. 상자 순간 난이도 미정이면 같은 보스 맵 읽기의 최다 난이도 = arBossState 동작),
  닉 = 마지막 확정 캐릭터, 해상도 = 프로필 확정, 아이템 = 자동 기록(runRec) 종류·개수.
