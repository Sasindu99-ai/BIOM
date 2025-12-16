from django.db import models

__all__ = ['Counters']


class Counters(models.Model):
    version = models.IntegerField(default=0, db_column='__v')
    seq = models.IntegerField(default=0)

    class Meta:
        db_table = 'counters'
        managed = False
