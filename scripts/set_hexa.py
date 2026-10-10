#!/usr/bin/env python3
"""헥사 환산 값 기록: python3 scripts/set_hexa.py NAME VALUE [--no-snapshot]
hexa.json 의 characters[NAME] = {value, updatedAt(현재 KST), snapshot(넥슨 API: 레벨·장비 해시·HEXA 해시·전투력)}.
스냅샷은 NEXON_API_KEY 가 필요. 없거나 실패하면 값만 저장하고 경고 (--no-snapshot 으로 생략)."""
import datetime, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hexa_snapshot as hs

KST = datetime.timezone(datetime.timedelta(hours=9))


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__); return 2
    name, raw = args
    v = raw.replace(",", "").strip()
    value = int(v) if v.isdigit() else (float(v) if v.replace(".", "", 1).isdigit() else raw)
    d = hs.load()
    ent = {"value": value, "updatedAt": datetime.datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00")}
    if "--no-snapshot" not in argv:
        try:
            ent["snapshot"] = hs.snapshot(name)
        except Exception as e:
            print(f"경고: 넥슨 API 스냅샷 실패 — 값만 저장 ({e})", file=sys.stderr)
    d["characters"][name] = ent
    hs.save(d)
    print(f"{name}: {value} ({ent['updatedAt']})" + (f" snapshot={ent['snapshot']}" if "snapshot" in ent else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
