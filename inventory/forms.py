from django import forms
from .models import InventoryItem
from decimal import Decimal, InvalidOperation
import datetime, calendar



class InventoryItemForm(forms.ModelForm):
    purchase_month = forms.CharField(
        required=False,
        widget=forms.DateInput(attrs={"type": "month"})
    )

    """
    在庫登録/編集フォーム
    - 購入月は YYYY-MM で受け取って purchase_date に入れる
    - 内容量の単位 / 個数の単位を選べるようにする
    """

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "content_amount",
            "content_unit",
            "quantity",
            "quantity_unit",
            "purchase_month",
            "expiry_date",
            "storage_location",
            "image",
        ]

        labels = {
            "category": "分類",
            "storage_location": "保管場所",
            "name": "商品名",
            "quantity": "個数",
            "quantity_unit": "個数の単位",
            "content_amount": "内容量",
            "content_unit": "内容量の単位",
            "purchase_date": "購入日",
            "expiry_date": "賞味期限",
            "image": "商品画像",
        }

        widgets = {
            "name": forms.TextInput(),
            "category": forms.Select(),
            "content_amount": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "content_unit": forms.Select(),
            "quantity": forms.NumberInput(attrs={"min": "0"}),
            "quantity_unit": forms.Select(),
            "expiry_date": forms.DateInput(attrs={"type": "month"}),
            "storage_location": forms.Select(),
            "image": forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 既存データ編集時：購入月を YYYY-MM で初期表示
        if self.instance and self.instance.pk and self.instance.purchase_date:
            self.initial["purchase_month"] = self.instance.purchase_date.strftime("%Y-%m")

        # 新規登録時：設計図寄せの初期値
        if not self.instance.pk:
            self.fields["content_unit"].initial = "L"
            self.fields["quantity_unit"].initial = "本"

    def clean_purchase_month(self):
        purchase_month = self.cleaned_data.get("purchase_month")
        if not purchase_month:
            return None

        year, month = map(int, purchase_month.split("-"))
        return datetime.date(year, month, 1)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.purchase_date = self.cleaned_data.get("purchase_month")

        if commit:
            instance.save()
            self.save_m2m()

        return instance