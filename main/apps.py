from django.apps import AppConfig

__all__ = ['MainConfig']


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
