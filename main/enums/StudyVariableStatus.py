from vvecon.zorion.db import models

__all__ = ['StudyVariableStatus']


class StudyVariableStatus(models.TextChoices):
	ACTIVE = 'ACTIVE', 'Active'
	INACTIVE = 'INACTIVE', 'Inactive'
