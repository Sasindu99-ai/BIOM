from django.apps.config import AppConfig

__all__ = ['AdminConfig']


class AdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admins'
