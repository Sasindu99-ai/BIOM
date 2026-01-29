from django.db import models

__all__ = ['User']


class User(models.Model):
	name = models.CharField(max_length=255)
	email = models.CharField(max_length=255, unique=True)
	userType = models.CharField(max_length=50)
	uid = models.CharField(max_length=255, unique=True)
	createdAt = models.DateTimeField(auto_now_add=True)
	updatedAt = models.DateTimeField(auto_now=True)
	version = models.IntegerField(default=0, db_column='__v')
	userId = models.IntegerField(blank=True, null=True, verbose_name='User ID')

	class Meta:
		db_table = 'user'
		managed = False
		indexes = [
			models.Index(fields=['email']),
			models.Index(fields=['uid']),
			models.Index(fields=['userType']),
		]

	def __str__(self):
		return self.name
