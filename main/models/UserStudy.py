from authentication.models import User
from vvecon.zorion.db import models

from ..enums import UserStudyStatus
from .Patient import Patient
from .Study import Study

__all__ = ['UserStudy']


class UserStudy(models.Model):
	createdBy = models.ForeignKey(
		User, on_delete=models.SET_NULL, related_name='createdStudies', null=True, blank=True,
	)
	reference = models.CharField(max_length=255, verbose_name='Reference')
	status = models.CharField(
		max_length=50, verbose_name='Status', choices=UserStudyStatus.choices, default=UserStudyStatus.PENDING,
	)
	study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='userStudies')
	patient = models.ForeignKey(
		Patient, on_delete=models.SET_NULL, related_name='userStudies', null=True, blank=True,
	)
	administeredBy = models.ForeignKey(
		User, on_delete=models.SET_NULL, related_name='administeredStudies', null=True, blank=True,
	)
	version = models.IntegerField(verbose_name='Version', default=1)

	def __str__(self):
		return f'{self.patient} - {self.study}'
