#!/usr/bin/env bash
# 전체 회귀 테스트 (Playwright 필요: pip install playwright && python -m playwright install chromium)
# 크롬 경로를 쓰려면 CHROME=/usr/bin/google-chrome. 스크린샷은 tests/out/
cd "$(dirname "$0")/.."
mkdir -p tests/out; fail=0
for n in 4 5 6 7 8 9 10 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 34 35 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103; do
  echo "== test_tracker$n"; python3 tests/test_tracker$n.py > tests/out/r$n.log 2>&1 || fail=1
  grep -E 'FAIL|ERRORS|Error' tests/out/r$n.log | tail -3
done
for t in tab_recount upcoming price_time feed_minor feed_sunday feed_keys sunday_ocr sunday_watch server server_b91 server_b94 server_b132 avg_done b179 b183 sync_speed b185 b187 b190 b193 b198 b200 b203 b206 b207 b208 b209 b210 b211 b213 b216 b217 b218 b219 b220 b221 b223 b224 b225 b225_items b229 b229_rred b230 b233 zosu_bgkey zosu_ringbtn b234_purge server_b234 b239 b241 b243 b244 b246 b247 b248 b249 b250 b251 b252 b253 b254 b255 b256 b257 b258 b260 b261 b262 b263; do  # server, 23: wrangler 없으면 SKIP (server/README.md)
  echo "== test_$t"; python3 tests/test_$t.py > tests/out/r_$t.log 2>&1 || fail=1
  grep -E 'FAIL' tests/out/r_$t.log | tail -3
done
exit $fail
