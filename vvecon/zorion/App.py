import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application
from django.core.wsgi import get_wsgi_application

__all__ = ['App']


class App:
	BASE_PATH: Path

	def __init__(self, base_path: Path):
		self.BASE_PATH = base_path

	def run(self):
		os.environ.setdefault('DJANGO_SETTINGS_BASE_PATH', str(self.BASE_PATH))
		"""Run administrative tasks."""
		os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vvecon.zorion.app.settings')
		try:
			from django.core.management import execute_from_command_line
		except ImportError as exc:
			importErrorMsg = "Couldn't import Django. Are you sure it's installed and "
			'available on your PYTHONPATH environment variable? Did you '
			'forget to activate a virtual environment?'
			raise ImportError(importErrorMsg) from exc
		execute_from_command_line(sys.argv)

	@classmethod
	def asgi(cls):
		os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vvecon.zorion.app.settings')
		return get_asgi_application()

	@classmethod
	def wsgi(cls):
		os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vvecon.zorion.app.settings')
		return get_wsgi_application()
