from django.db import models
from django_mongodb_backend.fields import ArrayField, ObjectIdField

__all__ = ['Study']

class Study(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=2048, blank=True, null=True)
    status = models.CharField(max_length=50)
    category = models.CharField(max_length=100)
    createdBy = ObjectIdField(blank=True, null=True)
    members = ArrayField(
        ObjectIdField(),
        blank=True,
        null=True,
    )
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    version = models.IntegerField(default=0, db_column='__v')

    class Meta:
        db_table = 'study'
        managed = False
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]
