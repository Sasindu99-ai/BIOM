from main.enums import StudyCategory, StudyStatus
from main.services import StudyService
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

		# Get user permissions
		user = request.user
		canAdd = user.has_perm('main.add_study')
		canEdit = user.has_perm('main.change_study')
		canDelete = user.has_perm('main.delete_study')

		context = dict(
			validated=False,
			categories=StudyCategory.choices,
			statuses=StudyStatus.choices,
			canAdd=canAdd,
			canEdit=canEdit,
			canDelete=canDelete,
		)

		return self.render(request, context=context, template_name='dashboard/datasets')
