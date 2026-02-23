from django.contrib import admin
from .models import InventoryItem, Memo, Category

admin.site.register(Category)
admin.site.register(InventoryItem)
admin.site.register(Memo)