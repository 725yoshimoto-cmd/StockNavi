from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
from .views import SignUpView

app_name = "accounts"

urlpatterns = [
    path("mypage/", views.MyPageView.as_view(), name="mypage"),
    path("alert_setting/", views.AlertSettingView.as_view(), name="alert_setting"),
    path("members/", views.MemberListView.as_view(), name="member_list"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("signup/<uuid:token>/", SignUpView.as_view(), name="signup_with_token"),
    
    # ----------------------------
    # パスワード再設定
    # ----------------------------
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]