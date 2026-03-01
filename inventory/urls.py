from django.urls import path
from . import views


app_name = "inventory"

urlpatterns = [
    # household未設定の案内ページ
    path("household-required/", views.HouseholdRequiredView.as_view(), name="household_required"),

    # 新規登録ページ
    path("signup/", views.SignupView.as_view(), name="signup"),

    # 案内ページ
    path("no-household/", views.NoHouseholdView.as_view(), name="no_household"),

    # ----------------------------
    # 在庫（inventory）一覧、追加、詳細、編集、削除、複製
    # ----------------------------
    path("", views.InventoryListView.as_view(), name="inventory_list"),
    path("add/", views.InventoryCreateView.as_view(), name="inventory_add"),

    # ★追加：詳細
    path("<int:pk>/", views.InventoryDetailView.as_view(), name="inventory_detail"),

    path("<int:pk>/edit/", views.InventoryUpdateView.as_view(), name="inventory_edit"),
    path("<int:pk>/delete/", views.InventoryDeleteView.as_view(), name="inventory_delete"),

    # ★追加：複製
    path("<int:pk>/duplicate/", views.InventoryDuplicateView.as_view(), name="inventory_duplicate"),


    # ----------------------------
    # 分類（Category）
    # ----------------------------
    path("category/", views.CategoryListView.as_view(), name="category_list"),
    path("category/add/", views.CategoryCreateView.as_view(), name="category_add"),
    path("category/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("category/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),

    # ----------------------------
    # 保管場所（StorageLocation）
    # ----------------------------
    path("storage-location/", views.StorageLocationListView.as_view(), name="storage_location_list"),
    path("storage-location/add/", views.StorageLocationCreateView.as_view(), name="storage_location_add"),
    path("storage-location/<int:pk>/edit/", views.StorageLocationUpdateView.as_view(), name="storage_location_edit"),
    path("storage-location/<int:pk>/delete/", views.StorageLocationDeleteView.as_view(), name="storage_location_delete"), 
   
    # ----------------------------
    # バランス確認（Balance）
    # ----------------------------
    path("balance/", views.BalanceView.as_view(), name="balance"),

    # ----------------------------
    # メモ機能
    # ----------------------------
    path("memo/", views.MemoListView.as_view(), name="memo_list"),
    path("memo/add/", views.MemoCreateView.as_view(), name="memo_add"),
    path("memo/<int:pk>/edit/", views.MemoUpdateView.as_view(), name="memo_edit"),
    path("memo/<int:pk>/delete/", views.MemoDeleteView.as_view(), name="memo_delete"),

    # ----------------------------
    # 設定一覧
    # ----------------------------
    path("settings/", views.SettingsListView.as_view(), name="settings"),
]


