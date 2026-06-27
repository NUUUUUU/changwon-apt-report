"""네이버부동산 라이브 매물 수집기.

방식: new.land.naver.com 페이지 HTML에서 인증 토큰(JWT)을 추출 → Referer를 맞춰
api/articles 호출 (curl_cffi TLS 위장). 지역(cortarNo)·거래유형·가격상한으로 필터.
"""
from __future__ import annotations
import math
import os
import re
import time
from curl_cffi import requests

BASE_HEADERS = {"Accept-Language": "ko-KR,ko;q=0.9"}
TRADE_CODE = {"매매": "A1", "전세": "B1", "월세": "B2"}


def make_session():
    s = requests.Session(impersonate="chrome131")
    s.headers.update(BASE_HEADERS)
    return s


def get_token(session) -> str:
    """new.land 페이지 HTML에서 Bearer 토큰(JWT) 추출."""
    html = session.get("https://new.land.naver.com/", timeout=20).text
    m = re.search(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", html)
    if not m:
        raise RuntimeError("네이버 토큰 추출 실패 (페이지 구조 변경 가능)")
    return m.group(0)


def parse_price(s: str) -> int:
    """'2억 8,700' / '9,800' / '3억' → 만원 정수."""
    if not s:
        return 0
    s = s.replace(" ", "")
    man = 0
    if "억" in s:
        eok, _, rest = s.partition("억")
        man += int(eok) * 10000
        rest = rest.replace(",", "")
        if rest:
            man += int(rest)
    else:
        man += int(s.replace(",", "") or 0)
    return man


def fetch_region(session, token, cortar_no, trade_types, max_price, max_pages=4):
    trade_param = ":".join(TRADE_CODE[t] for t in trade_types)
    headers = {
        **BASE_HEADERS,
        "Authorization": f"Bearer {token}",
        "Referer": "https://new.land.naver.com/houses",
        "Accept": "*/*",
    }
    out = []
    for page in range(1, max_pages + 1):
        url = (
            "https://new.land.naver.com/api/articles"
            f"?cortarNo={cortar_no}&order=rank&realEstateType=APT"
            f"&tradeType={trade_param}&priceMax={max_price}&page={page}"
        )
        r = session.get(url, headers=headers, timeout=20)
        if r.status_code != 200:
            break
        data = r.json()
        for a in data.get("articleList", []):
            out.append({
                "source": "naver",
                "article_no": a.get("articleNo"),
                "complex_name": a.get("articleName"),
                "trade_type": a.get("tradeTypeName"),
                "price_raw": a.get("dealOrWarrantPrc"),
                "price_manwon": parse_price(a.get("dealOrWarrantPrc", "0")),
                "area_supply": a.get("area1"),     # 공급(㎡)
                "area_excl": a.get("area2"),        # 전용(㎡)
                "floor": a.get("floorInfo"),
                "building": a.get("buildingName"),
                "direction": a.get("direction"),
                "tags": a.get("tagList", []),
                "feature": a.get("articleFeatureDesc"),
                "confirm_date": a.get("articleConfirmYmd"),
                "realtor": a.get("realtorName"),
                "same_addr_cnt": a.get("sameAddrCnt"),
                "url": f"https://new.land.naver.com/houses?articleNo={a.get('articleNo')}",
            })
        if not data.get("isMoreData"):
            break
        time.sleep(0.4)
    return out


def dedup(listings):
    """(단지+전용+층+가격) 기준 중복 제거."""
    seen = {}
    for l in listings:
        key = (l["complex_name"], l["area_excl"], l["floor"], l["price_manwon"])
        seen.setdefault(key, l)
    return list(seen.values())


def get_dongs(session, gu_cortar):
    """구/시 cortarNo → 하위 동 목록 [{name, cortarNo, lat, lng}]."""
    r = session.get(f"https://m.land.naver.com/map/getRegionList?cortarNo={gu_cortar}", timeout=15)
    out = []
    try:
        for x in r.json().get("result", {}).get("list", []):
            out.append({"name": x["CortarNm"], "cortarNo": x["CortarNo"],
                        "lat": float(x["MapYCrdn"]), "lng": float(x["MapXCrdn"])})
    except Exception:
        pass
    return out


def haversine_km(lat1, lng1, lat2, lng2):
    p = math.pi / 180
    a = (0.5 - math.cos((lat2 - lat1) * p) / 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lng2 - lng1) * p)) / 2)
    return 2 * 6371 * math.asin(math.sqrt(a))


def collect(config):
    s = make_session()
    token = get_token(s)
    f = config["filters"]
    w = config["workplace"]
    radius = config.get("commute_radius_km", 14)
    all_listings = []
    per_region = {}
    for gu in config["regions_gu"]:
        dongs = get_dongs(s, gu["cortarNo"])
        near = [d for d in dongs if haversine_km(d["lat"], d["lng"], w["lat"], w["lng"]) <= radius]
        for d in near:
            ls = fetch_region(s, token, d["cortarNo"], f["trade_types"], f["max_price_manwon"])
            for l in ls:
                l["gu"], l["lawd"], l["dong"] = gu["name"], gu.get("lawd"), d["name"]
            if ls:
                per_region[f"{gu['name']}·{d['name']}"] = len(ls)
            all_listings.extend(ls)
        time.sleep(0.3)
    return dedup(all_listings), per_region


if __name__ == "__main__":
    import yaml
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    cfg = yaml.safe_load(open(os.path.join(root, "config.yaml"), encoding="utf-8"))
    listings, per_region = collect(cfg)
    print("토큰 확보 OK · 지역별 수집:")
    for name, n in per_region.items():
        print(f"  {name}: {n}건")
    print(f"\n총 {len(listings)}건 (중복제거 후)\n")
    print("── 샘플 12건 ──")
    for l in listings[:12]:
        tags = ",".join(l["tags"]) if l["tags"] else "-"
        print(f"· {l['complex_name']} | {l['trade_type']} {l['price_manwon']}만 | "
              f"공급{l['area_supply']}/전용{l['area_excl']}㎡ | {l['floor']} | "
              f"{l['building'] or '-'} | {l['direction'] or '-'} | tags:{tags}")
