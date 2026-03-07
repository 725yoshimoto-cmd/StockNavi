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

    # 在庫（inventory）一覧、追加、詳細、編集、削除、複製
    path("", views.InventoryListView.as_view(), name="inventory_list"),
    path("add/", views.InventoryCreateView.as_view(), name="inventory_add"),
    path("<int:pk>/", views.InventoryDetailView.as_view(), name="inventory_detail"),
    path("<int:pk>/edit/", views.InventoryUpdateView.as_view(), name="inventory_edit"),
    path("<int:pk>/delete/", views.InventoryDeleteView.as_view(), name="inventory_delete"),
    path("<int:pk>/duplicate/", views.InventoryDuplicateView.as_view(), name="inventory_duplicate"),
  
    # 一括削除
    path("bulk-delete/", views.InventoryBulkDeleteView.as_view(), name="inventory_bulk_delete"),
    path("bulk-delete/execute/", views.InventoryBulkDeleteExecuteView.as_view(), name="inventory_bulk_delete_execute"),

    # 一括複製
    path("bulk-duplicate/", views.InventoryBulkDuplicateView.as_view(), name="inventory_bulk_duplicate"),
    path("bulk-duplicate/execute/", views.InventoryBulkDuplicateExecuteView.as_view(), name="inventory_bulk_duplicate_execute"),    
    
    # 過去一覧（History）
    path("history/", views.InventoryHistoryListView.as_view(), name="inventory_history"),
    path(
    "history/select/",
    views.InventoryHistorySelectView.as_view(),
    name="inventory_history_select"
    ),
    path(
        "history/delete/",
        views.InventoryHistoryDeleteView.as_view(),
        name="inventory_history_delete"
    ),
    path(
        "history/duplicate/<int:pk>/",
        views.InventoryHistoryDuplicateView.as_view(),
        name="inventory_history_duplicate"
    ),
    
    # バランス確認（Balance）
    path("balance/", views.BalanceView.as_view(), name="balance"),
    
    # 分類（Category）
    path("category/", views.CategoryListView.as_view(), name="category_list"),
    path("category/add/", views.CategoryCreateView.as_view(), name="category_add"),
    path("category/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("category/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),

    # 保管場所（StorageLocation）
    path("storage-location/", views.StorageLocationListView.as_view(), name="storage_location_list"),
    path("storage-location/add/", views.StorageLocationCreateView.as_view(), name="storage_location_add"),
    path("storage-location/<int:pk>/edit/", views.StorageLocationUpdateView.as_view(), name="storage_location_edit"),
    path("storage-location/<int:pk>/delete/", views.StorageLocationDeleteView.as_view(), name="storage_location_delete"), 
   
    # 設定（タブ統合）
    path("settings/", views.SettingsTabsView.as_view(), name="settings_tabs"),

    # 設定互換URL
    path(
        "settings/category-goal/",
        views.SettingsCategoryGoalView.as_view(),
        name="settings_category_goal",
    ),
    
    # メモ機能
    path("memo/", views.MemoListView.as_view(), name="memo_list"),
    path("memo/add/", views.MemoCreateView.as_view(), name="memo_add"),
    path("memo/<int:pk>/edit/", views.MemoUpdateView.as_view(), name="memo_edit"),
    path("memo/<int:pk>/delete/", views.MemoDeleteView.as_view(), name="memo_delete"),
    path("memo/bulk-delete/", views.MemoBulkDeleteView.as_view(), name="memo_bulk_delete"),
    
    # ----------------------------
    # 招待機能（InviteToken）
    # ----------------------------
    path("invite/", views.InviteCreateView.as_view(), name="invite_create"),
    path("invite/<uuid:token>/", views.InviteAcceptView.as_view(), name="invite_accept"),
    
    # フェーズ3：招待トークン一覧
    path("invite/list/", views.InviteTokenListView.as_view(), name="invite_token_list"),

    # 任意：使用済み/期限切れのみ削除
    path(
        "invite/token/<int:pk>/delete/",
        views.InviteTokenDeleteView.as_view(),
        name="invite_token_delete",
    ),
]


