"""하드 필터 — 면적(30평대·디딤돌), 가격, 연식(태그 기반 1차)."""
from __future__ import annotations

PYEONG = 3.305785  # 1평 = 3.305785㎡


def m2_to_pyeong(m2: float) -> float:
    return m2 / PYEONG if m2 else 0.0


def apply_area_filter(listings, config):
    """공급 30평대 & 전용 ≤ 디딤돌 상한(85㎡)."""
    f = config["filters"]
    out = []
    for l in listings:
        try:
            a1 = float(l.get("area_supply"))   # 공급
            a2 = float(l.get("area_excl"))      # 전용
        except (TypeError, ValueError):
            continue
        py = m2_to_pyeong(a1)
        if f["supply_pyeong_min"] <= py < f["supply_pyeong_max"] + 1 and a2 <= f["area_exclusive_max_m2"]:
            l["supply_pyeong"] = round(py, 1)
            out.append(l)
    return out


def tag_renovated(listing) -> bool:
    return any("올수리" in t or "리모델링" in t for t in listing.get("tags", []))


def tag_over_25y(listing) -> bool:
    return any("25년이상" in t for t in listing.get("tags", []))
