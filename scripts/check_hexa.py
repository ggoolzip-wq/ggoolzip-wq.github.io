#!/usr/bin/env python3
"""헥사 환산 다시 확인이 필요한지: python3 scripts/check_hexa.py [NAME ...]
hexa.json 에 저장된 스냅샷과 지금 넥슨 API(레벨·장비·HEXA·전투력)를 비교해 캐릭터마다
'CHANGED <이름> level,equipment,…' 또는 'SAME <이름>' 을 출력. 하나라도 바뀌면 종료 코드 1, 모두 같으면 0, 오류 2.
(값은 바꾸지 않음. 바뀐 캐릭터만 브라우저에서 환산을 확인한 뒤 set_hexa.py 로 기록)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hexa_snapshot as hs


def main(names):
    d = hs.load()["characters"]
    names = names or list(d)
    changed = err = False
    for n in names:
        try:
            now = hs.snapshot(n)
        except Exception as e:
            print(f"ERROR {n} {e}"); err = True; continue
        ks = hs.diff((d.get(n) or {}).get("snapshot"), now)
        print(("CHANGED " + n + " " + ",".join(ks)) if ks else ("SAME " + n))
        changed = changed or bool(ks)
    return 1 if changed else (2 if err else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
