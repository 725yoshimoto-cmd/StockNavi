# stocknavi/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # inventory
    path("inventory/", include("inventory.urls")),

    # accounts（あなたの alert_setting を残す）
    path("accounts/", include("accounts.urls")),

    # ----------------------------
    # ★追加：Django標準の認証URL
    # ----------------------------
    # /accounts/login/ , /accounts/logout/ などが使えるようになる
    path("accounts/", include("django.contrib.auth.urls")),
]