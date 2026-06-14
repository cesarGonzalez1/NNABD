from django.apps import AppConfig


class WebConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web"

    def ready(self):
        # Conecta las senales de auditoria (LGDNNA Art. 76).
        from . import signals  # noqa: F401
