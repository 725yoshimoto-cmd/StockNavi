# accounts/forms.py
# accountsアプリ専用のフォーム定義ファイル（User作成フォームなど）

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import CustomUser
from .models import AlertSetting

# 今使っているユーザーモデルを取得
User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    既存コードとの互換用のユーザー作成フォーム

    もともと inventory/views.py などで
    CustomUserCreationForm を import しているため残しておく
    """
    class Meta:
        model = CustomUser
        fields = ("username",)


class UserUpdateForm(forms.ModelForm):
    """
    ユーザー情報更新用フォーム

    accounts/views.py で import されているため必要
    """
    class Meta:
        model = User
        fields = ("username", "email")


class AlertSettingForm(forms.ModelForm):
    """
    アラート設定用フォーム

    このフォームでは、
    - 個数アラート
    - 期限アラート
    の2項目だけを扱う。

    household はログイン中ユーザーの世帯を View 側で決めるため、
    フォームには含めない。
    """

    class Meta:
        model = AlertSetting

        # AlertSetting モデルの本当のフィールド名に合わせる
        fields = ["quantity_threshold", "expiry_days"]

        # 入力欄を number にし、0未満を入れられないようにする
        widgets = {
            "quantity_threshold": forms.NumberInput(attrs={"min": 0}),
            "expiry_days": forms.NumberInput(attrs={"min": 0}),
        }

        # 画面に出す名前
        labels = {
            "quantity_threshold": "個数アラート",
            "expiry_days": "期限アラート",
        }

class SignUpForm(UserCreationForm):
    """
    サインアップ用フォーム

    目的
    ----
    Django標準の UserCreationForm には email が無いので、
    メールアドレス欄を追加する
    """

    email = forms.EmailField(
        required=True,
        label="メールアドレス"
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        """
        user に email をセットして保存する

        ※ household はここでは入れない
        ※ household は view 側で作成してからセットする
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

        return user