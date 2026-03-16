# stocknavi/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from inventory import views as inv_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", inv_views.PortfolioView.as_view(), name="portfolio"),
    path("admin/", admin.site.urls),
    path("inventory/", include("inventory.urls")),

    # ★mypage・signup・alert_setting・password reset など自作側を先に読む
    path("accounts/", include("accounts.urls")),

    # ★標準ログイン/ログアウトは後ろ
    path("accounts/", include("django.contrib.auth.urls")),

    # 要件どおり /invite/ でアクセスできるようにする
    path("invite/", inv_views.InviteCreateView.as_view(), name="invite_create_root"),
    path("invite/<str:token>/", inv_views.InviteAcceptView.as_view(), name="invite_accept_root"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])