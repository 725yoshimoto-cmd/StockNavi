from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Django標準ユーザーを拡張したカスタムユーザー。
    いまは最小構成（追加項目なし）で土台だけ作る。
    後で「表示名」「世帯（Household）」などの項目を追加していく想定。
    """
    pass
