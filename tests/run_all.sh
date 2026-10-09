#!/usr/bin/env bash
# 전체 회귀 테스트 (Playwright 필요: pip install playwright && python -m playwright install chromium)
# 크롬 경로를 쓰려면 CHROME=/usr/bin/google-chrome. 스크린샷은 tests/out/
cd "$(dirname "$0")/.."
mkdir -p tests/out; fail=0
for n in 4 5 6 7 8 9 10 11 12 13 14 15; do
  echo "== test_tracker$n"; python3 tests/test_tracker$n.py > tests/out/r$n.log 2>&1 || fail=1
  grep -E 'FAIL|ERRORS|Error' tests/out/r$n.log | tail -3
done
exit $fail
