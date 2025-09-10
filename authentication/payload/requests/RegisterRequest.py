from vvecon.zorion import serializers

from ...models import User

__all__ = ['RegisterRequest']


class RegisterRequest(serializers.ModelRequest):
	class Meta:
		model = User
		fields = ('firstName', 'lastName', 'email', 'username', 'password')
