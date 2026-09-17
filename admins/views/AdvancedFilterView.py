from main.services import PatientService, StudyService
from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.logger import Logger
from vvecon.zorion.views import GetMapping, Mapping, View

__all__ = ['AdvancedFilterView']


@Mapping('dashboard/advanced-filter')
class AdvancedFilterView(View):
	R: R = R()
	studyService: StudyService = StudyService()
	patientService: PatientService = PatientService()

	def adminConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.aside['admin'].enabled = True

	@GetMapping('/')
	@Authenticated(staff=True)
	def advanced_filter_view(self, request):
		"""
		Advanced filtering page across multiple datasets. This is a thin shell:
		the dataset picker is server-rendered so it works without JS, but
		filtering itself is driven client-side against the JSON endpoints under
		/api/v1/dataset/advanced-filter/* - the same engine (and, for a single
		dataset, the exact same behaviour) as the per-dataset filter page at
		/dashboard/datasets/filter/<id>.
		"""
		self.adminConfig()
		self.R.data.aside['admin'].activeSlug = 'advanced-filter'

		all_studies_data = self.studyService.getPaginatedStudies(limit=1000)
		all_studies = all_studies_data.get('studies', [])

		context = {
			'all_studies': [{'id': study.id, 'name': study.name} for study in all_studies],
		}

		return self.render(request, context, 'dashboard/filter/advanced_filter')
