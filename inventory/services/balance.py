# inventory/services/balance.py
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce

from inventory.models import InventoryItem, Category


def calc_category_amounts(household, storage_location_id=None):
    """
    分類（Category）ごとの現在量を集計する。
    画面設計図の「内容量 × 個数」で計算する前提。
    - household で必ず絞る（他世帯混入防止）
    - storage_location_id があれば保管場所でも絞る
    - 0件でも落ちない（Coalesceで0にする）
    """
    qs = InventoryItem.objects.filter(household=household)

    # 保管場所フィルタ（任意）
    if storage_location_id:
        qs = qs.filter(storage_location_id=storage_location_id)

    # category_idごとの合計：content_amount * quantity
    agg = (
        qs.values("category_id")
        .annotate(
            current_amount=Coalesce(
                Sum(F("content_amount") * F("quantity"), output_field=FloatField()),
                0.0,
            )
        )
    )
    current_map = {row["category_id"]: float(row["current_amount"]) for row in agg}

    # 分類マスタ（世帯の分類だけ）
    categories = Category.objects.filter(household=household).order_by("name")

    rows = []
    total = 0.0
    for c in categories:
        cur = current_map.get(c.id, 0.0)
        total += cur

        goal = float(c.goal_amount or 0.0)
        achievement = 0.0 if goal <= 0 else (cur / goal) * 100  # 目標0でも落ちない

        rows.append(
            {
                "id": c.id,
                "name": c.name,
                "color": c.color,
                "goal_amount": goal,
                "goal_unit": c.goal_unit,
                "current_amount": cur,
                "achievement_percent": achievement,
            }
        )

    # 円グラフ用：分類割合（total=0でも落ちない）
    for r in rows:
        r["share_percent"] = 0.0 if total <= 0 else (r["current_amount"] / total) * 100

    # 不足しているもの（達成度が低い順）を上に
    rows.sort(key=lambda x: x["achievement_percent"])
    
    return rows, total