from django import forms
from .models import InventoryItem
from decimal import Decimal, InvalidOperation
import datetime, calendar



class InventoryItemForm(forms.ModelForm):
    # =========================
    # 購入日
    # 設計図どおり「年月」入力にする
    # =========================
    purchase_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%Y/%m/%d"],
        widget=forms.DateInput(
            format="%Y/%m/%d",
            attrs={
                "type": "text",
                "placeholder": "YYYY/MM/DD"
            }
        )
    )

    # =========================
    # 消費・賞味期限
    # 設計図どおり「年月」入力にする
    # =========================
    expiry_date = forms.DateField(
        required=True,
        input_formats=["%Y-%m-%d", "%Y/%m/%d"],
        widget=forms.DateInput(
            format="%Y/%m/%d",
            attrs={
                "type": "text",
                "placeholder": "YYYY/MM/DD"
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
                "step": "1",
                "min": "1",   # フロントでも 1未満を入れにくくする
            }),
            "quantity": forms.NumberInput(attrs={
                "step": "1",
                "min": "1",   # フロントでも 1未満を入れにくくする
            }),
            "category": forms.Select(),
            "storage_location": forms.Select(),
            "image": forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        """
        フォーム表示時の初期設定
        - 画像は任意にする
        - 個数の初期値を1にする
        - 必須項目の設定をここでそろえる
        """
        super().__init__(*args, **kwargs)

        # =========================
        # 画像は任意
        # =========================
        self.fields["image"].required = False

        # =========================
        # 分類・保管場所も必須にする
        # ※ model側が blank=True でも、フォーム側で必須にできる
        # ※ 提出直前なので、まずは安全なフォーム制御で対応
        # =========================
        self.fields["category"].required = True
        self.fields["storage_location"].required = True

        # =========================
        # 個数の初期値を 1 にする
        # 既存編集時はDBの値が優先されるので壊れない
        # =========================
        if not self.instance.pk:
            self.fields["quantity"].initial = 1
            
        # =========================
        # 分かりやすい必須メッセージに統一
        # =========================
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
        self.fields["expiry_date"].error_messages = {
            "required": "賞味・消費期限を入力してください。",
            "invalid": "賞味・消費期限を正しく入力してください。"
        }
        self.fields["expiry_date"].error_messages = {
            "required": "消費・賞味期限を入力してください。",
            "invalid": "消費・賞味期限を正しく入力してください。"
        }

    def clean_quantity(self):
        """
        個数チェック
        - 未入力は required メッセージに任せる
        - 0以下は禁止
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
        - 未入力は required メッセージに任せる
        - 0以下は禁止
        """
        content_amount = self.cleaned_data.get("content_amount")

        if content_amount is None:
            return content_amount

        try:
            value = Decimal(str(content_amount))
        except (InvalidOperation, TypeError):
            raise forms.ValidationError("内容量を正しく入力してください。")

        if value <= 0:
            raise forms.ValidationError("内容量は1以上で入力してください。")

        return value

    def clean(self):
        """
        フォーム全体の共通バリデーション
        日付入力はそのまま使う
        """
        cleaned_data = super().clean()
        return cleaned_data