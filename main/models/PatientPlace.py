from settings.models import Place
from vvecon.zorion.db import models

__all__ = ['PatientPlace']


class PatientPlace(models.Model):
	"""Tracks location history for a patient."""
	patient = models.ForeignKey(
		'main.Patient', on_delete=models.CASCADE, related_name='places',
	)
	place = models.ForeignKey(
		Place, on_delete=models.CASCADE, related_name='patientPlaces',
	)
	visitedAt = models.DateTimeField(auto_now_add=True, verbose_name='Visited At')
	notes = models.TextField(blank=True, null=True)
	isCurrent = models.BooleanField(default=False, verbose_name='Is Current Location')

	class Meta:
		ordering = ['-visitedAt']
		verbose_name = 'Patient Place'
		verbose_name_plural = 'Patient Places'

	def __str__(self):
		return f'{self.patient} - {self.place}'

	def save(self, *args, **kwargs):
		# If this is marked as current, unset others for this patient
		if self.isCurrent:
			PatientPlace.objects.filter(patient=self.patient, isCurrent=True).update(isCurrent=False)
		super().save(*args, **kwargs)
