from django import forms
from .models import InventoryItem
import datetime


class InventoryItemForm(forms.ModelForm):
    purchase_month = forms.CharField(
        required=False,
        widget=forms.DateInput(attrs={"type": "month"})
    )
    expiry_month = forms.CharField(
        required=False,
        widget=forms.DateInput(attrs={"type": "month"})
    )

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "content_amount",
            "quantity",
            "purchase_month",
            "expiry_month",
            "storage_location",
            "image",
        ]
        labels = {
            "category": "分類",
            "storage_location": "保管場所",
            "name": "在庫名",
            "quantity": "数量",
            "content_amount": "内容量",
            "purchase_month": "購入日",
            "expiry_month": "賞味期限",
            "image": "商品画像",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.purchase_date:
            self.fields["purchase_month"].initial = self.instance.purchase_date.strftime("%Y-%m")

        if self.instance and self.instance.expiry_date:
            self.fields["expiry_month"].initial = self.instance.expiry_date.strftime("%Y-%m")

    def clean(self):
        cleaned_data = super().clean()

        purchase_month = cleaned_data.get("purchase_month")
        expiry_month = cleaned_data.get("expiry_month")

        if purchase_month:
            year, month = map(int, purchase_month.split("-"))
            cleaned_data["purchase_date"] = datetime.date(year, month, 1)
        else:
            cleaned_data["purchase_date"] = None

        if expiry_month:
            year, month = map(int, expiry_month.split("-"))
            cleaned_data["expiry_date"] = datetime.date(year, month, 1)
        else:
            cleaned_data["expiry_date"] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.purchase_date = self.cleaned_data.get("purchase_date")
        instance.expiry_date = self.cleaned_data.get("expiry_date")

        if commit:
            instance.save()
            self.save_m2m()

        return instance