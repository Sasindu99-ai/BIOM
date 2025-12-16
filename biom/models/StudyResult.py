from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django_mongodb_backend.fields import ArrayField, EmbeddedModelArrayField, ObjectIdField
from django_mongodb_backend.models import EmbeddedModel

__all__ = ['Result', 'StudyResult']


class Result(EmbeddedModel):
	variable = ObjectIdField(blank=True, null=True)
	value = models.CharField(max_length=100)
	values = ArrayField(
		models.CharField(max_length=2048),
		blank=True,
		null=True,
	)

	def variable_name(self):
		"""Resolve the variable ObjectId to its StudyVariable name."""
		from .StudyVariable import StudyVariable  # import inside to avoid circular import
		if not self.variable:
			return '-'
		try:
			return StudyVariable.objects.using('biom').get(pk=self.variable).name
		except ObjectDoesNotExist:
			return f'[Missing: {self.variable}]'


class StudyResult(models.Model):
	study = ObjectIdField(blank=True, null=True)
	results = EmbeddedModelArrayField(Result, blank=True, null=True)
	status = models.CharField(max_length=50)
	createdBy = ObjectIdField(blank=True, null=True)
	createdAt = models.DateTimeField(auto_now_add=True)
	updatedAt = models.DateTimeField(auto_now=True)
	reference = models.CharField(max_length=255, blank=True, null=True)
	version = models.IntegerField(default=0, db_column='__v')

	class Meta:
		db_table = 'studyResult'
		managed = False
		indexes = [
			models.Index(fields=['study']),
			models.Index(fields=['status']),
			models.Index(fields=['reference']),
		]
