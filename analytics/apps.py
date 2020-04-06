from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    name = 'analytics'
    def ready(self):
        import os
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        import spotify
        spotify.main()