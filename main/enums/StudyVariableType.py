from vvecon.zorion.db import models

__all__ = ['StudyVariableType']


class StudyVariableType(models.TextChoices):
	NUMBER = 'NUMBER', 'Number'
	TEXT = 'TEXT', 'Text'
	DATE = 'DATE', 'Date'
	BOOLEAN = 'BOOLEAN', 'Boolean'
