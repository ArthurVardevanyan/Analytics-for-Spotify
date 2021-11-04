"""WSGI config for AnalyticsforSpotify project."""
from django.core.wsgi import get_wsgi_application
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AnalyticsforSpotify.settings')
application = get_wsgi_application()
