import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class Household(models.Model):
    """
    Household（世帯）テーブル
    - どの世帯のデータか（在庫・メモ等）をひも付けるための「土台」
    """
    name = models.CharField("世帯名", max_length=50)
    created_at = models.DateTimeField("作成日時", auto_now_add=True)

    # 目標備蓄日数（画面設計図：3/7/14/カスタム）:contentReference[oaicite:6]{index=6}
    target_days = models.PositiveIntegerField(default=3)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """
    CustomUser（カスタムユーザー）
    - Djangoの標準Userを拡張して、このアプリ用に項目を追加できる
    - household：ユーザーが所属する世帯（1ユーザーは1世帯に所属する想定）
    """
    household = models.ForeignKey(
        Household,
        on_delete=models.SET_NULL,  # 世帯が消えてもユーザーを消さない
        null=True,
        blank=True,  # まずは未所属でもOKにして進める
        related_name="users",
        verbose_name="所属世帯",
    )


class Invitation(models.Model):
    """
    世帯への招待モデル
    """

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="invitations"
    )

    invited_email = models.EmailField("招待メールアドレス")

    invited_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="sent_invitations"
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    is_accepted = models.BooleanField(default=False)

    accepted_user = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accepted_invitations"
    )

    created_at = models.DateTimeField(auto_now_add=True)

class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["household", "invited_email"],
            name="uniq_household_invited_email",
        )
    ]

    def __str__(self):
        return f"{self.household.name} → {self.invited_email}"

class AlertSetting(models.Model):
    """
    世帯ごとのアラート判定基準
    - quantity_threshold: 個数アラートの閾値（例: 1個以下）
    - expiry_days: 期限アラートの閾値（例: 30日以内）
    """
    household = models.OneToOneField(
        "accounts.Household",
        on_delete=models.CASCADE,
        related_name="alert_setting",
    )

    quantity_threshold = models.PositiveIntegerField(default=1)
    expiry_days = models.PositiveIntegerField(default=30)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AlertSetting(household={self.household_id})"
    