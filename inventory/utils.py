# inventory/utils.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class AlertResult:
    """在庫1件のアラート判定結果（テンプレ表示用）"""
    is_red: bool
    is_blue: bool
    days_left: Optional[int]  # expiry_date が無い場合は None


def calc_days_left(expiry_date: Optional[date], today: date) -> Optional[int]:
    """
    期限までの残日数を返す。
    - expiry_date が None のときは None
    - 今日が 2026-02-27、期限が 2026-02-28 なら 1
    """
    if not expiry_date:
        return None
    return (expiry_date - today).days


def judge_alert(
    *,
    quantity: int,
    expiry_date: Optional[date],
    today: date,
    quantity_threshold: Optional[int],
    expiry_days: Optional[int],
) -> AlertResult:
    """
    赤/青の判定を一箇所にまとめる（ビューやテンプレにロジックを散らさない）
    優先順位：赤 > 青
    """

    days_left = calc_days_left(expiry_date, today)

    # ----------------------------
    # 赤：個数0 AND 期限切れ（expiry_date が無いなら赤にはしない）
    # ----------------------------
    is_red = bool(expiry_date) and quantity == 0 and expiry_date < today

    # ----------------------------
    # 青：赤でない AND（個数少ない OR 期限が近い）
    # - 閾値が未設定(None)なら、その条件は判定しない
    # - expiry_date が無いなら、期限条件は判定しない
    # ----------------------------
    is_low_stock = (quantity_threshold is not None) and (quantity <= quantity_threshold)

    is_expiring_soon = (
        (expiry_days is not None)
        and (days_left is not None)
        and (days_left <= expiry_days)
    )

    is_blue = (not is_red) and (is_low_stock or is_expiring_soon)

    return AlertResult(is_red=is_red, is_blue=is_blue, days_left=days_left)