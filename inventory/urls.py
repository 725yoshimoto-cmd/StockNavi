from django.urls import path
from . import views

urlpatterns = [
    # トップページにポートフォリオ画面を表示
    path("", views.PortfolioView.as_view(), name="portfolio"),

    # household未設定の案内ページ
    path("household-required/", views.HouseholdRequiredView.as_view(), name="household_required"),

    # 新規登録ページ
    path("signup/", views.SignupView.as_view(), name="signup"),

    # 在庫一覧ページ（ログイン必須）
    path("inventory/", views.InventoryListView.as_view(), name="inventory_list"),
    
    # 在庫追加ページ
    path("inventory/add/", views.InventoryCreateView.as_view(), name="inventory_add"),
    
    # 在庫編集ページ
    path("inventory/<int:pk>/edit/", views.InventoryUpdateView.as_view(), name="inventory_edit"),
    
    # 在庫削除ページ
    path("inventory/<int:pk>/delete/", views.InventoryDeleteView.as_view(), name="inventory_delete"),
]


