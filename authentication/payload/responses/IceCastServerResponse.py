from vvecon.zorion import serializers

from ...models import IceCastServer

__all__ = ['IceCastServerResponse']


class IceCastServerResponse(serializers.ModelResponse):
	model = IceCastServer
	fields = '__all__'
