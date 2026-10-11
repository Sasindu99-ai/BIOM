from typing import ClassVar

from vvecon.zorion.db import models

__all__ = ['ResearchTool']


class ResearchTool(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, default='General')
    summary = models.CharField(max_length=500)
    description = models.TextField(blank=True, default='')
    url = models.CharField(max_length=500)
    badge = models.CharField(max_length=50, blank=True, default='')
    icon = models.CharField(max_length=100, default='ph-gear')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'settings_research_tools'
        ordering: ClassVar = ['order', 'name']

    def __str__(self):
        return f'{self.name} [{self.category}]'
