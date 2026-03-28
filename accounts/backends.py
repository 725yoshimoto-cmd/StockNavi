from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


# CustomUser を直接 import せず、
# Django に「今使っているユーザーモデル」を聞く書き方にしている
# → 後で見返したときも、Djangoっぽい安全な書き方として学びやすい
UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """
    メールアドレス + パスワード でログインできるようにするための認証バックエンド

    役割：
    1. 入力されたメールアドレスを受け取る
    2. そのメールアドレスを持つユーザーを探す
    3. パスワードが一致したらログイン成功にする

    ポイント：
    - username という引数名でも値が入ってくることがあるため、
      email = kwargs.get("email", username) という形で両対応にしている
    - Django標準の ModelBackend を継承しているので、
      「有効ユーザーかどうか」などの標準動作も活かせる
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        ログイン時に呼ばれるメイン処理

        引数の意味：
        - request: リクエスト情報
        - username: Django標準フォームから来ることが多い入力値
        - password: 入力されたパスワード
        - kwargs: その他の追加情報

        今回は username の中に「メールアドレス」が入ってくる想定
        """

        # Django標準のログインフォームでは username という名前で値が来ることが多い
        # ただし将来的に email という名前で渡すことも考えて、両方に対応しておく
        email = kwargs.get("email", username)

        # メールアドレスかパスワードが空なら認証しない
        if email is None or password is None:
            return None

        try:
            # 大文字小文字の違いを気にせずメールアドレスでユーザー検索
            # 例：TEST@example.com と test@example.com を同じように扱いやすくする
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            # そのメールアドレスのユーザーがいなければ失敗
            return None
        except UserModel.MultipleObjectsReturned:
            # 同じメールアドレスのユーザーが複数いると、どの人か決められない
            # 本来はDB上で email を一意にしたいが、
            # まずは安全側で「認証失敗」にしておく
            return None

        # パスワード確認
        # check_password() は Django が安全にハッシュ比較してくれる
        if user.check_password(password):
            # self.user_can_authenticate(user) は
            # is_active=False のユーザーなどを弾く Django 標準チェック
            if self.user_can_authenticate(user):
                return user

        # パスワード不一致なら失敗
        return None