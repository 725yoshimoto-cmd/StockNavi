from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import InventoryItem

def index(request):
    return HttpResponse("StockNavi Top Page")

class InventoryListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = "inventory/list.html"