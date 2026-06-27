"""카카오 로컬(지오코딩) + 모빌리티(통근 차량시간). 타임아웃 재시도 포함."""
from __future__ import annotations
import os
import time
import requests

LOCAL_KEYWORD = "https://dapi.kakao.com/v2/local/search/keyword.json"
DIRECTIONS = "https://apis-navi.kakaomobility.com/v1/directions"


def _headers():
    key = os.environ.get("KAKAO_REST_KEY")
    if not key:
        raise RuntimeError("KAKAO_REST_KEY 미설정 (.env 확인)")
    return {"Authorization": f"KakaoAK {key}"}


def _get(url, params, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=_headers(), timeout=15)
            return r.json() if r.status_code == 200 else None
        except requests.RequestException:
            time.sleep(0.6)
    return None


def geocode(query: str):
    d = _get(LOCAL_KEYWORD, {"query": query, "size": 1})
    docs = (d or {}).get("documents", [])
    if not docs:
        return None
    return float(docs[0]["x"]), float(docs[0]["y"])


def commute_minutes(lng: float, lat: float, w_lng: float, w_lat: float):
    d = _get(DIRECTIONS, {"origin": f"{lng},{lat}", "destination": f"{w_lng},{w_lat}"})
    routes = (d or {}).get("routes", [])
    if routes and routes[0].get("result_code") == 0:
        return round(routes[0]["summary"]["duration"] / 60, 1)
    return None


def rush_commute(lng: float, lat: float, w_lng: float, w_lat: float, per_min=0.05):
    """출근(매물→공장)+퇴근(공장→매물) 평균에 러시아워 혼잡 보정(장거리일수록↑)."""
    go = commute_minutes(lng, lat, w_lng, w_lat)        # 출근
    back = commute_minutes(w_lng, w_lat, lng, lat)      # 퇴근
    vals = [v for v in (go, back) if v is not None]
    if not vals:
        return None
    base = sum(vals) / len(vals)
    return round(base * (1 + base * per_min), 1)
