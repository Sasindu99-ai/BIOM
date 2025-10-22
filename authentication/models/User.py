from typing import ClassVar

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Group, Permission, PermissionsMixin
from django.db import models
from django.db.models.functions import Concat

from settings.models import Country

from ..managers import UserManager

__all__ = ['User']


class User(AbstractBaseUser, PermissionsMixin):
	profile = models.ImageField(
		upload_to='profiles/', verbose_name='Profile Picture', blank=True, null=True,
	)
	countryCode = models.CharField(
		max_length=5, verbose_name='Country Code', blank=True,
	)
	mobileNumber = models.IntegerField(
		verbose_name='Mobile Number', null=True, blank=True,
	)
	firstName = models.CharField(
		max_length=50, verbose_name='First Name', blank=True,
	)
	lastName = models.CharField(
		max_length=50, verbose_name='Last Name', blank=True,
	)
	email = models.EmailField(
		blank=True, null=True, verbose_name='Email Address', unique=True,
	)
	nic = models.CharField(
		max_length=20, blank=True, verbose_name='NIC Number',
	)
	dateOfBirth = models.DateField(blank=True, null=True, verbose_name='Date of Birth')
	is_active = models.BooleanField(default=True, verbose_name='Active')
	is_superuser = models.BooleanField(default=False, verbose_name='Superuser')
	is_staff = models.BooleanField(default=False, verbose_name='Staff')
	date_joined = models.DateTimeField(auto_now_add=True, verbose_name='Date Joined')
	last_login = models.DateTimeField(auto_now=True, verbose_name='Last Login')
	country = models.ForeignKey(
		Country,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		verbose_name='Country',
	)
	username = models.CharField(
		max_length=150, verbose_name='Username', unique=True,
	)
	fullName = models.GeneratedField(
		verbose_name='Full Name', editable=False, db_persist=True,
		expression=Concat(
			models.F('firstName'),
			models.Value(' '),
			models.F('lastName'),
		),
		output_field=models.CharField(max_length=101),
	)

	groups = models.ManyToManyField(
		Group,
		related_name='authentication_user_groups',
		verbose_name='groups',
		blank=True,
		help_text=(
			'The groups this user belongs to. A user will get all permissions '
			'granted to each of their groups.'
		),
		related_query_name='user',
	)
	user_permissions = models.ManyToManyField(
		Permission,
		related_name='authentication_user_user_permissions',
		verbose_name='user permissions',
		blank=True,
		help_text='Specific permissions for this user.',
		related_query_name='user',
	)

	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS: ClassVar = ['firstName', 'lastName']

	objects = UserManager()

	def __str__(self):
		if self.fullName:
			return self.fullName
		if self.email:
			return self.email
		if self.countryCode and self.mobileNumber:
			return f'+{self.countryCode}{self.mobileNumber}'
		return self.username
