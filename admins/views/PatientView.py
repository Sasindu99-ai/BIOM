from authentication.enums import Gender
from authentication.services import UserService
from main.services import PatientService
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.logger import Logger
from vvecon.zorion.views import View, Mapping, GetMapping, PostMapping
from res import R

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
			canDelete=self.userService.hasPermission(request.user, 'delete_patient', 'main')
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
