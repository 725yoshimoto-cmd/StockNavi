# accounts/forms.py
# accountsアプリ専用のフォーム定義ファイル（User作成フォームなど）

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import AlertSetting

class CustomUserCreationForm(UserCreationForm):
    """
    CustomUser（AUTH_USER_MODEL）用のユーザー登録フォーム
    Django標準のUserCreationFormを、CustomUserに対応させたもの
    """
    class Meta:
        model = CustomUser
        # 最小構成：username + password
        fields = ("username",)

class AlertSettingForm(forms.ModelForm):
    """
    アラート設定の入力フォーム
    - ModelFormにすると、モデルとフォームのズレが起きにくい（無駄工数削減）
    """

    class Meta:
        model = AlertSetting
        fields = ("quantity_threshold", "expiry_days")
        # Bootstrap想定：クラスを付けて入力欄を整える（任意）
        widgets = {
            "quantity_threshold": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "expiry_days": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def clean_quantity_threshold(self):
        """
        個数アラート閾値のバリデーション
        - 例：9999みたいな現実的じゃない値は弾く
        """
        v = self.cleaned_data["quantity_threshold"]
        if v > 9999:
            raise forms.ValidationError("個数アラートは大きすぎます（9999以下にしてください）")
        return v

    def clean_expiry_days(self):
        """
        期限アラート日数のバリデーション
        """
        v = self.cleaned_data["expiry_days"]
        if v > 3650:
            raise forms.ValidationError("期限アラートは大きすぎます（3650日以下にしてください）")
        return v