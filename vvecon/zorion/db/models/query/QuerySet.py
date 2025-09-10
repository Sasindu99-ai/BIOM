from django.db import models
from django.utils import timezone

__all__ = ['QuerySet']


class QuerySet(models.QuerySet):

    def delete(self):
        for obj in self:
            obj.delete()
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.exclude(deleted_at__isnull=True)
