from django import forms
from .models import InventoryItem
from decimal import Decimal, InvalidOperation


class InventoryItemForm(forms.ModelForm):
    # =========================
    # 購入日
    # text入力に戻す
    # - 見た目は YYYY/MM/DD
    # - ただし YYYY-MM-DD でも受けられるようにする
    # =========================
    purchase_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%Y/%m/%d"],
        widget=forms.DateInput(
            format="%Y/%m/%d",
            attrs={
                "type": "text",
                "placeholder": "YYYY/MM/DD",
            }
        )
    )

    # =========================
    # 消費・賞味期限
    # text入力に戻す
    # - 見た目は YYYY/MM/DD
    # - ただし YYYY-MM-DD でも受けられるようにする
    # =========================
    expiry_date = forms.DateField(
        required=True,
        input_formats=["%Y-%m-%d", "%Y/%m/%d"],
        widget=forms.DateInput(
            format="%Y/%m/%d",
            attrs={
                "type": "text",
                "placeholder": "YYYY/MM/DD",
            }
        )
    )

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "content_amount",
            "content_unit",
            "quantity",
            "quantity_unit",
            "purchase_date",
            "expiry_date",
            "storage_location",
            "image",
        ]

        labels = {
            "name": "商品名",
            "category": "分類",
            "content_amount": "内容量",
            "content_unit": "内容量の単位",
            "quantity": "個数",
            "quantity_unit": "個数の単位",
            "purchase_date": "購入日",
            "expiry_date": "消費・賞味期限",
            "storage_location": "保管場所",
            "image": "商品画像",
        }

        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "例：水",
            }),
            "content_amount": forms.NumberInput(attrs={
                "step": "0.1",
                "min": "0.1",
            }),
            "quantity": forms.NumberInput(attrs={
                "step": "1",
                "min": "1",
            }),
            "category": forms.Select(),
            "storage_location": forms.Select(),
            "image": forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        """
        フォーム表示時の初期設定
        """
        super().__init__(*args, **kwargs)

        # 画像は任意
        self.fields["image"].required = False

        # 分類・保管場所は必須
        self.fields["category"].required = True
        self.fields["storage_location"].required = True

        # 個数の初期値は新規時だけ 1
        if not self.instance.pk:
            self.fields["quantity"].initial = 1

        # 分かりやすい必須メッセージ
        self.fields["name"].error_messages = {
            "required": "商品名を入力してください。"
        }
        self.fields["category"].error_messages = {
            "required": "分類を選択してください。"
        }
        self.fields["content_amount"].error_messages = {
            "required": "内容量を入力してください。"
        }
        self.fields["quantity"].error_messages = {
            "required": "個数を入力してください。"
        }
        self.fields["purchase_date"].error_messages = {
            "invalid": "購入日を正しく入力してください。"
        }
        self.fields["expiry_date"].error_messages = {
            "required": "消費・賞味期限を入力してください。",
            "invalid": "消費・賞味期限を正しく入力してください。"
        }

    def clean_quantity(self):
        """
        個数チェック
        """
        quantity = self.cleaned_data.get("quantity")

        if quantity is None:
            return quantity

        if quantity <= 0:
            raise forms.ValidationError("個数は1以上で入力してください。")

        return quantity

    def clean_content_amount(self):
        """
        内容量チェック
        - 0は禁止
        - 0.5はOK
        """
        content_amount = self.cleaned_data.get("content_amount")

        if content_amount is None:
            return content_amount

        try:
            value = Decimal(str(content_amount))
        except (InvalidOperation, TypeError):
            raise forms.ValidationError("内容量を正しく入力してください。")

        if value <= 0:
            raise forms.ValidationError("内容量は0より大きい値を入力してください。")

        return value

    def clean(self):
        """
        フォーム全体の共通バリデーション
        """
        cleaned_data = super().clean()
        return cleaned_data