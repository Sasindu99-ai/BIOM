from typing import ClassVar

from vvecon.zorion.db import models

__all__ = ['TeamMember']


class TeamMember(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    affiliation = models.CharField(max_length=255, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    avatar = models.CharField(max_length=500, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    orcid_url = models.URLField(blank=True, default='')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'settings_team_members'
        ordering: ClassVar = ['order', 'name']

    def __str__(self):
        return f'{self.name} ({self.role})'
