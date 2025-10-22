from icecream import ic

from biom.services import StudyService
from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['DataSetView']


@Mapping('dashboard/datasets')
class DataSetView(View):
	R: R = R()

	studyService: StudyService = StudyService()

	def authConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.aside['admin'].enabled = True

	@GetMapping('/')
	@Authenticated()
	def auth(self, request):
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/datasets'

		# Query all studies
		studies = self.studyService.getAll()

		return self.render(
			request,
			dict(validated=False, studies=studies),
			'dashboard/datasets'
		)
