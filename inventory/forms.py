from django import forms
from .models import InventoryItem
from decimal import Decimal, InvalidOperation
import datetime, calendar



class InventoryItemForm(forms.ModelForm):
    # =========================
    # 購入月
    # =========================
    purchase_month = forms.DateField(
        required=False,
        input_formats=["%Y-%m"],
        widget=forms.DateInput(
            format="%Y-%m",
            attrs={"type": "month"}
        )
    )

    # =========================
    # 賞味・消費期限
    # ※ 設計図どおり month入力
    # 必須にしたい場合は required=True のまま
    # =========================
    expiry_date = forms.DateField(
        required=True,
        input_formats=["%Y-%m"],
        widget=forms.DateInput(
            format="%Y-%m",
            attrs={"type": "month"}
        )
    )

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "content_amount",
            "quantity",
            "purchase_month",
            "expiry_date",
            "storage_location",
            "image",
        ]

        labels = {
            "name": "商品名",
            "category": "分類",
            "content_amount": "内容量",
            "quantity": "個数",
            "purchase_month": "購入日",
            "expiry_date": "賞味・消費期限",
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
        self.fields["storage_location"].error_messages = {
            "required": "保管場所を選択してください。"
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
        フォーム全体の変換処理
        purchase_month(YYYY-MM) を purchase_date に入れたい場合に使う
        既存の実装を壊さないように最低限だけ残す
        """
        cleaned_data = super().clean()

        purchase_month = cleaned_data.get("purchase_month")
        if purchase_month:
            # その月の1日を purchase_date に入れる
            cleaned_data["purchase_date"] = purchase_month.replace(day=1)

        expiry_date = cleaned_data.get("expiry_date")
        if expiry_date:
            # YYYY-MM 入力の場合、その月の末日として保存したいならここで変換
            last_day = calendar.monthrange(expiry_date.year, expiry_date.month)[1]
            cleaned_data["expiry_date"] = expiry_date.replace(day=last_day)

        return cleaned_data
