from res import R
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['PublicationsView']


@Mapping('publications')
class PublicationsView(View):
	R: R = R()

	def homeConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.footer.enabled = True

	@GetMapping('/')
	def publications(self, request):
		self.homeConfig()
		return self.render(request, dict(), 'publications')


