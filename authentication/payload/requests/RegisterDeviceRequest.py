from vvecon.zorion import serializers

from ...models import Device

__all__ = ['RegisterDeviceRequest']


class RegisterDeviceRequest(serializers.ModelRequest):
	class Meta:
		model = Device
		fields = ('name', 'nickname', 'macAddress', 'deviceType')
