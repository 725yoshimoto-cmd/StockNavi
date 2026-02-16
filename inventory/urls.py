from django.urls import path
from . import views

urlpatterns = [
    # トップページにポートフォリオ画面を表示
    path("", views.PortfolioView.as_view(), name="portfolio"),

    # 在庫一覧ページ（ログイン必須）
    path("inventory/", views.InventoryListView.as_view(), name="inventory_list"),

    # ★追加：新規登録ページ
    path("signup/", views.SignupView.as_view(), name="signup"),
]
