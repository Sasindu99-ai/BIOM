from vvecon.zorion import serializers

__all__ = ['LoginRequest']


class LoginRequest(serializers.Request):
	email = serializers.CharField(required=True)
	password = serializers.CharField(required=True)
	remember = serializers.CharField(required=False)
