from main.enums import StudyCategory, StudyStatus, StudyVariableField, StudyVariableStatus, StudyVariableType
from main.services import StudyService
from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.logger import Logger
from vvecon.zorion.views import GetMapping, Mapping, PostMapping, View

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
	def datasets(self, request):
		"""List all datasets"""
		Logger.info('Fetching datasets for dashboard view')
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

	@GetMapping('/view/<int:data_id>')
	@Authenticated(permissions=['main.view_study'])
	def viewDataset(self, request, data_id: int):
		"""View single dataset details"""
		Logger.info(f'Loading dataset view for ID: {data_id}')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/datasets'

		user = request.user
		context = dict(
			datasetId=id,
			categories=StudyCategory.choices,
			statuses=StudyStatus.choices,
			variableTypes=StudyVariableType.choices,
			variableFields=StudyVariableField.choices,
			variableStatuses=StudyVariableStatus.choices,
			canEdit=user.has_perm('main.change_study'),
			canDelete=user.has_perm('main.delete_study'),
		)
		return self.render(request, context=context, template_name='dashboard/datasets/view')

	@GetMapping('/create')
	@Authenticated(permissions=['main.add_study'])
	def createDataset(self, request):
		"""Create new dataset form"""
		Logger.info('Loading dataset create view')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/datasets'

		context = dict(
			categories=StudyCategory.choices,
			statuses=StudyStatus.choices,
		)
		return self.render(request, context=context, template_name='dashboard/datasets/create')

	@PostMapping('/create')
	@Authenticated(permissions=['main.add_study'])
	def createDatasetPopup(self, request):
		"""Create dataset popup mode"""
		Logger.info('Loading dataset create popup')
		self.authConfig()

		context = dict(
			categories=StudyCategory.choices,
			statuses=StudyStatus.choices,
		)
		return self.render(request, context=context, template_name='dashboard/datasets/_create_form')


	@GetMapping('/edit/<int:data_id>')
	@Authenticated(permissions=['main.change_study'])
	def editDataset(self, request, data_id: int):
		"""Edit existing dataset form"""
		Logger.info(f'Loading dataset edit view for ID: {data_id}')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/datasets'

		context = dict(
			datasetId=id,
			categories=StudyCategory.choices,
			statuses=StudyStatus.choices,
		)
		return self.render(request, context=context, template_name='dashboard/datasets/edit')

	@PostMapping('/edit/<int:data_id>')
	@Authenticated(permissions=['main.change_study'])
	def editDatasetPopup(self, request, data_id: int):
		"""Edit dataset popup mode"""
		Logger.info(f'Loading dataset edit popup for ID: {data_id}')
		self.authConfig()

		# Get dataset for pre-populating
		dataset = self.studyService.getById(data_id)

		context = dict(
			datasetId=data_id,
			dataset=dataset,
			categories=StudyCategory.choices,
			statuses=StudyStatus.choices,
		)
		return self.render(request, context=context, template_name='dashboard/datasets/_edit_form')

	@GetMapping('/import/<int:data_id>')
	@Authenticated(permissions=['main.change_study'])
	def importData(self, request, data_id: int):
		"""Data import wizard for a dataset"""
		Logger.info(f'Loading data import wizard for dataset ID: {data_id}')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/datasets'

		# Get dataset name for display
		dataset = self.studyService.getById(data_id)

		context = dict(
			datasetId=data_id,
			datasetName=dataset.name if dataset else 'Dataset',
		)
		return self.render(request, context=context, template_name='dashboard/datasets/import')
