from django.db import models
from django.utils import timezone

from .Manager import Manager, SoftManager
from .query import QuerySet

__all__ = ['Model']


class Model(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	deleted_at = models.DateTimeField(null=True, blank=True)

	objects = SoftManager()
	all_objects = Manager()

	class Meta:
		abstract = True

	def __repr__(self):
		return f'<{self.__class__.__name__}: {self.__str__()}>'

	def __str__(self):
		return f'{self.pk}'

	def delete(self, *, using=None, keep_parents=False):
		self.deleted_at = timezone.now()
		self.save()

		# Handle cascading soft deletes
		for related in self._meta.related_objects:
			if related.on_delete == models.CASCADE:
				related_objects = getattr(self, related.get_accessor_name()).all()
				for rel_obj in related_objects:
					if isinstance(rel_obj, QuerySet):
						rel_obj.delete()
					else:
						rel_obj.delete()

	def hard_delete(self):
		# Perform hard delete
		super().delete()
