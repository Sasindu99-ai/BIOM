import datetime
from typing import ClassVar

from django.utils import timezone
from rest_framework import authentication, exceptions

from ..models import ApiKey

__all__ = ['ApiKeyAuthentication']


class ApiKeyAuthentication(authentication.BaseAuthentication):
	"""
	Custom authentication provider for Django REST Framework using personal API keys.

	Accepts API keys in either:
	- 'X-API-Key: biom_live_...' header
	- 'Authorization: Api-Key biom_live_...' header
	- 'Authorization: Bearer biom_live_...' header
	"""

	HEADER_KEY: ClassVar[str] = 'HTTP_X_API_KEY'
	AUTH_HEADER_PREFIXES: ClassVar[tuple[str, ...]] = ('api-key', 'bearer')

	def authenticate(self, request):
		raw_key = self.extract_api_key(request)
		if not raw_key:
			return None

		key_hash = ApiKey.hash_key(raw_key)

		api_key = (
			ApiKey.objects
			.select_related('user')
			.filter(key_hash=key_hash, is_active=True, revoked_at__isnull=True)
			.first()
		)

		if not api_key:
			raise exceptions.AuthenticationFailed('Invalid or revoked API key')

		user = api_key.user
		if not user or not user.is_active:
			raise exceptions.AuthenticationFailed('User account is inactive or disabled')

		if not (user.is_staff or user.is_superuser):
			raise exceptions.AuthenticationFailed(
				'API key user is not authorized (staff or superadmin required)',
			)

		# Throttled update of last_used_at (once per minute) to minimize DB write pressure
		now = timezone.now()
		if not api_key.last_used_at or (now - api_key.last_used_at) > datetime.timedelta(minutes=1):
			api_key.last_used_at = now
			api_key.save(update_fields=['last_used_at'])

		return (user, api_key)

	def extract_api_key(self, request) -> str | None:
		# 1. Check custom X-API-Key header
		if self.HEADER_KEY in request.META:
			raw = request.META[self.HEADER_KEY]
			if raw:
				return raw.strip()

		# 2. Check Authorization header
		auth_header = request.META.get('HTTP_AUTHORIZATION')
		if auth_header:
			parts = auth_header.strip().split()
			if len(parts) == 2 and parts[0].lower() in self.AUTH_HEADER_PREFIXES:
				return parts[1].strip()

		return None

	def authenticate_header(self, request) -> str:
		return 'Api-Key realm="BIOM API"'
