from django.db import models
from accounts.models import Household
from django.conf import settings  # ← 追加（上部）

class InventoryItem(models.Model):
    """
    InventoryItem（在庫）
    """
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # ★カテゴリ（最初は未設定でも登録できるように null/blank OK にする）
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )

    storage_location = models.ForeignKey(
        "StorageLocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )

    name = models.CharField("在庫名", max_length=100)
    quantity = models.IntegerField("数量", default=0)

    def __str__(self):
        return self.name
    
    
class Category(models.Model):
    """
    Category（カテゴリ）マスタ
    - 世帯ごとにカテゴリを持てる（他世帯のカテゴリは見えない想定）
    """
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField("カテゴリ名", max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 同じ世帯で同名カテゴリを重複させない（例：食料が2つできない）
        constraints = [
            models.UniqueConstraint(
                fields=["household", "name"],
                name="uniq_household_category_name",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name



class StorageLocation(models.Model):
    """
    保管場所（ER図: storage_locations）
    世帯ごとに保管場所マスタを持つ想定。
    """
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="storage_locations",
    )

    name = models.CharField(max_length=50)  # 例: "キッチン棚", "玄関収納"
    description = models.CharField(max_length=255, blank=True)  # 概要（任意）

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 同一世帯で同名の保管場所を作れないようにする（地味に事故防止）
        constraints = [
            models.UniqueConstraint(
                fields=["household", "name"],
                name="uniq_storage_location_per_household",
            )
        ]

    def __str__(self) -> str:
        return self.name
    
    
class Memo(models.Model):
    """
    Memo（メモ）
    """
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="memos"
    )

    # ★ 追加（作成者）
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memos"
    )

    title = models.CharField("タイトル", max_length=100)
    body = models.TextField("本文", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title