from django.db import models
from accounts.models import Household
from django.conf import settings  # ← 追加（上部）
from django.utils import timezone

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
    
    # 画面設計図の「内容量」：内容量 × 個数で集計するために追加
    # 例）水 2L、缶詰 1個 など
    # 既存データがあっても落ちないよう default を入れる
    content_amount = models.FloatField(default=1.0)

    # ★追加：期限日（アラート判定用）
    expiry_date = models.DateField(
        "賞味期限",
        null=True,   # 既存データがあるため必須にしない
        blank=True   # フォーム未入力を許可
    )
    # もし unit を今すぐ増やすと工数増えるので、今回は最小で content_amount のみ追加
    def __str__(self):
        return self.name
    
        created_at = models.DateTimeField("登録日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)
        
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
    # 分類ごとの目標量（例：36）:contentReference[oaicite:7]{index=7}
    goal_amount = models.FloatField(default=0)

    # 目標の単位（L or 個）:contentReference[oaicite:8]{index=8}
    GOAL_UNIT_CHOICES = [
        ("L", "L"),
        ("PCS", "個"),
    ]
    goal_unit = models.CharField(max_length=10, choices=GOAL_UNIT_CHOICES, default="PCS")

    # ----------------------------
    # 分類カラー（HEX 形式） 例: "#ff0000"
    # - フロントで色選択できるようにする
    # - default を入れておくと既存データでも migration で事故らない
    # ----------------------------
    color = models.CharField(
        max_length=7,
        blank=True,
        default="#f1e8ff",  # 既定色（薄い紫）
        help_text="例：#ffcc00"
    )

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