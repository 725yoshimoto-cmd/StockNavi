# accounts/forms.py
# accountsアプリ専用のフォーム定義ファイル（User作成フォームなど）

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
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


class EmailAuthenticationForm(AuthenticationForm):
    """
    ログイン用フォーム（メールアドレス + パスワード）

    目的
    ----
    Django標準の AuthenticationForm は username という名前の入力欄を使うが、
    今回のアプリでは「メールアドレスでログイン」に寄せたい。

    ポイント
    --------
    - フィールド名そのものは username のまま使う
      → Django標準の LoginView とつながりやすい
    - ただし画面上の見た目やラベルは「メールアドレス」に変える
    - 実際の認証は accounts/backends.py の EmailBackend が担当する
    """

    username = forms.EmailField(
        required=True,
        label="メールアドレス",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "メールアドレスを入力",
                "autocomplete": "email",
            }
        ),
        error_messages={
            "required": "メールアドレスを入力してください。",
            "invalid": "メールアドレスの形式で入力してください。",
        },
    )

    password = forms.CharField(
        required=True,
        label="パスワード",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "パスワードを入力",
                "autocomplete": "current-password",
            }
        ),
        error_messages={
            "required": "パスワードを入力してください。",
        },
    )

    # フォーム全体のエラーメッセージ
    # 例：メールアドレスかパスワードが違うとき
    error_messages = {
        "invalid_login": "メールアドレスまたはパスワードが正しくありません。",
        "inactive": "このアカウントは現在利用できません。",
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
        label="メールアドレス",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "メールアドレスを入力",
                "autocomplete": "email",
            }
        ),
        error_messages={
            "required": "メールアドレスを入力してください。",
            "invalid": "メールアドレスの形式で入力してください。",
        },
    )

    username = forms.CharField(
        required=True,
        label="ユーザー名",
        error_messages={
            "required": "ユーザー名を入力してください。",
        },
    )

    password1 = forms.CharField(
        required=True,
        label="パスワード",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "パスワードを入力",
                "autocomplete": "new-password",
            }
        ),
        error_messages={
            "required": "パスワードを入力してください。",
        },
    )

    password2 = forms.CharField(
        required=True,
        label="パスワード（確認用）",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "確認用パスワードを入力",
                "autocomplete": "new-password",
            }
        ),
        error_messages={
            "required": "確認用パスワードを入力してください。",
        },
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        """
        メールアドレスの重複チェック

        なぜ必要？
        ----------
        同じメールアドレスで複数登録できてしまうと、
        後で「メールアドレスでログイン」するときに
        どのユーザーか決められず困るため
        """
        email = self.cleaned_data.get("email")

        if not email:
            return email

        # 大文字小文字の違いを無視して重複チェック
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")

        return email

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