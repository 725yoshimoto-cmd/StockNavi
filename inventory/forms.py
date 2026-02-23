from django import forms
from .models import InventoryItem, Category

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ["category", "name", "quantity"]

    def __init__(self, *args, **kwargs):
        household = kwargs.pop("household", None)
        super().__init__(*args, **kwargs)
        if household:
            self.fields["category"].queryset = Category.objects.filter(household=household)