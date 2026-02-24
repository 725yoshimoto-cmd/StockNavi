# stocknavi/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from inventory import views as inv_views  # ★PortfolioViewがinventory.viewsにある前提

urlpatterns = [
    path("admin/", admin.site.urls),

    # トップ（ポートフォリオ）
    path("", inv_views.PortfolioView.as_view(), name="portfolio"),  # ★/ に置く

    # 認証
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # アプリ本体（在庫）を /inventory/ 配下へ
    path("inventory/", include("inventory.urls")),
]