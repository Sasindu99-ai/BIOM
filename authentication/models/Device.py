import uuid

from vvecon.zorion.db import models

from ..enums import DeviceType

__all__ = ['Device']


class Device(models.Model):
	name = models.CharField(max_length=255, verbose_name='Device Name')
	nickname = models.CharField(max_length=255, null=True, blank=True, verbose_name='Nickname')
	macAddress = models.CharField(max_length=255, verbose_name='MAC Address')
	deviceType = models.CharField(
		choices=DeviceType.choices, max_length=255, default=DeviceType.DESKTOP, verbose_name='Device Type',
	)
	publicId = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='Public ID')
	ipAddress = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
	lastSeen = models.DateTimeField(null=True, blank=True, verbose_name='Last Seen')
	isActive = models.BooleanField(default=True, verbose_name='Is Active')

	def save(self, *args, **kwargs):
		if self.macAddress:
			self.macAddress = self.cleanMacAddress(str(self.macAddress))
		super().save(*args, **kwargs)

	@staticmethod
	def cleanMacAddress(macAddress: str) -> str:
		return ':'.join(macAddress.strip().lower().replace('-', ':').split(':'))
