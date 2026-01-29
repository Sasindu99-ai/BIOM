from vvecon.zorion.db import models

from ..enums import StudyVariableField, StudyVariableStatus, StudyVariableType

__all__ = ['StudyVariable']


class StudyVariable(models.Model):
	isRange = models.BooleanField(default=False, verbose_name='Is Range')
	name = models.CharField(max_length=255, verbose_name='Name')
	notes = models.TextField(verbose_name='Notes', blank=True, null=True)
	status = models.CharField(
		choices=StudyVariableStatus.choices, max_length=50, default=StudyVariableStatus.ACTIVE, verbose_name='Status',
	)
	type = models.CharField(
		choices=StudyVariableType.choices, max_length=100, default=StudyVariableType.TEXT, verbose_name='Type',
	)
	field = models.CharField(
		choices=StudyVariableField.choices, max_length=100, default=StudyVariableField.TEXT, verbose_name='Field',
	)
	isSearchable = models.BooleanField(default=False, verbose_name='Is Searchable')
	order = models.IntegerField(default=0, verbose_name='Order')
	isUnique = models.BooleanField(default=False, verbose_name='Is Unique')

	def __str__(self):
		return self.name
