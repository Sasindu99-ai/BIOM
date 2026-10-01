from django.test import Client, TestCase

from authentication.models import ApiKey, User


class SettingsViewTest(TestCase):

	def setUp(self):
		self.client = Client()
		self.staff_user = User.objects.create_user(
			username='staff_settings',
			firstName='Staff',
			lastName='Settings',
		)
		self.staff_user.set_password('Secret123!')
		self.staff_user.is_staff = True
		self.staff_user.save()

		self.regular_user = User.objects.create_user(
			username='regular_settings',
			firstName='Regular',
			lastName='Settings',
		)
		self.regular_user.set_password('Secret123!')
		self.regular_user.save()

	def test_anonymous_user_redirected(self):
		response = self.client.get('/dashboard/settings/')
		# Zorion @Authenticated redirects unauthenticated users
		self.assertIn(response.status_code, [302, 401, 403])

	def test_regular_user_forbidden(self):
		self.client.force_login(self.regular_user)
		response = self.client.get('/dashboard/settings/')
		self.assertIn(response.status_code, [302, 403])

	def test_staff_user_can_access_settings(self):
		self.client.force_login(self.staff_user)
		response = self.client.get('/dashboard/settings/')
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'dashboard/settings.html')
		self.assertIn('active_key', response.context)

	def test_generate_api_key_endpoint(self):
		self.client.force_login(self.staff_user)
		response = self.client.post('/dashboard/settings/api-key/generate', {'name': 'Notebook Key'})
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(data.get('status'), 'success')
		self.assertTrue(data.get('raw_key').startswith('biom_live_'))
		self.assertTrue(data.get('prefix').startswith('biom_live_'))

		# Verify key exists in DB and is active
		api_key = ApiKey.objects.get(user=self.staff_user, is_active=True)
		self.assertTrue(api_key.verify(data['raw_key']))

		# Test rotation: generating again deactivates first key
		response2 = self.client.post('/dashboard/settings/api-key/generate', {'name': 'Notebook Key 2'})
		self.assertEqual(response2.status_code, 200)
		data2 = response2.json()

		api_key.refresh_from_db()
		self.assertFalse(api_key.is_active)
		self.assertIsNotNone(api_key.revoked_at)

		active_key = ApiKey.objects.get(user=self.staff_user, is_active=True)
		self.assertTrue(active_key.verify(data2['raw_key']))

	def test_revoke_api_key_endpoint(self):
		self.client.force_login(self.staff_user)
		# First generate a key
		self.client.post('/dashboard/settings/api-key/generate')
		self.assertTrue(ApiKey.objects.filter(user=self.staff_user, is_active=True).exists())

		# Now revoke
		response = self.client.post('/dashboard/settings/api-key/revoke')
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(data.get('status'), 'success')
		self.assertFalse(ApiKey.objects.filter(user=self.staff_user, is_active=True).exists())
