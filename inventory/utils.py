# inventory/utils.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class AlertResult:
    """
    在庫一覧表示用のアラート判定結果
    - is_red : 赤字＋🔔（最優先）
    - is_blue: 青字＋🔔
    - days_left: 期限までの残日数（expiry_dateが無い場合はNone）
    """
    is_red: bool
    is_blue: bool
    days_left: Optional[int]

def _calc_days_left(expiry_date: Optional[date], today: date) -> Optional[int]:
    """
    期限までの残日数を返す
    例）今日=2/27、期限=2/28 → 1
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
    赤/青のアラート判定を行う（赤優先）

    仕様：
    - 赤：quantity==0 かつ expiry_date < 今日
    - 青：quantity <= quantity_threshold または days_left <= expiry_days（ただし赤優先）
    - expiry_dateがNoneの場合、期限判定はしない（落ちない）
    - 閾値がNoneの場合、その条件は判定しない（落ちない）
    """

    days_left = _calc_days_left(expiry_date, today)
    
    # 赤判定（最優先）
    # expiry_date が無い場合は赤にしない
    is_red = bool(expiry_date) and (quantity == 0) and (expiry_date < today)

    # 青判定（赤の時は出さない）
    is_low_stock = (quantity_threshold is not None) and (quantity <= quantity_threshold)

    is_expiring_soon = (
        (expiry_days is not None)
        and (days_left is not None)
        and (days_left <= expiry_days)
    )

    is_blue = (not is_red) and (is_low_stock or is_expiring_soon)

    return AlertResult(is_red=is_red, is_blue=is_blue, days_left=days_left)