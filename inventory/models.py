from django.db import models

# accountsアプリのHouseholdモデル（世帯）を参照する
from accounts.models import Household


class InventoryItem(models.Model):
    # どの世帯の在庫か？（1つの世帯に在庫がたくさん紐づく）
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,   # 世帯が削除されたら、その世帯の在庫も削除
        related_name="items"        # household.items で在庫一覧を取れる（任意だけど便利）
    )

    # 在庫名
    name = models.CharField(max_length=100)

    # 数量（デフォルト0）
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name
