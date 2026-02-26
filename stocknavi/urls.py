# stocknavi/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # 既存（あなたのinventory配下が動いているので残す）
    path("inventory/", include("inventory.urls")),

    # ★追加（アラート設定用）
    path("accounts/", include("accounts.urls")),
]