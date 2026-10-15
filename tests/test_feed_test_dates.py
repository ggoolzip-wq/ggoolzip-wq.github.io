# b159: 테섭 목록 날짜 파싱 — 오늘 글(시각만 표시)이 다음 글의 날짜를 가져가던 버그 (네트워크 없음)
import os, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import update_feed as F
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
li = lambda n, t, d: f'<li><p><a href="/Testworld/News/Update/{n}"><em class="new">NEW</em><span>{t}</span></a></p><dl><dt>작성일</dt><dd>{d}</dd></dl></li>'
html = '<ul class="update_board">' + li(202, "클라이언트 1.2.207 릴리즈", "오후 3:12") + li(201, "점검 안내", "PM 1:05") + li(199, "클라이언트 1.2.206 릴리즈(이벤트)", "2026.09.10") + li(198, "클라이언트 1.2.206 릴리즈(스킬 조정)", "2026.09.09") + "</ul>"
rows = F.parse_test(html, today=datetime.date(2026, 10, 15))
by = {r["n"]: r for r in rows}
check("4 rows", len(rows) == 4, [(r["n"], r["date"]) for r in rows])
check("오늘 글(오후 3:12) → 2026-10-15 15:12 (다음 글 날짜 아님)", by[202]["date"] == "2026-10-15T15:12:00+09:00", by[202]["date"])
check("PM 1:05 → 13:05", by[201]["date"] == "2026-10-15T13:05:00+09:00", by[201]["date"])
check("yyyy.mm.dd 그대로", by[199]["date"] == "2026-09-10T00:00:00+09:00" and by[198]["date"] == "2026-09-09T00:00:00+09:00", (by[199]["date"], by[198]["date"]))
check("제목에서 NEW 표시 제거", by[202]["title"] == "클라이언트 1.2.207 릴리즈", by[202]["title"])
lst = [{"id": "test:202", "date": "2026-09-10T00:00:00+09:00"}, {"id": "test:199", "date": "2026-09-10T00:00:00+09:00"}, {"id": "test:1", "date": "2026-01-01T00:00:00+09:00"}]
n = F.fix_test_dates(lst, rows)
check("저장된 잘못된 날짜 보정(일이 다른 것만)", n == 1 and lst[0]["date"] == "2026-10-15T15:12:00+09:00" and lst[1]["date"] == "2026-09-10T00:00:00+09:00" and lst[2]["date"].startswith("2026-01-01"), lst)
print("FAILS:", fails)
sys.exit(1 if fails else 0)
