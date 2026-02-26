# accounts/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from .forms import AlertSettingForm
from .models import AlertSetting

# すでにプロジェクトで使っている HouseholdRequiredMixin を流用
# ※置き場所が違うなら import はあなたの実装に合わせてOK
from inventory.mixins import HouseholdRequiredMixin


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

        # 成功レスポンス
        return JsonResponse({"ok": True, "message": "アラート設定を保存しました"})from django.shortcuts import render

# Create your views here.
