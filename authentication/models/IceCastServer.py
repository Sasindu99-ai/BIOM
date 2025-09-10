from vvecon.zorion.db import models

from .Channel import Channel

__all__ = ['IceCastServer']


class IceCastServer(models.Model):
	channel = models.ForeignKey(
		Channel, on_delete=models.CASCADE, related_name='icecast_servers', verbose_name='Channel',
	)
	icecastMountPoint = models.CharField(max_length=255, unique=True, verbose_name='Icecast Mount Point')
	icecastPassword = models.CharField(max_length=255, verbose_name='Icecast Password')
	isActive = models.BooleanField(default=False, verbose_name='Is Active')
	isSecret = models.BooleanField(default=False, verbose_name='Is Secret')
	host = models.CharField(max_length=255, verbose_name='Host')
	port = models.PositiveIntegerField(verbose_name='Port')
	username = models.CharField(max_length=255, verbose_name='Username')
	password = models.CharField(max_length=255, verbose_name='Password')
