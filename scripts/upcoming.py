"""테섭 공지에서 찾은 결정석 가격 변경 = '예정 가격' (prices.json 의 upcoming).
- 실서버 가격(rows)은 바꾸지 않음. 본섭 패치(update_prices.py)가 같은 가격을 적용하면 해당 줄을 지움.
- upcoming = {"source": {url,title,date}, "rows": [{boss, old?, new}], "detectedAt": iso}
"""
import re, datetime

KST = datetime.timezone(datetime.timedelta(hours=9))


def bkey(s):
    return re.sub(r"\s+", "", str(s or "")).replace("（", "(").replace("）", ")")


def reconcile(prices):
    """실서버 가격과 같아진 예정 줄 삭제. 바뀌었으면 True"""
    up = prices.get("upcoming")
    if not up:
        return False
    live = {bkey(r.get("boss")): r.get("new") for r in prices.get("rows", [])}
    keep = [r for r in up.get("rows", []) if live.get(bkey(r.get("boss"))) != r.get("new")]
    if len(keep) == len(up.get("rows", [])):
        return False
    if keep:
        up["rows"] = keep
    else:
        prices.pop("upcoming", None)
    return True


def add_upcoming(prices, source, rows, now=None):
    """테섭 글의 가격 줄을 예정 가격으로 (같은 보스는 새 글이 덮어씀). 실서버와 같은 줄은 넣지 않음. 바뀌었으면 True"""
    live = {bkey(r.get("boss")): r.get("new") for r in prices.get("rows", [])}
    cur = {bkey(r["boss"]): r for r in (prices.get("upcoming") or {}).get("rows", [])}
    before = dict(cur)
    for r in rows:
        if not isinstance(r.get("new"), int) or r["new"] <= 0 or not r.get("boss"):
            continue
        k = bkey(r["boss"])
        if live.get(k) == r["new"]:
            cur.pop(k, None)
            continue
        cur[k] = {x: r[x] for x in ("boss", "old", "new") if x in r}
    if cur == before:
        return False
    if cur:
        prices["upcoming"] = {"source": source, "rows": list(cur.values()),
                              "detectedAt": (now or datetime.datetime.now(KST)).isoformat(timespec="seconds")}
    else:
        prices.pop("upcoming", None)
    return True
