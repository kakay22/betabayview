from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ADMIN'

    def ready(self):
        import ADMIN.signals  # Import signals once when app is ready