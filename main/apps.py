from django.apps import AppConfig

__all__ = ['MainConfig']

from vvecon.zorion.logger import Logger


class MainConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'main'

	def ready(self):
		# A DataImportJob left 'RUNNING' when the process exits (crash, restart,
		# deploy) can never be resumed — start_job() only accepts PENDING/PAUSED —
		# and its worker thread (tracked only in that process's memory) is gone.
		# On every fresh process start, no such thread can still be alive, so any
		# 'RUNNING' job at this point is necessarily orphaned; pause it so it's
		# resumable instead of stuck forever.
		try:
			from .models import DataImportJob  # noqa: PLC0415
			DataImportJob.objects.filter(status='RUNNING').update(
				status='PAUSED',
				paused_reason='server_restart',
			)
		except Exception:
			Logger.exception('Error pausing orphaned DataImportJob')
