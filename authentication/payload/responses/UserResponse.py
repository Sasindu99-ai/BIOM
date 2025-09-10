from django.contrib.auth.models import Permission

from vvecon.zorion import serializers

from ...models import User
from .PermissionResponse import PermissionResponse

__all__ = ['UserResponse']


class UserResponse(serializers.ModelResponse):
	permissions = serializers.SerializerMethodField()

	model = User
	fields = (
		'id', 'username', 'firstName', 'lastName', 'email', 'nic', 'countryCode', 'mobileNumber', 'dateOfBirth',
		'country', 'fullName', 'permissions', 'is_active', 'is_staff', 'is_superuser',
	)

	@staticmethod
	def get_permissions(obj):
		if obj.is_superuser:
			return PermissionResponse(data=Permission.objects.all(), many=True).data
		permissions = obj.user_permissions.all()
		for group in obj.groups.all():
			permissions |= group.permissions.all()
		return PermissionResponse(data=permissions, many=True).data
