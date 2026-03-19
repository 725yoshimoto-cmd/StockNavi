from django import forms
from .models import InventoryItem


class InventoryItemForm(forms.ModelForm):
    """
    在庫登録/編集フォーム
    - purchase_date / expiry_date はスマホで入力しやすいように date picker にする
    """
    class Meta:
        model = InventoryItem
        fields = [
            "category",
            "storage_location",
            "name",
            "quantity",
            "content_amount",
            "purchase_date",
            "expiry_date",
            "image",
        ]
        labels = {
            "category": "分類",
            "storage_location": "保管場所",
            "name": "在庫名",
            "quantity": "数量",
            "content_amount": "内容量",
            "purchase_date": "購入日",
            "expiry_date": "賞味期限",
            "image": "商品画像",
        }
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }