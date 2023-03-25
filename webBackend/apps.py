from django.apps import AppConfig


def boot():
    import logging
    import os
    import monitoringBackend.spotify as spotify
    log = logging.getLogger(__name__)

    try:
        if(os.environ.get('TEST') == "test" or os.environ.get('MIGRATIONS') == "true"):
            log.info("Testing Environment")
        else:
            spotify.main()
    except:
        log.exception("Monitoring Backend Fail")
        return False
    return True


class WebBackendConfig(AppConfig):
    name = 'webBackend'

    def ready(self):
        pass
        name = 'webBackend'
        from webBackend import views
        boot()
