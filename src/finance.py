"""디딤돌 대출 추정 (가정치 — 실제 한도·금리는 조건별 상이)."""
from __future__ import annotations

# 디딤돌 일반 한도(만원) 가정치. 신혼·다자녀 등은 상향. 본인 조건별 상이.
DDIMDOL_CAP = 25000
LTV = 0.70


def estimate(price_manwon, trade_type):
    """매매 매물 → {loan(추정대출), cash(필요현금), ltv}. 전세/실패 시 None."""
    if trade_type != "매매" or not price_manwon:
        return None
    loan = min(int(price_manwon * LTV), DDIMDOL_CAP)
    return {"loan": loan, "cash": price_manwon - loan, "ltv_pct": int(LTV * 100)}
