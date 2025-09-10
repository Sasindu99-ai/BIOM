from typing import Any, ClassVar

from rest_framework import serializers
from rest_framework.response import Response as APIResponse
from rest_framework.status import HTTP_200_OK

__all__ = ['ModelResponse']


class ModelResponse:
	"""
	ModelResponse(data: Any = None, *args, raise_exception: bool = False, **kwargs)
	"""
	__raise_exception = False
	__exclude: ClassVar = [
		'model', 'fields', 'serializer', 'status', 'data', 'is_valid', '_exclude', 'json', 'errors', '_data',
		'__init__', '__raise_exception', '__object',
	]
	__args: tuple = tuple()
	__kwargs: ClassVar = {}

	def __init__(self, data: Any = None, *args, raise_exception=False, **kwargs):
		self.__pureData = data
		self.__data = data if kwargs.get('many', False) or data is None else data.__dict__
		self.__raise_exception = raise_exception
		self.__args = args
		self.__kwargs = kwargs

		# Get model and fields from class attributes
		model = self.__class__.__dict__.get('model')
		fields = self.__class__.__dict__.get('fields')

		if model is None or fields is None:
			error_msg = 'Model and fields must be defined in the subclass.'
			raise ValueError(error_msg)

		methods: dict = {}

		serializer_fields = {
			attr: value
			for attr, value in self.__class__.__dict__.items()
			if attr not in self.__exclude and not attr.startswith('__')
		}

		# Define the serializer class dynamically using type
		DynamicModelSerializer = type(
			self.__class__.__name__, (serializers.ModelSerializer,), {
				'Meta': type('Meta', (), {
					'model': model,
					'fields': fields,
				}),
				**serializer_fields, 'to_representation': self._create_to_representation_method(methods),
			},
		)

		self.__object = DynamicModelSerializer

		self.serializer = DynamicModelSerializer(*args, data=self.__data, **kwargs)
		if self.serializer.is_valid(raise_exception=raise_exception):
			pass

	def validate(self, attrs):
		return attrs

	def is_valid(self, raise_exception=None):
		if raise_exception is None:
			raise_exception = self.__raise_exception
		return self.serializer.is_valid(raise_exception=raise_exception)

	def json(self, status=HTTP_200_OK, raise_exception=None):
		if raise_exception is None:
			raise_exception = self.__raise_exception
		if self.is_valid(raise_exception=raise_exception):
			pass
		try:
			self.serializer = self.__object(*self.__args, data=self.__pureData, **self.__kwargs)
			if self.serializer.is_valid(raise_exception=raise_exception):
				pass
			if (
				isinstance(self.errors, dict)
				and next(iter(self.errors.values()))[0].code == 'invalid'
				and ('many' not in self.__kwargs or not self.__kwargs['many'])
			):
				self.serializer = self.__object(*self.__args, data=[self.__pureData], many=True, **self.__kwargs)
				if self.serializer.is_valid(raise_exception=raise_exception):
					return APIResponse(
						self.serializer.validated_data[0] if raise_exception else self.serializer.data[0],
						status=status,
					)
		except IndexError:
			self.serializer = self.__object(*self.__args, data=self.__data, **self.__kwargs)
			if self.is_valid(raise_exception=raise_exception):
				pass
		return APIResponse(self.serializer.validated_data if raise_exception else self.serializer.data, status=status)

	@property
	def initial_data(self):
		return self.serializer.initial_data

	@property
	def data(self):
		return self.serializer.data

	@property
	def validated_data(self):
		return self.serializer.validated_data

	@property
	def errors(self):
		return self.serializer.errors

	def _create_to_representation_method(self, methods):

		def to_representation(self, instance):
			representation = super(self.__class__, self).to_representation(instance)
			for method_name, method in methods.items():
				field_name = method_name[len('get_'):]
				representation[field_name] = method(self, instance)
			return representation

		return to_representation

	@property
	def response(self):
		return self.__object

	def getData(self, raise_exception=None):
		if raise_exception is None:
			raise_exception = self.__raise_exception
		if self.is_valid(raise_exception=raise_exception):
			pass
		return self.validated_data if raise_exception else self.data

	def to_representation(self, instance):
		return self.serializer.to_representation(instance)
