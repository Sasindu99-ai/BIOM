from typing import ClassVar

from vvecon.zorion.db import models

__all__ = ['Currency']


class Currency(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Currency Name')
    code = models.CharField(max_length=3, verbose_name='Currency Code')
    symbol = models.CharField(max_length=3, verbose_name='Currency Symbol')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1, verbose_name='Exchange Rate')
    is_default = models.BooleanField(default=False, verbose_name='Default Currency')
    is_active = models.BooleanField(default=False, verbose_name='Active')
    is_featured = models.BooleanField(default=False, verbose_name='Featured')

    class Meta:
        db_table = 'settings_currencies'
        ordering: ClassVar = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            currentDefault = Currency.objects.filter(is_default=True).first()
            if currentDefault and currentDefault != self:
                currentDefault.is_default = False
                currentDefault.save()
        if self.is_active:
            currentActive = Currency.objects.filter(is_active=True).first()
            if currentActive and currentActive != self:
                currentActive.is_active = False
                currentActive.save()
        super(Currency, self).save(*args, **kwargs)
