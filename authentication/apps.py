from django.apps import AppConfig

__all__ = ['AuthenticationConfig']


class AuthenticationConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'authentication'

	def ready(self):
		from . import signals  # noqa: F401, PLC0415
