from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve

from accounts.views import tenant, dashboard, administrator

# handler500 = 'self_registration.views.server_error',

urlpatterns = [
    path('', include('accounts.urls')),
    path('self-register/', include('self_registration.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/admin/create/', administrator.AdminCreationView.as_view(), name='create_admin'),
    path('accounts/tenant/create/', tenant.TenantCreationView.as_view(), name='create_tenant'),
]

# urlpatterns += [ re_path(r'^.*', TemplateView.as_view(template_name='404.html'), name='not-found') ]

if settings.DEBUG:
    # urlpatterns += static(
    #     settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # urlpatterns += static(
    #     settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    # path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT})
