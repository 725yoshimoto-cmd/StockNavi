# inventory/mixins.py

from django.shortcuts import redirect
from django.urls import reverse

class HouseholdRequiredMixin:
    """
    ログインユーザーに household が設定されていない場合、
    /no-household/ にリダイレクトするMixin
    """

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request.user, "household", None):
            return redirect(reverse("inventory:no_household"))
        return super().dispatch(request, *args, **kwargs)
    