from vvecon.zorion.db import models

__all__ = ['Gender']


class Gender(models.TextChoices):
	MALE = 'MALE', 'Male'
	FEMALE = 'FEMALE', 'Female'
	PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY', 'Prefer not to say'
