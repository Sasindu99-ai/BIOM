from res import R
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['HomeView']


@Mapping()
class HomeView(View):
	R: R = R()

	def homeConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.footer.enabled = True

	@GetMapping()
	def home(self, request):
		self.homeConfig()
		return self.render(request, dict(), 'home')

	@GetMapping('privacy-policy')
	def privacyPolicy(self, request):
		self.homeConfig()
		return self.render(request, dict(), 'privacy-policy')

	@GetMapping('terms-and-conditions')
	def termsAndConditions(self, request):
		self.homeConfig()
		return self.render(request, dict(), 'terms-and-conditions')
