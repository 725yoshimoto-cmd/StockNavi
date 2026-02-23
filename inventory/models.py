from django.db import models
from accounts.models import Household


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
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name="カテゴリ",
    )

    name = models.CharField("在庫名", max_length=100)
    quantity = models.IntegerField("数量", default=0)

    def __str__(self):
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
    title = models.CharField("タイトル", max_length=100)
    body = models.TextField("本文", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title