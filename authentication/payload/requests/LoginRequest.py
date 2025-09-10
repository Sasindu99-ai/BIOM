from vvecon.zorion import serializers

__all__ = ['LoginRequest']


class LoginRequest(serializers.Request):
	username = serializers.CharField(required=True)
	password = serializers.CharField(required=True)
