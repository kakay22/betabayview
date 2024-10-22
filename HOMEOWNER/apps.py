# apps.py

from django.apps import AppConfig

class YourAppConfig(AppConfig):
    name = 'HOMEOWNER'

    def ready(self):
        import HOMEOWNER.signals
