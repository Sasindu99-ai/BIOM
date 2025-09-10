from vvecon.zorion.db import models

__all__ = ['DeviceType']


class DeviceType(models.TextChoices):
	LAPTOP = 'LAPTOP', 'Laptop'
	DESKTOP = 'DESKTOP', 'Desktop'
