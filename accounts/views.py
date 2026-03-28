# accounts/views.py

# Django基本
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin

# 追加：
# パスワード再設定URLを作るときに使う安全なトークン生成
from django.contrib.auth.tokens import default_token_generator

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

# 追加：
# ユーザーIDをURLに安全に入れるために使う
from django.utils.http import urlsafe_base64_encode

# 追加：
# ユーザーIDをバイト列に変換するために使う
from django.utils.encoding import force_bytes

from django.utils import timezone
from django.views import View

# 既存の TemplateView / CreateView に加えて、
# 追加で FormView を使う
from django.views.generic import TemplateView, CreateView, FormView

from django.db import transaction

# 追加：
# パスワード再設定メールを実際に送るために使う
from django.core.mail import send_mail, get_connection

# 自アプリ
from .forms import (
    AlertSettingForm,
    UserUpdateForm,
    SignUpForm,
    EmailAuthenticationForm,

    # 追加：
    # メールアドレス入力だけのパスワード再設定用フォーム
    PasswordResetRequestForm,
)
from .models import AlertSetting, Household

# 既存：世帯必須のMixin（プロジェクトにあるやつ）
from inventory.mixins import HouseholdRequiredMixin
from inventory.models import InviteToken   # ← InviteToken の場所に合わせて修正

User = get_user_model()

class CustomLoginView(LoginView):
    """
    ログイン画面

    目的
    ----
    Django標準のログイン処理に、
    自作した EmailAuthenticationForm をつなぐ。

    これにより、
    - 画面では「メールアドレス」「パスワード」と表示できる
    - 認証は accounts/backends.py の EmailBackend を使える
    """

    template_name = "registration/login.html"
    authentication_form = EmailAuthenticationForm

    def get_success_url(self):
        """
        ログイン成功後の遷移先
        settings.py の LOGIN_REDIRECT_URL を使ってもよいが、
        ここで明示しておくと後で見返したとき分かりやすい
        """
        return reverse_lazy("inventory:inventory_list")
    
class MemberListView(LoginRequiredMixin, HouseholdRequiredMixin, TemplateView):
    template_name = "accounts/member_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        household = self.request.user.household
        members = User.objects.filter(household=household).order_by("id")

        context["household"] = household
        context["members"] = members
        return context
    
class AlertSettingView(LoginRequiredMixin, HouseholdRequiredMixin, View):
    """
    アラート設定画面
    - GET : フォーム表示
    - POST: 保存して JSON を返す（画面遷移なしでトースト表示させるため）
    """

    template_name = "accounts/alert_setting.html"

    def _get_setting(self):
        """
        世帯ごとのアラート設定を取得（無ければ作成）
        - ここを共通化すると GET/POST 両方で使えてミスが減る
        """
        household = self.request.user.household
        obj, _ = AlertSetting.objects.get_or_create(household=household)
        return obj

    def get(self, request, *args, **kwargs):
        """
        画面表示
        """
        setting = self._get_setting()
        form = AlertSettingForm(instance=setting)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        """
        保存（AJAX想定）
        """
        setting = self._get_setting()
        form = AlertSettingForm(request.POST, instance=setting)

        # バリデーションエラーならエラー内容をJSONで返す
        if not form.is_valid():
            return JsonResponse(
                {"ok": False, "errors": form.errors},
                status=400
            )

        # 保存
        form.save()
        
        # 成功レスポンス（トースト表示用）
        return JsonResponse({"ok": True, "message": "アラート設定を保存しました"})

# ----------------------------
# ★ マイページ
# ----------------------------
class MyPageView(LoginRequiredMixin, TemplateView):
    """
    マイページ
    - 世帯情報表示
    - ニックネーム/メール更新（最短：username をニックネーム扱い）
    - ログアウト導線
    """
    template_name = "accounts/mypage.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = UserUpdateForm(instance=self.request.user)
        return ctx

    def post(self, request, *args, **kwargs):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "保存しました。")
            return redirect("accounts:mypage")
        # バリデーションエラー時は同じ画面にform付きで戻す
        ctx = self.get_context_data(**kwargs)
        ctx["form"] = form
        return self.render_to_response(ctx)

# ----------------------------
# ★ サインアップ（アカウント登録）
# ----------------------------
class SignUpView(CreateView):
    """
    新規登録画面

    通常登録
    - Householdを新規作成
    - userをその世帯に所属させる

    招待URL登録
    - InviteTokenが有効なら
    - その世帯に参加する
    """
    template_name = "accounts/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("inventory:inventory_list")

    @transaction.atomic
    def form_valid(self, form):

        # まだ保存しないuser
        user = form.save(commit=False)

        # URLの招待tokenを取得
        invite_token = self.kwargs.get("token")

        household = None

        # ----------------------------
        # 招待リンク経由
        # ----------------------------
        if invite_token:

            try:
                token_obj = InviteToken.objects.get(token=invite_token)
            except InviteToken.DoesNotExist:
                messages.error(self.request, "招待リンクが正しくありません。")
                return self.form_invalid(form)

            # 有効チェック
            if not token_obj.is_valid():
                messages.error(self.request, "招待リンクの期限が切れています。")
                return self.form_invalid(form)

            household = token_obj.household

            # 使用済みにする
            token_obj.is_used = True
            token_obj.save()

        # ----------------------------
        # 通常登録
        # ----------------------------
        else:

            household = Household.objects.create(
                name=f"{user.username}さんの世帯"
            )

        # userに世帯をセット
        user.household = household
        user.save()

        # ログイン
        login(self.request, user)

        messages.success(self.request, "アカウント登録が完了しました。")

        return redirect(self.success_url)
    
class CustomPasswordResetRequestView(FormView):
    """
    パスワード再設定メール送信画面

    目的
    ----
    Django標準の PasswordResetView を避けて、
    自前で再設定URLを作ってメール送信する。

    理由
    ----
    今回は SMTP 自体は動いているため、
    再設定メール送信処理をシンプルにして確実に通すため。
    """
    template_name = "accounts/password_reset_form.html"
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy("accounts:password_reset_done")

    def form_valid(self, form):
        """
        メールアドレスが存在するユーザーに対してだけ
        パスワード再設定URLを送る
        """
        email = form.cleaned_data["email"]

        # 大文字小文字を無視してメール一致ユーザーを探す
        # is_active=True のみ対象にする
        users = User.objects.filter(email__iexact=email, is_active=True)

        for user in users:
            # トークン発行
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # 本番URLを組み立てる
            reset_url = self.request.build_absolute_uri(
                reverse_lazy(
                    "accounts:password_reset_confirm",
                    kwargs={"uidb64": uid, "token": token},
                )
            )

            # 件名
            subject = "【StockNavi】パスワード再設定"

            # 本文
            message = (
                "StockNavi パスワード再設定\n\n"
                "以下のURLからパスワードを変更してください\n\n"
                f"{reset_url}\n"
            )

            # =========================
            # Gmail SMTP 接続をここで明示する
            # 理由：
            # - shell テストで成功した条件を、そのままWeb画面送信にも使いたい
            # - settings.py / WSGI の読み込み差異を避けるため
            # =========================
            connection = get_connection(
                backend="django.core.mail.backends.smtp.EmailBackend",
                host="smtp.gmail.com",
                port=587,
                username=os.environ.get("EMAIL_HOST_USER"),
                password=os.environ.get("EMAIL_HOST_PASSWORD"),
                use_tls=True,
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=os.environ.get("EMAIL_HOST_USER"),
                recipient_list=[user.email],
                fail_silently=False,
                connection=connection,
            )

        # メールアドレスが存在しなくても、画面上は同じ完了画面へ
        # （セキュリティ上、存在有無を見せないため）
        return super().form_valid(form)