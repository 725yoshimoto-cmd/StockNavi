# accounts/urls.py
from django.urls import path
from .views import AlertSettingView

app_name = "accounts"

urlpatterns = [
    path("alert-setting/", AlertSettingView.as_view(), name="alert_setting"),
]