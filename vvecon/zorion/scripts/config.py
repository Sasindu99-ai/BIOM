import os
from pathlib import Path

import django

__all__ = ['config']


def config(BASE_PATH: Path | str):
	os.environ.setdefault('DJANGO_SETTINGS_BASE_PATH', str(BASE_PATH))
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vvecon.zorion.app.settings')
	django.setup()
