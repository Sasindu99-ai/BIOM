from typing import ClassVar

from vvecon.zorion.db import models

__all__ = ['Publication']


class Publication(models.Model):
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500)
    journal = models.CharField(max_length=255, blank=True, default='')
    year = models.IntegerField(default=2026)
    doi = models.CharField(max_length=255, blank=True, default='')
    url = models.URLField(blank=True, default='')
    abstract = models.TextField(blank=True, default='')
    citation_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'settings_publications'
        ordering: ClassVar = ['order', '-year', 'title']

    def __str__(self):
        return f'{self.title} ({self.year})'
