from django.contrib import admin
from .models import InventoryItem, Memo, Category, StorageLocation

admin.site.register(Category)
admin.site.register(InventoryItem)
admin.site.register(Memo)

@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "household", "name", "updated_at")
    search_fields = ("name",)
    list_filter = ("household",)