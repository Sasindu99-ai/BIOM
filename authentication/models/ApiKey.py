import hashlib
import secrets
from typing import ClassVar

from django.conf import settings
from django.db import models
from django.utils import timezone

__all__ = ['ApiKey']


class ApiKey(models.Model):
	PREFIX: ClassVar[str] = 'biom_live_'

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='api_keys',
		verbose_name='User',
	)
	name = models.CharField(
		max_length=100, default='Default API Key', verbose_name='Key Name',
	)
	key_prefix = models.CharField(
		max_length=16, verbose_name='Key Prefix',
	)
	key_hash = models.CharField(
		max_length=64, unique=True, db_index=True, verbose_name='Key Hash (SHA-256)',
	)
	created_at = models.DateTimeField(
		auto_now_add=True, verbose_name='Created At',
	)
	last_used_at = models.DateTimeField(
		null=True, blank=True, verbose_name='Last Used At',
	)
	revoked_at = models.DateTimeField(
		null=True, blank=True, verbose_name='Revoked At',
	)
	is_active = models.BooleanField(
		default=True, verbose_name='Is Active',
	)

	class Meta:
		verbose_name = 'API Key'
		verbose_name_plural = 'API Keys'
		ordering = ['-created_at']

	def __str__(self) -> str:
		status = 'Active' if self.is_active else 'Revoked'
		return f'{self.user.username} - {self.key_prefix} ({status})'

	@classmethod
	def hash_key(cls, raw_key: str) -> str:
		return hashlib.sha256(raw_key.strip().encode('utf-8')).hexdigest()

	@classmethod
	def generate_token(cls) -> tuple[str, str, str]:
		"""
		Generates a new secure random token.
		Returns (raw_key, key_prefix, key_hash).
		The raw_key should be displayed to the user once and never stored.
		"""
		random_bytes = secrets.token_hex(20)
		raw_key = f'{cls.PREFIX}{random_bytes}'
		key_prefix = raw_key[:14] + '...'
		key_hash = cls.hash_key(raw_key)
		return raw_key, key_prefix, key_hash

	@classmethod
	def create_key_for_user(cls, user, name: str = 'Default API Key') -> tuple['ApiKey', str]:
		"""
		Creates a new active API key for the user, rotating/deactivating previous active keys.
		Returns the ApiKey instance and the one-time raw plaintext key string.
		"""
		cls.objects.filter(user=user, is_active=True).update(
			is_active=False,
			revoked_at=timezone.now(),
		)
		raw_key, key_prefix, key_hash = cls.generate_token()
		api_key = cls.objects.create(
			user=user,
			name=name,
			key_prefix=key_prefix,
			key_hash=key_hash,
			is_active=True,
		)
		return api_key, raw_key

	def revoke(self) -> None:
		"""Revokes this API key immediately."""
		self.is_active = False
		self.revoked_at = timezone.now()
		self.save(update_fields=['is_active', 'revoked_at'])

	def verify(self, raw_key: str) -> bool:
		"""Verifies that the provided raw key matches this ApiKey's hash in constant time."""
		if not self.is_active or self.revoked_at is not None:
			return False
		candidate_hash = self.hash_key(raw_key)
		return secrets.compare_digest(self.key_hash, candidate_hash)
