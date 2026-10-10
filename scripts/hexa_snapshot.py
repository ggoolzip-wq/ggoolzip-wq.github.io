"""헥사 환산 변경 감지용 넥슨 API 스냅샷 (레벨 · 장비 해시 · HEXA · 전투력). maplescouter 는 호출하지 않음.
키: 환경변수 NEXON_API_KEY (또는 NEXON_API_KEY2)."""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_feed as uf  # nx(): 넥슨 Open API 호출 (키 2개 전환)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEXA = os.path.join(ROOT, "hexa.json")


def _h(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def _strip(x):  # 'date' 등 매번 바뀌는 값 제외
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k != "date"}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def snapshot(name):
    ocid = uf.nx("id", character_name=name)["ocid"]
    basic = uf.nx("character/basic", ocid=ocid)
    eq = uf.nx("character/item-equipment", ocid=ocid)
    hx = uf.nx("character/hexamatrix", ocid=ocid)
    hs = uf.nx("character/hexamatrix-stat", ocid=ocid)
    st = uf.nx("character/stat", ocid=ocid)
    cp = next((s.get("stat_value") for s in st.get("final_stat") or [] if s.get("stat_name") == "전투력"), None)
    return {"level": basic.get("character_level"), "equipment": _h(_strip(eq)),
            "hexa": _h(_strip({"core": hx, "stat": hs})), "combatPower": int(cp) if str(cp or "").isdigit() else cp}


def load():
    try:
        with open(HEXA, encoding="utf-8") as f:
            d = json.load(f)
    except FileNotFoundError:
        d = {}
    d.setdefault("characters", {})
    return d


def save(d):
    with open(HEXA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1); f.write("\n")


def diff(old, new):
    return [k for k in ("level", "equipment", "hexa", "combatPower") if (old or {}).get(k) != new.get(k)]
