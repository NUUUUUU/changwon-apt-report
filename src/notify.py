"""카카오톡 '나에게 보내기' — refresh_token으로 access_token 갱신 후 메모 전송."""
from __future__ import annotations
import json
import os
import requests

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


def _fmt_price(man):
    if man is None:
        return "-"
    eok, rest = divmod(int(man), 10000)
    if eok and rest:
        return f"{eok}억{rest:,}"
    if eok:
        return f"{eok}억"
    return f"{rest:,}만"


def get_access_token():
    r = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "client_id": os.environ["KAKAO_REST_KEY"],
        "client_secret": os.environ.get("KAKAO_CLIENT_SECRET", ""),
        "refresh_token": os.environ["KAKAO_REFRESH_TOKEN"],
    }, timeout=15)
    return r.json().get("access_token")


def send_to_me(text, link_url=None, button_title="매물 보기"):
    token = get_access_token()
    if not token:
        raise RuntimeError("access_token 발급 실패 (refresh_token 확인)")
    fallback = link_url or "https://m.land.naver.com"
    tmpl = {
        "object_type": "text",
        "text": text[:200],
        "link": {"web_url": fallback, "mobile_web_url": fallback},
    }
    if link_url:
        tmpl["button_title"] = button_title
    r = requests.post(MEMO_URL, headers={"Authorization": f"Bearer {token}"},
                      data={"template_object": json.dumps(tmpl, ensure_ascii=False)}, timeout=15)
    return r.status_code, r.json()


def build_summary(top, meta):
    head = f"🏠 창원 통근권 아파트 Top5 · {meta['date'][5:].replace('-', '/')}"
    lines = [head]
    for i, l in enumerate(top[:5], 1):
        uv, jr = l.get("undervalue_pct"), l.get("jeonse_ratio")
        m = f"저평가{uv:+.0f}%" if uv is not None else (f"전세{jr:.0f}%" if jr else "")
        lines.append(f"{i}.{l['complex_name']} {_fmt_price(l['price_manwon'])}·{l['commute_min']:.0f}분·{m}")
    return "\n".join(lines)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    code, resp = send_to_me("📨 창원 아파트 리포트 — 카톡 발송 테스트 성공!\n"
                            "이제 매일 아침 이 채팅(나와의 채팅)으로 Top5를 보내드릴게요. 🏠")
    print("발송 결과:", code, resp)
