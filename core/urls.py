from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core import settings
from vvecon.zorion.urls import django_include, django_path, include

urlpatterns = [
    path('superadmin/', admin.site.urls),
    include('main.urls'),
    include('authentication.urls'),
    include('admins.urls'),
    include('settings.urls'),
    # include('biom.urls'),
] + static(settings.STATIC_URL,
           document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
	re_path(r'^media/(?P<path>.*)$', serve, {
		'document_root': settings.MEDIA_ROOT,
	}),
] + [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + [
	django_path('auth/', django_include('allauth.urls')),
]

if settings.DEBUG:
	urlpatterns += debug_toolbar_urls()
