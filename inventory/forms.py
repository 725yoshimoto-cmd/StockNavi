# inventory/forms.py
from django import forms
from .models import InventoryItem


class InventoryItemForm(forms.ModelForm):
    """
    在庫登録/編集フォーム
    - expiry_date はスマホで入力しやすいように date picker にする
    """
    class Meta:
        model = InventoryItem
        fields = [
            "category",
            "storage_location",
            "name",
            "quantity",
            "content_amount",
            "expiry_date",
        ]
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }