from django.apps import AppConfig
from django.core.signals import request_started

from vvecon.zorion.logger import Logger

__all__ = ['MainConfig']


def _pause_orphaned_jobs(**kwargs):  # noqa: ARG001
	"""
	A DataImportJob left 'RUNNING' when the process exits (crash, restart,
	deploy) can never be resumed — start_job() only accepts PENDING/PAUSED —
	and its worker thread (tracked only in that process's memory) is gone.
	Pause orphaned jobs once the application has finished initializing and
	starts serving requests, avoiding database access during AppConfig.ready().
	"""
	try:
		from .models import DataImportJob  # noqa: PLC0415

		count = DataImportJob.objects.filter(status='RUNNING').update(
			status='PAUSED',
			paused_reason='server_restart',
		)
		if count > 0:
			Logger.info(f'Paused {count} orphaned DataImportJob(s) after server restart')
	except Exception:
		Logger.exception('Error pausing orphaned DataImportJob')
	finally:
		request_started.disconnect(dispatch_uid='pause_orphaned_import_jobs')


class MainConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'main'

	def ready(self):
		request_started.connect(
			_pause_orphaned_jobs,
			dispatch_uid='pause_orphaned_import_jobs',
		)
