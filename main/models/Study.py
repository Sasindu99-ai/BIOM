from authentication.models import User
from vvecon.zorion.db import models
from ..enums import StudyCategory, StudyStatus
from .StudyVariable import StudyVariable

__all__ = ['Study']


class Study(models.Model):
	category = models.CharField(
		max_length=50, verbose_name='Category', choices=StudyCategory.choices, null=True, blank=True
	)
	createdBy = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='Created By', null=True, blank=True)
	members = models.ManyToManyField(
		User, verbose_name='Members', related_name='members', null=True, blank=True
	)
	name = models.CharField(max_length=255, verbose_name='Name')
	reference = models.CharField(max_length=255, verbose_name='Reference')
	status = models.CharField(
		max_length=50, verbose_name='Status', choices=StudyStatus.choices, default=StudyStatus.ACTIVE
	)
	description = models.TextField(verbose_name='Description', blank=True, null=True)
	version = models.IntegerField(verbose_name='Version', default=1)
	variables = models.ManyToManyField(
		StudyVariable, verbose_name='Variables', related_name='studies', null=True, blank=True
	)

	def __str__(self):
		return self.name
