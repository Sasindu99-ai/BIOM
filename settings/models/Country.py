from vvecon.zorion.db import models

__all__ = ['Country']


class Country(models.Model):
    name = models.CharField(max_length=50, verbose_name='Country Name')
    code = models.CharField(max_length=20, verbose_name='Country Code')
    flag = models.URLField(verbose_name='Flag URL', default='', blank=True, null=True)
    length = models.IntegerField(verbose_name='Mobile Number Length', default=0)
    emoji = models.CharField(max_length=10, verbose_name='Flag Emoji', default='🏳️')

    def __str__(self):
        return self.name
