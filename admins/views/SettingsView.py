from django.http import JsonResponse

from authentication.models import ApiKey
from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.views import GetMapping, Mapping, PostMapping, View

__all__ = ['SettingsView']


@Mapping('dashboard/settings')
class SettingsView(View):
	R: R = R()

	def adminConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.aside['admin'].enabled = True

	@GetMapping('/')
	@Authenticated(staff=True)
	def settings(self, request):
		self.adminConfig()
		self.R.data.aside['admin'].activeSlug = 'settings'

		active_key = ApiKey.objects.filter(user=request.user, is_active=True).first()

		context = {
			'active_key': active_key,
			'user': request.user,
		}
		return self.render(request, context, 'dashboard/settings')

	@PostMapping('/api-key/generate')
	@Authenticated(staff=True)
	def generate_api_key(self, request):
		key_name = request.POST.get('name', 'Personal API Key')
		api_key, raw_key = ApiKey.create_key_for_user(request.user, name=key_name)

		return JsonResponse({
			'status': 'success',
			'raw_key': raw_key,
			'prefix': api_key.key_prefix,
			'name': api_key.name,
			'created_at': api_key.created_at.strftime('%b %d, %Y %H:%M UTC'),
		})

	@PostMapping('/api-key/revoke')
	@Authenticated(staff=True)
	def revoke_api_key(self, request):
		active_keys = ApiKey.objects.filter(user=request.user, is_active=True)
		count = active_keys.count()
		for key in active_keys:
			key.revoke()

		return JsonResponse({
			'status': 'success',
			'message': f'{count} API key(s) revoked successfully.',
		})
