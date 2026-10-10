#!/usr/bin/env python3
"""데모 '테섭 예정' 가격 삭제: prices.json 의 upcoming 이 demo=True 일 때만 지움 (진짜 테섭 예정 가격은 건드리지 않음).
사용: python3 scripts/remove_demo_upcoming.py && git commit -am '데모 테섭 예정 가격 삭제' && git push"""
import json, os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prices.json")
d = json.load(open(P, encoding="utf-8"))
if (d.get("upcoming") or {}).get("demo"):
    d.pop("upcoming")
    with open(P, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1); f.write("\n")
    print("데모 예정 가격 삭제됨")
else:
    print("데모 예정 가격 없음 — 변경 없음")
