# stocknavi/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/accounts/login/", permanent=False)),
    path("admin/", admin.site.urls),
    path("inventory/", include("inventory.urls")),

    # ★標準ログイン/ログアウト
    path("accounts/", include("django.contrib.auth.urls")),
    # ★mypageなど自作
    path("accounts/", include("accounts.urls")),
]