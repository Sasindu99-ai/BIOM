from drf_spectacular.utils import extend_schema
from rest_framework.status import HTTP_201_CREATED

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, Mapping, GetMapping, PostMapping, PutMapping, DeleteMapping
from ..payload.requests import FilterPatientRequest, PatientRequest
from ..payload.responses import PatientResponse
from ..services import PatientService

__all__ = ['V1Patient']


@Mapping('api/v1/patient')
class V1Patient(API):
	patientService: PatientService = PatientService()

	@extend_schema(
		tags=['Patient'],
		summary='Get patients',
		description='Get patients',
		request=FilterPatientRequest,
		responses={200: PatientResponse().response()},
	)
	@PostMapping('/')
	@Authorized(True, permissions=['main.view_patient'])
	def getPatients(self, request, data: FilterPatientRequest):
		Logger.info(f'Validating patient filter data: {data.initial_data}')
		if data.is_valid(raise_exception=True):
			Logger.info('Patient filter data is valid')
			patients = self.patientService.match(data)
			Logger.info(f'{len(patients)} patients found')
			return PatientResponse(data=patients, many=True).json()

	@extend_schema(
		tags=['Patient'],
		summary='Add patient(s)',
		description='Add single or multiple patients',
		request=PatientRequest,
		responses={201: PatientResponse().response()},
	)
	@PostMapping('/create')
	@Authorized(True, permissions=['main.add_patient'])
	def addPatient(self, request, data: PatientRequest):
		Logger.info('Validating patient data')
		if data.is_valid(raise_exception=True):
			Logger.info('Patient data is valid')
			
			# Check if validated_data is a list (bulk create) or single patient
			validated_data = data.validated_data
			
			if isinstance(validated_data, list):
				# Bulk create
				created_patients = []
				
				for idx, patient_data in enumerate(validated_data):
					try:
						patient_dict = patient_data.copy() if isinstance(patient_data, dict) else patient_data
						if 'createdBy' not in patient_dict or not patient_dict.get('createdBy'):
							patient_dict['createdBy'] = request.user
						
						patient = self.patientService.create(patient_dict)
						created_patients.append(patient)
						Logger.info(f'Patient {patient.id} created')
					except Exception as e:
						Logger.error(f'Error creating patient {idx+1}: {str(e)}')
				
				return PatientResponse(data=created_patients, many=True).json(status=HTTP_201_CREATED)
			else:
				# Single create
				if 'createdBy' not in validated_data or not validated_data.get('createdBy'):
					validated_data['createdBy'] = request.user
				patient = self.patientService.create(validated_data)
				Logger.info(f'Patient {patient.id} created')
				return PatientResponse(data=patient).json(status=HTTP_201_CREATED)

	@extend_schema(
		tags=['Patient'],
		summary='Update patient',
		description='Update patient',
		request=PatientRequest,
		responses={200: PatientResponse().response()},
	)
	@PutMapping('/<int:pid>')
	@Authorized(True, permissions=['main.change_patient'])
	def updatePatient(self, request, pid: int, data: PatientRequest):
		Logger.info('Validating patient data')
		if data.is_valid(raise_exception=True):
			Logger.info('Patient data is valid')
			patient = self.patientService.update(self.patientService.getById(pid), data.validated_data)
			Logger.info(f'Patient {patient.id} updated')
			return PatientResponse(data=patient).json()

	@extend_schema(
		tags=['Patient'],
		summary='Delete patient',
		description='Delete patient',
	)
	@DeleteMapping('/<int:pid>')
	@Authorized(True, permissions=['main.delete_patient'])
	def deletePatient(self, request, pid: int):
		Logger.info(f'Deleting patient {pid}')
		self.patientService.delete(pid)
		Logger.info(f'Patient {pid} deleted')
		return Return.ok()

	@extend_schema(
		tags=['Patient'],
		summary='Get patient',
		description='Get patient',
		responses={200: PatientResponse().response()},
	)
	@GetMapping('/<int:pid>')
	@Authorized(True, permissions=['main.view_patient'])
	def getPatient(self, request, pid: int):
		Logger.info(f'Fetching patient {pid}')
		patient = self.patientService.getById(pid)
		Logger.info(f'Patient {patient} fetched')
		return PatientResponse(data=patient).json()
