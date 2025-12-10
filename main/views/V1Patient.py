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
			
			# Handle age and dateOfBirth mutual exclusivity
			validated_data = data.validated_data.copy()
			if validated_data.get('age') and validated_data.get('dateOfBirth'):
				# If both are provided, prefer age and clear dateOfBirth
				validated_data['dateOfBirth'] = None
				data._validated_data = validated_data  # Update the request data
				Logger.info('Both age and dateOfBirth provided, using age filter')
			
			# Get pagination info before filtering
			pagination_data = validated_data.get('pagination', {})
			page = pagination_data.get('page', 1) if pagination_data else 1
			limit = pagination_data.get('limit', 20) if pagination_data else 20
			
			# Get filtered queryset WITHOUT pagination for stats (service.search without pagination)
			search_data = validated_data.copy()
			search_data.pop('pagination', None)  # Remove pagination to get all filtered results
			filtered_queryset = self.patientService.search(search_data)
			
			# Calculate statistics from filtered results
			from datetime import datetime
			from django.db.models import Avg, Count, Q
			
			total_count = filtered_queryset.count()
			
			# Get aggregated stats
			stats_query = filtered_queryset.aggregate(
				avgAge=Avg('age'),
				maleCount=Count('id', filter=Q(gender='MALE')),
				femaleCount=Count('id', filter=Q(gender='FEMALE')),
			)
			
			# Count patients created this month in filtered results
			current_month = datetime.now().month
			current_year = datetime.now().year
			this_month_count = filtered_queryset.filter(
				created_at__year=current_year,
				created_at__month=current_month
			).count()
			
			# Now get paginated patients using match (which includes pagination)
			patients = self.patientService.paginate(filtered_queryset, page, limit)
			
			# Build response
			total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
			
			response_data = {
				'results': PatientResponse(data=patients, many=True).json().data,
				'pagination': {
					'page': page,
					'limit': limit,
					'total': total_count,
					'totalPages': total_pages,
					'hasNext': page < total_pages,
					'hasPrev': page > 1,
				},
				'stats': {
					'total': total_count,
					'avgAge': round(stats_query['avgAge'], 1) if stats_query['avgAge'] else 0,
					'male': stats_query['maleCount'] or 0,
					'female': stats_query['femaleCount'] or 0,
					'thisMonth': this_month_count,
				}
			}
			
			Logger.info(f'{len(patients)} patients found on page {page}/{total_pages}')
			return Return.ok(response_data)

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

	@extend_schema(
		tags=['Patient'],
		summary='Match patients from file',
		description='Match patients from uploaded file URL with column mapping',
	)
	@PostMapping('/match')
	@Authorized(True, permissions=['main.view_patient'])
	def matchPatients(self, request):
		Logger.info('Starting patient matching from file')
		
		from rest_framework.response import Response
		from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
		
		# Get file URL and column mapping from request
		file_url = request.data.get('file_url', '')
		column_mapping = request.data.get('column_mapping', dict())
		
		if not file_url:
			return Return.badRequest(dict(error='No file URL provided', message='No file URL provided'))
		
		try:
			# Process file and match patients
			results_path = self.patientService.matchPatientsFromFile(file_url, column_mapping)
			
			Logger.info(f'Patient matching completed. Results saved to: {results_path}')
			
			return Return.ok(dict(
				success=True,
				results_file=results_path,
				download_url=f'/media/{results_path}'
			))
		except ValueError as e:
			Logger.error(f'Validation error matching patients: {str(e)}')
			return Return.badRequest(dict(error='Validation error', message=str(e)))
		except Exception as e:
			Logger.error(f'Error matching patients: {str(e)}')
			return Response(
				data=dict(error='Error processing file', message=str(e)),
				status=HTTP_500_INTERNAL_SERVER_ERROR
			)