import uuid

from vvecon.zorion.db import models

from .User import User

__all__ = ['Channel']


class Channel(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Channel Name')
    description = models.TextField(null=True, blank=True, verbose_name='Description')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channels', verbose_name='Owner')
    publicId = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='Public ID')
    s3FolderPath = models.CharField(max_length=255, null=True, blank=True, verbose_name='S3 Folder Path')
    isActive = models.BooleanField(default=True, verbose_name='Is Active')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Channel'
        verbose_name_plural = 'Channels'
        ordering = ('-created_at', )
