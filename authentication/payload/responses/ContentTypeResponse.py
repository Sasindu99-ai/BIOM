from django.contrib.contenttypes.models import ContentType

from vvecon.zorion import serializers

__all__ = ['ContentTypeResponse']


class ContentTypeResponse(serializers.ModelResponse):
	model = ContentType
	fields = '__all__'
