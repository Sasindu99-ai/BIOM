from vvecon.zorion.db import models

__all__ = ['StudyVariableField']


class StudyVariableField(models.TextChoices):
	DROPDOWN = 'DROPDOWN', 'Dropdown'
	IMAGE = 'IMAGE', 'Image'
	FILE = 'File', 'File'
	DATE = 'DATE', 'Date'
	TEXT = 'TEXT', 'Text'
