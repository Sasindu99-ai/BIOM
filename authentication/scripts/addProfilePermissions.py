from pathlib import Path

from vvecon.zorion.logger import Logger
from vvecon.zorion.scripts import config

config(Path(__file__).resolve().parent.parent.parent)


def addProfilePermissions():
	from django.contrib.auth.models import Permission
	from django.contrib.contenttypes.models import ContentType

	permissions = [
		dict(codename='login_user', name='Can login into their account'),
		dict(codename='view_profile', name='Can view their own user account'),
		dict(codename='change_profile', name='Can change their user account'),
		dict(codename='delete_profile', name='Can delete their user account'),
	]

	contentType = ContentType.objects.filter(app_label='authentication', model='user').first()
	for permission in permissions:
		Logger.info(f'Adding permission {permission.get("codename")}')
		if Permission.objects.filter(codename=permission.get('codename')).exists():
			Logger.info(f'Permission {permission.get("codename")} already exists')
			continue
		Permission(**permission, content_type=contentType).save()
		Logger.info(f'Permission {permission.get("codename")} added')


if __name__ == '__main__':
	addProfilePermissions()
