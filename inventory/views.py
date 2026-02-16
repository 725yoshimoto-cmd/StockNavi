# ----------------------------
# Django標準の便利機能の読み込み
# ----------------------------

from django.shortcuts import render
from django.http import HttpResponse

# ログイン必須にするためのMixin
from django.contrib.auth.mixins import LoginRequiredMixin

# クラスベースビュー
from django.views.generic import ListView, CreateView, TemplateView
# ListView：一覧表示
# CreateView：新規作成（ユーザー登録）
# TemplateView：表示だけのページ（ポートフォリオ）

# Django標準ユーザー登録フォーム
from django.contrib.auth.forms import UserCreationForm

# 成功後のリダイレクト用
from django.urls import reverse_lazy

# 自分のアプリのモデル
from .models import InventoryItem



# ----------------------------
# 仮トップページ（今後は使わなくなる可能性あり）
# ----------------------------
def index(request):
    """
    関数ベースビュー（Function Based View）
    文字をそのまま返すだけの簡易ページ
    """
    return HttpResponse("StockNavi Top Page")


# ----------------------------
# ポートフォリオ画面（ログイン前の玄関ページ）
# ----------------------------
class PortfolioView(TemplateView):
    """
    TemplateView（テンプレート表示専用ビュー）

    データベースは使わず、
    HTMLファイルをそのまま表示するだけのページ。
    """
    template_name = "inventory/portfolio.html"


# ----------------------------
# 在庫一覧ページ（ログイン必須）
# ----------------------------
class InventoryListView(LoginRequiredMixin, ListView):
    """
    ListView（一覧表示専用ビュー）

    InventoryItemモデルのデータを取得し、
    list.htmlへ渡して表示する。

    LoginRequiredMixinを使うことで、
    ログインしていない人はアクセスできない。
    """
    model = InventoryItem
    template_name = "inventory/list.html"

# ----------------------------
# サインインページ
# ----------------------------
class SignupView(CreateView):
    """
    CreateView（新規作成ビュー）
    UserCreationForm（Django標準のユーザー作成フォーム）を使って
    ユーザー登録を行う。
    """
    form_class = UserCreationForm
    template_name = "inventory/signup.html"
    success_url = reverse_lazy("login") # 登録後はログインページへ
