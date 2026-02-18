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

# 更新・削除用のクラスベースビュー
from django.views.generic import UpdateView, DeleteView

# 登録成功後の遷移先
from django.urls import reverse_lazy

# 未設定時に止める
from django.http import HttpResponseForbidden

#“世帯が未設定のユーザー” のガード（落ちないように）
from django.shortcuts import redirect
from django.contrib import messages

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
# 世帯未設定ユーザー向けの案内ページ
# ----------------------------
class HouseholdRequiredView(TemplateView):
    template_name = "inventory/household_required.html"

# ----------------------------
# 世帯チェック（dispatch）は「ログイン済み」になってから見る
# ----------------------------
class HouseholdRequiredMixin:
    """
    ログイン済みユーザーに household が設定されていることを必須にするMixin
    - 未ログインは LoginRequiredMixin に任せる（ここでは触らない）
    - household未設定なら、ループしないページへ逃がす
    """
    def dispatch(self, request, *args, **kwargs):
        # 未ログインなら household を見ない（AnonymousUser対策）
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # household未設定なら操作させない
        if not getattr(request.user, "household", None):
            messages.error(request, "世帯が未設定のため操作できません。管理者に連絡してください。")
            return redirect("/household-required/")  # ★ここに変更 # ★ /inventory/ にしない（ループ防止）

        return super().dispatch(request, *args, **kwargs)

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

# ----------------------------
# 在庫一覧画面（ログイン必須）
# ----------------------------
class InventoryListView(LoginRequiredMixin, HouseholdRequiredMixin, ListView):
    model = InventoryItem
    template_name = "inventory/list.html"

    def get_queryset(self):
        """
        ログインユーザーの household に紐づく在庫だけ表示する
        """
        return InventoryItem.objects.filter(household=self.request.user.household)

# ----------------------------
# 在庫を追加する画面（ログイン必須）
# ----------------------------
class InventoryCreateView(LoginRequiredMixin, HouseholdRequiredMixin, CreateView):
    model = InventoryItem
    fields = ["name", "quantity"]  # 入力させたい項目
    template_name = "inventory/item_form.html"
    success_url = "/inventory/"  # 追加後に在庫一覧へ戻る
 
    def form_valid(self, form):
        """
        保存前に household を自動セットする（ここが重要）
        household未設定だと NOT NULL 制約で落ちるので、先に止める
        """
        # ★ガード：ユーザーの household が未設定なら保存させない
        if not getattr(self.request.user, "household", None):
            return HttpResponseForbidden(
                "世帯（household）が未設定です。管理画面でユーザーに世帯を設定してください。"
            )

        # ★ここで household を詰める
        form.instance.household = self.request.user.household
        return super().form_valid(form)

# ----------------------------
# 在庫を編集する画面（ログイン必須）
# ----------------------------
class InventoryUpdateView(LoginRequiredMixin, HouseholdRequiredMixin, UpdateView):
    """
    在庫編集ページ
    ポイント：
    - get_queryset() で「自分の世帯の在庫だけ」に絞る（他世帯のURL直打ち対策）
    """
    model = InventoryItem
    fields = ["name", "quantity"]
    template_name = "inventory/item_form.html"
    success_url = "/inventory/"

    def get_queryset(self):
        """
        編集対象を「ログイン中ユーザーの世帯の在庫」に限定する
        """
        return InventoryItem.objects.filter(household=self.request.user.household)


# ----------------------------
# 在庫を削除する画面（ログイン必須）
# ----------------------------
class InventoryDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, DeleteView):
    # 自分の世帯の在庫だけ編集できる    - get_queryset() で
    model = InventoryItem
    template_name = "inventory/item_confirm_delete.html"
    success_url = "/inventory/"
    
    def get_queryset(self):
        # 自分の世帯の在庫だけ削除できる
        return InventoryItem.objects.filter(household=self.request.user.household)

