# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Household, Invitation
from .models import AlertSetting

# ----------------------------
# CustomUser 管理画面設定
# ----------------------------

# CustomUser（カスタムユーザー）を管理画面で扱う設定
class CustomUserAdmin(UserAdmin):
    """
    Django標準のUserAdminをベースに、
    自作フィールド（household）を管理画面に表示できるよう拡張する
    """

    # 一覧画面で household も見たい場合（任意）
    list_display = ("username", "email", "household", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "household")

    # 編集画面（Change user）に household を追加
    fieldsets = UserAdmin.fieldsets + (
        ("世帯情報", {"fields": ("household",)}),
    )

    # ユーザー新規追加画面（Add user）にも household を追加
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("世帯情報", {"fields": ("household",)}),
    )


# ----------------------------
# モデル登録（ここが重要）
# ----------------------------
# ユーザー（CustomUser）を管理画面に出す（UserAdmin付き）
admin.site.register(CustomUser, CustomUserAdmin)

# 世帯（Household）
admin.site.register(Household)

# 招待（Invitation）
admin.site.register(Invitation)

# ------------------------------
# AlertSetting を管理画面に登録
# ------------------------------
@admin.register(AlertSetting)
class AlertSettingAdmin(admin.ModelAdmin):
    """
    管理画面での表示設定をカスタマイズするクラス

    何をしている？
    → 管理画面で「どの項目を表示するか」
      「どの項目で検索できるか」を指定している
    """

    # 一覧画面に表示するカラム
    # household: どの世帯の設定か
    # quantity_threshold: 個数アラートの閾値
    # expiry_days: 期限アラートの閾値
    # updated_at: 最終更新日時
    list_display = (
        "household",
        "quantity_threshold",
        "expiry_days",
        "updated_at",
    )

    # 検索バーで検索できる項目
    # household__id は「世帯IDで検索できるようにする」という意味
    search_fields = (
        "household__id",
    )