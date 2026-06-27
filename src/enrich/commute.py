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
