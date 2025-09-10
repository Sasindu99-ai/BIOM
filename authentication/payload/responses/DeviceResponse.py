from vvecon.zorion import serializers

from ...models import Device

__all__ = ['DeviceResponse']


class DeviceResponse(serializers.ModelResponse):
	model = Device
	fields = '__all__'
