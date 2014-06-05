from django.apps import AppConfig

class DataAppConfig(AppConfig):
    name = 'mygpo.data'

    def ready(self):
        # make sure those are executed on startup
        import mygpo.data.signals
