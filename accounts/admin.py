from django.contrib import admin 
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Household

# CustomUserはDjango標準の管理画面で表示
admin.site.register(CustomUser, UserAdmin)

# Householdを追加
admin.site.register(Household)
