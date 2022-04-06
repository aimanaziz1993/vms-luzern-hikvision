from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import tenant, dashboard, administrator

urlpatterns = [
    path('', include('accounts.urls')),
    path('self-register/', include('self_registration.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/admin/create/', administrator.AdminCreationView.as_view(), name='create_admin'),
    path('accounts/tenant/create/', tenant.TenantCreationView.as_view(), name='create_tenant'),
]

if settings.DEBUG:
    # urlpatterns += static(
    #     settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # urlpatterns += static(
    #     settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
