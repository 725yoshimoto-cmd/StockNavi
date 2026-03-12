# accounts/views.py

# Django基本
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.db import transaction

# 自アプリ
from .forms import AlertSettingForm, UserUpdateForm, SignUpForm
from .models import AlertSetting, Household

# 既存：世帯必須のMixin（プロジェクトにあるやつ）
from inventory.mixins import HouseholdRequiredMixin

from inventory.views import HouseholdRequiredMixin

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

    通常登録では
    - Household を新規作成
    - user にその household をセット
    - そのままログイン
    を行う
    """
    template_name = "accounts/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("inventory:inventory_list")

    @transaction.atomic
    def form_valid(self, form):
        """
        登録成功時の処理

        transaction.atomic を使う理由：
        user だけ保存されて household が無い、
        という中途半端な状態を防ぐため
        """
        # まだ保存しない user を作る
        user = form.save(commit=False)

        # 新しい世帯を自動作成
        household = Household.objects.create(
            name=f"{user.username}さんの世帯"
        )

        # user に household をセット
        user.household = household

        # user を保存
        user.save()

        # そのままログイン
        login(self.request, user)

        messages.success(self.request, "アカウント登録が完了しました。")
        return redirect(self.success_url)