
from django.db.models.functions import Concat
from django.utils import timezone

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
	photo = models.CharField(max_length=500, blank=True, null=True, help_text='Profile photo URL')
	latitude = models.FloatField(blank=True, null=True, verbose_name='Latitude')
	longitude = models.FloatField(blank=True, null=True, verbose_name='Longitude')
	reference = models.CharField(
		max_length=100,
		blank=True,
		null=True,
		unique=True,
		db_index=True,
		verbose_name='Reference',
		help_text='Doctor or dataset assigned unique patient reference/identifier',
	)
	createdBy = models.ForeignKey(
		User, on_delete=models.SET_NULL, null=True, blank=True, related_name='createdPatients',
	)

	def save(self, *args, **kwargs):
		if self.reference is not None:
			self.reference = self.reference.strip() or None
		super().save(*args, **kwargs)

	def __str__(self):
		ref_part = f'[{self.reference}] ' if self.reference else ''
		return f'{ref_part}{self.fullName or self.pk}'

	@property
	def ageNow(self) -> int | None:
		if not self.dateOfBirth:
			return None
		today = timezone.today()
		age = today.year - self.dateOfBirth.year
		if (today.month, today.day) < (self.dateOfBirth.month, self.dateOfBirth.day):
			age -= 1
		return age

	@property
	def currentLocation(self):
		"""Returns the patient's current location (latest place marked as current)."""
		return self.places.filter(isCurrent=True).first()

	@property
	def latestLocation(self):
		"""Returns the patient's most recent visited location."""
		return self.places.first()  # Already ordered by -visitedAt

