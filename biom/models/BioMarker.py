from django.db import models
from django_mongodb_backend.fields import ObjectIdField

__all__ = ['BioMarker']


class BioMarker(models.Model):
    name = models.CharField(max_length=255)
    shortName = models.CharField(max_length=100, blank=True, null=True)
    commonName = models.CharField(max_length=255, blank=True, null=True)
    uniProtKB = models.CharField(max_length=100, blank=True, null=True)
    pdb = models.CharField(max_length=100, blank=True, null=True)
    molecularWeight = models.FloatField(blank=True, null=True)
    molecularLength = models.IntegerField(blank=True, null=True)
    aaSequence = models.CharField(max_length=4096, blank=True, null=True)
    status = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    biomType = models.CharField(max_length=50)
    uploadedBy = ObjectIdField(blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=0, db_column='__v')
    imagePath = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'bioMarker'
        managed = False
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['type']),
            models.Index(fields=['biomType']),
        ]

    def __str__(self):
        return self.name
