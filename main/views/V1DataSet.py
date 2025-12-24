from drf_spectacular.utils import extend_schema

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, DeleteMapping, GetMapping, Mapping, PostMapping, PutMapping

from ..payload.requests import FilterDataSetRequest, StudyVariableRequest
from ..payload.responses import DataSetResponse, StudyVariableResponse
from ..services import StudyService

__all__ = ['V1DataSet']


@Mapping('api/v1/dataset')
class V1DataSet(API):
	studyService: StudyService = StudyService()

	@extend_schema(
		tags=['Dataset'],
		summary='Get datasets',
		description='Get datasets with filtering, search, and pagination',
		request=FilterDataSetRequest,
		responses={200: DataSetResponse().response()},
	)
	@PostMapping('/')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasets(self, request, data: FilterDataSetRequest):
		Logger.info(f'Validating dataset filter data: {data.initial_data}')
		if data.is_valid(raise_exception=True):
			Logger.info('Dataset filter data is valid')

			# Get pagination info before filtering
			validated_data = data.validated_data.copy()
			pagination_data = validated_data.get('pagination', {})
			page = pagination_data.get('page', 1) if pagination_data else 1
			limit = pagination_data.get('limit', 20) if pagination_data else 20

			# Get filtered queryset WITHOUT pagination for stats
			search_data = validated_data.copy()
			search_data.pop('pagination', None)  # Remove pagination to get all filtered results
			filtered_queryset = self.studyService.search(search_data)

			# Apply sorting
			sort_field = validated_data.get('sortField', 'created_at')
			sort_direction = validated_data.get('sortDirection', 'desc')

			# Map frontend field names to model field names
			field_mapping = {
				'name': 'name',
				'created': 'created_at',
				'version': 'version',
				'category': 'category',
				'created_at': 'created_at',
			}

			# Get the actual field name
			actual_field = field_mapping.get(sort_field, 'created_at')

			# Apply ordering
			if sort_direction == 'asc':
				filtered_queryset = filtered_queryset.order_by(actual_field)
			else:
				filtered_queryset = filtered_queryset.order_by(f'-{actual_field}')

			# Calculate statistics from filtered results
			from django.db.models import Count, Max

			total_count = filtered_queryset.count()

			# Get aggregated stats
			stats_query = filtered_queryset.aggregate(
				totalVariables=Count('variables', distinct=True),
				totalUserStudies=Count('userStudies', distinct=True),
				maxVersion=Max('version'),
			)

			# Now get paginated datasets using paginate method
			datasets = self.studyService.paginate(filtered_queryset, page, limit)

			# Build response
			total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

			response_data = {
				'results': DataSetResponse(data=datasets, many=True).json().data,
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
					'totalVariables': stats_query['totalVariables'] or 0,
					'totalUserStudies': stats_query['totalUserStudies'] or 0,
					'latestVersion': stats_query['maxVersion'] or 1,
				},
			}

			Logger.info(f'{len(datasets)} datasets found on page {page}/{total_pages}')
			return Return.ok(response_data)

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset',
		description='Get single dataset details',
		responses={200: DataSetResponse().response()},
	)
	@GetMapping('/<int:id>')
	@Authorized(True, permissions=['main.view_study'])
	def getDataset(self, request, id: int):
		Logger.info(f'Fetching dataset {id}')
		dataset = self.studyService.getById(id)
		Logger.info(f'Dataset {dataset} fetched')
		return DataSetResponse(data=dataset).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Delete dataset',
		description='Delete dataset',
	)
	@DeleteMapping('/<int:id>')
	@Authorized(True, permissions=['main.delete_study'])
	def deleteDataset(self, request, id: int):
		Logger.info(f'Deleting dataset {id}')
		self.studyService.delete(id)
		Logger.info(f'Dataset {id} deleted')
		return Return.ok()

	# ========== Phase 2 Endpoints ==========

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset details',
		description='Get full dataset details with variables and statistics',
	)
	@GetMapping('/<int:id>/details')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetDetails(self, request, id: int):
		Logger.info(f'Fetching dataset details for {id}')
		details = self.studyService.getDetails(id)

		response_data = {
			'dataset': DataSetResponse(data=details['study']).json().data,
			'variables': StudyVariableResponse(data=details['variables'], many=True).json().data,
			'stats': details['stats'],
		}

		Logger.info(f'Dataset {id} details fetched')
		return Return.ok(response_data)

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset variables',
		description='Get all variables for a dataset',
	)
	@GetMapping('/<int:id>/variables')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetVariables(self, request, id: int):
		Logger.info(f'Fetching variables for dataset {id}')
		variables = self.studyService.getVariables(id)
		Logger.info(f'{len(variables)} variables found for dataset {id}')
		return StudyVariableResponse(data=variables, many=True).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Add variable to dataset',
		description='Add a new variable to a dataset',
		request=StudyVariableRequest,
	)
	@PostMapping('/<int:id>/variables')
	@Authorized(True, permissions=['main.change_study'])
	def addDatasetVariable(self, request, id: int, data: StudyVariableRequest):
		Logger.info(f'Adding variable to dataset {id}')
		if data.is_valid(raise_exception=True):
			variable = self.studyService.addVariable(id, data.validated_data)
			Logger.info(f'Variable {variable.id} added to dataset {id}')
			return StudyVariableResponse(data=variable).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Update variable',
		description='Update an existing variable',
		request=StudyVariableRequest,
	)
	@PutMapping('/<int:dataset_id>/variables/<int:variable_id>')
	@Authorized(True, permissions=['main.change_study'])
	def updateDatasetVariable(self, request, dataset_id: int, variable_id: int, data: StudyVariableRequest):
		Logger.info(f'Updating variable {variable_id} in dataset {dataset_id}')
		if data.is_valid(raise_exception=True):
			variable = self.studyService.updateVariable(variable_id, data.validated_data)
			Logger.info(f'Variable {variable_id} updated')
			return StudyVariableResponse(data=variable).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Delete variable',
		description='Remove a variable from a dataset',
	)
	@DeleteMapping('/<int:dataset_id>/variables/<int:variable_id>')
	@Authorized(True, permissions=['main.change_study'])
	def deleteDatasetVariable(self, request, dataset_id: int, variable_id: int):
		Logger.info(f'Removing variable {variable_id} from dataset {dataset_id}')
		self.studyService.removeVariable(dataset_id, variable_id)
		Logger.info(f'Variable {variable_id} removed from dataset {dataset_id}')
		return Return.ok()

	@extend_schema(
		tags=['Dataset'],
		summary='Get data preview',
		description='Get paginated data preview for a dataset',
	)
	@PostMapping('/<int:id>/data')
	@Authorized(True, permissions=['main.view_study'])
	def getDataPreview(self, request, id: int):
		Logger.info(f'Fetching data preview for dataset {id}')

		# Get pagination from request body
		page = request.data.get('page', 1)
		limit = request.data.get('limit', 10)

		data_preview = self.studyService.getDataPreview(id, page, limit)
		Logger.info(f'{len(data_preview["rows"])} data rows found for dataset {id}')
		return Return.ok(data_preview)

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset history',
		description='Get update history timeline for a dataset',
	)
	@GetMapping('/<int:id>/history')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetHistory(self, request, id: int):
		Logger.info(f'Fetching history for dataset {id}')
		history = self.studyService.getHistory(id)
		Logger.info(f'{len(history)} history events found for dataset {id}')
		return Return.ok({'events': history})

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset patients',
		description='Get patients who have data entries in this dataset with pagination',
	)
	@GetMapping('/<int:id>/patients')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetPatients(self, request, id: int):
		Logger.info(f'Fetching patients for dataset {id}')

		page = int(request.GET.get('page', 1))
		limit = int(request.GET.get('limit', 20))

		patients_data = self.studyService.getPatients(id, page, limit)
		Logger.info(f'{len(patients_data.get("patients", []))} patients found for dataset {id}')
		return Return.ok(patients_data)

	@extend_schema(
		tags=['Dataset'],
		summary='Download import template',
		description='Download a CSV template with columns for patient reference and dataset variables',
	)
	@GetMapping('/<int:id>/template')
	@Authorized(True, permissions=['main.view_study'])
	def downloadTemplate(self, request, id: int):
		Logger.info(f'Generating import template for dataset {id}')

		import csv
		import io

		from django.http import StreamingHttpResponse

		# Get dataset and variables
		dataset = self.studyService.getById(id)
		variables = list(dataset.variables.all().order_by('order', 'name'))

		def generate_csv():
			output = io.StringIO()
			writer = csv.writer(output)

			# Header row: PatientReference + all variable names
			headers = ['PatientReference']
			for v in variables:
				headers.append(v.name)
			writer.writerow(headers)
			yield output.getvalue()
			output.seek(0)
			output.truncate(0)

			# Add 3 sample rows with placeholder data
			for i in range(3):
				row = [f'PATIENT-{i+1:03d}']
				for v in variables:
					if v.type == 'NUMBER':
						row.append('')
					elif v.type == 'BOOLEAN':
						row.append('Yes/No')
					elif v.type == 'DATE':
						row.append('YYYY-MM-DD')
					else:
						row.append('')
				writer.writerow(row)
				yield output.getvalue()
				output.seek(0)
				output.truncate(0)

		response = StreamingHttpResponse(generate_csv(), content_type='text/csv')
		safe_name = ''.join(c for c in dataset.name if c.isalnum() or c in (' ', '-', '_')).strip()
		response['Content-Disposition'] = f'attachment; filename="{safe_name}_import_template.csv"'

		Logger.info(f'Template generated for dataset {id} with {len(variables)} variables')
		return response

	@extend_schema(
		tags=['Dataset'],
		summary='Create dataset',
		description='Create a new dataset',
	)
	@PostMapping('/create')
	@Authorized(True, permissions=['main.add_study'])
	def createDataset(self, request):
		Logger.info('Creating new dataset')
		data = request.data

		# Create the dataset
		from ..models import Study
		dataset = Study.objects.create(
			name=data.get('name'),
			description=data.get('description', ''),
			category=data.get('category'),
			status=data.get('status', 'ACTIVE'),
			reference=data.get('reference', ''),
			createdBy=request.user,
			version=1,
		)

		Logger.info(f'Dataset {dataset.id} created')
		return DataSetResponse(data=dataset).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Update dataset',
		description='Update an existing dataset',
	)
	@PutMapping('/<int:id>')
	@Authorized(True, permissions=['main.change_study'])
	def updateDataset(self, request, id: int):
		Logger.info(f'Updating dataset {id}')
		data = request.data

		dataset = self.studyService.getById(id)

		# Track changes for history
		changes = []
		if 'name' in data and data['name'] != dataset.name:
			changes.append(f"Name changed from '{dataset.name}' to '{data['name']}'")
			dataset.name = data['name']
		if 'description' in data and data['description'] != dataset.description:
			changes.append('Description updated')
			dataset.description = data['description']
		if 'category' in data and data['category'] != dataset.category:
			changes.append(f"Category changed to '{data['category']}'")
			dataset.category = data['category']
		if 'status' in data and data['status'] != dataset.status:
			changes.append(f"Status changed to '{data['status']}'")
			dataset.status = data['status']
		if 'reference' in data and data['reference'] != dataset.reference:
			changes.append('Reference updated')
			dataset.reference = data['reference']

		# Increment version if there are changes
		if changes:
			dataset.version = (dataset.version or 1) + 1
			dataset.save()
			Logger.info(f'Dataset {id} updated to version {dataset.version}: {", ".join(changes)}')
		else:
			Logger.info(f'No changes made to dataset {id}')

		return DataSetResponse(data=dataset).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Preview import data',
		description='Parse uploaded file and preview data for import with column detection',
	)
	@PostMapping('/<int:id>/import/preview')
	@Authorized(True, permissions=['main.change_study'])
	def previewImportData(self, request, id: int):
		Logger.info(f'Previewing import data for dataset {id}')

		data = request.data
		file_url = data.get('fileUrl')
		mapping = data.get('mapping')
		preview_mode = data.get('preview', False)

		if not file_url:
			return Return.error('No file URL provided')

		# Get dataset and variables
		dataset = self.studyService.getById(id)
		variables = list(dataset.variables.all())

		try:
			# Parse file (simplified - in production would use pandas/openpyxl)
			import csv

			# Construct file path from URL
			file_path = file_url.replace('/media/', 'media/')

			columns = []
			sample_rows = []
			all_rows = []

			if file_path.endswith('.csv'):
				with open(file_path, encoding='utf-8') as f:
					reader = csv.DictReader(f)
					columns = reader.fieldnames or []
					for i, row in enumerate(reader):
						all_rows.append(row)
						if i < 5:
							sample_rows.append(row)

			# If just parsing (step 1), return columns
			if not preview_mode or not mapping:
				return Return.ok({
					'columns': columns,
					'sampleRows': sample_rows,
					'totalRows': len(all_rows),
				})

			# If preview mode (step 2), analyze data
			patient_col = mapping.get('patientColumn')
			patient_identifier = mapping.get('patientIdentifier', 'reference')
			variable_mapping = mapping.get('variables', {})

			from ..models import Patient, UserStudy

			rows_result = []
			new_count = 0
			update_count = 0
			error_count = 0
			errors = []

			for idx, row in enumerate(all_rows):
				patient_value = row.get(patient_col, '').strip()

				if not patient_value:
					errors.append({'row': idx + 2, 'message': 'Missing patient identifier'})
					error_count += 1
					continue

				# Find patient
				patient = None
				if patient_identifier == 'reference':
					patient = Patient.objects.filter(reference=patient_value).first()
				else:
					# Try name matching (simplified)
					parts = patient_value.split()
					if len(parts) >= 2:
						patient = Patient.objects.filter(firstName__iexact=parts[0], lastName__iexact=' '.join(parts[1:])).first()
					elif len(parts) == 1:
						patient = Patient.objects.filter(firstName__iexact=parts[0]).first() or Patient.objects.filter(lastName__iexact=parts[0]).first()

				# Check if entry exists
				status = 'new'
				if patient:
					existing = UserStudy.objects.filter(study=dataset, patient=patient).exists()
					if existing:
						status = 'update'
						update_count += 1
					else:
						new_count += 1
				else:
					status = 'error'
					errors.append({'row': idx + 2, 'message': f'Patient not found: {patient_value}'})
					error_count += 1

				# Build values dict
				values = {}
				for var_id, col_name in variable_mapping.items():
					values[var_id] = row.get(col_name, '')

				rows_result.append({
					'patientName': patient_value,
					'patientId': patient.id if patient else None,
					'status': status,
					'values': values,
				})

			return Return.ok({
				'total': len(all_rows),
				'newCount': new_count,
				'updateCount': update_count,
				'errorCount': error_count,
				'errors': errors[:10],  # Limit errors
				'rows': rows_result[:100],  # Limit preview rows
			})

		except Exception as e:
			Logger.error(f'Error previewing import: {e!s}')
			return Return.error(f'Failed to parse file: {e!s}')

	@extend_schema(
		tags=['Dataset'],
		summary='Execute data import',
		description='Execute the data import from uploaded file into the dataset',
	)
	@PostMapping('/<int:id>/import/execute')
	@Authorized(True, permissions=['main.change_study'])
	def executeImportData(self, request, id: int):
		Logger.info(f'Executing data import for dataset {id}')

		data = request.data
		file_url = data.get('fileUrl')
		mapping = data.get('mapping')

		if not file_url or not mapping:
			return Return.error('File URL and mapping are required')

		# Get dataset and variables
		dataset = self.studyService.getById(id)

		try:
			import csv

			file_path = file_url.replace('/media/', 'media/')

			patient_col = mapping.get('patientColumn')
			patient_identifier = mapping.get('patientIdentifier', 'reference')
			variable_mapping = mapping.get('variables', {})

			from ..models import Patient, StudyResult, StudyVariable, UserStudy

			imported = 0
			updated = 0
			skipped = 0
			failed = 0

			with open(file_path, encoding='utf-8') as f:
				reader = csv.DictReader(f)

				for row in reader:
					patient_value = row.get(patient_col, '').strip()

					if not patient_value:
						skipped += 1
						continue

					# Find patient
					patient = None
					if patient_identifier == 'reference':
						patient = Patient.objects.filter(reference=patient_value).first()
					else:
						parts = patient_value.split()
						if len(parts) >= 2:
							patient = Patient.objects.filter(firstName__iexact=parts[0], lastName__iexact=' '.join(parts[1:])).first()
						elif len(parts) == 1:
							patient = Patient.objects.filter(firstName__iexact=parts[0]).first()

					if not patient:
						failed += 1
						continue

					# Create or update UserStudy
					user_study, created = UserStudy.objects.get_or_create(
						study=dataset,
						patient=patient,
						defaults={
							'status': 'ACTIVE',
							'createdBy': request.user,
						},
					)

					if created:
						imported += 1
					else:
						updated += 1

					# Create/update StudyResults
					for var_id, col_name in variable_mapping.items():
						value = row.get(col_name, '').strip()
						if value:
							try:
								variable = StudyVariable.objects.get(id=var_id)
								StudyResult.objects.update_or_create(
									userStudy=user_study,
									studyVariable=variable,
									defaults={'value': value},
								)
							except StudyVariable.DoesNotExist:
								pass

			Logger.info(f'Import complete for dataset {id}: {imported} imported, {updated} updated, {skipped} skipped, {failed} failed')

			return Return.ok({
				'imported': imported,
				'updated': updated,
				'skipped': skipped,
				'failed': failed,
			})

		except Exception as e:
			Logger.error(f'Error executing import: {e!s}')
			return Return.error(f'Import failed: {e!s}')
