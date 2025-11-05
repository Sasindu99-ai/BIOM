from res import R
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['ApiView']


@Mapping('api')
class ApiView(View):
	R: R = R()

	def homeConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.footer.enabled = True

	@GetMapping('/')
	def api(self, request):
		self.homeConfig()
		return self.render(request, dict(), 'api')


