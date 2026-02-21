# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Household, Invitation

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

