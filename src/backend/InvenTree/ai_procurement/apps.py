from django.apps import AppConfig


class AIProcurementConfig(AppConfig):
    """App configuration for AI Procurement."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_procurement'
    verbose_name = 'AI Procurement'

    def ready(self):
        """Register signal handlers when app is ready."""
        # Import signals to register handlers
        from . import signals  # noqa: F401