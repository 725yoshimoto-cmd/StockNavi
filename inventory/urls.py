from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("inventory/", views.InventoryListView.as_view(), name="inventory_list"),
]
