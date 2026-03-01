# Django標準の便利機能の読み込み
from django.shortcuts import render
from django.http import HttpResponse

# 自分のアプリのモデル
from .models import InventoryItem, Category, StorageLocation, Memo
from .mixins import HouseholdRequiredMixin  # 既に使ってるやつ

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

# 在庫詳細用のクラスベースビュー
from django.views.generic import DetailView

# 登録成功後の遷移先
from django.urls import reverse_lazy

# URL名（name="no_household"）からURL文字列を作るために使う
from django.urls import reverse

#“世帯が未設定のユーザー” のガード（落ちないように）
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

# 在庫集計(合計・件数)
from django.db.models import Sum, Count

# 「カテゴリ一覧を渡す」と「GETで絞る」
from django.utils.http import urlencode  # なくてもOKだが後で便利

# バランス確認
from .services.balance import calc_category_amounts

# ★ 追加：今日の日付（タイムゾーン安全）を扱うため
from django.utils import timezone

# ★ 追加：カスタムユーザー登録フォームを読み込む
# accountsアプリで作成したフォームを使用する
# ※ デフォルトのUserCreationFormは使わない
from accounts.forms import CustomUserCreationForm

# ★ 追加：世帯ごとの閾値（AlertSetting）を取得する
# 「世帯で1つだけ」の設定値を在庫一覧の判定基準として使う
from accounts.models import AlertSetting

# ★追加：在庫フォーム（期限入力対応）
from .forms import InventoryItemForm

# アラート判定
from datetime import date, timedelta

# 複製
from django.views import View

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
    household 未設定ユーザーを弾くMixin

    目的：
    - request.user.household が未設定のユーザーが各機能ページに来た場合、
      DB検索や保存処理に入る前に案内ページへ誘導する（エラー画面を出さない）
    """

    def dispatch(self, request, *args, **kwargs):
        """
        dispatch は CBV の入口（GET/POST 共通で最初に通る）
        """
        # ★household が未設定なら案内ページへ
        if not getattr(request.user, "household", None):
            return redirect(reverse("no_household"))

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
    在庫一覧ページ（スマホ前提）

    このクラスの役割：
    ① ログイン中ユーザーの「世帯」に属する在庫だけ表示する
       → 他世帯のデータ混入を防ぐ（セキュリティ）
    ② GETパラメータ (?category=, ?storage=) があれば絞り込み
    ③ 各在庫に「アラート判定結果（赤/青）」と「残日数」を付与して
       テンプレートに渡す

    ※ データベースには保存せず、
       表示用の一時的な属性を item に追加している
    """
    model = InventoryItem
    template_name = "inventory/list.html"
    context_object_name = "items"   # テンプレ側で {% for item in items %} と書ける

    # ① 一覧の取得（データ取得部分）
    def get_queryset(self):
        """
        在庫データを取得する部分。
        ここでは「どの在庫を表示するか」だけを決める。
        """
        # ログイン中ユーザーの世帯を取得
        household = self.request.user.household
                
        # 世帯でフィルタ（他世帯混入防止）
        qs = (
            InventoryItem.objects
            .filter(household=household)
            .select_related("storage_location", "category")  # パフォーマンス最適化
        )


        # GETパラメータによる絞り込み（分類）
        category_id = self.request.GET.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        # GETパラメータによる絞り込み（保管場所）
        storage_id = self.request.GET.get("storage")
        if storage_id:
            qs = qs.filter(storage_location_id=storage_id)

        return qs

    def get_context_data(self, **kwargs):
        """
        テンプレート表示用の追加情報を作る場所。
        - 絞り込みフォームの選択肢（categories, storages）
        - 選択状態（selected_category, selected_storage）
        - 集計（total_items, total_quantity）
        - アラート判定（days_left, is_red, is_blue）
        を context に詰める。
        """
        # まず親クラスの context を取得（これが超重要）
        context = super().get_context_data(**kwargs)

        household = self.request.user.household

        # 絞り込みフォーム用の選択肢
        context["categories"] = Category.objects.filter(household=household).order_by("name")
        context["storages"] = StorageLocation.objects.filter(household=household).order_by("name")

        # 今選ばれている値（テンプレの selected 用）
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_storage"] = self.request.GET.get("storage", "")

        # 一覧（items）を取り出す
        items = context.get("items") or context.get("object_list") or []

        # 集計（件数 / 数量合計）
        context["total_items"] = len(items)
        context["total_quantity"] = sum((i.quantity or 0) for i in items)

        # ---------- ここからアラート判定（設定連動） ----------
        today = timezone.localdate()

        # ✅ accounts.AlertSetting を世帯で1件取得。なければデフォルトで動かす
        DEFAULT_ALERT = {
            "quantity_threshold": 1,  # 青（個数）
            "expiry_days": 30,        # 青（期限日数）
        }

        setting = AlertSetting.objects.filter(household=household).first()
        if setting is None:
            alert = DEFAULT_ALERT
        else:
            alert = {
                "quantity_threshold": setting.quantity_threshold,
                "expiry_days": setting.expiry_days,
            }

        # 各在庫アイテムごとに判定を付与
        for item in items:
            # 残り日数を計算（expiry_date がない場合は None）
            if item.expiry_date is None:
                days_left = None
            else:
                days_left = (item.expiry_date - today).days

            item.days_left = days_left

            qty = item.quantity or 0  # None対策

            # ✅ 赤（固定）：在庫0 または 期限<=0日
            red_by_qty = (qty <= 0)
            red_by_days = (days_left is not None) and (days_left <= 0)
            item.is_red = red_by_qty or red_by_days

            # ✅ 青（設定連動）：赤じゃない場合だけ
            if not item.is_red:
                blue_by_qty = (qty <= alert["quantity_threshold"])
                blue_by_days = (days_left is not None) and (days_left <= alert["expiry_days"])
                item.is_blue = blue_by_qty or blue_by_days
            else:
                item.is_blue = False
                
            # テンプレ互換（既存テンプレは is_alert_* を参照しているため）
            item.is_alert_red = item.is_red
            item.is_alert_blue = item.is_blue

        return context
    
    def _get_alert_setting(self):
        """
        accounts.AlertSetting を世帯で1件取得。
        無ければデフォルトを返す（落ちないための保険）。
        """
        household = self.request.user.household
        setting = AlertSetting.objects.filter(household=household).first()

        if setting is None:
            return self.DEFAULT_ALERT

        return {
            "quantity_threshold": setting.quantity_threshold,
            "expiry_days": setting.expiry_days,
        }
    
        
        
# ----------------------------
# 在庫を追加する画面（ログイン必須）
# ----------------------------
class InventoryCreateView(LoginRequiredMixin, HouseholdRequiredMixin, CreateView):
    """
    - form_valid() で InventoryItem.household を自動セットする（世帯ひも付け漏れ防止）
    - get_form() で Category の候補を「自分の世帯だけ」に絞る（他世帯カテゴリ混入防止）
    """
    model = InventoryItem
    form_class = InventoryItemForm  # ★追加：この1行がポイント
    template_name = "inventory/item_form.html"

    
    # success_url は reverse_lazy 推奨（URL変更にも強い）
    success_url = reverse_lazy("inventory:inventory_list")  # ← urls.py の name に合わせてね

    def form_valid(self, form):
        """
        保存前に household を自動セットする（ここが重要）
        household未設定だと NOT NULL 制約で落ちるので、先に止める
        """
        # ★ガード：ユーザーの household が未設定なら保存させない
        if not getattr(self.request.user, "household", None):
            return redirect(reverse("inventory:no_household"))

        # ★ここで household を詰める
        form.instance.household = self.request.user.household
        
        return super().form_valid(form)

    def get_form(self, form_class=None):
        """
        ★追加時もカテゴリ候補を自分の世帯だけに絞る
        - これをしないと、他世帯のカテゴリがプルダウンに出てしまう事故が起きる
        """
        form = super().get_form(form_class)

        # カテゴリ候補を自世帯だけ
        form.fields["category"].queryset = Category.objects.filter(
            household=self.request.user.household
        )

        # 保管場所候補を自世帯だけ（★追加）
        form.fields["storage_location"].queryset = StorageLocation.objects.filter(
            household=self.request.user.household
        )

        return form

# ----------------------------
# 在庫を詳細画面（ログイン必須）
# ----------------------------
class InventoryDetailView(LoginRequiredMixin, HouseholdRequiredMixin, DetailView):
    model = InventoryItem
    template_name = "inventory/detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return InventoryItem.objects.filter(household=self.request.user.household)
    
# ----------------------------
# 在庫を編集する画面（ログイン必須）
# ----------------------------
class InventoryUpdateView(LoginRequiredMixin, HouseholdRequiredMixin, UpdateView):
    """
    - 他世帯のURL直打ち対策：get_queryset()で絞る
    - household未設定ユーザー対策：dispatch()で早期ガード（安全）
    """
    model = InventoryItem
    form_class = InventoryItemForm  # ★fieldsの代わりにこれ
    template_name = "inventory/item_form.html"
    success_url = reverse_lazy("inventory:inventory_list")

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

        form.fields["storage_location"].queryset = StorageLocation.objects.filter(
            household=self.request.user.household
        )

        return form

# ----------------------------
# 在庫を複製する画面（ログイン必須）
# ----------------------------
class InventoryDuplicateView(LoginRequiredMixin, HouseholdRequiredMixin, View):
    def post(self, request, pk):
        src = get_object_or_404(
            InventoryItem,
            pk=pk,
            household=request.user.household
        )

        new_item = InventoryItem.objects.create(
            household=src.household,
            category=src.category,
            storage_location=src.storage_location,
            name=src.name,
            quantity=src.quantity,
            content_amount=src.content_amount,
            expiry_date=src.expiry_date,
        )

        return redirect("inventory:inventory_edit", pk=new_item.pk) 


# ----------------------------
# 在庫を削除する画面（ログイン必須）
# ----------------------------
class InventoryDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, DeleteView):
    """
    在庫削除ページ

    ポイント：
    - テンプレート名を明示して衝突事故を防ぐ
    - get_queryset() で自分の世帯の在庫だけ削除できるようにする
    """
    model = InventoryItem
    template_name = "inventory/inventory_confirm_delete.html"  # ★スクショの期待名に合わせる
    success_url = reverse_lazy("inventory:inventory_list")

    def get_queryset(self):
        """削除対象を自分の世帯の在庫に限定"""
        return InventoryItem.objects.filter(household=self.request.user.household)

# ----------------------------
# バランス確認（Balance）（ログイン必須）
# ----------------------------
class BalanceView(LoginRequiredMixin, HouseholdRequiredMixin, TemplateView):
    template_name = "inventory/balance.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        household = self.request.user.household
        storage_id = self.request.GET.get("storage") or None

        rows, total = calc_category_amounts(household, storage_id)

        storages = StorageLocation.objects.filter(
            household=household
        ).order_by("name")

        ctx.update({
            "target_days": household.target_days,
            "storage_id": storage_id,
            "storages": storages,
            "rows": rows,
            "total": total,
        })
        return ctx

# ----------------------------
# 設定一覧（ログイン必須）
# ----------------------------
class SettingsListView(LoginRequiredMixin, HouseholdRequiredMixin, TemplateView):
    template_name = "inventory/settings/index.html"
                
# ----------------------------
# 分類（Category）一覧（ログイン必須）
# ----------------------------
class CategoryListView(LoginRequiredMixin, HouseholdRequiredMixin, ListView):
    """
    分類一覧ページ

    役割：
    - ログイン中ユーザーの世帯のカテゴリだけ一覧表示する
    """
    model = Category
    template_name = "category/list.html"  # ★必ずこれ

    def get_queryset(self):
        """
        ★表示対象を自分の世帯のカテゴリに限定する
        """
        return Category.objects.filter(
            household=self.request.user.household
        ).order_by("name")

# ----------------------------
# 分類（Category）追加（ログイン必須）
# ----------------------------
class CategoryCreateView(LoginRequiredMixin, HouseholdRequiredMixin, CreateView):
    model = Category
    """
    カテゴリ追加ページ
    - household はユーザーに入力させず、自動でログインユーザーの世帯をセットする
    - 他世帯カテゴリを誤作成する事故を防ぐ
    """
    
    # ----------------------------
    # フォームに表示する項目
    # - name: 分類名
    # - color: 分類カラー（今回追加）
    # ----------------------------
    fields = ["name", "color"]
    template_name = "category/form.html"
    success_url = reverse_lazy("inventory:category_list")

    def form_valid(self, form):
        """
        保存前に household を自動セットする（世帯ひも付け漏れ防止）
        """
        form.instance.household = self.request.user.household
        return super().form_valid(form)


# ----------------------------
# 分類（Category）編集（ログイン必須）
# ----------------------------
class CategoryUpdateView(LoginRequiredMixin, HouseholdRequiredMixin, UpdateView):
    model = Category
    fields = ["name", "color"]
    template_name = "category/form.html"
    success_url = reverse_lazy("inventory:category_list")

    def get_queryset(self):
        # 他世帯のカテゴリを編集できない
        return Category.objects.filter(household=self.request.user.household)


# ----------------------------
# 分類（Category）削除（ログイン必須）
# ----------------------------
class CategoryDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, DeleteView):
    """
    カテゴリ削除ページ

    ポイント：
    - テンプレート名の衝突を防ぐため、template_name を明示する
    - Category を削除すると、InventoryItem.category は SET_NULL で未分類になる
    """
    model = Category
    template_name = "category/category_confirm_delete.html"
    success_url = reverse_lazy("inventory:category_list")  # ★ここが重要

    def get_queryset(self):
        """
        ★削除対象を「自分の世帯のカテゴリ」に限定する
        """
        return Category.objects.filter(household=self.request.user.household)

# ----------------------------
# 保管場所（StorageLocation）
# ----------------------------
class StorageLocationListView(LoginRequiredMixin, HouseholdRequiredMixin, ListView):
    """
    自分の世帯（household）の保管場所だけを一覧表示する
    """
    model = StorageLocation
    template_name = "inventory/storage_location_list.html"  # ←命名事故を防ぐため明示
    context_object_name = "locations"

    def get_queryset(self):
        # ★事故防止：必ず世帯で絞る（他世帯混入・URL直打ち対策の基本）
        return StorageLocation.objects.filter(household=self.request.user.household).order_by("name")


class StorageLocationCreateView(LoginRequiredMixin, HouseholdRequiredMixin, CreateView):
    """
    保管場所を追加する
    - form_valid() で household を自動セット（世帯ひも付け漏れ防止）
    """
    model = StorageLocation
    fields = ["name"]  # 必要に応じて増やす（最短は name だけ）
    template_name = "inventory/storage_location_form.html"
    success_url = reverse_lazy("inventory:storage_location_list")

    def form_valid(self, form):
        # ★重要：保存前に世帯を自動セット（他世帯混入・NULL事故防止）
        form.instance.household = self.request.user.household
        return super().form_valid(form)


class StorageLocationUpdateView(LoginRequiredMixin, HouseholdRequiredMixin, UpdateView):
    """
    保管場所を編集する
    - get_queryset() で自世帯のみに限定（他世帯URL直打ち対策）
    """
    model = StorageLocation
    template_name = "inventory/storage_location_confirm_delete.html"
    success_url = reverse_lazy("inventory:storage_location_list")
    fields = ["name"]
    
    def get_queryset(self):
        # ★超重要：他世帯データ削除を防ぐ
        return StorageLocation.objects.filter(
            household=self.request.user.household
        )

class StorageLocationDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, DeleteView):
    """
    保管場所を削除する
    - get_queryset() で自世帯のみに限定（他世帯URL直打ち対策）
    """
    model = StorageLocation
    template_name = "inventory/storage_location_confirm_delete.html"
    success_url = reverse_lazy("inventory:storage_location_list")

    def get_queryset(self):
        # ★超重要：他世帯の削除を絶対させない
        return StorageLocation.objects.filter(household=self.request.user.household)

    
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
    success_url = reverse_lazy("inventory:memo_list")

    def form_valid(self, form):
        # household を自動セット（NOT NULL対策）
        form.instance.household = self.request.user.household
        # 作成者を自動セット
        form.instance.user = self.request.user
        return super().form_valid(form)

# ----------------------------
# メモ編集（ログイン必須）
# ----------------------------
class MemoUpdateView(LoginRequiredMixin, HouseholdRequiredMixin, UpdateView):
    model = Memo
    fields = ["title", "body"]
    template_name = "memo/form.html"
    success_url = reverse_lazy("inventory:memo_list")

    def get_queryset(self):
        # 他世帯のメモは編集できない（pk直打ち対策）
        return Memo.objects.filter(household=self.request.user.household)

    def form_valid(self, form):
        print("★ MemoCreateView.form_valid called")  # ←確認用（あとで消す）
        print("★ user household =", getattr(self.request.user, "household", None))
        form.instance.household = self.request.user.household
        form.instance.user = self.request.user
        return super().form_valid(form)

# ----------------------------
# メモ削除（ログイン必須）
# ----------------------------
class MemoDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, DeleteView):
    model = Memo
    template_name = "memo/confirm_delete.html"
    success_url = reverse_lazy("inventory:memo_list")

    def get_queryset(self):
        # 他世帯のメモは削除できない（pk直打ち対策）
        return Memo.objects.filter(household=self.request.user.household)

# ----------------------------
# マイページ
# ----------------------------
class MyPageView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/mypage.html"
