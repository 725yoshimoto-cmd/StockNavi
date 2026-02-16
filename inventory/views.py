# ----------------------------
# Django標準の便利機能の読み込み
# ----------------------------
from django.shortcuts import render
from django.http import HttpResponse

# ログイン必須にするためのMixin
from django.contrib.auth.mixins import LoginRequiredMixin

# クラスベースビュー（一覧表示用）
from django.views.generic import ListView

# ★ 追加：表示専用ページ用
from django.views.generic import TemplateView

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
