from django.contrib.auth.models import Permission

from vvecon.zorion import serializers

from .ContentTypeResponse import ContentTypeResponse

__all__ = ['PermissionResponse']


class PermissionResponse(serializers.ModelResponse):
	content_type = ContentTypeResponse().response()

	model = Permission
	fields = '__all__'
