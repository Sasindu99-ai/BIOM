from vvecon.zorion.db import models

__all__ = ['StudyStatus']


class StudyStatus(models.TextChoices):
	ACTIVE = 'ACTIVE', 'Active'
	INACTIVE = 'INACTIVE', 'Inactive'
