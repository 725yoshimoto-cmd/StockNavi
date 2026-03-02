# Django標準の便利機能の読み込み
from django.shortcuts import render
from django.http import HttpResponse

# 自分のアプリのモデル
from .models import InventoryItem, Category, StorageLocation, Memo

# 自作：世帯必須Mixin（世帯が無いユーザーは弾くため）
from .mixins import HouseholdRequiredMixin

# Django：ログイン必須にするMixin（未ログインならログイン画面へ）
from django.contrib.auth.mixins import LoginRequiredMixin

# 一覧表示用クラスベースビュー
from django.views.generic import ListView

# Django：画面表示用のCBV（ポートフォリオ画面など）
from django.views.generic import TemplateView

# 新規データ作成用クラスベースビュー（ユーザー登録で使用）
from django.views.generic import CreateView

# 更新・削除用のクラスベースビュー
from django.views.generic import UpdateView, DeleteView

# 在庫詳細用のクラスベースビュー
from django.views.generic import DetailView

# Django：URL生成（登録成功後の遷移先や招待URLを作るため）
from django.urls import reverse_lazy

# URL名（name="no_household"）からURL文字列を作るために使う
from django.urls import reverse

#“世帯が未設定のユーザー” のガード（落ちないように）
from django.shortcuts import get_object_or_404, redirect

# Django：メッセージ表示（成功/失敗を画面に出す）
from django.contrib import messages

# 在庫集計(合計・件数)
from django.db.models import Sum, Count

# 在庫sort 処理
from django.db import models

# 「カテゴリ一覧を渡す」と「GETで絞る」
from django.utils.http import urlencode  # なくてもOKだが後で便利

# バランス確認
from .services.balance import calc_category_amounts

# Django：現在時刻（期限切れ判定やused_at更新に使う）
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

# 標準ライブラリ：日時計算（招待リンクの有効期限を作るため）
from datetime import timedelta
from django.conf import settings

# Django：DBの同時実行（同じ招待リンクを同時に使われても壊れないようにする）
from django.db import transaction

# DBにデータが無い場合、自動で404にしてくれる便利関数
from django.shortcuts import get_object_or_404

# 処理後にページを移動させる
from django.shortcuts import redirect

# 自作：招待トークンモデル
from .models import InviteToken

# 検索条件を OR で組みたいときに使う
from django.db.models import Q

# **Categoryモデル（分類）**を views.py から使うための import
from .models import Category

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
            return redirect(reverse("inventory:no_household"))

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
# 招待リンク発行画面（ログイン必須）
# ----------------------------
class InviteCreateView(LoginRequiredMixin, HouseholdRequiredMixin, TemplateView):
    """
    - household必須（HouseholdRequiredMixinで担保）
    """
    template_name = "inventory/invite/create.html"
    EXPIRE_HOURS = 24  # 有効期限（時間）

    def post(self, request, *args, **kwargs):
        # 念のためガード（500を避ける）
        if not getattr(request.user, "household", None):
            messages.error(request, "世帯が未設定のため招待リンクを発行できません。")
            return self.redirect_top()

        expires_at = timezone.now() + timedelta(hours=self.EXPIRE_HOURS)

        invite = InviteToken.objects.create(
            household=request.user.household,
            expires_at=expires_at,
        )

        invite_url = request.build_absolute_uri(
            reverse("inventory:invite_accept", kwargs={"token": str(invite.token)})
        )

        messages.success(request, "招待リンクを発行しました。")

        context = self.get_context_data(**kwargs)
        context["invite_url"] = invite_url
        context["expires_at"] = invite.expires_at
        return self.render_to_response(context)

    def redirect_top(self):
        # 既存のトップに合わせて変えてOK（inventory_list が無い場合は別名に）
        from django.shortcuts import redirect
        return redirect("inventory:inventory_list")


class InviteAcceptView(LoginRequiredMixin, TemplateView):
    """
    招待URLから参加
    - GET: 確認画面
    - POST: 参加確定（user.householdをセットし、tokenを使用済みに）
    """
    template_name = "inventory/invite/accept.html"

    def get_invite(self):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(InviteToken, token=self.kwargs["token"])

    def get(self, request, *args, **kwargs):
        invite = self.get_invite()

        # トークンが無効（使用済み or 期限切れ）
        if not invite.is_valid():
            messages.error(request, "この招待リンクは無効です。")
            return redirect("inventory:no_household")

        # すでに世帯を持っている場合は拒否
        if getattr(request.user, "household", None):
            messages.error(request, "すでに世帯に参加済みです。")
            return redirect("inventory:no_household")

        context = self.get_context_data(**kwargs)
        context["invite"] = invite
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            invite = self.get_invite()

            # ロック（同時押し対策）
            invite = InviteToken.objects.select_for_update().get(pk=invite.pk)

            # 再チェック
            if not invite.is_valid():
                messages.error(request, "この招待リンクは無効です。")
                return redirect("inventory:no_household")

            if getattr(request.user, "household", None):
                messages.error(request, "すでに世帯に参加済みです。")
                return redirect("inventory:no_household")

           
            # 参加処理
            request.user.household = invite.household
            request.user.save(update_fields=["household"])

            # 使用済みにする
            invite.is_used = True
            invite.save(update_fields=["is_used"])

        messages.success(request, "世帯に参加しました。")
        return redirect("inventory:inventory_list")
    
    
# ----------------------------
# 世帯内の招待トークン一覧（発行履歴）（ログイン必須）
# ----------------------------
# inventory/views.py

class InviteTokenListView(LoginRequiredMixin, HouseholdRequiredMixin, ListView):
    """
    - household必須（HouseholdRequiredMixin）
    - 自分の世帯のInviteTokenだけ表示
    - 未使用のものは招待URLを表示してコピーできるようにする
    """
    model = InviteToken
    template_name = "inventory/invite/invite_token_list.html"
    context_object_name = "tokens"

    def get_queryset(self):
        """
        一覧に出すデータを「自分の世帯」に限定する（世帯分離）
        """
        household = self.request.user.household
        return (
            InviteToken.objects.filter(household=household)
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        """
        テンプレで使う追加データを渡す
        - now: 期限切れ判定に使う
        """
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()

        # 各トークンに「invite_url」を後付けする（DB保存はしない）
        for t in context["tokens"]:
            t.invite_url = self.build_invite_url(t.token)

        return context

    def build_invite_url(self, token_uuid):
        """
        未使用トークンの招待URLを作る
        - reverseでパスを生成
        - build_absolute_uriでドメイン込みURLにする
        """
        path = reverse("inventory:invite_accept", kwargs={"token": token_uuid})
        return self.request.build_absolute_uri(path)


class InviteTokenDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, DeleteView):
    """
    任意（最小）：使用済み or 期限切れトークンだけ削除

    - 「未使用」は削除させない（事故防止）
    - 世帯分離：自分の世帯のものだけ削除可能
    """
    model = InviteToken
    template_name = "inventory/invite_token_confirm_delete.html"

    def get_queryset(self):
        """
        削除対象を
        - 自分の世帯
        - かつ「使用済み」or「期限切れ」
        に限定する
        """
        household = self.request.user.household
        now = timezone.now()
        return InviteToken.objects.filter(household=household).filter(
            # 使用済み or 期限切れ
            models.Q(is_used=True) | models.Q(expires_at__lt=now)
        )

    def dispatch(self, request, *args, **kwargs):
        """
        get_querysetで拾えない（=未使用など）場合は404になるが、
        ユーザーに優しいメッセージを出して一覧へ返す
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception:
            messages.error(request, "未使用の招待リンクは削除できません。")
            return redirect("inventory:invite_token_list")

    def get_success_url(self):
        messages.success(self.request, "招待トークンを削除しました。")
        return reverse("inventory:invite_token_list")


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

        # GETパラメータによる検索（商品名）
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        
        # GETパラメータによる並び替え
        sort = self.request.GET.get("sort", "")

        if sort == "expiry":
            # 期限が近い順（未設定は最後）
            qs = qs.order_by(models.F("expiry_date").asc(nulls_last=True), "name")

        elif sort == "quantity":
            # 数量が少ない順（同数は名前順）
            qs = qs.order_by("quantity", "name")

        elif sort == "name":
            # 名前順（50音順相当）
            qs = qs.order_by("name")

        else:
            # デフォルト（いままでの表示順を維持したいなら何もしない）
            pass
            
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
# 履歴一覧（HistoryListView）（ログイン必須）
# ----------------------------
class InventoryHistoryListView(LoginRequiredMixin, HouseholdRequiredMixin, ListView):
    model = InventoryItem
    template_name = "inventory/history_list.html"
    context_object_name = "items"

    def get_queryset(self):
        return (
            InventoryItem.objects
            .filter(household=self.request.user.household)
            .select_related("storage_location", "category")
            .order_by("-updated_at")
        )

# ----------------------------
# 在庫を一括削除（確認ページ表示）
# ----------------------------
class InventoryBulkDeleteView(LoginRequiredMixin, HouseholdRequiredMixin, View):
    template_name = "inventory/bulk_delete_confirm.html"

    def post(self, request, *args, **kwargs):
        selected_ids = request.POST.getlist("selected_ids")

        # ✅ 追加：チェック無しガード
        if not selected_ids:
            messages.warning(request, "削除する在庫を選択してください。")
            return redirect(reverse("inventory:inventory_list") + "?select_mode=1")

        items = InventoryItem.objects.filter(
            household=request.user.household,
            id__in=selected_ids
        )

        return render(request, "inventory/bulk_delete_confirm.html", {"items": items})

# ----------------------------
# 在庫を一括削除（実行）
# ----------------------------
class InventoryBulkDeleteExecuteView(LoginRequiredMixin, HouseholdRequiredMixin, View):

    def post(self, request):
        household = request.user.household
        ids = request.POST.getlist("selected_ids")

        if ids:
            InventoryItem.objects.filter(
                household=household,
                id__in=ids
            ).delete()

        return redirect("inventory:inventory_list")
    

# ----------------------------
# 在庫を一括削除（実行）
# ----------------------------
class InventoryBulkDeleteExecuteView(LoginRequiredMixin, HouseholdRequiredMixin, View):

    def post(self, request):
        household = request.user.household
        ids = request.POST.getlist("selected_ids")

        if ids:
            InventoryItem.objects.filter(
                household=household,
                id__in=ids
            ).delete()

        return redirect("inventory:inventory_list")

# ----------------------------
# 在庫を一括複製（確認ページ表示）
# ----------------------------
class InventoryBulkDuplicateView(LoginRequiredMixin, HouseholdRequiredMixin, View):
    template_name = "inventory/bulk_duplicate_confirm.html"

    def post(self, request, *args, **kwargs):
        selected_ids = request.POST.getlist("selected_ids")

        # ✅ 追加：チェック無しガード
        if not selected_ids:
            messages.warning(request, "複製する在庫を選択してください。")
            return redirect(reverse("inventory:inventory_list") + "?select_mode=1")

        items = InventoryItem.objects.filter(
            household=request.user.household,
            id__in=selected_ids
        )

        return render(request, "inventory/bulk_duplicate_confirm.html", {"items": items})
        
# ----------------------------
# 在庫を一括複製（実行）
# ----------------------------
class InventoryBulkDuplicateExecuteView(LoginRequiredMixin, HouseholdRequiredMixin, View):
    def post(self, request):
        household = request.user.household
        ids = request.POST.getlist("selected_ids")

        if not ids:
            return redirect("inventory:inventory_list")

        src_items = InventoryItem.objects.filter(household=household, id__in=ids)

        # 1件ずつコピー（安全＆分かりやすい）
        for src in src_items:
            InventoryItem.objects.create(
                household=src.household,
                category=src.category,
                storage_location=src.storage_location,
                name=src.name,
                quantity=src.quantity,
                content_amount=src.content_amount,
                expiry_date=src.expiry_date,
            )

        return redirect("inventory:inventory_list")
            
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
    fields = ["name", "goal_amount", "goal_unit", "color"]
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
    fields = ["name", "goal_amount", "goal_unit", "color"]
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
        qs = StorageLocation.objects.filter(household=self.request.user.household)

        q = (self.request.GET.get("q") or "").strip()
        sort = self.request.GET.get("sort") or "created"  # created / name

        if q:
            qs = qs.filter(name__icontains=q)

        if sort == "name":
            qs = qs.order_by("name", "id")
        else:
            qs = qs.order_by("id")  # 登録順（最短で安全）

        return qs
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        ctx["sort"] = self.request.GET.get("sort") or "created"
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action != "bulk_delete":
            messages.warning(request, "不正な操作です。")
            return redirect("inventory:storage_location_list")

        ids = request.POST.getlist("selected_ids")
        if not ids:
            messages.warning(request, "削除する保管場所を選択してください。")
            return redirect("inventory:storage_location_list")

        StorageLocation.objects.filter(
            household=request.user.household,
            id__in=ids,
        ).delete()

        messages.success(request, "保管場所を削除しました。")
        return redirect("inventory:storage_location_list")


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
    template_name = "inventory/storage_location_form.html"
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

class SettingsCategoryGoalView(LoginRequiredMixin, HouseholdRequiredMixin, View):
    """
    設定＞分類・目標設定（統合画面）
    - 目標備蓄日数（3/7/14/カスタム）を保存
    - 分類一覧（検索・並び替え）を表示
    - 選択削除（confirmでOK）を実行
    """
    template_name = "inventory/settings/category_goal.html"

    def get(self, request, *args, **kwargs):
        return self._render(request)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "save_target_days":
            self._save_target_days(request)
            messages.success(request, "変更が保存されました。")
            return redirect("inventory:settings_category_goal")

        if action == "bulk_delete_categories":
            self._bulk_delete_categories(request)
            return redirect("inventory:settings_category_goal")

        messages.warning(request, "不正な操作です。")
        return redirect("inventory:settings_category_goal")

    def _render(self, request):
        household = request.user.household

        q = (request.GET.get("q") or "").strip()
        order = request.GET.get("order") or "created"  # created=登録順, kana=50音順

        categories = Category.objects.filter(household=household)

        # 検索（nameフィールド前提）
        if q:
            categories = categories.filter(Q(name__icontains=q))

        # 並び替え
        if order == "kana":
            categories = categories.order_by("name", "id")
        else:
            categories = categories.order_by("id")  # 登録順の最短はid

        return render(request, self.template_name, {
            "household": household,
            "categories": categories,
            "q": q,
            "order": order,
        })

    def _save_target_days(self, request):
        household = request.user.household
        target_choice = request.POST.get("target_choice")  # "3" / "7" / "14" / "custom"
        custom_days = request.POST.get("custom_days")

        if target_choice in {"3", "7", "14"}:
            household.target_days = int(target_choice)
            household.save(update_fields=["target_days"])
            return

        if target_choice == "custom":
            try:
                days = int(custom_days)
                if days <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                messages.error(request, "カスタム日数は1以上の数字で入力してください。")
                return

            household.target_days = days
            household.save(update_fields=["target_days"])
            return

        messages.error(request, "目標備蓄日数を選択してください。")

    def _bulk_delete_categories(self, request):
        household = request.user.household
        ids = request.POST.getlist("selected_ids")

        if not ids:
            messages.warning(request, "削除する分類を選択してください。")
            return

        Category.objects.filter(household=household, id__in=ids).delete()
        messages.success(request, "分類を削除しました。")
        
    def _render(self, request):
        household = request.user.household

        q = (request.GET.get("q") or "").strip()

        # ✅ sort（並び替え） created / name
        sort = request.GET.get("sort") or "created"

        categories = Category.objects.filter(household=household)

        # ✅ 検索（今はnameだけでOK）
        if q:
            categories = categories.filter(name__icontains=q)

        # ✅ 並び替え
        if sort == "name":
            categories = categories.order_by("name", "id")
        else:
            categories = categories.order_by("id")  # 登録順（id順）

        return render(request, self.template_name, {
            "household": household,
            "categories": categories,
            "q": q,
            "sort": sort,
        })      
        
            
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
