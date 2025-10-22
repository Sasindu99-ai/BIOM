from vvecon.zorion.auth import Authenticated
from vvecon.zorion.views import GetMapping, Mapping, View

from res import R

__all__ = ['HomeView']


@Mapping('dashboard')
class HomeView(View):
	R: R = R()

	def adminConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.aside['admin'].enabled = True

	@GetMapping('/')
	@Authenticated(staff=True)
	def home(self, request):
		self.adminConfig()

		self.R.data.aside['admin'].activeSlug = 'dashboard'

		return self.render(request, dict(), 'dashboard/home')
