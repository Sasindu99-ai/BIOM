from vvecon.zorion.db import models

__all__ = ['UserStudyStatus']


class UserStudyStatus(models.TextChoices):
	PENDING = 'PENDING', 'Pending'
	APPROVED = 'APPROVED', 'Approved'
	REJECTED = 'REJECTED', 'Rejected'
