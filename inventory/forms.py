from django import forms
from .models import InventoryItem
from decimal import Decimal, InvalidOperation
import datetime, calendar



class InventoryItemForm(forms.ModelForm):
    purchase_month = forms.CharField(
        required=False,
        widget=forms.DateInput(attrs={"type": "month"})
    )
    
    expiry_month = forms.CharField(
        required=False,
        widget=forms.DateInput(attrs={"type": "month"})
    )    
    """
    在庫登録/編集フォーム
    - purchase_date / expiry_date はスマホで入力しやすいようにする
    """

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "content_amount",
            "quantity",
            "purchase_month",
            "expiry_month",
            "expiry_date",
            "storage_location",
            "image",
        ]

        labels = {
            "category": "分類",
            "storage_location": "保管場所",
            "name": "在庫名",
            "quantity": "数量",
            "content_amount": "内容量",
            "purchase_date": "購入日",
            "expiry_date": "消費・賞味期限",
            "image": "商品画像",
        }

        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "商品名を入力"}),
            "category": forms.Select(),
            "content_amount": forms.NumberInput(attrs={"placeholder": "内容量を入力"}),
            "quantity": forms.NumberInput(attrs={"placeholder": "個数を入力"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "storage_location": forms.Select(),
            "image": forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_labels = {
            "name": "商品名",
            "category": "分類",
            "content_amount": "内容量",
            "quantity": "個数",
            "storage_location": "保管場所",
        }

        for field_name, label in required_labels.items():
            if field_name in self.fields:
                self.fields[field_name].required = True
                self.fields[field_name].error_messages["required"] = f"{label}は必須です。"

        if "content_amount" in self.fields:
            self.fields["content_amount"].widget.attrs.update({
                "step": "1",
                "min": "1",
                "inputmode": "numeric",
                "pattern": "[0-9]*",
            })

        if "quantity" in self.fields:
            self.fields["quantity"].widget.attrs.update({
                "step": "1",
                "min": "1",
                "inputmode": "numeric",
                "pattern": "[0-9]*",
            })

    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        if not value:
            raise forms.ValidationError("商品名は必須です。")
        return value

    def clean_content_amount(self):
        value = self.cleaned_data.get("content_amount")

        if value in (None, ""):
            raise forms.ValidationError("内容量は必須です。")

        if int(value) <= 0:
            raise forms.ValidationError("内容量は1以上で入力してください。")

        return int(value)

    def clean_quantity(self):
        value = self.cleaned_data.get("quantity")

        if value in (None, ""):
            raise forms.ValidationError("個数は必須です。")

        if int(value) <= 0:
            raise forms.ValidationError("個数は1以上で入力してください。")

        return int(value)

    def clean(self):
        cleaned_data = super().clean()

        purchase_month = cleaned_data.get("purchase_month")
        if purchase_month:
            try:
                year, month = map(int, purchase_month.split("-"))
                cleaned_data["purchase_date"] = datetime.date(year, month, 1)
            except Exception:
                self.add_error("purchase_month", "購入月の形式が正しくありません。")

        return cleaned_data