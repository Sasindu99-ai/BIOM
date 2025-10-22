from django.apps import AppConfig

__all__ = ['BiomConfig']


class BiomConfig(AppConfig):
	default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
	name = "biom"
