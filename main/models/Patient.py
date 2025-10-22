from authentication.enums import Gender
from authentication.models import User
from vvecon.zorion.db import models

__all__ = ['Patient']


class Patient(models.Model):
	pid = models.CharField(max_length=100, verbose_name='PID')
	firstName = models.CharField(max_length=150, blank=True, null=True)
	lastName = models.CharField(max_length=150, blank=True, null=True)
	dateOfBirth = models.DateField(blank=True, null=True)
	gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.PREFER_NOT_TO_SAY)
	notes = models.TextField(blank=True, null=True)
	createdBy = models.ForeignKey(
		User, on_delete=models.SET_NULL, null=True, blank=True, related_name='createdPatients'
	)

	def __str__(self):
		return f'{self.pid} - {self.fullName}' if self.fullName else self.pid

	@property
	def fullName(self):
		return " ".join(filter(None, (self.firstName, self.lastName))).strip()
