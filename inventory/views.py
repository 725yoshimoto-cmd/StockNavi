# ----------------------------
# Django標準の便利機能の読み込み
# ----------------------------
from django.shortcuts import render
from django.http import HttpResponse

# ログイン必須にするためのMixin
from django.contrib.auth.mixins import LoginRequiredMixin

# 一覧表示用クラスベースビュー
from django.views.generic import ListView

# 表示専用ページ用（ポートフォリオ画面）
from django.views.generic import TemplateView

# 新規データ作成用クラスベースビュー（ユーザー登録で使用）
from django.views.generic import CreateView

# 登録成功後の遷移先
from django.urls import reverse_lazy

# ----------------------------
# ★ 追加：カスタムユーザー登録フォームを読み込む
# ----------------------------
# accountsアプリで作成したフォームを使用する
# ※ デフォルトのUserCreationFormは使わない
from accounts.forms import CustomUserCreationForm

# ----------------------------
# 自分のアプリのモデル
# ----------------------------
from .models import InventoryItem

# ----------------------------
# ポートフォリオトップ画面
# ----------------------------
class PortfolioView(TemplateView):
    template_name = "inventory/portfolio.html"


# ----------------------------
# 在庫一覧画面（ログイン必須）
# ----------------------------
class InventoryListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = "inventory/list.html"


# ----------------------------
# ユーザー新規登録画面
# ----------------------------
class SignupView(CreateView):
    """
    新規登録ページ（サインアップ）
    登録に成功したらログインページへ戻す
    """
    # ★ カスタムユーザー用フォームを使用する
    form_class = CustomUserCreationForm

    # 表示に使うテンプレート
    template_name = "registration/signup.html"

    # 登録成功後の遷移先（login のURL名へ）
    success_url = reverse_lazy("login")
