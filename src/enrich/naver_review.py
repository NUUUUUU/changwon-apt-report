"""실거주자 후기 — 네이버 검색 API(블로그/카페) 스니펫. 키 없으면 None."""
from __future__ import annotations
import html
import os
import re
import requests

BLOG = "https://openapi.naver.com/v1/search/blog.json"
CAFE = "https://openapi.naver.com/v1/search/cafearticle.json"


def _strip(s):
    return re.sub(r"<[^>]+>", "", html.unescape(s or "")).strip()


def fetch_reviews(complex_name, gu, max_n=3):
    cid = os.environ.get("NAVER_CLIENT_ID")
    csec = os.environ.get("NAVER_CLIENT_SECRET")
    if not cid or not csec:
        return None   # 키 미설정 → 호출부에서 안내문 표시
    headers = {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}
    out = []
    for src, url in [("블로그", BLOG), ("카페", CAFE)]:
        try:
            r = requests.get(url, params={"query": f"{complex_name} {gu} 실거주 후기",
                                          "display": 3, "sort": "sim"},
                             headers=headers, timeout=10)
            for it in r.json().get("items", []):
                out.append({"src": src, "title": _strip(it.get("title")),
                            "desc": _strip(it.get("description"))[:110],
                            "link": it.get("link", "")})
        except Exception:
            pass
    return out[:max_n]
