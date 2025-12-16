from vvecon.zorion.db import models

from .StudyVariable import StudyVariable

__all__ = ['StudyVariableAnswer']


class StudyVariableAnswer(models.Model):
	variable = models.ForeignKey(
		StudyVariable, on_delete=models.CASCADE, verbose_name='Variable', related_name='answers',
	)
	value = models.CharField(max_length=255, verbose_name='Value')

	def __str__(self):
		return self.value
