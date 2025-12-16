from vvecon.zorion.db import models

from .StudyVariable import StudyVariable
from .UserStudy import UserStudy

__all__ = ['StudyResult']


class StudyResult(models.Model):
	userStudy = models.ForeignKey(
		UserStudy, on_delete=models.CASCADE, verbose_name='User Study', related_name='results',
	)
	studyVariable = models.ForeignKey(
		StudyVariable, on_delete=models.CASCADE, verbose_name='Study Variable', related_name='results',
	)
	value = models.CharField(verbose_name='Value', blank=True, null=True, max_length=2048)

	def __str__(self):
		return f'{self.userStudy} - {self.studyVariable}: {self.value}'
