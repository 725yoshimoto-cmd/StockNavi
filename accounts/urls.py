# accounts/urls.py
from django.urls import path
from .views import AlertSettingView
from .views import MyPageView
from . import views

app_name = "accounts"

urlpatterns = [
    path("alert-setting/", views.AlertSettingView.as_view(), name="alert_setting"),
    path("mypage/", views.MyPageView.as_view(), name="mypage"),
]