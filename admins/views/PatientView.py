from django.http import Http404

from authentication.enums import Gender
from authentication.services import UserService
from main.models import UserStudy
from main.services import PatientService
from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.logger import Logger
from vvecon.zorion.views import GetMapping, Mapping, PostMapping, View

__all__ = ['PatientView']


@Mapping('dashboard/patients')
class PatientView(View):
	R: R = R()

	patientService: PatientService = PatientService()
	userService: UserService = UserService()

	def authConfig(self):
		self.R.data.navigator.enabled = True
		self.R.data.aside['admin'].enabled = True

	@GetMapping('/')
	@Authenticated()
	def patients(self, request):
		Logger.info('Fetching patients for dashboard view')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/patients'

		context = dict(
			genders=Gender,
			canAdd=self.userService.hasPermission(request.user, 'add_patient', 'main'),
			canEdit=self.userService.hasPermission(request.user, 'change_patient', 'main'),
			canDelete=self.userService.hasPermission(request.user, 'delete_patient', 'main'),
		)
		return self.render(request, context=context, template_name='dashboard/patients')

	@GetMapping('/add')
	@Authenticated(permissions=['main.add_patient'])
	def addPatient(self, request):
		self.authConfig()

		context = dict(genders=Gender)
		return self.render(request, context=context, template_name='dashboard/patients/add')

	@GetMapping('/create')
	@Authenticated(permissions=['main.add_patient'])
	def createPatient(self, request):
		"""Single patient creation view with profile photo upload"""
		Logger.info('Loading single patient create view')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/patients'

		context = dict(genders=Gender)
		return self.render(request, context=context, template_name='dashboard/patients/create')

	@GetMapping('/view/<int:pid>')
	@GetMapping('/<int:pid>')
	@Authenticated(permissions=['main.view_patient'])
	def viewPatient(self, request, pid: int):
		"""Single patient view page with details, test history, and location"""
		Logger.info(f'Loading patient single view for ID: {pid}')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/patients'

		try:
			patient = self.patientService.getById(pid)
		except Exception:
			raise Http404(f'Patient with ID {pid} not found')

		user_studies = UserStudy.objects.filter(patient=patient).select_related(
			'study', 'createdBy',
		).prefetch_related('results__studyVariable').order_by('-testedDate', '-created_at')
		places = patient.places.all().order_by('-visitedAt') if hasattr(patient, 'places') else []

		for_popup = request.GET.get('popup') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'

		context = dict(
			patient=patient,
			userStudies=user_studies,
			places=places,
			forPopup=for_popup,
			canEdit=self.userService.hasPermission(request.user, 'change_patient', 'main'),
			canDelete=self.userService.hasPermission(request.user, 'delete_patient', 'main'),
		)
		return self.render(request, context=context, template_name='dashboard/patients/view')

	@PostMapping('/view/<int:pid>')
	@Authenticated(permissions=['main.view_patient'])
	def viewPatientPopup(self, request, pid: int):
		"""Single patient quick view popup modal content"""
		Logger.info(f'Loading patient quick view popup for ID: {pid}')
		self.authConfig()

		try:
			patient = self.patientService.getById(pid)
		except Exception:
			raise Http404(f'Patient with ID {pid} not found')

		user_studies = UserStudy.objects.filter(patient=patient).select_related(
			'study', 'createdBy',
		).prefetch_related('results__studyVariable').order_by('-testedDate', '-created_at')
		places = patient.places.all().order_by('-visitedAt') if hasattr(patient, 'places') else []

		context = dict(
			patient=patient,
			userStudies=user_studies,
			places=places,
			forPopup=True,
			canEdit=self.userService.hasPermission(request.user, 'change_patient', 'main'),
			canDelete=self.userService.hasPermission(request.user, 'delete_patient', 'main'),
		)
		return self.render(request, context=context, template_name='dashboard/patients/view')

	@GetMapping('/edit/<int:pid>')
	@Authenticated(permissions=['main.change_patient'])
	def editPatient(self, request, pid: int):
		"""Edit existing patient with photo management"""
		Logger.info(f'Loading patient edit view for ID: {pid}')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/patients'

		context = dict(
			genders=Gender,
			patientId=pid,
		)
		return self.render(request, context=context, template_name='dashboard/patients/edit')

	@PostMapping('/add')
	@Authenticated(permissions=['main.add_patient'])
	def addPatientPopup(self, request):
		Logger.info('Loading add patient popup')
		self.authConfig()

		context = dict(
			genders=Gender,
			forPopup=True,
		)
		return self.render(request, context=context, template_name='dashboard/patients/add')

	@GetMapping('/import')
	@Authenticated(permissions=['main.add_patient'])
	def importPatients(self, request):
		"""CSV/Excel import wizard"""
		Logger.info('Loading patient import wizard')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/patients'

		context = dict(genders=Gender)
		return self.render(request, context=context, template_name='dashboard/patients/import')

	@GetMapping('/match')
	@Authenticated(permissions=['main.view_patient'])
	def matchPatients(self, request):
		"""Patient matching tool - match CSV data against existing patients"""
		Logger.info('Loading patient matching tool')
		self.authConfig()
		self.R.data.aside['admin'].activeSlug = 'dashboard/patients'

		context = dict(genders=Gender)
		return self.render(request, context=context, template_name='dashboard/patients/match')

	@PostMapping('/create')
	@Authenticated(permissions=['main.add_patient'])
	def createPatientPopup(self, request):
		Logger.info('Loading create patient popup')
		self.authConfig()

		context = dict(
			genders=Gender,
			forPopup=True,
		)
		return self.render(request, context=context, template_name='dashboard/patients/create')

