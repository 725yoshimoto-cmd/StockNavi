from django.contrib import admin
from .models import InventoryItem, Memo, Category, StorageLocation

admin.site.register(Category)
admin.site.register(Memo)

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("id", "household", "name", "is_deleted", "updated_at")
    list_filter = ("household", "is_deleted")
    search_fields = ("name",)
    
@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "household", "name", "updated_at") 
    search_fields = ("name",)
    list_filter = ("household",)

