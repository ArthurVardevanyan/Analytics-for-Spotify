"""AnalyticsforSpotify URL Configuration"""
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('webBackend.urls')),
    path('/', include('webBackend.urls')),
    path('spotify/', include('webBackend.urls')),
    path('analytics/', include('webBackend.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
