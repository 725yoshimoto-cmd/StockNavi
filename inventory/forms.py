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
            "image",
        ]
        labels = {
            "category": "分類",
            "storage_location": "保管場所",
            "name": "在庫名",
            "quantity": "数量",
            "content_amount": "内容量",
            "expiry_date": "賞味期限",
            "image": "商品画像",
        }
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }