from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    name = 'analytics'

    def ready(self):
        pass
        name = 'analytics'
        from analytics import views
        views.boot()
