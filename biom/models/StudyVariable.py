from django.db import models
from django_mongodb_backend.fields import ArrayField, ObjectIdField

__all__ = ['StudyVariable']


class StudyVariable(models.Model):
    name = models.CharField(max_length=255)
    notes = models.CharField(max_length=1024, blank=True, null=True)
    type = models.CharField(max_length=100)
    answerOptions = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=50)
    isSearchable = models.BooleanField(default=False)
    isRange = models.BooleanField(default=False)
    isUnique = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    study = ObjectIdField(blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=0, db_column='__v')

    class Meta:
        db_table = 'studyVariable'
        managed = False
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['type']),
            models.Index(fields=['study']),
        ]

    def __str__(self):
        return self.name
