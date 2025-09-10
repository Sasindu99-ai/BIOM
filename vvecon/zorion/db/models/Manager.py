from django.db import models

__all__ = ['Manager', 'SoftManager']


class SoftManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def all_objects(self):
        return super().get_queryset()

    def deleted_objects(self):
        return super().get_queryset().filter(deleted_at__isnull=False)


class Manager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def all_objects(self):
        return super().get_queryset()

    def deleted_objects(self):
        return super().get_queryset().filter(deleted_at__isnull=False)

    def hard_delete(self):
        return super().get_queryset().hard_delete()

    def delete(self):
        return super().get_queryset().delete()
