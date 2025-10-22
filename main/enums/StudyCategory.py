from vvecon.zorion.db import models

__all__ = ['StudyCategory']


class StudyCategory(models.TextChoices):
	CKDU = 'CKDU', 'ckdu'
