import hashlib

from django.test import RequestFactory, TestCase
from rest_framework.exceptions import AuthenticationFailed

from authentication.auth import ApiKeyAuthentication
from authentication.models import ApiKey, User


class ApiKeyModelTest(TestCase):

	def setUp(self):
		self.staff_user = User.objects.create_user(
			username='staff_test',
			firstName='Staff',
			lastName='Tester',
		)
		self.staff_user.is_staff = True
		self.staff_user.save()

		self.regular_user = User.objects.create_user(
			username='regular_test',
			firstName='Regular',
			lastName='Tester',
		)

	def test_token_generation_structure(self):
		raw_key, prefix, key_hash = ApiKey.generate_token()
		self.assertTrue(raw_key.startswith('biom_live_'))
		self.assertTrue(prefix.startswith('biom_live_'))
		self.assertTrue(prefix.endswith('...'))
		self.assertEqual(len(key_hash), 64)
		expected_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
		self.assertEqual(key_hash, expected_hash)

	def test_create_key_and_rotation(self):
		api_key1, raw1 = ApiKey.create_key_for_user(self.staff_user, name='First Key')
		self.assertTrue(api_key1.is_active)
		self.assertIsNone(api_key1.revoked_at)
		self.assertNotEqual(api_key1.key_hash, raw1)
		self.assertTrue(api_key1.verify(raw1))

		# Now create second key (rotation)
		api_key2, raw2 = ApiKey.create_key_for_user(self.staff_user, name='Rotated Key')
		self.assertTrue(api_key2.is_active)
		self.assertTrue(api_key2.verify(raw2))

		# Refresh first key from DB
		api_key1.refresh_from_db()
		self.assertFalse(api_key1.is_active)
		self.assertIsNotNone(api_key1.revoked_at)
		self.assertFalse(api_key1.verify(raw1))

	def test_revoke_key(self):
		api_key, raw = ApiKey.create_key_for_user(self.staff_user)
		self.assertTrue(api_key.is_active)
		api_key.revoke()
		self.assertFalse(api_key.is_active)
		self.assertIsNotNone(api_key.revoked_at)
		self.assertFalse(api_key.verify(raw))


class ApiKeyAuthenticationTest(TestCase):

	def setUp(self):
		self.factory = RequestFactory()
		self.auth = ApiKeyAuthentication()
		self.staff_user = User.objects.create_user(
			username='staff_auth_user',
			firstName='Staff',
			lastName='Auth',
		)
		self.staff_user.is_staff = True
		self.staff_user.save()

		self.regular_user = User.objects.create_user(
			username='regular_auth_user',
			firstName='Regular',
			lastName='Auth',
		)
		self.api_key, self.raw_key = ApiKey.create_key_for_user(self.staff_user)

	def test_authenticate_with_x_api_key_header(self):
		request = self.factory.get('/api/test', HTTP_X_API_KEY=self.raw_key)
		result = self.auth.authenticate(request)
		self.assertIsNotNone(result)
		user, key_instance = result
		self.assertEqual(user.pk, self.staff_user.pk)
		self.assertEqual(key_instance.pk, self.api_key.pk)

		# Verify last_used_at was populated
		self.api_key.refresh_from_db()
		self.assertIsNotNone(self.api_key.last_used_at)

	def test_authenticate_with_bearer_authorization_header(self):
		request = self.factory.get('/api/test', HTTP_AUTHORIZATION=f'Bearer {self.raw_key}')
		result = self.auth.authenticate(request)
		self.assertIsNotNone(result)
		user, _ = result
		self.assertEqual(user.pk, self.staff_user.pk)

	def test_authenticate_with_api_key_authorization_header(self):
		request = self.factory.get('/api/test', HTTP_AUTHORIZATION=f'Api-Key {self.raw_key}')
		result = self.auth.authenticate(request)
		self.assertIsNotNone(result)
		user, _ = result
		self.assertEqual(user.pk, self.staff_user.pk)

	def test_authenticate_no_header_returns_none(self):
		request = self.factory.get('/api/test')
		result = self.auth.authenticate(request)
		self.assertIsNone(result)

	def test_authenticate_invalid_key_raises_error(self):
		request = self.factory.get('/api/test', HTTP_X_API_KEY='biom_live_invalidkey12345')
		with self.assertRaises(AuthenticationFailed):
			self.auth.authenticate(request)

	def test_authenticate_revoked_key_raises_error(self):
		self.api_key.revoke()
		request = self.factory.get('/api/test', HTTP_X_API_KEY=self.raw_key)
		with self.assertRaises(AuthenticationFailed):
			self.auth.authenticate(request)

	def test_authenticate_non_staff_raises_error(self):
		reg_key, reg_raw = ApiKey.create_key_for_user(self.regular_user)
		request = self.factory.get('/api/test', HTTP_X_API_KEY=reg_raw)
		with self.assertRaises(AuthenticationFailed):
			self.auth.authenticate(request)
