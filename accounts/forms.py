# accounts/forms.py
# accountsアプリ専用のフォーム定義ファイル（User作成フォームなど）

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    CustomUser（AUTH_USER_MODEL）用のユーザー登録フォーム
    Django標準のUserCreationFormを、CustomUserに対応させたもの
    """
    class Meta:
        model = CustomUser
        # 最小構成：username + password
        fields = ("username",)
