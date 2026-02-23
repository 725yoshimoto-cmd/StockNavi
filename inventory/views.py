# ----------------------------
# Django標準の便利機能の読み込み
# ----------------------------
from django.shortcuts import render
from django.http import HttpResponse
from .models import InventoryItem, Memo, Category

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

# 在庫集計(合計・件数)
from django.db.models import Sum, Count

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
# メモ
# ----------------------------
from .models import InventoryItem, Memo

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
            return redirect("/no-household/")  # ★ここに変更 # ★ /inventory/ にしない（ループ防止）

        return super().dispatch(request, *args, **kwargs)

# ----------------------------
# 案内画面
# ----------------------------
class NoHouseholdView(TemplateView):
    template_name = "inventory/no_household.html"

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
    """
    在庫一覧ページ

    役割：
    - ログイン中ユーザーの世帯(household)に紐づく在庫だけを一覧表示する
    - 一覧の集計（件数・総数量）もテンプレートへ渡す
    """
    model = InventoryItem
    template_name = "inventory/list.html"

    def get_queryset(self):
        """
        ★表示対象を「ログインユーザーの世帯の在庫」に限定する
        - 他世帯の在庫が混ざる事故防止
        - URL直打ち・不正アクセス対策にもなる
        """
        return InventoryItem.objects.filter(household=self.request.user.household)

    def get_context_data(self, **kwargs):
        """
        ★テンプレートに渡す追加データを作る
        - template_check：list.htmlが使われているか確認するためのデバッグ印
        - total_items：在庫の件数
        - total_quantity：数量の合計
        """
        context = super().get_context_data(**kwargs)

        # --- デバッグ用：list.htmlが使われているか確認 ---
        context["template_check"] = "LIST_TEMPLATE_IS_WORKING"

        # --- 集計用：このページに表示している在庫データの合計 ---
        queryset = self.get_queryset()
        context["total_items"] = queryset.count()
        context["total_quantity"] = queryset.aggregate(total=Sum("quantity"))["total"] or 0

        return context
        
# ----------------------------
# 在庫を追加する画面（ログイン必須）
# ----------------------------
class InventoryCreateView(LoginRequiredMixin, HouseholdRequiredMixin, CreateView):
    """
    - form_valid() で InventoryItem.household を自動セットする（世帯ひも付け漏れ防止）
    - get_form() で Category の候補を「自分の世帯だけ」に絞る（他世帯カテゴリ混入防止）
    """
    model = InventoryItem
    # 入力させたい項目だけ表示（categoryはプルダウンになる）
    fields = ["category", "name", "quantity"]  # 入力させたい項目
    template_name = "inventory/item_form.html"
    
    # success_url は reverse_lazy 推奨（URL変更にも強い）
    success_url = reverse_lazy("inventory_list")  # ← urls.py の name に合わせてね

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

def get_form(self, form_class=None):
    """
    ★追加時もカテゴリ候補を自分の世帯だけに絞る
    - これをしないと、他世帯のカテゴリがプルダウンに出てしまう事故が起きる
    """
    form = super().get_form(form_class)
    form.fields["category"].queryset = Category.objects.filter(
        household=self.request.user.household
    )
    return form
    
# ----------------------------
# 在庫を編集する画面（ログイン必須）
# ----------------------------
class InventoryUpdateView(LoginRequiredMixin, HouseholdRequiredMixin, UpdateView):
    """
    - 他世帯のURL直打ち対策：get_queryset()で絞る
    - household未設定ユーザー対策：dispatch()で早期ガード（安全）
    """
    model = InventoryItem
    fields = ["category", "name", "quantity"]
    template_name = "inventory/item_form.html"
    success_url = "/inventory/"

    def get_queryset(self):
        """
        編集対象を「ログイン中ユーザーの世帯の在庫」に限定する
        """
        return InventoryItem.objects.filter(household=self.request.user.household)
    
    def get_form(self, form_class=None):
        """
        ★編集時もカテゴリ候補を自分の世帯だけに絞る
        """
        form = super().get_form(form_class)
        form.fields["category"].queryset = Category.objects.filter(
            household=self.request.user.household
        )
        return form

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

# ----------------------------
# メモ一覧（ログイン必須）
# ----------------------------
class MemoListView(LoginRequiredMixin, HouseholdRequiredMixin, ListView):
    model = Memo
    template_name = "memo/list.html"

    def get_queryset(self):
        # 自分の世帯のメモだけ表示
        return Memo.objects.filter(household=self.request.user.household).order_by("-created_at")


# ----------------------------
# メモ追加（ログイン必須）
# ----------------------------
class MemoCreateView(LoginRequiredMixin, HouseholdRequiredMixin, CreateView):
    model = Memo
    fields = ["title", "body"]
    template_name = "memo/form.html"
    success_url = "/memo/"

    def form_valid(self, form):
        # 保存前に household を自動セット
        form.instance.household = self.request.user.household
        return super().form_valid(form)


# ----------------------------
# メモ編集（ログイン必須）
# ----------------------------
class MemoUpdateView(LoginRequiredMixin, HouseholdRequiredMixin, UpdateView):
    model = Memo
    fields = ["title", "body"]
    template_name = "memo/form.html"
    success_url = "/memo/"

    def get_queryset(self):
        # 他世帯のメモは編集できない（pk直打ち対策）
        return Memo.objects.filter(household=self.request.user.household)


# ----------------------------
# メモ削除（ログイン必須）
# ----------------------------
class MemoDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, DeleteView):
    model = Memo
    template_name = "memo/confirm_delete.html"
    success_url = "/memo/"

    def get_queryset(self):
        # 他世帯のメモは削除できない（pk直打ち対策）
        return Memo.objects.filter(household=self.request.user.household)

# ----------------------------
# 分類（Category）一覧（ログイン必須）
# ----------------------------
class CategoryListView(LoginRequiredMixin, HouseholdRequiredMixin, ListView):
    model = Category
    template_name = "category/list.html"

    def get_queryset(self):
        return Category.objects.filter(household=self.request.user.household).order_by("name")


# ----------------------------
# 分類（Category）追加（ログイン必須）
# ----------------------------
class CategoryCreateView(LoginRequiredMixin, HouseholdRequiredMixin, CreateView):
    """
    カテゴリ追加ページ
    - household はユーザーに入力させず、自動でログインユーザーの世帯をセットする
    - 他世帯カテゴリを誤作成する事故を防ぐ
    """
    model = Category
    fields = ["name"]
    template_name = "category/form.html"
    success_url = "/category/"

    def form_valid(self, form):
        """
        保存前に household を自動セットする
        """
        form.instance.household = self.request.user.household
        return super().form_valid(form)


# ----------------------------
# 分類（Category）編集（ログイン必須）
# ----------------------------
class CategoryUpdateView(LoginRequiredMixin, HouseholdRequiredMixin, UpdateView):
    model = Category
    fields = ["name"]
    template_name = "category/form.html"
    success_url = "/category/"

    def get_queryset(self):
        return Category.objects.filter(household=self.request.user.household)


# ----------------------------
# 分類（Category）削除（ログイン必須）
# ----------------------------
class CategoryDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, DeleteView):
    model = Category
    template_name = "category/confirm_delete.html"
    success_url = "/category/"

    def get_queryset(self):
        return Category.objects.filter(household=self.request.user.household)