from vvecon.zorion.db import models

__all__ = ['BioMarkerStatus']


class BioMarkerStatus(models.TextChoices):
	PENDING = 'PENDING', 'Pending'
	APPROVED = 'APPROVED', 'Approved'
	REJECTED = 'REJECTED', 'Rejected'
