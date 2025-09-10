import os
from pathlib import Path

import django

from .TestCase import TestCase


def _getAppsPath(path: Path) -> Path:
    """
	Get apps path
	:param path: Path
	:type path: Path
	:return: Apps path
	"""
    if path.parent.name == 'apps':
        return path.parent
    return _getAppsPath(path.parent)


_apps: Path = _getAppsPath(Path(os.environ.get('PWD', './')).resolve())
os.environ.setdefault('DJANGO_SETTINGS_BASE_PATH', str(_apps.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vvecon.zorion.app.settings')

django.setup()

__all__ = ['TestCase']
