from vvecon.zorion.db import models

__all__ = ['Place']


class Place(models.Model):
    name = models.CharField(max_length=255, verbose_name='Name')
    placeId = models.CharField(max_length=255, verbose_name='Place ID')
    latitude = models.FloatField(verbose_name='Latitude')
    longitude = models.FloatField(verbose_name='Longitude')

    def __str__(self):
        return self.place

    @property
    def place(self):
        return self.name.split(',')[0].strip()
