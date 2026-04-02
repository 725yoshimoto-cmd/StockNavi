from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
from .views import SignUpView, CustomLoginView, CustomPasswordResetRequestView

app_name = "accounts"

urlpatterns = [
    # ----------------------------
    # ログイン / ログアウト
    # ----------------------------
    # ここが今回の最重要
    # django.contrib.auth.urls の標準 login ではなく、
    # 自作した CustomLoginView を先に定義して使う
    path("login/", CustomLoginView.as_view(), name="login"),

    # ログアウトは Django標準のままでOK
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path("mypage/", views.MyPageView.as_view(), name="mypage"),
    path("alert_setting/", views.AlertSettingView.as_view(), name="alert_setting"),
    path("members/", views.MemberListView.as_view(), name="member_list"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("signup/<uuid:token>/", SignUpView.as_view(), name="signup_with_token"),

    # ----------------------------
    # パスワード再設定
    # ----------------------------
    # メールアドレス入力画面
    path(
        "password-reset/",
        CustomPasswordResetRequestView.as_view(),
        name="password_reset"
    ),

    # メール送信完了画面
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),

    # メール内リンクから開く、新しいパスワード入力画面
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),

    # 再設定完了画面
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]