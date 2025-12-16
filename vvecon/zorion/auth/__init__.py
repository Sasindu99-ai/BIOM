import inspect
from functools import wraps
from os import environ

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import resolve
from rest_framework import status
from rest_framework.response import Response

from .JWTProvider import JWTProvider

__all__ = ['Authenticated', 'Authorized', 'JWTProvider']


def Authorize(
	authorized: bool | None = None, staff: bool = False, admin: bool = False, permissions: list[str] | None = None,  # noqa: FBT002, FBT001
):

	def Auth(func):
		sig = inspect.signature(func)
		params = list(sig.parameters.values())

		@wraps(func)
		def wrapper(self, *args, **kwargs):
			unAuthErrorMsg = 'Unauthorized'

			request = kwargs.get('request')
			if (request is None and authorized) or (not request.user.is_authenticated and authorized):
				return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
			if authorized:
				if not (
					(staff and request.user.is_staff) or (admin and request.user.is_superuser) or (
					not staff and not admin)
				):
					raise PermissionDenied(unAuthErrorMsg)
				if not admin and not request.user.has_perms(permissions if permissions is not None else []):
						raise PermissionDenied(unAuthErrorMsg)
			parameters = inspect.signature(func).parameters
			if 'request' in parameters:
				return func(self, *args, **kwargs)
			kwargs.pop('request')
			return func(self, *args, **kwargs)

		if 'request' not in [param.name for param in params]:
			params.append(inspect.Parameter('request', inspect.Parameter.POSITIONAL_OR_KEYWORD))
		if hasattr(wrapper, '__signature__'):
			wrapper.__signature__ = sig.replace(parameters=params)
		return wrapper

	return Auth


def Authenticate(staff=False, admin=False, permissions: list[str] | None = None):  # noqa: FBT002
	if permissions is None:
		permissions = []

	def Auth(func):
		sig = inspect.signature(func)
		params = list(sig.parameters.values())

		@wraps(func)
		def wrapper(self, *args, **kwargs):
			unAuthErrorMsg = 'Unauthorized'

			request = kwargs.get('request')
			if request is None:
				unAuthErrorMsg = 'Unauthorized'
				raise PermissionDenied(unAuthErrorMsg)
			if not request.user.is_authenticated:
				return redirect(
					f'/{environ.get('AUTH_ADMIN_URL')}/'
					if request.path.startswith(f'/{environ.get('ADMIN_PATH', 'admin')}/')
					else f'/{environ.get('AUTH_URL')}/',
				)
			if not (
				(staff and request.user.is_staff) or (admin and request.user.is_superuser) or (not staff and not admin)
			):
				raise PermissionDenied(unAuthErrorMsg)
			if not admin and not request.user.has_perms(permissions):
					raise PermissionDenied(unAuthErrorMsg)
			parameters = inspect.signature(func).parameters
			if 'request' in parameters:
				return func(self, *args, **kwargs)
			kwargs.pop('request')
			return func(self, *args, **kwargs)

		if 'request' not in [param.name for param in params]:
			params.append(inspect.Parameter('request', inspect.Parameter.POSITIONAL_OR_KEYWORD))
		wrapper.__signature__ = sig.replace(parameters=params)
		return wrapper

	return Auth


Authorized = Authorize
Authenticated = Authenticate
