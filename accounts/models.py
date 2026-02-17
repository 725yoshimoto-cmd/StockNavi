from django.db import models
from django.contrib.auth.models import AbstractUser

class Household(models.Model):
    """
    Household（世帯）テーブル
    - どの世帯のデータか（在庫・メモ等）をひも付けるための「土台」
    """
    name = models.CharField("世帯名", max_length=50)
    created_at = models.DateTimeField("作成日時", auto_now_add=True)

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
        on_delete=models.SET_NULL, #世帯が消えてもユーザーを消さない
        null=True,
        blank=True, #まずは未所属でもOKにして進める
        related_name="users",
        verbose_name="所属世帯",
    )
