from main.enums import BioMarkerStatus, BioMarkerType, BiomType
from main.services import BioMarkerService
from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.logger import Logger
from vvecon.zorion.views import GetMapping, Mapping, PostMapping, View

__all__ = ['BioMarkerView']


@Mapping('dashboard/biomarkers')
class BioMarkerView(View):
	R: R = R()

	biomarkerService: BioMarkerService = BioMarkerService()

	def authConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.aside['admin'].enabled = True

	@GetMapping('/')
	@Authenticated()
	def biomarkers(self, request):
		"""List all biomarkers"""
		Logger.info('Fetching biomarkers for dashboard view')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/biomarkers'

		user = request.user
		context = dict(
			types=BioMarkerType.choices,
			biomTypes=BiomType.choices,
			statuses=BioMarkerStatus.choices,
			canAdd=user.has_perm('main.add_biomarker'),
			canEdit=user.has_perm('main.change_biomarker'),
			canDelete=user.has_perm('main.delete_biomarker'),
			canReview=user.has_perm('main.change_biomarker'),
		)
		return self.render(request, context=context, template_name='dashboard/biomarkers')

	@GetMapping('/create')
	@Authenticated(permissions=['main.add_biomarker'])
	def createBioMarker(self, request):
		"""Create new biomarker form"""
		Logger.info('Loading biomarker create view')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/biomarkers'

		context = dict(types=BioMarkerType.choices, biomTypes=BiomType.choices)
		return self.render(request, context=context, template_name='dashboard/biomarkers/create')

	@PostMapping('/create')
	@Authenticated(permissions=['main.add_biomarker'])
	def createBioMarkerPopup(self, request):
		"""Create biomarker popup mode"""
		Logger.info('Loading biomarker create popup')
		self.authConfig()

		context = dict(types=BioMarkerType.choices, biomTypes=BiomType.choices)
		return self.render(request, context=context, template_name='dashboard/biomarkers/_create_form')

	@GetMapping('/edit/<int:bid>')
	@Authenticated(permissions=['main.change_biomarker'])
	def editBioMarker(self, request, bid: int):
		"""Edit existing biomarker form"""
		Logger.info(f'Loading biomarker edit view for ID: {bid}')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/biomarkers'

		context = dict(biomarkerId=bid, types=BioMarkerType.choices, biomTypes=BiomType.choices)
		return self.render(request, context=context, template_name='dashboard/biomarkers/edit')

	@PostMapping('/edit/<int:bid>')
	@Authenticated(permissions=['main.change_biomarker'])
	def editBioMarkerPopup(self, request, bid: int):
		"""Edit biomarker popup mode"""
		Logger.info(f'Loading biomarker edit popup for ID: {bid}')
		self.authConfig()

		biomarker = self.biomarkerService.getById(bid)
		context = dict(
			biomarkerId=bid,
			biomarker=biomarker,
			types=BioMarkerType.choices,
			biomTypes=BiomType.choices,
		)
		return self.render(request, context=context, template_name='dashboard/biomarkers/_edit_form')
