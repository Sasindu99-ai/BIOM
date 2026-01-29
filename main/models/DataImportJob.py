from authentication.models import User
from vvecon.zorion.db import models

from .Study import Study

__all__ = ['DataImportJob']


class DataImportJobStatus(models.TextChoices):
	PENDING = 'PENDING', 'Pending'
	RUNNING = 'RUNNING', 'Running'
	PAUSED = 'PAUSED', 'Paused'
	COMPLETED = 'COMPLETED', 'Completed'
	FAILED = 'FAILED', 'Failed'
	CANCELLED = 'CANCELLED', 'Cancelled'


class DataImportJob(models.Model):
	"""Tracks background data import jobs with pause/resume capability."""

	study = models.ForeignKey(
		Study, on_delete=models.CASCADE, related_name='importJobs',
		verbose_name='Study/Dataset',
	)
	status = models.CharField(
		max_length=20, choices=DataImportJobStatus.choices,
		default=DataImportJobStatus.PENDING, db_index=True,
	)

	# File information
	file_url = models.CharField(max_length=500, verbose_name='File URL')
	file_name = models.CharField(max_length=255, verbose_name='Original Filename')

	# Import configuration (stored as JSON)
	mapping = models.JSONField(default=dict, verbose_name='Column Mapping')
	column_types = models.JSONField(default=dict, verbose_name='Column Types')

	# Progress tracking
	total_rows = models.IntegerField(default=0, verbose_name='Total Rows')
	processed_rows = models.IntegerField(default=0, verbose_name='Processed Rows')
	imported_count = models.IntegerField(default=0, verbose_name='Imported Count')
	updated_count = models.IntegerField(default=0, verbose_name='Updated Count')
	skipped_count = models.IntegerField(default=0, verbose_name='Skipped Count')
	error_count = models.IntegerField(default=0, verbose_name='Error Count')
	consecutive_errors = models.IntegerField(default=0, verbose_name='Consecutive Errors')
	patients_created = models.IntegerField(default=0, verbose_name='Patients Created')
	variables_created = models.IntegerField(default=0, verbose_name='Variables Created')

	# Error details
	errors = models.JSONField(default=list, verbose_name='Error Details')

	# Timestamps and ownership
	created_by = models.ForeignKey(
		User, on_delete=models.SET_NULL, null=True, blank=True,
		related_name='dataImportJobs', verbose_name='Created By',
	)
	started_at = models.DateTimeField(null=True, blank=True, verbose_name='Started At')
	completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completed At')
	paused_reason = models.CharField(
		max_length=50, null=True, blank=True,
		verbose_name='Pause Reason',
		help_text='manual, consecutive_errors, or server_restart',
	)

	# Django-Q task tracking
	task_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='Task ID')

	class Meta:
		ordering = ['-created_at']
		verbose_name = 'Data Import Job'
		verbose_name_plural = 'Data Import Jobs'
		indexes = [
			models.Index(fields=['study', 'status']),
			models.Index(fields=['created_by', 'status']),
		]

	def __str__(self):
		return f'Import #{self.pk} - {self.study.name} ({self.status})'

	@property
	def progress_percent(self) -> int:
		if self.total_rows == 0:
			return 0
		return min(100, int((self.processed_rows / self.total_rows) * 100))

	@property
	def is_active(self) -> bool:
		return self.status in (DataImportJobStatus.PENDING, DataImportJobStatus.RUNNING)

	@property
	def can_resume(self) -> bool:
		return self.status == DataImportJobStatus.PAUSED

	@property
	def can_pause(self) -> bool:
		return self.status == DataImportJobStatus.RUNNING
