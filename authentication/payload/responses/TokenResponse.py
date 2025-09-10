from vvecon.zorion import serializers

__all__ = ['TokenResponse']


class TokenResponse(serializers.Response):
    token = serializers.CharField(max_length=255)
    refresh = serializers.CharField(max_length=255)
