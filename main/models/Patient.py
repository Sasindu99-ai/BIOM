from django.db.models.functions import Concat

from authentication.enums import Gender
from authentication.models import User
from vvecon.zorion.db import models

__all__ = ['Patient']


class Patient(models.Model):
	firstName = models.CharField(max_length=150, blank=True, null=True)
	lastName = models.CharField(max_length=150, blank=True, null=True)
	fullName = models.GeneratedField(
		verbose_name='Full Name', editable=False, db_persist=True,
		expression=Concat(
			models.F('firstName'),
			models.Value(' '),
			models.F('lastName'),
		),
		output_field=models.CharField(max_length=101),
	)
	dateOfBirth = models.DateField(blank=True, null=True)
	gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.PREFER_NOT_TO_SAY)
	notes = models.TextField(blank=True, null=True)
	createdBy = models.ForeignKey(
		User, on_delete=models.SET_NULL, null=True, blank=True, related_name='createdPatients'
	)

	def __str__(self):
		return f'{self.pk} - {self.fullName}' if self.fullName else self.pk
