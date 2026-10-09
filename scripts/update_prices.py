#!/usr/bin/env python3
"""결정석 가격 자동 갱신 (GitHub Actions 에서 매일 실행, 표준 라이브러리만 사용)

maplestory.nexon.com 업데이트 공지 목록을 최신순으로 확인해 '강렬한 힘의 결정' 가격표가 있는
가장 최근 공지를 찾고(scripts/nexon_prices.py 파서), 사이트 루트의 prices.json 을 갱신합니다.

- 가격표가 바뀌었을 때만 파일을 바꿉니다. 같으면 일주일에 한 번만 checkedAt(마지막 확인)을 갱신합니다.
- 접속 실패·형식 변경 등으로 읽지 못하면 기존 prices.json 을 그대로 두고 경고만 남깁니다(종료 코드 0).
- 이전 공지(현재 prices.json 보다 오래된 공지)의 표로 되돌리지 않습니다.
"""
import datetime, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nexon_prices as parser  # noqa: E402  (공지 가격표 파서)

OUT = os.path.join(ROOT, "prices.json")
MIN_ROWS = 20          # 이보다 적으면 파싱이 잘못된 것으로 보고 저장하지 않음
HEARTBEAT_DAYS = 7     # 내용이 같아도 이 주기마다 '마지막 확인' 날짜 갱신
KST = datetime.timezone(datetime.timedelta(hours=9))


def warn(msg):
    print(f"::warning::{msg}")


def post_id(url):
    m = re.search(r"/(\d+)/?$", url or "")
    return int(m.group(1)) if m else 0


def main():
    old = None
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as f:
                old = json.load(f)
        except Exception as e:
            warn(f"기존 prices.json 을 읽지 못함: {e}")
    today = datetime.datetime.now(KST).strftime("%Y-%m-%d")
    try:
        res = parser.nexon_prices(posts=int(os.environ.get("MBT_POSTS", "15")))
    except Exception as e:
        warn(f"공식 홈페이지 접속/파싱 실패 — 기존 prices.json 유지: {type(e).__name__}: {e}")
        return 0
    for s in res.get("scanned", []):
        print("확인:", s.get("url"), s.get("title"), "rows=", s.get("rows"), s.get("error", ""))

    if not res.get("ok"):
        # 목록은 읽었지만 최근 공지에 가격표가 없음 = 가격 변경 없음
        if res.get("error", {}).get("name") == "NO_PRICE_TABLE" and old:
            print("최근 공지에 새 가격표 없음 — 기존 가격 유지")
            return touch(old, today)
        warn(f"가격표를 찾지 못함 — 기존 prices.json 유지: {res.get('error')}")
        return 0

    rows = [{k: r[k] for k in ("boss", "old", "new", "effective", "effective_note") if k in r} for r in res["rows"]]
    if len(rows) < MIN_ROWS or any(not isinstance(r.get("new"), int) or r["new"] <= 0 for r in rows):
        warn(f"가격표 형식이 이상함(rows={len(rows)}) — 기존 prices.json 유지")
        return 0
    if old and post_id(res["source"]["url"]) < post_id(old.get("source", {}).get("url")):
        print("찾은 공지가 현재 것보다 오래됨 — 기존 가격 유지")
        return touch(old, today)

    new = {"version": 1, "source": res["source"], "rows": rows, "notes": res.get("notes", []),
           "checkedAt": today, "fetchedAt": res.get("fetchedAt")}
    if old and old.get("rows") == new["rows"] and old.get("source") == new["source"]:
        print("가격 변경 없음")
        return touch(old, today)
    write(new)
    print(f"prices.json 갱신: {new['source']['title']} ({len(rows)}개)")
    return 0


def touch(old, today):
    last = old.get("checkedAt") or "1970-01-01"
    if (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(last)).days >= HEARTBEAT_DAYS:
        old["checkedAt"] = today
        write(old)
        print("마지막 확인 날짜 갱신:", today)
    return 0


def write(obj):
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, OUT)


if __name__ == "__main__":
    sys.exit(main())
