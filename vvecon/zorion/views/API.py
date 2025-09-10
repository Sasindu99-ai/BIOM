import inspect
from functools import wraps
from typing import ClassVar

from django.urls import path as django_path
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from ..enums import Method
from ..utils import Utils

__all__ = ['API']


class API:
	exclude: ClassVar = ['generateURLPatterns', 'callAPI', 'getRequestParser', 'getPermissions']
	views: ClassVar = dict()
	permissions: ClassVar = dict()
	base: str = ''

	@classmethod
	def getRequestParser(cls, params) -> type[Serializer] | None:
		for value in params.values():
			if issubclass(value.annotation, (Serializer, ModelSerializer)):
				return value.annotation
		return None

	def callAPI(self, func, method):

		@wraps(func)
		def viewFunc(viewSelf, request, *args, **kwargs):  # noqa: ARG001
			params = inspect.signature(func).parameters
			if len(params) > 0:
				requestParser = self.getRequestParser(params)
				if requestParser is not None and issubclass(requestParser, (Serializer, ModelSerializer)):
					data = request.GET if method == Method.GET else request.data
					many = isinstance(data, list)
					parser = requestParser(data=data, many=many)
					if parser.is_valid(raise_exception=False):
						pass
					if not many:
						for key, value in parser.validated_data.items():
							setattr(parser, key, value)
					if 'request' in params:
						return func(*args, data=parser, request=request, **kwargs)
					return func(*args, data=parser, request=request, **kwargs)
				if 'request' in params:
					return func(*args, request=request, **kwargs)
				try:
					return func(*args, request=request, **kwargs)
				except TypeError:
					return func(*args, **kwargs)
			return func(*args, **kwargs)
		return viewFunc

	def getPermissions(self, className: str, request) -> list:
		"""
		Get the permissions for the class
		:param className: class name
		:param request: request
		:return: permissions
		"""
		if className in self.permissions and request.method.lower() in self.permissions[className]:
			return self.permissions[className][request.method.lower()]
		return []

	def generateURLPatterns(self, app_name: str = NotImplemented):
		self.views = dict()
		funcs = [
			func for func in dir(self)
			if callable(getattr(self, func)) and not func.startswith('__') and func not in self.exclude
		]

		for fn in funcs:
			func = getattr(self, fn)
			if hasattr(func, 'method') and hasattr(func, 'path'):
				# Extract method and path from function
				method = func.method
				path = func.path
				authorized = getattr(func, 'authorized', False)

				# Create view class if not already in views
				if path not in self.views:
					self.views[path] = type(
						Utils.urlToClassName(path), (APIView,), {
							'authentication_classes': [
								*api_settings.DEFAULT_AUTHENTICATION_CLASSES,
								SessionAuthentication,
								TokenAuthentication,
							],
							'get_permissions':
								lambda viewSelf, path=path: self.getPermissions(
									Utils.urlToClassName(path), viewSelf.request,
								),
						},
					)
					self.permissions[Utils.urlToClassName(path)] = dict()
				permissions = self.permissions[Utils.urlToClassName(path)].get(method.name.lower(), [])
				if authorized:
					permissions.append(IsAuthenticated())
				else:
					permissions.append(AllowAny())
				self.permissions[Utils.urlToClassName(path)][method.name.lower()] = permissions

				setattr(self.views[path], method.name.lower(), self.callAPI(func, method))
		# generate urls from views
		return [
			django_path(
				self.base + url,
				view.as_view(),
				name=Utils.urlName((app_name + ':' if app_name is not NotImplemented else '') + self.base + url),
			) for url, view in self.views.items()
		]
