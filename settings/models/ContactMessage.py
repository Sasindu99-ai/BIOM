from typing import ClassVar

from vvecon.zorion.db import models

__all__ = ['ContactMessage']


class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'settings_contact_messages'
        ordering: ClassVar = ['-created_at']

    def __str__(self):
        return f'[{self.email}] {self.subject}'
