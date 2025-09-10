from django.contrib.auth.models import Permission
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..models import User

__all__ = ['userAccountCreated']


@receiver(post_save, sender=User, dispatch_uid='user_account_created_signal')
def userAccountCreated(sender, instance, created, **kwargs):  # noqa: ARG001
	if not created:
		return

	if not instance.has_perm('authentication.login_user'):
		permissions = ['login_user', 'view_profile', 'change_profile', 'delete_profile']
		for permission in permissions:
			instance.user_permissions.add(Permission.objects.get(codename=permission))
		instance.save()
