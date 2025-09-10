from typing import Any, ClassVar

from rest_framework import serializers
from rest_framework.response import Response as APIResponse

__all__ = ['Response']


class Response:
	__raise_exception = False
	__exclude: ClassVar = [
		'serializer', 'status', 'data', 'is_valid', '_exclude', 'json', 'errors', '_data', '__init__',
		'__raise_exception',
	]

	def __init__(self, data: Any = None, *args, raise_exception=False, **kwargs):
		self.__data = data
		self.__raise_exception = raise_exception

		serializer_fields = {
			attr: value
			for attr, value in self.__class__.__dict__.items()
			if attr not in self.__exclude and not callable(value) and not attr.startswith('__')
		}

		self.serializer = type('DynamicSerializer', (serializers.Serializer,), serializer_fields)

		self.serializer = self.serializer(*args, data=self.__data, **kwargs)

	def validate(self, attrs):
		return attrs

	def is_valid(self, raise_exception=None):
		if raise_exception is None:
			raise_exception = self.__raise_exception
		return self.serializer.is_valid(raise_exception=raise_exception)

	def json(self, status=200, raise_exception=None):
		if raise_exception is None:
			raise_exception = self.__raise_exception
		if self.is_valid(raise_exception=raise_exception):
			pass
		return APIResponse(self.serializer.validated_data if raise_exception else self.serializer.data, status=status)

	@property
	def data(self):
		return self.serializer.data

	@property
	def errors(self):
		return self.serializer.errors
