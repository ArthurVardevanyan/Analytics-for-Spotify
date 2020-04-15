from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    name = 'analytics'

    def ready(self):
        pass
        name = 'analytics'
        from analytics import views
        from SpotifyAnalytics.credentials import PRIVATE
        # 1:None
        # 2:Local Private Key
        # 3:Runtime Private Key
        encryptionLevel = 2
        if(encryptionLevel == 2):
            views.boot(PRIVATE, 1)
