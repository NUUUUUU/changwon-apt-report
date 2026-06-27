"""카카오 로컬 — 육아 인프라(어린이집·초등) + 상권(마트·병원). 타임아웃 재시도 포함."""
from __future__ import annotations
import os
import re
import time
import requests

CAT = "https://dapi.kakao.com/v2/local/search/category.json"
KW = "https://dapi.kakao.com/v2/local/search/keyword.json"


def _headers():
    return {"Authorization": f"KakaoAK {os.environ['KAKAO_REST_KEY']}"}


def _get(url, params, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=_headers(), timeout=15)
            return r.json() if r.status_code == 200 else None
        except requests.RequestException:
            time.sleep(0.6)
    return None


def _count_cat(lng, lat, code, radius=1500):
    d = _get(CAT, {"category_group_code": code, "x": lng, "y": lat, "radius": radius, "size": 1})
    return (d or {}).get("meta", {}).get("total_count", 0)


def nearest_school(lng, lat):
    d = _get(KW, {"query": "초등학교", "x": lng, "y": lat, "radius": 2000, "size": 15})
    docs = [x for x in (d or {}).get("documents", []) if "초등학교" in x["place_name"]]
    if not docs:
        return None
    nd = min(docs, key=lambda x: int(x.get("distance") or 999999))
    name = re.sub(r"(초등학교).*", r"\1", nd["place_name"])   # '교무실/후문' 등 제거
    return {"name": name, "dist_m": int(nd.get("distance") or 0),
            "x": float(nd["x"]), "y": float(nd["y"])}


def _places(lng, lat, code, radius, size=3):
    d = _get(CAT, {"category_group_code": code, "x": lng, "y": lat,
                   "radius": radius, "size": size, "sort": "distance"})
    return [{"name": x["place_name"], "x": float(x["x"]), "y": float(x["y"])}
            for x in (d or {}).get("documents", [])]


def enrich(lng, lat):
    sch = nearest_school(lng, lat)
    markers = []
    if sch and sch.get("x"):
        markers.append({"name": sch["name"], "x": sch["x"], "y": sch["y"], "type": "school"})
    markers += [{**p, "type": "daycare"} for p in _places(lng, lat, "PS3", 800, 3)]
    return {
        "daycare": _count_cat(lng, lat, "PS3", 1000),
        "nearest_school": sch,
        "mart": _count_cat(lng, lat, "MT1", 1500),
        "hospital": _count_cat(lng, lat, "HP8", 1500),
        "markers": markers,
    }
