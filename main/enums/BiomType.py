from vvecon.zorion.db import models

__all__ = ['BiomType']


class BiomType(models.TextChoices):
	EXISTING = 'EXISTING', 'Existing'
	NEW = 'NEW', 'New'
