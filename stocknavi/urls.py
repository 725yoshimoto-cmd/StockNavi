# stocknavi/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from inventory import views as inv_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", RedirectView.as_view(url="/accounts/login/", permanent=False)),
    path("admin/", admin.site.urls),
    path("inventory/", include("inventory.urls")),

    # ★標準ログイン/ログアウト
    path("accounts/", include("django.contrib.auth.urls")),
    # ★mypageなど自作
    path("accounts/", include("accounts.urls")),

    #要件どおり /invite/ でアクセスできるようにする
    path("invite/", inv_views.InviteCreateView.as_view(), name="invite_create_root"),
    path("invite/<str:token>/", inv_views.InviteAcceptView.as_view(), name="invite_accept_root"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    