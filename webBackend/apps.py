from django.apps import AppConfig


class WebBackendConfig(AppConfig):
    name = 'webBackend'

    def ready(self):
        pass
        name = 'webBackend'
        from webBackend import views
        views.boot()
