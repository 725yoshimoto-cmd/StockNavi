# accounts/views.py

# Django基本
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.db import transaction

# 自アプリ
from .forms import AlertSettingForm, UserUpdateForm, SignUpForm
from .models import AlertSetting, Household

# 既存：世帯必須のMixin（プロジェクトにあるやつ）
from inventory.mixins import HouseholdRequiredMixin
from inventory.models import InviteToken   # ← InviteToken の場所に合わせて修正


User = get_user_model()

class MemberListView(LoginRequiredMixin, HouseholdRequiredMixin, TemplateView):
    template_name = "accounts/member_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        household = self.request.user.household
        members = User.objects.filter(household=household).order_by("id")

        context["household"] = household
        context["members"] = members
        return context
    
class AlertSettingView(LoginRequiredMixin, HouseholdRequiredMixin, View):
    """
    アラート設定画面
    - GET : フォーム表示
    - POST: 保存して JSON を返す（画面遷移なしでトースト表示させるため）
    """

    template_name = "accounts/alert_setting.html"

    def _get_setting(self):
        """
        世帯ごとのアラート設定を取得（無ければ作成）
        - ここを共通化すると GET/POST 両方で使えてミスが減る
        """
        household = self.request.user.household
        obj, _ = AlertSetting.objects.get_or_create(household=household)
        return obj

    def get(self, request, *args, **kwargs):
        """
        画面表示
        """
        setting = self._get_setting()
        form = AlertSettingForm(instance=setting)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        """
        保存（AJAX想定）
        """
        setting = self._get_setting()
        form = AlertSettingForm(request.POST, instance=setting)

        # バリデーションエラーならエラー内容をJSONで返す
        if not form.is_valid():
            return JsonResponse(
                {"ok": False, "errors": form.errors},
                status=400
            )

        # 保存
        form.save()
        
        # 成功レスポンス（トースト表示用）
        return JsonResponse({"ok": True, "message": "アラート設定を保存しました"})

# ----------------------------
# ★ マイページ
# ----------------------------
class MyPageView(LoginRequiredMixin, TemplateView):
    """
    マイページ
    - 世帯情報表示
    - ニックネーム/メール更新（最短：username をニックネーム扱い）
    - ログアウト導線
    """
    template_name = "accounts/mypage.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = UserUpdateForm(instance=self.request.user)
        return ctx

    def post(self, request, *args, **kwargs):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "保存しました。")
            return redirect("accounts:mypage")
        # バリデーションエラー時は同じ画面にform付きで戻す
        ctx = self.get_context_data(**kwargs)
        ctx["form"] = form
        return self.render_to_response(ctx)

# ----------------------------
# ★ サインアップ（アカウント登録）
# ----------------------------
class SignUpView(CreateView):
    """
    新規登録画面

    通常登録
    - Householdを新規作成
    - userをその世帯に所属させる

    招待URL登録
    - InviteTokenが有効なら
    - その世帯に参加する
    """
    template_name = "accounts/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("inventory:inventory_list")

    @transaction.atomic
    def form_valid(self, form):

        # まだ保存しないuser
        user = form.save(commit=False)

        # URLの招待tokenを取得
        invite_token = self.kwargs.get("token")

        household = None

        # ----------------------------
        # 招待リンク経由
        # ----------------------------
        if invite_token:

            try:
                token_obj = InviteToken.objects.get(token=invite_token)
            except InviteToken.DoesNotExist:
                messages.error(self.request, "招待リンクが正しくありません。")
                return self.form_invalid(form)

            # 有効チェック
            if not token_obj.is_valid():
                messages.error(self.request, "招待リンクの期限が切れています。")
                return self.form_invalid(form)

            household = token_obj.household

            # 使用済みにする
            token_obj.is_used = True
            token_obj.save()

        # ----------------------------
        # 通常登録
        # ----------------------------
        else:

            household = Household.objects.create(
                name=f"{user.username}さんの世帯"
            )

        # userに世帯をセット
        user.household = household
        user.save()

        # ログイン
        login(self.request, user)

        messages.success(self.request, "アカウント登録が完了しました。")

        return redirect(self.success_url)