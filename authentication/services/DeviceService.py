import uuid

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from rest_framework.exceptions import NotFound

from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger

from ..models import Device

__all__ = ['DeviceService']


class DeviceService(Service):
	model = Device
	searchableFields = ('name', 'nickname', 'macAddress', 'publicId', 'ipAddress')
	filterableFields = ('deviceType', 'isActive')

	def registerDevice(self, request, data):
		validated_data = data.validated_data
		validated_data['macAddress'] = self.model.cleanMacAddress(validated_data['macAddress'])
		validated_data['ipAddress'] = request.META.get('HTTP_X_FORWARDED_FOR')
		validated_data['lastSeen'] = timezone.now()
		return self.create(validated_data)

	def validateDevice(self, request, deviceId: uuid.UUID):
		Logger.info(f'Validating device with public ID {deviceId}')
		try:
			device = self.model.objects.get(publicId=deviceId, isActive=True)
			device.lastSeen = timezone.now()
			device.ipAddress = request.META.get('HTTP_X_FORWARDED_FOR')
			device.save()
			return device
		except (ObjectDoesNotExist, ValidationError):
			raise NotFound(f'Device with public ID {deviceId} not found')

	def deactivateDevice(self, deviceId: uuid.UUID):
		try:
			Logger.info(f'Deactivating device with public ID {deviceId}')
			device = self.model.objects.get(publicId=deviceId)
			device.isActive = False
			device.save()
			return device
		except (ObjectDoesNotExist, ValidationError):
			raise NotFound(f'Device with public ID {deviceId} not found')

	def getByPublicId(self, publicId: uuid.UUID):
		return self.model.objects.filter(publicId=publicId).first()
